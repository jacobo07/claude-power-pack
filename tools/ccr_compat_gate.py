"""CCR compat gate (spec vault/specs/ccr-compat-gate.md): detect a host version CCR was not measured on, re-measure it,
and say exactly how to widen COMPAT. It never edits policy.ts, never releases, and spends tokens only with --confirm.

    python -I tools/ccr_compat_gate.py check                  # zero model; exit 0 only for COVERED
    python -I tools/ccr_compat_gate.py reprobe --confirm      # runs tools/ccr_compat_probe.py (up to 1.5M haiku tokens)
    python -I tools/ccr_compat_gate.py plan                   # prints the widen steps, or why it refuses
    python -I tools/ccr_compat_gate.py source-check --tree P  # P's policy.ts/register.ts vs the active release, COMPAT line aside
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
CCR = pathlib.Path.home() / ".claude" / "ccr"
VERDICTS = REPO / "vault" / "programs" / "ccr" / "compat"
REQUIRED = ("S1b", "S2", "S3", "S4")
COMPAT_RE = re.compile(r"^export const COMPAT\s*=\s*\[([^\]]*)\][^\n]*$", re.M)
VER_RE = re.compile(r"\b(\d+\.\d+\.\d+)\b")
PROBE_TIMEOUT_S = 3000


def host_version(claude: str | None = None) -> str | None:
    claude = claude or shutil.which("claude")
    if not claude:
        return None
    try:
        out = subprocess.run([claude, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = VER_RE.search(out)
    return m.group(1) if m else None


def parse_compat(text: str | None) -> list[str] | None:
    """The COMPAT list in a policy.ts, or None when the line is absent (an empty list is a valid, covers-nothing answer)."""
    m = COMPAT_RE.search(text or "")
    return re.findall(r"""['"]([^'"]+)['"]""", m.group(1)) if m else None


def read_text(p: pathlib.Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8-sig")
    except OSError:
        return None


def check(version: str | None, policy_text: str | None, release: str | None) -> dict:
    compat = parse_compat(policy_text)
    base = {"host": version, "release": release, "compat": compat}
    if version is None:
        return {**base, "verdict": "UNKNOWN", "why": "host version unreadable"}
    if compat is None:
        return {**base, "verdict": "UNKNOWN", "why": "COMPAT line not found in the active policy.ts"}
    return {**base, "verdict": "COVERED" if version in compat else "UNCOVERED"}


def active_release(ccr: pathlib.Path = CCR) -> tuple[str | None, str | None]:
    policy = read_text(ccr / "active" / "hooks" / "policy.ts")
    meta = read_text(ccr / "active" / "RELEASE.json")
    try:
        rel = json.loads(meta).get("release") if meta else None
    except ValueError:
        rel = None
    return policy, rel


def plan(version: str | None, verdict_dir: pathlib.Path = VERDICTS) -> dict:
    if version is None:
        return {"ok": False, "why": "host version unreadable"}
    f = verdict_dir / f"verdict-{version}.json"
    text = read_text(f)
    if text is None:
        return {"ok": False, "why": f"no verdict for {version}: run `reprobe --confirm` first ({f.name})"}
    try:
        v = json.loads(text)
    except ValueError:
        return {"ok": False, "why": f"{f.name} is not valid JSON"}
    if v.get("host_version") != version:
        return {"ok": False, "why": f"{f.name} was measured on {v.get('host_version')}, the host is {version}"}
    got = v.get("verdicts") or {}
    bad = {k: got.get(k, "MISSING") for k in REQUIRED if got.get(k) != "PASS"}   # recomputed: the stored flag is not trusted
    if bad:
        return {"ok": False, "why": "required cases not PASS: " + json.dumps(bad), "named_limits": v.get("named_limits")}
    steps = [
        f"1. Pick the source tree (the worktree that built the active release, NOT the main tree). Run: python -I tools/ccr_compat_gate.py source-check --tree <tree>  (must say SAME_EXCEPT_COMPAT)",
        f"2. In <tree>/mods/cpp-cognitive-runtime/hooks/policy.ts line 8 add '{version}' to the explicit COMPAT list (no range, no wildcard); change nothing else.",
        "3. Gates on that tree: claude plugin test mods/cpp-cognitive-runtime; tools/test_ccr_release.py; tools/test_ccr_main_shadow.py; tools/ccr_estate_gate.py.",
        "4. From that tree: python tools/ccr_release.py release  (never edit ~/.claude/ccr/releases by hand). Rollback ready: python tools/ccr_release.py rollback",
        "5. python -I tools/ccr_compat_gate.py source-check --tree <tree> against the NEW active release must still say SAME_EXCEPT_COMPAT, and `check` must say COVERED.",
    ]
    return {"ok": True, "version": version, "named_limits": v.get("named_limits"), "steps": steps}


def source_check(tree: pathlib.Path, ccr: pathlib.Path = CCR) -> dict:
    """The tree's policy.ts and register.ts against the active release's, with the COMPAT line masked: any other
    difference means a release from this tree would drop or add behaviour (2026-10-17: a main-tree build had 381 lines
    against the active 531 and silently lost the Stage 1-3 work)."""
    out = {"tree": str(tree)}
    for name in ("policy.ts", "register.ts"):
        a = read_text(tree / "mods" / "cpp-cognitive-runtime" / "hooks" / name)
        b = read_text(ccr / "active" / "hooks" / name)
        if a is None or b is None:
            return {**out, "verdict": "UNKNOWN", "why": f"{name} unreadable in the tree or in the active release"}
        mask = lambda t: COMPAT_RE.sub("COMPAT_MASKED", t).replace("\r\n", "\n")
        if mask(a) != mask(b):
            return {**out, "verdict": "DIFFERS", "why": f"{name}: {len(a.splitlines())} lines in the tree, {len(b.splitlines())} in the active release"}
    return {**out, "verdict": "SAME_EXCEPT_COMPAT"}


def reprobe(confirm: bool, version: str | None, release: str | None) -> tuple[int, dict]:
    if not confirm:
        return 2, {"ok": False, "why": "refused: the probe spends up to 1,500,000 haiku tokens; pass --confirm"}
    if version is None:
        return 2, {"ok": False, "why": "host version unreadable"}
    results = VERDICTS / "probe-results.json"
    p = subprocess.run([sys.executable, "-I", str(REPO / "tools" / "ccr_compat_probe.py"), "--fresh", "--results", str(results)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT_S)
    text = read_text(results)
    if text is None:
        return 1, {"ok": False, "why": f"probe left no results (rc={p.returncode})", "stderr": p.stderr[-300:]}
    r = json.loads(text)
    m = VER_RE.search(str(r.get("host", "")))
    v = {"host_version": m.group(1) if m else None, "active_release_at_probe": release, "verdicts": r.get("verdicts"),
         "all_required_pass": r.get("all_required_pass"), "named_limits": r.get("named_limits"), "spent": r.get("spent")}
    dest = VERDICTS / f"verdict-{v['host_version'] or 'unknown'}.json"
    dest.write_text(json.dumps(v, indent=1), encoding="utf-8")
    return 0, {"ok": True, "verdict_file": str(dest), **v}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    version = host_version()
    if cmd == "check":
        policy, rel = active_release()
        out = check(version, policy, rel)
        print(json.dumps(out))
        return {"COVERED": 0, "UNCOVERED": 1}.get(out["verdict"], 3)
    if cmd == "reprobe":
        rc, out = reprobe("--confirm" in argv, version, active_release()[1])
        print(json.dumps(out))
        return rc
    if cmd == "plan":
        out = plan(version)
        print(json.dumps(out, indent=1))
        return 0 if out["ok"] else 1
    if cmd == "source-check" and "--tree" in argv:
        out = source_check(pathlib.Path(argv[argv.index("--tree") + 1]))
        print(json.dumps(out))
        return 0 if out["verdict"] == "SAME_EXCEPT_COMPAT" else 1
    print(__doc__)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
