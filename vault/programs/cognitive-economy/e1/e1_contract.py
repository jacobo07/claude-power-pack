"""E1 stopping contract as pure functions (ADDENDUM-E1 "Stopping contract", 02-CONTEXT clauses 1-9).

No I/O, no subprocess, no file access, no clock: every verdict is computed from the raw fields of the records the
runner (e1_runner.py) writes, never from a stored verdict.

Run-record field contract (kind "run"), relied on by plans 02-02..02-04:
    kind "run", run_id, task, rule, arm, attempt, base, bank_dir, task_file_sha256, cli, cli_version, model,
    excluded (the arm-B claudeMdExcludes list; [] for arm A), started (ISO UTC), started_epoch,
    tree_files (files the leak listing saw), bank_in_tree (leak hits), pin_copies_removed (jprepare's scrub),
    precondition_rc, precondition_summary, session_launched (bool), claude_rc (int, "timeout", "exec-error" or
    None), wall_s, num_turns, is_error, subtype (the CLI result subtype), result_head (first 200 chars of the CLI
    result), session_id, session_changed_paths ("A|D|M <path>" across the session),
    grade_rc (int, "timeout" or None), grade_summary, grade_passed, grade_total, grade_fails,
    metrics {state MEASURED|NO_CALLS|UNMEASURED, reason, transcript, entrypoint, calls, first_call_context,
             total_context, output_tokens, models},
    bank_access [[marker, excerpt], ...] (bank markers found in the transcript's tool calls; evidence only, never a
             validity clause; None when no transcript was found), bank_access_error (only when the scan raised),
    cli_versions_observed (sorted distinct `version` values of the session transcript's lines; None when no
             transcript was found), bank_drift_after (e1_runner.bank_drift re-run after the post-session grade:
             [] = the graded bank was the frozen bank; absent = never re-checked),
    error (only when an exception was caught: "<ExcType>: <msg>"), ended, worktree_removed,
    valid, invalid_reasons, task_pass, spend.
Run-start record (appended once the session process exists and before the runner waits on it):
    kind "run_start", run_id, task, rule, arm, attempt, base, wt, started, started_epoch, cli_version, excluded,
    session_pid, session_pid_start (the child's pid and its /proc start time in clock ticks; both None when no
    process was started: an exec error or an injected exec_fn). e1_runner.reconcile refuses while that pid with
    that start time is alive.

A field that is absent is read as its failing value, never as a pass.
"""
import sys

sys.dont_write_bytecode = True

MODEL = "claude-opus-5-5"
CLI_VERSION = "2.1.289"  # ADDENDUM-E1 Design; STATE.md PINNED IDENTITIES
CAP = 17_000_000
PC_DELTA = 15_000
HARM_WINDOW = 8
HARM_LOSSES = 4
MAX_ATTEMPTS = 2
MAX_TASKS = 11
ARMS = ("A", "B")

# per-rule decisions
RELOCATION_CANDIDATE = "RELOCATION_CANDIDATE"
STAYS = "STAYS"
NO_INFORMATION = "NO_INFORMATION"
UNDECIDED_STAYS = "UNDECIDED_STAYS"
R2_CARRIED = "R2_CARRIED"

# terminal conditions
ALL_DECIDED = "ALL_DECIDED"
HARM_STOP = "HARM_STOP"
SPEND_STOP = "SPEND_STOP"
SPEND_UNMEASURED = "SPEND_UNMEASURED"
POSITIVE_CONTROL_STOP = "POSITIVE_CONTROL_STOP"


class ContractError(Exception):
    pass


def _pos_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def run_id(task_id, arm, attempt):
    """"<task_id>-<arm>-a<attempt>". Every attempt gets its own run tree, hence its own transcript directory."""
    if arm not in ARMS:
        raise ContractError(f"arm {arm!r} not in {ARMS}")
    if not (isinstance(attempt, int) and not isinstance(attempt, bool) and 1 <= attempt <= MAX_ATTEMPTS):
        raise ContractError(f"attempt {attempt!r} outside 1..{MAX_ATTEMPTS}")
    return f"{task_id}-{arm}-a{attempt}"


