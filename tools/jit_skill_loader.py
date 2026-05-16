#!/usr/bin/env python3
"""jit_skill_loader.py — JIT Aggressive Activation (UserPromptSubmit hook).

Force-injects the FULL SKILL.md of directly-matched Apollo modules into
context the instant a prompt/cwd trigger fires. Latent otherwise — the
SessionStart sentinel keeps the 80-token cards; this is purely additive.

Contract (Claude Code UserPromptSubmit):
  stdin JSON {hook_event_name, prompt, cwd, session_id}
  -> stdout JSON with TOP-LEVEL `additionalContext` (verified shape:
     hook-dispatcher.js:156-166 — only PreToolUse nests it under
     hookSpecificOutput; every other event uses top-level).
  Fail-open: ANY error -> {"continue": true} (never block the prompt).

Tiered-aggressive (Q&A 1a): inject full SKILL.md ONLY of directly-matched
module(s); others stay cards. 40 KB circuit breaker (BL-0068): priority
fill, defer overflow. Session-dedupe (anti-buffer-overflow): inject a
module full ONCE per session; TTL 2 h prevents permanent cross-session
suppression when session_id is absent.
"""
from __future__ import annotations
import hashlib
import json
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

BUDGET_BYTES = 40_000           # BL-0068 circuit breaker (Token Austerity)
DEDUPE_TTL_SEC = 2 * 60 * 60    # 2 h — caps cross-session false-dedupe
WALK_CAP = 2000                 # hard ceiling on dirent stats
MAX_DEPTH = 4
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


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _package_deps(cwd: Path) -> str:
    try:
        pj = cwd / "package.json"
        if pj.is_file():
            j = json.loads(pj.read_text(encoding="utf-8"))
            keys = []
            for sec in ("dependencies", "devDependencies", "peerDependencies"):
                keys += list((j.get(sec) or {}).keys())
            return " ".join(keys)
    except Exception:
        pass
    return ""


def _walk_has_graphql(cwd: Path) -> bool:
    """Bounded DFS, early-exit on FIRST .graphql/.gql (G5)."""
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


def _sid(data: dict) -> str:
    raw = data.get("session_id")
    if raw:
        return re.sub(r"[^A-Za-z0-9_-]", "-", str(raw))[:64]
    cwd = data.get("cwd") or os.getcwd()
    return "cwd-" + hashlib.sha1(str(cwd).encode("utf-8")).hexdigest()[:12]


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


def run(data) -> dict:
    try:
        data = data or {}
        prompt = str(data.get("prompt") or "")
        cwd = Path(data.get("cwd") or os.getcwd())
        mods = _match_modules(prompt, cwd)
        if not mods:
            return {"continue": True}

        sid = _sid(data)
        state = _load_state(sid)
        now = time.time()
        blocks, injected, deferred = [], [], []
        total = 0
        for m in mods:
            if m in state:
                continue                     # already resident this session
            skill = UPSTREAM / m / "SKILL.md"
            if not skill.is_file():
                continue
            body = skill.read_text(encoding="utf-8")
            size = len(body.encode("utf-8"))
            if total + size > BUDGET_BYTES:
                deferred.append(m)
                continue
            blocks.append(
                f"=== APOLLO JIT MODULE: {m} "
                f"(full SKILL.md, force-injected) ===\n{body}"
            )
            total += size
            injected.append(m)
            state[m] = now

        if not injected:
            return {"continue": True}

        _save_state(sid, state)
        header = (
            "## JIT Aggressive Activation — Apollo specialist module(s) "
            "loaded at FULL depth (trigger matched this prompt/project).\n"
            f"Injected ({total} B / {BUDGET_BYTES} B budget): "
            f"{', '.join(injected)}."
        )
        if deferred:
            header += (
                f" 40 KB budget reached — deferred (remain as 80-token "
                f"cards via SessionStart sentinel): {', '.join(deferred)}."
            )
        ctx = header + "\n\n" + "\n\n".join(blocks)
        _log(f"sid={sid} injected={injected} bytes={total} "
             f"deferred={deferred}")
        return {"continue": True, "additionalContext": ctx}
    except Exception as exc:                  # fail-open (Ley 24: logged)
        _log(f"ERROR {type(exc).__name__}: {exc}")
        return {"continue": True}


# Importable by hook-dispatcher-style bundlers / tests.
__all__ = ["run"]


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
