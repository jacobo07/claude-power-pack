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
import subprocess
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


_WALK_CACHE_TTL = 3600  # 1 hour — graphql files don't appear/disappear mid-task


def _walk_cache_path(cwd: Path) -> Path:
    h = hashlib.sha1(str(cwd).encode("utf-8")).hexdigest()[:12]
    return STATE_DIR / f"jit-walk-{h}.json"


def _walk_has_graphql(cwd: Path) -> bool:
    """Bounded DFS, early-exit on FIRST .graphql/.gql. Cached 1h per cwd.

    The walk costs 200-1500ms on Windows for repos with many files (PP repo:
    ~600-2500ms measured 2026-05-31, jit_skill_loader cold lag root cause).
    Cache file at STATE_DIR/jit-walk-<sha1>.json with {ts, found}. Cache miss
    or expired -> do the walk + write cache. Fail-open: any cache error
    falls through to the walk.
    """
    cache_path = _walk_cache_path(cwd)
    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if time.time() - float(cached.get("ts", 0)) < _WALK_CACHE_TTL:
            return bool(cached.get("found", False))
    except (OSError, ValueError, TypeError):
        pass

    stack = [(cwd, 0)]
    seen = 0
    found = False
    while stack and not found:
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
                            found = True
                            break
                    except OSError:
                        continue
        except OSError:
            continue

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"ts": time.time(), "found": found}),
            encoding="utf-8")
    except OSError:
        pass
    return found


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


_SPEC_CACHE_TTL = 300  # 5 min — specs DO change inside a working session


def _spec_cache_path(cwd: Path) -> Path:
    h = hashlib.sha1(str(cwd).encode("utf-8")).hexdigest()[:12]
    return STATE_DIR / f"jit-spec-{h}.json"


def _active_spec(cwd: Path) -> tuple[Path, str] | None:
    """Detect a Spec-Driven Development active spec in the project cwd.

    Honors two canonical paths:
      1. .specify/specs/<feature-id>/spec.md (Spec Kit canonical layout)
      2. vault/specs/<feature>.md (PP-local alternative)

    Picks the most-recently-modified spec when multiple exist. Returns
    (path, content) or None. Fail-open: any read/glob error -> None.

    Result is cached 5 min per cwd at STATE_DIR/jit-spec-<sha1>.json:
    payload stores the spec path + mtime so the cache is invalidated if
    a fresh write lands. None-results are cached as {"none": true}.
    """
    cache_path = _spec_cache_path(cwd)
    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        ts = float(cached.get("ts", 0))
        if time.time() - ts < _SPEC_CACHE_TTL:
            if cached.get("none"):
                return None
            sp = Path(cached.get("path") or "")
            if sp.is_file():
                # Only honor cache if mtime matches stored one
                # (i.e. the spec hasn't been touched since we cached).
                stored_mtime = float(cached.get("mtime", 0))
                if abs(sp.stat().st_mtime - stored_mtime) < 0.5:
                    body = sp.read_text(encoding="utf-8")
                    if body.strip():
                        return (sp, body)
    except (OSError, ValueError, TypeError):
        pass
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
            try:
                STATE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps({"ts": time.time(), "none": True}),
                    encoding="utf-8")
            except OSError:
                pass
            return None
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        body = latest.read_text(encoding="utf-8")
        if body.strip():
            try:
                STATE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps({"ts": time.time(),
                                "path": str(latest),
                                "mtime": latest.stat().st_mtime}),
                    encoding="utf-8")
            except OSError:
                pass
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


# --- Architecture Decision Skill piggyback ---
# Fast-path arch_check spawn on prompts that look like design decisions.
# Cheap pre-filter (>=2 design verbs); subprocess only on hit. Fail-open.
_ARCH_DESIGN_VERBS = (
    "design", "architecture", "implement", "propose", "should",
    "choose", "between", "build", "plan", "strategy", "decide",
    "decision", "evaluate", "alternative", "approach",
    # Spanish
    "diseña", "diseñar", "arquitectura", "implementar", "propon",
    "proponer", "deberia", "deberiamos", "elegir", "construir",
    "evaluar", "planificar", "estrategia", "decidir",
)