def run_valid(rec):
    """-> (valid, reasons). Clause 3: precondition red AND session ran AND grade ran; one reason per failed
    clause, in a fixed order. "Session ran" excludes a CLI error result other than error_max_turns (an API or
    usage-limit abort; VALIDITY READINGS (b)). "Grade ran" includes the bank's own grade timeout (reading (a)).
    The arm/exclude match (reading (c)) is refused before launch by e1_runner.check_arm_excludes; bank_access
    (reading (d)) is evidence only and is never read here. For a launched session (or one whose launch is not
    recorded) two more clauses hold: the transcript reports exactly CLI_VERSION (an auto-update between the
    per-run check and the exec would otherwise go unseen), and the bank re-checked after the grade is unchanged."""
    reasons = []
    if rec.get("bank_in_tree", ["(unlisted)"]):
        reasons.append("bank file in run tree")
    if rec.get("tree_files", 0) == 0 or not _pos_int(rec.get("tree_files")):
        reasons.append("run tree listing empty")
    pre_rc = rec.get("precondition_rc")
    if pre_rc == 0 or pre_rc is None or "E1J_PASS=" not in str(rec.get("precondition_summary") or ""):
        reasons.append("precondition not red")
    m = rec.get("metrics")
    m = m if isinstance(m, dict) else {}
    state = m.get("state")
    if state != "MEASURED":
        reasons.append(f"session transcript {state if state is not None else 'absent'}")
    ep = m.get("entrypoint")
    if ep != "sdk-cli":
        reasons.append(f"entrypoint {ep}")
    if MODEL not in (m.get("models") or []):
        reasons.append(f"model {MODEL} absent from transcript")
    if rec.get("is_error") is True and rec.get("subtype") != "error_max_turns":
        reasons.append(f"session ended in CLI error {rec.get('subtype')}")
    if not (grade_timed_out(rec) or ("E1J_PASS=" in str(rec.get("grade_summary") or "")
                                     and _pos_int(rec.get("grade_total")))):
        reasons.append("grade did not run")
    if rec.get("session_launched") is not False:
        seen = rec.get("cli_versions_observed")
        if seen != [CLI_VERSION]:
            reasons.append(f"cli version drift: transcript reports {seen!r}, want [{CLI_VERSION!r}]")
        drift = rec.get("bank_drift_after")
        if drift != []:
            reasons.append("bank drift during run" if drift else "bank not re-checked after grade")
    return (not reasons), reasons


def grade_timed_out(rec):
    """The frozen bank jgrade's own timeout result (rc 124, summary "grade timeout"): the grade RAN and the
    solution failed it (VALIDITY READINGS (a)). The runner's rc "timeout" (jgrade raised) is not this shape."""
    rc = rec.get("grade_rc")
    return _int(rc) and rc != 0 and rec.get("grade_summary") == "grade timeout"


def task_pass(rec):
    rc, total, passed = rec.get("grade_rc"), rec.get("grade_total"), rec.get("grade_passed")
    return (rc == 0 and not isinstance(rc, bool) and _pos_int(total) and passed == total)


def run_spend(rec):
    """Measured total_context; 0 for a transcript with no billed call or a session never launched; None (an
    unknown amount, never folded into 0) for a launched session whose transcript was not measured."""
    m = rec.get("metrics")
    m = m if isinstance(m, dict) else {}
    state = m.get("state")
    if state == "MEASURED":
        return m.get("total_context")
    if state == "NO_CALLS":
        return 0
    if rec.get("session_launched") is False:
        return 0
    return None


# ---- stopping-contract primitives (ADDENDUM-E1 stopping contract 1, 2, 4, 5, 6; Design: positive control) ----

