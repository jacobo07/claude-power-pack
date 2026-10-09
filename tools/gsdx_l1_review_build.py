#!/usr/bin/env python
"""L1 review step: ordered title rules (cognition, frozen as data) -> l1/review.json for the classifier.
Applies only to rows the classifier left UNKNOWN. Every probe is re-run by the dispose gate."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsdx_l1_classify as c  # noqa: E402

ROOT, L1 = c.ROOT, c.L1
ROADMAP = r"C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\ROADMAP.md"
LC3 = r"C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle"
MP = str(ROOT / "vault/plans/gsdx-factory-master-plan.md")
SECT = str(L1 / "sections.json")


def fe(p): return [{"kind": "file_exists", "path": p}]
def gr(p, rx): return [{"kind": "grep", "path": p, "pattern": rx}]


PGO = "S-phase-14-profile-guided-optimization"
MASTER = "S-master-mission"
RULES = [
    (r"MACHINE RESTART|CROSS-MACHINE|GEX44", "WAIT_DEPENDENCY", {"depends_on": "GEX44 port (W5)", "reason": "needs the GEX44 control-plane port"}),
    (r"^S1 |PHASE 1 |S1 DURAB|CERTIFIED CLOSEOUT|PHASE 8|PHASE 9|STEWARD|PROGRAM LIVENESS|WORKER STOP|CONTROL-PLANE|DEADLOCK|FORGOTTEN MISSION|CONTINUATION|CONTINUITY", "REUSE_EXISTING", {"evidence": fe(str(ROOT / "vault/specs/gsdx-factory.RECEIPT-S1.json")), "reason": "S1 steward + certified closeout shipped (RECEIPT-S1)"}),
    (r"RESERVATION|PHANTOM|UNKNOWN IS NOT FREE|PROGRAM AUTHORITY VS", "WAIT_DEPENDENCY", {"depends_on": "ce-lifecycle-v3 INST2", "reason": "W3 residual: R4 reconciliation"}),
    (r"PREDICTIVE LEASE", "REUSE_EXISTING", {"evidence": fe(LC3 + r"\WU-S4-receipt.md"), "reason": "lc3 WU-S4 lease edge"}),
    (r"PHASE 2 |S2 |CALL ACCOUNTING|UNIT-TYPED|CALL LEGITIMACY|PURCHASE ORDER|COGNITIVE RECEIPT|MULTIDIMENSIONAL", "WAIT_DEPENDENCY", {"depends_on": "ce-lifecycle-v3 INST2", "reason": "W3 residual: calls_unit field + model-call counter"}),
    (r"PHASE 3 |S3 |GROWTH-AWARE|PHASE-AWARE|STOCHASTIC|FORECAST CONF|THREE-MISS|PROTECTED RESERVES|LEARNED COST|REFORECAST|TARGET BANDS", "REUSE_EXISTING", {"evidence": fe(LC3 + r"\WU-S3-receipt.md"), "reason": "lc3 WU-S3 growth estimator (MERGE onto it in W3)"}),
    (r"PHASE 4|L1 |OBLIGATION LEDGER|PROOF OF NON-WORK|PROOF OF NO COGNITION", "ALREADY_SATISFIED", {"evidence": gr(str(ROOT / "tools/gsd_dossier.py"), r"def dispose\("), "reason": "L1 gate tool exists"}),
    (r"PHASE 5|DO NOT INFLATE|PHASE 13|NO BUDGET-INFLATION", "DETERMINISTIC", {"reason": "W4 reforecast / autopsy is arithmetic over receipts"}),
    (r"PHASE 6|RESOLVER LADDER|SLIM-T2|FRONTIER TOKEN", "REUSE_EXISTING", {"evidence": gr(MP, r"(?i)slim-t2"), "reason": "Master Plan section 3 resolver profiles"}),
    (r"PHASE 7|READ EXTINCTION|ZERO-TRANSCRIPT|WORKER LIFETIME|CONTEXT|EPOCH|ROTATION", "REUSE_EXISTING", {"evidence": gr(MP, r"(?i)epoch length"), "reason": "Master Plan answer 5 epoch length L*"}),
    (r"A-G1", "ALREADY_SATISFIED", {"evidence": fe(str(ROOT / "vault/specs/gsdx-factory.RECEIPT-AG1.json")), "reason": "A-G1 receipt"}),
    (r"A-G[2-5]|PHASE 10|PART A|MISSION A", "WAIT_DEPENDENCY", {"depends_on": "W3 (ce-lifecycle-v3 INST2)", "reason": "W6 Part A units, after W3"}),
    (r"CROSS-PROJECT TRANSFER|REVERSE TRANSFER", "WAIT_DEPENDENCY", {"depends_on": "CP50 criterion", "reason": "transfer canary needs P3/CP50 results"}),
    (r"FULL WSR", "DEFERRED_EXTERNAL", {"reason": "gsdx plan section 5 / TRANCHE-CP50: FULL_WSR is never a budget"}),
    (r"ZERO-HOT WAITING", "ALREADY_SATISFIED", {"evidence": gr(MP, r"Zero-hot"), "reason": "Master Plan W1 zero-hot wait"}),
    (r"ECONOMIC IMMUNITY", "ALREADY_SATISFIED", {"evidence": gr(MP, r"Economic immunity"), "reason": "Master Plan answer 13"}),
    (r"PRODUCTION REALITY GATE", "DETERMINISTIC", {"reason": "W8 closeout checks the reality gate over receipts"}),
    (r"PART B COORDINATION", "WAIT_DEPENDENCY", {"depends_on": "W7 Part B on GEX44", "reason": "coordination economics measured during W7"}),
    (r"UWCP","WAIT_DEPENDENCY", {"depends_on": "GEX44 port (W5)", "reason": "Master Plan W5: UWCP evaluated at the port"}),
    (r"MASTER DONE-GATE|FINAL META|CLOSEOUT ECON|BUDGET MASTER|ECONOMIC MASTER|HANDOFF", "DETERMINISTIC", {"reason": "W8 closeout gate evaluated over receipts"}),
    (r"PREAMBLE|MASTER MISSION|SCOPE BOUNDARY|REPORTED|CURRENT REALITY|PHASE 0|HISTORICAL|PRIMARY (MISSION|EXECUTION)|SOURCE-OF-TRUTH|SOURCE OF TRUTH", "ALREADY_SATISFIED", {"evidence": gr(MP, r"Reality Delta"), "reason": "Master Plan section 0 re-derives the reported state"}),
    (r"FIRST RESPONSE|AFTER THE SINGLE|TOKEN BUDGET|OWNER APPROVAL|OWNER AUTHORITY|NO BLIND 100M|AUTONOMOUS AUTHORITY|PROGRAM AUTHORITY|NO 320M", "ALREADY_SATISFIED", {"evidence": gr(MP, r"hard ceiling of 55M"), "reason": "Master Plan section 1 answer 10: 40M envelope / 55M ceiling, approved"}),
    (r"PHASE 14|PHASE 15|OPTIMIZER ROI|AMDAHL|FIOS|FAILURE KNOWLEDGE|CONSTITUTIVE BASELINE|BASELINE RETIREMENT", "CHEAP_COGNITION", {"reason": "W8 knowledge writer / PGO owner row (slim-t2)"}),
    (r"BENCHMARK|PHASE 12|PROOF|MUTATION ECON|CERTIFIED PROOF|VERIFICATION|RED TEAM", "REUSE_EXISTING", {"evidence": gr(ROADMAP, r"(?i)verif|proof"), "reason": "recon-factory proof/verification phases (P5/P6 checked)"}),
    (r"RECONSTRUCT|KME|KSR|WII|CBR|HOMOLOG|COMPILER|GLOBAL TYPE|UNCERTAINTY GRAPH|DOMINATOR|AVALANCHE|POPULATION|MINIMUM SOURCE|STATIC \+ DYNAMIC|EXPERIMENT|ORACLE|KOBIMAP|^B\d+ |CONSTRUCTION RETURN|DOUBLE RATCHET|BASELINE DISTANCE|FAMILY|FUNCTION INVENTORY|FRONTIER REASONING|BATCH COG|CAUSAL APPLIC|PHASE 11|CAMPAIGN|REASONING REGIONS|CIRCULARITY", "REUSE_EXISTING", {"evidence": gr(ROADMAP, r"(?i)reconstruct"), "reason": "Part B maps onto the recon-factory ROADMAP phases"}),
]
SKIP_MERGE = "older-prompt row without a title rule: folded under S-master-mission by prompt precedence (not reviewed in depth)"


def main() -> int:
    secs = json.loads(Path(c.L1 / "sections.json").read_text(encoding="utf-8-sig"))["rows"]
    base = {o["id"]: o for o in c.build(secs, {})["obligations"]}
    src = {r["id"]: r["sources"][0] for r in secs}
    third = "2026-10-09T0725-530d9700.txt"
    rv = {}
    for r in secs:
        o = base[r["id"]]
        if o["claimed"] != "UNKNOWN":
            continue
        t = r["title"].upper().replace("\u2014", "-")
        for rx, disp, extra in RULES:
            if re.search(rx, t):
                rv[r["id"]] = {"claimed": disp, **extra}
                break
        else:
            if src[r["id"]] == third:
                rv[r["id"]] = {"claimed": "MERGE", "merge_into": PGO, "evidence": fe(SECT),
                               "reason": "optimization-stack candidate: enters only through the PGO/ROI market under the moratorium"}
            elif src[r["id"]] != "2026-10-09T1232-a354ad5e.txt":
                rv[r["id"]] = {"claimed": "MERGE", "merge_into": MASTER, "evidence": fe(SECT), "reason": SKIP_MERGE}
            else:
                rv[r["id"]] = {"claimed": "UNKNOWN", "reason": "needs review: current-prompt row without a title rule"}
    (L1 / "review.json").write_text(json.dumps(rv, indent=1), encoding="utf-8")
    cnt = {}
    for v in rv.values():
        cnt[v["claimed"]] = cnt.get(v["claimed"], 0) + 1
    print("REVIEW", len(rv), json.dumps(cnt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
