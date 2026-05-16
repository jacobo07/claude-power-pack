#!/usr/bin/env bash
# tests/test_oracle_delta_tier.sh — MC-OVO-110 FORENSIC enforcement smoke test.
#
# Exercises both branches of the [FORENSIC_PROBES] band check in
# tools/oracle_delta.py cmd_record_verdict. NOT idempotent — appends a
# real verdict line on the success path, then trims it off so the audit
# log stays clean.
#
# Run from project root:
#   bash tests/test_oracle_delta_tier.sh

set -e
cd "$(dirname "$0")/.."

# Prefer python3 (Linux/macOS canonical) and fall back to python (Windows
# git-bash, some venvs). Caught by VPS parity run when this script
# originally hardcoded `python` and failed on Ubuntu — see commit log.
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "FAIL: no python3 or python on PATH"
  exit 1
fi

DID=$("$PY" tools/oracle_delta.py --project . --json 2>/dev/null \
  | "$PY" -c "import sys,json; print(json.load(sys.stdin)['delta_id'])")

if [ -z "$DID" ]; then
  echo "FAIL: could not get delta_id"
  exit 1
fi
echo "delta_id=$DID"

# Test 1 — FORENSIC + A + no band → must FAIL exit 4.
set +e
"$PY" tools/oracle_delta.py --project . \
  --record-verdict A --tier FORENSIC --delta-id "$DID" \
  --council-text "no probes band here" >/dev/null 2>&1
RC=$?
set -e
if [ "$RC" -ne 4 ]; then
  echo "FAIL test1: expected exit 4, got $RC"
  exit 1
fi
echo "PASS test1: FORENSIC+A+no-band → exit 4 (Mistake #53 enforcement)"

# Test 2 — FORENSIC + A + band → must SUCCEED exit 0.
"$PY" tools/oracle_delta.py --project . \
  --record-verdict A --tier FORENSIC --delta-id "$DID" \
  --council-text "[FORENSIC_PROBES: rlp=NOT_CONFIGURED, cap=none]" >/dev/null
echo "PASS test2: FORENSIC+A+band → exit 0"

# Test 3 — DEEP + A + no band → must SUCCEED (advisory only below FORENSIC).
DID2=$("$PY" tools/oracle_delta.py --project . --json 2>/dev/null \
  | "$PY" -c "import sys,json; print(json.load(sys.stdin)['delta_id'])")
"$PY" tools/oracle_delta.py --project . \
  --record-verdict A --tier DEEP --delta-id "$DID2" \
  --council-text "no band, but DEEP doesn't require it" >/dev/null
echo "PASS test3: DEEP+A+no-band → exit 0 (advisory only)"

# Trim the 2 smoke verdicts off so the audit log stays clean.
LINES=$(wc -l < vault/audits/verdicts.jsonl)
TRIM=$((LINES - 2))
head -n "$TRIM" vault/audits/verdicts.jsonl > vault/audits/verdicts.jsonl.tmp
mv vault/audits/verdicts.jsonl.tmp vault/audits/verdicts.jsonl
echo "trimmed 2 smoke-test verdicts; audit log restored"

echo "ALL 3 TESTS PASS"
