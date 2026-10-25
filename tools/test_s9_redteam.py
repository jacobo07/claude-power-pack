#!/usr/bin/env python3
"""V-S9RT-* gates: the S9 red team harness (flow-compression Phase 8, plan 08-02).

The gates assert properties of the INSTRUMENT (closed verdict set, HELD needs a fired control, read-only host, every control
fires, every attack touched its real subject). They never assert a particular claim verdict: the verdict is a finding.
Each gate has a drill: a one-line mutation of a temp copy of tools/redteam_s9.py that must turn it red. Prints S9RT_PASS=n/n.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s9-redteam-test-")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["PP_OWNER_QUEUE_STATE_DIR"] = str(Path(TMP) / "owner-queue")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT))
import redteam_s9 as REAL_RT  # noqa: E402
import flow_replay as fr  # noqa: E402

PHASE7 = ROOT / REAL_RT.PHASE7
PHASE8 = ROOT / ".planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate"
PIN = PHASE7 / "07-PIN.json"
REAL_SRC = TOOLS / "redteam_s9.py"
REAL_TEXT = REAL_SRC.read_text(encoding="utf-8")
_SEEN = "TOOLS = Path(__file__).resolve().parent"
RT = REAL_RT                      # the module the gates judge; the drills point it at a mutated copy
RESULTS: list[tuple[str, bool, str]] = []
T0 = time.time()

# the 15 Owner claims, held a second time here; V-S9RT-REGISTRY compares the two copies
OWNER_CLAIMS = {
    1: "The context hypothesis was correlation, not cause.",
    2: "Rotation increases rehydration cost more than compaction.",
    3: "Preflight merely moves waits earlier without reducing span.",
    4: "Auto-normalized ROADMAP changes semantics.",
    5: "Immutable packets become stale too quickly.",
    6: "Admission reservation causes deadlocks or resource hoarding.",
    7: "Auto-renew allows runaway cost.",
    8: "The semantic progress signal can be gamed by noisy commits or tests.",
    9: "Night readiness asks too many Owner questions.",
    10: "The terminal reconciler creates false DONE.",
    11: "Blocked work stealing violates dependency or workspace ownership.",
    12: "Historical replay is biased by missing telemetry.",
    13: "The efficiency compiler optimizes aggregate mission-hours rather than the actual critical path.",
    14: "GSD X policy leaked into GSD Core.",
}


def check(gate: str, cond, ev: str = "") -> None:
    RESULTS.append((gate, bool(cond), ev))
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


CTX = REAL_RT.Ctx(PIN)            # one Ctx for every variant, so host and transcript extraction is cached once
_RUNS: dict = {}


def run(cid: int) -> dict:
    """The claim result under the module RT, computed once per module."""
    key = (RT.__name__, cid)
    if key not in _RUNS:
        _RUNS[key] = RT.run_claims(CTX, [cid], probe=False)["claims"][cid]
    return _RUNS[key]


def sub(cid: int, name: str) -> dict:
    return next(s for s in run(cid)["subs"] if s["name"] == name)


# ------------------------------------------------------------------------------------------------ instrument gates
def gate_registry():
    same = all(RT.CLAIMS.get(i) == t for i, t in OWNER_CLAIMS.items()) and sorted(RT.CLAIMS) == list(range(1, 16))
    check("V-S9RT-REGISTRY", same, f"{len(RT.CLAIMS)} claims; texts equal to the test's own copy for ids 1-14; id 15 declared")
    declared = all(isinstance(RT.SUBATTACKS.get(i), list) and RT.SUBATTACKS[i] for i in range(1, 16))
    check("V-S9RT-SUBATTACKS-DECLARED", declared, "every claim declares its sub-attacks before they run")


def _s(name, v, plane="seeded", ctl=None, reason=None):
    return RT.result(name, v, plane, {}, control_fired=ctl, reason=reason)


def gate_closed_set():
    ok_set = tuple(RT.VERDICTS) == ("HELD", "BREACH", "UNMEASURED") and "PASS" not in RT.VERDICTS
    rejected = False
    try:
        RT.judge([_s("x", "PASS", ctl=True)])
    except ValueError:
        rejected = True
    check("V-S9RT-CLOSED-SET", ok_set and rejected, f"VERDICTS={RT.VERDICTS}; a PASS sub-result is rejected={rejected}")
    ran = run(14)
    token = [s["verdict"] for s in ran["subs"]] + [ran["verdict"]]
    check("V-S9RT-NO-PASS-TOKEN", all(v in ("HELD", "BREACH", "UNMEASURED") for v in token), f"verdicts seen {sorted(set(token))}")


def gate_judge():
    held_ctl = RT.judge([_s("a", "HELD", ctl=True)])
    held_noctl = RT.judge([_s("a", "HELD", ctl=False)])
    held_none = RT.judge([_s("a", "HELD", ctl=None)])
    check("V-S9RT-HELD-NEEDS-CONTROL",
          held_ctl["verdict"] == "HELD" and held_noctl["verdict"] == "UNMEASURED" and held_none["verdict"] == "UNMEASURED"
          and held_noctl["subs"][0]["reason"] == "control_did_not_fire",
          f"fired->{held_ctl['verdict']} not-fired->{held_noctl['verdict']} unset->{held_none['verdict']}")
    H, U, B = _s("h", "HELD", ctl=True), _s("u", "UNMEASURED", reason="r"), _s("b", "BREACH")
    orders = [RT.judge(list(p))["verdict"] for p in ([H, U, B], [B, U, H], [U, H, B], [H, U], [H, H])]
    check("V-S9RT-WORST-OF", orders == ["BREACH", "BREACH", "BREACH", "UNMEASURED", "HELD"], f"{orders}")
    bad_plane = False
    try:
        RT.judge([RT.result("x", "HELD", "mars", {}, control_fired=True)])
    except ValueError:
        bad_plane = True
    noreason = RT.judge([RT.result("x", "UNMEASURED", "seeded", {})])["subs"][0]["reason"]
    ran_all = [s for cid in CLAIMS_RUN for s in run(cid)["subs"]]
    planes_ok = all(s["plane"] in RT.PLANES for s in ran_all)
    unm_ok = all(s["reason"] for s in ran_all if s["verdict"] == "UNMEASURED")
    check("V-S9RT-PLANE-NAMED", bad_plane and bool(noreason) and planes_ok and unm_ok,
          f"unknown plane refused={bad_plane}; reasonless UNMEASURED gets '{noreason}'; {len(ran_all)} real sub-results carry a plane")
    ne = RT.judge([_s("host-evidence", "UNMEASURED", "GEX44-host-readonly", reason="r"), _s("crafted-receipts", "HELD", ctl=True)])
    nb = RT.judge([_s("host-evidence", "BREACH", "GEX44-host-readonly"), _s("crafted-receipts", "HELD", ctl=True)])
    check("V-S9RT-NONESSENTIAL", ne["verdict"] == "HELD" and nb["verdict"] == "BREACH" and "host-evidence" in RT.NON_ESSENTIAL,
          f"non-essential UNMEASURED does not drag ({ne['verdict']}); a non-essential BREACH still counts ({nb['verdict']})")


def gate_readonly():
    pn = CTX.pin
    ledger = Path(pn["ledger"])
    before = hashlib.sha256(ledger.read_bytes()[:pn["bytes"]]).hexdigest()
    with RT.WriteProbe(RT.host_roots(pn)) as wp:
        RT.run_claims(CTX, [14, 10], probe=False)
    after = hashlib.sha256(ledger.read_bytes()[:pn["bytes"]]).hexdigest()
    check("V-S9RT-READONLY", not wp.writes and wp.opens > 0 and before == after == pn["sha256"],
          f"{wp.opens} opens observed, {len(wp.writes)} host write opens; pinned prefix sha256 {before[:12]} unchanged")
    fake = Path(TMP) / "fakehost" / "ledger.jsonl"
    fake.parent.mkdir(parents=True, exist_ok=True)
    with RT.WriteProbe([fake.parent]) as wp2:
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.makedirs(fake.parent / "sub", exist_ok=True)
    check("V-S9RT-READONLY-PROBE-FIRES", any(w.startswith("open(") for w in wp2.writes) and any("mkdir" in w or "makedirs" in w for w in wp2.writes),
          f"probe recorded {wp2.writes}")
    # a copy of the pinned ledger is byte-identical after a full-harness path that reads it
    copy = Path(TMP) / "ledger-copy.jsonl"
    copy.write_bytes(ledger.read_bytes()[:pn["bytes"]])
    h1 = sha(copy)
    with RT.WriteProbe([copy]) as wp3:
        fr.read_prefix({**pn, "ledger": str(copy)})
    check("V-S9RT-READONLY-COPY-IDENTICAL", sha(copy) == h1 == pn["sha256"] and not wp3.writes,
          f"read_prefix over a temp copy: {len(wp3.writes)} writes, sha256 unchanged")


def gate_patch_restored():
    import mission_reconcile as mrc
    orig = mrc.reconcile
    with RT.attr_patch(mrc, "reconcile", lambda *a, **k: None):
        inside = mrc.reconcile is not orig
    raised = False
    try:
        with RT.attr_patch(mrc, "reconcile", lambda *a, **k: None):
            raise RuntimeError("boom")
    except RuntimeError:
        raised = True
    after_all = [run(c) for c in CLAIMS_RUN]            # every claim ran its own scopes
    import receipt_judge as rj
    check("V-S9RT-PATCH-RESTORED", inside and raised and mrc.reconcile is orig and rj.is_done is REAL_ORIG["is_done"]
          and mrc.reconcile is REAL_ORIG["reconcile"] and len(after_all) == len(CLAIMS_RUN),
          "attribute scopes restore the original objects after normal and raised exits and after every attack")


def gate_c14():
    c = run(14)
    bd, hc = sub(14, "branch-diff"), sub(14, "host-core")
    e1, e2 = bd["evidence"], hc["evidence"]
    ctl = (bd["verdict"] != "HELD" or bd["control_fired"] is True) and e1["control_diff_flagged"] and e1["control_mutate_classified"] >= 1 \
        and (hc["verdict"] != "HELD" or hc["control_fired"] is True) and e2["control_injected_found"] is True
    snippet = "import subprocess\nGSD_TOOLS='x'\ndef f():\n    subprocess.run(['node', GSD_TOOLS, 'config-set', 'k', 'v'])\n"
    ctl = ctl and any(c["class"] == "mutate" for c in RT.classify_gsd_tools_calls(snippet))
    check("V-S9RT-C14-CONTROLS", ctl, f"diff control flagged {e1['control_diff_flagged']}, mutate classified {e1['control_mutate_classified']}, "
          f"injected switch found={e2['control_injected_found']}")
    check("V-S9RT-C14-SUBJECT", e1["changed_files_in_range"] > 0 and e2["core_files_read"] > 0 and e2["needles"] > 0,
          f"{e1['changed_files_in_range']} branch files diffed, {e2['core_files_read']} core files swept for {e2['needles']} names; verdict {c['verdict']}")


def gate_c10():
    c = run(10)
    cr = sub(10, "crafted-receipts")
    e = cr["evidence"]
    ctl = bool(e["mutant_recovered_done_cases"]) and e["negative_control_real_values"] == "RECOVERED_DONE" \
        and (cr["verdict"] != "HELD" or cr["control_fired"] is True)
    check("V-S9RT-C10-CONTROLS", ctl, f"mutant terminal-without-proof -> RECOVERED_DONE on {e['mutant_recovered_done_cases']}; "
          f"real matching values -> {e['negative_control_real_values']}")
    six = ["measured_key", "divergent_values", "other_mission_receipt", "epoch_mismatch", "not_done", "missing"]
    check("V-S9RT-C10-CASES", sorted(e["cases"]) == sorted(six) and e["reconcile_calls"] == 15,
          f"{len(e['cases'])} cases through the real reconcile; call-count probe {e['reconcile_calls']} (6 base + 6 mutant + 1 negative + 2 forced-status)")
    check("V-S9RT-C10-SUBJECT", sub(10, "host-evidence")["verdict"] == "UNMEASURED" and c["verdict"] in RT.VERDICTS,
          "host-evidence is reported apart as UNMEASURED(no host receipts), never counted as a pass")


def gate_c7():
    c = run(7)
    s = sub(7, "renew-loop")
    e = s["evidence"]
    ctl = e["control_expand_authority_over_cap_calls"] > 0 and e["control_lease_cap_removed_renewals"] > 20 \
        and e["control_seq_ignored_grants"] > 1 and (s["verdict"] != "HELD" or s["control_fired"] is True)
    check("V-S9RT-C7-CONTROLS", ctl, f"expand-authority: {e['control_expand_authority_over_cap_calls']} calls past the cap without a trip; "
          f"lease cap removed: {e['control_lease_cap_removed_renewals']} renewals; seq ignored: {e['control_seq_ignored_grants']} grants")
    b = e["base"]
    check("V-S9RT-C7-SUBJECT", b["renewals"] == 20 and b["trips"] == 1 and e["topup"]["grants_for_one_hold"] == 1
          and e["authority_lapsed_at_call_10"]["trips"] == 1, f"real judge: {b['renewals']} renewals then trip at call {b['tripped_at']}; "
          f"one grant per hold; lapse trips at call {e['authority_lapsed_at_call_10']['tripped_at']}; verdict {c['verdict']}")


def gate_c8():
    c = run(8)
    s = sub(8, "noise-cases")
    e = s["evidence"]
    cases = e["cases"]
    ctl = e["control_count_mode_state_md_only_moved"] is True and not cases["state_md_only"]["moved"] \
        and e["real_code_change"]["moved"] and e["real_code_change"]["renewal_granted"] \
        and s["control_fired"] is True and s["negative_control_quiet"] is True
    check("V-S9RT-C8-CONTROLS", ctl, f"count mode moves the STATE.md-only fingerprint ({e['control_count_mode_state_md_only_moved']}); "
          f"a real code change moves it and renews ({e['real_code_change']['renewal_granted']})")
    six = ["empty_commit", "amend_identical_tree", "state_md_only", "resumption_file_md_only", "resumption_md_only",
           "tracked_junk_file", "untracked_test_log", "gitignored_dir_file", "mtime_only"]
    check("V-S9RT-C8-SUBJECT", sorted(cases) == sorted(six) and not e["unmeasured_cases"]
          and (c["verdict"] == "BREACH") == bool(e["gamed_cases"]) and (not e["gamed_cases"] or c["verdict"] == "BREACH"),
          f"{len(cases)} noise cases through the real progress_fingerprint and judge; gamed={e['gamed_cases']}; verdict {c['verdict']}")


def gate_c4():
    c = run(4)
    sw, pn = sub(4, "writer-sweep"), sub(4, "packet-normaliser")
    ctl = sw["evidence"]["control_injected_found_and_reachable"] is True and sw["control_fired"] is True \
        and pn["evidence"]["control_whitespace_stripping"]["semantic_changes_merged"] and pn["evidence"]["control_whitespace_stripping"]["random_collision_count"] > 0 \
        and pn["control_fired"] is True and not pn["evidence"]["allowed_equivalences_split"]
    check("V-S9RT-C4-CONTROLS", ctl, f"injected reachable ROADMAP writer found={sw['evidence']['control_injected_found_and_reachable']}; "
          f"whitespace-stripping normaliser merges {pn['evidence']['control_whitespace_stripping']['semantic_changes_merged']}")
    check("V-S9RT-C4-SUBJECT", sw["evidence"]["functions_examined_gt_1000"] is True and sw["evidence"]["files_swept_gt_100"] is True
          and pn["evidence"]["inputs"] >= 200 and len(sw["evidence"]["roadmap_write_sites"]) >= 1,
          f"functions>1000 {sw['evidence']['functions_examined_gt_1000']} files>100 {sw['evidence']['files_swept_gt_100']}, {len(sw['evidence']['roadmap_write_sites'])} ROADMAP "
          f"writers ({sw['evidence']['reachable_count']} reachable); {pn['evidence']['inputs']} byte inputs; verdict {c['verdict']}")


def gate_c9():
    c = run(9)
    ds, pf = sub(9, "decisions-sweep"), sub(9, "production-frequency")
    e = ds["evidence"]
    ctl = e["control_filters_off"]["spurious_positive"] is True and e["seeded_ask"]["items"] >= 1 and e["seeded_ask"]["spurious"] == 0 \
        and ds["control_fired"] is True and ds["negative_control_quiet"] is True
    check("V-S9RT-C9-CONTROLS", ctl, f"filters off: spurious items present={e['control_filters_off']['spurious_positive']}; seeded ask emitted {e['seeded_ask']['items']} Owner-class item(s)")
    check("V-S9RT-C9-SUBJECT", e["real"]["workstreams"] >= 5 and e["real"]["sources_read_ge_5"] is True and pf["verdict"] == "UNMEASURED"
          and "owner_decisions_batch" in json.dumps(pf["evidence"]) and c["verdict"] in RT.VERDICTS,
          f"{e['real']['workstreams']} workstreams, sources>=5 {e['real']['sources_read_ge_5']}; real spurious {e['real']['spurious']} dup {e['real']['duplicates']}; "
          f"production frequency {pf['verdict']} (non-essential, reported apart)")


def gate_c11():
    c = run(11)
    ns, pr = sub(11, "no-stealing-code"), sub(11, "predicate")
    e, p = ns["evidence"], pr["evidence"]
    ctl = e["control_injected_consumer_found"] is True and p["seeded_qualifying"] is True and p["independent_work_true_without_action"] is False \
        and p["action_without_independent_work_true"] is False and ns["control_fired"] is True and pr["control_fired"] is True
    check("V-S9RT-C11-CONTROLS", ctl, f"injected launch-on-independent_work consumer found={e['control_injected_consumer_found']}; predicate true on the seeded "
          f"qualifying ledger={p['seeded_qualifying']}, false on both negative seeds")
    check("V-S9RT-C11-SUBJECT", e["files_swept"] > 100 and len({r["file"] for r in e["readers_of_independent_work"]}) >= 3
          and p["pinned_prefix"]["blocked_rows"] == 55 and p["pinned_prefix"]["blocked_with_independent_work_true"] == 0
          and p["pinned_prefix"]["value"] is False and p["pin_rows"] == 6339,
          f"{e['files_swept']} files swept, {len(e['readers_of_independent_work'])} readers, {len(e['consumers'])} consumers; pin {p['pin_rows']} rows, "
          f"{p['pinned_prefix']['blocked_rows']} mission_blocked, {p['pinned_prefix']['blocked_with_independent_work_true']} independent_work=true; verdict {c['verdict']}")


def gate_c6():
    c = run(6)
    sp, ho, de = sub(6, "primitive-sweep"), sub(6, "hoarding"), sub(6, "deadlock")
    ctl = sp["evidence"]["control_injected_wait_and_lock_found"] is True and ho["evidence"]["seeded_open_claim_blocks_other_under_mutant"] == 1 \
        and de["evidence"]["mutant_wait_for_cycle_found"] is True and sp["control_fired"] is True and ho["control_fired"] is True and de["control_fired"] is True
    check("V-S9RT-C6-CONTROLS", ctl, "injected wait-on-mission wake and flock found; an open claim blocks another mission under the occupied-capacity mutant; "
          "the mutant wait-for graph has a cycle")
    e, h, d = sp["evidence"], ho["evidence"], de["evidence"]
    check("V-S9RT-C6-SUBJECT", e["admission_runs_before_the_claim"] is True and e["wake_kinds_on_the_path"] == ["env_ready"] and not e["lock_like_primitives_in_admission_modules"]
          and h["claims"] == 160 and h["claims_never_followed_up"] == 0 and h["claims_followed_up_late"] == 0 and h["pin_rows"] == 6339
          and d["held_under_preflight_not_ready"] == 3 and d["held_after_ready_in_reverse_order"] == 0 and d["wait_for_cycle"] is None
          and d["resource_refusal_low_memory"] == "REFUSE_LOW_MEMORY" and d["resource_refusal_after_delta"] is None,
          f"{h['claims']} claims, {h['claims_followed_up_late']} late, {h['claims_never_followed_up']} never followed up; "
          f"{h['refusal_rows_inside_another_missions_open_claim']} of {h['refusal_rows']} refusal rows sit inside another mission's open claim, "
          f"refusal code reads other missions={h['refusal_code_reads_other_missions']}; 3 held then {d['held_after_ready_in_reverse_order']} after the delta; verdict {c['verdict']}")


def gate_c13():
    c = run(13)
    sj, ob, se = sub(13, "subject"), sub(13, "objective-sweep"), sub(13, "seeded-serialization")
    ctl = ob["evidence"]["control_injected_decider_found"] is True and se["evidence"]["summed_keyed_label_calls_serialized_a_gain"] is True \
        and se["evidence"]["critical_path_keyed_label_calls_it_a_gain"] is False and sj["control_fired"] is True \
        and ob["control_fired"] is True and se["control_fired"] is True
    check("V-S9RT-C13-CONTROLS", ctl, "injected summed-hours decider found; a summed-hours labeller calls the serialized arm a gain while the critical path says it is not")
    e, v = ob["evidence"], se["evidence"]
    check("V-S9RT-C13-SUBJECT", sj["evidence"]["files_swept"] > 100 and len(e["readers"]) >= 2 and v["parallel"]["summed_mission_hours"] == 6.0
          and v["serialized"]["summed_mission_hours"] == 4.0 and v["serialized"]["critical_path_wall_clock_hours"] == 4.0,
          f"{sj['evidence']['files_swept']} files swept, {len(e['readers'])} readers, {len(e['deciders'])} deciders; parallel {v['parallel']} vs serialized {v['serialized']}; verdict {c['verdict']}")


def gate_c15():
    c = run(15)
    cs = sub(15, "claim-text-search")
    check("V-S9RT-C15-CONTROLS", cs["control_fired"] is True and cs["negative_control_quiet"] is True,
          "a planted 15-item numbered list is found by the same search that finds none in the real files")
    e = cs["evidence"]
    check("V-S9RT-C15-SUBJECT", len(e["files_searched"]) == 5 and e["claim_text_found"] is False and not e["lists_of_15_or_more"]
          and c["verdict"] == "UNMEASURED" and RT.C15_REASON in (c["reason"] or ""),
          f"{len(e['files_searched'])} files searched, claim text found={e['claim_text_found']}, verdict {c['verdict']}: {c['reason']}")


def gate_c12():
    c = run(12)
    ms = sub(12, "missing-telemetry")
    e = ms["evidence"]
    check("V-S9RT-C12-CONTROLS", ms["control_fired"] is True and e["seeded_complete"]["bias_h"] == 0.0 and e["seeded_terminals_removed"]["bias_h"] == 9.0,
          f"a fully telemetered seeded ledger has bias {e['seeded_complete']['bias_h']} h; the same ledger without terminal rows has {e['seeded_terminals_removed']['bias_h']} h")
    i = e["independent"]
    check("V-S9RT-C12-SUBJECT", c["verdict"] == "BREACH" and i["open"] >= 50 and i["bias_h"] > 20000 and e["independent_matches_flow_replay"] is True
          and e["unmeasured_kept_apart"]["unmeasured_apart"] == 17 and e["unmeasured_kept_apart"]["measured_total"] == 249,
          f"headline {i['headline_h']} h vs bounded {i['bounded_h']} h over {i['open']} open missions; unmeasured kept apart {e['unmeasured_kept_apart']}; verdict {c['verdict']}")


def gate_c3():
    c = run(3)
    sp = sub(3, "span-effect")
    e = sp["evidence"]
    check("V-S9RT-C3-CONTROLS", sp["control_fired"] is True and e["seeded_fixed_time_resolution"]["span_delta_s"] == 0
          and e["seeded_notify_resolution"]["span_delta_s"] == -900.0,
          "a fixed-time resolution leaves the span unchanged and a notify-delay resolution shortens it by the whole earlier-stop interval")
    check("V-S9RT-C3-SUBJECT", c["verdict"] == "UNMEASURED" and e["incident"]["mission_id"] == "m-9d00610493fc" and e["challenger_stops_earlier_by_s"] == 1127.0
          and e["resolution_exogenous"] is True and e["unblock_before_end"] is False and e["avoidable_idle_h_before_after"][0] == e["avoidable_idle_h_before_after"][1],
          f"one S2 incident, stop {e['challenger_stops_earlier_by_s']} s earlier, mission ended '{e['mission_end']['reason']}'; verdict {c['verdict']}")


def gate_c5():
    c = run(5)
    ps = sub(5, "packet-staleness")
    e = ps["evidence"]
    check("V-S9RT-C5-CONTROLS", ps["control_fired"] is True and e["seeded_fast"]["share"] == 1.0 and e["seeded_slow"]["share"] == 0.0 and e["seeded_untimed"]["share"] is None,
          "a fast-superseded set reads 1.0, a slow set 0.0, and untimed packets are unmeasured rather than zero")
    r = e["real"]
    check("V-S9RT-C5-SUBJECT", r["admitted"] == 17 and r["timed"] == 16 and r["untimed"] == 1 and r["superseded_fast"] == 2 and e["supersessions_in_pin"] == 7
          and e["packet_refusal_rows"] == 0 and c["verdict"] == "UNMEASURED",
          f"{r['superseded_fast']} of {r['timed']} timed packets superseded within 24 h ({r['untimed']} untimed), share {r['share']}; verdict {c['verdict']}")


def gate_c1():
    c = run(1)
    cw, ce = sub(1, "causal-wording"), sub(1, "causal-effect")
    check("V-S9RT-C1-CONTROLS", cw["control_fired"] is True and ce["control_fired"] is True and len(cw["evidence"]["control_qualifiers_removed_unqualified"]) >= 1
          and ce["evidence"]["seeded_confounded_arms"]["stratified_diff_min"] == 0.0,
          "deleting the confound qualifiers makes the comparison read as unqualified; a confounded sample's gap vanishes once stratified")
    check("V-S9RT-C1-SUBJECT", len(cw["evidence"]["files_scanned"]) == 6 and len(cw["evidence"]["comparative_effect_paragraphs"]) >= 1
          and not cw["evidence"]["unqualified"] and cw["verdict"] == "HELD" and c["verdict"] == "UNMEASURED",
          f"{len(cw['evidence']['comparative_effect_paragraphs'])} effect comparison(s), {len(cw['evidence']['unqualified'])} unqualified; wording {cw['verdict']}, effect {ce['verdict']}, claim {c['verdict']}")


def gate_c2():
    c = run(2)
    rc = sub(2, "rehydration-cost")
    e = rc["evidence"]
    check("V-S9RT-C2-CONTROLS", rc["control_fired"] is True and e["seeded"]["rotation_dearer"]["verdict"] == "BREACH" and e["seeded"]["rotation_cheaper"]["verdict"] == "HELD"
          and e["seeded"]["between"]["verdict"] == "UNMEASURED", "a seeded dearer rotation is proven, a cheaper one held, an in-between one unmeasured")
    check("V-S9RT-C2-SUBJECT", len(e["rotation_first_call_ctx"]) >= 3 and e["ledger_compactions_in_closed_epochs"] >= 1 and c["verdict"] in ("UNMEASURED", "HELD", "BREACH")
          and all(v > 0 for v in e["rotation_first_call_ctx"]),
          f"{len(e['rotation_first_call_ctx'])} rotation epochs, {len(e['compaction_post_ctx_lower_bound'])} observable compactions of {e['ledger_compactions_in_closed_epochs']} ledgered; verdict {c['verdict']}")


_FRESH: dict = {}


def _fresh_report(k=0) -> dict:
    """The k-th fresh whole run under the module RT with its own context; generated_at is pinned so runs can be compared."""
    if (RT.__name__, k) not in _FRESH:
        _FRESH[(RT.__name__, k)] = _fresh_report_once()
    return _FRESH[(RT.__name__, k)]


def _fresh_report_once() -> dict:
    ctx = RT.Ctx(PIN)
    ran = RT.run_claims(ctx, sorted(RT.CLAIMS), probe=False)
    rel = lambda p: str(p.relative_to(ROOT))
    cmd = RT.command_tag(sorted(RT.CLAIMS), rel(PIN), rel(PHASE8 / "08-REDTEAM.json"), rel(PHASE8 / "08-REDTEAM.md"))
    return json.loads(json.dumps(RT.build_report(ctx, ran, cmd, generated_at="T"), sort_keys=True, default=str))


def gate_allattacked():
    # every claim is attacked: no sub-result is a placeholder
    placeholder = [(c, s["name"]) for c in sorted(RT.CLAIMS) for s in run(c)["subs"] if s.get("reason") == "no_attack_implemented"]
    check("V-S9RT-ALL-ATTACKED", sorted(RT.ATTACKS) == sorted(RT.CLAIMS) and not placeholder and sorted(CLAIMS_RUN) == sorted(RT.CLAIMS),
          f"{len(RT.ATTACKS)} of {len(RT.CLAIMS)} claims have an attack; placeholders {placeholder}")


def gate_reuse():
    import subprocess
    import types
    # the reused 07 evidence is hashed against the committed blob and the pin before use
    rel = RT.PHASE7 + "/07-REPLAY.json"
    with RT.temp_root() as td:
        tgt = td / rel
        tgt.parent.mkdir(parents=True)
        tgt.write_bytes((ROOT / rel).read_bytes())
        for a in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false",
                                                    "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "x"]):
            subprocess.run(["git", *a], cwd=str(td), check=True, capture_output=True, timeout=60)
        pin_sha = json.loads(tgt.read_bytes())["pin"]["data"]["sha256"]
        fake = lambda sha: types.SimpleNamespace(pin={"sha256": sha}, cached=lambda k, fn: fn())

        def attempt(sha):
            try:
                return bool(RT.load_replay(fake(sha))["raw"])
            except fr.Inconclusive:
                return False
        with RT.attr_patch(RT, "ROOT", td):
            loads = attempt(pin_sha)
            wrong_pin = attempt("0" * 64)
            tgt.write_bytes(tgt.read_bytes() + b" ")
            one_byte = attempt(pin_sha)
    check("V-S9RT-REUSE-HASHED", loads and not wrong_pin and not one_byte,
          f"matching blob and pin load={loads}; a different pin load={wrong_pin}; one extra byte in the working copy load={one_byte}")


def gate_pin():
    # a pin that does not verify is Inconclusive, never a result
    with RT.temp_root() as td:
        pj = json.loads(PIN.read_text())
        pj["sha256"] = ("0" if pj["sha256"][0] != "0" else "1") + pj["sha256"][1:]
        (td / "tampered.json").write_text(json.dumps(pj))
        tampered = False
        try:
            RT.Ctx(td / "tampered.json")
        except fr.Inconclusive:
            tampered = True
    check("V-S9RT-PIN", tampered and len(CTX.rows) == 6339, f"a pin with one hex digit changed is Inconclusive={tampered}; the real pin loads {len(CTX.rows)} rows")


def gate_det():
    a, b = _fresh_report(0), _fresh_report(1)
    check("V-S9RT-DETERMINISTIC", a == b and len(a["claims"]) == 15, f"two whole runs equal={a == b} over {len(a['claims'])} claims (generated_at pinned)")


def gate_repro():
    a = _fresh_report(0)
    committed_p = PHASE8 / "08-REDTEAM.json"
    if committed_p.is_file():
        committed = json.loads(committed_p.read_text())
        committed["generated_at"] = "T"
        same = committed == a
        diff = [c["id"] for c, d in zip(committed.get("claims", []), a["claims"]) if c != d]
    else:
        same, diff = False, "08-REDTEAM.json absent"
    check("V-S9RT-REPORT-REPRODUCES", same, f"the committed 08-REDTEAM.json equals a fresh run minus generated_at: {same}; claims differing {diff}")


EXTRA_GROUPS: dict = {}
CLAIMS_RUN = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
REAL_ORIG: dict = {}
import mission_reconcile as _mrc  # noqa: E402
import receipt_judge as _rj  # noqa: E402
import mission_spend as _ms  # noqa: E402
import gsd_mission as _gm  # noqa: E402
REAL_ORIG.update(reconcile=_mrc.reconcile, is_done=_rj.is_done)

GROUPS = {"registry": gate_registry, "closed": gate_closed_set, "judge": gate_judge, "readonly": gate_readonly,
          "patch": gate_patch_restored, "c14": gate_c14, "c10": gate_c10, "c7": gate_c7, "c8": gate_c8, "c4": gate_c4, "c9": gate_c9, "c11": gate_c11, "c13": gate_c13, "c6": gate_c6, "c12": gate_c12, "c15": gate_c15, "c3": gate_c3, "c5": gate_c5, "c1": gate_c1, "c2": gate_c2, "allatt": gate_allattacked, "reuse": gate_reuse, "pin": gate_pin, "det": gate_det, "repro": gate_repro}
GROUP_ORDER = ["registry", "closed", "judge", "readonly", "patch", "c14", "c10", "c7", "c8", "c4", "c9", "c11", "c13", "c6", "c12", "c15", "c3", "c5", "c1", "c2", "allatt", "reuse", "pin", "det", "repro"]

# ------------------------------------------------------------------------------------------------ mutation machinery
MUTATIONS: dict[str, list[tuple[str, str]]] = {
    "M-C13-CTL-OFF": [('found = any(d["file"] == "modules/zz_inject.py" for d in sweep_hours_deciders(inj)["deciders"])', 'found = False')],
    "M-C13-READERS-NONE": [('(isinstance(n, ast.Constant) and n.value == "summed_mission_hours") or\n                        (isinstance(n, ast.Name)', '(isinstance(n, ast.Constant) and n.value == "zz_never") or\n                        (isinstance(n, ast.Name)')],
    "M-C6-CTL-OFF": [('found = any(w["kind"] == "mission" for w in csw["wakes"]) and', 'found = False and')],
    "M-C6-CYCLE-BLIND": [("            c = visit(m, [])", "            c = None")],
    "M-C6-CLAIMS-NONE": [('            if r.get("event") != "launch_claimed":\n                continue\n            claims += 1', '            if True:\n                continue\n            claims += 1')],
    "M-C6-DELTA-NOT-RELEASED": [('        state["v"] = "READY"', '        state["v"] = "NOT_READY"')],
    "M-C15-CTL-OFF": [('ctl = any(f["file"] == "planted.md" for f in c15_lists(planted))', 'ctl = False')],
    "M-C15-LIST-BLIND": [("        if best >= minimum:", "        if best >= 99:")],
    "M-C15-FILES-NONE": [("for rel in _C15_FILES if (ROOT / rel).is_file()}", "for rel in _C15_FILES if False}")],
    "M-C12-TERMINAL-BLIND": [('            m["terminal"] = True', '            m["terminal"] = False')],
    "M-C12-OPEN-AT-LAST": [('(m["last"] if m["terminal"] else pin_end) - m["first"]', 'm["last"] - m["first"]')],
    "M-C12-TOL-HUGE": [('real["bias_ratio"] > tol', 'real["bias_ratio"] > 1e9')],
    "M-C3-CTL-OFF": [('fired = seeded_fixed["span_delta_s"] == 0 and seeded_notify["span_delta_s"] == -900.0', 'fired = False')],
    "M-C3-EXO-BLIND": [('exo = last.get("event") == "mission_halted" and', 'exo = False and')],
    "M-C5-CTL-OFF": [("    fired = fast[\"share\"] >= C5_SHARE > slow[\"share\"] and untimed[\"share\"] is None", "    fired = False")],
    "M-C5-UNTIMED-ZERO": [('timed = [i for i in items if i.get("set_at") is not None]', 'timed = [dict(i, set_at=i.get("set_at") or 0.0) for i in items]')],
    "M-C5-SUPERSEDED-NONE": [('sup = {r["mission_id"]: _c12_ts(r.get("ts")) for r in ctx.rows if r.get("event") == "mission_superseded"}', 'sup = {}')],
    "M-C1-CTL-OFF": [('fired = bool(hits) and all(h["qualified"] for h in hits) and any(not h["qualified"] for h in ctl_hits)', 'fired = False')],
    "M-C1-QUALIFIER-BLIND": [('window = " ".join(paras[max(0, i - 1):i + 2])\n                hits.append', 'window = ""\n                hits.append')],
    "M-C1-STRATA-OFF": [("    diffs = [_med(arm(\"rotation\", s)) - _med(arm(\"compaction\", s)) for s in sorted({st for (_, st, _) in samples})", "    diffs = [_med(arm(\"rotation\")) - _med(arm(\"compaction\")) for s in sorted({st for (_, st, _) in samples})")],
    "M-C2-CTL-OFF": [("    fired = (ctl_breach[\"verdict\"], ctl_held[\"verdict\"], ctl_mid[\"verdict\"]) == (BREACH, HELD, UNMEASURED)", "    fired = False")],
    "M-C2-ROTATION-NONE": [('        if e.get("start_cause") == "CONTEXT_ROTATION" and calls:', '        if False and calls:')],
    "M-REUSE-UNHASHED": [('if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != sha256(p):', 'if False:')],
    "M-PIN-UNVERIFIED": [("        self.rows, self.torn = fr.read_prefix(self.pin)          # Inconclusive when the pin does not verify", "        self.rows, self.torn = [], 0")],
    "M-ATTACK-DROPPED": [("ATTACKS = {1: attack_1, ", "ATTACKS = {")],
    "M-NONDETERMINISTIC": [('{"files_scanned": sorted(files), "comparative_effect_paragraphs": hits,', '{"files_scanned": sorted(files), "t": time.time(), "comparative_effect_paragraphs": hits,')],
    "M-REPORT-DRIFT": [('ev = {"mission": C2_MISSION, "rotation_first_call_ctx"', 'ev = {"mission": C2_MISSION, "drift": 1, "rotation_first_call_ctx"')],
    "M-REGISTRY-TEXT": [('1: "The context hypothesis was correlation, not cause."', '1: "The context hypothesis was causal."')],
    "M-SUBATTACK-EMPTY": [('    4: ["writer-sweep", "packet-normaliser"],', '    4: [],')],
    "M-VERDICT-SET-WIDENED": [("VERDICTS = (HELD, BREACH, UNMEASURED)", 'VERDICTS = (HELD, BREACH, UNMEASURED, "PASS")')],
    "M-VERDICT-NOT-VALIDATED": [("        if v not in VERDICTS:", "        if False:")],
    "M-HELD-WITHOUT-CONTROL": [('if v == HELD and s.get("control_fired") is not True:', "if False:")],
    "M-RANK-INVERTED": [("rank = {HELD: 0, UNMEASURED: 1, BREACH: 2}", "rank = {HELD: 0, UNMEASURED: 2, BREACH: 1}")],
    "M-PLANE-NOT-CHECKED": [("        if s.get(\"plane\") not in PLANES:", "        if False:")],
    "M-REASON-DROPPED": [('        if s["verdict"] == UNMEASURED and not s.get("reason"):', "        if False:")],
    "M-NONESSENTIAL-DECIDES": [("NON_ESSENTIAL = {\"host-evidence\", \"production-frequency\"}", "NON_ESSENTIAL = set()")],
    "M-PROBE-BLIND-WRITE": [('any(c in str(mode) for c in "wax+")', "False")],
    "M-PROBE-BLIND-MKDIR": [('for name in ("remove", "unlink", "rename", "replace", "mkdir", "makedirs", "rmdir", "truncate", "utime"):',
                             "for name in ():")],
    "M-PATCH-NOT-RESTORED": [("    finally:\n        setattr(module, name, original)", "    finally:\n        pass")],
    "M-C14-DIFF-BLIND": [(r'(^|/)gsd-core(/|$)', r'(^|/)gsd-corx(/|$)')],
    "M-C14-CORE-ABSENT": [('core = Path.home() / ".claude" / "gsd-core"', 'core = Path.home() / ".claude" / "gsd-corx"')],
    "M-C14-CLASSIFY-ALL-READ": [('out.append({"function": fn.name, "class": "mutate" if mutate else "read", "verbs": mutate})',
                                 'out.append({"function": fn.name, "class": "read", "verbs": mutate})')],
    "M-C10-MUTANT-OFF": [('fr.mutant_scope("terminal-without-proof")', 'fr.mutant_scope("never-rotate")')],
    "M-C10-NOT-COUNTED": [("        calls.append(1)\n", "        pass\n")],
    "M-C10-NEG-BLIND": [('("real_values",)', '("not_done",)')],
    "M-C10-CASE-DROPPED": [('C10_CASES = ("measured_key", "divergent_values", "other_mission_receipt", "epoch_mismatch", "not_done", "missing")',
                            'C10_CASES = ("measured_key", "divergent_values", "other_mission_receipt", "epoch_mismatch", "not_done")')],
    "M-C7-MUTANT-OFF": [('fr.mutant_scope("expand-authority")', 'fr.mutant_scope("never-rotate")')],
    "M-C7-LOOP-SHORT": [("C7_CALLS = 10_000_000_000, 100", "C7_CALLS = 10_000_000_000, 3")],
    "M-C8-CTL-OFF": [('c8_cases(gm, ms, ("state_md_only",), bookkeeping_count=True)', 'c8_cases(gm, ms, ("state_md_only",), bookkeeping_count=False)')],
    "M-C8-CASE-DROPPED": [('"tracked_junk_file", "untracked_test_log", "gitignored_dir_file", "mtime_only")\n\n\ndef _g', '"tracked_junk_file", "gitignored_dir_file", "mtime_only")\n\n\ndef _g')],
    "M-C4-CTL-OFF": [("    def stripping(data: bytes) -> bytes:\n        return data.strip()", "    def stripping(data: bytes) -> bytes:\n        return data")],
    "M-C4-ENTRIES-EMPTY": [('_C4_ENTRIES = ("arm_preflight", "arm_chain", "arm", "arm_mission", "plan_next", "supervise", "supervisor_pass")', '_C4_ENTRIES = ("zz_none",)')],
    "M-C4-FILES-FEW": [("    files = {str(p.relative_to(ROOT)): p.read_text(encoding=\"utf-8\", errors=\"replace\") for p in _tools_py()}", "    files = {str(p.relative_to(ROOT)): p.read_text(encoding=\"utf-8\", errors=\"replace\") for p in _tools_py()[:20]}")],
    "M-C9-CTL-OFF": [("ctl = c9_sweep(bc, gate, ctx.root, use_filters=False)", "ctl = c9_sweep(bc, gate, ctx.root, use_filters=True)")],
    "M-C9-SEED-DROPPED": [("OWNER DECISION NEEDED: whether to publish", "all done: whether to publish")],
    "M-C9-SWEEP-EMPTY": [('    root = Path(cwd) / ".planning" / "workstreams"\n    per', '    root = Path(cwd) / ".planning" / "zz"\n    root.mkdir(exist_ok=True) if False else None\n    per')],
    "M-C11-CTL-OFF": [("            launch_mission(r)", "            print(r)")],
    "M-C11-SEED-NOT-TRUE": [('dict(t0, event="mission_blocked", independent_work=True), dict(t0, event="unit_completed"),\n                                dict(t0, event="mission_unblocked")])', 'dict(t0, event="mission_blocked", independent_work=True), dict(t0, event="noop"),\n                                dict(t0, event="mission_unblocked")])')],
    "M-C11-PIN-FALSE-TRUE": [('if later.get("event") in _C11_ACTION_EVENTS:', 'if True:')],
    "M-C11-READERS-NONE": [('            readers.append({"file": name, "function": fn.name})', '            pass')],
    "M-C10-HOSTEVIDENCE-HELD": [('subs.append(result("host-evidence", UNMEASURED,', 'subs.append(result("host-evidence", HELD,'),
                                ('reason="no host receipts (done_proof not_applicable)",', 'control_fired=True,')],
}
MUTANT_FOR: dict[str, list[str]] = {
    "V-S9RT-REGISTRY": ["M-REGISTRY-TEXT"],
    "V-S9RT-SUBATTACKS-DECLARED": ["M-SUBATTACK-EMPTY"],
    "V-S9RT-CLOSED-SET": ["M-VERDICT-SET-WIDENED", "M-VERDICT-NOT-VALIDATED"],
    "V-S9RT-HELD-NEEDS-CONTROL": ["M-HELD-WITHOUT-CONTROL"],
    "V-S9RT-WORST-OF": ["M-RANK-INVERTED"],
    "V-S9RT-PLANE-NAMED": ["M-PLANE-NOT-CHECKED", "M-REASON-DROPPED"],
    "V-S9RT-NONESSENTIAL": ["M-NONESSENTIAL-DECIDES"],
    "V-S9RT-READONLY-PROBE-FIRES": ["M-PROBE-BLIND-WRITE", "M-PROBE-BLIND-MKDIR"],
    "V-S9RT-PATCH-RESTORED": ["M-PATCH-NOT-RESTORED"],
    "V-S9RT-C14-CONTROLS": ["M-C14-DIFF-BLIND", "M-C14-CLASSIFY-ALL-READ"],
    "V-S9RT-C14-SUBJECT": ["M-C14-CORE-ABSENT"],
    "V-S9RT-C10-CONTROLS": ["M-C10-MUTANT-OFF", "M-C10-NEG-BLIND"],
    "V-S9RT-C10-CASES": ["M-C10-NOT-COUNTED", "M-C10-CASE-DROPPED"],
    "V-S9RT-C10-SUBJECT": ["M-C10-HOSTEVIDENCE-HELD"],
    "V-S9RT-C7-CONTROLS": ["M-C7-MUTANT-OFF"],
    "V-S9RT-C7-SUBJECT": ["M-C7-LOOP-SHORT"],
    "V-S9RT-C8-CONTROLS": ["M-C8-CTL-OFF"],
    "V-S9RT-C4-CONTROLS": ["M-C4-CTL-OFF", "M-C4-ENTRIES-EMPTY"],
    "V-S9RT-C4-SUBJECT": ["M-C4-FILES-FEW"],
    "V-S9RT-C9-CONTROLS": ["M-C9-CTL-OFF", "M-C9-SEED-DROPPED"],
    "V-S9RT-C9-SUBJECT": ["M-C9-SWEEP-EMPTY"],
    "V-S9RT-C11-CONTROLS": ["M-C11-CTL-OFF", "M-C11-SEED-NOT-TRUE", "M-C11-PIN-FALSE-TRUE"],
    "V-S9RT-C11-SUBJECT": ["M-C11-READERS-NONE"],
    "V-S9RT-C6-CONTROLS": ["M-C6-CTL-OFF", "M-C6-CYCLE-BLIND"],
    "V-S9RT-C6-SUBJECT": ["M-C6-CLAIMS-NONE", "M-C6-DELTA-NOT-RELEASED"],
    "V-S9RT-C13-CONTROLS": ["M-C13-CTL-OFF"],
    "V-S9RT-C13-SUBJECT": ["M-C13-READERS-NONE"],
    "V-S9RT-C8-SUBJECT": ["M-C8-CASE-DROPPED"],
    "V-S9RT-ALL-ATTACKED": ["M-ATTACK-DROPPED"],
    "V-S9RT-REUSE-HASHED": ["M-REUSE-UNHASHED"],
    "V-S9RT-PIN": ["M-PIN-UNVERIFIED"],
    "V-S9RT-DETERMINISTIC": ["M-NONDETERMINISTIC"],
    "V-S9RT-REPORT-REPRODUCES": ["M-REPORT-DRIFT"],
    "V-S9RT-C3-CONTROLS": ["M-C3-CTL-OFF"],
    "V-S9RT-C3-SUBJECT": ["M-C3-EXO-BLIND"],
    "V-S9RT-C5-CONTROLS": ["M-C5-CTL-OFF", "M-C5-UNTIMED-ZERO"],
    "V-S9RT-C5-SUBJECT": ["M-C5-SUPERSEDED-NONE"],
    "V-S9RT-C1-CONTROLS": ["M-C1-CTL-OFF", "M-C1-STRATA-OFF"],
    "V-S9RT-C1-SUBJECT": ["M-C1-QUALIFIER-BLIND"],
    "V-S9RT-C2-CONTROLS": ["M-C2-CTL-OFF"],
    "V-S9RT-C2-SUBJECT": ["M-C2-ROTATION-NONE"],
    "V-S9RT-C15-CONTROLS": ["M-C15-CTL-OFF", "M-C15-LIST-BLIND"],
    "V-S9RT-C15-SUBJECT": ["M-C15-FILES-NONE"],
    "V-S9RT-C12-CONTROLS": ["M-C12-TERMINAL-BLIND", "M-C12-OPEN-AT-LAST"],
    "V-S9RT-C12-SUBJECT": ["M-C12-TOL-HUGE"],
}
UNMUTATED: dict[str, str] = {
    "V-S9RT-NO-PASS-TOKEN": "it reads verdicts of a real run; the closed-set widening is pinned red by V-S9RT-CLOSED-SET under M-VERDICT-SET-WIDENED",
    "V-S9RT-READONLY": "its subject is the live host prefix, which no line of the harness targets; the probe that proves it can fail is drilled by V-S9RT-READONLY-PROBE-FIRES",
    "V-S9RT-READONLY-COPY-IDENTICAL": "its subject is a temp copy no harness line targets; the in-gate probe on the copy shows a write would be recorded",
}

VARIANTS: list = []
VAR_DIR = Path(TMP) / "variants"


def make_variant(mid: str, subs: list):
    text = REAL_TEXT.replace(_SEEN, f"TOOLS = Path({str(TOOLS)!r})", 1)
    for old, new in subs:
        if old not in text:
            raise ValueError(f"mutation {mid}: pattern not found: {old[:70]!r}")
        text = text.replace(old, new)
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    n = len(VARIANTS)
    path = VAR_DIR / f"redteam_s9_v{n}.py"
    path.write_text(text, encoding="utf-8")
    name = f"redteam_s9_v{n}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    VARIANTS.append(mod)
    return mod


@contextlib.contextmanager
def using(mod):
    """Point the gates at `mod`; afterwards put back the module and the patched attributes of the real seams."""
    global RT
    prev, env = RT, dict(os.environ)
    saved = {(m, a): getattr(m, a) for m, a in ((_mrc, "reconcile"), (_rj, "is_done"), (_ms, "LEASE_MAX_RENEWALS"), (_ms, "judge"), (_gm, "_normalise_packet"), (_gm, "progress_fingerprint"))}
    RT = mod
    try:
        yield
    finally:
        RT = prev
        os.environ.clear()
        os.environ.update(env)
        for (m, a), v in saved.items():
            setattr(m, a, v)


def run_groups(names) -> dict:
    """Run gate groups against the module RT names; {gate: ok}. A crashing group reports the gates it never reached absent."""
    saved = RESULTS[:]
    RESULTS.clear()
    crashed = {}
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        for n in sorted(set(names), key=GROUP_ORDER.index):
            try:
                GROUPS[n]()
            except Exception as exc:  # noqa: BLE001 -- a crashing gate is a red gate
                crashed[n] = f"{type(exc).__name__}: {exc}"[:160]
    out = {g: ok for g, ok, _ in RESULTS}
    RESULTS[:] = saved
    out["__crashed__"] = crashed
    return out


def drills(base: dict, group_of: dict) -> None:
    mids = sorted({m for ms in MUTANT_FOR.values() for m in ms})
    for mid in mids:
        expected = sorted(g for g, ms in MUTANT_FOR.items() if mid in ms)
        groups = sorted({group_of[g] for g in expected if g in group_of}, key=GROUP_ORDER.index)
        try:
            with using(make_variant(mid, MUTATIONS[mid])):
                got = run_groups(groups)
        except Exception as exc:  # noqa: BLE001 -- a mutation that cannot be applied is a failed drill
            check(f"V-S9RT-DRILL-{mid}", False, f"mutation not applicable: {type(exc).__name__}: {exc}")
            continue
        still_green = [g for g in expected if got.get(g) is True]
        never_green = [g for g in expected if base.get(g) is not True]
        check(f"V-S9RT-DRILL-{mid}", bool(expected) and not still_green and not never_green,
              f"expected_red={len(expected)} still_green={still_green} baseline_not_green={never_green} crashed={list(got['__crashed__'])}")


def drill_control(base: dict, group_of: dict) -> None:
    """With every mutation replaced by a no-op every mapped gate stays green, which each drill reads as a failed drill."""
    expected = sorted(MUTANT_FOR)
    groups = sorted({group_of[g] for g in expected if g in group_of}, key=GROUP_ORDER.index)
    with using(make_variant("noop", [])):
        got = run_groups(groups)
    still_green = [g for g in expected if got.get(g) is True]
    mids = sorted({m for ms in MUTANT_FOR.values() for m in ms})
    would_fail = [m for m in mids if not [g for g, ms in MUTANT_FOR.items() if m in ms and got.get(g) is not True]]
    check("V-S9RT-DRILL-CONTROL-NOOP-FIRES", bool(expected) and len(still_green) == len(expected) and len(would_fail) == len(mids),
          f"no-op substitution left {len(still_green)}/{len(expected)} mapped gates green: all {len(would_fail)}/{len(mids)} drills would read it as a failure")


def map_gate(names: list) -> None:
    gate_names = [n for n in names if not n.startswith("V-S9RT-DRILL-") and n != "V-S9RT-MUTANT-MAP"]
    unmapped = [n for n in gate_names if n not in MUTANT_FOR and n not in UNMUTATED]
    stale = [g for g in MUTANT_FOR if g not in gate_names]
    undefined = sorted({m for ms in MUTANT_FOR.values() for m in ms if m not in MUTATIONS})
    unused = sorted(m for m in MUTATIONS if not any(m in ms for ms in MUTANT_FOR.values()))
    check("V-S9RT-MUTANT-MAP", not unmapped and not stale and not undefined and not unused,
          f"unmapped={unmapped} stale={stale} undefined={undefined} unused={unused} gates={len(gate_names)} unmutated={sorted(UNMUTATED)}")


def main() -> int:
    real_before = sha(REAL_SRC)
    group_of = {}
    for name in GROUP_ORDER:
        before = len(RESULTS)
        GROUPS[name]()
        for n, _, _ in RESULTS[before:]:
            group_of[n] = name
    base = {n: ok for n, ok, _ in RESULTS}
    drills(base, group_of)
    drill_control(base, group_of)
    check("V-S9RT-DRILL-REAL-FILE-UNTOUCHED", sha(REAL_SRC) == real_before and REAL_TEXT == REAL_SRC.read_text(encoding="utf-8"),
          f"tools/redteam_s9.py sha256 {real_before[:12]} identical before and after {len(VARIANTS)} mutated copies")
    map_gate(list(group_of))
    n = len(RESULTS)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, ev in RESULTS:
        if not ok:
            print(f"FAIL {name} {ev}")
    wall = time.time() - T0
    print(f"S9RT_PASS={p}/{n}  threshold={n}/{n}  wall={wall:.0f}s (limit 540s)")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if p == n and wall < 540 else 1


if __name__ == "__main__":
    sys.exit(main())