def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def contract_order(tasks, allowed_rules):
    """Clause 1: tasks in descending rule bytes, so the largest rent is decided first if a stop comes early.
    Refuses more than MAX_TASKS tasks, a rule outside allowed_rules (the 11 E1 rules; the caller passes them, this
    module reads no file), a repeated id or rule, and equal rule_bytes (the order must be total)."""
    tasks = list(tasks)
    if len(tasks) > MAX_TASKS:
        raise ContractError(f"{len(tasks)} tasks > MAX_TASKS {MAX_TASKS}")
    allowed = set(allowed_rules)
    ids, rules, sizes = set(), set(), set()
    for t in tasks:
        tid, rule, size = t.get("id"), t.get("rule"), t.get("rule_bytes")
        if rule not in allowed:
            raise ContractError(f"task {tid}: rule {rule!r} is not an E1 rule")
        if not (_int(size) and size > 0):
            raise ContractError(f"task {tid}: rule_bytes {size!r} is not a positive int")
        if tid in ids:
            raise ContractError(f"task id {tid} repeated")
        if rule in rules:
            raise ContractError(f"rule {rule} carried by two tasks")
        if size in sizes:
            raise ContractError(f"task {tid}: rule_bytes {size} equals another task's (order not total)")
        ids.add(tid)
        rules.add(rule)
        sizes.add(size)
    return sorted(tasks, key=lambda t: -t["rule_bytes"])


def arm_order(i):
    """Clause 1: arm order alternates task by task -- position 0 A then B, position 1 B then A, ..."""
    return ("A", "B") if i % 2 == 0 else ("B", "A")


def decide(a_pass, b_pass):
    """Clause 4 -> (decision, b_pass_where_a_fails). Booleans only: token counts are not an input, so tokens can
    never break a tie. A pass + B fail STAYS (under group exclusion the loss is still charged to this task's rule,
    which errs toward keeping); A fail is no information; B passing where A fails is reported, never used."""
    a_pass, b_pass = a_pass is True, b_pass is True
    if a_pass and b_pass:
        return RELOCATION_CANDIDATE, False
    if a_pass:
        return STAYS, False
    return NO_INFORMATION, b_pass


def positive_control_ok(a_first, b_first):
    """Gate 1 on the first valid pair: B's first-call context at least PC_DELTA below A's. Unknown -> False."""
    if not (_int(a_first) and _int(b_first)):
        return False
    return b_first <= a_first - PC_DELTA


def harm_fired(valid_pair_decisions):
    """Clause 5: B loses (STAYS) in HARM_LOSSES or more of the first HARM_WINDOW valid pairs. Firing at the 4th
    loss inside the window is the outcome waiting for the 8th pair would give (the count only grows), for less
    spend. A loss in the 9th valid pair never counts; NO_INFORMATION (A failed) is not a B loss."""
    return sum(1 for d in list(valid_pair_decisions)[:HARM_WINDOW] if d == STAYS) >= HARM_LOSSES


def spend_reached(spent):
    """Clause 6 as worded ("reaches 17,000,000"). Kept for the stop record and the reader; NOT the gate."""
    return spent >= CAP


def spend_stop_due(spent, max_seen):
    """The clause-6 gate, checked before every run start (ORCHESTRATOR AMENDMENT 2026-10-05). spent = summed spend
    of ALL run records (valid and invalid: they were spent); max_seen = the largest single-run spend so far (None
    before the first measured run). Stop when the cap is reached, or when a run as large as the largest seen would
    carry the total past it: going past 17,000,000 needs a new Owner yes (ADDENDUM-E1 clause 6). It only stops
    sooner; no decision changes. Callers handle spent None (SPEND_UNMEASURED) before calling it."""
    if spent >= CAP:
        return True
    return max_seen is not None and spent + max_seen > CAP


# ---- replayable state machine (ADDENDUM-E1 stopping contract 2-7, "After the runs") ---------------------------
#
# The state is a pure function of the append-only record list, so resuming after a crash is the same computation
# as the first start. Validity, pass and spend are recomputed from raw run-record fields on every replay; a stored
# "valid" / "task_pass" / "spend" key is never read.

PENDING = "PENDING"
PAIR_VALID = "PAIR_VALID"
STOP_CONDITIONS = (ALL_DECIDED, HARM_STOP, SPEND_STOP, SPEND_UNMEASURED, POSITIVE_CONTROL_STOP)


