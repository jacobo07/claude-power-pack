"""Design Surface Router: which design tools a visual task must use, and whether the work is done.

Spec: vault/specs/design-surface-router.md. Data: vault/config/design_routes.json.
Used by tools/design_route_prompt.py (UserPromptSubmit), tools/design_donegate_stop.py (Stop) and
tools/design_review_record.py (the recorder cdio-reviewer calls). Pure logic plus small state files under
~/.claude/state/design_route/ (CPP_DESIGN_STATE_DIR overrides it).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
ROUTES_PATH = PP_ROOT / "vault" / "config" / "design_routes.json"
HTML_EXT = (".html", ".htm")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
FIRST_SCAN_BYTES = 16_000_000
CHECKS = ("design-taste", "design-skills", "design-review")
NA_RX = re.compile(r"NO APLICA:\s*`?(design-(?:taste|skills|review))`?\s*[:\-]\s*(\S.{2,})", re.I)
_CMD_RX = re.compile(r"<command-name>/?([A-Za-z0-9_:.-]+)</command-name>")


# ------------------------------------------------------------------ routes

def load_routes(path: str | os.PathLike | None = None) -> dict:
    with open(path or ROUTES_PATH, encoding="utf-8") as fh:
        routes = json.load(fh)
    for spec in routes["surfaces"].values():
        spec["_rx"] = re.compile(spec["prompt"], re.I)
    return routes


def _apply_overrides(kinds: list, routes: dict) -> list:
    drop = {o for k in kinds for o in routes["surfaces"][k].get("overrides", [])}
    return [k for k in kinds if k not in drop]


def classify(prompt: str, routes: dict) -> list:
    """Kinds named by a prompt, in table order, overrides applied. [] = not visual work by its words."""
    text = prompt or ""
    kinds = [k for k, spec in routes["surfaces"].items() if spec["_rx"].search(text)]
    return _apply_overrides(kinds, routes)


def effective_kinds(session_kinds: list, routes: dict) -> list:
    """The kinds that judge a written visual file. A file written with no visual words in any prompt is web."""
    kinds = [k for k in session_kinds if k in routes["surfaces"]]
    return _apply_overrides(kinds or [routes["default_kind"]], routes)


def policy(kinds: list, routes: dict) -> dict:
    s = routes["surfaces"]
    req, rec = [], []
    for k in kinds:
        req += [x for x in s[k]["required"] if x not in req]
        rec += [x for x in s[k]["recommended"] if x not in rec]
    return {"kinds": kinds, "required": req, "recommended": [x for x in rec if x not in req],
            "taste": any(s[k].get("taste") for k in kinds), "review": any(s[k].get("review") for k in kinds),
            "advice": [s[k]["advice"] for k in kinds if s[k].get("advice")]}


def is_visual(path: str, routes: dict) -> bool:
    return os.path.splitext(path or "")[1].lower() in routes["visual_ext"]


def skill_key(name: str) -> str:
    """`ui-ux-pro-max:ui-ux-pro-max` and `/design-md` load the same thing as their bare names."""
    n = (name or "").strip().lstrip("/").lower()
    return n.split(":")[-1] if ":" in n else n


def resolve_skill(name: str, home: str | None = None) -> str | None:
    """Where an installed skill or command lives, or None. A route naming an unloadable skill is a dead promise."""
    h = Path(home or Path.home()) / ".claude"
    key = skill_key(name)
    for cand in (h / "skills" / key / "SKILL.md", h / "commands" / ("%s.md" % key),
                 PP_ROOT / "skills" / key / "SKILL.md", PP_ROOT / "vendor" / "skills" / key / "SKILL.md"):
        if cand.is_file():
            return str(cand)
    return None


# ------------------------------------------------------------------ state

def state_dir() -> Path:
    d = Path(os.environ.get("CPP_DESIGN_STATE_DIR") or (Path.home() / ".claude" / "state" / "design_route"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sid_file(sid: str) -> Path:
    return state_dir() / ("%s.json" % (re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:80] or "nosid"))


def load_session(sid: str) -> dict:
    try:
        st = json.loads(_sid_file(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    for k, v in (("kinds", []), ("skills", []), ("writes", []), ("offset", 0), ("transcript", "")):
        st.setdefault(k, v)
    return st


def save_session(sid: str, st: dict) -> None:
    p = _sid_file(sid)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def append_row(name: str, row: dict) -> None:
    with open(state_dir() / name, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(row, ts=time.time()), ensure_ascii=False) + "\n")


def read_rows(name: str) -> list:
    p = state_dir() / name
    out = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    except OSError:
        pass
    return out


# ------------------------------------------------------------------ transcript

def _add(seq: list, item: str) -> None:
    if item and item not in seq:
        seq.append(item)


def _scan_row(row: dict, st: dict) -> None:
    msg = row.get("message") if isinstance(row, dict) else None
    if not isinstance(msg, dict):
        return
    content = msg.get("content")
    if row.get("type") == "user":
        texts = [content] if isinstance(content, str) else \
            [c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text"]
        for t in texts:
            for m in _CMD_RX.finditer(t or ""):
                _add(st["skills"], skill_key(m.group(1)))
        return
    if row.get("type") != "assistant" or not isinstance(content, list):
        return
    for c in content:
        if not isinstance(c, dict) or c.get("type") != "tool_use":
            continue
        inp = c.get("input") if isinstance(c.get("input"), dict) else {}
        if c.get("name") == "Skill":
            _add(st["skills"], skill_key(str(inp.get("skill") or "")))
        elif c.get("name") in WRITE_TOOLS:
            _add(st["writes"], str(inp.get("file_path") or inp.get("notebook_path") or ""))


def scan_transcript(path: str, st: dict) -> dict:
    """Incremental: reads only the bytes after st['offset'] (complete lines). A new transcript restarts the scan."""
    if not path or not os.path.isfile(path):
        return st
    if st.get("transcript") != path:
        st.update(transcript=path, offset=0)
    size = os.path.getsize(path)
    start = st["offset"]
    if start > size:
        start = 0
    skip_partial = False
    if start == 0 and size > FIRST_SCAN_BYTES:
        start, skip_partial = size - FIRST_SCAN_BYTES, True
    with open(path, "rb") as fh:
        fh.seek(start)
        data = fh.read()
    end = data.rfind(b"\n")
    if end < 0:
        return st
    lines = data[:end].split(b"\n")
    if skip_partial:
        lines = lines[1:]
    for raw in lines:
        try:
            _scan_row(json.loads(raw.decode("utf-8", errors="replace")), st)
        except ValueError:
            continue
    st["offset"] = start + end + 1
    return st


def last_assistant_text(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path, "rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(max(0, size - 600_000))
        lines = fh.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        msg = row.get("message") if isinstance(row, dict) else None
        if row.get("type") != "assistant" or not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        texts = [c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text"]
        if texts:
            return "\n".join(texts)
    return ""


def not_applicable(text: str) -> dict:
    return {m.group(1).lower(): m.group(2).strip() for m in NA_RX.finditer(text or "")}


# ------------------------------------------------------------------ surfaces and reviews

def canon(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def sha256(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(child: str, parent: str) -> bool:
    try:
        return os.path.commonpath([canon(child), canon(parent)]) == canon(parent)
    except ValueError:
        return False


def approved() -> dict:
    """canonical path -> set of sha256 whose recorded review is DONE (APPROVE and conformant)."""
    out: dict = {}
    for r in read_rows("reviews.jsonl"):
        if r.get("is_done") is True:
            for p, h in (r.get("files") or {}).items():
                out.setdefault(p, set()).add(h)
    return out


def rendered() -> dict:
    """canonical path -> set of sha256 that were rendered to PNG by the recorder."""
    out: dict = {}
    for r in read_rows("renders.jsonl"):
        if r.get("file") and r.get("sha") and r.get("pngs"):
            out.setdefault(r["file"], set()).add(r["sha"])
    return out


def judge(st: dict, cwd: str, routes: dict, na: dict | None = None) -> dict:
    """{files, kinds, problems:[{check, file, detail}], waived}. No visual file written in cwd -> no problems."""
    na = na or {}
    files = []
    for w in st.get("writes", []):
        if w and is_visual(w, routes) and os.path.isfile(w) and inside(w, cwd) and canon(w) not in files:
            files.append(canon(w))
    res = {"files": files, "kinds": [], "problems": [], "waived": {}}
    if not files:
        return res
    pol = policy(effective_kinds(st.get("kinds", []), routes), routes)
    res["kinds"] = pol["kinds"]
    problems = []
    if pol["taste"]:
        from modules.cdio import taste
        for f in files:
            if f.endswith(HTML_EXT):
                rep = taste.lint(f, site_root=cwd)
                for v in rep.verdicts:
                    if v.criterion in rep.blocking:
                        problems.append({"check": "design-taste", "file": f, "detail": "%s: %s" % (v.criterion, v.observed)})
    used = {skill_key(s) for s in st.get("skills", [])}
    missing = [s for s in pol["required"] if skill_key(s) not in used]
    if missing:
        problems.append({"check": "design-skills", "file": "", "detail": "not loaded this session: " + ", ".join(missing)})
    if pol["review"]:
        ok = approved()
        for f in files:
            h = sha256(f)
            if h not in ok.get(f, set()):
                problems.append({"check": "design-review", "file": f,
                                 "detail": "no recorded cdio-reviewer APPROVE for these bytes (sha %s)" % h[:12],
                                 "sha": h})
    res["waived"] = {k: v for k, v in na.items() if k in CHECKS}
    res["problems"] = [p for p in problems if p["check"] not in res["waived"]]
    return res
