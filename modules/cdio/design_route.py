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


def kinds_for(path: str, session_kinds: list, routes: dict) -> list | None:
    """The kinds that judge ONE written file, or None when that file is not judged.

    An HTML page is always judged: as web, unless the session's latest visual prompt made it a copy (calco) or a
    film (motion), whose own gates judge it. A non-gating kind (dataviz, brand) never replaces web for a page: it
    used to, and "plot"/"chart" in an unrelated prompt then switched Taste and the review off for the session
    (review of a9db1d43, F1). App source (tsx, jsx, vue, css) is judged only when the work was named as a visual
    surface: a logic fix in a component is not a design task (F2).
    """
    s = routes["surfaces"]
    ext = os.path.splitext(path or "")[1].lower()
    # A kind that declares extra_ext (brand) judges ONLY those extensions: as a gating kind for every path it made a
    # motion/calco page need a review and made app source judged in a brand-only session (review of bb95f710, M1).
    kinds = [k for k in session_kinds if k in s
             and (not s[k].get("extra_ext") or ext in [e.lower() for e in s[k]["extra_ext"]])]
    gating = [k for k in kinds if s[k].get("review")]
    overriding = any(s[k].get("overrides") for k in kinds)
    if (path or "").lower().endswith(HTML_EXT):
        # A page keeps web unless a kind that brings its own Taste/review (web, app_ui, mobile) or an overriding kind
        # (calco, motion) is present. Brand gates its assets since 2026-11-22; keyed on "gating" alone, a brand prompt
        # would have judged a page as brand only and switched Taste off (the F1 class again).
        if not any(s[k].get("taste") for k in kinds) and not overriding:
            kinds = kinds + [routes["default_kind"]]
    elif not gating:
        return None
    return _apply_overrides(kinds, routes)


def extra_ext(session_kinds: list, routes: dict) -> tuple:
    """Extensions a session's kinds add to the judged set: brand assets (.svg, .png) only in a brand session, so an
    icon written during web work is not pulled into the review."""
    s = routes["surfaces"]
    out = []
    for k in session_kinds:
        for e in (s.get(k) or {}).get("extra_ext", []):
            if e.lower() not in out:
                out.append(e.lower())
    return tuple(out)


def effective_kinds(session_kinds: list, routes: dict) -> list:
    """The kinds that judge an HTML page written in a session with these prompt kinds."""
    return kinds_for("page.html", session_kinds, routes)


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
    for k, v in (("kinds", []), ("skills", []), ("writes", []), ("shell_writes", []), ("offset", 0), ("transcript", ""),
                 ("write_kinds", {})):
        st.setdefault(k, v)
    return st


def _note_kinds(st: dict, path: str) -> None:
    """Remember the session kinds a file was written under (a union over every write of it). Writes are scanned at the
    Stop of the turn that made them, so the current kinds are that turn's (review of bb95f710, L1)."""
    if path:
        seen = st["write_kinds"].setdefault(canon(path), [])
        seen += [k for k in st.get("kinds", []) if k not in seen]


def asset_ext_for(path: str, st: dict, routes: dict) -> tuple:
    """Asset extensions admitted for this file: by the kinds it was written under; a write recorded before kinds were
    stored falls back to the current kinds. Keyed on the current kinds, a logo written under brand dropped out on the
    next web prompt, and a screenshot written during web work was judged once brand arrived."""
    at_write = st.get("write_kinds", {}).get(canon(path))
    return extra_ext(st.get("kinds", []) if at_write is None else at_write, routes)


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


SHELL_TOOLS = ("Bash", "PowerShell")
# A visual path named in a shell command (heredoc, Set-Content, Out-File, cp, a generator's --out). The Stop gate used
# to collect writes only from Write/Edit, so a page written through the shell skipped Taste and the review entirely
# (V-DSR-SHELL-*, 2026-11-22). A path is a candidate here; judge() admits it only if the file changed after the command.
# Linear by construction: one split into tokens, then an anchored match per token. A single unbounded pattern over
# the whole command backtracked quadratically on a long run with no dot (an inline base64 image in a heredoc):
# measured 6.04 s at 20 KB and 18.31 s at 40 KB, against the Stop chain's 8 s kill (review of S2, M1).
_SHELL_SPLIT_RX = re.compile(r"""[\s"'`<>|;&()=,]+""")
# svg/png are candidates here too; judge() admits them only in a session whose kinds list them (brand, extra_ext).
_SHELL_TOKEN_RX = re.compile(r"""(.{0,1000}?\.(?:html?|css|scss|sass|tsx|jsx|vue|svelte|svg|png))(?![\w.])""", re.I)
_MSYS_DRIVE_RX = re.compile(r"^/(?:mnt/)?([A-Za-z])(?=/)")
SHELL_TOKEN_MAX = 1024
SHELL_MTIME_SLACK_S = 2.0
# B-4 (benchmark 2026-11-22): `$out\p1.png`, `assets\*.svg`, `%TEMP%\a.html`, `{out}/p{i}.png` were recorded and
# resolved under the project root. A token still carrying a variable, a glob or a template field is not a literal
# path; the file it becomes is reached by script_outputs (mtime) instead. `[` stays allowed: app/[slug]/page.tsx is real.
_SHELL_NONLITERAL_RX = re.compile(r"[$*?{}%]")


