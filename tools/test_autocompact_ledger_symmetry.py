#!/usr/bin/env python
"""V-ACD-* -- every terminal outcome of the auto-compact daemon must ledger.

Why this exists, measured 2026-09-23. The daemon's three FAILURE paths each
wrote a ledger row (refused x2, withdrawn) and its SUCCESS path wrote only to
the daemon's own log file. The ledger was therefore structurally incapable of
reporting a compact that worked: a query over it returned 26 requests and 0
deliveries, and that zero was believed -- while the daemon's log held two SENT
rows from the same day, one of them for the very session doing the querying.

A zero bounded by the instrument's vocabulary is UNKNOWN, never evidence.

This gate asserts the CLASS, not the instance. Pinning the one line that was
missing would go green the day someone adds a fourth outcome without a ledger
row, which is exactly how the defect arrived. So it sweeps every terminal
outcome and requires each to ledger, with:

  * a POPULATION FLOOR, so a sweep that silently stopped matching cannot read
    clean -- an empty "unledgered" list is the dangerous state;
  * a SYNTHETIC red subject, so the drill survives the daemon being correct and
    cannot be fixed out from under the assertion;
  * a SYNTHETIC green control beside it, so a predicate that flags everything
    cannot pass the red branch and look like a working detector.
"""
import re
import sys
from pathlib import Path

DAEMON = Path(__file__).resolve().parent.parent / "hooks" / "auto-compact-sendkeys-daemon.ps1"

# A terminal outcome is a log line announcing that this flag's fate is decided.
# Matched on the daemon's own uppercase verdict tokens, not on function names,
# so a new outcome written in a new function is still in the population.
TERMINAL = re.compile(r'Log\s+"(?:inbox:\s*)?(SENT|REFUSED|WITHDRAWN)\b')
LEDGER = "Write-LedgerRow"
LOOKAHEAD = 20   # lines after the verdict in which the ledger write must appear

MIN_TERMINAL_OUTCOMES = 4   # SENT + REFUSED(flag) + REFUSED(no-exact) + WITHDRAWN

passes = 0
fails = 0


def _ok(gate, evidence):
    global passes
    passes += 1
    print("  PASS %-34s %s" % (gate, evidence))


def _fail(gate, diagnostic):
    global fails
    fails += 1
    print("  FAIL %-34s %s" % (gate, diagnostic))


def unledgered(text):
    """-> (outcomes_found, [(lineno, verdict) lacking a ledger write])"""
    lines = text.splitlines()
    found = []
    missing = []
    for i, line in enumerate(lines):
        m = TERMINAL.search(line)
        if not m:
            continue
        found.append((i + 1, m.group(1)))
        window = "\n".join(lines[i:i + LOOKAHEAD])
        if LEDGER not in window:
            missing.append((i + 1, m.group(1)))
    return found, missing


def main():
    if not DAEMON.is_file():
        print("HARNESS-FAILED: daemon not found at %s" % DAEMON)
        return 2

    text = DAEMON.read_text(encoding="utf-8", errors="replace")
    found, missing = unledgered(text)

    # --- population floor: prove the sweep can still see its subject ----------
    if len(found) >= MIN_TERMINAL_OUTCOMES:
        _ok("V-ACD-POPULATION-FLOOR",
            "%d terminal outcomes found (floor %d): %s"
            % (len(found), MIN_TERMINAL_OUTCOMES,
               ", ".join("%s@%d" % (v, n) for n, v in found)))
    else:
        _fail("V-ACD-POPULATION-FLOOR",
              "only %d terminal outcomes matched, expected >= %d -- the sweep may "
              "have stopped seeing the daemon's verdict vocabulary"
              % (len(found), MIN_TERMINAL_OUTCOMES))

    # --- the claim -----------------------------------------------------------
    if not missing:
        _ok("V-ACD-LEDGER-SYMMETRY",
            "every terminal outcome writes a ledger row within %d lines" % LOOKAHEAD)
    else:
        _fail("V-ACD-LEDGER-SYMMETRY",
              "terminal outcomes with no ledger row: %s -- the ledger cannot report "
              "these, so any query over it reads them as never having happened"
              % ", ".join("%s@line %d" % (v, n) for n, v in missing))

    # --- synthetic red: a subject that must be caught ------------------------
    red = 'Log "SENT via=extension sid=$($e.sid)"\ncontinue\n'
    _, red_missing = unledgered(red)
    if red_missing:
        _ok("V-ACD-SYNTHETIC-RED",
            "a synthetic outcome with no ledger row is caught (%s)" % (red_missing[0][1],))
    else:
        _fail("V-ACD-SYNTHETIC-RED",
              "the detector did NOT flag a synthetic unledgered outcome -- it would "
              "report any daemon as clean")

    # --- synthetic green: the detector must not flag everything --------------
    green = 'Log "SENT via=extension sid=$($e.sid)"\nWrite-LedgerRow $e.sid \'x\' "y"\n'
    green_found, green_missing = unledgered(green)
    if green_found and not green_missing:
        _ok("V-ACD-SYNTHETIC-GREEN",
            "a synthetic outcome WITH a ledger row is not flagged")
    else:
        _fail("V-ACD-SYNTHETIC-GREEN",
              "the detector flagged a correctly-ledgered outcome (found=%d missing=%d) -- "
              "a predicate that fires on everything passes the red branch for free"
              % (len(green_found), len(green_missing)))

    print("ACD_PASS=%d/%d  threshold=4/4" % (passes, passes + fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
