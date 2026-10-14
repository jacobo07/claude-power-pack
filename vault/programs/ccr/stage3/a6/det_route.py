"""WU-A6: route the A2-A5 re-measure through gsd_mission's DETERMINISTIC_PATH in an isolated mission store.
Usage (env GSD_LONG_RUN_STATE_DIR etc. set by the caller to the isolated store): python3 det_route.py <clone> <data>"""
import json
import sys
from pathlib import Path

clone, data = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(clone / "tools"))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
st = Path(gm.lr.state_dir())
pkt = st / "WU-A6-remeasure.md"
pkt.write_text("# WU-A6 re-measure Stage 3 processed tokens\n"
               f"deterministic: vault/programs/ccr/stage3/a6/remeasure.py {data} A2 A3 A4 A5\n", encoding="utf-8")
route = st / "route.json"
route.write_text(json.dumps({"envelope": {"target": 200000, "warn": 250000, "stop": 300000, "calls": 10},
                             "workers": [{"name": "s0", "profile": "slim-t2", "calls": 3, "packet": 500}]}))
mid = "m-a6-remeasure"
gm.create(str(clone), "/gsd-autonomous --ws ccr-a6", mission_id=mid)
gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="a6_setup", state=gm.RUNNING, epoch=1)
gm.set_envelope(mid, wu_packet=str(pkt))
adm = gm.admit_route(mid, str(route), floors_path=str(clone / "vault/config/route-floors.json"),
                     measure=lambda r: None)["admission"]


def refuse(*a, **k):
    raise AssertionError("model launch attempted")


cur = gm.load(mid)
res = gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="a6 deterministic",
                       runner=refuse, spawner=refuse)
rec = gm.load(mid)
print(json.dumps({"admission": adm["verdict"], "result": {k: res.get(k) for k in
                  ("ok", "deterministic", "rc", "model_calls", "argv", "stdout_sha256", "out_path")},
                  "stdout": res.get("stdout", "").strip(), "state": rec["state"], "epoch": rec["epoch"],
                  "record_deterministic": rec.get("deterministic")}, indent=1))