# --- Prompt Quality Axis (sealed 2026-05-23): vague-prompt lint signal ---
# Detects short prompts whose referent is unresolved ("the bug", "esto",
# "hazlo"). Emits a one-line warning into additionalContext. Never
# blocks, never rewrites — the agent decides whether to ask the Owner.
# AND of three conditions, all deterministic / regex-only:
#   1. len(prompt.split()) < 30 tokens
#   2. at least one vague referent matches
#   3. no mitigator present (file extension, line number, function name,
#      >1 design verb, active .specify spec)
# Owner spec: auto-rewriter is explicitly vetoed — risk > benefit.
_VAGUE_REFERENT_RX = re.compile(
    r"\b(?:"
    # Pronouns / demonstratives (referent unresolved without context)
    r"esto|this|it|that|eso|aquello|lo\s+de|"
    # Definite article + opaque noun, allowing up to 3 modifier words
    # between (e.g. "the bug", "the auth bug", "the recent ci error")
    r"the\s+(?:\w+\s+){0,3}(?:bug|issue|error|thing|problem|stuff|"
    r"feature|change|fix|file|code|function|method|module|component)|"
    r"el\s+(?:\w+\s+){0,3}(?:bug|error|fallo|problema|asunto|tema|"
    r"funcion|funci[oó]n|metodo|m[eé]todo|modulo|m[oó]dulo|"
    r"componente|cambio|arreglo|archivo|codigo|c[oó]digo)|"
    r"la\s+(?:\w+\s+){0,3}(?:cosa|funci[oó]n|funcion|p[aá]gina|pagina)|"
    # Spanish imperative + enclitic-lo (hazlo, házmelo, dámelo, etc.)
    r"hazlo|h[aá]zmelo|d[aá]melo|d[ií]melo|t[oó]malo|ponlo|"
    r"d[eé]jalo|us[aá]lo|m[ií]ralo|m[uú]?[eé]?stra(?:me)?lo|"
    r"hace?d?lo|haga(?:n|mos)?lo"
    r")\b",
    re.I | re.UNICODE)
_FILE_HINT_RX = re.compile(
    r"\b[\w.-]+\.(?:py|pyi|ts|tsx|js|jsx|mjs|cjs|java|kt|ex|exs|rs|go|"
    r"cpp|cc|c|h|hpp|md|yml|yaml|json|toml|sh|ps1|sql|css|scss|html|"
    r"xml|swift|dart|rb|php|cs|vue|svelte|astro|gradle|mod|lock)\b",
    re.I)
_LINE_HINT_RX = re.compile(
    r"\b(?:line|l[ií]nea|row)\s*\d+\b|:\d+\b", re.I | re.UNICODE)
_FUNCTION_HINT_RX = re.compile(
    r"\b(?:function|method|def|defn|fn|fun|class|module|struct)\s+\w+"
    r"|\b[a-zA-Z_]\w*\([^)]*\)",
    re.I)
VAGUE_LINT_MESSAGE = (
    "[vague-prompt-lint] Prompt corto (<30 tok) con referente sin "
    "concretar. Si hay ambiguedad real, pregunta al Owner que es 'X' "
    "antes de ejecutar. No bloqueante."
)


# --- Lateral-Thinking Axis (sealed 2026-05-25, trigger family #10) ---
# Discovery-card injection when the prompt signals stuckness, a design
# pivot, or an explicit "how should I" question. Pointer-only: the body
# of the lateral-thinking SKILL.md is NOT inlined here — the card tells
# the agent the skill exists and how to invoke it. Mutex with the
# vague-prompt lint (no card if the prompt is too vague to think about
# laterally yet) and with arch-check (no card if arch_check already
# fired — arch_check's context carries the lateral nudge).
_LATERAL_RX = re.compile(
    r"\b(?:"
    r"stuck|stymied|blocked|atascado|atrapado|"
    r"no\s+idea|no\s+se\s+me\s+ocurre|no\s+sabemos|"
    r"how\s+should\s+i|how\s+do\s+i\s+approach|"
    r"what'?s?\s+the\s+best\s+(?:approach|way)|"
    r"design\s+problem|design\s+pivot|"
    r"brainstorm|alternativas?|lateral|"
    r"complex\s+problem|hard\s+problem|"
    r"too\s+obvious|obvious\s+(?:answer|solution)\s+is\s+wrong"
    r")\b",
    re.I | re.UNICODE)
