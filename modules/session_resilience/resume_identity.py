"""G6 runtime -- Resume Identity: human labels, work-type, catalog, search.

Extends RESUME_V3 (section 8) WITHOUT a parallel "Resume Identity OS". The PP
already shows each pane's ``topic`` (first prompt) in the PP Sessions panel and
already derives descriptive names in NAMED_RECOVERY_INDEX.md. The residual the
G6 plan names is the *catalog + classification + search* layer:

  * classify_task_type -- feature / debug / research / architecture / review / general
  * build_label        -- a stable human label (repo + cleaned topic + type),
                          never a raw UUID
  * build_catalog      -- a persistent session_catalog.json (durable, fsync'd)
  * search             -- rank sessions by query relevance, recency-tiebroken

Source of truth stays ``pane_map.json`` (disk truth, transcript-derived); this
module never invents a session id and never derives pane data itself. The native
/resume picker title is the session's first user message and cannot be safely
renamed (editing transcripts violates the Session Safety Contract) -- so these
labels live on the PP-owned surfaces (panel + catalog + index), the host limit
documented in RESUME_V3 section 8.5.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

CATALOG_FILENAME = "session_catalog.json"

# Work-type taxonomy. Order matters: more specific intents are tested before the
# broad "feature" verbs (build/add/create also appear in non-feature work).
TASK_TYPES = ("debug", "research", "review", "architecture", "feature", "general")

_TYPE_PATTERNS = [
    ("debug", re.compile(r"\b(bug|error|fix|crash|fail(?:ing|ed|ure)?|hang|broken|regression|traceback)\b", re.I)),
    ("research", re.compile(r"\b(research|audit|investigat\w*|analy[sz]\w*|scan|forensic|explore)\b", re.I)),
    ("review", re.compile(r"\b(review|code[- ]review|pr\s|pull request|critique)\b", re.I)),
    ("architecture", re.compile(r"\b(ultra[- ]?plan|architect\w*|design|dataset|spec|blueprint|schema)\b", re.I)),
    ("feature", re.compile(r"\b(feat\w*|build|implement|add|create|runtime|wire|integrat\w*|ship)\b", re.I)),
]

# Noise prefixes stripped so a label is the real topic, not a mode banner.
_NOISE = [
    re.compile(r"^PREFLIGHT:.*?(?=[A-Za-z]{4})", re.I),
    re.compile(r"^MODO:\s*", re.I),
    re.compile(r"^MASTER SYSTEM CONSTRUCTION PROMPT\s*", re.I),
    re.compile(r"^PROMPT MAESTRO\s*", re.I),
    re.compile(r"^SESI[O0]N:?\s*", re.I),
    re.compile(r"^#+\s*"),
    re.compile(r"^ULTRA[- ]?PLAN MODE\s*", re.I),
    re.compile(r"^EXECUTION MODE\s*", re.I),
    re.compile(r"git fetch origin.*?-\d+\s*", re.I),
]

_LABEL_MAX = 64
_UUID_RE = re.compile(r"[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}", re.I)


def _now_iso(now: str | None) -> str:
    return now if now else datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify_task_type(topic: str | None, branch: str | None = None) -> str:
    """Best-effort work-type from the first prompt (+ optional branch name).
    Advisory metadata, never a destructive filter: unmatched -> 'general'."""
    hay = f"{topic or ''} {branch or ''}"
    for name, pat in _TYPE_PATTERNS:
        if pat.search(hay):
            return name
    return "general"


def _clean_topic(topic: str | None) -> str:
    t = (topic or "").strip()
    for pat in _NOISE:
        t = pat.sub("", t).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def build_label(repo: str | None, topic: str | None,
                last_commit: str | None = None, task_type: str | None = None) -> str:
    """A stable, human label: '<repo> -- <clean topic> (<type>)'. Derived
    deterministically from context; never a UUID. Falls back to the last commit
    subject, then to the repo name, so the label is always something a human can
    read -- the T-RESUME-UUID-ANTIPATTERN-001 rule."""
    tt = task_type or classify_task_type(topic)
    body = _clean_topic(topic)
    if not body and last_commit:
        body = _clean_topic(last_commit)
    if not body:
        body = "(no topic)"
    repo_s = (repo or "session").strip()
    label = f"{repo_s} -- {body}"
    if len(label) > _LABEL_MAX:
        label = label[: _LABEL_MAX - 1].rstrip() + "…"
    return f"{label} ({tt})"


def label_is_human(label: str) -> bool:
    """True if the label reads as human text, not a bare UUID/hash."""
    return bool(label) and not _UUID_RE.search(label) and " -- " in label


def _durable_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=2))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def build_catalog(panes: list[dict], state_dir: Path | str,
                  now: str | None = None) -> list[dict]:
    """Build + persist session_catalog.json from pane_map panes. One entry per
    distinct session id, each with a human label, work-type and real metadata.
    Returns the catalog list."""
    seen: set[str] = set()
    catalog: list[dict] = []
    for p in panes or []:
        sid = p.get("sessionId")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        topic = p.get("topic")
        repo = p.get("repo")
        tt = classify_task_type(topic, p.get("branch"))
        catalog.append({
            "session_id": sid,
            "label": build_label(repo, topic, p.get("lastCommit"), tt),
            "repo": repo or "(unknown)",
            "task_type": tt,
            "cwd": p.get("cwd"),
            "topic": topic or "",
            "last_active": p.get("lastActivity") or p.get("ageHours"),
            "status": p.get("status") or ("live" if p.get("live") else "resumable"),
            "resume_cmd": p.get("resumeCmd") or (f"claude --resume {sid}"),
        })
    payload = {"schema_version": 1, "generated_at": _now_iso(now), "sessions": catalog}
    _durable_write_json(Path(state_dir) / CATALOG_FILENAME, payload)
    return catalog


def load_catalog(state_dir: Path | str) -> list[dict]:
    p = Path(state_dir) / CATALOG_FILENAME
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return list(data.get("sessions") or [])
    except (ValueError, OSError):
        return []


def _score(entry: dict, terms: list[str]) -> int:
    hay = " ".join(str(entry.get(k, "")) for k in
                   ("label", "repo", "task_type", "topic", "cwd")).lower()
    return sum(hay.count(t) for t in terms if t)


def search(catalog: list[dict], query: str) -> list[dict]:
    """Rank catalog entries by query-term frequency in label/repo/type/topic,
    recency-tiebroken (lastActivity desc). Zero-hit entries are excluded -- a
    query that matches nothing returns []."""
    terms = [t for t in re.split(r"\s+", (query or "").lower().strip()) if t]
    if not terms:
        return []
    scored = []
    for e in catalog:
        s = _score(e, terms)
        if s > 0:
            scored.append((s, str(e.get("last_active") or ""), e))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [e for _, _, e in scored]


def _main(argv=None) -> int:  # pragma: no cover - manual/hub entry point
    import argparse
    ap = argparse.ArgumentParser(description="G6 resume identity")
    ap.add_argument("--state-dir", default=str(Path.home() / ".claude" / "state"))
    ap.add_argument("--build", action="store_true", help="(re)build session_catalog.json from pane_map.json")
    ap.add_argument("--search", default=None, help="query the catalog")
    a = ap.parse_args(argv)
    sd = Path(a.state_dir)
    if a.build:
        pm = sd / "pane_map.json"
        panes = []
        if pm.is_file():
            try:
                panes = json.loads(pm.read_text(encoding="utf-8-sig")).get("panes") or []
            except (ValueError, OSError):
                panes = []
        cat = build_catalog(panes, sd)
        print(f"catalog: {len(cat)} sessions -> {sd / CATALOG_FILENAME}")
    elif a.search is not None:
        hits = search(load_catalog(sd), a.search)
        for h in hits[:20]:
            print(f"  [{h['task_type']:>12}] {h['label']}  ({h['session_id'][:8]})")
        if not hits:
            print("(no matches)")
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
