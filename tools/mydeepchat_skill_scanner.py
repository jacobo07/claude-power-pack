r"""
mydeepchat_skill_scanner.py - harvest the full mydeepchat catalog (MC-SCR-05 expanded).

Backend: Supabase project iobhvvjrssigmnfmjlvx, table 'skills', anon key embedded
in the public SPA bundle (used identically by skills.mydeepchat.com itself).

Schema observed:
  id, name, slug, description, author, author_avatar, github_url, skill0_url, prompt

Strategy: paginate via Range header in chunks of 1000.
Output: vault/audits/mydeepchat_skills_raw.jsonl (one entry per line)
        vault/audits/mydeepchat_skills_summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = REPO_ROOT / "vault" / "audits" / "mydeepchat_skills_raw.jsonl"
SUMMARY_OUT = REPO_ROOT / "vault" / "audits" / "mydeepchat_skills_summary.json"

SUPABASE_URL = "https://iobhvvjrssigmnfmjlvx.supabase.co"
TABLE = "skills"
ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvYmh2dmpyc3NpZ21uZm1qbHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDE1ODIsImV4cCI6MjA5MTkxNzU4Mn0."
    "ofXFDldhrCqHxa698LRZEWKf61XQdGeePopz5Tn2rR4"
)


def fetch_page(start: int, end: int, select: str) -> tuple[list[dict], str | None]:
    """Fetch one Range slice. Returns (rows, content_range_header)."""
    qs = urllib.parse.urlencode({"select": select})
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?{qs}"
    req = urllib.request.Request(url)
    req.add_header("apikey", ANON_KEY)
    req.add_header("Authorization", f"Bearer {ANON_KEY}")
    req.add_header("Range-Unit", "items")
    req.add_header("Range", f"{start}-{end}")
    req.add_header("Prefer", "count=exact")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        cr = resp.headers.get("Content-Range")
    return json.loads(body), cr


def atomic_write_jsonl(path: Path, entries) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            for e in entries:
                h.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
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
            json.dump(payload, h, indent=2, sort_keys=False, ensure_ascii=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mydeepchat_skill_scanner")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip the 'prompt' column to keep output small (just metadata)",
    )
    parser.add_argument("--out-raw", default=str(RAW_OUT))
    parser.add_argument("--out-summary", default=str(SUMMARY_OUT))
    args = parser.parse_args(argv)

    select = "id,name,slug,description,author,author_avatar,github_url,skill0_url"
    if not args.no_prompt:
        select += ",prompt"

    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_rows: list[dict] = []
    total_count: int | None = None
    page = 0
    cursor = 0

    while True:
        end = cursor + args.page_size - 1
        try:
            rows, content_range = fetch_page(cursor, end, select)
        except Exception as e:  # noqa: BLE001
            print(f"page {page} fetch error: {e}", file=sys.stderr)
            break
        if content_range and total_count is None and "/" in content_range:
            try:
                total_count = int(content_range.split("/")[-1])
            except ValueError:
                pass
        n = len(rows)
        print(
            f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] page {page} range {cursor}-{end} got {n} (total_known={total_count})",
            file=sys.stderr,
        )
        if n == 0:
            break
        all_rows.extend(rows)
        cursor += n
        page += 1
        if total_count is not None and cursor >= total_count:
            break
        if page > 50:
            print("too many pages; aborting", file=sys.stderr)
            break
        time.sleep(0.2)  # be nice

    atomic_write_jsonl(Path(args.out_raw), all_rows)

    summary = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "supabase_project": "iobhvvjrssigmnfmjlvx",
        "table": TABLE,
        "page_size": args.page_size,
        "pages_fetched": page,
        "total_count_reported": total_count,
        "rows_persisted": len(all_rows),
        "out_raw": args.out_raw,
        "out_size_bytes": Path(args.out_raw).stat().st_size if Path(args.out_raw).is_file() else 0,
    }
    atomic_write_json(Path(args.out_summary), summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
