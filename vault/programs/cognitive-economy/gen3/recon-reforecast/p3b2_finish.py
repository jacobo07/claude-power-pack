"""P3b-2 steps 9-10 only (registry + bundles already written by p3b2_promote.py). Exit 3 = host floor, nothing written."""
import json, os, sys

D = r"C:\Users\User\Apps\recon_work\wt_keosdtk_home\tools\wros\binary\decomp\gex44"
sys.path.insert(0, D)
import src_bundles as SB  # noqa: E402
import levels  # noqa: E402

SEALED = ["main:801A2CC0", "main:8020EAD4", "main:8026BE34", "main:802B21A4", "main:803571D8"]


def src(path=levels.LEDGER):
    return {e: json.loads(r.decode("utf-8"))["dimensions"]["SRC"] for e, r in levels.read_ledger(path).items()}


free = levels.host_free_mb()
print("HOST free_mb=%d floor=%d" % (free, levels.FLOOR_MB))
if free < levels.FLOOR_MB:
    print("STOP HOST_FLOOR (nothing written)")
    sys.exit(3)
store = levels.load_store()
ids = sorted(e for e in SB.entity_ids() if store.src_bundle(e) is not None)
print("BUNDLED_IDS=%d" % len(ids))
before = src()
proven_before = sorted(i for i, d in before.items() if d["verdict"] == "PROVEN")
print("SRC_PROVEN_BEFORE=%d" % len(proven_before))
pr = levels.promote(ids=ids, store=store)
print("PROMOTE rows=%d promoted=%d ledger_sha256=%s" % (pr["rows"], pr["promoted"], pr["ledger_sha256"]))
after = src()
proven_after = sorted(i for i, d in after.items() if d["verdict"] == "PROVEN")
expected = sorted(set(proven_before) | set(ids))
not_proven = sorted(i for i in ids if after.get(i, {}).get("verdict") != "PROVEN")
via_bundle = sorted(i for i in ids if (after.get(i, {}).get("evidence") or {}).get("bundle_sha256"))
lost = sorted(i for i in SEALED if after.get(i, {}).get("verdict") != "PROVEN")
print("SRC_PROVEN_AFTER=%d expected=%d rise=%d" % (len(proven_after), len(expected), len(proven_after) - len(proven_before)))
print("PROMOTED_NOT_PROVEN=%d %s" % (len(not_proven), [(i, after.get(i, {}).get("verdict")) for i in not_proven[:20]]))
print("SEALED_LOST=%s PROVEN_VIA_BUNDLE=%d/%d" % (lost, len(via_bundle), len(ids)))
drift = SB.impact(levels.load_store())
print("POST_IMPACT_DRIFTING=%d" % sum(1 for v in drift.values() if v["drift"]))
ok = proven_after == expected and not not_proven and not lost and len(via_bundle) == len(ids)
print("P3B2_CHECK=%s" % ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
