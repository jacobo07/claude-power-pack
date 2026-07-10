#!/usr/bin/env python3
"""rename_sessions.py -- safe retroactive session rename via inline custom-title append.

MECHANISM (forensically verified -- see PR-TRANSCRIPT-RENAME-SAFETY-001):
  Claude Code's /resume picker renders the LATEST
    {"type":"custom-title","customTitle":"<name>","sessionId":"<uuid>"}
  record found in <proj>/<uuid>.jsonl. The .jsonl is an APPEND-ONLY event log;
  the harness never rewrites prior lines. Setting a display name = appending one
  custom-title line. This is exactly what the Ctrl+R rename does, and exactly what
  hooks/mark-live-session.js already does in production (the "voltage" live marker).
  There is NO separate metadata store -- the name lives inline in the transcript.

SAFETY INVARIANT (prefix-byte-identity, NOT whole-file hash):
  A whole-file sha256 CANNOT stay identical after an append -- and would be
  impossible for Claude Code's OWN Ctrl+R rename too, since it appends as well.
  The real, provable guarantee is:
    * the ORIGINAL N bytes remain byte-identical after the write (append never
      touches prior bytes),
    * the file grew by exactly one valid custom-title line,
    * the appended tail decodes to precisely the expected JSON object.
  The tool records sha256(original_bytes[0:N]) BEFORE, then verifies AFTER:
    len(after) == N + len(line)  AND  sha256(after[0:N]) == pre  AND  after[N:] == line
  Any deviation -> truncate the file back to N (full revert) and report FAIL.
  Message content and transcript structure are never modified.

NAMING SOURCE (priority ladder -- see PR-SESSION-NAME-FORMAT-001, 2026-07-06):
  A display name is derived from the first available of:
    1. ai-title   -- the clean Claude-generated summary already embedded in the
                     transcript ({"type":"ai-title","aiTitle":"..."}). Used verbatim
                     (whitespace-normalised only).
    2. first-user -- the Owner's first message (real sessions only), run through
                     clean_prompt() which strips mode/metadata scaffolding (MODO:,
                     PREFLIGHT:, EXECUTION MODE, CONTRATO DE REALIDAD:, ROI:,
                     box-drawing rules, shell command lines, PANE/SESIÓN headers,
                     interrupt markers) and returns the first substantive fragment.
    3. SUB label  -- for sub-sessions (SERP research agents, local-command runs,
                     slash-command launches) the name is "SUB - <what it is>" so the
                     picker makes clear it is a tool-spawned session, not Owner work:
                       "SUB - SERP: <query>", "SUB - /<command>", "SUB - <branch>".
    4. git branch -- a genuine no-title session with a non-default branch falls back
                     to that branch name.
  NO repo prefix is added (the picker already groups by project). The legacy
  "<repo> — " prefix is treated as reclaimable old-format residue (see below).

RECLAIM (which titles may be overwritten):
  A session is renamed ONLY when its current effective custom-title is reclaimable:
    * absent / empty,
    * a bare hex UUID or 8-hex string (the mark-live-session.js fallback),
    * a bare repo token (e.g. "TUA-X"),
    * the legacy "<repo> <dash> ..." prefix (any Unicode dash variant), or
    * a mode/metadata-scaffold prefix (MODO:, PREFLIGHT:, "You are an expert",
      "Given the following", "Generate a list of", Caveat:, ...).
  A genuine Owner Ctrl+R name (and a clean ai-title name already applied) is NEVER
  overwritten. Sessions with no derivable name are left untouched.

EXCLUSIONS:
  * mislocated copies -- a transcript whose recorded cwd does NOT munge to its
    physical project dir (a resumed-from-elsewhere fork),
  * sessions that already carry a real (non-reclaimable) custom name,
  * sessions with no derivable name at all,
  * the currently-running session(s) via --skip-sid / env PP_EVT_SID.

Encoding: writes are BINARY appends of UTF-8 (no BOM), LF terminator, no-space
  separators -- byte-compatible with Node's JSON.stringify output in the harness.

Usage:
  python tools/rename_sessions.py --dry-run                # this repo only, writes nothing
  python tools/rename_sessions.py --all --dry-run          # every repo, writes nothing
  python tools/rename_sessions.py --all --apply            # every repo, waves per dir, verified
  optional:
    --repo-prefix        prepend "<repo> — " to each name (default off: picker is per-project)
    --project <dir>      operate on one specific <proj> dir (default: this repo's project dir)
    --repo <name>        with --all: restrict to project dirs whose repo leaf matches (substring)
    --skip-sid <uuid>    never touch this session id (repeatable); also honours env PP_EVT_SID
    --sample <n>         print at most N rename rows per group (0 = all; default 0)
    --verbose            show skipped rows too
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROJECTS_ROOT = HOME / ".claude" / "projects"
DEFAULT_PROJECT = PROJECTS_ROOT / "C--Users-User--claude-skills-claude-power-pack"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
HEX8_RE = re.compile(r"^[0-9a-fA-F]{8}$")
NONALNUM_RE = re.compile(r"[^a-zA-Z0-9]")   # cwd -> project-dir encoding (same as harness)
LIVE_PREFIX = "⚡ "   # voltage sign + space -- the mark-live-session.js live marker
SUB_LABEL = "SUB - "  # prefix that marks a tool-spawned sub-session in the picker
MAX_LABEL = 60        # picker has room for ~60 chars (was 50)
HEAD_LINE_CAP = 2000      # bounded head scan for ai-title / first-user / cwd / branch
TAIL_BYTES = 64 * 1024    # bounded tail scan for the LATEST custom-title
CWD_RE = re.compile(r'"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"')
BRANCH_RE = re.compile(r'"gitBranch"\s*:\s*"((?:[^"\\]|\\.)*)"')
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

DEFAULT_BRANCHES = {"main", "master", "head", "detached", ""}

# Unicode dash variants (hyphen, non-breaking hyphen, figure/en/em dash, minus).
DASHES = {0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0x002D}

# Decoration chars that make a "rule" / separator line carry no information.
DECOR_CHARS = set("═─━—–‑-=_*·•~▪▶►◆●→⇒»«│|<>#/\\.: ")

# Whole-line scaffolding prefixes -> the line is metadata, skip it entirely.
SKIP_LINE_RE = re.compile(
    r"^(MODO\s*[:=]|PREFLIGHT\b|EXECUTION\s+MODE\b|ULTRA[- ]?PLAN(\s+MODE)?\b|"
    r"CONTRATO\s+DE\s+REALIDAD\b|ROI\s*[:=]|CONSTRAINTS?\s*[:=]|DONE[\s-]?GATE\b|"
    r"PLAN\s+INLINE\b|PASO\s|STOP\b|Caveat\s*:|Given\s+the\s+following\b|"
    r"You\s+are\s+an?\s+(are\s+an?\s+)?(expert|insightful)\b|"
    r"Generate\s+a\s+list\s+of\b|Contents\s+from\s+a\s+SERP\b|"
    r"Request\s+interrupted\b|"
    r"System\s*:|Human\s*:|Assistant\s*:)",
    re.I,
)

# "MODO: <mode> (<real intent>)" -> the parenthetical is the substantive part.
MODO_PAREN_RE = re.compile(r"MODO\s*[:=].*?\((.+?)(?:\)|$)", re.I | re.S)

# Status / anchor preamble lines that precede the real objective in the standard
# loop-session template (MODO -> CONTRATO -> Prod:/Pane status -> anchors ->
# OBJECTIVE). These describe deploy state, not the task -> skip to reach the
# objective paragraph below (PR-NAME-OBJECTIVE-001, Owner-chosen 2026-07-10).
STATUS_LINE_RE = re.compile(
    r"^(Prod\s*[:=]|Pane\s*\d|smoke\s+\d|KILL[\s-]?SWITCH\b|SESSION\s+ANCHOR\b|"
    r"TUAX[_A-Z0-9]*\s*[:=]|PR-[A-Z0-9-]+\s*[:\-]|HEAD\s+real\b|git\s+fetch\b|"
    r"Owner\s+dashboard\b|Operador\s+surface\b|kernel\s+v|HEAD\s+confirmad)",
    re.I,
)

# "PANE NUEVO: X", "SESIÓN: X", "SPRINT: X" -> the text after the header is the name.
HEADER_RE = re.compile(
    r"^(?:PANE(?:\s+NUEVO)?|SESI[ÓO]N|SPRINT|TAREA|TASK|FEATURE|OBJETIVO|GOAL|TARGET)"
    r"\s*[:=]\s*(.+)$",
    re.I,
)

# Shell-command-looking line (a PREFLIGHT command, a git invocation, etc).
CMD_RE = re.compile(
    r"^(git|python3?|py|node|npm|pnpm|corepack|mix|gh|cd|ls|cat|grep|rg|bash|sh|"
    r"pwsh|powershell|curl|wget|docker|kubectl|\./|\$|&)\b|&&|\|\|",
    re.I,
)

# Sub-session content extractors.
CMD_NAME_RE = re.compile(r"<command-name>\s*([^<>\n]+?)\s*</command-name>", re.I)
SERP_Q_RE = re.compile(r"for the query\s+(.+?)(?:[.\n]|$)", re.I)

# First-user markers that identify a genuine sub-session (research / SERP agent).
SUB_PREFIXES = (
    "expert and insightful researcher",
    "contents from a serp search",
    "generate a list of serp",
    "generate a list of search queries",
    "given the following prompt from the user",
    "generated by the user while running local commands",
    "running local commands",
)

# Empty session-control built-ins -- these produce throwaway stub sessions with no
# work; they are left in their hex fallback rather than labelled (Owner decision,
# 2026-07-06). A SERP / research / content command is NOT in this set.
STUB_COMMANDS = frozenset({"clear", "login", "logout", "compact", "exit", "quit", "resume"})

# Preferred wave order for --apply. Repos not listed come after, alphabetically.
REPO_ORDER = (
    "claude-power-pack",
    "TUA-X",
    "InfinityOps",
    "KobiiCraft",
    "GEO-audit",
    "moneymaker",
)


# --------------------------------------------------------------------------- #
# Text cleaning
# --------------------------------------------------------------------------- #
def _clean(text: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub(" ", text)).strip()


def _norm_dash(s: str) -> str:
    return "".join("-" if ord(c) in DASHES else c for c in s)


def _is_separator(line: str) -> bool:
    s = line.strip()
    return bool(s) and all(ch in DECOR_CHARS for ch in s)


def _has_substance(s: str) -> bool:
    s = s.strip()
    return len(s) >= 4 and sum(ch.isalpha() for ch in s) >= 4


def _strip_decor(line: str) -> str:
    # Trim leading/trailing decoration so "═══ PANE NUEVO: X" -> "PANE NUEVO: X".
    return line.strip().strip("".join(DECOR_CHARS)).strip()


def clean_prompt(text: str) -> str:
    """Return the first substantive fragment of a first-user message, stripping
    mode/metadata scaffolding, separators, shell commands and section headers.
    Operates line-by-line on the RAW (newline-preserving) text."""
    if not text:
        return ""
    text = TAG_RE.sub(" ", text)   # drop <local-command-*>, <command-name>, etc.
    for raw in text.replace("\r", "").split("\n")[:60]:
        line = raw.strip()
        if not line or _is_separator(line):
            continue
        # A wholly-bracketed system marker like "[Request interrupted by user]".
        if line.startswith("[") and line.endswith("]"):
            continue
        # A MODO line carrying a parenthetical real-intent -> use the parenthetical.
        mp = MODO_PAREN_RE.search(line)
        if mp:
            inner = _clean(mp.group(1)).strip(" .-—–()")
            if _has_substance(inner):
                return inner
            continue
        line = _strip_decor(line)
        if not line or _is_separator(line):
            continue
        if SKIP_LINE_RE.match(line):
            continue
        if STATUS_LINE_RE.match(line):
            continue                       # deploy/status/anchor preamble -> keep looking
        if CMD_RE.search(line):
            continue
        hm = HEADER_RE.match(line)
        if hm:
            inner = _clean(hm.group(1)).strip(" .-—–()")
            if _has_substance(inner):
                return inner
            continue
        if _has_substance(line):
            return _clean(line)
    return ""


def sub_name(first_user: str, cmd_name: str, branch: str) -> str:
    """Build a "SUB - ..." label that makes clear what kind of tool-spawned session
    this is: a slash-command launch, a SERP research agent, a local command, or
    (last resort) the branch it ran on."""
    if cmd_name:
        return f"{SUB_LABEL}/{cmd_name.strip().lstrip('/')}"
    low = _clean(first_user).lower()
    if "serp" in low or "search quer" in low:
        q = SERP_Q_RE.search(first_user)
        if q:
            query = _clean(q.group(1))
            if _has_substance(query):
                return f"{SUB_LABEL}SERP: {query}"
        return f"{SUB_LABEL}SERP research"
    if "expert and insightful researcher" in low or "given the following prompt" in low:
        return f"{SUB_LABEL}research agent"
    if "running local commands" in low:
        return f"{SUB_LABEL}local command"
    if branch and branch.strip().lower() not in DEFAULT_BRANCHES:
        return f"{SUB_LABEL}{branch.strip()}"
    return f"{SUB_LABEL}session"


# Genuine tool-spawned research/SERP agents -- their FIRST real message IS the
# agent instruction, so they keep a "SUB - ..." label. Distinct from the local-
# command CAVEAT wrapper below, which merely precedes real Owner work.
RESEARCH_SUB_PREFIXES = (
    "expert and insightful researcher",
    "contents from a serp search",
    "generate a list of serp",
    "generate a list of search queries",
    "given the following prompt from the user",
)
WRAPPER_RE = re.compile(r"messages below were generated by the user", re.I)


def _is_wrapper_or_command(text: str) -> bool:
    """True when a leading transcript message is NOT the session's identity and
    must be skipped when naming a session that merely BEGAN with a command
    (see PR-STUB-REAL-WORK-001). These precede the real Owner prompt:
      * a slash-command invocation -- stored as '<command-name>clear</command-name>
        <command-message>...' scaffolding (NOT a leading '/'), or a bare '/clear'
        line in older transcripts,
      * local-command stdout/stderr scaffolding,
      * the caveat wrapper ('...generated by the user while running local commands'),
      * a system marker ('[Request interrupted by user]')."""
    st = text.strip()
    if not st:
        return True
    if ("<command-name>" in st or "<local-command-stdout>" in st
            or "<local-command-stderr>" in st):
        return True                       # command invocation / output scaffolding
    c = _clean(text)
    if not c:
        return True
    low = c.lower()
    if low.startswith("caveat:") or WRAPPER_RE.search(low):
        return True
    if st.startswith("[") and st.endswith("]"):
        return True                       # [Request interrupted by user]
    first_line = st.splitlines()[0]
    if first_line.startswith("/") and len(first_line) > 1:
        tok = first_line[1:].split()[0].lower()
        if tok in STUB_COMMANDS:
            return True                   # bare "/clear", "/compact", "/login" ...
    return False


def first_real_user(user_msgs: list[str]) -> str:
    """First user message that carries genuine content (an Owner prompt or an
    agent instruction), skipping the caveat wrapper / bare control command /
    interrupt marker. Returns RAW text so clean_prompt can work line-wise."""
    for t in user_msgs:
        if not _is_wrapper_or_command(t):
            return t
    return ""


# --------------------------------------------------------------------------- #
# Scanning
# --------------------------------------------------------------------------- #
def _extract_user_text(obj: dict) -> str:
    msg = obj.get("message") or {}
    if msg.get("role") != "user":
        return ""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text") or ""
    return ""


def scan_session(path: Path) -> dict:
    """Bounded scan: head for ai-title / first-user (RAW) / cwd / branch /
    command-name, tail for the latest custom-title."""
    ai = ""
    user_msgs: list[str] = []   # first several RAW user messages (newlines preserved)
    cwd = ""
    branch = ""
    cmd_name = ""
    n = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                n += 1
                if n > HEAD_LINE_CAP:
                    break
                if not cwd:
                    m = CWD_RE.search(line)
                    if m:
                        cwd = m.group(1).replace("\\\\", "\\")
                if not branch:
                    mb = BRANCH_RE.search(line)
                    if mb:
                        branch = mb.group(1).replace("\\\\", "\\")
                if not cmd_name and "<command-name>" in line:
                    mc = CMD_NAME_RE.search(line)
                    if mc:
                        cmd_name = mc.group(1)
                if '"ai-title"' in line and not ai:
                    try:
                        o = json.loads(line)
                    except Exception:
                        o = None
                    if o and o.get("type") == "ai-title" and isinstance(o.get("aiTitle"), str):
                        ai = o["aiTitle"]
                elif '"type":"user"' in line and len(user_msgs) < 6:
                    try:
                        o = json.loads(line)
                    except Exception:
                        o = None
                    if o and o.get("type") == "user":
                        txt = _extract_user_text(o)
                        if txt:
                            user_msgs.append(txt)
                if ai and len(user_msgs) >= 6 and cwd and branch and cmd_name:
                    break
    except OSError:
        pass

    last_custom = None
    try:
        size = path.stat().st_size
        start = max(0, size - TAIL_BYTES)
        with open(path, "rb") as fh:
            fh.seek(start)
            tail = fh.read()
        for raw in tail.decode("utf-8", errors="replace").split("\n"):
            if '"custom-title"' not in raw:
                continue
            try:
                o = json.loads(raw)
            except Exception:
                continue
            if o.get("type") == "custom-title" and isinstance(o.get("customTitle"), str):
                last_custom = o["customTitle"]   # keep scanning -> ends on the last
    except OSError:
        pass

    first_user = user_msgs[0] if user_msgs else ""
    low = _clean(first_user).lower()
    is_sub = bool(cmd_name) or (any(p in low for p in SUB_PREFIXES) if low else False)
    return {"ai": ai, "first_user": first_user, "user_msgs": user_msgs,
            "cwd": cwd, "branch": branch, "cmd_name": cmd_name,
            "last_custom": last_custom, "is_sub": is_sub}


def effective_base(custom_raw: str | None) -> str:
    if custom_raw is None:
        return ""
    return custom_raw[len(LIVE_PREFIX):] if custom_raw.startswith(LIVE_PREFIX) else custom_raw


def is_truncated_ai_title(base: str, ai: str) -> bool:
    """True when `base` is OUR own ai-title name applied under an earlier, shorter
    truncation limit (MAX_LABEL was 50, now 60): base minus its trailing ellipsis
    is a prefix of the full ai-title, but shorter than it. Refreshing yields the
    full ideal ai-title (PR-AITITLE-DIRECT-001). A human Ctrl+R name would not be
    an exact prefix of the auto-generated title. Guard len>=8 against coincidence."""
    if not ai:
        return False
    core = base.strip().rstrip("…").rstrip(".").rstrip()
    if len(core) < 8:
        return False
    ai_clean = _clean(ai)
    return ai_clean.startswith(core) and len(ai_clean) > len(core)


def is_reclaimable_title(base: str, repo: str) -> bool:
    """True when the current title is machine-derived / legacy residue and may be
    overwritten: empty, a bare 8-hex / full UUID, a bare repo token, the legacy
    '<repo> <dash> ...' prefix, or a mode/metadata scaffold prefix. A genuine
    human Ctrl+R name (and a clean ai-title name) returns False. A name we ourselves
    apply -- a "SUB - ..." label -- is reclaimable so re-runs can refine it."""
    b = base.strip()
    if not b:
        return True
    if HEX8_RE.match(b) or UUID_RE.match(b):
        return True
    if b.startswith(SUB_LABEL):
        return True                           # our own sub label -> refine on re-run
    nb = _norm_dash(b)
    rl = _norm_dash(repo.strip()).lower()
    nbl = nb.lower()
    if rl:
        if nbl == rl:
            return True                       # bare repo token, e.g. "TUA-X"
        if nbl.startswith(rl + " -"):
            return True                       # legacy "<repo> — ..." prefix
    if SKIP_LINE_RE.match(nb):
        return True                           # mode/metadata scaffold leaked in
    return False


def is_canonical_location(proj_dir: Path, cwd: str) -> bool:
    """A transcript belongs in <proj_dir> iff its recorded cwd munges to that dir
    name (the harness encodes cwd -> dir by replacing every non-alnum with '-').
    No cwd recorded -> cannot disprove -> treat as canonical (best effort)."""
    if not cwd:
        return True
    return NONALNUM_RE.sub("-", cwd) == proj_dir.name


def repo_of(proj_dir: Path, cwd: str) -> str:
    if cwd:
        leaf = cwd.replace("/", "\\").rstrip("\\").split("\\")[-1]
        if leaf:
            return leaf
    return proj_dir.name.split("-")[-1] or proj_dir.name


def derive_name(s: dict) -> tuple[str, str]:
    """Pick a display name via the priority ladder. Returns (name, source).

    The first-user step looks past the local-command CAVEAT wrapper and the bare
    control command to the first REAL user message. This recovers sessions that
    merely BEGAN with /clear or /compact but then contain hundreds of real Owner
    turns -- previously mis-classified as empty stubs and stranded as hex
    (PR-STUB-REAL-WORK-001). A genuine research/SERP sub-agent -- whose first
    real message IS the agent instruction -- still gets a "SUB - ..." label."""
    ai = s["ai"]
    if ai:
        c = _clean(ai)
        if _has_substance(c):
            return c, "ai-title"
    user_msgs = s.get("user_msgs") or ([s["first_user"]] if s["first_user"] else [])
    real_raw = first_real_user(user_msgs)
    real_low = _clean(real_raw).lower()
    # genuine tool-spawned research/SERP agent -> SUB label (instruction = identity)
    if real_low and any(p in real_low for p in RESEARCH_SUB_PREFIXES):
        return sub_name(real_raw, "", s["branch"]), "sub"
    # real Owner prompt (covers /clear-/compact-initiated real sessions)
    if real_raw:
        c = clean_prompt(real_raw)
        if _has_substance(c):
            return c, "first-user"
    # a non-stub slash-command launch keeps its "SUB - /cmd" label
    cmd = s["cmd_name"].strip().lstrip("/").lower()
    if s["cmd_name"] and cmd not in STUB_COMMANDS:
        return sub_name(s["first_user"], s["cmd_name"], s["branch"]), "sub"
    branch = s["branch"]
    if branch and branch.strip().lower() not in DEFAULT_BRANCHES:
        return branch.strip(), "branch"
    return "", ""   # genuinely empty session-control stub -> leave in hex fallback


def make_title(source: str, repo: str, repo_prefix: bool) -> str:
    label = source.strip()
    if len(label) > MAX_LABEL:
        label = label[: MAX_LABEL - 1].rstrip() + "…"
    return f"{repo} — {label}" if repo_prefix else label


def build_record(uuid: str, title: str) -> bytes:
    obj = {"type": "custom-title", "customTitle": title, "sessionId": uuid}
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


# --------------------------------------------------------------------------- #
# Planning
# --------------------------------------------------------------------------- #
def plan_project(proj_dir: Path, repo_prefix: bool, skip_sids: set[str],
                 reclaim_manifest: dict | None = None) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(proj_dir.glob("*.jsonl")):
        uuid = path.stem
        if not UUID_RE.match(uuid):
            continue
        s = scan_session(path)
        base = effective_base(s["last_custom"])
        repo = repo_of(proj_dir, s["cwd"])
        # A stored title equal to its reclaim-manifest entry is a name WE generated
        # in a prior run -> reclaimable so an improved format can overwrite it. A
        # human Ctrl+R name (stored title != our derivation) is NOT in the manifest
        # match and stays protected.
        ours = ((bool(reclaim_manifest) and reclaim_manifest.get(uuid) == base)
                or is_truncated_ai_title(base, s["ai"]))
        row = {
            "uuid": uuid, "path": path, "repo": repo, "proj": proj_dir.name,
            "current": base if base else "(none)",
            "new": "", "action": "", "source": "",
        }
        if uuid.lower() in skip_sids:
            row["action"] = "SKIP (running/protected)"
        elif not is_canonical_location(proj_dir, s["cwd"]):
            row["action"] = "SKIP (mislocated copy)"
        elif not (is_reclaimable_title(base, repo) or ours):
            row["action"] = "SKIP (has custom name)"
        else:
            name, src = derive_name(s)
            if not name:
                row["action"] = "SKIP (no derivable name)"
            elif make_title(name, repo, repo_prefix) == base:
                row["action"] = "SKIP (already named)"
            else:
                row["new"] = make_title(name, repo, repo_prefix)
                row["source"] = src
                row["action"] = "RENAME"
        rows.append(row)
    return rows


def iter_project_dirs() -> list[Path]:
    try:
        entries = sorted(p for p in PROJECTS_ROOT.iterdir() if p.is_dir())
    except OSError:
        return []
    return [p for p in entries if p.name != "_empty_shells"]


def repo_sort_key(repo: str) -> tuple[int, str]:
    low = repo.lower()
    for i, name in enumerate(REPO_ORDER):
        if name.lower() in low:
            return (i, low)
    return (len(REPO_ORDER), low)


# --------------------------------------------------------------------------- #
# Applying
# --------------------------------------------------------------------------- #
def apply_one(path: Path, uuid: str, title: str) -> tuple[bool, str]:
    """Append + verify prefix-byte-identity. Auto-revert on any mismatch."""
    try:
        original = path.read_bytes()
    except OSError as e:
        return False, f"read failed: {e}"
    n = len(original)
    pre = hashlib.sha256(original).hexdigest()
    line = build_record(uuid, title)
    try:
        with open(path, "ab") as fh:   # binary append: no CRLF translation, no BOM
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
    except OSError as e:
        return False, f"append failed: {e}"
    try:
        after = path.read_bytes()
    except OSError as e:
        return False, f"reread failed: {e}"
    ok = (
        len(after) == n + len(line)
        and hashlib.sha256(after[:n]).hexdigest() == pre
        and after[n:] == line
    )
    if ok:
        return True, f"prefix sha256 intact ({pre[:12]}...), +{len(line)}B"
    try:
        with open(path, "r+b") as fh:
            fh.truncate(n)
        return False, "VERIFY FAILED -> reverted (truncated to original size)"
    except OSError as e:
        return False, f"VERIFY FAILED and revert errored: {e}"


# --------------------------------------------------------------------------- #
# Reporting / CLI
# --------------------------------------------------------------------------- #
def summarize(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    return counts


def source_breakdown(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        if r["action"] == "RENAME":
            counts[r["source"]] = counts.get(r["source"], 0) + 1
    return counts


def print_group(label: str, proj_name: str, rows: list[dict], verbose: bool, sample: int) -> None:
    to_rename = [r for r in rows if r["action"] == "RENAME"]
    print(f"\n=== {label}  [{proj_name}]  ({len(rows)} sessions, {len(to_rename)} to rename) ===")
    shown = rows if verbose else to_rename
    if sample and not verbose:
        shown = shown[:sample]
    for r in shown:
        if r["action"] == "RENAME":
            print(f"  [{r['uuid'][:8]}] ({r['source']:<10}) {r['current'][:22]:<22} -> {r['new']}")
        else:
            print(f"  [{r['uuid'][:8]}] {r['current'][:28]:<28}  {r['action']}")
    if sample and not verbose and len(to_rename) > sample:
        print(f"  ... (+{len(to_rename) - sample} more rename rows)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe retroactive session rename (inline custom-title append).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print plan, write nothing (default)")
    g.add_argument("--apply", action="store_true", help="perform the rename with verify+revert")
    ap.add_argument("--all", dest="all_repos", action="store_true", help="operate on every project dir")
    ap.add_argument("--project", default=str(DEFAULT_PROJECT), help="single project dir (default: this repo)")
    ap.add_argument("--repo", default="", help="with --all: restrict to repos whose leaf matches (substring)")
    ap.add_argument("--repo-prefix", action="store_true", help="prepend '<repo> — ' to names")
    ap.add_argument("--skip-sid", action="append", default=[], help="never touch this session id (repeatable)")
    ap.add_argument("--sample", type=int, default=0, help="print at most N rename rows per group (0 = all)")
    ap.add_argument("--verbose", action="store_true", help="show skipped rows too")
    ap.add_argument("--reclaim-manifest", default="", help="JSON {uuid: prior-title} of names WE generated; a stored title matching its entry is reclaimable for reformat (human names are untouched)")
    args = ap.parse_args()

    skip_sids = {s.lower() for s in args.skip_sid}
    for env_key in ("PP_EVT_SID", "CLAUDE_SESSION_ID"):
        v = os.environ.get(env_key)
        if v:
            skip_sids.add(v.lower())

    reclaim_manifest: dict = {}
    if args.reclaim_manifest:
        try:
            reclaim_manifest = json.loads(Path(args.reclaim_manifest).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"ERROR: could not read --reclaim-manifest: {e}", file=sys.stderr)
            return 2

    if args.all_repos:
        proj_dirs = iter_project_dirs()
    else:
        p = Path(args.project)
        if not p.is_dir():
            print(f"ERROR: project dir not found: {p}", file=sys.stderr)
            return 2
        proj_dirs = [p]

    # Plan, keeping physical-dir grouping (mislocated copies never merge across dirs).
    groups: list[dict] = []   # {proj, label, rows}
    for pd in proj_dirs:
        rows = plan_project(pd, args.repo_prefix, skip_sids, reclaim_manifest)
        if not rows:
            continue
        label = rows[0]["repo"]
        if args.repo and args.repo.lower() not in label.lower():
            continue
        groups.append({"proj": pd.name, "label": label, "rows": rows})

    groups.sort(key=lambda g: repo_sort_key(g["label"]))

    all_rows = [r for g in groups for r in g["rows"]]
    total = len(all_rows)
    to_rename = [r for r in all_rows if r["action"] == "RENAME"]
    print(f"Scope: {'ALL repos' if args.all_repos else (proj_dirs[0].name if proj_dirs else '-')}")
    print(f"Sessions scanned: {total} | to rename: {len(to_rename)} | project dirs: {len(groups)}")
    counts = summarize(all_rows)
    print("Breakdown: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    srcs = source_breakdown(all_rows)
    if srcs:
        print("Rename source: " + ", ".join(f"{k}={v}" for k, v in sorted(srcs.items())))

    for g in groups:
        print_group(g["label"], g["proj"], g["rows"], args.verbose, args.sample)

    if not args.apply:
        print(f"\nDRY-RUN. Nothing written. {len(to_rename)} session(s) would be renamed.")
        print("Re-run with --apply (waves per project dir, per-file sha256-verified, auto-revert).")
        return 0

    print("\nAPPLY (waves per project dir; a failure in a wave STOPS before the next):")
    ok_ct = fail_ct = 0
    stopped = False
    for g in groups:
        wave = [r for r in g["rows"] if r["action"] == "RENAME"]
        if not wave:
            continue
        print(f"\n--- wave: {g['label']} [{g['proj']}]  ({len(wave)} rename) ---")
        wave_fail = 0
        for r in wave:
            ok, msg = apply_one(r["path"], r["uuid"], r["new"])
            print(f"  {'OK ' if ok else 'FAIL'} [{r['uuid'][:8]}] -> {r['new']}  ({msg})")
            if ok:
                ok_ct += 1
            else:
                fail_ct += 1
                wave_fail += 1
        if wave_fail:
            print(f"  !! {wave_fail} failure(s) in this wave -> STOP (no further waves).")
            stopped = True
            break

    print(f"\nAPPLIED: {ok_ct} ok, {fail_ct} failed"
          + (" -- STOPPED early on failure." if stopped else "."))
    return 0 if fail_ct == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