LATERAL_CARD = (
    "[lateral-thinking-skill] Stuck / design-pivot prompt detected. "
    "Invoke the Skill tool with name `lateral-thinking` for the "
    "5-frame procedure (reframing, inversion, cross-domain analogy, "
    "constraint-removal, first-principles), scoring rubric (1-5 per "
    "frame), and audit-trail block format. Default top-3 by "
    "problem-domain; the full procedure is mandatory before solution "
    "convergence. Cross-references: 5 per-frame files under "
    "~/.claude/skills/lateral-thinking/references/."
)


def _detect_lateral_thinking_trigger(
    prompt: str, arch_block, vague_block,
) -> str | None:
    """Trigger family #10 — discovery card for the lateral-thinking skill.

    Mutex: defers to arch_check (if `arch_block` is non-None) and to
    vague-lint (if `vague_block` is non-None). Same fail-open contract
    as the other JIT helpers (any error -> None, log, never block).
    """
    try:
        if os.environ.get("CLAUDEPP_LATERAL_DISABLE") == "1":
            return None
        if os.environ.get("CLAUDEPP_JIT_RUNNING") == "1":
            return None
        if not prompt:
            return None
        if arch_block is not None:
            return None   # arch_check covers design-decision prompts;
                          # genuine semantic overlap, mutex stays.
        # Note: vague-lint mutex DROPPED 2026-05-25 after empirical run.
        # vague-lint's `this/that/it` matchers fire on conversational use
        # of those pronouns (e.g. "above that", "this repo"); muting LT
        # on those false positives was over-conservative. Both advisories
        # coexist; the agent can decide which (or both) to act on.
        if not _LATERAL_RX.search(prompt):
            return None
        return LATERAL_CARD
    except Exception as exc:
        _log(f"lateral-thinking ERROR {type(exc).__name__}: {exc}")
        return None


def _detect_vague_prompt(prompt: str, spec) -> str | None:
    """Owner-spec lint signal — returns one-line warning or None.

    `spec` is the result of `_active_spec(cwd)`: tuple or None. We pass
    it instead of re-walking the filesystem (already paid in run()).
    Fail-open: any error -> None.
    """
    try:
        if os.environ.get("CLAUDEPP_VAGUE_LINT_DISABLE") == "1":
            return None
        if os.environ.get("CLAUDEPP_JIT_RUNNING") == "1":
            return None
        if not prompt:
            return None
        if len(prompt.split()) >= 30:
            return None
        if spec is not None:
            return None
        if not _VAGUE_REFERENT_RX.search(prompt):
            return None
        if _FILE_HINT_RX.search(prompt):
            return None
        if _LINE_HINT_RX.search(prompt):
            return None
        if _FUNCTION_HINT_RX.search(prompt):
            return None
        lo = prompt.lower()
        design_hits = sum(1 for v in _ARCH_DESIGN_VERBS if v in lo)
        if design_hits > 1:
            return None
        return VAGUE_LINT_MESSAGE
    except Exception as exc:
        _log(f"vague-lint ERROR {type(exc).__name__}: {exc}")
        return None


