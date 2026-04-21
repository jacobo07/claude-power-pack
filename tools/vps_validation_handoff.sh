#!/usr/bin/env bash
# vps_validation_handoff.sh -- MC-OVO-32-F / 31-Q / 34-V VPS validation bundle.
#
# Runs the three remote-dependent gates from this session's MC-OVO cycle on
# the VPS where QEMU is installed and AF_UNIX works. Paste the full output
# back to the Owner for evidence archiving in vault/audits/.
#
# Owner usage (on VPS 204.168.166.63, from the claude-power-pack working tree):
#   git pull
#   bash tools/vps_validation_handoff.sh 2>&1 | tee /tmp/mc_ovo_vps_$(date +%Y%m%dT%H%M%SZ).log
#
# Exit codes:
#   0 -- all three gates pass
#   1 -- MC-OVO-32-F (FastAPI scaffolder) failed
#   2 -- MC-OVO-31-Q (QEMU dumper scaffolder) failed
#   3 -- MC-OVO-34-V (mistake-hook xplat) failed
#   4 -- environment unfit (missing python3 / qemu-system-x86_64)

set -uo pipefail

HEADER() { printf '\n================================================================\n%s\n================================================================\n' "$1"; }

HEADER "env probe"
echo "host:     $(hostname)"
echo "uname:    $(uname -a)"
echo "python3:  $(python3 --version 2>&1)"
if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo "qemu-x86: $(qemu-system-x86_64 --version | head -1)"
else
    echo "qemu-x86: MISSING"
fi
echo "git HEAD: $(git rev-parse --short HEAD) -- $(git log -1 --format=%s)"

if ! command -v python3 >/dev/null 2>&1; then
    echo "FATAL: python3 missing" >&2
    exit 4
fi
if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo "FATAL: qemu-system-x86_64 missing -- sudo apt install -y qemu-system-x86 qemu-system-arm" >&2
    exit 4
fi

# -----------------------------------------------------------------------------
HEADER "MC-OVO-32-F -- FastAPI scaffolder (3-gate cascade: pip + pytest + uvicorn)"
FASTAPI_OUT=$(mktemp -d -t fastapi-vps-XXXXXX)
rm -rf "${FASTAPI_OUT}/demo"
python3 tools/scaffold_fastapi.py --out "${FASTAPI_OUT}/demo" --name demo
FASTAPI_EXIT=$?
if [ "$FASTAPI_EXIT" -ne 0 ]; then
    echo "RESULT: MC-OVO-32-F FAIL (exit=$FASTAPI_EXIT)"
    exit 1
fi
echo "RESULT: MC-OVO-32-F PASS"

# -----------------------------------------------------------------------------
HEADER "MC-OVO-31-Q -- QEMU dumper scaffolder (3-gate cascade: pip + pytest + qemu+CLI)"
QEMU_OUT=$(mktemp -d -t qdump-vps-XXXXXX)
rm -rf "${QEMU_OUT}/qdump"
python3 tools/scaffold_qemu_dumper.py --out "${QEMU_OUT}/qdump" --name qdump
QEMU_EXIT=$?
if [ "$QEMU_EXIT" -ne 0 ]; then
    echo "RESULT: MC-OVO-31-Q FAIL (exit=$QEMU_EXIT)"
    exit 2
fi
echo "RESULT: MC-OVO-31-Q PASS"

# -----------------------------------------------------------------------------
HEADER "MC-OVO-34-V -- mistake-hook cross-platform parity test"
python3 tests/test_mistake_frequency_xplat.py
PARITY_EXIT=$?
if [ "$PARITY_EXIT" -ne 0 ]; then
    echo "RESULT: MC-OVO-34-V FAIL (exit=$PARITY_EXIT)"
    exit 3
fi
echo "RESULT: MC-OVO-34-V PASS"

# -----------------------------------------------------------------------------
HEADER "ALL VPS GATES PASS"
echo "MC-OVO-32-F (FastAPI 3-gate):      PASS"
echo "MC-OVO-31-Q (QEMU dumper 3-gate):  PASS"
echo "MC-OVO-34-V (mistake-hook parity): PASS"
echo ""
echo "Next: archive this log to vault/audits/vps_validation_\$(date +%Y%m%dT%H%M%SZ).log and commit."
exit 0