def _first(rec):
    m = rec.get("metrics")
    return m.get("first_call_context") if isinstance(m, dict) else None


def _task_state(pos, task, runs):
    """Status of the task at contract position pos from its run records (already integrity-checked)."""
    arms = arm_order(pos)
    st = {"position": pos, "id": task["id"], "rule": task["rule"], "arms": arms, "status": PENDING,
          "decision": None, "b_pass_where_a_fails": None, "a_run": None, "b_run": None, "a_pass": None,
          "b_pass": None, "a_first": None, "b_first": None, "no_info_reason": None, "next": None,
          "runs": [r["run_id"] for r in runs]}
    valid = {}
    for arm in arms:
        rs = sorted((r for r in runs if r["arm"] == arm), key=lambda r: r["attempt"])
        v = next((r for r in rs if run_valid(r)[0]), None)
        if v is None:
            if len(rs) >= MAX_ATTEMPTS:
                st.update(status=NO_INFORMATION, decision=NO_INFORMATION,
                          no_info_reason=f"arm {arm} invalid twice")
            else:
                st["next"] = (arm, len(rs) + 1)
            return st
        valid[arm] = v
    a, b = valid["A"], valid["B"]
    a_pass, b_pass = task_pass(a), task_pass(b)
    decision, flag = decide(a_pass, b_pass)
    st.update(status=PAIR_VALID, decision=decision, b_pass_where_a_fails=flag, a_run=a["run_id"],
              b_run=b["run_id"], a_pass=a_pass, b_pass=b_pass, a_first=_first(a), b_first=_first(b))
    return st


def replay(order, records):
    """-> state. `order` is the contract-ordered task list (dicts with id, rule, rule_bytes). Only kind "run"
    drives task state; "run_start" feeds pending_starts, "pair" fills pairs_recorded, the last "stop" is kept,
    "refusal" is informational. Raises ContractError on a record set the contract could not have produced."""
    order = list(order)
    index = {t["id"]: i for i, t in enumerate(order)}
    by_task = {t["id"]: [] for t in order}
    states = [_task_state(i, t, []) for i, t in enumerate(order)]
    seen, run_recs = set(), []
    stopped_at = None
    for n, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ContractError(f"record {n}: not a JSON object ({type(rec).__name__})")
        if rec.get("kind") == "stop" and stopped_at is None:
            stopped_at = n
        if rec.get("kind") != "run":
            continue
        where = f"record {n} ({rec.get('run_id')!r})"
        if stopped_at is not None:
            raise ContractError(f"{where}: run recorded after the stop record at {stopped_at}")
        tid, arm, att = rec.get("task"), rec.get("arm"), rec.get("attempt")
        if tid not in index:
            raise ContractError(f"{where}: unknown task {tid!r}")
        if arm not in ARMS:
            raise ContractError(f"{where}: arm {arm!r} not in {ARMS}")
        if not (_int(att) and 1 <= att <= MAX_ATTEMPTS):
            raise ContractError(f"{where}: attempt {att!r} outside 1..{MAX_ATTEMPTS}")
        if rec.get("run_id") != run_id(tid, arm, att):
            raise ContractError(f"{where}: run_id is not {run_id(tid, arm, att)!r}")
        if (tid, arm, att) in seen:
            raise ContractError(f"{where}: duplicate run of ({tid}, {arm}, attempt {att})")
        pos = index[tid]
        cur = states[pos]
        if cur["status"] != PENDING:
            raise ContractError(f"{where}: task {tid} is already terminal ({cur['status']})")
        earlier = next((s for s in states[:pos] if s["status"] == PENDING), None)
        if earlier is not None:
            raise ContractError(f"{where}: run of {tid} while earlier task {earlier['id']} is still PENDING")
        first_arm = arm_order(pos)[0]
        if arm != first_arm and cur["next"][0] == first_arm:
            raise ContractError(f"{where}: arm {arm} of {tid} before its first arm {first_arm} has a valid run")
        if (arm, att) != cur["next"]:
            raise ContractError(f"{where}: expected ({tid}, {cur['next'][0]}, attempt {cur['next'][1]})")
        seen.add((tid, arm, att))
        run_recs.append(rec)
        by_task[tid].append(rec)
        states[pos] = _task_state(pos, order[pos], by_task[tid])

    valid_pairs = [s["id"] for s in states if s["status"] == PAIR_VALID]
    fp = next((s for s in states if s["status"] == PAIR_VALID), None)
    first_pair = None
    if fp is not None:
        delta = fp["a_first"] - fp["b_first"] if _int(fp["a_first"]) and _int(fp["b_first"]) else None
        first_pair = {"task": fp["id"], "a_first": fp["a_first"], "b_first": fp["b_first"], "delta": delta,
                      "ok": positive_control_ok(fp["a_first"], fp["b_first"])}
    decisions = [s["decision"] for s in states if s["status"] == PAIR_VALID]
    spends = [run_spend(r) for r in run_recs]
    measured = [s for s in spends if _int(s)]
    run_ids_seen = {r["run_id"] for r in run_recs}
    pending_starts = []
    for rec in records:
        rid = rec.get("run_id")
        if rec.get("kind") == "run_start" and rid not in run_ids_seen and rid not in pending_starts:
            pending_starts.append(rid)
    stops = [r for r in records if r.get("kind") == "stop"]
    return {
        "tasks": states,
        "valid_pairs": valid_pairs,
        "first_pair": first_pair,
        "losses_in_window": sum(1 for d in decisions[:HARM_WINDOW] if d == STAYS),
        "harm": harm_fired(decisions),
        "spent": sum(spends) if len(measured) == len(spends) else None,
        "max_seen": max(measured) if measured else None,
        "runs_counted": len(run_recs),
        "pending_starts": pending_starts,
        "pairs_recorded": [r.get("task") for r in records if r.get("kind") == "pair"],
        "stop": stops[-1] if stops else None,
    }