def shell_paths(cmd: str) -> list:
    """Literal visual-extension paths named in a shell command, in order. Tokens longer than SHELL_TOKEN_MAX, and
    tokens still carrying a variable, glob or template field, are not paths."""
    out = []
    for tok in _SHELL_SPLIT_RX.split(cmd or ""):
        if not tok or len(tok) > SHELL_TOKEN_MAX:
            continue
        m = _SHELL_TOKEN_RX.match(tok)
        if m and _SHELL_NONLITERAL_RX.search(m.group(1)):
            continue
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def _row_epoch(row: dict) -> float | None:
    ts = row.get("timestamp")
    if not isinstance(ts, str) or not ts:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


# `ccf.cli generate <project>` writes <project>/.ccf/images/<id>.png from inside its process (modules/ccf/cli.py
# _keep_artifact): the command names no .png, so CCF's own outputs never reached the gate (review of bb95f710, M2).
_CCF_GENERATE_RX = re.compile(r"""ccf[./\\]cli(?:\.py)?["']?\s+generate\s+["']?([^\s"';&|]+)""", re.I)


def ccf_outputs(cmd: str, base: str) -> list:
    """The images a `ccf.cli generate` command can have written: every .png in each named project's .ccf/images."""
    out = []
    for proj in _CCF_GENERATE_RX.findall(cmd or ""):
        d = os.path.join(proj if os.path.isabs(proj) or not base else os.path.join(base, proj), ".ccf", "images")
        try:
            out += [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.lower().endswith(".png")]
        except OSError:
            continue
    return out


# A script the session runs writes its outputs from inside its own process: in the cross-sector benchmark
# (2026-11-22, B-3) `python build.py` wrote a brand kit's ten logo SVGs, the command named none of them, and only the
# favicon (named by another command) got its framed light/dark review. In a session whose kinds judge extra assets
# (brand), every such asset under the command's cwd that changed after the command is a candidate; shell_written's
# mtime rule admits it. The walk is bounded for the Stop chain's 8 s budget; an untimed command enrols nothing (it
# would pull every logo in the tree into the review).
_SCRIPT_RUN_RX = re.compile(
    r"""(?:^|[\s;&|(])(?:py(?:thon[\d.]*)?(?:\.exe)?|node|deno|bun|ruby|pwsh|powershell|bash|sh)\b[^;&|\n]*?"""
    r"""(?:\s-m\s+[\w.]+|\.(?:py|m?js|ts|rb|ps1|sh)\b)""", re.I)
_SCRIPT_SKIP_DIRS = {".git", "node_modules", ".claude", "__pycache__", ".venv", "venv"}
SCRIPT_SCAN_MAX_FILES = 5000


def script_outputs(cmd: str, base: str, exts: tuple, since: float | None) -> list:
    """Assets with one of `exts` under `base` changed at/after `since`, when `cmd` runs a script. [] otherwise."""
    if not exts or not base or since is None or not _SCRIPT_RUN_RX.search(cmd or "") or not os.path.isdir(base):
        return []
    out, seen = [], 0
    for root, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if x not in _SCRIPT_SKIP_DIRS]
        for f in files:
            seen += 1
            if seen > SCRIPT_SCAN_MAX_FILES:
                return out
            if os.path.splitext(f)[1].lower() in exts:
                p = os.path.join(root, f)
                try:
                    if os.path.getmtime(p) >= since - SHELL_MTIME_SLACK_S:
                        out.append(p)
                except OSError:
                    continue
    return out


def _scan_shell(row: dict, inp: dict, st: dict) -> None:
    cmd = str(inp.get("command") or "")
    base = str(row.get("cwd") or "")
    when = _row_epoch(row)
    made = []
    if _SCRIPT_RUN_RX.search(cmd) and when is not None:
        made = script_outputs(cmd, base, extra_ext(st.get("kinds", []), load_routes()), when)
    for p in shell_paths(cmd) + ccf_outputs(cmd, base) + made:
        if os.name == "nt":       # Git Bash names C:\x as /c/x (or /mnt/c/x); isabs() says True, canon() makes c:\c\x
            p = _MSYS_DRIVE_RX.sub(lambda m: m.group(1) + ":", p)
        if not os.path.isabs(p) and base:
            p = os.path.join(base, p)
        c = canon(p)
        # The mtime is read NOW (the first Stop after the command), not at every later Stop: a page this session only
        # read must not become its work when another pane or the Owner saves it afterwards (review of S2, M3).
        try:
            seen = os.path.getmtime(c)
        except OSError:
            seen = None
        if not any(x[0] == c and x[1] == when for x in st["shell_writes"]):
            st["shell_writes"].append([c, when, seen])
        _note_kinds(st, c)


