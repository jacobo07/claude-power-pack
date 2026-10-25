"""V-S3-* gates: packet digest normalisation and hold backoff (flow-compression S3). No host state."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="s3-admission-")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

passes = fails = 0


def check(name, cond, detail=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {name} {detail}")
    else:
        fails += 1
        print(f"FAIL {name} {detail}")


tmp = Path(tempfile.mkdtemp(prefix="s3-pkt-"))
lf, crlf, bom, other = tmp / "lf.md", tmp / "crlf.md", tmp / "bom.md", tmp / "other.md"
lf.write_bytes(b"# WU\nline one\nline two\n")
crlf.write_bytes(b"# WU\r\nline one\r\nline two\r\n")
bom.write_bytes(b"\xef\xbb\xbf# WU\nline one\nline two\n")
other.write_bytes(b"# WU\nline one\nline TWO\n")
d = gm._packet_digest(str(lf))
check("V-S3-DIGEST-CRLF-EQUAL", gm._packet_digest(str(crlf)) == d)
check("V-S3-DIGEST-BOM-EQUAL", gm._packet_digest(str(bom)) == d)
check("V-S3-DIGEST-CONTENT-DIFFERS", gm._packet_digest(str(other)) != d)   # control: real change still detected
check("V-S3-DIGEST-MISSING-NONE", gm._packet_digest(str(tmp / "nope.md")) is None)
check("V-S3-LEGACY-RAW-DIGEST-STILL-MATCHES", gm._packet_digest_matches(gm._packet_digest_raw(str(crlf)), str(crlf)))
check("V-S3-MATCH-REJECTS-NONE-AND-WRONG", not gm._packet_digest_matches(None, str(lf))
      and not gm._packet_digest_matches("0" * 64, str(lf)))

b = [gm.gsd_hold_backoff_s(k) for k in range(6)]
check("V-S3-BACKOFF-DOUBLES-THEN-CAPS", b == [300, 600, 1200, 1800, 1800, 1800], str(b))

os.environ["CPP_GSD_HOLD_BACKOFF"] = "off"
check("V-S3-KILL-SWITCH", gm.gsd_backoff_on() is False)
del os.environ["CPP_GSD_HOLD_BACKOFF"]
check("V-S3-BACKOFF-DEFAULT-ON", gm.gsd_backoff_on() is True)

# mutant: a digest that does not normalise must fail the CRLF gate (the gate can go red)
orig = gm._normalise_packet
gm._normalise_packet = lambda data: data
check("V-S3-MUTANT-NO-NORMALISE-GOES-RED", gm._packet_digest(str(crlf)) != gm._packet_digest(str(lf)))
gm._normalise_packet = orig
orig_b = gm.gsd_hold_backoff_s
gm.gsd_hold_backoff_s = lambda k, base=300, cap=1800: 0
check("V-S3-MUTANT-NO-BACKOFF-GOES-RED", gm.gsd_hold_backoff_s(3) != 1200)
gm.gsd_hold_backoff_s = orig_b

print(f"S3_PASS={passes}/{passes + fails}  threshold=all")
sys.exit(0 if fails == 0 else 1)
