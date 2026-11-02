#!/usr/bin/env python3
"""V-OBL-* and V-LATEST-KCLEAR gates (vault/specs/interactive-context-rollover.md; defects found by GPF run K4,
scoped in vault/programs/global-prefix-floor/CCR_CAPSULE_DEFECTS_SCOPE.md).

V-OBL: a goal file the caller NAMED supplies the obligations verbatim; the stated (model-summarised) items are
only a fallback, and the exam's `next` answer is the goal file's own text.
V-LATEST-KCLEAR: the real /kclear seal path (session_checkpoint.seal_capsule) leaves latest/<repo-key>.json, the
only way a successor's CCR frontier finds its capsule.
Hermetic: throwaway dirs; the /kclear gate runs in a subprocess with CPP_ROLLOVER_STATE_DIR set before import.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402

passes = fails = 0
MARK = "PROBE-MARK-T1-xyz"
VERBATIM = f"Create done.txt in the project root containing exactly {MARK}"
PARAPHRASE = "Owner go-ahead to create done.txt with the PROBE-MARK-T1 marker"


def check(gate: str, cond: bool, ev) -> None:
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def goal_file(d: Path, with_next: bool = True) -> Path:
    g = d / "RESUMPTION_FILE.md"
    body = "# probe\n\nGoal: prove recovery.\n\n"
    body += f"## Next\n1. {VERBATIM}\n2. Reply with one line.\n" if with_next else "## Notes\n- nothing pending here\n"
    g.write_text(body, encoding="utf-8")
    return g


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="obl_t_"))
    a, b = tmp / "a", tmp / "b"
    a.mkdir(); b.mkdir()

    ga = goal_file(a)
    cap = ro.compile_capsule("sid-obl-1", str(a), None, goal=str(ga), next_items=[PARAPHRASE], summary="s")
    check("V-OBL-NAMED-GOAL-WINS", cap["obligations"][0] == VERBATIM and cap["obligations_source"] == "goal file",
          (cap["obligations"][:1], cap["obligations_source"]))
    check("V-OBL-STATED-KEPT", cap.get("obligations_stated") == [PARAPHRASE], cap.get("obligations_stated"))

    gb = goal_file(b, with_next=False)
    capb = ro.compile_capsule("sid-obl-2", str(b), None, goal=str(gb), next_items=[PARAPHRASE], summary="s")
    check("V-OBL-EXPLICIT-FALLBACK", capb["obligations"] == [PARAPHRASE] and capb["obligations_source"] == "explicit",
          (capb["obligations"], capb["obligations_source"]))

    capn = ro.compile_capsule("sid-obl-3", str(b), None, goal=None, next_items=["x"], summary="s")
    check("V-OBL-UNNAMED-GOAL-UNCHANGED", capn["obligations"] == ["x"] and capn["obligations_source"] == "explicit",
          (capn["obligations"], capn["obligations_source"], capn["goal"].get("state")))

    want = {q["key"]: q["a"] for q in ro.exam(cap, ro.reality_now(cap, str(a)))}["next"]
    check("V-OBL-CERTIFY-VERBATIM", ro._matches("next", want, VERBATIM) and not ro._matches("next", want, PARAPHRASE),
          f"key={want[:60]!r}")

    ga.write_text(ga.read_text(encoding="utf-8").replace(VERBATIM, "Ship the parser fix"), encoding="utf-8")
    check("V-OBL-LIVE", ro.obligations_now(cap)[0] == "Ship the parser fix", ro.obligations_now(cap)[:1])

    # V-LATEST-KCLEAR: the /kclear path, not the CLI, must leave the frontier pointer.
    work, state = tmp / "kc", tmp / "state"
    work.mkdir()
    gk = goal_file(work)
    subprocess.run([ro._git_exe(), "-C", str(work), "init", "-q"], check=True, capture_output=True)
    env = dict(os.environ, CPP_ROLLOVER_STATE_DIR=str(state), CLAUDE_CODE_SESSION_ID="sid-kclear-1")
    code = ("import sys; sys.path.insert(0, %r); import session_checkpoint as sc; "
            "print(sc.seal_capsule({'goal': %r, 'pending': [%r], 'summary': 's'}, 'sid-kclear-1'))"
            % (str(HERE), str(gk), PARAPHRASE))
    out = subprocess.run([sys.executable, "-c", code], cwd=str(work), env=env, capture_output=True, text=True, timeout=120)
    caps = sorted((state / "capsules").glob("*.json")) if (state / "capsules").is_dir() else []
    ptrs = sorted((state / "latest").glob("*.json")) if (state / "latest").is_dir() else []
    ok = False
    if caps and len(ptrs) == 1:
        p = json.loads(ptrs[0].read_text(encoding="utf-8"))
        ok = (Path(p["capsule"]).resolve() == caps[0].resolve()
              and p["sha256"] == hashlib.sha256(caps[0].read_bytes()).hexdigest())
    check("V-LATEST-KCLEAR", ok, (out.stdout.strip()[-120:] or out.stderr.strip()[-200:], [x.name for x in ptrs]))
    if caps:
        sealed = json.loads(caps[0].read_text(encoding="utf-8"))
        check("V-OBL-KCLEAR-VERBATIM", sealed["obligations"][:1] == [VERBATIM], sealed["obligations"][:1])
    else:
        check("V-OBL-KCLEAR-VERBATIM", False, "no capsule sealed")

    print(f"OBLIGATIONS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
