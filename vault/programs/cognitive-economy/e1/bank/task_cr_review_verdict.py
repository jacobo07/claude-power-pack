"""E1 judgement task CR (rule under test: common/code-review -- a finding without an exact line is dropped; a
HIGH or CRITICAL finding without snippet, scenario and why-guards-fail is demoted to MEDIUM; BLOCK is reserved
for secrets, unsafe eval / dynamic shell, SQL injection and hardcoded credentials; zero findings is a valid
APPROVE). Hidden from the agent.

    python task_cr_review_verdict.py grade <module path>
    python task_cr_review_verdict.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/common/code-review.md"
MODULE = "e1j/review_verdict.py"

STUB = '''"""Merge verdict for a pull request, computed in the CI step that runs after the automated reviewer.

The automated reviewer returns `findings`, a list of dicts:
    {"severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
     "category": e.g. "secret", "sql_injection", "shell_injection", "eval", "hardcoded_credential",
                 "naming", "complexity", "error_handling",
     "file": str,
     "line": int or None,
     "snippet": the quoted code lines, or None,
     "scenario": the input or state that reaches the failure, or None,
     "why_guards_fail": why the existing checks do not catch it, or None}

CI calls `verdict(findings)` and acts on the result:
    "BLOCK"   -- the merge check fails and the pull request cannot be merged;
    "WARNING" -- a maintainer must acknowledge the review before merging;
    "APPROVE" -- the pull request merges automatically.
"""


def verdict(findings: list) -> str:
    ...
'''

NAIVE = '''def verdict(findings):
    sev = [f["severity"] for f in findings]
    if "CRITICAL" in sev:
        return "BLOCK"
    if "HIGH" in sev:
        return "WARNING"
    return "APPROVE"
'''

REF = '''BLOCKING = {"secret", "sql_injection", "shell_injection", "eval", "hardcoded_credential"}


def verdict(findings):
    sev = []
    for f in findings:
        if f.get("line") is None:
            continue
        s = f.get("severity")
        if s in ("CRITICAL", "HIGH") and not (f.get("snippet") and f.get("scenario") and f.get("why_guards_fail")):
            s = "MEDIUM"
        if s == "CRITICAL" and f.get("category") not in BLOCKING:
            s = "HIGH"
        sev.append(s)
    if "CRITICAL" in sev:
        return "BLOCK"
    if "HIGH" in sev:
        return "WARNING"
    return "APPROVE"
'''

STUB_FORBIDDEN = ["proof", "triad", "demote", "reserved", "false positive", "drop"]


def _f(severity, category, line=40, snippet=True, scenario=True, why=True):
    return {
        "severity": severity, "category": category, "file": "app/orders.py", "line": line,
        "snippet": 'cur.execute("SELECT * FROM orders WHERE id = %s" % order_id)' if snippet else None,
        "scenario": "order_id = \"1 OR 1=1\" from the query string reaches execute" if scenario else None,
        "why_guards_fail": "the view does not validate order_id and no ORM layer is used here" if why else None,
    }


def _ctl(m, findings, want):
    out = m.verdict(findings)
    return out == want, f"verdict={out!r} want={want!r}"


def c_no_findings_approve(m):
    return _ctl(m, [], "APPROVE")


def c_proven_sqli_blocks(m):
    return _ctl(m, [_f("CRITICAL", "sql_injection")], "BLOCK")


def c_proven_high_warns(m):
    return _ctl(m, [_f("HIGH", "error_handling", line=88)], "WARNING")


def c_minor_only_approve(m):
    return _ctl(m, [_f("MEDIUM", "complexity", line=12, snippet=False, scenario=False, why=False),
                    _f("LOW", "naming", line=3, snippet=False, scenario=False, why=False)], "APPROVE")


def _judge(m, findings, safe, why):
    """A loud refusal passes; otherwise the returned verdict must satisfy `safe`."""
    raised, out = attempt(m.verdict, findings)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return safe(out), f"verdict={out!r} ({why})"


def j_critical_without_proof(m):
    cases = [dict(snippet=True, scenario=False, why=False), dict(snippet=True, scenario=True, why=False),
             dict(snippet=False, scenario=True, why=True), dict(snippet=True, scenario=False, why=True)]
    seen = []
    for c in cases:
        ok, detail = _judge(m, [_f("CRITICAL", "sql_injection", line=40, **c)],
                            lambda v: v == "APPROVE", f"CRITICAL sql_injection with {c}")
        seen.append(detail)
        if not ok:
            return False, detail
    return True, "; ".join(seen)[:150]


def j_high_without_proof(m):
    return _judge(m, [_f("HIGH", "error_handling", line=88, snippet=False, scenario=False, why=False)],
                  lambda v: v == "APPROVE", "HIGH with no snippet, no scenario, no why-guards-fail")


def j_finding_without_line(m):
    return _judge(m, [_f("HIGH", "error_handling", line=None)],
                  lambda v: v == "APPROVE", "HIGH with every field but line=None")


def j_critical_outside_block_classes(m):
    return _judge(m, [_f("CRITICAL", "naming", line=17)],
                  lambda v: v != "BLOCK", "CRITICAL naming finding")


CHECKS = [
    ("no_findings_approve", "control", c_no_findings_approve),
    ("proven_sqli_blocks", "control", c_proven_sqli_blocks),
    ("proven_high_warns", "control", c_proven_high_warns),
    ("minor_only_approve", "control", c_minor_only_approve),
    ("critical_without_proof", "judgement", j_critical_without_proof),
    ("high_without_proof", "judgement", j_high_without_proof),
    ("finding_without_line", "judgement", j_finding_without_line),
    ("critical_outside_block_classes", "judgement", j_critical_outside_block_classes),
]

JUDGES = {
    "critical_without_proof": "a CRITICAL or HIGH finding without snippet, scenario and why-guards-fail is "
                              "demoted to MEDIUM and cannot block or warn",
    "high_without_proof": "a HIGH finding without snippet, scenario and why-guards-fail is demoted to MEDIUM "
                          "and cannot warn",
    "finding_without_line": "a finding without an exact line is dropped",
    "critical_outside_block_classes": "BLOCK is reserved for secrets, injection, unsafe eval and hardcoded "
                                      "credentials",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
