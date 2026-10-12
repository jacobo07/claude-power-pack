"""V-CLAIM-* gates for the authoritative result contract (receipt_judge divergence + tools/claim_evidence.py).

    python tools/test_claim_evidence.py      # exit 0 only if every gate passes
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import claim_evidence as ce  # noqa: E402
import receipt_judge as rj  # noqa: E402

PASS, FAIL = [], []


def gate(name: str, ok: bool, ev: str) -> None:
    (PASS if ok else FAIL).append(name)
    print(("PASS " if ok else "FAIL ") + name + "  " + ev)


def receipt(d: Path, body: str) -> str:
    p = d / "WU-X-receipt.md"
    p.write_text(body, encoding="utf-8")
    return str(p)


def cert_cmd(values: dict) -> list:
    return [sys.executable, "-c", "import json; print('noise'); print(json.dumps(%r))" % (values,)]


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # Arrange: the W12 shape -- the worker claims 14, the ledger certifies 12
        r = receipt(d, "# WU-W12 receipt\nStatus: DONE\nClaims: match=14, sent=22\n")
        gate("V-CLAIM-NO-CERT-UNCHANGED", rj.receipt_status(r) == "DONE" and rj.divergences(r) == [],
             "no certificate -> status %s (old reading kept)" % rj.receipt_status(r))
        rc, out = ce.certify(r, cert_cmd({"match": 12, "sent": 22}))
        gate("V-CLAIM-W12-DIVERGENT", rc == 3 and out["status"] == "DIVERGENT" and not rj.is_done(r)
             and not rj.is_closed(r), "rc=%s status=%s" % (rc, out["status"]))
        dv = out["divergences"]
        gate("V-CLAIM-TYPED-ROW", len(dv) == 1 and dv[0]["class"] == "CLAIM_EVIDENCE_DIVERGENCE"
             and dv[0]["key"] == "match" and str(dv[0]["claim"]) == "14" and dv[0]["certified"] == 12, json.dumps(dv))
        # control: the claim agrees with the certificate -> the unit closes (a judge that refuses everything fails here)
        r2 = receipt(d, "# WU-W12 receipt\nStatus: DONE\n- **Claims:** match=12, sent=22.0\n")
        rc2, out2 = ce.certify(r2, cert_cmd({"match": 12, "sent": 22}))
        gate("V-CLAIM-AGREE-DONE", rc2 == 0 and out2["status"] == "DONE" and rj.is_done(r2),
             "rc=%s status=%s" % (rc2, out2["status"]))
        # the certificate carries a status: a receipt saying DONE over a certified FAILED is divergent
        r3 = receipt(d, "# WU receipt\nStatus: DONE\n")
        rc3, out3 = ce.certify(r3, cert_cmd({"status": "FAILED"}))
        gate("V-CLAIM-STATUS-DIVERGENT", rc3 == 3 and out3["status"] == "DIVERGENT"
             and out3["divergences"][0]["key"] == "status", "rc=%s %s" % (rc3, out3["divergences"]))
        # a failed certifying command writes no certificate and certifies nothing
        r4 = receipt(d, "# WU receipt\nStatus: DONE\nClaims: match=14\n")
        rj.certificate_path(r4).unlink(missing_ok=True)
        rc4, out4 = ce.certify(r4, [sys.executable, "-c", "import sys; sys.exit(1)"])
        gate("V-CLAIM-CMD-FAIL-NO-CERT", rc4 == 2 and not rj.certificate_path(r4).exists()
             and rj.receipt_status(r4) == "DONE", "rc=%s cert=%s" % (rc4, rj.certificate_path(r4).exists()))
        # a corrupt certificate is a divergence, never silently ignored
        rj.certificate_path(r4).write_text("{not json", encoding="utf-8")
        gate("V-CLAIM-CORRUPT-CERT", rj.receipt_status(r4) == "DIVERGENT", "status=%s" % rj.receipt_status(r4))
        # claims parser: decoration, case, several lines
        cl = rj.claims_of_text("> **Claims:** Match=3; tokens=4,388,094\nClaims: sent=22\n")
        gate("V-CLAIM-PARSE", cl.get("match") == "3" and cl.get("sent") == "22" and cl.get("tokens") == "4,388,094",
             json.dumps(cl))
        r5 = receipt(d, "# WU receipt\nStatus: DONE\nClaims: tokens=4,388,094, match=12\n")
        rc5, out5 = ce.certify(r5, cert_cmd({"tokens": 4388094, "match": 12}))
        gate("V-CLAIM-THOUSANDS-AGREE", rc5 == 0 and out5["status"] == "DONE", "rc=%s %s" % (rc5, out5["divergences"]))
    print("CLAIM_EVIDENCE=%d/%d" % (len(PASS), len(PASS) + len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
