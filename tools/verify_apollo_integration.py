#!/usr/bin/env python3
"""verify_apollo_integration.py — empirical DONE gate for Apollo Skills fusion.

Exits 0 ONLY if all criteria pass. Every check tests real on-disk state or a
real subprocess; criterion (v) runs a genuine brace-aware GraphQL scanner, not
a simulated parser. Harness activation (hook/agent cold-load) requires
`/restart` and is OUT of phase-7 scope — this gate proves the files on disk are
correct, which is what is independently verifiable now.

Criteria:
  (i)   every MANIFEST module present (non-quarantined under upstream/ with
        SKILL.md; quarantined under optional/); module_count >= recorded.
  (ii)  every MANIFEST file's SHA-256 recomputes to the stored hash.
  (iii) learning-sentinel.js, fed a synthetic GraphQL project cwd over stdin
        (properly JSON-escaped), emits the ground-rules card in
        additionalContext; and is absent for a non-GraphQL cwd.
  (iv)  oneshot-architect-auditor.md (repo mirror + live) carries APOLLO-GRAPHQL.
  (v)   the corrupted fixture yields >=4 violations (>=2 hard, >=2 soft) via a
        real GraphQL operation scanner.
  (vi)  ~/.claude/CLAUDE.md carries the Sovereign GraphQL Baseline seal.
  (vii) vendor/apollo carries LICENSE + SOURCE.txt (vendor/README Rules 1&2).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
VENDOR = PP_ROOT / "vendor" / "apollo"
HOME = Path(os.path.expanduser("~"))
LIVE_HOOK = HOME / ".claude" / "hooks" / "learning-sentinel.js"
REPO_HOOK = PP_ROOT / "hooks" / "learning-sentinel.js"
REPO_AUDITOR = PP_ROOT / "agents" / "oneshot-architect-auditor.md"
LIVE_AUDITOR = HOME / ".claude" / "agents" / "oneshot-architect-auditor.md"
GLOBAL_CLAUDE_MD = HOME / ".claude" / "CLAUDE.md"
FIXTURE = PP_ROOT / "tests" / "fixtures" / "apollo-corrupted" / "src" / "queries.graphql"
JIT_LOADER = PP_ROOT / "tools" / "jit_skill_loader.py"
GQL_OPS_SKILL = PP_ROOT / "vendor" / "apollo" / "upstream" / "graphql-operations" / "SKILL.md"
PY_INTERP = sys.executable  # absolute interpreter running this gate
STATE_DIR = HOME / ".claude" / "state"  # jit_skill_loader dedupe-state dir

PASS, FAIL = "PASS", "FAIL"
results = []


def record(cid: str, ok: bool, detail: str) -> None:
    results.append((cid, ok, detail))
    print(f"[{PASS if ok else FAIL}] {cid}: {detail}")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Real GraphQL operation scanner (brace/paren aware, comment-stripped).
# ---------------------------------------------------------------------------
def _strip_comments(src: str) -> str:
    out = []
    in_str = False
    i = 0
    while i < len(src):
        c = src[i]
        if c == '"' and not in_str:
            in_str = True
        elif c == '"' and in_str:
            in_str = False
        if c == "#" and not in_str:
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        out.append(src[i])
        i += 1
    return "".join(out)


def _match_block(src: str, open_idx: int, openc: str, closec: str) -> int:
    depth = 0
    i = open_idx
    while i < len(src):
        if src[i] == openc:
            depth += 1
        elif src[i] == closec:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


OP_RE = re.compile(r"\b(query|mutation|subscription)\b", re.MULTILINE)
LITERAL_ARG_RE = re.compile(
    r'[A-Za-z_][A-Za-z0-9_]*\s*:\s*'
    r'("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|true|false)(?=[\s,)\]}]|$)'
)
VAR_DEF_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
FIELD_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*[A-Za-z_][A-Za-z0-9_]*)?\s*$")


def scan_graphql(src: str):
    """Return dict with hard/soft violation lists. Real structural scan."""
    text = _strip_comments(src)
    hard, soft = [], []
    for m in OP_RE.finditer(text):
        kw = m.group(1)
        rest = text[m.end():]
        # Identify operation name (token before ( or {).
        name_m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)?", rest)
        op_name = (name_m.group(1) or "").strip() if name_m else ""
        after_name = rest[name_m.end():] if name_m else rest
        nxt = after_name.lstrip()[:1]
        if not op_name and nxt in ("{", "("):
            hard.append(f"anonymous {kw}")

        # Variable definitions, if any.
        declared_vars = set()
        var_block_end = m.end()
        if nxt == "(":
            paren_open = text.index("(", m.end())
            paren_close = _match_block(text, paren_open, "(", ")")
            if paren_close != -1:
                declared_vars = set(VAR_DEF_RE.findall(text[paren_open:paren_close]))
                var_block_end = paren_close

        # Operation body.
        body_open = text.find("{", var_block_end)
        if body_open == -1:
            continue
        body_close = _match_block(text, body_open, "{", "}")
        if body_close == -1:
            continue
        body = text[body_open + 1:body_close]

        # Inline literal args not backed by a declared variable.
        for lm in LITERAL_ARG_RE.finditer(body):
            hard.append(f"inline literal {lm.group(0).strip()} in {op_name or kw}")
            break  # one hard flag per operation is sufficient signal

        # Selection-set analysis: duplicate fields + over-fetch.
        # Walk balanced { } inside the body.
        idx = 0
        while idx < len(body):
            if body[idx] == "{":
                close = _match_block(body, idx, "{", "}")
                if close == -1:
                    break
                inner = body[idx + 1:close]
                # leaf fields = lines that are bare identifiers (no nested {).
                lines = [ln.strip() for ln in inner.splitlines() if ln.strip()]
                leaves = []
                for ln in lines:
                    if "{" in ln or "}" in ln or ln.startswith("..."):
                        continue
                    fm = FIELD_RE.match(ln)
                    if fm:
                        leaves.append(fm.group(1))
                dupes = {f for f in leaves if leaves.count(f) > 1}
                if dupes and "..." not in inner:
                    soft.append(
                        f"duplicate field(s) {sorted(dupes)} in {op_name or kw}"
                    )
                if len(leaves) >= 8 and "..." not in inner:
                    soft.append(
                        f"over-fetch {len(leaves)} leaf fields in {op_name or kw}"
                    )
                idx = close + 1
            else:
                idx += 1
    return {"hard": hard, "soft": soft}


# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------
def c_i_modules():
    mf = VENDOR / "MANIFEST.json"
    if not mf.is_file():
        return record("(i)  modules", False, "MANIFEST.json missing")
    m = json.loads(mf.read_text(encoding="utf-8"))
    quar = set(m.get("quarantined", []))
    bad = []
    for mod in m["modules"]:
        name = mod["name"]
        root = VENDOR / ("optional" if name in quar else "upstream")
        d = root / name
        if not d.is_dir():
            bad.append(f"{name} dir missing")
            continue
        if name not in quar:
            if not mod.get("skill_md") or not (VENDOR / mod["skill_md"]).is_file():
                bad.append(f"{name} SKILL.md missing")
    ok = not bad and m["module_count"] >= len(m["modules"]) and m["module_count"] >= 1
    record("(i)  modules", ok,
           f'{m["module_count"]} modules, quarantined={sorted(quar)}'
           + (f' | issues: {bad}' if bad else ""))


def c_ii_sha():
    mf = VENDOR / "MANIFEST.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    mismatches = []
    for f in m["files"]:
        p = VENDOR / f["path"]
        if not p.is_file():
            mismatches.append(f'{f["path"]} (missing)')
            continue
        if _sha256(p) != f["sha256"]:
            mismatches.append(f'{f["path"]} (hash drift)')
    record("(ii) sha256", not mismatches,
           f'{len(m["files"])} files verified'
           + (f' | {len(mismatches)} mismatch: {mismatches[:3]}' if mismatches else ""))


def _run_hook_for(cwd: Path):
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": str(cwd)})
    proc = subprocess.run(
        ["node", str(REPO_HOOK)], input=payload,
        capture_output=True, text=True, timeout=15,
    )
    try:
        out = json.loads(proc.stdout)
        return (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
    except json.JSONDecodeError:
        return ""


def c_iii_sentinel():
    if not REPO_HOOK.is_file():
        return record("(iii) sentinel", False, "hooks/learning-sentinel.js missing")
    tmp = Path(tempfile.mkdtemp(prefix="apollo_verify_"))
    try:
        gql_dir = tmp / "gql"
        gql_dir.mkdir()
        (gql_dir / "package.json").write_text(
            json.dumps({"name": "x", "dependencies": {"@apollo/client": "^3.9.0"}}),
            encoding="utf-8",
        )
        plain = tmp / "plain"
        plain.mkdir()
        (plain / "package.json").write_text(
            json.dumps({"name": "y", "dependencies": {"react": "^18"}}),
            encoding="utf-8",
        )
        pos = _run_hook_for(gql_dir)
        neg = _run_hook_for(plain)
        ok = ("Apollo GraphQL Ground Rules" in pos
               and "ALWAYS name operations" in pos
               and "Apollo GraphQL Ground Rules" not in neg)
        record("(iii) sentinel", ok,
               f"positive_card={'Apollo GraphQL Ground Rules' in pos} "
               f"negative_clean={'Apollo GraphQL Ground Rules' not in neg}")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def c_iv_auditor():
    repo_ok = REPO_AUDITOR.is_file() and "APOLLO-GRAPHQL" in REPO_AUDITOR.read_text(
        encoding="utf-8")
    live_ok = LIVE_AUDITOR.is_file() and "APOLLO-GRAPHQL" in LIVE_AUDITOR.read_text(
        encoding="utf-8")
    record("(iv) auditor", repo_ok and live_ok,
           f"repo_mirror={repo_ok} live={live_ok}")


def c_v_fixture():
    if not FIXTURE.is_file():
        return record("(v)  fixture", False, "queries.graphql fixture missing")
    res = scan_graphql(FIXTURE.read_text(encoding="utf-8"))
    h, s = len(res["hard"]), len(res["soft"])
    ok = h >= 2 and s >= 2 and (h + s) >= 4
    record("(v)  fixture", ok,
           f"hard={h} {res['hard']} | soft={s} {res['soft']}")


def c_vi_seal():
    txt = GLOBAL_CLAUDE_MD.read_text(encoding="utf-8") \
        if GLOBAL_CLAUDE_MD.is_file() else ""
    gql_seal = "Sovereign GraphQL" in txt          # GraphQL baseline (BL-0068)
    jit_seal = "jit_skill_loader" in txt and "0069" in txt and "JIT" in txt
    lines = len(txt.splitlines()) if txt else -1
    ok = gql_seal and jit_seal and lines < 100
    record("(vi) seal", ok,
           f"gql_seal={gql_seal} jit_seal={jit_seal} "
           f"claude_md_lines={lines} (<100 required)")


def c_vii_license():
    lic = (VENDOR / "LICENSE").is_file()
    src = (VENDOR / "SOURCE.txt").is_file()
    record("(vii) provenance", lic and src,
           f"LICENSE={lic} SOURCE.txt={src} (vendor/README Rules 1&2)")


def _jit_call(cwd: Path, session_id: str, prompt: str):
    payload = json.dumps({
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt,
        "cwd": str(cwd),
        "session_id": session_id,
    })
    proc = subprocess.run(
        [PY_INTERP, str(JIT_LOADER)], input=payload,
        capture_output=True, text=True, timeout=20,
    )
    try:
        return json.loads(proc.stdout), proc.stderr
    except json.JSONDecodeError:
        return {"_parsefail": proc.stdout[:200]}, proc.stderr


def c_viii_jit():
    """JIT loader: real subprocess, top-level additionalContext, >=95% bytes,
    literal heading present (no-summary), dedupe, negative-clean, budget."""
    if not JIT_LOADER.is_file() or not GQL_OPS_SKILL.is_file():
        return record("(viii) jit", False, "jit_skill_loader or SKILL.md missing")
    skill = GQL_OPS_SKILL.read_text(encoding="utf-8")
    skill_bytes = len(skill.encode("utf-8"))
    heading = next((ln for ln in skill.splitlines() if ln.strip()), "")
    # Unique session ids per gate run — the loader's session-dedupe is
    # real persistent state; a fixed id would collide with this gate's
    # OWN prior run and false-fail the positive case.
    import uuid
    tok = uuid.uuid4().hex[:8]
    s1, s2 = f"VERIFYJIT-{tok}-A", f"VERIFYJIT-{tok}-B"
    state_files = [STATE_DIR / f"jit-injected-{s}.json" for s in (s1, s2)]
    tmp = Path(tempfile.mkdtemp(prefix="jit_verify_"))
    try:
        gql = tmp / "gqlproj"
        gql.mkdir()
        (gql / "schema.graphql").write_text("type Query { me: ID }",
                                            encoding="utf-8")
        plain = tmp / "plain"
        plain.mkdir()
        (plain / "package.json").write_text(
            json.dumps({"name": "p", "dependencies": {"react": "^18"}}),
            encoding="utf-8")

        pos, perr = _jit_call(gql, s1,
                              "help me write a graphql query")
        ac = pos.get("additionalContext", "")
        ac_bytes = len(ac.encode("utf-8"))
        top_level = "additionalContext" in pos and "hookSpecificOutput" not in pos
        cont = pos.get("continue") is True
        pct = (ac_bytes / skill_bytes) if skill_bytes else 0
        # full SKILL.md body must be literally embedded, not summarized
        body_embedded = skill[:1500] in ac and skill[-800:] in ac
        heading_present = bool(heading) and heading in ac
        budget_ok = ac_bytes <= 40_000

        ded, _ = _jit_call(gql, s1,
                            "more graphql work")  # same session -> skip
        dedupe_ok = "additionalContext" not in ded and ded.get("continue") is True

        # negative: no graphql/apollo keyword in prompt AND no graphql in
        # cwd — proves the loader does not over-trigger on neutral work.
        neg, _ = _jit_call(plain, s2, "fix the css flexbox padding")
        neg_ok = "additionalContext" not in neg and neg.get("continue") is True

        ok = (top_level and cont and pct >= 0.95 and body_embedded
              and heading_present and budget_ok and dedupe_ok and neg_ok
              and not perr.strip())
        record("(viii) jit", ok,
               f"top_level_ac={top_level} continue={cont} "
               f"bytes={ac_bytes}/{skill_bytes} (>=95%={pct >= 0.95}) "
               f"embedded={body_embedded} heading={heading_present} "
               f"budget<=40K={budget_ok} dedupe={dedupe_ok} "
               f"neg_clean={neg_ok} stderr_clean={not perr.strip()} "
               f"| BL-0067: real-session firing needs /restart "
               f"(subprocess proves file-on-disk logic only)")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        for sf in state_files:               # no leaked dedupe state
            try:
                sf.unlink()
            except OSError:
                pass


def main() -> int:
    print("=== Apollo Skills Fusion — empirical verification ===")
    for fn in (c_i_modules, c_ii_sha, c_iii_sentinel, c_iv_auditor,
               c_v_fixture, c_vi_seal, c_vii_license, c_viii_jit):
        try:
            fn()
        except Exception as exc:  # a crashing check is a FAIL, never a skip
            record(fn.__name__, False, f"EXCEPTION {type(exc).__name__}: {exc}")
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n=== {passed}/{total} criteria passed ===")
    if passed == total:
        print("VERDICT: DONE — Apollo Skills fusion verified.")
        return 0
    print("VERDICT: NOT DONE — unresolved criteria above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
