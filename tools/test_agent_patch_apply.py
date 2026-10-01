#!/usr/bin/env python3
"""V-PATCH-* gates: the parent's half of patch-proposal-v1 (tools/agent_patch_apply.py).

The fixture is the REAL first proposal from harness-optimizer on GEX44 (2026-10-01, record
vault/audits/agent_estate/real_boundary/s4/ho_b.json): correct body, miscounted hunk header.
A control proves plain `git apply` rejects it, so the recount gate cannot pass on a patch
that was never broken.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_patch_apply as P  # noqa: E402

HOOK = "{\"matcher\": \"Edit\", \"hooks\": [{\"type\": \"command\", \"command\": \"bash -c 'echo edited $(cat) >> /tmp/edits.log'\"}]}"
SETTINGS = "{\n  \"hooks\": {\n    \"PostToolUse\": [\n      " + HOOK + ",\n      " + HOOK + "\n    ]\n  }\n}\n"
REAL_PATCH = ("--- a/.claude/settings.json\n+++ b/.claude/settings.json\n@@ -2,7 +2,6 @@\n"
              "   \"hooks\": {\n     \"PostToolUse\": [\n-      " + HOOK + ",\n       " + HOOK + "\n"
              "     ]\n   }\n")
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def reply(*patches):
    return "**Baseline** ...\n\n" + "".join(f"```diff\n{p}```\n\n" for p in patches) + "**Rollback** ..."


def repo(t: Path) -> Path:
    r = t / "target"
    (r / ".claude").mkdir(parents=True)
    (r / ".claude" / "settings.json").write_bytes(SETTINGS.encode())
    g = P._git()
    for cmd in (["init", "-q"], ["add", "-A"],
                ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", "commit", "-qm", "base"]):
        subprocess.run([g, "-C", str(r), *cmd], check=True, capture_output=True)
    return r


def refused(fn):
    try:
        fn()
        return None
    except P.PatchRefused as e:
        return e.code


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        r = repo(Path(td))
        f = r / ".claude" / "settings.json"
        patch = P.extract_patch(reply(REAL_PATCH))

        # Control: the fixture really is miscounted.
        # Bytes: in text mode Windows would add \r and the rejection would prove nothing.
        plain = subprocess.run([P._git(), "-C", str(r), "apply", "--check", "-"], input=patch.encode(),
                               capture_output=True)
        err = plain.stderr.decode("utf-8", "replace").strip()
        check("V-PATCH-CONTROL-PLAIN-REJECTS", plain.returncode != 0 and "corrupt patch" in err, err[:60])

        res = P.apply_patch(patch, r, apply=False)
        check("V-PATCH-DRY-RUN-CHANGES-NOTHING", res["checked"] and not res["applied"]
              and f.read_bytes() == SETTINGS.encode(), f"{res}")

        res = P.apply_patch(patch, r, apply=True)
        after = f.read_text(encoding="utf-8")
        check("V-PATCH-RECOUNT-APPLIES", res["applied"] and after.count('"matcher"') == 1
              and json.loads(after)["hooks"]["PostToolUse"][0]["matcher"] == "Edit",
              f"files={res['files']} entries={after.count(chr(34) + 'matcher' + chr(34))}")

        # Recount forgives the header, never the body: applying again must fail (context gone).
        check("V-PATCH-BODY-MUST-MATCH", refused(lambda: P.apply_patch(patch, r)) == "CHECK_FAILED",
              "re-applying to the patched file is refused")

        check("V-PATCH-NO-DIFF", refused(lambda: P.extract_patch("no patch here")) == "NO_DIFF", "")
        check("V-PATCH-MULTIPLE-DIFFS",
              refused(lambda: P.extract_patch(reply(REAL_PATCH, REAL_PATCH))) == "MULTIPLE_DIFFS", "")
        esc = REAL_PATCH.replace("a/.claude/settings.json", "a/../outside.json", 1)
        check("V-PATCH-ESCAPE-DOTDOT", refused(lambda: P.extract_patch(reply(esc))) == "PATH_ESCAPES_ROOT", "")
        absp = REAL_PATCH.replace("+++ b/.claude/settings.json", "+++ /etc/passwd", 1)
        check("V-PATCH-ESCAPE-ABSOLUTE", refused(lambda: P.extract_patch(reply(absp))) == "PATH_ESCAPES_ROOT", "")
        check("V-PATCH-NOT-A-REPO", refused(lambda: P.apply_patch(patch, Path(td))) == "NOT_A_REPO", "")

    total = passes + fails
    print(f"PATCH_APPLY_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
