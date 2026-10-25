#!/usr/bin/env python3
"""V-CCN-CENSUS-* gates for tools/ccn_census.py. Every detector is driven from both poles
(a fixture where the thing exists, one where it does not) and from a mutant that must go red.

Run: python3 tools/test_ccn_census.py   -> prints CCN_PASS=n/m, exit 0 only when n == m.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ccn_census as cc  # noqa: E402

SEED_DIR = os.path.join(HERE, "..", ".planning", "workstreams", "ccn", "seed")
NOW = 1_800_000_000.0   # fixed "now" for fixtures (2027-01-15); everything is relative to it

passes = fails = 0


def _ok(name, evidence):
    global passes
    passes += 1
    print("PASS %s: %s" % (name, evidence))


def _fail(name, diagnostic):
    global fails
    fails += 1
    print("FAIL %s: %s" % (name, diagnostic))


def gate(name, cond, evidence):
    (_ok if cond else _fail)(name, evidence)


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(t))


def write_session(root, project, sid, lines, mtime=None):
    d = os.path.join(root, project)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, sid + ".jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for rec in lines:
            fh.write(json.dumps(rec) + "\n")
    stamp = (NOW if mtime is None else mtime)
    os.utime(path, (stamp, stamp))   # mtime is only the scope prefilter; fixtures live around NOW
    return path


def tool_pair(t, tid, name, inp, result="x" * 100):
    return [
        {"type": "assistant", "timestamp": iso(t), "message": {"content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}]}},
        {"type": "user", "timestamp": iso(t + 1), "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": result}]}},
    ]


def first_call(t, write, read):
    return [{"type": "assistant", "timestamp": iso(t), "message": {"model": "m", "usage": {"cache_creation_input_tokens": write, "cache_read_input_tokens": read}, "content": []}}]


def mutant(replacements):
    """Load ccn_census with source replacements; each must hit exactly once or the mutant is void."""
    src = open(os.path.join(HERE, "ccn_census.py"), encoding="utf-8").read()
    for old, new in replacements:
        if src.count(old) != 1:
            raise AssertionError("mutant anchor not unique: %r (%d)" % (old, src.count(old)))
        src = src.replace(old, new)
    mod = types.ModuleType("ccn_census_mutant")
    mod.__file__ = "<mutant>"
    exec(compile(src, "<mutant>", "exec"), mod.__dict__)
    return mod


def build_dup_estate(root, now=NOW):
    """A: positive pole. B: negatives (same session twice; two sessions 1 h apart)."""
    base = now - 3600
    # session s1 and s2 read the same file 100 s apart -> the second read is a duplicate
    write_session(root, "p-a", "s1", tool_pair(base, "a1", "Read", {"file_path": "/r/F.md"}))
    write_session(root, "p-a", "s2", tool_pair(base + 100, "b1", "Read", {"file_path": "/r/F.md"}))
    # s3 repeats ITS OWN read twice, nobody else reads it -> not a cross-session duplicate
    write_session(root, "p-b", "s3", tool_pair(base, "c1", "Read", {"file_path": "/r/own.md"}) +
                  tool_pair(base + 60, "c2", "Read", {"file_path": "/r/own.md"}))
    # s4 and s5 read the same file 2000 s apart (> 1800 s window) -> not a duplicate
    write_session(root, "p-c", "s4", tool_pair(base - 2500, "d1", "Read", {"file_path": "/r/late.md"}))
    write_session(root, "p-c", "s5", tool_pair(base - 500, "e1", "Read", {"file_path": "/r/late.md"}))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        # ---------------------------------------------------------------- dup, both poles
        root = os.path.join(tmp, "dup")
        build_dup_estate(root)
        res = cc.dup_scan([root], hours=24, now=NOW)
        gate("V-CCN-CENSUS-DUP-POSITIVE", res["dup_calls"] == 1 and res["tool_events"] == 6,
             "events=%d dup_calls=%d (expected 6 / 1: only s2's read of F.md)" % (res["tool_events"], res["dup_calls"]))
        gate("V-CCN-CENSUS-DUP-NEGATIVE", res["per_tool"].get("Read", {}).get("calls") == 1 and
             not any("own.md" in t["key"] or "late.md" in t["key"] for t in res["top_shared"] if t["key"].endswith("own.md:None:None")),
             "same-session repeat and >1800 s gap produced no extra duplicate (per_tool=%s)" % res["per_tool"])
        gate("V-CCN-CENSUS-DUP-BYTES", res["dup_bytes"] > 0 and res["dup_bytes_pct"] == round(100.0 * res["dup_bytes"] / res["result_bytes"], 3),
             "dup_bytes=%d of %d (%s%%)" % (res["dup_bytes"], res["result_bytes"], res["dup_bytes_pct"]))

        # same-instant tie: two sessions at the same second both count as duplicates of each other
        tie = os.path.join(tmp, "tie")
        write_session(tie, "p", "t1", tool_pair(NOW - 600, "x1", "Grep", {"pattern": "foo", "path": "/r"}))
        write_session(tie, "p", "t2", tool_pair(NOW - 600, "y1", "Grep", {"pattern": "foo", "path": "/r"}))
        tres = cc.dup_scan([tie], hours=24, now=NOW)
        gate("V-CCN-CENSUS-DUP-TIE", tres["dup_calls"] == 2, "same-second pair: dup_calls=%d (expected 2)" % tres["dup_calls"])

        # window scoping: events older than the window do not count at all
        old = cc.dup_scan([root], hours=0.2, now=NOW)
        gate("V-CCN-CENSUS-DUP-WINDOW", old["tool_events"] == 0 and old["dup_calls_pct"] is None,
             "0.2 h window sees 0 events and reports pct=None, not 0 (events=%d pct=%s)" % (old["tool_events"], old["dup_calls_pct"]))

        # mutant: break the session-distinct check -> the same-session repeat must now be flagged (red)
        m = mutant([("if any(p[1] != e[1] for p in group[lo:hi]):", "if any(True for p in group[lo:hi]):")])
        single = os.path.join(tmp, "single")
        write_session(single, "p", "only", tool_pair(NOW - 600, "z1", "Read", {"file_path": "/r/a"}) +
                      tool_pair(NOW - 500, "z2", "Read", {"file_path": "/r/a"}))
        write_session(single, "p", "other", tool_pair(NOW - 9000, "z3", "Read", {"file_path": "/r/a"}))
        real_single = cc.dup_scan([single], hours=24, now=NOW)["dup_calls"]
        mut_single = m.dup_scan([single], hours=24, now=NOW)["dup_calls"]
        gate("V-CCN-CENSUS-DUP-MUTANT", real_single == 0 and mut_single > 0,
             "session-distinct check removed: real=%d mutant=%d (mutant must be > 0)" % (real_single, mut_single))

        # ---------------------------------------------------------------- stampede, both poles
        st = os.path.join(tmp, "stamp")
        # 12 isolated starts, 1 h apart, write 80_000; then a burst of 12 within 20 s each, write 60_000
        t0 = NOW - 86400
        for i in range(12):
            write_session(st, "p-i", "iso%02d" % i, first_call(t0 + i * 3600, 80_000, 30_000))
        burst0 = NOW - 7200
        for i in range(12):
            write_session(st, "p-c", "con%02d" % i, first_call(burst0 + i * 20, 60_000, 50_000))
        sres = cc.stampede_scan([st], days=2, now=NOW)
        gate("V-CCN-CENSUS-STAMPEDE-ARMS", sres["isolated"]["n"] == 13 and sres["concurrent"]["n"] == 11,
             "isolated n=%d concurrent n=%d (expected 13 / 11: the first burst start has no predecessor within 300 s)" %
             (sres["isolated"]["n"], sres["concurrent"]["n"]))
        gate("V-CCN-CENSUS-STAMPEDE-MEDIANS", sres["isolated"]["write_median"] == 80_000 and sres["concurrent"]["write_median"] == 60_000 and
             sres["concurrent"]["read_median"] == 50_000,
             "write medians iso=%s conc=%s read conc=%s" % (sres["isolated"]["write_median"], sres["concurrent"]["write_median"], sres["concurrent"]["read_median"]))
        none = os.path.join(tmp, "stamp-none")
        for i in range(12):
            write_session(none, "p", "n%02d" % i, first_call(t0 + i * 3600, 70_000, 30_000))
        nres = cc.stampede_scan([none], days=2, now=NOW)
        gate("V-CCN-CENSUS-STAMPEDE-NEGATIVE", nres["concurrent"]["n"] == 0 and nres["concurrent"]["write_median"] is None,
             "all starts 1 h apart: concurrent n=%d median=%s (None, not 0)" % (nres["concurrent"]["n"], nres["concurrent"]["write_median"]))
        mm = mutant([("near = any(times[j] < t for j in range(lo, i))", "near = False")])
        mres = mm.stampede_scan([st], days=2, now=NOW)
        gate("V-CCN-CENSUS-STAMPEDE-MUTANT", mres["concurrent"]["n"] == 0 and sres["concurrent"]["n"] > 0,
             "concurrency detection removed: real n=%d mutant n=%d (mutant must be 0)" % (sres["concurrent"]["n"], mres["concurrent"]["n"]))

        # ---------------------------------------------------------------- CI thresholds, both sides of each limit
        def fake_dup(events, pct):
            return {"tool_events": events, "dup_calls_pct": pct}

        def fake_stamp(cn, cw, inn, iw):
            return {"concurrent": {"n": cn, "write_median": cw}, "isolated": {"n": inn, "write_median": iw}}
        a = cc.check_thresholds(fake_dup(100, 2.9), fake_stamp(20, 1090, 20, 1000))
        b = cc.check_thresholds(fake_dup(100, 3.1), fake_stamp(20, 1110, 20, 1000))
        c = cc.check_thresholds(fake_dup(10, 99.0), fake_stamp(3, 5000, 3, 1000))
        gate("V-CCN-CENSUS-CHECK-OK", a["dup"]["verdict"] == "OK" and a["stampede"]["verdict"] == "OK", "2.9%% / x1.09 -> %s" % a)
        gate("V-CCN-CENSUS-CHECK-BREACH", b["dup"]["verdict"] == "BREACH" and b["stampede"]["verdict"] == "BREACH", "3.1%% / x1.11 -> %s" % b)
        gate("V-CCN-CENSUS-CHECK-UNMEASURED", c["dup"]["verdict"] == "UNMEASURED" and c["stampede"]["verdict"] == "UNMEASURED",
             "too little data is UNMEASURED, never green and never a breach -> %s" % c)

        # CLI exit codes through main(): breach -> 1, clean -> 0, unmeasured -> 0, unmeasured + --strict -> 2
        breach = os.path.join(tmp, "cli-breach")
        for i in range(30):   # 30 sessions read 2 shared files within a minute -> heavy duplication
            write_session(breach, "p", "b%02d" % i, tool_pair(NOW - 900 + i, "r1", "Read", {"file_path": "/r/hot1"}) +
                          tool_pair(NOW - 800 + i, "r2", "Read", {"file_path": "/r/hot2"}))
        clean = os.path.join(tmp, "cli-clean")
        for i in range(30):   # 30 sessions each read their OWN file -> zero duplication
            write_session(clean, "p", "c%02d" % i, tool_pair(NOW - 900 + i, "r1", "Read", {"file_path": "/r/own%d" % i}) +
                          tool_pair(NOW - 800 + i, "r2", "Read", {"file_path": "/r/also%d" % i}))
        empty = os.path.join(tmp, "cli-empty")
        os.makedirs(empty)

        def run_cli(root_dir, *extra):
            real_now = time.time
            time.time = lambda: NOW
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    return cc.main(["--root", root_dir, "--json", "all", "--check"] + list(extra))
            finally:
                time.time = real_now
        # hot-idle inside `all` reads the real /proc; that is fine, the exit code only reads dup/stampede
        gate("V-CCN-CENSUS-CLI-BREACH", run_cli(breach) == 1, "heavy duplication -> exit 1")
        gate("V-CCN-CENSUS-CLI-CLEAN", run_cli(clean) == 0, "no duplication -> exit 0")
        gate("V-CCN-CENSUS-CLI-UNMEASURED", run_cli(empty) == 0 and run_cli(empty, "--strict") == 2,
             "empty estate: exit 0 by default, exit 2 with --strict")

        # ---------------------------------------------------------------- hot-idle, both poles + unjoinable
        hi = os.path.join(tmp, "hot")
        sid_old = "11111111-1111-4111-8111-111111111111"
        sid_new = "22222222-2222-4222-8222-222222222222"
        sid_cwd = "33333333-3333-4333-8333-333333333333"
        p_old = write_session(hi, "-r-old", sid_old, first_call(NOW - 30 * 3600, 1, 1) + tool_pair(NOW - 30 * 3600, "h1", "Read", {"file_path": "/x"}))
        write_session(hi, "-r-new", sid_new, tool_pair(NOW - 90, "h2", "Read", {"file_path": "/x"}))
        write_session(hi, encode := cc.encode_cwd("/work/by-cwd"), sid_cwd, tool_pair(NOW - 3 * 3600, "h3", "Read", {"file_path": "/x"}))
        os.utime(p_old, (NOW, NOW))   # mtime says "just now"; the records say 30 h ago -> records must win
        procs = [
            cc.proc_record(101, 1, ["claude", "--resume", sid_old], "/w/a", 400.0),
            cc.proc_record(102, 1, ["claude", "--session-id", sid_new], "/w/b", 300.0),
            cc.proc_record(103, 1, ["claude"], "/work/by-cwd", 350.0),
            cc.proc_record(104, 1, ["claude", "--resume", "44444444-4444-4444-8444-444444444444"], "/w/c", 200.0),
            cc.proc_record(105, 1, ["claude"], "/nowhere", 100.0),
            cc.proc_record(106, 1, ["claude", "daemon", "run"], "/", 150.0),
        ]
        out = cc.hot_idle_scan([hi], now=NOW, procs=procs, free_mb=1600)
        by_pid = {r["pid"]: r for r in out["rows"]}
        gate("V-CCN-CENSUS-HOTIDLE-IDLE", by_pid[101]["state"] == "JOINED" and abs(by_pid[101]["idle_min"] - 1800.0) < 0.2,
             "30 h idle listed from record timestamps, not mtime (mtime was forced to now): idle_min=%s" % by_pid[101]["idle_min"])
        gate("V-CCN-CENSUS-HOTIDLE-ACTIVE", by_pid[102]["state"] == "JOINED" and by_pid[102]["idle_min"] == 1.5 and
             out["rows"][0]["pid"] == 101, "active session idle_min=%s, sorted below the idle one (first=%s)" % (by_pid[102]["idle_min"], out["rows"][0]["pid"]))
        gate("V-CCN-CENSUS-HOTIDLE-CWD", by_pid[103]["joined_by"] == "cwd" and by_pid[103]["idle_min"] == 180.0,
             "no id on the command line: joined by cwd, idle_min=%s" % by_pid[103]["idle_min"])
        gate("V-CCN-CENSUS-HOTIDLE-UNKNOWN", by_pid[104]["state"] == "UNKNOWN" and by_pid[105]["state"] == "UNKNOWN" and
             by_pid[104]["idle_min"] is None, "unresolvable id and unowned cwd are UNKNOWN with idle=None, not 0")
        gate("V-CCN-CENSUS-HOTIDLE-COUNTS", out["sessions"] == 5 and out["joined_by_id"] == 2 and out["joined_by_cwd"] == 1 and
             out["unjoined"] == 2 and out["by_role"].get("daemon") == 1 and out["free_ram_mb"] == 1600,
             "sessions=%d by_id=%d by_cwd=%d unjoined=%d roles=%s free=%s" % (out["sessions"], out["joined_by_id"], out["joined_by_cwd"], out["unjoined"], out["by_role"], out["free_ram_mb"]))

        # Phase 3 advisory: idle listed, active not, unjoinable UNKNOWN and never ranked; atomic file; read-only
        procs2 = procs + [cc.proc_record(107, 1, ["claude", "--resume", sid_old], "/home/k/missions/ccn", 250.0)]
        adv = cc.advise(cc.hot_idle_scan([hi], now=NOW, procs=procs2, free_mb=1600))
        ranked = [a["pid"] for a in adv["idle"]]
        gate("V-CCN-CENSUS-ADVISE-IDLE", ranked[:2] == [101, 107] and 102 not in ranked and 103 not in ranked and
             adv["idle"][0]["idle_hours"] == 30.0, "30 h sessions listed (ranked by working set on ties), active 102 and 3 h-idle 103 not: %s" % ranked)
        gate("V-CCN-CENSUS-ADVISE-UNKNOWN", sorted(u["pid"] for u in adv["unknown"]) == [104, 105] and not {104, 105} & set(ranked),
             "unjoinable sessions are UNKNOWN and absent from the ranking: %s" % adv["unknown"])
        by_adv = {a["pid"]: a for a in adv["idle"]}
        gate("V-CCN-CENSUS-ADVISE-PATH", "hold --stop" in by_adv[107]["release"] and "Owner closes" in by_adv[101]["release"] and
             by_adv[101]["confidence"] == "HIGH", "mission worker -> hold --stop, pane -> Owner closes: %s | %s" % (by_adv[107]["release"][:40], by_adv[101]["release"][:40]))
        quiet = cc.advise(cc.hot_idle_scan([hi], now=NOW, procs=[procs[1]], free_mb=1600))
        gate("V-CCN-CENSUS-ADVISE-EMPTY", quiet["idle"] == [] and quiet["unknown"] == [], "only an active session: nothing listed (not an error)")
        sf = os.path.join(tmp, "state", "ccn-hot-idle.json")
        cc.write_advisory(adv, sf)
        back = json.load(open(sf))
        gate("V-CCN-CENSUS-ADVISE-FILE", [a["pid"] for a in back["idle"]] == ranked and "written_at" in back and
             not [f for f in os.listdir(os.path.dirname(sf)) if f.endswith(".tmp")], "file round-trips and leaves no .tmp behind")
        sect = open(cc.__file__).read().split("# ---------------------------------------------------------------- advisory")[1].split("# ---------------------------------------------------------------- check")[0]
        gate("V-CCN-CENSUS-ADVISE-READONLY", not re.search(r"os\.kill|signal\.|terminate|subprocess|\.stop\(", sect),
             "advisory section has no kill/signal/subprocess call")
        m = mutant([("elif r[\"idle_min\"] >= min_idle:", "elif True:")])
        madv = m.advise(m.hot_idle_scan([hi], now=NOW, procs=procs2, free_mb=1600))
        gate("V-CCN-CENSUS-ADVISE-MUTANT", 102 in [a["pid"] for a in madv["idle"]], "idle filter removed: the active session is listed (mutant must go red)")

        # a transcript whose records carry no timestamp must read as UNKNOWN, not as idle-forever or active
        notime = write_session(hi, "-r-nt", "55555555-5555-4555-8555-555555555555", [{"type": "summary"}])
        out2 = cc.hot_idle_scan([hi], now=NOW, procs=[cc.proc_record(201, 1, ["claude", "--resume", "55555555-5555-4555-8555-555555555555"], "/w", 1.0)], free_mb=None)
        gate("V-CCN-CENSUS-HOTIDLE-NOTIME", out2["rows"][0]["state"] == "UNKNOWN" and out2["rows"][0]["idle_min"] is None and out2["free_ram_mb"] is None,
             "no timestamp: state=%s idle=%s; unreadable RAM stays None" % (out2["rows"][0]["state"], out2["rows"][0]["idle_min"]))

        # argv parsing: path form of --resume, the = form, -r, and a non-claude process
        gate("V-CCN-CENSUS-ARGV", cc.argv_session_id(["claude", "--resume", "/h/.claude/projects/p/" + sid_old + ".jsonl"]) == sid_old and
             cc.argv_session_id(["claude", "--session-id=" + sid_new.upper()]) == sid_new and cc.argv_session_id(["claude", "-r", sid_cwd]) == sid_cwd and
             cc.argv_session_id(["claude", "--resume", "not-a-uuid"]) is None and not cc.is_claude_argv(["bash", "-c", "claude"]) and
             cc.is_claude_argv([r"C:\Users\x\claude.exe"]), "id forms parsed; bash -c 'claude' is not a claude process")

        # Linux backend against a fake /proc, including the fused-argv[0] process-title form seen on real hosts
        # The fake /proc needs symlinks; an unprivileged Windows account cannot create them, so on
        # that plane the gate is reported as SKIP (not counted as a pass) instead of crashing the suite.
        fake = os.path.join(tmp, "proc")
        try:
            for pid, raw, cwd in [("301", b"claude bg-spare\x00--bg-spare\x00/tmp/s.sock", "/work/by-cwd"),
                                  ("302", b"/usr/bin/claude\x00--resume\x00" + sid_new.encode(), "/w/b"),
                                  ("303", b"/bin/bash\x00-c\x00claude", "/")]:
                os.makedirs(os.path.join(fake, pid))
                open(os.path.join(fake, pid, "cmdline"), "wb").write(raw)
                open(os.path.join(fake, pid, "status"), "w").write("Name:\tclaude\nPPid:\t1\nVmRSS:\t204800 kB\n")
                os.symlink(cwd, os.path.join(fake, pid, "cwd"))
            symlinks_ok = True
        except OSError as e:
            symlinks_ok = False
            print("SKIP V-CCN-CENSUS-LINUX-BACKEND: cannot build the fake /proc on this plane (%s); run on Linux" % e)
        if symlinks_ok:
            os.makedirs(os.path.join(fake, "self"))   # non-numeric entries must be ignored
            lp = {p["pid"]: p for p in cc.procs_linux(fake)}
            gate("V-CCN-CENSUS-LINUX-BACKEND", sorted(lp) == [301, 302] and lp[301]["role"] == "spare" and lp[302]["session_id"] == sid_new and
                 lp[301]["rss_mb"] == 200.0 and lp[301]["cwd"] == "/work/by-cwd",
                 "fused title split, bash excluded, rss from VmRSS: pids=%s roles=%s" % (sorted(lp), {k: v["role"] for k, v in lp.items()}))

        # Windows backend against a recorded CIM JSON shape (single object and list forms)
        cim = json.dumps([{"ProcessId": 11, "ParentProcessId": 2, "WorkingSetSize": 314572800,
                           "CommandLine": '"C:\\Users\\U\\claude.exe" --resume ' + sid_old},
                          {"ProcessId": 12, "ParentProcessId": 2, "WorkingSetSize": 1048576, "CommandLine": "notepad.exe a.txt"}])
        wp = cc.procs_from_cim_json(cim)
        single_form = cc.procs_from_cim_json(json.dumps({"ProcessId": 13, "ParentProcessId": 2, "WorkingSetSize": 2097152, "CommandLine": "claude.exe"}))
        gate("V-CCN-CENSUS-WINDOWS-BACKEND", len(wp) == 1 and wp[0]["session_id"] == sid_old and wp[0]["rss_mb"] == 300.0 and wp[0]["cwd"] is None and
             len(single_form) == 1 and single_form[0]["rss_mb"] == 2.0 and cc.procs_from_cim_json("") == [],
             "CIM list+single object parsed, non-claude dropped, cwd None, empty output -> []")

        # ---------------------------------------------------------------- parity with the seed scripts (the plan's exact evidence)
        seed_dup = os.path.join(SEED_DIR, "dup.py")
        seed_stamp = os.path.join(SEED_DIR, "stampede.py")
        if os.path.isfile(seed_dup) and os.path.isfile(seed_stamp):
            home = os.path.join(tmp, "home")
            proj = os.path.join(home, ".claude", "projects")
            fixture_now = time.time()
            # the seed reads local time and the real clock: build a fixture relative to the real clock
            build_dup_estate(proj, fixture_now)
            for i in range(6):
                write_session(proj, "p-s", "st%02d" % i, first_call(fixture_now - 7200 + i * 60, 50_000 + i, 20_000))
            write_session(proj, "p-s", "stiso", first_call(fixture_now - 40000, 80_000, 10_000))
            env = dict(os.environ, HOME=home, USERPROFILE=home, TZ="UTC")
            sd = subprocess.run([sys.executable, "-I", seed_dup, "24"], env=env, capture_output=True, text=True).stdout
            ss = subprocess.run([sys.executable, "-I", seed_stamp], env=env, capture_output=True, text=True).stdout
            mine = cc.dup_scan([proj], hours=24)
            mst = cc.stampede_scan([proj], days=7)
            sm = re.search(r"tool_events=(\d+).*\n.*calls=(\d+)", sd)
            seed_ev, seed_dups = (int(sm.group(1)), int(sm.group(2))) if sm else (None, None)
            gate("V-CCN-CENSUS-SEED-PARITY-DUP", (seed_ev, seed_dups) == (mine["tool_events"], mine["dup_calls"]) and seed_dups == 1,
                 "seed dup.py events/dups=%s/%s, ccn_census=%s/%s" % (seed_ev, seed_dups, mine["tool_events"], mine["dup_calls"]))
            sc = re.search(r"launched <=5 min after another session:\n\s+cache_write n=(\d+) median=(\d+)", ss)
            si = re.search(r"isolated start:\n\s+cache_write n=(\d+) median=(\d+)", ss)
            seed_arms = (int(sc.group(1)), int(sc.group(2)), int(si.group(1)), int(si.group(2))) if sc and si else None
            my_arms = (mst["concurrent"]["n"], round(mst["concurrent"]["write_median"]), mst["isolated"]["n"], round(mst["isolated"]["write_median"]))
            gate("V-CCN-CENSUS-SEED-PARITY-STAMPEDE", seed_arms == my_arms and seed_arms is not None,
                 "seed stampede.py (conc n, median, iso n, median)=%s, ccn_census=%s" % (seed_arms, my_arms))
        else:
            _fail("V-CCN-CENSUS-SEED-PARITY-DUP", "seed scripts missing under %s" % SEED_DIR)
            _fail("V-CCN-CENSUS-SEED-PARITY-STAMPEDE", "seed scripts missing under %s" % SEED_DIR)

    print("CCN_PASS=%d/%d" % (passes, passes + fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
