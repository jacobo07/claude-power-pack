"""V-MHFI-* -- a project that inherits multi_host_fabric B1 catches a planted regression (DWS row 55).

The subject is a copy of exactly the files B1's checks read, taken from the real Orca repo. The clean copy
must be judged like the real repo (control); each plant must turn exactly its own entry VIOLATED.

Run: python tools/test_tower_mhf_inheritance_drill.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

_PP_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import donegate as dg  # noqa: E402

FAMILY = "multi_host_fabric"
ORCA = os.environ.get("CPP_MHF_SUBJECT_REPO", r"C:\Users\User\Apps\orca-rb-live-wt")
TRANSFER = "multi_host_fabric-transfer-is-read-back-on-the-target"
CONSENT = "multi_host_fabric-consent-refusal-is-not-failure"
_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-44s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-44s %s" % (gate, diagnostic))


def _check_path(check: str) -> str:
    kind, _, rest = check.partition(":")
    return rest.split("::", 1)[0] if kind == "regex" else rest


def _violated(report) -> list[str]:
    return sorted(e["entry_id"] for e in report["entries"] if e["verdict"] != dg.APPLIED_VERIFIED)


def _plant(subject, rel, old, new):
    p = os.path.join(subject, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    if old not in text:
        raise AssertionError(f"plant anchor {old!r} not in {rel}")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new))


def main() -> int:
    print("V-MHFI gates")
    active = bl.active_entries(FAMILY)
    paths = sorted({_check_path(e["check"]) for e in active if isinstance(e.get("check"), str)})
    _check("V-MHFI-SUBJECT-FROM-CHECKS", len(active) >= 8 and len(paths) >= 5,
           f"{len(active)} active entries read {len(paths)} files", f"entries={len(active)} paths={paths}")
    real = dg.judge(FAMILY, ORCA)
    _check("V-MHFI-REAL-REPO-GREEN", not real["would_block"] and not _violated(real),
           f"{real['judged_under']} on the real repo: all APPLIED_VERIFIED", f"violated={_violated(real)}")

    tmp = tempfile.mkdtemp(prefix="mhfi-")
    try:
        clean = os.path.join(tmp, "clean")
        for rel in paths:
            dst = os.path.join(clean, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ORCA, *rel.split("/")), dst)
        c = dg.judge(FAMILY, clean)
        _check("V-MHFI-CLEAN-COPY-MATCHES-REAL", not c["would_block"] and not _violated(c)
               and c["judged_under"] == real["judged_under"],
               "the file-only copy is judged exactly like the real repo (control)", f"violated={_violated(c)}")

        p1 = os.path.join(tmp, "p1")
        shutil.copytree(clean, p1)
        # Plant: the resume spec stops reading the transfer back on the target.
        _plant(p1, "tests/e2e/hwf-two-host-continue-here-resume.spec.ts", "XFER_BYTES=", "XFER_SKIPPED=")
        r1 = dg.judge(FAMILY, p1)
        _check("V-MHFI-PLANT-TRANSFER-READBACK-RED", r1["would_block"] and _violated(r1) == [TRANSFER],
               f"only {TRANSFER} VIOLATED, would_block", f"violated={_violated(r1)} block={r1['would_block']}")

        p2 = os.path.join(tmp, "p2")
        shutil.copytree(clean, p2)
        # Plant: the consent-refusal module is deleted.
        os.remove(os.path.join(p2, "src", "main", "workspace-execution-consent.ts"))
        r2 = dg.judge(FAMILY, p2)
        _check("V-MHFI-PLANT-CONSENT-MODULE-RED", r2["would_block"] and _violated(r2) == [CONSENT],
               f"only {CONSENT} VIOLATED, would_block", f"violated={_violated(r2)} block={r2['would_block']}")
        _check("V-MHFI-VERDICT-STAMPED", all(x["judged_under"] == real["judged_under"] for x in r1["entries"]),
               f"each finding stamped {real['judged_under']}", "a finding without the generation stamp")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("MHFI_PASS=%d/%d  threshold=%d/%d" % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