def shell_written(st: dict) -> list:
    """Shell-named visual paths whose file had changed at or after the command when the command was scanned. A command
    with no timestamp is admitted if the file existed (a gate that cannot place a write in time judges it rather than
    letting it pass). Rows from before the snapshot existed ([path, when]) are read against the current mtime."""
    out = []
    for row in st.get("shell_writes", []):
        p, when = row[0], row[1]
        seen = row[2] if len(row) > 2 else None
        if len(row) <= 2:
            try:
                seen = os.path.getmtime(p)
            except OSError:
                seen = None
        if seen is None or not os.path.isfile(p):
            continue
        if (when is None or seen >= when - SHELL_MTIME_SLACK_S) and p not in out:
            out.append(p)
    return out


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
            path = str(inp.get("file_path") or inp.get("notebook_path") or "")
            _add(st["writes"], path)
            _note_kinds(st, path)
        elif c.get("name") in SHELL_TOOLS:
            _scan_shell(row, inp, st)


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


def latest_review(path: str) -> dict | None:
    """The last reviews.jsonl row naming this file, whatever bytes it judged (None if never reviewed)."""
    last = None
    for r in read_rows("reviews.jsonl"):
        if path in (r.get("files") or {}):
            last = r
    return last


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
    assets = set()   # admitted only as an asset: judged by the kinds it was written under (L1)
    for w in list(st.get("writes", [])) + shell_written(st):
        visual = is_visual(w, routes)
        asset = not visual and os.path.splitext(w or "")[1].lower() in asset_ext_for(w, st, routes)
        if w and (visual or asset) and os.path.isfile(w) and inside(w, cwd) and canon(w) not in files:
            files.append(canon(w))
            if asset:
                assets.add(canon(w))
    res = {"files": [], "kinds": [], "problems": [], "waived": {}}
    now = st.get("kinds", [])
    judged = [(f, kinds_for(f, st.get("write_kinds", {}).get(f, now) if f in assets else now, routes)) for f in files]
    judged = [(f, k) for f, k in judged if k is not None]
    res["files"] = [f for f, _ in judged]
    if not judged:
        return res
    for _, k in judged:
        res["kinds"] += [x for x in k if x not in res["kinds"]]
    problems, required, ok = [], [], None
    for f, k in judged:
        pol = policy(k, routes)
        required += [x for x in pol["required"] if x not in required]
        if pol["taste"] and f.endswith(HTML_EXT):
            from modules.cdio import taste
            rep = taste.lint(f, site_root=cwd)
            for v in rep.verdicts:
                if v.criterion in rep.blocking:
                    problems.append({"check": "design-taste", "file": f, "key": v.criterion,
                                     "detail": "%s: %s" % (v.criterion, v.observed)})
        if pol["review"]:
            ok = approved() if ok is None else ok
            h = sha256(f)
            if h not in ok.get(f, set()):
                p = {"check": "design-review", "file": f, "key": "",
                     "detail": "no recorded cdio-reviewer APPROVE for these bytes (sha %s)" % h[:12]}
                last = latest_review(f)
                if last is not None and not last.get("is_done"):
                    p["recorded"] = True
                    p["detail"] += "; the last recorded review of this file is %s %s%s: fix what it names, then " \
                                   "review again" % (last.get("verdict"), last.get("score"),
                                                     " (refused: %s)" % "; ".join(last["refused"]) if last.get("refused") else "")
                    failed = last.get("failed") or [[c, "critical", ""] for c in last.get("critical") or []]
                    order = {"critical": 0, "major": 1, "minor": 2}
                    failed = sorted(failed, key=lambda x: order.get(x[1], 3))
                    if failed:
                        p["detail"] += "; failed: " + "; ".join(
                            "%s [%s]%s" % (c, sev, ": " + obs if obs else "") for c, sev, obs in failed[:8])
                        if len(failed) > 8:
                            p["detail"] += "; +%d more" % (len(failed) - 8)
                problems.append(p)
    used = {skill_key(s) for s in st.get("skills", [])}
    missing = [s for s in required if skill_key(s) not in used]
    if missing:
        problems.append({"check": "design-skills", "file": "", "key": ",".join(missing),
                         "detail": "not loaded this session: " + ", ".join(missing)})
    res["waived"] = {k: v for k, v in na.items() if k in CHECKS}
    res["problems"] = [p for p in problems if p["check"] not in res["waived"]]
    return res


def ux_findings(waiting=None, disabled=None, targets=None) -> dict:
    """Declared-record UX contract findings (BCAP2-05, modules/cdio/ux_contracts.py). Absent input -> absent key, never a pass."""
    from modules.cdio import ux_contracts as ux
    res = {}
    if waiting is not None:
        res["waiting"] = ux.waiting_pattern(**waiting)
    if disabled is not None:
        res["disabled"] = ux.check_disabled_control(disabled)
    if targets is not None:
        res["targets"] = ux.check_hit_targets(targets)
    return res
