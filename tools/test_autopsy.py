"""V-AUTOPSY / V-FORECAST gates for tools/mission_spend.py `autopsy` and `forecast` (cost-collapse T2).

Every gate drives both poles on synthetic transcripts in a hermetic temp dir. One mutation check per gate
family copies the module, reverts one hunk, imports the copy and asserts the gate's predicate goes red.
Run: python tools/test_autopsy.py
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402

PASS = FAIL = 0
T0 = dt.datetime(2026, 10, 7, 12, 0, 0, tzinfo=dt.timezone.utc)


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name} {detail}".rstrip())
    else:
        FAIL += 1
        print(f"FAIL {name} {detail}".rstrip())


def ts(sec: float) -> str:
    return (T0 + dt.timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


def call(mid: str, sec: float, inp=10, cw=100, cr=1000, out=5, tools=(), rec_uuid=None) -> dict:
    content = [{"type": "tool_use", "id": t[0], "name": t[1]} for t in tools]
    return {"type": "assistant", "timestamp": ts(sec), "uuid": rec_uuid or f"u-{mid}-{sec}",
            "message": {"id": mid, "model": "claude-sonnet-5-5", "content": content,
                        "usage": {"input_tokens": inp, "cache_creation_input_tokens": cw,
                                  "cache_read_input_tokens": cr, "output_tokens": out}}}


def put(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def load_copy(tag: str, old: str, new: str):
    """Import a copy of mission_spend with one hunk reverted. Asserts the hunk exists."""
    src = (HERE / "mission_spend.py").read_text(encoding="utf-8")
    assert src.count(old) == 1, f"mutation anchor not unique: {old!r}"
    p = Path(tempfile.mkdtemp(prefix="mut_")) / f"ms_{tag}.py"
    p.write_text(src.replace(old, new), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"ms_{tag}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def world(tmp: Path):
    """A projects root with one mission: work_dir W, owner session S1, a worker S2, a subagent of S1,
    plus a foreign session in the same directory that must not be attributed."""
    W = str(tmp / "work")
    root = tmp / "projects"
    d = root / ms.encode_cwd(W)
    rec = {"mission_id": "m-test", "work_dir": W, "cwd": W, "owner": {"session_id": "S1"},
           "created_at": T0.timestamp() - 60}
    put(d / "S1.jsonl", [
        call("a1", 0, cr=1000, tools=[("t1", "Bash")]),
        call("a1", 0, cr=1000, tools=[("t1", "Bash")]),            # streamed duplicate of a1
        call("a2", 30, cr=2000, tools=[("t2", "Read"), ("t3", "Bash")]),
        call("a3", 2000, cr=3000, tools=[("t4", "Bash")]),         # 1970 s after a2: a stall
    ])
    put(d / "S1" / "subagents" / "agent-x1.jsonl", [
        call("b1", 100, inp=1, cw=0, cr=500, out=1), call("b2", 110, inp=1, cw=0, cr=700, out=1)])
    put(d / "S2.jsonl", [call("c1", 3000, cr=4000)])
    put(d / "OTHER.jsonl", [call("z1", 10, cr=9_999_999)])         # foreign: same dir, not the mission
    return rec, root, d


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rec, root, d = world(tmp)
        ledger = tmp / "ledger.jsonl"
        ledger.write_text(json.dumps({"session_id": "m-test", "worker": "S2"}) + "\n", encoding="utf-8")
        ses = ms.mission_sessions(rec, ledger)
        res = ms.autopsy(rec, root, stall_s=600, sessions=ses)
        rows = {r["file"]: r for r in res["rows"]}

        # ---- V-AUTOPSY-TOTAL: the autopsy sums to the meter, and the foreign session is not in it
        pt = ms.processed_tokens(rec, root, sessions=ses)
        check("V-AUTOPSY-TOTAL-EQUALS-METER", res["total"]["processed"] == pt, f"{res['total']['processed']}=={pt}")
        check("V-AUTOPSY-FOREIGN-EXCLUDED", "OTHER.jsonl" not in rows and res["total"]["processed"] < 9_000_000)
        check("V-AUTOPSY-FOREIGN-WOULD-INFLATE", ms.processed_tokens({**rec, "owner": {"session_id": "OTHER"}},
              root, sessions=({"OTHER"}, set())) >= 9_999_999, "control: the foreign file carries 9.99M")

        # ---- V-AUTOPSY-DEDUP: a streamed duplicate message id counts once
        s1 = rows["S1.jsonl"]
        check("V-AUTOPSY-DEDUP-CALLS", s1["calls"] == 3, f"calls={s1['calls']}")
        check("V-AUTOPSY-DEDUP-TOKENS", s1["processed"] == (10 + 100 + 1000 + 5) + (10 + 100 + 2000 + 5) + (10 + 100 + 3000 + 5))

        # ---- V-AUTOPSY-SUBAGENT: kind, parent session and agent are separated
        sub = rows["S1/subagents/agent-x1.jsonl"]
        check("V-AUTOPSY-SUBAGENT-ROW", sub["kind"] == "subagent" and sub["session"] == "S1" and sub["agent"] == "agent-x1")
        check("V-AUTOPSY-SESSION-ROW", s1["kind"] == "session" and s1["session"] == "S1" and s1["agent"] is None)
        check("V-AUTOPSY-WORKER-ATTRIBUTED", "S2.jsonl" in rows, "worker named by the ledger")

        # ---- V-AUTOPSY-CTX: first / max / mean context = input + cache write + cache read per call
        check("V-AUTOPSY-CTX-FIRST-MAX-MEAN",
              (s1["first_ctx"], s1["max_ctx"], s1["mean_ctx"]) == (1110, 3110, round((1110 + 2110 + 3110) / 3)),
              f"{s1['first_ctx']},{s1['max_ctx']},{s1['mean_ctx']}")
        check("V-AUTOPSY-CACHE-SPLIT", (s1["cache_read"], s1["cache_write"], s1["output"]) == (6000, 300, 15))

        # ---- V-AUTOPSY-TOOLMIX: counted by tool_use id, so the streamed duplicate is not a second Bash
        check("V-AUTOPSY-TOOLMIX", s1["tool_mix"] == {"Bash": 3, "Read": 1}, str(s1["tool_mix"]))

        # ---- V-AUTOPSY-STALL: a gap above the threshold is a window, one below is not
        check("V-AUTOPSY-STALL-DETECTED", len(s1["stalls"]) == 1 and s1["stalls"][0]["gap_s"] == 1970.0, str(s1["stalls"]))
        check("V-AUTOPSY-STALL-BELOW-THRESHOLD-ABSENT", sub["stalls"] == [] and sub["stall_seconds"] == 0)
        quiet = ms.autopsy(rec, root, stall_s=5000, sessions=ses)
        check("V-AUTOPSY-STALL-THRESHOLD-IS-A-PARAMETER", quiet["total"]["stall_seconds"] == 0)

        # ---- V-AUTOPSY-FORK: a forked copy replays its parent's message ids; counted once in unique
        fd = tmp / "fk"
        fkrec = {"mission_id": "m-fk", "work_dir": str(tmp / "fkwork"), "cwd": str(tmp / "fkwork"),
                 "owner": {"session_id": "P"}, "created_at": T0.timestamp() - 60}
        fdir = tmp / "fkproj" / ms.encode_cwd(fkrec["work_dir"])
        put(fdir / "P.jsonl", [call("p1", 0), call("p2", 10)])
        put(fdir / "F.jsonl", [call("p1", 0), call("p2", 10), call("f3", 20)])   # fork of P plus one new call
        fk = ms.autopsy(fkrec, tmp / "fkproj", sessions=({"P", "F"}, set()))
        one = (10 + 100 + 1000 + 5)
        check("V-AUTOPSY-FORK-EXCLUDED", fk["total"]["processed_unique"] == 3 * one and fk["total"]["fork_calls"] == 2,
              f"unique={fk['total']['processed_unique']} fork_calls={fk['total']['fork_calls']}")
        # EVC 01-01 (dedup by message id, ROADMAP operating constraint): the meter now counts a forked copy ONCE, so it
        # agrees with the autopsy's unique total, not its per-file total. A meter that double-counts again fails here.
        meter = ms.processed_tokens(fkrec, tmp / "fkproj", sessions=({"P", "F"}, set()))
        check("V-AUTOPSY-FORK-METER-PARITY", meter == fk["total"]["processed_unique"] and meter < fk["total"]["processed"],
              f"meter={meter} unique={fk['total']['processed_unique']} per_file={fk['total']['processed']}")
        nofork = ms.autopsy(rec, root, sessions=ses)
        check("V-AUTOPSY-NO-FORK-NO-EXCLUSION", nofork["total"]["fork_calls"] == 0 and
              nofork["total"]["processed_unique"] == nofork["total"]["processed"])

        # ---- V-AUTOPSY-UNMEASURABLE: absent is not zero
        check("V-AUTOPSY-NO-DIR-IS-NONE", ms.autopsy({**rec, "work_dir": str(tmp / "nope"), "cwd": str(tmp / "nope")}, root, sessions=ses) is None)
        check("V-AUTOPSY-NO-SESSION-IS-NONE", ms.autopsy(rec, root, sessions=(set(), set())) is None)

        # ---- V-AUTOPSY-CLI: the command a human runs
        sd = tmp / "state"
        sd.mkdir()
        mrec = {"mission_id": "m-test", "state": "RUNNING", "schema_version": 1, **{k: rec[k] for k in ("work_dir", "cwd", "owner", "created_at")}}
        (sd / "gsd-mission-m-test.json").write_text(json.dumps(mrec), encoding="utf-8")
        env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": str(sd), "PYTHONIOENCODING": "utf-8"}
        pr = subprocess.run([sys.executable, str(HERE / "mission_spend.py"), "autopsy", "--mission", "m-test",
                             "--root", str(root)], capture_output=True, text=True, env=env, timeout=60,
                            cwd=str(HERE.parent))
        try:
            cli = json.loads(pr.stdout)
        except ValueError:
            cli = {}
        check("V-AUTOPSY-CLI-RUNS", pr.returncode == 0 and cli.get("ok") is True and "rows" in cli,
              f"rc={pr.returncode} {pr.stderr[-200:]}")
        pr2 = subprocess.run([sys.executable, str(HERE / "mission_spend.py"), "autopsy", "--mission", "m-test",
                              "--root", str(tmp / "empty")], capture_output=True, text=True, env=env, timeout=60,
                             cwd=str(HERE.parent))
        check("V-AUTOPSY-CLI-UNMEASURABLE-EXIT-3", pr2.returncode == 3 and '"ok": false' in pr2.stdout, f"rc={pr2.returncode}")

    # ---- V-AUTOPSY-REPRODUCES: m-53847a002b65 to +-1% on processed tokens
    fx = HERE.parent / "vault" / "specs" / "fixtures"
    exp = json.loads((fx / "autopsy-m53847-sample.expected.json").read_text(encoding="utf-8"))
    samp = ms.autopsy_transcript(fx / "autopsy-m53847-sample.jsonl")
    check("V-AUTOPSY-RECORDED-FIXTURE-PINNED", all(samp[k] == v for k, v in exp.items()),
          f"calls={samp['calls']} processed={samp['processed']}")
    check("V-AUTOPSY-RECORDED-FIXTURE-EQUALS-METER", samp["processed"] == ms._file_tokens(fx / "autopsy-m53847-sample.jsonl", None))
    try:
        import gsd_mission as gm
        live = gm.load("m-53847a002b65")
    except Exception as e:  # noqa: BLE001 - the host may simply not have it; reported below, never silent
        live, why = None, repr(e)
    else:
        why = "mission record absent"
    if live is not None:
        a = ms.autopsy(live)
        m = ms.processed_tokens(live)
        if a is None or m is None:
            check("V-AUTOPSY-REPRODUCES-LIVE-m-53847a002b65", False, f"autopsy={a is not None} meter={m}")
        else:
            err = abs(a["total"]["processed"] - m) / max(m, 1)
            check("V-AUTOPSY-REPRODUCES-LIVE-m-53847a002b65", err <= 0.01,
                  f"autopsy={a['total']['processed']:,} meter={m:,} err={err:.4%} (transcripts present on this host)")
    else:
        print(f"NOTE live m-53847a002b65 transcripts unavailable on this host ({why}); reproduction rests on the recorded fixture above")

    # ---- V-FORECAST
    full = {"name": "unit", "units": {"value": 10, "basis": "measured:roadmap"}, "calls_per_unit": {"value": 20, "basis": "measured:autopsy"},
            "floor": {"value": 100_000, "basis": "measured:autopsy"}, "context_image": {"value": 30_000, "basis": "measured:autopsy"},
            "repair": {"value": 0.25, "basis": "measured:autopsy"}}
    f1 = ms.forecast([full])
    check("V-FORECAST-FORMULA", f1["rows"][0]["tokens"] == round(10 * 20 * 130_000 * 1.25) and f1["total"] == 32_500_000, str(f1["rows"][0]["tokens"]))
    check("V-FORECAST-CONFIDENCE-MEASURED", f1["rows"][0]["confidence"] == "measured" and f1["lower_bound"] is False)
    est = ms.forecast([{**full, "floor": 100_000}])
    check("V-FORECAST-CONFIDENCE-WEAKEST-INPUT", est["rows"][0]["confidence"] == "estimated", "a declared floor demotes the row")
    check("V-FORECAST-BASIS-RECORDED", f1["rows"][0]["basis"]["floor"] == "measured:autopsy" and est["rows"][0]["basis"]["floor"] == "declared")
    for k in ("units", "calls_per_unit", "floor", "context_image", "repair"):
        miss = {kk: vv for kk, vv in full.items() if kk != k}
        fr = ms.forecast([miss])["rows"][0]
        check(f"V-FORECAST-MISSING-{k.upper()}-IS-UNMEASURED", fr["tokens"] is None and fr["confidence"] == "unmeasured" and fr["missing"] == [k])
    zero = ms.forecast([{**full, "repair": {"value": 0, "basis": "measured:autopsy"}}])["rows"][0]
    check("V-FORECAST-STATED-ZERO-IS-A-VALUE", zero["tokens"] == 10 * 20 * 130_000 and zero["confidence"] == "measured", "repair 0 stated != repair absent")
    q = ms.forecast([{**full, "floor": "?"}])["rows"][0]
    check("V-FORECAST-QUESTION-MARK-IS-UNMEASURED", q["tokens"] is None)
    mix = ms.forecast([full, {"name": "gap", "units": 5}])
    check("V-FORECAST-TOTAL-IS-LOWER-BOUND", mix["lower_bound"] is True and mix["unmeasured_rows"] == 1 and mix["total"] == 32_500_000)
    with tempfile.TemporaryDirectory() as td2:
        rf = Path(td2) / "rows.json"
        rf.write_text(json.dumps([full]), encoding="utf-8")
        pr = subprocess.run([sys.executable, str(HERE / "mission_spend.py"), "forecast", "--rows", str(rf)],
                            capture_output=True, text=True, timeout=60, cwd=str(HERE.parent))
        check("V-FORECAST-CLI-RUNS", pr.returncode == 0 and json.loads(pr.stdout)["total"] == 32_500_000, pr.stderr[-200:])

    # ---- Mutation checks: one per gate family. Each reverts one hunk and asserts the predicate goes red.
    with tempfile.TemporaryDirectory() as td3:
        t3 = Path(td3)
        rec3, root3, _ = world(t3)
        ses3 = ({"S1", "S2"}, set())
        fkrec3 = {"mission_id": "m-fk", "work_dir": str(t3 / "fkwork"), "cwd": str(t3 / "fkwork"),
                  "owner": {"session_id": "P"}, "created_at": T0.timestamp() - 60}
        fdir3 = t3 / "fkproj" / ms.encode_cwd(fkrec3["work_dir"])
        put(fdir3 / "P.jsonl", [call("p1", 0), call("p2", 10)])
        put(fdir3 / "F.jsonl", [call("p1", 0), call("p2", 10), call("f3", 20)])

        m_fork = load_copy("fork", "if seen_global is not None and mid in seen_global:", "if False:")
        r = m_fork.autopsy(fkrec3, t3 / "fkproj", sessions=({"P", "F"}, set()))
        check("V-AUTOPSY-MUTATION-FORK", r["total"]["fork_calls"] != 2 or r["total"]["processed_unique"] != 3 * (10 + 100 + 1000 + 5),
              "reverting fork exclusion is caught")
        m_stall = load_copy("stall", "if times[i] - times[i - 1] > stall_s]", "if times[i] - times[i - 1] > 10**12]")
        r = m_stall.autopsy(rec3, root3, 600, sessions=ses3)
        s1m = [x for x in r["rows"] if x["file"] == "S1.jsonl"][0]
        check("V-AUTOPSY-MUTATION-STALL", len(s1m["stalls"]) != 1, "a blinded stall detector is caught")
        m_dedup = load_copy("dedup", "            if mid in seen:\n                continue\n            seen.add(mid)\n            tok = sum",
                            "            seen.add(mid)\n            tok = sum")
        r = m_dedup.autopsy(rec3, root3, 600, sessions=ses3)
        s1m = [x for x in r["rows"] if x["file"] == "S1.jsonl"][0]
        check("V-AUTOPSY-MUTATION-DEDUP", s1m["calls"] != 3, "dropping per-file dedupe is caught")
        m_attr = load_copy("attr", "            if _attributed(p, d, ids, prefixes):\n                files.append((d, p))",
                           "            files.append((d, p))")
        r = m_attr.autopsy(rec3, root3, 600, sessions=ses3)
        check("V-AUTOPSY-MUTATION-ATTRIBUTION", r["total"]["processed"] > 9_000_000, "dropping attribution counts the foreign session")
        m_zero = load_copy("zero", "    if val is None or (isinstance(val, str)", "    if val is None and False or (isinstance(val, str)")
        try:
            fr = m_zero.forecast([{k: v for k, v in full.items() if k != "repair"}])["rows"][0]
            red = fr["tokens"] is not None or fr["confidence"] != "unmeasured"
        except Exception:  # noqa: BLE001 - a mutant that crashes on a missing input is also caught
            red = True
        check("V-FORECAST-MUTATION-ABSENT-IS-NOT-ZERO", red, "treating an absent input as a value is caught")

    print(f"AUTOPSY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