def _arch_check_inject(prompt: str) -> str | None:
    """Spawn arch_check.py --fast; return its context block on
    COLLISION/WARNING, else None. Fail-open on any exception."""
    if os.environ.get("CLAUDEPP_ARCHCHECK_DISABLED") == "1":
        return None
    if os.environ.get("CLAUDEPP_ARCHCHECK_RUNNING") == "1":
        return None
    if not prompt or len(prompt) < 20:
        return None
    lo = prompt.lower()
    hits = sum(1 for v in _ARCH_DESIGN_VERBS if v in lo)
    if hits < 2:
        return None
    arch_check = PP_ROOT / "modules" / "arch-decision" / "arch_check.py"
    if not arch_check.is_file():
        return None
    try:
        # NOTE: do NOT set CLAUDEPP_ARCHCHECK_RUNNING=1 here. The
        # recursion guard is for level-2+ chains (when /arch-decision
        # --deep spawns claude.exe which re-fires UserPromptSubmit).
        # The FAST piggyback is level-1 and should run normally.
        proc = subprocess.run(
            [sys.executable, str(arch_check), "--fast"],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=3,
        )
        out = json.loads(proc.stdout.decode("utf-8", errors="replace"))
        if out.get("verdict") in ("COLLISION", "WARNING"):
            ctx = out.get("context")
            if ctx:
                return ctx
    except Exception as exc:
        _log(f"arch-check inject ERROR {type(exc).__name__}: {exc}")
    return None


_TCO_TASK_KEYWORDS = (
    # Keywords listed in priority order. First match wins.
    ("iteration_on_error", ("error", "crash", "exception", "traceback",
                             "failing", "bug")),
    ("code_review_final",  ("review", "audit", "code-review",
                             "block", "approve")),
    ("arch_decision",      ("architecture", "arquitectura", "design",
                             "diseno", "schema", "trade-off", "tradeoff",
                             "ultra plan", "decision")),
    ("test_runner",        ("test", "pytest", "verify", "smoke",
                             "regression")),
    ("commit_push_pr",     ("commit", "push", "pull request", "merge",
                             "rebase")),
    ("doc_generation",     ("readme", "changelog", "doc ", "docs ",
                             "documentation", "release notes")),
    ("subagent_explore",   ("explore", "find", "search", "locate",
                             "grep", "list ", "where is")),
    ("single_file_lookup", ("show me", "open ", "cat ", "head ", "tail ")),
)


def _tco_infer_task_type(prompt: str) -> str | None:
    """Heuristic: scan prompt for keywords mapped to TCO task_types.
    Returns the first match or None if no clear signal."""
    if not prompt:
        return None
    lo = prompt.lower()
    for task_type, kws in _TCO_TASK_KEYWORDS:
        for kw in kws:
            if kw in lo:
                return task_type
    return None


def _tco_load_routing_cached():
    """Cache the routing JSON for the lifetime of this process. The
    JIT runs many times per session; re-reading the JSON each call is
    wasteful. Cache miss => disk read => store. Cache invalidation is
    not required because the file is human-edited at config time."""
    if hasattr(_tco_load_routing_cached, "_cache"):
        return _tco_load_routing_cached._cache
    cfg_path = PP_ROOT / "vault" / "config" / "model-routing.json"
    if not cfg_path.is_file():
        cfg = {"default_model": "claude-opus-4-7",
               "rules": [], "skill_to_task_type": {}}
    else:
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cfg = {"default_model": "claude-opus-4-7",
                   "rules": [], "skill_to_task_type": {}}
    _tco_load_routing_cached._cache = cfg
    return cfg


def _tco_inject_routing(fn):
    """TCO B3: append a one-line model recommendation to
    additionalContext when the prompt heuristic infers a clear
    task_type. Advisory only; never blocks. Fail-open."""
    import functools as _ft
    @_ft.wraps(fn)
    def _wrapper(data):
        result = fn(data)
        try:
            prompt = str((data or {}).get("prompt") or "")
            task_type = _tco_infer_task_type(prompt)
            if not task_type:
                return result
            cfg = _tco_load_routing_cached()
            default = cfg.get("default_model", "claude-opus-4-7")
            rec = default
            for r in cfg.get("rules", []):
                if r.get("task_type") == task_type:
                    rec = r.get("recommended_model", default)
                    break
            line = (f"TCO router: prompt heuristic -> task_type="
                    f"{task_type}; recommended model: {rec} "
                    f"(see vault/config/model-routing.json)")
            if not isinstance(result, dict):
                return result
            ac = result.get("additionalContext") or ""
            if ac and not ac.endswith("\n"):
                ac += "\n"
            ac += line
            result["additionalContext"] = ac
            return result
        except Exception as _exc:
            _log(f"tco router inject ERROR {type(_exc).__name__}: {_exc}")
            return result
    return _wrapper


