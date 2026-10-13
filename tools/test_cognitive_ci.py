#!/usr/bin/env python
"""V-CCI-* gates for cognitive_ci.py and the land_worktree COGNITIVE_REGRESSION refusal (CDC C7). Hermetic."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cognitive_ci as cci  # noqa: E402
import land_worktree as lw  # noqa: E402

REAL = HERE.parent
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def fixture(root: Path):
    (root / "vault/config").mkdir(parents=True)
    shutil.copy(REAL / "vault/config/route-floors.json", root / "vault/config/route-floors.json")
    (root / "CLAUDE.md").write_text("# rules\n" + "x" * 2000)
    (root / "rules").mkdir()
    (root / "rules/a.md").write_text("r" * 500)
    for i in range(3):
        d = root / "skills" / f"s{i}"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: s{i}\ndescription: skill number {i}\n---\nbody")
    (root / "agents").mkdir()
    (root / "agents/ag.md").write_text("---\nname: ag\ndescription: an agent\n---\n")
    (root / "hooks").mkdir()
    (root / "hooks/h.js").write_text("out({additionalContext: 'hello'});\n")
    for rel in cci.STATUS_PATHS + cci.WAIT_PATHS:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("print('status')\n")


def vals(m):
    return {k: v["value"] for k, v in m.items()}


def noisy(k):
    return k == "admission.latency_ms"


with tempfile.TemporaryDirectory() as t:
    fx = Path(t) / "fx"
    fixture(fx)
    base = cci.measure(fx)
    base2 = cci.measure(fx)
    check("V-CCI-01 size/count metrics deterministic across runs",
          all(vals(base)[k] == vals(base2)[k] for k in base if not noisy(k)))
    check("V-CCI-02 status path model calls == 0 and wait residents == 0",
          base["status.model_call_sites"]["value"] == 0 and base["wait.resident_sites"]["value"] == 0)
    # metamorphic: unrelated growth leaves every fixed-work metric alone
    for i in range(50):
        d = fx / "skills" / f"extra{i}"
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: e{i}\ndescription: unrelated {i}\n---\n")
    after = cci.measure(fx)
    fixed = [k for k in base if not k.startswith("floor.") and not noisy(k)]
    check("V-CCI-03 +50 skills: fixed-work metrics unchanged", all(base[k]["value"] == after[k]["value"] for k in fixed))
    check("V-CCI-04 sensitivity: +50 skills DO grow floor.skill_listing_bytes",
          after["floor.skill_listing_bytes"]["value"] > base["floor.skill_listing_bytes"]["value"])
    with (fx / "history.jsonl").open("w") as f:
        for i in range(1000):
            f.write(json.dumps({"row": i}) + "\n")
    (fx / "goals").mkdir()
    for i in range(100):
        (fx / "goals" / f"g{i}.json").write_text('{"status":"dormant"}')
    for i in range(500):
        (fx / "tools").mkdir(exist_ok=True)
        (fx / "tools" / f"test_unrelated_{i}.py").write_text("pass\n")
    after2 = cci.measure(fx)
    check("V-CCI-05 +1000 history rows, +100 dormant goals, +500 tests: fixed-work metrics unchanged",
          all(after[k]["value"] == after2[k]["value"] for k in fixed))
    check("V-CCI-06 latency within noise limit under the same growth",
          after2["admission.latency_ms"]["value"] <= cci.limit(dict(base["admission.latency_ms"], noise=0)))

    # evaluate: planted +8K
    cert = cci.certify(fx)
    cur = cci.measure(fx)
    check("V-CCI-07 unchanged tree is GREEN", cci.evaluate(cur, cert)["status"] == "GREEN")
    (fx / "CLAUDE.md").write_text("# rules\n" + "x" * 2000 + "y" * 8192)
    cur = cci.measure(fx)
    ev = cci.evaluate(cur, cert)
    check("V-CCI-08 planted +8K always-on injection goes RED",
          ev["status"] == "RED" and ev["regressions"][0]["metric"] == "floor.claude_md_bytes", ev["status"])
    ok = [{"metric": "floor.claude_md_bytes", "allowed_max": 20000, "reason": "new rule", "owner": "owner"}]
    check("V-CCI-09 justified entry (reason+owner+allowed_max) clears it",
          cci.evaluate(cur, cert, ok)["status"] == "GREEN" and cci.evaluate(cur, cert, ok)["justified"])
    for bad in ({"metric": "floor.claude_md_bytes", "allowed_max": 20000, "reason": "", "owner": "o"},
                {"metric": "floor.claude_md_bytes", "allowed_max": 20000, "reason": "r", "owner": " "},
                {"metric": "floor.claude_md_bytes", "allowed_max": 100, "reason": "r", "owner": "o"}):
        check("V-CCI-10 unjustified/too-small entry stays RED: %s" % sorted(k for k, v in bad.items() if not str(v).strip() or v == 100),
              cci.evaluate(cur, cert, [bad])["status"] == "RED")
    zc = json.loads(json.dumps(cert))
    cur_z = dict(cur, **{"status.model_call_sites": {"value": 1, "class": "count", "blast": "ZERO"}})
    ez = cci.evaluate(cur_z, zc, [{"metric": "status.model_call_sites", "allowed_max": 5, "reason": "r", "owner": "o"}])
    check("V-CCI-11 ZERO metric cannot be excused by a budget entry", ez["status"] == "RED")
    check("V-CCI-12 shrinking is never a regression",
          cci.evaluate(dict(cur, **{"floor.claude_md_bytes": {"value": 10, "class": "size", "blast": "ALWAYS_ON"}}), cert)["status"] == "GREEN")
    check("V-CCI-13 kill switch -> OFF", cci.check(fx, env={"CPP_COG_CI": "off"})["status"] == "OFF")
    check("V-CCI-14 no baseline -> OPEN NO_BASELINE", cci.check(fx, env={})["reason"] == "NO_BASELINE")
    (fx / "vault/programs/cdc").mkdir(parents=True)
    (fx / cci.BASELINE).write_text("{not json")
    check("V-CCI-15 own error fails OPEN", cci.check(fx, env={})["reason"] == "INSTRUMENT_ERROR")


def g(repo, *a):
    return subprocess.run([lw.GIT, "-C", str(repo), *a], capture_output=True, text=True)


def mk(tmp):
    live, wt = Path(tmp) / "live", Path(tmp) / "wt"
    live.mkdir()
    g(live, "init", "-q", "-b", "main")
    g(live, "config", "user.email", "t@t")
    g(live, "config", "user.name", "t")
    fixture(live)
    (live / "vault/programs/cdc").mkdir(parents=True)
    (live / cci.BASELINE).write_text(json.dumps(cci.certify(live)))
    g(live, "add", "."); g(live, "commit", "-qm", "i")
    g(live, "worktree", "add", "-q", "-b", "feat", str(wt))
    (wt / "CLAUDE.md").write_text("# rules\n" + "x" * 2000 + "z" * 8192)
    g(wt, "add", "CLAUDE.md"); g(wt, "commit", "-qm", "plant")
    return live, wt


T = ['python -c "pass"']
with tempfile.TemporaryDirectory() as t:
    live, wt = mk(t)
    head = lw.rev(live)
    r = lw.land(str(wt), str(live), tests=T)
    check("V-CCI-16 landing REFUSED on planted +8K, live untouched",
          r["reason"] == "COGNITIVE_REGRESSION" and not r["landed"] and lw.rev(live) == head
          and r["cognitive_ci"]["regressions"][0]["metric"] == "floor.claude_md_bytes", r["reason"])
    (wt / cci.BUDGET).write_text(json.dumps([{"metric": "floor.claude_md_bytes", "allowed_max": 20000,
                                              "reason": "planted for proof", "owner": "cdc"}]))
    g(wt, "add", "-f", str(cci.BUDGET)); g(wt, "commit", "-qm", "budget")
    r = lw.land(str(wt), str(live), tests=T)
    check("V-CCI-17 justified entry lets the landing through", r["status"] == "LANDED"
          and r["cognitive_ci"]["justified"], r.get("reason"))

with tempfile.TemporaryDirectory() as t:
    live, wt = mk(t)
    r = lw.land(str(wt), str(live), tests=T, cog_fn=lambda w: (_ for _ in ()).throw(RuntimeError("boom")))
    check("V-CCI-18 land: instrument exception fails OPEN", r["status"] == "LANDED"
          and r["cognitive_ci"]["reason"] == "INSTRUMENT_ERROR", r.get("reason"))

with tempfile.TemporaryDirectory() as t:
    live, wt = mk(t)
    import os
    os.environ["CPP_COG_CI"] = "off"
    try:
        r = lw.land(str(wt), str(live), tests=T)
    finally:
        del os.environ["CPP_COG_CI"]
    check("V-CCI-19 CPP_COG_CI=off lets the planted regression land", r["status"] == "LANDED"
          and r["cognitive_ci"]["status"] == "OFF", r.get("reason"))

print(f"\n{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
