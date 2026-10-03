#!/usr/bin/env python3
"""V-RUN-* gates: agent run accounting (ACV C6, plan vault/plans/acv-c6-run-accounting-2026-10-03.md).

The executor is the real one's OUTPUT: four `claude -p` stream-json logs recorded on real runs
(vault/audits/agent_estate/real_boundary/s4/*.stream.jsonl) are replayed at the subprocess
boundary of tools/agent_carrier_run.py, so parse, judge and accounting all run unmodified on bytes
the executor really produced. Each replay gets a per-run nonce session id, so no row this suite
produces can be mistaken for a historical or live one.

The live CO-12 corpus is protected as in C5: record_signal is replaced suite-wide by a guard that
writes only to a temp dir, and the last gate proves no live agent_run row carries a suite run_id.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import agent_carrier_run as RUN  # noqa: E402
from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime import agent_telemetry as T  # noqa: E402
from modules.cognitive_os import co_12_telemetry as CO12  # noqa: E402

STREAMS = ROOT / "vault" / "audits" / "agent_estate" / "real_boundary" / "s4"
SFH = "silent-failure-hunter"
NONCE = "".join(random.choice("bcdfghjklmnpqrstvwxz") for _ in range(12))
SFH_TASK = f"check this service for swallowed errors {NONCE}"
NOMATCH_TASK = f"compose a jingle for a pizza advert {NONCE}"
RUN_FIELDS = {"schema", "resolution_id", "run_id", "run_id_source", "spec", "spec_hash", "permission_class",
              "carrier", "purpose", "executor_status", "executor_error", "harness_status", "result_events",
              "usage_state", "model_usage", "carrier_share", "models_observed", "carrier_model_configured", "seconds"}
passes = fails = 0
SUITE_RUN_IDS: set = set()
REAL_RECORD = CO12.record_signal
GUARD: dict = {"dir": None, "calls": []}


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def guarded_record(kind, payload, *, state_dir=None, now=None):
    GUARD["calls"].append((kind, payload))
    return REAL_RECORD(kind, payload, state_dir=state_dir or GUARD["dir"], now=now)


class Capture:
    def __init__(self, answer=True):
        self.calls, self.answer = [], answer

    def __call__(self, kind, payload):
        self.calls.append((kind, payload))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer

    def of(self, kind):
        return [p for k, p in self.calls if k == kind]


def events(name: str) -> list:
    out = []
    for ln in (STREAMS / f"{name}.stream.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict):
            out.append(ev)
    return out


def result_of(evs: list) -> dict:
    return next((e for e in reversed(evs) if e.get("type") == "result"), {})


def stream(evs: list, sid: str | None = None) -> str:
    """Serialise events back to a stream, giving the run a fresh nonce session id."""
    sid = sid or f"{NONCE}-{random.randrange(10**9)}"
    SUITE_RUN_IDS.add(sid)
    return "\n".join(json.dumps({**e, "session_id": sid} if "session_id" in e else e) for e in evs) + "\n"


class Replay:
    """The subprocess boundary of agent_carrier_run: answers with a recorded real stream."""
    def __init__(self, text: str | None = None, timeout: bool = False, partial: bytes | None = None):
        self.text, self.timeout, self.partial, self.calls = text, timeout, partial, 0

    def __enter__(self):
        # RUN.subprocess IS the global module: patching it reaches every caller in the process (the
        # resolver's own git probes included). Only the executor's argv is replayed and counted;
        # anything else passes through to the real call.
        self.real_run, self.real_which = RUN.subprocess.run, RUN.shutil.which
        real_run, real_which = self.real_run, self.real_which
        RUN.shutil.which = lambda name: "claude" if name == "claude" else real_which(name)

        def fake(argv, **kw):
            if not argv or argv[0] != "claude":
                return real_run(argv, **kw)
            self.calls += 1
            if self.timeout:
                raise subprocess.TimeoutExpired(argv, kw.get("timeout"), output=self.partial)
            return subprocess.CompletedProcess(argv, 0, stdout=self.text, stderr="")
        RUN.subprocess.run = fake
        return self

    def __exit__(self, *exc):
        RUN.subprocess.run, RUN.shutil.which = self.real_run, self.real_which
        return False


def usage_contract() -> None:
    print("\n[run] usage contract on the real executor's result events")
    bad, shares = [], {}
    for name in ("e2e", "ho_b", "mech", "writer"):
        evs = events(name)
        res = result_of(evs)
        state, usage = T.usage_from_result(res)
        src = res.get("modelUsage") or {}
        copied = set(usage) == set(src) and all(usage[m][f] == src[m][f] for m in usage for f in usage[m])
        no_price = not any(k in row for row in usage.values() for k in ("costUSD", "costBasis", "contextWindow"))
        if not (state == "MEASURED" and copied and no_price and all(set(T.CORE_USAGE) <= set(r) for r in usage.values())):
            bad.append(f"{name}: {state} copied={copied} no_price={no_price}")
        shares[name] = T.carrier_share(usage, RUN.parse_stream([json.dumps(e) for e in evs])["models"])
    check("V-RUN-USAGE-COPIED", not bad, bad or "4 real result events: MEASURED, token fields copied verbatim, no price")
    check("V-RUN-CARRIER-SHARE", (shares["e2e"], shares["writer"], shares["mech"]) == (
        "SEPARABLE", "SEPARABLE", "UNSEPARABLE"), f"{shares} (mech: parent and carrier both haiku)")

    base = result_of(events("e2e"))
    one = next(iter(base["modelUsage"]))
    cases = {
        "no result event": T.usage_from_result(None),
        "no modelUsage": T.usage_from_result({k: v for k, v in base.items() if k != "modelUsage"}),
        "empty modelUsage": T.usage_from_result({**base, "modelUsage": {}}),
        "entry lacks outputTokens": T.usage_from_result({**base, "modelUsage": {
            **base["modelUsage"], one: {k: v for k, v in base["modelUsage"][one].items() if k != "outputTokens"}}}),
    }
    got = {k: v[0] for k, v in cases.items()}
    zeros = [k for k, (st, u) in cases.items() if st == "UNMEASURED" and u]
    check("V-RUN-UNMEASURED-NOT-ZERO", got == {"no result event": "UNMEASURED", "no modelUsage": "UNMEASURED",
                                              "empty modelUsage": "UNMEASURED", "entry lacks outputTokens": "PARTIAL"}
          and not zeros and "outputTokens" not in cases["entry lacks outputTokens"][1][one],
          f"{got}; a missing field stays missing, never 0")
    no_side = [e for e in events("e2e") if not e.get("parent_tool_use_id")]
    check("V-RUN-SHARE-UNKNOWN", T.carrier_share(base["modelUsage"], RUN.parse_stream(
        [json.dumps(e) for e in no_side])["models"]) == "UNKNOWN", "no sidechain message observed -> UNKNOWN")


def run_paths(t: Path) -> None:
    print("\n[run] every post-start exit emits exactly one terminal agent_run")
    mission = "check the fixture for swallowed errors"
    evs = events("e2e")
    res = result_of(evs)
    init = [e for e in evs if e.get("type") == "system"]
    parent_call = next(e for e in evs if e.get("type") == "assistant" and not e.get("parent_tool_use_id")
                       and any(c.get("type") == "tool_use" for c in e["message"]["content"]))
    blocked = {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "x", "content": "PreToolUse:Agent hook error: blocked"}]}}
    shapes = {   # name -> (events, expected harness status)
        "full run": (evs, "MEASURED"),
        "no tool call": (init + [res], "UNMEASURED"),
        "dispatch blocked": (init + [parent_call, blocked, res], "DISPATCH_BLOCKED"),
        "empty reply": (init + [parent_call, res], "UNMEASURED"),
    }
    bad = []
    for name, (shape, harness) in shapes.items():
        cap = Capture()
        text = stream(shape)
        with Replay(text):
            rec = RUN.run(SFH, mission, sink=cap)
        runs = cap.of(T.RUN_KIND)
        p = runs[0] if len(runs) == 1 else {}
        sid = result_of([json.loads(x) for x in text.splitlines()]).get("session_id")
        n_results = sum(1 for e in shape if e.get("type") == "result")
        ok = (len(runs) == 1 and set(p) == RUN_FIELDS and p["run_id"] == sid and p["executor_status"] == "success"
              and p["run_id_source"] == "result" and p["result_events"] == n_results and p["executor_error"] is False
              and p["usage_state"] == "MEASURED" and p["harness_status"] == harness == rec["status"]
              and p["resolution_id"] is None and p["purpose"] == "manual" and p["spec"] == SFH
              and rec.get("run_id") == sid and rec.get("run_recorded") is True)
        if not ok:
            bad.append(f"{name}: signals={len(runs)} harness={p.get('harness_status')}/{rec.get('status')} "
                       f"usage={p.get('usage_state')} run_id_ok={p.get('run_id') == sid} keys={sorted(set(p) ^ RUN_FIELDS)}")
    check("V-RUN-EVERY-EXIT-ACCOUNTED", not bad, bad or
          "full / no-tool-call / dispatch-blocked / empty-reply: one signal each, usage MEASURED from the result")

    cap = Capture()
    with Replay(timeout=True):
        rec = RUN.run(SFH, mission, sink=cap, timeout=5)
    p = (cap.of(T.RUN_KIND) or [{}])[0]
    check("V-RUN-TIMEOUT", len(cap.of(T.RUN_KIND)) == 1 and (p.get("executor_status"), p.get("usage_state"),
          p.get("run_id"), p.get("model_usage")) == ("TIMEOUT", "UNMEASURED", None, {}) and rec["status"] == "UNMEASURED",
          f"a run that started and timed out: {p.get('executor_status')}/{p.get('usage_state')} run_id={p.get('run_id')}")

    cap = Capture()
    real_which = RUN.shutil.which
    RUN.shutil.which = lambda name: None
    try:
        rec = RUN.run(SFH, mission, sink=cap)
    finally:
        RUN.shutil.which = real_which
    try:
        RUN.run("no-such-spec", mission, sink=cap)
        code = "NO_ERROR"
    except A.AgentSpecError as e:
        code = e.code
    check("V-RUN-NEVER-STARTED", not cap.calls and rec["status"] == "UNMEASURED" and code != "NO_ERROR",
          f"CLI missing -> {rec['status']} and typed error {code}: no process ran, no agent_run")

    outs = {}
    for name, sink in {"returns-False": Capture(False), "raises": Capture(OSError("disk"))}.items():
        with Replay(stream(evs)):
            rec = RUN.run(SFH, mission, sink=sink)
        outs[name] = (rec["status"], rec.get("run_recorded"))
    check("V-RUN-SINK-FAILURE", all(v == ("MEASURED", False) for v in outs.values()),
          f"(run status, run_recorded) {outs}: the run record is unchanged, the failed write is visible")

    cap = Capture()
    real_reply = RUN.carrier_reply
    RUN.carrier_reply = lambda s: (_ for _ in ()).throw(ValueError("harness defect"))
    try:
        with Replay(stream(evs)):
            try:
                RUN.run(SFH, mission, sink=cap)
                raised = False
            except ValueError:
                raised = True
    finally:
        RUN.carrier_reply = real_reply
    p = (cap.of(T.RUN_KIND) or [{}])[0]
    check("V-RUN-HARNESS-ERROR", raised and len(cap.of(T.RUN_KIND)) == 1 and p.get("harness_status") == "HARNESS_ERROR"
          and p.get("usage_state") == "MEASURED",
          f"harness exception after the run: re-raised={raised}, signal {p.get('harness_status')}/{p.get('usage_state')}")
    audit_gates(t, evs, mission)


def audit_gates(t: Path, evs: list, mission: str) -> None:
    print("\n[run] phase-4 audit gaps 1/2/3/5")

    def one(shape=None, **replay):
        cap = Capture()
        text = stream(shape) if shape is not None else None
        with Replay(text, **replay):
            RUN.run(SFH, mission, sink=cap, timeout=5)
        runs = cap.of(T.RUN_KIND)
        return (runs[0] if len(runs) == 1 else {"signals": len(runs)}), text

    # gap 1: real streams carry two result events; disagreement makes the total untrustworthy.
    n = sum(1 for e in evs if e.get("type") == "result")
    first = next(i for i, e in enumerate(evs) if e.get("type") == "result")
    m0 = next(iter(evs[first]["modelUsage"]))
    bumped = json.loads(json.dumps(evs))
    bumped[first]["modelUsage"][m0]["inputTokens"] += 1
    ctrl, _ = one(evs)
    p, _ = one(bumped)
    _, last_usage = T.usage_from_result(result_of(evs))
    check("V-RUN-RESULTS-DISAGREE", n >= 2 and (ctrl.get("usage_state"), ctrl.get("result_events"), "usage_reason" in ctrl)
          == ("MEASURED", n, False) and (p.get("usage_state"), p.get("usage_reason"), p.get("result_events"))
          == ("PARTIAL", "result_events_disagree", n) and p.get("model_usage") == last_usage,
          f"real stream has {n} result events: agreeing -> {ctrl.get('usage_state')}, one modelUsage bumped -> "
          f"{p.get('usage_state')}/{p.get('usage_reason')} (last result's tokens kept, not merged)")

    # gap 2: the CLI reports an API failure as subtype success + is_error true.
    erred = json.loads(json.dumps(evs))
    erred[max(i for i, e in enumerate(erred) if e.get("type") == "result")]["is_error"] = True
    state = t / "err-state"
    cap = Capture()
    with Replay(stream(erred)):
        RUN.run(SFH, mission, sink=lambda k, pl: cap(k, pl) and REAL_RECORD(k, pl, state_dir=state))
    p = (cap.of(T.RUN_KIND) or [{}])[0]
    split = T.agent_metrics(state_dir=state).get("runs", {}).get("by_executor_status")
    check("V-RUN-EXECUTOR-ERROR", (p.get("executor_status"), p.get("executor_error")) == ("success", True)
          and ctrl.get("executor_error") is False and split == {"success+is_error": 1},
          f"is_error copied verbatim ({p.get('executor_status')}, is_error={p.get('executor_error')}; control "
          f"{ctrl.get('executor_error')}); metrics split {split}")

    # gap 3: a typed spec error raised AFTER the process ran is still one accounted run.
    cap = Capture()
    real_reply = RUN.carrier_reply
    RUN.carrier_reply = lambda s: (_ for _ in ()).throw(A.AgentSpecError("BUNDLE_INVALID", "post-start"))
    text, code = stream(evs), None
    try:
        with Replay(text):
            try:
                RUN.run(SFH, mission, sink=cap)
            except A.AgentSpecError as e:
                code = e.code
    finally:
        RUN.carrier_reply = real_reply
    runs = cap.of(T.RUN_KIND)
    sid = result_of([json.loads(x) for x in text.splitlines()]).get("session_id")
    check("V-RUN-POST-START-SPEC-ERROR", code == "BUNDLE_INVALID" and len(runs) == 1
          and (runs[0].get("harness_status"), runs[0].get("run_id")) == ("HARNESS_ERROR", sid),
          f"AgentSpecError after start: re-raised {code}, {len(runs)} agent_run, keyed on `started` not the exception")

    # gap 5: a timed-out run still names its session from the init event in the partial output.
    init = [e for e in evs if e.get("type") == "system"]
    partial = stream(init)
    p, _ = one(timeout=True, partial=partial.encode("utf-8"))
    sid = next(json.loads(x)["session_id"] for x in partial.splitlines() if "session_id" in json.loads(x))
    check("V-RUN-TIMEOUT-INIT-ID", init and (p.get("run_id"), p.get("run_id_source"), p.get("executor_status"),
          p.get("executor_error"), p.get("usage_state"), p.get("usage_reason"))
          == (sid, "init", "TIMEOUT", None, "UNMEASURED", "no_result_event"),
          f"timeout with partial bytes: run_id={p.get('run_id') == sid} source={p.get('run_id_source')} "
          f"{p.get('executor_status')}/{p.get('usage_state')}")


def resolve_first(t: Path) -> None:
    print("\n[run] resolve-first: one resolution, its runs joined on resolution_id")
    cat = t / "cat"
    shutil_copy(A.SPECS_DIR / SFH, cat / SFH)
    cap = Capture()
    with Replay(stream(events("e2e"))) as rp:
        out = RUN.resolve_and_run(SFH_TASK, "check the fixture", max_class="investigator", specs_dir=cat,
                                  use_cache=False, sink=cap)
    res, runs = cap.of(T.KIND), cap.of(T.RUN_KIND)
    rid = res[0]["resolution_id"] if len(res) == 1 else None
    check("V-RUN-RESOLVE-JOIN", rp.calls == 1 and len(res) == 1 and len(runs) == 1 and rid
          and runs[0]["resolution_id"] == rid == out["resolution_id"] and runs[0]["purpose"] == "resolved"
          and runs[0]["spec"] == res[0]["candidate_ids"][0] == SFH,
          f"resolution {rid} -> run {runs[0].get('run_id') if runs else None} ({len(res)} resolution, {len(runs)} run)")

    cap = Capture()
    with Replay(stream(events("e2e"))) as rp:
        out = RUN.resolve_and_run(NOMATCH_TASK, "anything", specs_dir=cat, use_cache=False, sink=cap)
    check("V-RUN-NO-CANDIDATE-NO-RUN", rp.calls == 0 and len(cap.of(T.KIND)) == 1 and not cap.of(T.RUN_KIND)
          and out.get("status") == "NO_RUN" and out.get("miss") == "NO_MATCH",
          f"NO_MATCH -> {len(cap.of(T.KIND))} resolution, {len(cap.of(T.RUN_KIND))} runs, executor calls {rp.calls}")


def shutil_copy(src: Path, dst: Path) -> None:
    import shutil
    shutil.copytree(src, dst)


def metrics(t: Path) -> None:
    print("\n[run] metrics derived from the same signals")
    state = t / "metrics-state"

    def sink(kind, payload):
        return REAL_RECORD(kind, payload, state_dir=state)

    cat = t / "mcat"
    shutil_copy(A.SPECS_DIR / SFH, cat / SFH)
    e2e, mech = events("e2e"), events("mech")
    with Replay(stream(e2e)):
        RUN.resolve_and_run(SFH_TASK, "m", max_class="investigator", specs_dir=cat, use_cache=False, sink=sink)
    with Replay(stream(mech)):
        RUN.run(SFH, "m", sink=sink)                                  # unlinked, UNSEPARABLE
    with Replay(timeout=True):
        RUN.run(SFH, "m", sink=sink, timeout=5)                       # unlinked, UNMEASURED
    T.resolve_and_record(NOMATCH_TASK, specs_dir=cat, use_cache=False, sink=sink)   # zero runs
    with Replay(stream(e2e)):
        RUN.run(SFH, "m", sink=sink, resolution_id="dangling-" + NOMATCH_TASK.split()[-1])
    m = T.agent_metrics(state_dir=state)
    r = m.get("runs", {})
    e2e_tok = result_of(e2e)["modelUsage"]
    mech_tok = result_of(mech)["modelUsage"]
    expect_in = {mdl: sum(u[mdl]["inputTokens"] for u in (e2e_tok, e2e_tok, mech_tok) if mdl in u)
                 for mdl in set(e2e_tok) | set(mech_tok)}
    got_in = {mdl: v.get("inputTokens") for mdl, v in r.get("measured_tokens", {}).items()}
    check("V-RUN-METRICS", r.get("runs") == 4 and (r.get("linked"), r.get("unlinked"), r.get("dangling")) == (1, 2, 1)
          and r.get("usage_state") == {"MEASURED": 3, "UNMEASURED": 1} and r.get("resolutions_with_zero_runs") == 1
          and r.get("carrier_share", {}).get("UNSEPARABLE") == 1 and got_in == expect_in
          and r.get("linked_by_resolution_cache") == {"MISS": 1},
          f"runs={r.get('runs')} linked/unlinked/dangling={r.get('linked')}/{r.get('unlinked')}/{r.get('dangling')} "
          f"usage={r.get('usage_state')} zero-run resolutions={r.get('resolutions_with_zero_runs')} input tokens {got_in}")
    blob = json.dumps(m).lower()
    banned = [w for w in ("waste", "saving", "roi", "demand", "value", "cost") if f'"{w}' in blob or f'_{w}' in blob]
    check("V-RUN-METRICS-NAMES", not banned, f"no overclaiming keys {banned}")


def main() -> int:
    live_dir = CO12._default_state_dir()
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        GUARD["dir"] = t / "guard"
        CO12.record_signal = guarded_record
        try:
            n0 = len(GUARD["calls"])
            with Replay(stream(events("e2e"))):
                RUN.run(SFH, "control")                               # sink=None -> CO-12 (guarded)
            check("V-RUN-DEFAULT-SINK-CONTROL", len(GUARD["calls"]) == n0 + 1 and GUARD["calls"][-1][0] == T.RUN_KIND,
                  "sink=None reaches CO-12 record_signal, looked up at call time")
            usage_contract()
            run_paths(t)
            resolve_first(t)
            metrics(t)
        finally:
            CO12.record_signal = REAL_RECORD
    try:
        live = [s for s in CO12.load_signals(state_dir=live_dir, strict=True)
                if isinstance(s, dict) and s.get("kind") == T.RUN_KIND]
        leaked, looked = [s.get("run_id") for s in live if s.get("run_id") in SUITE_RUN_IDS], "read"
    except OSError as e:
        live, leaked, looked = [], [], f"UNREADABLE {type(e).__name__}"
    check("V-RUN-LIVE-ISOLATION", SUITE_RUN_IDS and looked == "read" and not leaked,
          f"live corpus {looked}: {len(SUITE_RUN_IDS)} suite run ids, {len(live)} live agent_run rows, leaked={leaked}")
    print(f"AGENT_RUN_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
