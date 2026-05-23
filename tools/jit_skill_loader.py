#!/usr/bin/env python3
"""jit_skill_loader.py — JIT Aggressive Activation (UserPromptSubmit hook).

Apollo-retrofit (2026-05-18): per-task context compression. Instead of
always force-injecting the FULL SKILL.md of a trigger-matched module, the
loader now selects a TIER from the prompt intent and injects only the
task-scoped slice:

  discovery (~80 cl100k tok) — name + first sentence of the YAML
      description. Read-ish prompts ("what is", "explain", "when to").
  summary  (~profiled)       — frontmatter + preamble + only the
      include[] ## sections of that module's TASK_PROFILE (verbose
      walkthrough / quick-ref code dumps are negative space). Build-ish
      prompts ("add", "implement", "configure", "set up"). DEFAULT.
  full      (verbatim)       — byte-identical to the pre-retrofit
      behavior (extractor bypassed). Deep prompts ("error", "failing",
      "optimi", "migrat", "review").

Modules with no explicit profile resolve to full + whole-file (the 13
vendored dirs vs 9 trigger entries reconcile here — never KeyError).

Contract (Claude Code UserPromptSubmit):
  stdin JSON {hook_event_name, prompt, cwd, session_id}
  -> stdout JSON with TOP-LEVEL `additionalContext` (verified shape:
     hook-dispatcher.js:156-166 — only PreToolUse nests it under
     hookSpecificOutput; every other event uses top-level).
  Fail-open: ANY error -> {"continue": true} (never block the prompt).

40 KB circuit breaker (BL-0068): priority fill, defer overflow.
Session-dedupe: inject a module ONCE per session; TTL 2 h prevents
permanent cross-session suppression when session_id is absent.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
UPSTREAM = PP_ROOT / "vendor" / "apollo" / "upstream"
STATE_DIR = HOME / ".claude" / "state"
LOG = HOME / ".claude" / "logs" / "jit-skill-loader.log"
# Absolute (NOT hook-cwd-relative): the hook's cwd is the user's
# arbitrary project, never the PP repo.
TELEMETRY_DIR = PP_ROOT / "vault" / "telemetry"

BUDGET_BYTES = 40_000           # BL-0068 circuit breaker (Token Austerity)
DEDUPE_TTL_SEC = 2 * 60 * 60    # 2 h — caps cross-session false-dedupe
WALK_CAP = 2000                 # hard ceiling on dirent stats
MAX_DEPTH = 4
DISCOVERY_TOK = 80              # hard cap for the discovery card
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "vendor", ".next", "out",
    "coverage", ".turbo", ".cache", "target", ".venv", "__pycache__",
}

# (name, regex over prompt+package deps, [modules], priority).
# Lower priority = filled first under the 40 KB breaker.
TRIGGERS = [
    ("graphql_ops",
     re.compile(r"\.graphql\b|\.gql\b|\bgraphql\b|\bmutation\b|\bresolver\b"
                r"|\bsubscription\b|\bquery\s+\w+\s*[({]", re.I),
     ["graphql-operations", "graphql-schema"], 0),
    ("apollo_client",
     re.compile(r"@apollo/client|useQuery|useMutation|useLazyQuery"
                r"|ApolloClient|ApolloProvider", re.I),
     ["apollo-client"], 1),
    ("apollo_server",
     re.compile(r"@apollo/server|apollo-server|ApolloServer", re.I),
     ["apollo-server"], 1),
    ("federation",
     re.compile(r"@apollo/subgraph|@apollo/federation|buildSubgraphSchema"
                r"|\bfederation\b|\bsupergraph\b", re.I),
     ["apollo-federation"], 2),
    ("rover",
     re.compile(r"\brover\b|supergraph\.yaml|rover\.toml", re.I),
     ["rover"], 2),
    ("connectors",
     re.compile(r"@apollo/connectors|apollo\s+connector", re.I),
     ["apollo-connectors"], 2),
    ("mcp",
     re.compile(r"apollo[-\s]mcp|@apollo/mcp", re.I),
     ["apollo-mcp-server"], 2),
    ("ios",
     re.compile(r"apollo-ios|Apollo\.framework", re.I),
     ["apollo-ios"], 3),
    ("kotlin",
     re.compile(r"apollo-kotlin|com\.apollographql", re.I),
     ["apollo-kotlin"], 3),
]

# Per-module summary profile. `include` = the level-2 `## ` headers kept
# for the summary tier (high-signal: rules/principles/patterns +
# reference pointers). Everything else is explicit negative space
# (verbose walkthroughs, quick-ref code dumps). Anchors verified against
# the actual vendored SKILL.md headers (2026-05-18). A module absent
# here -> full tier, whole file (no KeyError, behavior unchanged).
TASK_PROFILES: dict[str, dict] = {
    "graphql-operations": {
        "include": ["## Key Principles", "## Ground Rules"],
        "exclude": ["## Operation Basics", "## Quick Reference",
                    "## Reference Files"],
    },
    "graphql-schema": {
        "include": ["## Schema Design Principles", "## Key Rules",
                    "## Reference Files", "## Ground Rules"],
        "exclude": ["## Quick Reference"],
    },
    "apollo-client": {
        "include": ["## Key Rules", "## Reference Files",
                    "## Ground Rules"],
        "exclude": ["## Integration Guides", "## Quick Reference"],
    },
    "apollo-server": {
        "include": ["## Key Rules", "## Reference Files",
                    "## Ground Rules"],
        "exclude": ["## Quick Start", "## Schema Definition",
                    "## Resolvers Overview", "## Context Setup"],
    },
    "apollo-federation": {
        "include": ["## Core Directives Quick Reference",
                    "## Reference Files", "## Ground Rules"],
        "exclude": ["## Federation 2 Schema Setup", "## Key Patterns"],
    },
    "rover": {
        "include": ["## Core Commands Overview", "## Reference Files",
                    "## Common Patterns"],
        "exclude": ["## Quick Start", "## Graph Reference Format",
                    "## Subgraph Workflow", "## Supergraph Composition",
                    "## Local Development with `rover dev`"],
    },
    "apollo-connectors": {
        "include": ["## Key Rules", "## Reference Files",
                    "## Ground Rules"],
        "exclude": ["## MCP Tools", "## Process", "## Schema Template"],
    },
    "apollo-mcp-server": {
        "include": ["## Key Rules", "## Reference Files",
                    "## Common Patterns"],
        "exclude": ["## Quick Start", "## Built-in Tools",
                    "## Defining Custom Tools"],
    },
    "apollo-ios": {
        "include": ["## Key Rules", "## Process"],
        "exclude": ["## Untrusted content", "## Scripts",
                    "## Reference Files"],
    },
    "apollo-kotlin": {
        "include": ["## Key Rules"],
        "exclude": ["## Scripts", "## Process", "## Reference Files"],
    },
}

# Skeletal-tier modules (S+ 2026-05-19, Owner-decided per-module ≥40%).
# For these, the summary tier renders POINTER-ONLY: frontmatter +
# trimmed preamble + an on-demand section/reference index — anchor
# bodies are NOT reproduced verbatim (the active task profile for these
# does not need the bodies inline; the title+reference pointer is
# enough, full SKILL.md is one read away). The anchor-verbatim floor
# deliberately does NOT apply here (Owner: "el floor de anchors solo
# aplica cuando el task profile los necesita"). Modules NOT in this set
# keep the unchanged verbatim-include summary — zero regression by
# construction.
SKELETAL_MODULES = {"apollo-client", "apollo-ios", "graphql-schema",
                    "apollo-federation"}

# Tier verb taxonomy (pinned — deterministic; default = summary, NOT
# full, because full is the regression-risk default).
RX_DISCOVERY = re.compile(
    r"\bwhat\s+is\b|\bwhat'?s\b|\bexplain\b|\bwhen\s+to\b|\boverview\b"
    r"|\bshould\s+i\b|\bdifference\s+between\b|\bwhich\b", re.I)
RX_FULL = re.compile(
    r"\berror\b|\bfail(?:ing|ed|s)?\b|\bbug\b|\bbroken\b|\boptimi[sz]"
    r"|\bmigrat|\brefactor\b|\breview\b|\bdebug\b|\btroubleshoot", re.I)
RX_SUMMARY = re.compile(
    r"\badd\b|\bimplement\b|\bwrite\b|\bcreate\b|\bconfigure\b"
    r"|\bset\s*up\b|\bsetup\b|\bbuild\b|\bintegrate\b|\bwire\b", re.I)


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except Exception:
        pass


_TIKTOKEN = {"enc": None, "tried": False}


def _tok(s: str) -> int:
    """cl100k token count; lazy tiktoken, ceil(len/4) fallback."""
    if not _TIKTOKEN["tried"]:
        _TIKTOKEN["tried"] = True
        try:
            import tiktoken
            _TIKTOKEN["enc"] = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TIKTOKEN["enc"] = None
    enc = _TIKTOKEN["enc"]
    if enc is not None:
        try:
            return len(enc.encode(s))
        except Exception:
            pass
    return math.ceil(len(s) / 4)


def _package_deps(cwd: Path) -> str:
    try:
        pj = cwd / "package.json"
        if pj.is_file():
            j = json.loads(pj.read_text(encoding="utf-8"))
            keys = []
            for sec in ("dependencies", "devDependencies",
                        "peerDependencies"):
                keys += list((j.get(sec) or {}).keys())
            return " ".join(keys)
    except Exception:
        pass
    return ""


def _walk_has_graphql(cwd: Path) -> bool:
    """Bounded DFS, early-exit on FIRST .graphql/.gql."""
    stack = [(cwd, 0)]
    seen = 0
    while stack:
        d, depth = stack.pop()
        if seen > WALK_CAP:
            break
        try:
            with os.scandir(d) as it:
                for e in it:
                    seen += 1
                    if seen > WALK_CAP:
                        break
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if depth < MAX_DEPTH and e.name not in SKIP_DIRS:
                                stack.append((Path(e.path), depth + 1))
                        elif e.is_file(follow_symlinks=False) and (
                                e.name.endswith(".graphql")
                                or e.name.endswith(".gql")):
                            return True
                    except OSError:
                        continue
        except OSError:
            continue
    return False


def _match_modules(prompt: str, cwd: Path):
    deps = _package_deps(cwd)
    hay = f"{prompt}\n{deps}"
    matched: dict[str, int] = {}
    fs_checked = False
    fs_has = False
    for name, rx, mods, prio in TRIGGERS:
        hit = bool(rx.search(hay))
        if not hit and name == "graphql_ops":
            if not fs_checked:               # pay the walk at most once
                fs_has = _walk_has_graphql(cwd)
                fs_checked = True
            hit = fs_has
        if hit:
            for m in mods:
                matched[m] = min(prio, matched.get(m, 9))
    return sorted(matched, key=lambda m: (matched[m], m))


def _select_tier(prompt: str) -> str:
    """Deterministic prompt-verb -> tier. Default summary (not full)."""
    p = prompt or ""
    if RX_FULL.search(p):
        return "full"
    if RX_DISCOVERY.search(p) and not RX_SUMMARY.search(p):
        return "discovery"
    return "summary"


_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.S)


def _split_frontmatter(body: str):
    """Return (frontmatter_block_incl_fences, rest). No FM -> ('', body)."""
    m = _FM_RE.match(body)
    if not m:
        return "", body
    return body[: m.end()], body[m.end():]


def _discovery_card(body: str, module: str) -> str:
    """name + first sentence of description, hard-capped to 80 cl100k."""
    fm, _ = _split_frontmatter(body)
    name = module
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    if nm:
        name = nm.group(1).strip()
    desc = ""
    dm = re.search(r"^description:\s*(.*)$", fm, re.M)
    if dm:
        inline = dm.group(1).strip()
        if inline in (">", "|", ">-", "|-", "", ">+", "|+"):
            # YAML block scalar — gather indented continuation lines.
            lines = fm.splitlines()
            start = None
            for i, ln in enumerate(lines):
                if re.match(r"^description:\s*", ln):
                    start = i + 1
                    break
            buf = []
            if start is not None:
                for ln in lines[start:]:
                    if re.match(r"^[A-Za-z_][\w-]*:\s", ln) or ln.strip() == "---":
                        break
                    buf.append(ln.strip())
            desc = " ".join(x for x in buf if x)
        else:
            desc = inline
    # first sentence: stop at '. ' or first numbered clause "(1)".
    first = re.split(r"(?<=\.)\s+|\s*\(1\)", desc, maxsplit=1)[0].strip()
    card = f"{name} — {first}" if first else name
    if _tok(card) > DISCOVERY_TOK:
        # binary-free greedy trim to the token cap, ellipsis on overflow.
        words = card.split()
        out = []
        for w in words:
            trial = " ".join(out + [w])
            if _tok(trial + " …") > DISCOVERY_TOK:
                break
            out.append(w)
        card = " ".join(out) + " …"
    return card


def _summary_extract(body: str, profile: dict) -> str:
    """frontmatter + preamble + only include[] level-2 sections.

    No include anchor matched -> return full body (never silent-empty).
    """
    fm, rest = _split_frontmatter(body)
    include = set(profile.get("include") or [])
    lines = rest.splitlines(keepends=True)
    # preamble = everything before the first '## ' header.
    preamble: list[str] = []
    idx = 0
    for i, ln in enumerate(lines):
        if re.match(r"^## ", ln):
            idx = i
            break
        preamble.append(ln)
    else:
        return body  # no sections at all -> verbatim, never empty

    kept: list[str] = []
    cur_keep = False
    for ln in lines[idx:]:
        if re.match(r"^## ", ln):
            header = ln.strip()
            cur_keep = header in include
        if cur_keep:
            kept.append(ln)
    if not kept:
        return body  # fallback: nothing matched -> verbatim
    return fm + "".join(preamble).rstrip() + "\n\n" + "".join(kept).rstrip() + "\n"


_REF_RE = re.compile(r"\b([\w./-]+\.md)\b")


def _skeletal_extract(body: str, profile: dict) -> str:
    """Pointer-only: frontmatter + first preamble paragraph + an
    on-demand index of the profile's include anchors and any referenced
    *.md files. Anchor BODIES are intentionally not reproduced. Never
    silent-empty (frontmatter+index always present).
    """
    fm, rest = _split_frontmatter(body)
    anchors = [h[3:].strip() if h.startswith("## ") else h.strip()
               for h in (profile.get("include") or [])]
    lines = rest.splitlines()
    # first non-empty preamble paragraph (before the first '## ').
    para: list[str] = []
    for ln in lines:
        if re.match(r"^## ", ln):
            break
        if ln.strip():
            para.append(ln.strip())
        elif para:
            break
    refs = sorted({m.group(1) for m in _REF_RE.finditer(rest)
                   if "/" in m.group(1) or m.group(1).startswith("references")})
    out = [fm.rstrip(), ""]
    if para:
        out.append(" ".join(para))
        out.append("")
    out.append("## On-demand sections (skeletal tier — read full "
               "SKILL.md for any of these)")
    for a in anchors:
        out.append(f"- {a}")
    if refs:
        out.append("")
        out.append("Reference files: " + ", ".join(refs))
    return "\n".join(out).rstrip() + "\n"


def _is_programmatic() -> bool:
    """Programmatic-channel detection (Apollo retrofit, 2026-05-19).

    From 2026-06-15 Anthropic moves Agent SDK / claude -p / GH Actions /
    third-party orchestrators off the subscription bucket onto a separate
    metered credit at full API rates. In that channel every byte of
    injected context is paid for; the summary tier still includes
    verbatim anchor bodies which the headless agent rarely needs.
    Programmatic mode promotes EVERY profiled module to the skeletal
    (pointer-only) renderer, not just the SKELETAL_MODULES set.

    Detection precedence:
      1. env CLAUDE_PROGRAMMATIC=1 (explicit, highest)
      2. stdin is not a TTY (fallback)
    """
    if os.environ.get("CLAUDE_PROGRAMMATIC") == "1":
        return True
    try:
        return not sys.stdin.isatty()
    except Exception:
        return False


def _render(module: str, body: str, tier: str,
            programmatic: bool = False) -> str:
    """tier -> rendered text. full = verbatim (byte-identical).

    When programmatic=True and the module has a TASK_PROFILE, the
    skeletal renderer is used regardless of SKELETAL_MODULES membership
    (programmatic channels pay per token; pointer-only is the default).
    """
    if tier == "full":
        return body
    if tier == "discovery":
        return _discovery_card(body, module)
    prof = TASK_PROFILES.get(module)
    if not prof:
        return body  # unprofiled -> full verbatim
    if programmatic or module in SKELETAL_MODULES:
        return _skeletal_extract(body, prof)
    return _summary_extract(body, prof)


def _sid(data: dict) -> str:
    raw = data.get("session_id")
    if raw:
        return re.sub(r"[^A-Za-z0-9_-]", "-", str(raw))[:64]
    cwd = data.get("cwd") or os.getcwd()
    return "cwd-" + hashlib.sha1(str(cwd).encode("utf-8")).hexdigest()[:12]


def _raw_sid(data: dict) -> str:
    """Unsanitized session_id for cross-hook joins (Stop correlator)."""
    raw = data.get("session_id")
    return str(raw) if raw else ""


def _load_state(sid: str) -> dict:
    p = STATE_DIR / f"jit-injected-{sid}.json"
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
        now = time.time()
        return {k: v for k, v in st.items()
                if isinstance(v, (int, float)) and now - v < DEDUPE_TTL_SEC}
    except Exception:
        return {}                            # fail-open: unknown == not injected


def _save_state(sid: str, st: dict) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        p = STATE_DIR / f"jit-injected-{sid}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st), encoding="utf-8")
        os.replace(tmp, p)                   # atomic; lost-update tolerated
    except Exception:
        pass


CACHE_HINTS_DIR = PP_ROOT / "vault" / "cache_hints"


def _emit_cache_hint(module: str, tier: str, rendered: str,
                     skill_relpath: str) -> None:
    """Sibling cache-control hint for downstream Agent-SDK consumers.

    Only emitted in programmatic mode (where the caller is using the
    Anthropic API directly and CAN set cache_control on prompt blocks).
    Inside Claude Code's own hook chain, cache_control is Anthropic-side
    and we do not control it; the hint file is read by callers that DO
    control it (validated by tools/cache_hint_apply.py).

    Honest contract: the hint carries content_sha256 + cache_control
    directive only. No fabricated savings figure, no inferred TTL.
    """
    try:
        CACHE_HINTS_DIR.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        safe = re.sub(r"[^A-Za-z0-9_.-]", "-", module)
        out = CACHE_HINTS_DIR / f"{safe}_{tier}.json"
        payload = {
            "schema_version": 1,
            "module": module,
            "tier": tier,
            "skill_path": skill_relpath,
            "content_sha256": digest,
            "content_bytes": len(rendered.encode("utf-8")),
            "cache_control": {"type": "ephemeral"},
            "generated_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime()),
        }
        out.write_text(json.dumps(payload, indent=2) + "\n",
                       encoding="utf-8")
    except Exception as exc:
        _log(f"cache_hint emit failed {module}/{tier}: "
             f"{type(exc).__name__}: {exc}")


def _telemetry(sid: str, raw_sid: str, rows: list[dict]) -> None:
    """Append one JSONL row per injected module. Fail-open, absolute path.

    Each row carries the RAW session_id as a field (not only in the
    filename) so the Stop ref-correlator can join on it regardless of
    _sid() sanitization/synthetic-id divergence.
    """
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        p = TELEMETRY_DIR / f"jit_usage_{sid}.jsonl"
        with open(p, "a", encoding="utf-8") as fh:
            for r in rows:
                r = dict(r)
                r["session_id"] = raw_sid
                r["ts"] = time.time()
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception:
        pass


SPEC_CAP_BYTES = 24_000   # spec gets <=60% of the 40 KB budget; remainder for Apollo


def _active_spec(cwd: Path) -> tuple[Path, str] | None:
    """Detect a Spec-Driven Development active spec in the project cwd.

    Honors two canonical paths:
      1. .specify/specs/<feature-id>/spec.md (Spec Kit canonical layout)
      2. vault/specs/<feature>.md (PP-local alternative)

    Picks the most-recently-modified spec when multiple exist. Returns
    (path, content) or None. Fail-open: any read/glob error -> None.
    """
    try:
        candidates: list[Path] = []
        speckit_root = cwd / ".specify" / "specs"
        if speckit_root.is_dir():
            for sub in speckit_root.iterdir():
                if sub.is_dir():
                    sp = sub / "spec.md"
                    if sp.is_file():
                        candidates.append(sp)
        pp_specs = cwd / "vault" / "specs"
        if pp_specs.is_dir():
            for sp in pp_specs.glob("*.md"):
                if sp.is_file():
                    candidates.append(sp)
        if not candidates:
            return None
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        body = latest.read_text(encoding="utf-8")
        if body.strip():
            return (latest, body)
    except Exception:
        pass
    return None


# Zero-Command B.2 — new-feature intent patterns. Match conservative: each
# pattern must have a verb-of-creation + object class. Tuned for English EN
# prompts; ES additions appended after the EN block.
_NEW_FEATURE_RX = re.compile(
    r"\b(?:"
    r"add\s+(?:a\s+|an\s+|the\s+)?(?:feature|function|endpoint|command|"
    r"page|screen|button|component|hook|skill|tool|gate|module|"
    r"flag|setting|preference|integration|api|route|webhook|migration)"
    r"|implement(?:s|ing|ation)?\s+(?:a\s+|an\s+|the\s+)?\w+"
    r"|build\s+(?:a\s+|an\s+|the\s+)?(?:feature|page|screen|component|"
    r"dashboard|panel|widget|api|backend|frontend|cli|tool)"
    r"|create\s+(?:a\s+|an\s+|the\s+)?(?:feature|page|screen|component|"
    r"endpoint|api|cli|tool|hook|skill)"
    r"|let'?s\s+build|let'?s\s+add"
    # ES coverage — Owner speaks ES half the time
    r"|añade|añadir|agrega|agregar|implementa|crea\s+(?:una?\s+)?(?:función|funcion|comando|página|pagina|pantalla)"
    r")\b",
    re.I | re.UNICODE,
)


def _detect_new_feature_intent_and_flag(prompt: str, cwd: Path,
                                        spec: tuple | None,
                                        session_id: str | None) -> dict | None:
    """B.2 side-effect: when the prompt looks like new-feature work AND the
    project has .specify/ AND no active spec, drop .pp-pending-spec.json so
    the SendKeys daemon (B.3) can dispatch /speckit-spec after the agent's
    response lands.

    Returns the flag dict on write (for telemetry), or None when skipped.
    Fail-open: any error -> None.
    """
    try:
        if not prompt or len(prompt) > 8000:
            return None  # extreme prompts skip — UUID-pending pollution risk
        if not _NEW_FEATURE_RX.search(prompt):
            return None
        specify_dir = cwd / ".specify"
        if not specify_dir.is_dir():
            return None
        if spec is not None:
            return None  # active spec already exists; nothing to seed
        flag_path = cwd / ".pp-pending-spec.json"
        if flag_path.exists():
            return None  # already pending; daemon will pick it up
        import uuid
        flag = {
            "uuid": str(uuid.uuid4()),
            "ts": time.time(),
            "session_id": session_id or "unknown",
            "prompt": prompt[:4000],  # cap; daemon reads what's here
            "command_to_dispatch": "/speckit-spec",
            "ttl_sec": 1800,
        }
        tmp = flag_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(flag, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        os.replace(tmp, flag_path)  # atomic
        _log(f"B.2 pending-spec flag dropped uuid={flag['uuid']} cwd={cwd}")
        return flag
    except Exception as exc:                      # fail-open (Ley 24)
        _log(f"B.2 ERROR {type(exc).__name__}: {exc}")
        return None


def run(data) -> dict:
    try:
        data = data or {}
        prompt = str(data.get("prompt") or "")
        cwd = Path(data.get("cwd") or os.getcwd())
        mods = _match_modules(prompt, cwd)
        spec = _active_spec(cwd)
        # Zero-Command B.2 — fire-and-forget flag drop; never blocks the
        # prompt, never adds to additionalContext. Daemon B.3 picks it up.
        _detect_new_feature_intent_and_flag(prompt, cwd, spec,
                                            data.get("session_id"))
        if not mods and not spec:
            return {"continue": True}

        tier = _select_tier(prompt)
        programmatic = _is_programmatic()
        sid = _sid(data)
        raw_sid = _raw_sid(data)
        state = _load_state(sid)
        now = time.time()
        blocks, injected, deferred, tele = [], [], [], []
        total = 0

        spec_injected_size = 0
        if spec is not None:
            spec_path, spec_body = spec
            try:
                rel = spec_path.relative_to(cwd)
            except Exception:
                rel = spec_path
            spec_bytes = spec_body.encode("utf-8")
            if len(spec_bytes) > SPEC_CAP_BYTES:
                spec_body = spec_bytes[:SPEC_CAP_BYTES].decode(
                    "utf-8", "ignore") + "\n\n[... spec truncated at " \
                    f"{SPEC_CAP_BYTES} B cap; read {rel} for full text]\n"
                spec_size = SPEC_CAP_BYTES
            else:
                spec_size = len(spec_bytes)
            blocks.append(
                f"=== ACTIVE PROJECT SPEC: {rel} (priority context, "
                f"PASO -1 of the Apex Onboarding Standard) ===\n"
                f"{spec_body}"
            )
            total += spec_size
            spec_injected_size = spec_size
            tele.append({"module": "__spec__", "tier": "active",
                         "bytes": spec_size, "budget": BUDGET_BYTES,
                         "programmatic": programmatic,
                         "spec_path": str(rel)})
            _log(f"sid={sid} spec-injected {rel} ({spec_size} B)")

        for m in mods:
            if m in state:
                continue                     # already resident this session
            skill = UPSTREAM / m / "SKILL.md"
            if not skill.is_file():
                continue
            body = skill.read_text(encoding="utf-8")
            rendered = _render(m, body, tier, programmatic=programmatic)
            size = len(rendered.encode("utf-8"))
            if total + size > BUDGET_BYTES:
                deferred.append(m)
                continue
            mode = "skeletal-prog" if programmatic and tier == "summary" \
                else tier
            blocks.append(
                f"=== APOLLO JIT MODULE: {m} "
                f"(tier={mode}, force-injected) ===\n{rendered}"
            )
            total += size
            injected.append(m)
            tele.append({"module": m, "tier": tier, "bytes": size,
                         "budget": BUDGET_BYTES,
                         "programmatic": programmatic})
            state[m] = now
            if programmatic:
                _emit_cache_hint(m, tier, rendered,
                                 f"vendor/apollo/upstream/{m}/SKILL.md")

        if not injected and spec_injected_size == 0:
            return {"continue": True}

        _save_state(sid, state)
        _telemetry(sid, raw_sid, tele)
        if injected:
            header = (
                "## JIT Aggressive Activation — Apollo specialist "
                f"module(s) loaded at tier={tier} (trigger matched this "
                f"prompt/project).\n"
                f"Injected ({total} B / {BUDGET_BYTES} B budget): "
                f"{', '.join(injected)}."
            )
        else:
            header = (
                "## JIT Aggressive Activation — active project spec "
                f"injected ({spec_injected_size} B); no Apollo trigger "
                "matched this prompt."
            )
        if spec_injected_size > 0 and injected:
            header += (
                f" Active spec also injected as PASO -1 priority context "
                f"({spec_injected_size} B)."
            )
        if deferred:
            header += (
                f" 40 KB budget reached — deferred (remain as 80-token "
                f"cards via SessionStart sentinel): {', '.join(deferred)}."
            )
        ctx = header + "\n\n" + "\n\n".join(blocks)
        _log(f"sid={sid} tier={tier} injected={injected} bytes={total} "
             f"spec_bytes={spec_injected_size} deferred={deferred}")
        return {"continue": True, "additionalContext": ctx}
    except Exception as exc:                  # fail-open (Ley 24: logged)
        _log(f"ERROR {type(exc).__name__}: {exc}")
        return {"continue": True}


# Importable by hook-dispatcher-style bundlers / tests.
__all__ = ["run", "TASK_PROFILES", "TRIGGERS", "_select_tier", "_render"]


if __name__ == "__main__":
    import threading

    box = {"raw": ""}

    def _reader():
        try:
            box["raw"] = sys.stdin.read()
        except Exception:
            box["raw"] = ""

    th = threading.Thread(target=_reader, daemon=True)
    th.start()
    th.join(3.0)                              # 3 s stdin budget; then proceed

    raw = box["raw"]
    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        payload = {}
    try:
        sys.stdout.write(json.dumps(run(payload)))
    except Exception:
        sys.stdout.write('{"continue": true}')