def next_action(state):
    """The single next action, checks in this fixed order:
    HALTED (a stop record exists: a stop is never a request to go on), RECONCILE (an interrupted run must be
    measured and recorded before anything else, so its spend is counted), POSITIVE_CONTROL_STOP (first valid
    pair), HARM_STOP, ALL_DECIDED (no PENDING task, even at the cap), SPEND_UNMEASURED, SPEND_STOP, else RUN.

    The spend check runs before every run start and is predictive (ORCHESTRATOR AMENDMENT 2026-10-05; CONTEXT
    clause 6: "a run that would start at or above the cap does not start"; ADDENDUM-E1 clause 6: going past
    17,000,000 needs a new Owner yes): a run does not start when the largest run seen so far would carry the summed
    context past the cap. The total can therefore pass 17,000,000 only when a run spends more than every earlier
    run, and only by that excess; stop_record reports it as over_cap_by, which is 0 otherwise. SPEND_UNMEASURED is
    the instrument stop for an unknown spend (UNMEASURED is never PASS; the cap cannot be checked against an
    unknown) -- Claude's discretion, erring toward stopping.
    Returns ("HALTED", condition) | ("RECONCILE", run_id) | ("STOP", condition) | ("RUN", task_id, arm, attempt)."""
    if state["stop"] is not None:
        return ("HALTED", state["stop"].get("condition"))
    if state["pending_starts"]:
        return ("RECONCILE", state["pending_starts"][0])
    if state["first_pair"] is not None and not state["first_pair"]["ok"]:
        return ("STOP", POSITIVE_CONTROL_STOP)
    if state["harm"]:
        return ("STOP", HARM_STOP)
    pending = next((t for t in state["tasks"] if t["status"] == PENDING), None)
    if pending is None:
        return ("STOP", ALL_DECIDED)
    if state["spent"] is None:
        return ("STOP", SPEND_UNMEASURED)
    if spend_stop_due(state["spent"], state["max_seen"]):
        return ("STOP", SPEND_STOP)
    return ("RUN", pending["id"], pending["next"][0], pending["next"][1])


