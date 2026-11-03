"""Phase 5 smoke fixture: ~20K chars of routine log with ONE buried verdict line carrying a per-run code.

usage: python phase5_fixture.py <key>   (key = a short run label; the code is derived from it and never printed elsewhere)
No line other than the verdict line carries the key or the code, so a model can answer only from that line.
Size window: above the CCR projection budget (8,000 chars) and below the host's own persisted-output threshold. At 800
lines (52.3 KB) Claude Code 2.1.317 persisted the result itself (persistedOutputPath), which CCR rightly never projects,
so the first smoke measured nothing (phase5-smoke-null-host-2.1.317.json).
"""
import hashlib, sys

LINES, BURIED = 280, 157
key = sys.argv[1] if len(sys.argv) > 1 else "k0"
code = hashlib.sha256(("phase5:" + key).encode()).hexdigest()[:6].upper()
for i in range(LINES):
    if i == BURIED:
        print(f"RESULT verdict=FAIL shard=19 code={code}")
    else:
        print(f"row {i:03d} status ok records processed checksum matched {'.' * 12}")
