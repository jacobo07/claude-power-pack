"""compare_runs.py - phase-local fixture (Phase 5, plan 05-02): compare two recorded boundary-suite runs.

Usage: python3 -I compare_runs.py BEFORE_RECORD AFTER_RECORD

Reads two record_run.py records of tools/test_hook_boundary.py (format read from the before record:
`  [STATUS] GATE-ID: detail` per gate, a `HOOK_PASS=n/N  threshold=n/N` footer, a `# exit=N` footer).
Prints one line per gate (before status, after status, SAME or CHANGED), both footers, and exactly one
`VERDICT:` line. Verdict rules (preregistered as G4 in 05-02-PLAN.md, not tuned after seeing the runs):

  1. FAIL      a gate that was PASS before is not PASS after (or is missing), or the after run cannot be read.
  2. NOT_SHOWN the before run was not green (full-count footer, exit 0, every gate PASS). Never becomes PASS.
  3. FAIL      the after run is not green.
  4. PASS      both green and every gate line is identical; otherwise NOT_SHOWN (lines differ, so
               "unchanged" is not shown).

No gate is named anywhere in this file: every behaviour is derived from the line text. Stdlib only,
registered nowhere, imported by nothing under tools/.
"""
import re
import sys

GATE_RE = re.compile(r"^\s*\[(?P<status>[A-Z_]+)\]\s+(?P<gate>[A-Za-z0-9_.-]+):\s*(?P<detail>.*)$")
FOOT_RE = re.compile(r"^(?P<name>[A-Z_]+)=(?P<p>\d+)/(?P<n>\d+)\s+threshold=(?P<tp>\d+)/(?P<tn>\d+)\s*$")
EXIT_RE = re.compile(r"^# exit=(?P<code>\S+)\s*$")


def parse(path):
    gates, footer, exit_code = {}, None, None
    order = []
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if line.startswith("#"):
                m = EXIT_RE.match(line)
                if m:
                    exit_code = m.group("code")
                continue
            m = GATE_RE.match(line)
            if m:
                g = m.group("gate")
                if g not in gates:
                    order.append(g)
                gates[g] = (m.group("status"), m.group("detail"), line.strip())
                continue
            m = FOOT_RE.match(line)
            if m:
                footer = tuple(int(m.group(k)) for k in ("p", "n", "tp", "tn")) + (m.group("name"),)
    return {"gates": gates, "order": order, "footer": footer, "exit": exit_code}


def green(run):
    f = run["footer"]
    footer_ok = f is not None and f[0] == f[1] and f[2] == f[3] and f[1] > 0
    return (footer_ok and run["exit"] == "0" and len(run["gates"]) > 0
            and all(v[0] == "PASS" for v in run["gates"].values()))


def fmt_footer(run):
    f = run["footer"]
    foot = "UNPARSED" if f is None else "%s=%d/%d threshold=%d/%d" % (f[4], f[0], f[1], f[2], f[3])
    return "%s  exit=%s" % (foot, run["exit"])


def main(argv):
    if len(argv) != 3:
        print("usage: compare_runs.py BEFORE AFTER", file=sys.stderr)
        return 2
    try:
        before, after = parse(argv[1]), parse(argv[2])
    except OSError as exc:
        print("COMPARE_UNREADABLE: %s" % type(exc).__name__, file=sys.stderr)
        return 2
    names = list(before["order"]) + [g for g in after["order"] if g not in before["gates"]]
    differing, regressed = [], []
    for g in names:
        b, a = before["gates"].get(g), after["gates"].get(g)
        bs = b[0] if b else "ABSENT"
        as_ = a[0] if a else "ABSENT"
        same_status = bs == as_
        same_line = b is not None and a is not None and b[2] == a[2]
        if bs == "PASS" and as_ != "PASS":
            regressed.append(g)
        if not same_line:
            differing.append(g)
        print("GATE %s  before=%s after=%s  %s%s" % (
            g, bs, as_, "SAME" if same_status else "CHANGED",
            "" if same_line or not same_status else "  (status same, detail text differs)"))
    print("BEFORE %s" % fmt_footer(before))
    print("AFTER  %s" % fmt_footer(after))
    # Sub-checks a gate line itself reports as not evaluated: surfaced from the text, never by gate name.
    for label, run in (("before", before), ("after", after)):
        for g in run["order"]:
            if "UNEVALUATED" in run["gates"][g][1]:
                print("NOTE %s run: gate %s reports an UNEVALUATED sub-check (isolated HOME has no live settings); "
                      "the real-HOME run is LP-12, LAPTOP-ONLY / UNJUDGED" % (label, g))
    after_readable = after["footer"] is not None and bool(after["gates"])
    if regressed or not after_readable:
        verdict, reason = "FAIL", ("gate(s) regressed: %s" % ", ".join(regressed)) if regressed else "after run unreadable (no gates or footer)"
    elif not green(before):
        verdict, reason = "NOT_SHOWN", "the before run was not green, so 'keeps green' is not shown (unchanged may still hold)"
    elif not green(after):
        verdict, reason = "FAIL", "the after run is not green"
    elif not differing:
        verdict, reason = "PASS", "before green and every gate line identical in the after run (isolated HOME, GEX44)"
    else:
        verdict, reason = "NOT_SHOWN", "both green but gate lines differ: %s" % ", ".join(differing)
    print("VERDICT: %s - %s" % (verdict, reason))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
