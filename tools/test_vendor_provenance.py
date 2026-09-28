"""V-VENDOR gates for tools/vendor_provenance.py, on a synthetic tree (never the real vendor/).
    python tools/test_vendor_provenance.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import vendor_provenance as vp  # noqa: E402

passes = fails = 0


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        vp.VENDOR = Path(td) / "vendor"
        vp.RECORDS = vp.VENDOR / "_provenance"
        tree = vp.VENDOR / "synthetic"
        (tree / "lib").mkdir(parents=True)
        (tree / "lib" / "a.cjs").write_bytes(b"module.exports = 1;\n")
        (tree / "package.json").write_bytes(b'{"version":"0.0.1","license":"MIT"}\n')
        z = Path(td) / "src.zip"
        import zipfile
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("x.txt", "x")
        vp.build("synthetic", z, None, None)

        out, _ = vp.verify(["synthetic"], fresh=False)
        gate("V-VENDOR-GREEN", out == vp.VALID, out)

        (tree / "lib" / "a.cjs").write_bytes(b"module.exports = 1;\r\n")  # a line-ending filter
        out, res = vp.verify(["synthetic"], fresh=False)
        gate("V-VENDOR-RED-CHANGED", out == vp.SUBJECT_INVALID and res[0]["changed"] == ["lib/a.cjs"], json.dumps(res[0])[:120])
        (tree / "lib" / "a.cjs").write_bytes(b"module.exports = 1;\n")

        (tree / "extra.js").write_bytes(b"")
        out, res = vp.verify(["synthetic"], fresh=False)
        gate("V-VENDOR-RED-EXTRA", out == vp.SUBJECT_INVALID and res[0]["extra"] == ["extra.js"], out)
        (tree / "extra.js").unlink()

        out, _ = vp.verify(["no-such-tree"], fresh=False)
        gate("V-VENDOR-UNREADABLE", out == vp.UNREADABLE, out)

        (vp.RECORDS / "synthetic.json").write_text("{not json", encoding="utf-8")
        out, _ = vp.verify(["synthetic"], fresh=False)
        gate("V-VENDOR-VERIFIER-FAILED", out == vp.VERIFIER_FAILED, out)

    print(f"VENDOR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
