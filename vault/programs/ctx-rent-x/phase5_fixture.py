"""Phase 5 smoke fixture: ~40K chars of routine log with ONE buried verdict line carrying a per-run code.

usage: python phase5_fixture.py <key>   (key = a short run label; the code is derived from it and never printed elsewhere)
No line other than the verdict line carries the key or the code, so a model can answer only from that line.
"""
import hashlib, sys

key = sys.argv[1] if len(sys.argv) > 1 else "k0"
code = hashlib.sha256(("phase5:" + key).encode()).hexdigest()[:6].upper()
for i in range(800):
    if i == 437:
        print(f"RESULT verdict=FAIL shard=19 code={code}")
    else:
        print(f"row {i:03d} status ok records processed checksum matched {'.' * 12}")
