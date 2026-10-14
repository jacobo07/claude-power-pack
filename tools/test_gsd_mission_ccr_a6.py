#!/usr/bin/env python
"""V-CCRA6-* gates: the WU-A6 admission actions in gsd_mission (confidence-gated enforce, DEFLATE,
DETERMINISTIC_PATH). Each action has a pole where it acts and a pole where it must not.
Hermetic: state in a temp dir BEFORE import, injected spawner / runners, no real worker, no model."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-a6-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
for k in ("CPP_MISSION_RENEW", "CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION", "CPP_CCR_DEFLATE", "CCR_WORK_UNIT"):
    os.environ.pop(k, None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
REAL_CONTRACT = gm._ccr_contract
FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")
NOW = 1_800_000_000.0
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
THIN = {"envelope": ENV, "workers": [{"name": "w0r", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}
SLIM = {"envelope": {"target": 200_000, "warn": 250_000, "stop": 300_000, "calls": 10},
        "workers": [{"name": "s0", "profile": "slim-t2", "calls": 3, "packet": 500}]}
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def write(name: str, text: str) -> str:
    p = Path(TMP) / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def mission(mid: str, body: str = "") -> None:
    gm.create(TMP, f"/gsd-autonomous --ws ws-{mid}", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n{body}"), ccr_class="bounded-code", now=NOW)


def admit(mid: str, route: dict, contract: dict) -> dict:
    gm._ccr_contract = lambda rec, pkt, cap: dict(contract)
    return gm.admit_route(mid, write(f"{mid}-route.json", json.dumps(route)), floors_path=FLOORS, now=NOW,
                          measure=lambda r: None)["admission"]


def launch(mid: str, **kw) -> dict:
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t", now=NOW, **kw)


def ledger(mid: str, event: str) -> list:
    p = gm.lr.ledger_path()
    rows = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []
    return [r for r in rows if r.get("event") == event and r.get("session_id") == mid]


def no_model(*a, **k):
    raise AssertionError("a model launch was attempted")


def main() -> int:
    split = {"verdict": "SPLIT", "work_class": "bounded-code", "reasons": ["forecast P80 over cap"]}

    # 1. enforce acts only at MEDIUM or better; LOW observes
    os.environ["CPP_CCR_ADMISSION"] = "enforce"
    mission("m-enf-med")
    a = admit("m-enf-med", THIN, {**split, "confidence": "MEDIUM"})
    check("V-CCRA6-ENFORCE-MEDIUM-REFUSES", a["verdict"] not in gm.LAUNCHABLE_VERDICTS
          and "ccr_contract:SPLIT" in a["reasons"], str(a["verdict"]))
    mission("m-enf-low")
    a = admit("m-enf-low", THIN, {**split, "confidence": "LOW"})
    check("V-CCRA6-ENFORCE-LOW-OBSERVES", a["verdict"] in gm.LAUNCHABLE_VERDICTS
          and a["ccr_contract"]["verdict"] == "SPLIT", str(a["verdict"]))
    os.environ.pop("CPP_CCR_ADMISSION")

    # 2. DEFLATE: an undeclared slim Work Unit launch gets its unit declared by class
    med = {"verdict": "ADMIT", "work_class": "bounded-code", "confidence": "MEDIUM"}
    seen: dict = {}

    def spawner(argv, cwd, out_path, err_path, env=None):
        seen.clear()
        seen.update(argv=argv, env=env)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        return 4242

    mission("m-defl")
    admit("m-defl", SLIM, med)
    r = launch("m-defl", runner=no_model, spawner=spawner)
    unit = (seen.get("env") or {}).get("CCR_WORK_UNIT")
    decl = json.loads(Path(unit).read_text(encoding="utf-8")) if unit and Path(unit).is_file() else {}
    check("V-CCRA6-DEFLATE-DECLARES-UNIT", r.get("ok") is True and decl.get("class") == "bounded-code-worker"
          and decl.get("id") == "m-defl" and len(ledger("m-defl", "deflate_applied")) == 1, str(decl))

    # 2b. the opposite pole: a launch that already declares, a LOW class, the off switch
    os.environ["CCR_WORK_UNIT"] = "/already/declared.json"
    mission("m-decl")
    admit("m-decl", SLIM, med)
    launch("m-decl", runner=no_model, spawner=spawner)
    check("V-CCRA6-DEFLATE-LEAVES-DECLARED", seen.get("env") is None and not ledger("m-decl", "deflate_applied"),
          str(seen.get("env") and seen["env"].get("CCR_WORK_UNIT")))
    os.environ.pop("CCR_WORK_UNIT")
    mission("m-low")
    admit("m-low", SLIM, {**med, "work_class": "lookup", "confidence": "LOW"})
    launch("m-low", runner=no_model, spawner=spawner)
    obs = ledger("m-low", "deflate_observed")
    check("V-CCRA6-DEFLATE-LOW-OBSERVES", seen.get("env") is None and len(obs) == 1
          and obs[0].get("action") == "would_deflate" and obs[0].get("unit") == "read-only-reviewer", str(obs))
    os.environ["CPP_CCR_DEFLATE"] = "off"
    mission("m-off")
    admit("m-off", SLIM, med)
    launch("m-off", runner=no_model, spawner=spawner)
    check("V-CCRA6-DEFLATE-OFF-SWITCH", seen.get("env") is None and not ledger("m-off", "deflate_applied")
          and not ledger("m-off", "deflate_observed"))
    os.environ.pop("CPP_CCR_DEFLATE")

    # 2c. a --bg launch cannot carry an env declaration (W0 E3): recorded, not claimed as delivered
    bg: list = []

    def runner(argv, cwd):
        from types import SimpleNamespace
        bg.append(argv)
        return SimpleNamespace(stdout=f"backgrounded · c0ffee01 · {argv[3]}", stderr="", returncode=0)

    mission("m-bg")
    admit("m-bg", THIN, med)
    launch("m-bg", runner=runner)
    obs = ledger("m-bg", "deflate_observed")
    check("V-CCRA6-DEFLATE-BG-NOT-DELIVERED", len(bg) == 1 and len(obs) == 1 and obs[0].get("delivered") is False
          and obs[0].get("action") == "would_deflate" and not obs[0].get("declared"),
          str(obs))

    # 3. DETERMINISTIC_PATH: the packet's script runs, zero model calls, mission completed with the output hash
    write("det_ok.py", "print('{\"A2\": 4302121}')\n")
    mission("m-det", "deterministic: det_ok.py\n")
    admit("m-det", THIN, med)
    e0 = gm.load("m-det")["epoch"]
    r = launch("m-det", runner=no_model, spawner=no_model)
    rec = gm.load("m-det")
    check("V-CCRA6-DET-RUNS-NO-MODEL", r.get("ok") is True and r.get("model_calls") == 0
          and r["stdout"].strip() == '{"A2": 4302121}' and rec["state"] == gm.COMPLETED and rec["epoch"] == e0
          and rec["deterministic"]["stdout_sha256"] == r["stdout_sha256"], str({k: r.get(k) for k in ("ok", "rc")}))

    # 3b. the opposite pole: a failing script stays put and never falls back to a model; a script outside
    # the work tree is refused; a packet without the line goes to the model as before
    write("det_bad.py", "import sys; sys.exit(3)\n")
    mission("m-detbad", "deterministic: det_bad.py\n")
    admit("m-detbad", THIN, med)
    r = launch("m-detbad", runner=no_model, spawner=no_model)
    check("V-CCRA6-DET-FAIL-NO-FALLBACK", r.get("ok") is False and r.get("rc") == 3
          and gm.load("m-detbad")["state"] == gm.RUNNING and len(ledger("m-detbad", "deterministic_failed")) == 1)
    mission("m-detout", "deterministic: ../../etc/passwd.py\n")
    admit("m-detout", THIN, med)
    r = launch("m-detout", runner=no_model, spawner=no_model)
    check("V-CCRA6-DET-OUTSIDE-TREE-REFUSED", r.get("ok") is False and "inside" in r.get("why", ""), r.get("why"))
    bg.clear()
    mission("m-nodet", "no script here\n")
    admit("m-nodet", THIN, med)
    r = launch("m-nodet", runner=runner)
    check("V-CCRA6-DET-ABSENT-LAUNCHES-MODEL", r.get("ok") is True and len(bg) == 1 and not r.get("deterministic"))

    # 4. the real A3 class models (pgo-classes.json), no stub: the packet is classified and carries its confidence
    gm._ccr_contract = REAL_CONTRACT
    import shutil
    a3 = Path(__file__).resolve().parent.parent / "vault/programs/ccr/stage3/a3/pgo-classes.json"
    os.environ["CPP_CCR_PGO_DIR"] = str(Path(TMP) / "pgo-a3")
    Path(os.environ["CPP_CCR_PGO_DIR"]).mkdir()
    shutil.copy(a3, Path(os.environ["CPP_CCR_PGO_DIR"]) / "pgo-classes.json")
    for mid, title, cls, conf, declared in (("m-a3-code", "# WU fix the parser\nEdit tools/foo.py, add tests.\n",
                                             "bounded-code", "MEDIUM", True),
                                            ("m-a3-look", "# WU look up the predecessor\nWhere is X.\n",
                                             "lookup", "LOW", False)):
        gm.create(TMP, f"/gsd-autonomous --ws ws-{mid}", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                      epoch=1)
        gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", title), now=NOW)
        c = gm.admit_route(mid, write(f"{mid}-route.json", json.dumps(SLIM)), floors_path=FLOORS, now=NOW,
                           measure=lambda r: None)["admission"]["ccr_contract"]
        launch(mid, runner=no_model, spawner=spawner)
        check(f"V-CCRA6-A3-MODELS-{cls.upper()}-{conf}", c.get("work_class") == cls and c.get("confidence") == conf
              and bool((seen.get("env") or {}).get("CCR_WORK_UNIT")) is declared,
              f"{c.get('work_class')} {c.get('confidence')} {c.get('verdict')}")
    os.environ.pop("CPP_CCR_PGO_DIR")

    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
