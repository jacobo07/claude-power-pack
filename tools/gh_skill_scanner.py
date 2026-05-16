r"""
gh_skill_scanner.py - harvest GitHub-hosted Claude skills via gh CLI (MC-SCR-05).

Strategy: GitHub search API, queried via `gh search code`, looking for files
named skill.md or SKILL.md across all public repos. Each result is a candidate
Claude skill. We persist the raw search results plus enriched metadata
(name, repo, raw_url, frontmatter excerpts) to JSONL for downstream use by
MC-SCR-06 (unified index merge).

Rate limit: GitHub search is 30 req/min. `gh search code` paginates internally
to --limit (max 1000). Per query of --limit 1000 = ~10 page calls. Two queries
(skill.md + SKILL.md) = ~20 calls = well under the 30/min cap.

Limitations:
- GitHub search caps at 1000 results per query no matter what. If there are
  truly 1387 skills, we get the first 1000 of each filename variant after
  GitHub's relevance ranking. Dedup by (owner, repo, path) reduces the union.
- This does NOT fetch file contents — just lists candidates. Content fetch
  is a separate step that would burn the core API quota (5000 req/hr).

Output: vault/audits/gh_skills_raw.jsonl  (one JSON object per line)
        vault/audits/gh_skills_summary.json  (counts + dedup stats)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = REPO_ROOT / "vault" / "audits" / "gh_skills_raw.jsonl"
SUMMARY_OUT = REPO_ROOT / "vault" / "audits" / "gh_skills_summary.json"

GH_BIN = "gh"


def run_gh_search(filename: str, limit: int) -> list[dict]:
    """Invoke `gh search code path:<filename> --limit N --json ...`."""
    fields = "repository,path,sha,url"
    cmd = [
        GH_BIN,
        "search",
        "code",
        f"path:{filename}",
        "--limit",
        str(limit),
        "--json",
        fields,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [{"_error": "timeout", "_filename": filename}]
    if proc.returncode != 0:
        return [
            {
                "_error": "gh_returned_nonzero",
                "_filename": filename,
                "_rc": proc.returncode,
                "_stderr": (proc.stderr or "").strip()[:400],
            }
        ]
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return [
            {
                "_error": f"json_decode: {e}",
                "_filename": filename,
                "_stdout_head": proc.stdout[:200],
            }
        ]


def derive_skill_name(path: str) -> str | None:
    """Skill name is the parent directory of skill.md / SKILL.md."""
    m = re.match(r"(?:.*/)?([^/]+)/(?:skill|SKILL)\.md$", path)
    if m:
        return m.group(1)
    return None


def derive_raw_url(repo_full_name: str, sha: str | None, path: str) -> str:
    """Construct the raw.githubusercontent.com URL.
    Prefer sha-pinned URL when available; fall back to default branch."""
    if sha:
        return f"https://raw.githubusercontent.com/{repo_full_name}/{sha}/{path}"
    return f"https://raw.githubusercontent.com/{repo_full_name}/HEAD/{path}"


def normalize_entry(item: dict) -> dict | None:
    """Flatten a `gh search code` result into our canonical schema."""
    if "_error" in item:
        return item
    repo = item.get("repository") or {}
    repo_full = repo.get("nameWithOwner") or repo.get("name")
    path = item.get("path")
    sha = item.get("sha")
    if not repo_full or not path:
        return None
    return {
        "name": derive_skill_name(path),
        "repo": repo_full,
        "path": path,
        "sha": sha,
        "raw_url": derive_raw_url(repo_full, sha, path),
        "html_url": item.get("url"),
        "source": "github_search",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def atomic_write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            for e in entries:
                h.write(json.dumps(e, separators=(",", ":")) + "\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            json.dump(payload, h, indent=2, sort_keys=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gh_skill_scanner")
    parser.add_argument("--limit", type=int, default=1000, help="Per-query result cap")
    parser.add_argument(
        "--filenames",
        default="skill.md,SKILL.md",
        help="Comma-separated filenames to search for",
    )
    parser.add_argument(
        "--out-raw",
        default=str(RAW_OUT),
        help="Output JSONL of raw enriched entries",
    )
    parser.add_argument(
        "--out-summary",
        default=str(SUMMARY_OUT),
        help="Output JSON of run summary",
    )
    args = parser.parse_args(argv)

    if subprocess.run(["gh", "--version"], capture_output=True).returncode != 0:
        print("ERROR: gh CLI not on PATH or not authenticated", file=sys.stderr)
        return 2

    filenames = [s.strip() for s in args.filenames.split(",") if s.strip()]
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    raw_results: list[dict] = []
    errors: list[dict] = []
    per_query_counts: dict[str, int] = {}

    for fn in filenames:
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] querying path:{fn}", file=sys.stderr)
        items = run_gh_search(fn, args.limit)
        if items and isinstance(items[0], dict) and "_error" in items[0]:
            errors.append(items[0])
            per_query_counts[fn] = 0
            continue
        per_query_counts[fn] = len(items)
        for item in items:
            normalized = normalize_entry(item)
            if normalized is None:
                continue
            normalized["_query"] = fn
            raw_results.append(normalized)
        print(f"  -> {len(items)} results", file=sys.stderr)

    # Dedup by (repo, path)
    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for e in raw_results:
        if "_error" in e:
            deduped.append(e)
            continue
        key = (e["repo"], e["path"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    atomic_write_jsonl(Path(args.out_raw), deduped)

    summary = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filenames_queried": filenames,
        "limit_per_query": args.limit,
        "per_query_raw_count": per_query_counts,
        "total_raw": len(raw_results),
        "total_deduped": len(deduped) - sum(1 for e in deduped if "_error" in e),
        "errors": errors,
        "out_raw": args.out_raw,
    }
    atomic_write_json(Path(args.out_summary), summary)

    print(json.dumps(summary, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