_BASIS = {RELOCATION_CANDIDATE: "A passed, B passed",
          STAYS: "A passed, B failed: the loss is charged to this task's rule",
          NO_INFORMATION: "A failed: no information, the rule stays"}


def final_decisions(state, condition, r2_rules):
    """-> {rule: {decision, basis, task, a_run, b_run, b_pass_where_a_fails}} for the E1 rules, plus
    {rule: {decision, basis}} for the r2_rules. HARM_STOP: all 13 STAY (clause 5). POSITIVE_CONTROL_STOP: the E1
    rules STAY, "arms did not differ" (the manipulation failed, so no pair is used). Otherwise a valid pair keeps
    its decision, a no-information task stays, and a task whose pair did not run is UNDECIDED_STAYS (clause 6)."""
    if condition not in STOP_CONDITIONS:
        raise ContractError(f"unknown stop condition {condition!r}")
    if condition == ALL_DECIDED and any(t["status"] == PENDING for t in state["tasks"]):
        raise ContractError("ALL_DECIDED with a PENDING task")
    out = {}
    for t in state["tasks"]:
        if condition == HARM_STOP:
            dec, basis = STAYS, "harm stop: group exclusion falsified"
        elif condition == POSITIVE_CONTROL_STOP:
            dec, basis = STAYS, "arms did not differ"
        elif t["status"] == PAIR_VALID:
            dec, basis = t["decision"], _BASIS[t["decision"]]
        elif t["status"] == NO_INFORMATION:
            dec, basis = NO_INFORMATION, t["no_info_reason"]
        else:
            dec, basis = UNDECIDED_STAYS, f"pair did not run before {condition}: the rule stays resident"
        out[t["rule"]] = {"decision": dec, "basis": basis, "task": t["id"], "a_run": t["a_run"],
                          "b_run": t["b_run"], "b_pass_where_a_fails": t["b_pass_where_a_fails"]}
    for r in r2_rules:
        if condition == HARM_STOP:
            out[r] = {"decision": STAYS, "basis": "harm stop: group exclusion falsified"}
        else:
            out[r] = {"decision": R2_CARRIED, "basis": "decided by R2, carried in by reference"}
    return out


def pair_record(state, task_id):
    """The record appended once a task becomes terminal (PAIR_VALID or NO_INFORMATION)."""
    t = next((x for x in state["tasks"] if x["id"] == task_id), None)
    if t is None:
        raise ContractError(f"unknown task {task_id!r}")
    if t["status"] == PENDING:
        raise ContractError(f"task {task_id} is still PENDING")
    fp = state["first_pair"]
    is_first = fp is not None and fp["task"] == task_id
    delta = t["a_first"] - t["b_first"] if _int(t["a_first"]) and _int(t["b_first"]) else None
    return {"kind": "pair", "task": task_id, "rule": t["rule"], "position": t["position"], "status": t["status"],
            "decision": t["decision"], "a_run": t["a_run"], "b_run": t["b_run"], "a_pass": t["a_pass"],
            "b_pass": t["b_pass"], "a_first": t["a_first"], "b_first": t["b_first"], "delta": delta,
            "b_pass_where_a_fails": t["b_pass_where_a_fails"], "no_info_reason": t["no_info_reason"],
            "positive_control": dict(fp) if is_first else None, "used": not (is_first and not fp["ok"]),
            "spent_so_far": state["spent"]}


def stop_record(state, condition, r2_rules):
    """The final record naming the stop condition. No timestamp here (the loop adds "at")."""
    spent = state["spent"]
    return {"kind": "stop", "condition": condition,
            "final_decisions": final_decisions(state, condition, r2_rules),
            "spent": spent, "cap": CAP,
            "over_cap_by": None if spent is None else max(0, spent - CAP),
            "cap_reached": None if spent is None else spend_reached(spent),
            "max_seen": state["max_seen"], "runs_counted": state["runs_counted"],
            "valid_pairs": len(state["valid_pairs"]), "losses_in_window": state["losses_in_window"],
            "positive_control": dict(state["first_pair"]) if state["first_pair"] else None}