def _tis_log_call(fn):
    """M3: Token-Intelligence hook. Wraps jit_skill_loader.run() and
    records a per-call TokenEvent to vault/token_logs/. Fail-open: any
    exception in the logger is swallowed so the prompt pipeline is
    never disrupted. The hook is local (no third-party deps); SCS C7
    RTK-compat is preserved (we emit structured JSON, never parse raw
    stdout)."""
    import functools as _ft
    @_ft.wraps(fn)
    def _wrapper(data):
        result = fn(data)
        try:
            from datetime import datetime as _dt, timezone as _tz
            import tis as _tis
            sid = _tis.get_session_id()
            prompt = str((data or {}).get("prompt") or "")
            # Estimate cl100k tokens via chars / 4 proxy. The hook
            # itself is not an LLM call -- this is the JIT-context
            # injection size we want forensic visibility into.
            inp_est = max(len(prompt) // 4, 0)
            ctx = ""
            if isinstance(result, dict):
                ctx = str(result.get("additionalContext") or "")
                inner = result.get("hookSpecificOutput") or {}
                ctx += str(inner.get("additionalContext") or "")
            out_est = len(ctx) // 4
            label = "jit-context-injected" if ctx else "jit-no-injection"
            _tis.append_log(_tis.TokenEvent(
                session_id=sid,
                timestamp_iso=_dt.now(_tz.utc).isoformat(),
                skill_name="jit_skill_loader.run",
                model="claude-code-hook",
                input_tokens=inp_est,
                output_tokens=out_est,
                cache_read_tokens=0,
                cache_creation_tokens=0,
                call_label=label,
                project=str((data or {}).get("cwd") or ""),
            ))
        except Exception as _exc:
            _log(f"tis hook ERROR {type(_exc).__name__}: {_exc}")
        return result
    return _wrapper


_PROACTIVE_THROTTLE_DIR = PP_ROOT / "vault" / "pp_agents" / "throttle"


def _proactive_any_eligible() -> bool:
    """Cheap pre-check: would ANY agent's throttle let it fire right now?

    Returns False when every throttle file in the dir was touched within
    the shortest known cooldown (5 min, the pp-monitor / pp-cascade-guard
    floor). In that case, the dispatcher would short-circuit on every
    agent anyway, so skip the ~30 ms import + dispatch cost entirely.

    Fail-open: any I/O error -> True (run the full dispatcher).
    """
    try:
        if not _PROACTIVE_THROTTLE_DIR.is_dir():
            return True  # no state yet -> first run could fire
        now = time.time()
        floor_sec = 5 * 60  # the smallest configured cooldown
        for entry in os.scandir(_PROACTIVE_THROTTLE_DIR):
            if not entry.name.endswith(".json"):
                continue
            try:
                age = now - entry.stat().st_mtime
            except OSError:
                return True
            if age >= floor_sec:
                return True  # at least one agent is past its floor
        return False  # every agent throttled
    except OSError:
        return True


def _pp_proactive_inject(fn):
    """PP Proactive Agents (Jobs/Woz) -- append agent advisories to
    additionalContext when their signals fire. Sleepy-by-default,
    non-blocking, fail-open. Sealed BL-PROACTIVE-001 (2026-05-29).

    Hot-path pre-check (T-JIT-001, sealed 2026-05-31): the dispatcher
    import + per-agent throttle scan is ~30 ms per subprocess. When
    every agent's throttle file is < 5 min old (the shortest cooldown),
    no advisory could fire anyway, so skip the entire dispatch.
    """
    import functools as _ft

    @_ft.wraps(fn)
    def _wrapper(data):
        result = fn(data)
        try:
            if not _proactive_any_eligible():
                return result  # all agents throttled, ~30 ms saved
            data = data or {}
            cwd_raw = data.get("cwd") or ""
            project = Path(cwd_raw).name.lower() if cwd_raw else "global"
            ctx_in = {
                "project": project or "global",
                "last_written_code": "",
                "last_written_file": "",
                "current_error": "",
                "session_had_errors": False,
                "errors_fixed": 0,
            }
            try:
                import tis as _tis
                sid = _tis.get_session_id()
                entries = _tis.read_log() or []
                window = [e for e in entries
                          if e.get("session_id") == sid][-20:]
                ctx_in["session_had_errors"] = any(
                    "error" in str(e.get("skill_name", "")).lower()
                    or "fail" in str(e.get("call_label", "")).lower()
                    for e in window
                )
            except Exception:
                pass

            from modules.pp_agents.proactive_dispatcher import (
                dispatch_to_additional_context,
            )
            advisory_block = dispatch_to_additional_context(ctx_in)
            if not advisory_block:
                return result
            if not isinstance(result, dict):
                return result
            ac = result.get("additionalContext") or ""
            if ac and not ac.endswith("\n"):
                ac += "\n"
            ac += advisory_block
            result["additionalContext"] = ac
        except Exception as _exc:
            _log(f"pp proactive inject ERROR {type(_exc).__name__}: {_exc}")
        return result
    return _wrapper


# --- One-Shot Compiler Axis (BL-ONESHOT-001 wiring) ---
# When a prompt looks like an L/XL build task, compile a fidelity
# contract inline and inject it as priority context so the agent works
# against an explicit scope / done-gate / budget from the first token.
# Conservative gate: long prompt (>= 120 chars) + a creation verb.
# Cooldown 30 min per session so a burst of long prompts injects once.
_ONESHOT_XL_RX = re.compile(
    r"\b(?:implement|build|create\s+the|develop|architect|"
    r"refactor\s+the\s+entire|redesign|migrate|rewrite|overhaul|"
    r"design\s+the\s+system|construye|implementa|redise[nñ]a|"
    r"reescribe|migra)\b",
    re.I | re.UNICODE,
)
_ONESHOT_MIN_PROMPT_LEN = 120
_ONESHOT_COOLDOWN_SEC = 30 * 60


def _oneshot_recent(sid: str) -> bool:
    """True iff a contract was injected for this session within the
    cooldown window. Fail-open: any error -> False (allow injection)."""
    p = STATE_DIR / f"jit-oneshot-{sid}.json"
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
        return (time.time() - float(st.get("ts", 0))) < _ONESHOT_COOLDOWN_SEC
    except Exception:
        return False


def _oneshot_mark(sid: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        p = STATE_DIR / f"jit-oneshot-{sid}.json"
        p.write_text(json.dumps({"ts": time.time()}), encoding="utf-8")
    except Exception:
        pass


def _oneshot_contract_inject(fn):
    """Append a compiled One-Shot fidelity contract to additionalContext
    on L/XL build prompts. Advisory; never blocks. Fail-open."""
    import functools as _ft

    @_ft.wraps(fn)
    def _wrapper(data):
        result = fn(data)
        try:
            if os.environ.get("CLAUDEPP_ONESHOT_DISABLE") == "1":
                return result
            data_d = data or {}
            prompt = str(data_d.get("prompt") or "")
            if len(prompt) < _ONESHOT_MIN_PROMPT_LEN:
                return result
            if not _ONESHOT_XL_RX.search(prompt):
                return result
            sid = _sid(data_d)
            if _oneshot_recent(sid):
                return result
            from modules.one_shot.compiler import compile_contract
            c = compile_contract(prompt[:300], "L")
            block = (
                "## One-Shot Contract (BL-ONESHOT-001 -- L/XL task detected)\n"
                f"- task_id: {c.task_id}\n"
                f"- budget: ${c.budget_usd:g} (size L)\n"
                f"- scope: {'; '.join(c.scope) if c.scope else '(derive from prompt)'}\n"
                f"- done_gate: {c.done_gate}\n"
                "- Honor the Fidelity Lock: if >40% of touched files fall "
                "outside scope, pause and re-confirm (HR-ONESHOT-002)."
            )
            if not isinstance(result, dict):
                return result
            ac = result.get("additionalContext") or ""
            if ac and not ac.endswith("\n"):
                ac += "\n"
            ac += "\n" + block
            result["additionalContext"] = ac
            _oneshot_mark(sid)
            return result
        except Exception as _exc:
            _log(f"oneshot inject ERROR {type(_exc).__name__}: {_exc}")
            return result
    return _wrapper


@_tis_log_call
@_tco_inject_routing
@_pp_proactive_inject
@_oneshot_contract_inject
def run(data) -> dict:
    try:
        data = data or {}
        prompt = str(data.get("prompt") or "")
        arch_block = _arch_check_inject(prompt)
        cwd = Path(data.get("cwd") or os.getcwd())
        mods = _match_modules(prompt, cwd)
        spec = _active_spec(cwd)
        # Prompt Quality Axis (2026-05-23): one-line lint signal for short
        # prompts with vague referents. Spec is passed (already computed)
        # to avoid a second .specify walk. Never blocks; advisory only.
        vague_block = _detect_vague_prompt(prompt, spec)
        # Lateral-Thinking Axis (2026-05-25): discovery card for the
        # lateral-thinking skill. Mutex with arch_block + vague_block.
        lt_block = _detect_lateral_thinking_trigger(
            prompt, arch_block, vague_block)
        # Zero-Command B.2 — fire-and-forget flag drop; never blocks the
        # prompt, never adds to additionalContext. Daemon B.3 picks it up.
        _detect_new_feature_intent_and_flag(prompt, cwd, spec,
                                            data.get("session_id"))
        if not mods and not spec:
            extras = "\n\n".join(
                b for b in (arch_block, vague_block, lt_block) if b)
            if extras:
                return {"continue": True, "additionalContext": extras}
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
            extras = "\n\n".join(
                b for b in (arch_block, vague_block, lt_block) if b)
            if extras:
                return {"continue": True, "additionalContext": extras}
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
        extras = "\n\n".join(
            b for b in (arch_block, vague_block, lt_block) if b)
        if extras:
            ctx = ctx + "\n\n" + extras
        _log(f"sid={sid} tier={tier} injected={injected} bytes={total} "
             f"spec_bytes={spec_injected_size} deferred={deferred} "
             f"arch={'yes' if arch_block else 'no'} "
             f"vague={'yes' if vague_block else 'no'} "
             f"lt={'yes' if lt_block else 'no'}")
        return {"continue": True, "additionalContext": ctx}
    except Exception as exc:                  # fail-open (Ley 24: logged)
        _log(f"ERROR {type(exc).__name__}: {exc}")
        return {"continue": True}


# Importable by hook-dispatcher-style bundlers / tests.
__all__ = ["run", "TASK_PROFILES", "TRIGGERS", "_select_tier", "_render",
           "_detect_vague_prompt", "VAGUE_LINT_MESSAGE",
           "_detect_lateral_thinking_trigger", "LATERAL_CARD"]


def _warm_run() -> int:
    """SessionStart pre-warm path (PP_WARM_RUN=1, T-JIT-001).

    Pays the heavy first-time costs (Python interpreter cold start,
    module imports, walk + spec disk caches priming, tiktoken BPE load
    on the discovery code path) so the user's first real prompt skips
    them. Detached spawn from hooks/jit_warm.js. NEVER blocks the
    session: any error -> exit 0 silently.

    Honest scope: a subprocess pre-warm cannot share its in-process
    caches (tiktoken handle, sys.modules) with the user's later
    UserPromptSubmit subprocess -- those start fresh. The wins that
    DO survive across subprocess boundaries:
      * OS page cache for python.exe + the stdlib + jit_skill_loader.py
      * STATE_DIR/jit-walk-<sha>.json (1 h)
      * STATE_DIR/jit-spec-<sha>.json (5 min)
      * .pyc bytecode files emitted by the interpreter

    Does NOT call run(): we do NOT want to mark Apollo modules as
    "already injected this session" before the user has typed (that
    would suppress their first real Apollo injection).
    """
    try:
        cwd_env = os.environ.get("PP_WARM_CWD") or os.getcwd()
        cwd = Path(cwd_env)
        _walk_has_graphql(cwd)
        _active_spec(cwd)
        sys.stdout.write("warm:ok")
    except Exception as exc:
        _log(f"warm-run ERROR {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    if os.environ.get("PP_WARM_RUN") == "1":
        raise SystemExit(_warm_run())

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
