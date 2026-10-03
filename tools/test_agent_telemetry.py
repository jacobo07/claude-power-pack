#!/usr/bin/env python3
"""V-TEL-* gates: resolver results into CO-12 telemetry (ACV C5, plan acv-c5-agent-telemetry).

Everything runs through the REAL resolver and, where a write is the subject, the REAL
co_12_telemetry.record_signal on a temp state_dir. The live signals corpus is protected two ways:
for the whole suite CO-12's record_signal is replaced by a guard that writes only to a temp dir,
and every task carries a per-run nonce word, so the last gate can prove that no live
agent_resolution row carries any query_fp this suite produced.

These gates test the MAPPING and the wiring. Resolver semantics are tools/test_agent_resolver.py.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import random
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime import agent_resolver as R  # noqa: E402
from modules.capability_runtime import agent_resolver_cli as CLI  # noqa: E402
from modules.capability_runtime import agent_telemetry as T  # noqa: E402
from modules.cognitive_os import co_12_telemetry as CO12  # noqa: E402

SFH, AUDITOR = "silent-failure-hunter", "oneshot-architect-auditor"
NONCE = "".join(random.choice("bcdfghjklmnpqrstvwxz") for _ in range(12))   # no spec contains it
SFH_TASK = f"check this service for swallowed errors {NONCE}"
AUDIT_TASK = f"audit this migration plan for gaps before implementation {NONCE}"
NOMATCH_TASK = f"compose a jingle for a pizza advert {NONCE}"
FIELDS = {"schema", "resolution_id", "miss", "candidate_ids", "miss_ids", "miss_ids_total", "vetoed_by",
          "cache", "policy", "catalog_fp", "query_fp", "grant"}
passes = fails = 0
SUITE_QFPS: set = set()
REAL_RECORD = CO12.record_signal
GUARD_CALLS: list = []


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


class Capture:
    """A sink that keeps what it was given and answers like record_signal."""
    def __init__(self, answer=True):
        self.calls, self.answer = [], answer

    def __call__(self, kind, payload):
        self.calls.append((kind, payload))
        SUITE_QFPS.add(payload.get("query_fp"))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def real_spec(cat: Path, sid: str, as_dir: str | None = None, evidence: list | None = None) -> None:
    d = cat / (as_dir or sid)
    shutil.copytree(A.SPECS_DIR / sid, d)
    if evidence:
        raw = json.loads((d / "spec.json").read_text(encoding="utf-8"))
        raw["contract"]["required_evidence"] = evidence
        (d / "spec.json").write_text(json.dumps(raw), encoding="utf-8")


def strip(res: dict) -> dict:
    return {k: v for k, v in res.items() if k != "ms"}


def rr(task, sink, **kw):
    rec = T.resolve_and_record(task, sink=sink, **kw)
    SUITE_QFPS.add(rec.result.get("query_fp"))
    return rec


def contract_and_misses(t: Path) -> None:
    print("\n[telemetry] contract + every typed miss through the real resolver")
    both = t / "both"
    real_spec(both, SFH)
    real_spec(both, AUDITOR)
    below = t / "below"
    real_spec(below, SFH, evidence=["runtime-trace"])
    partial = t / "partial"
    real_spec(partial, SFH)
    (partial / "zz-broken").mkdir()
    (partial / "zz-broken" / "spec.json").write_bytes(b"\xff\xfe{ not text")
    cases = {  # name: (task, grant, catalog, expected miss, expected miss_ids, expected candidates)
        "RESOLVED": (SFH_TASK, "investigator", both, None, [], [SFH]),
        "NO_MATCH": (NOMATCH_TASK, "verifier", both, "NO_MATCH", [], []),
        "CLASS_EXCLUDED": (AUDIT_TASK, "investigator", both, "CLASS_EXCLUDED", [AUDITOR], []),
        "BELOW_GATE": (SFH_TASK, "investigator", below, "BELOW_GATE", [SFH], []),
        "CATALOG_PARTIAL": (NOMATCH_TASK, "verifier", partial, "CATALOG_UNREADABLE", ["zz-broken"], []),
        "NO_CATALOG": (NOMATCH_TASK, "verifier", t / "absent", "CATALOG_UNREADABLE", [], []),
    }
    bad = []
    for name, (task, grant, cat, miss, ids, cands) in cases.items():
        cap = Capture()
        rec = rr(task, cap, max_class=grant, specs_dir=cat, use_cache=False)
        if len(cap.calls) != 1:
            bad.append(f"{name}: {len(cap.calls)} signals")
            continue
        kind, p = cap.calls[0]
        res = rec.result
        copied = all(p[f] == res[g] for f, g in (("miss", "miss"), ("miss_ids", "miss_ids"), ("cache", "cache"),
                                                  ("policy", "policy"), ("catalog_fp", "fingerprint"),
                                                  ("query_fp", "query_fp"), ("vetoed_by", "vetoed_by")))
        ok = (kind == T.KIND and set(p) == FIELDS and p["schema"] == T.SCHEMA and copied and rec.recorded
              and p["resolution_id"] == rec.resolution_id and p["grant"] == grant
              and (p["miss"], p["miss_ids"], p["candidate_ids"]) == (miss, ids, cands)
              and p["miss_ids_total"] == len(ids) and not ({"kind", "ts"} & p.keys()))
        if not ok:
            bad.append(f"{name}: {kind} miss={p['miss']} ids={p['miss_ids']} cands={p['candidate_ids']} "
                       f"keys={sorted(set(p) ^ FIELDS)} copied={copied}")
    check("V-TEL-MISS-TYPES", not bad, bad or f"{len(cases)} outcomes incl. NO_CATALOG with no path in "
                                                  "miss_ids, payload copied from the result")

    # Ranker residue never becomes a causal id: on the REAL catalog this request leaves near-misses
    # and lexical exclusions, and the payload still carries no miss_ids. The residue is asserted
    # present, or the gate would pass vacuously.
    cap = Capture()
    rec = rr(f"write a haiku about the ocean {NONCE}", cap, max_class="investigator", use_cache=False)
    residue = len(rec.result["near_misses"]) + len(rec.result["excluded"])
    p = cap.calls[0][1] if cap.calls else {}
    check("V-TEL-RESIDUE-NOT-IDS", residue > 0 and p.get("miss") == "NO_MATCH" and p.get("miss_ids") == [],
          f"residue={residue} miss={p.get('miss')} ids={p.get('miss_ids')}")

    # The reserved-key refusal: a mapping that would emit `kind` is refused, the sink is never called.
    real_map = T.to_payload
    T.to_payload = lambda *a, **kw: {**real_map(*a, **kw), "kind": "spoofed"}
    try:
        cap = Capture()
        rec = rr(NOMATCH_TASK, cap, specs_dir=both, use_cache=False)
    finally:
        T.to_payload = real_map
    check("V-TEL-RESERVED-KEYS", not cap.calls and rec.recorded is False and rec.result["miss"] == "NO_MATCH",
          f"sink calls={len(cap.calls)} recorded={rec.recorded}")


def cache_and_identity(t: Path) -> None:
    print("\n[telemetry] cache provenance + request identity")
    cat = t / "cache-cat"
    real_spec(cat, SFH)
    cpath = t / "cache.json"
    cap = Capture()
    a = rr(NOMATCH_TASK, cap, specs_dir=cat, cache_path=cpath)
    b = rr(NOMATCH_TASK, cap, specs_dir=cat, cache_path=cpath)
    p1, p2 = cap.calls[0][1], cap.calls[1][1]
    check("V-TEL-CACHE", (p1["cache"], p2["cache"]) == ("MISS", "HIT") == (a.result["cache"], b.result["cache"])
          and p1["query_fp"] == p2["query_fp"] and p1["miss"] == p2["miss"] == "NO_MATCH"
          and p1["resolution_id"] != p2["resolution_id"],
          f"{p1['cache']}->{p2['cache']} qfp {p1['query_fp']}=={p2['query_fp']}")
    cap = Capture()
    x = rr(f"Review C++ code {NONCE}", cap, specs_dir=cat, use_cache=False)
    y = rr(f"review cpp code {NONCE}", cap, specs_dir=cat, use_cache=False)
    z = rr(f"review rust code {NONCE}", cap, specs_dir=cat, use_cache=False)
    q = [c[1]["query_fp"] for c in cap.calls]
    check("V-TEL-QUERY-FP", q == [x.result["query_fp"], y.result["query_fp"], z.result["query_fp"]]
          and q[0] == q[1] != q[2], f"payload qfps {q}")
    check("V-TEL-POLICY", all(c[1]["policy"] == R.policy_hash() for c in cap.calls),
          f"payload policy {cap.calls[0][1]['policy']} == policy_hash() {R.policy_hash()}")


def failure_and_cardinality(t: Path) -> None:
    print("\n[telemetry] failure domain + cardinality")
    cat = t / "fail-cat"
    real_spec(cat, SFH)
    direct = strip(R.resolve(SFH_TASK, "investigator", specs_dir=cat, use_cache=False))
    outs = {}
    for name, sink in {"returns-False": Capture(False), "raises": Capture(OSError("disk full"))}.items():
        rec = rr(SFH_TASK, sink, max_class="investigator", specs_dir=cat, use_cache=False)
        outs[name] = (rec.recorded, strip(rec.result) == direct)
    real_map = T.to_payload
    T.to_payload = lambda *a, **kw: (_ for _ in ()).throw(KeyError("query_fp"))
    try:
        rec = rr(SFH_TASK, Capture(), max_class="investigator", specs_dir=cat, use_cache=False)
        outs["mapping-raises"] = (rec.recorded, strip(rec.result) == direct)
    finally:
        T.to_payload = real_map
    check("V-TEL-SINK-FAILURE", all(v == (False, True) for v in outs.values()),
          f"(recorded, result==direct resolve) {outs}")

    cap = Capture()
    for _ in range(3):
        rr(SFH_TASK, cap, max_class="investigator", specs_dir=cat, use_cache=False)
    codes = []
    for bad_task, grant in (("!!! ???", "verifier"), ("", "verifier"), (SFH_TASK, "root")):
        try:
            T.resolve_and_record(bad_task, grant, specs_dir=cat, sink=cap, use_cache=False)
            codes.append("NO_ERROR")
        except A.AgentSpecError as e:
            codes.append(e.code)
    check("V-TEL-ONE-SIGNAL", len(cap.calls) == 3 and codes == ["EMPTY_TASK", "EMPTY_TASK", "UNKNOWN_CLASS"],
          f"3 resolutions -> {len(cap.calls)} signals; typed errors {codes} recorded nothing")


def production_reality(t: Path) -> None:
    print("\n[telemetry] real record_signal + metrics on an isolated state_dir")
    state, cat, cpath = t / "state", t / "prg-cat", t / "prg-cache.json"
    real_spec(cat, SFH)

    def sink(kind, payload):
        SUITE_QFPS.add(payload.get("query_fp"))
        return REAL_RECORD(kind, payload, state_dir=state)

    r1 = T.resolve_and_record(NOMATCH_TASK, specs_dir=cat, use_cache=False, sink=sink)
    T.resolve_and_record(NOMATCH_TASK, specs_dir=cat, use_cache=False, sink=sink)
    T.resolve_and_record(NOMATCH_TASK, specs_dir=cat, cache_path=cpath, sink=sink)    # MISS, fills cache
    T.resolve_and_record(NOMATCH_TASK, specs_dir=cat, cache_path=cpath, sink=sink)    # HIT
    T.resolve_and_record(SFH_TASK, "investigator", specs_dir=cat, use_cache=False, sink=sink)
    REAL_RECORD(T.KIND, {"schema": "agent-telemetry/0", "miss": "NO_MATCH", "cache": "MISS"}, state_dir=state)
    rows = [s for s in CO12.load_signals(state_dir=state) if s.get("kind") == T.KIND]
    first = rows[0] if rows else {}
    check("V-TEL-PRG-ROUNDTRIP", r1.recorded and len(rows) == 6 and first.get("ts")
          and first.get("resolution_id") == r1.resolution_id and first.get("query_fp") == r1.result["query_fp"],
          f"{len(rows)} rows read back; first ts={first.get('ts')}")

    m = T.agent_metrics(state_dir=state)
    nm = m.get("by_miss", {}).get("NO_MATCH")
    check("V-TEL-METRICS-FRESH-VS-CACHED", m.get("measured") and m.get("resolutions") == 6
          and (m.get("fresh"), m.get("cached")) == (4, 1) and nm == {"fresh": 3, "cached": 1}
          and m.get("distinct_fresh_observations") == 2 and m.get("schemas_seen") == {T.SCHEMA: 5, "agent-telemetry/0": 1},
          f"fresh={m.get('fresh')} cached={m.get('cached')} NO_MATCH={nm} "
          f"observations={m.get('distinct_fresh_observations')} schemas={m.get('schemas_seen')}")
    banned = [k for k in json.dumps(m).lower().split('"') if any(w in k for w in ("demand", "need", "gap"))]
    check("V-TEL-METRICS-NAMES", not banned, f"no overclaiming key names {banned}")

    empty = T.agent_metrics(state_dir=t / "no-state")
    real_read = pathlib.Path.read_text
    pathlib.Path.read_text = lambda self, *a, **kw: (_ for _ in ()).throw(PermissionError("locked")) \
        if self.name == "signals.jsonl" else real_read(self, *a, **kw)
    try:
        unreadable = T.agent_metrics(state_dir=state)
        lenient = CO12.load_signals(state_dir=state)
    finally:
        pathlib.Path.read_text = real_read
    check("V-TEL-METRICS-UNREADABLE-NOT-EMPTY",
          (empty.get("measured"), empty.get("status"), empty.get("resolutions")) == (True, "no observations", 0)
          and unreadable.get("measured") is False and "resolutions" not in unreadable and lenient == [],
          f"absent -> {empty.get('status')}/{empty.get('resolutions')}; unreadable -> {unreadable}; "
          f"default reader still fail-open -> {lenient}")

    rep = CO12.readiness_report(t / "no-projects", state_dir=state)
    real_metrics = T.agent_metrics
    T.agent_metrics = lambda **kw: (_ for _ in ()).throw(ValueError("reader defect"))
    try:
        broken = CO12.readiness_report(t / "no-projects", state_dir=state).get("agent_resolution", {})
    finally:
        T.agent_metrics = real_metrics
    numeric = [k for k, v in broken.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    check("V-TEL-CO12-REPORT", rep.get("agent_resolution") == m and broken.get("measured") is False
          and broken.get("status") == "error" and not numeric,
          f"report == agent_metrics; on a reader error -> {broken} (numeric keys {numeric})")

    # A torn line is counted as unparseable, never silently dropped (R2 audit gap 5), and the
    # rows that did parse are still counted.
    with (state / "signals.jsonl").open("ab") as fh:
        fh.write(b'{"kind": "agent_resolution", "schema": "agent-tel\n')
    torn = T.agent_metrics(state_dir=state)
    check("V-TEL-METRICS-UNPARSEABLE", m.get("unparseable_lines") == 0 and torn.get("unparseable_lines") == 1
          and torn.get("resolutions") == m.get("resolutions"),
          f"clean {m.get('unparseable_lines')} -> torn {torn.get('unparseable_lines')}, "
          f"resolutions {m.get('resolutions')} -> {torn.get('resolutions')}")


def cli(t: Path) -> None:
    print("\n[telemetry] CLI path, in-process, default sink = guarded CO-12")
    outs = {}
    for name, argv in {"text": ["resolve", NOMATCH_TASK, "--no-cache"],
                       "json": ["resolve", NOMATCH_TASK, "--no-cache", "--json"]}.items():
        n0 = len(GUARD_CALLS)
        so, se = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            code = R.main(argv)                    # the documented entry: stub -> agent_resolver_cli
        outs[name] = (code, so.getvalue(), se.getvalue(), GUARD_CALLS[n0:])
    code, out, err, calls = outs["text"]
    rid = calls[0][1]["resolution_id"] if len(calls) == 1 else None
    check("V-TEL-CLI-RECORDS", code == 1 and len(calls) == 1 and calls[0][0] == T.KIND and rid
          and f"resolution_id={rid}" in out and "miss=NO_MATCH" in out and not err,
          f"exit={code} signals={len(calls)} out={out.splitlines()[:1]} err={err.strip()!r}")
    code, out, err, calls = outs["json"]
    try:
        doc = json.loads(out)
    except json.JSONDecodeError:
        doc = {}
    check("V-TEL-CLI-JSON", len(calls) == 1 and doc.get("resolution_id") == calls[0][1]["resolution_id"]
          and doc.get("recorded") is True and doc.get("miss") == "NO_MATCH" and doc.get("query_fp"),
          f"json keys resolution_id/recorded/miss/query_fp = {[doc.get(k) for k in ('resolution_id', 'recorded', 'miss')]}")

    GUARD_STATE["answer"] = False
    so, se = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            code = CLI.main(["resolve", NOMATCH_TASK, "--no-cache"])
    finally:
        GUARD_STATE["answer"] = None
    check("V-TEL-CLI-NOT-RECORDED-VISIBLE", code == 1 and "TELEMETRY_NOT_RECORDED" in se.getvalue()
          and "miss=NO_MATCH" in so.getvalue(),
          f"exit={code} stderr={se.getvalue().strip()!r}")


GUARD_STATE: dict = {"answer": None, "dir": None}


def guarded_record(kind, payload, *, state_dir=None, now=None):
    """Stands in for CO-12 record_signal for the whole suite: the REAL writer, never the live dir."""
    GUARD_CALLS.append((kind, payload))
    SUITE_QFPS.add(payload.get("query_fp"))
    if GUARD_STATE["answer"] is not None:
        return GUARD_STATE["answer"]
    return REAL_RECORD(kind, payload, state_dir=state_dir or GUARD_STATE["dir"], now=now)


def main() -> int:
    live_dir = CO12._default_state_dir()
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        GUARD_STATE["dir"] = t / "guard-state"
        CO12.record_signal = guarded_record
        try:
            # Positive control: the guard does see a default-sink call, so its silence later means something.
            n0 = len(GUARD_CALLS)
            empty = t / "ctl-empty"
            empty.mkdir()
            ctl = T.resolve_and_record(NOMATCH_TASK, specs_dir=empty, use_cache=False)
            check("V-TEL-DEFAULT-SINK-CONTROL", len(GUARD_CALLS) == n0 + 1 and ctl.recorded,
                  "sink=None reaches CO-12 record_signal, looked up at call time")
            # The isolation gate keys on query_fp, so the nonce must survive the resolver's own
            # normalisation; a dropped nonce would make suite requests collide with real ones.
            check("V-TEL-NONCE-SEARCHED", all(NONCE in R._tokens(x) for x in (SFH_TASK, AUDIT_TASK, NOMATCH_TASK)),
                  f"nonce {NONCE} is a searched token of every suite task")
            contract_and_misses(t)
            cache_and_identity(t)
            failure_and_cardinality(t)
            production_reality(t)
            cli(t)
        finally:
            CO12.record_signal = REAL_RECORD
    # Live isolation: no live agent_resolution row carries a query_fp this suite produced. Other
    # producers write that file concurrently, so its size or hash is no evidence either way.
    # Strict read: an unreadable live file is a look that failed, not an empty corpus -- it fails
    # this gate instead of reading as "nothing leaked" (pre-commit review LOW).
    SUITE_QFPS.discard(None)
    try:
        live = [s for s in CO12.load_signals(state_dir=live_dir, strict=True)
                if isinstance(s, dict) and s.get("kind") == T.KIND]
        leaked, looked = [s.get("resolution_id") for s in live if s.get("query_fp") in SUITE_QFPS], "read"
    except OSError as e:
        live, leaked, looked = [], [], f"UNREADABLE {type(e).__name__}"
    check("V-TEL-LIVE-ISOLATION", SUITE_QFPS and looked == "read" and not leaked,
          f"live corpus {looked}: {len(SUITE_QFPS)} suite query_fps, {len(live)} live agent_resolution rows, "
          f"leaked={leaked}")
    print(f"AGENT_TELEMETRY_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
