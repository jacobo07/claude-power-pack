# Phase 2: W1 Convergence semantics - Research

**Researched:** 2026-10-07
**Domain:** Python event-log projections (GSD X goal spine), spec amendment, zero-behaviour-change seam
**Confidence:** HIGH for in-repo facts (all read from source this session), MEDIUM for recommended semantics (design choices, flagged)

<user_constraints>
## User Constraints (from 02-CONTEXT.md)

### Locked Decisions
- **Spec of record:** `vault/specs/gsdx-proof-conserving-convergence.md`. §Semantics says "nothing below is final until the W1 audit", and this phase is that audit. Amend the spec in place; do not fork a second spec.
- **ULTRA protocol in an unattended run.** The /ultra Q&A pass (phase 2 of 7) is answered BY THE WORKER from the spec, the dataset §s that DENOMINATOR rows cite, and Phase 1 evidence. Each answer is recorded as a decision with its reason in the workstream STATE.md. Never stop to ask (mission card DECISION GATE). Anything the gate reserves to the Owner is recorded as OWNER DECISION NEEDED, and the work continues.
- **Auditor:** `subagent_type: oneshot-architect-auditor`. It is read-only and emits a numbered gap list. Every gap is injected into the spec, or dispositioned with a reason in the phase EVIDENCE.md. Agent dispatch goes alone in its batch, with a bound and a durable-output clause (write findings to a file as it goes).
- **Items the spec must resolve:** proof states FRESH / INHERITED / SUPERSEDED / STALE / UNKNOWN, with UNKNOWN -> FULL (D01); certificate validity: claim, revision, gate pin, causal fingerprint, environment, policy; the causal fingerprint premise set, with unknown -> legacy whole-tree binding (`git_state.py:129-133`); freshness classes extending `gate_class`, including the legacy mapping; frontier semantics, with `decide()` keeping its signature (D43); the new event types, all additive; kill switches `GSDX_FRONTIER=off` and `GSDX_PROOF_INHERITANCE=off`; legacy-log replay; the typed proof contract, where a legacy done_gate is a one-element contract (D10); the five laws as executable invariants + V-gates (D03); event log, not a second DB (D44).
- **Zero behaviour change** is the seam's whole contract. Every new event type is additive and every projection is pure over the GoalLog. No legacy caller changes behaviour, and with no new events present the outputs are byte-identical. Incumbent suite counts to hold: reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8, gate_provider 18/18, plus every other `tools/test_gsd_x_goal_*.py` at its Phase 1 count (`01-EVIDENCE.md` incumbent table).
- **Legacy replay corpus:** g-002-router-surface and g-001-smoke-runner, recorded by an older engine under `~/.claude/state/gsd-x/goals`. They are read ONLY through a hash-verified copy (the `tools/gsdx_goal_timeline.py recorded` pattern) and never written. A committed fixture copy under the test tree is preferred, so that the replay test is hermetic and does not depend on the live store.
- **RED-first** applies to any behaviour this phase adds. For a seam whose contract is "no change", the red case is that a projection or event changes a legacy output, and that case must be driven and seen to fail the invariant test.
- **Liveness:** each new module is wired in the same commit, or declared in `vault/liveness/reachability_registry.json`. `python modules/liveness/reachability.py` exits 0 at phase end.
- **Operating constraints** in ROADMAP.md apply verbatim: worktree-only writes, PowerShell for git/python, the absolute git path, hermetic tests, one msgfile per commit, never push.

### Claude's Discretion
- Module layout for the new event types and projections, inside the `modules/gsd_x/goal/` owner. No new top-level package.
- Whether the five laws land as one invariant suite or as gates inside the existing suites, as long as each law has a gate that can go red.

### Deferred Ideas (OUT OF SCOPE)
- Frontier compilation and scheduling behaviour (Phase 3), candidate snapshots and inheritance behaviour (Phase 4), the judge VALIDATE path (Phase 5). Phase 2 only lands their event types and projections, with no behaviour change.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (DENOMINATOR.md rows 10,12,19,52,53) | Research Support |
|----|---------------------------------------------------|------------------|
| D01 | FRESH/INHERITED/SUPERSEDED/UNKNOWN->full; disposition "EXTEND convergence projection"; phases 2,4 | Section 6 G1-G6 (state machine + certificate validity), sections 1.3-1.5 (projection shape precedent `evidence.py`), section 8 gates V-PCC-STATE-* |
| D03 | Five laws executable (§2); "CONNECT as invariants + V-gates + baseline entries"; phases 2,10 | Section 3 (laws verbatim from dataset lines 511-517, style of existing suites), section 8 gates V-PCC-LAW-* (baseline entries belong to Phase 10, R09) |
| D10 | Typed proof contract (§9); "EXTEND, legacy = 1-element contract"; phases 2,4 | Section 6 G7 (contract schema), section 2 (`done_gate`/`gate_class` consumers), section 8 gates V-PCC-CONTRACT-* |
| D43 | Backward compat decide()/done_gate (§42); "EXTEND + legacy replay test"; phase 2 | Section 2 (every consumer), section 4 (replay corpus facts), section 8 gates V-PCC-REPLAY-* and V-PCC-DECIDE-SIG |
| D44 | Event log, not second DB (§43); "invariant test"; phase 2 | Sections 1.1-1.4 (GoalLog contract), section 6 G9, section 8 gate V-PCC-NO-SECOND-STORE |
</phase_requirements>

Provenance: every in-repo discrete value below was read with `Read` this session and quoted verbatim with file:line.
Design recommendations are `[ASSUMED]` unless a source is cited (they are decisions for the W1 audit, not facts).
Dataset quotes are from `C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md` (design INPUT per the spec, not implementation truth).

## Summary

The GoalLog is an append-only, hash-chained directory of `NNNNNN.json` events whose `read()` verifies the chain and the digest but NEVER looks at `type` or `data` (`log.py:152-178`). Every projection over it (`contract.project`, `project_convergence`, `project_epochs`, `judge.current`, `project_operator`, `project_hypotheses`) is an `if/elif` ladder with no `else`, so an unknown event type is silently skipped today. `evidence.py:24-26` already documents that as the intended forward-compat contract, and `evidence.py`, `intervention.py`, `judge.py` and `sweep.py` are four precedents of a module that owns its own event constants and its own pure projection. The compatibility seam is therefore low-risk by construction. Its real risks are not "do old readers crash" but: (a) seq-valued fields that shift if new events are interleaved; (b) `engine_identity` changing the moment a new `.py` lands under `modules/gsd_x/goal/` (it stales the sweep's autonomy record); (c) the spec leaving candidate identity, certificate claim identity, risk-tag derivation and the `unknown:` tree equality hole undefined; (d) a write-authority rule (`epoch.begin` one-open-epoch) that contradicts the Phase 3 goal and is not mentioned in the spec.

Legacy replay is cheap and a committed fixture is reasonable: g-002 is 50 events (about 44 KB without `runs/`), g-001 is 123 events (about 119 KB without `runs/`). The repo already has a characterization-golden pattern to copy (`tools/test_gsd_mission_legacy_characterization.py` + `tools/fixtures/gsd_mission_legacy_golden.json`: `--capture` refused when the golden exists, a gate that the golden predates the change, in-process mutants that must turn the comparison red). The recorded logs do NOT contain `goal.revised`, `obligation.carried`, `operator.*`, `evidence.hypothesis`, `goal.budget_set` or `goal.authority_set` events, so a synthetic legacy generator is also required for coverage.

**Primary recommendation:** land ONE new module in `modules/gsd_x/goal/` (`proof.py`: proof-state / certificate / freshness / contract projections, its event constants and the two kill-switch readers, following the `evidence.py` shape), capture the legacy golden from the UNMODIFIED engine BEFORE the first line of the seam, drive the red case by an in-process mutant that makes a legacy projection react to a new type, and keep `compile_frontier` and any inheritance consumption OUT of Phase 2 (spec semantics only), because landing them would be scaffold with no consumer.

## Project Constraints (from CLAUDE.md)

- Windows host: git / python / mix through the PowerShell tool, never Bash; git by absolute path `& 'C:\Program Files\Git\cmd\git.exe' -C <repo>`; python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` with `$env:PYTHONIOENCODING='utf-8'`.
- Reality Contract: zero placeholders, zero stub returns, zero empty catch blocks in shipped code; if a feature cannot be wired end-to-end this turn, state the gap and stop (so: no `compile_frontier` stub in Phase 2).
- Liveness Standard: `python modules/liveness/reachability.py` exit 0 before a module is declared done; wire, DECLARE (`PLANNED` + OWNER_QUEUE note) or delete (`vault/liveness/reachability_registry.json`, precedent lines 442-453).
- HR-PREMISE-001: before coding against any API a plan names, run `python modules/error_prevention/premise_verifier.py --premises <json>` (Phase 1 did this for the spec's APIs: `01-PREMISES.md`).
- Tests: hermetic (`GSDX_GOALS_ROOT`/HOME redirected to a temp dir), summary line `<SUITE>_PASS=n/m  threshold=n/m`, gate naming `V-<DOMAIN>-<NAME>`, RED-first, mutation evidence through `tools/mutation_drill.py` (isolated copy + control), never `mutation_probe` live mode.
- Python testing doctrine (`~/.claude/rules/python/testing.md`): AAA, mock at the boundary only, every fail-open branch has a dedicated test.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/`; a live-hook change is an OWNER STEP.
- One msgfile per commit, `git commit -F`, verify `git log -1 --format=%s`, never push; commit message ends with the session Co-Authored-By line.
- Regla 12: two materially identical failures of one approach -> pivot.

## 1. GoalLog facts (target 1)

### 1.1 Storage, write, read [VERIFIED: modules/gsd_x/goal/log.py]

- Layout: `goals_root()/<repo-id>/<goal-id>/NNNNNN.json`. `EVENT_RE = re.compile(r"^(\d{6})\.json$")` (log.py:41). Root: `ENV_ROOT = "GSDX_GOALS_ROOT"          # tests and alternate hosts only` (log.py:43); default `Path.home() / ".claude" / "state" / "gsd-x" / "goals"` (log.py:102).
- Event dataclass (log.py:115-123): `seq:int, type:str, ts:str, actor:str, data:dict, prev_digest:str, digest:str`. `Event.from_dict` reads exactly `d["seq"], d["type"], d["ts"], d["actor"], d.get("data") or {}, d["prev_digest"], d["digest"]` (log.py:126-128). NO schema/version field exists anywhere in the envelope.
- Digest: `event_digest(event)` = sha256 over canonical JSON (`sort_keys=True, ensure_ascii=False, separators=(",", ":")`) of the event minus `digest` (log.py:105-112). `GENESIS = "0" * 64` (log.py:135).
- `GoalLog.read()` (log.py:152-178) verifies: contiguous sequence (gap -> `GoalLogCorrupt`), digest recompute, `prev_digest` chain and `seq` match. It does NOT inspect `type` or `data` at all. An event of any type string with a valid envelope reads fine.
- `append(expected_seq, type_, data, actor)` (log.py:180-200): re-reads the log (cheap early out, `LostRace` if `expected_seq != len(events)+1`), builds body, calls `publish` (atomic temp+`os.link`, fsync). `type_` is not validated against any vocabulary.
- A written event file is `json.dumps(body, indent=2, ensure_ascii=False)` (log.py:218); `ts` is `datetime.now(timezone.utc).isoformat()` (log.py:194). Digest is over the canonical form, so file formatting does not matter.

### 1.2 Unknown event types on read today [VERIFIED: contract.py:93-110, convergence.py:110-141, epoch.py:241-258]

Every projection is an `if/elif` ladder over `ev.type` with NO `else` branch and no unknown-type error:
- `contract.project` (contract.py:93-109): handles `DECLARED/REVISED`, `BUDGET_SET`, `AUTHORITY_SET`; unknown types fall through, then `st.last_seq = ev.seq` (contract.py:109) runs for EVERY event.
- `project_convergence` (convergence.py:110-141): `PLANE_SET, OB_ACCEPTED, OB_SATISFIED, OB_DISPOSITIONED, OB_CARRIED, FAILURE_RECORDED, FAILURE_DISPOSITIONED`; no else.
- `project_epochs` (epoch.py:241-258): `DISPATCHING, RUNNING, ENDED, RECEIPT`; no else.

Conclusion: an additive new event type is silently ignored by all three projections. The only observable effects of a new event on legacy code are (a) `GoalState.last_seq` and `len(GoalState.events)` grow, (b) the on-disk file count grows, (c) the chain tip digest changes.

### 1.3 Event-type vocabulary today (discovered by grep over modules/gsd_x, all read) [VERIFIED]

| Type string | Constant (file:line) | Projection that reads it |
|---|---|---|
| `goal.declared` / `goal.revised` / `goal.budget_set` / `goal.authority_set` | contract.py:25-28 | `contract.project` |
| `plane.applicability`, `obligation.accepted`, `obligation.satisfied`, `obligation.dispositioned`, `obligation.carried`, `failure.recorded`, `failure.dispositioned` | convergence.py:52-58 | `project_convergence` |
| `epoch.dispatching`, `epoch.running`, `epoch.ended`, `epoch.receipt` | epoch.py:43-46 | `project_epochs` |
| `goal.judged` | judge.py:44 | `judge.current` (iterates `state.events`, `if ev.type != JUDGED: continue`, judge.py:88-90) |
| `goal.autonomous` | sweep.py:49 | `sweep.is_autonomous`, `_autonomy_event`, `autonomous_goals` |
| `operator.pause/resume/cancel/note` | intervention.py:34-35 | `project_operator` (`if ev.type not in KINDS: continue`, intervention.py:57-58) |
| `evidence.hypothesis` | evidence.py:36 | `project_hypotheses` (`if ev.type != HYPOTHESIS: continue`, evidence.py:69-70) |

Precedent for the seam (strongest finding): `evidence.py:24-26` already states the contract in prose: "Old readers ignore this event type (contract.project skips unknown types). That is acceptable here and only here: no pre-UWCP code consulted hypotheses, so an old reader loses nothing it ever had." Four modules (`intervention.py`, `evidence.py`, `judge.py`, `sweep.py`) own their own event constants and their own projection over `state.events` -- NOT `contract.py`. The new PCC events should follow exactly this shape: constants + pure `project_*(state)` in a new module under `modules/gsd_x/goal/`, `continue` on foreign types, `GoalLogCorrupt` on a malformed payload of OWN types.

### 1.4 What an additive new event must look like [VERIFIED by the above reads; recommendation is ASSUMED design]

An event is legacy-safe iff all hold:
1. Type string is a dotted name not in the 22 strings of the table above (4 + 7 + 4 + 1 + 1 + 4 + 1 by row) (suggest namespaces `proof.*`, `frontier.*`, `adapter.*`, `candidate.*`; spec already names `proof.produced/inherited/invalidated`).
2. Envelope is the unchanged 7-field `Event` (no new envelope field: `Event.from_dict` reads exactly those keys, and `event_digest` hashes every key but `digest`; an extra top-level key would be hashed and survive but `to_dict` would drop it, so ANY new top-level field is silently lost on `Event` round-trips). All new data goes under `data`.
3. `data` carries its own schema marker (e.g. `"v": 1`) because the envelope has no version field -- the only forward-compat lever.
4. It is written through `GoalLog.append(state.last_seq + 1, ...)` (CAS), never by a side channel (D44: event log, not a second DB).
5. It never reuses a legacy type with a different payload shape: every legacy projection raises `GoalLogCorrupt` on a KeyError/TypeError for its OWN types (contract.py:100-103, convergence.py:139-141, epoch.py:256-258). A new field added INSIDE an existing event's `data` is tolerated by readers that use `d["x"]`/`d.get`, but `OB_SATISFIED`'s `verdict` is copied with `dict(d["verdict"])` (convergence.py:122) so extra keys inside `verdict` would flow into `o.verdict` and `judge`/`reconcile` only read named keys -- safe, but a new TYPE is cleaner and is what D44 wants.

### 1.5 Places a new event DOES change legacy-observable output (the only ones) [VERIFIED]

| Observer | What moves | Zero-change verdict |
|---|---|---|
| `GoalState.last_seq` (contract.py:109), `len(state.events)` | grows by 1 per event | benign: writers use `state.last_seq + 1` against a re-read (log.py:187-189) |
| `epoch.begin` "one epoch at a time" (epoch.py:280-286) | counts only `project_epochs` records, unaffected | safe -- and note it HARD-BLOCKS the Phase 3 N-parallel-gates goal at the write authority; Phase 3 must change it (flag as spec gap G11) |
| `tools/gsdx_goal_timeline.py` / CLI status renderers | if they enumerate event types, a new type may print "unknown" | NEEDS CHECK of `tools/gsd_x_goal.py` (see section 2.3) |
| `engine_identity` (engine_identity.py:34-39) | seeds are `sorted(pkg.rglob("*.py"))` + CLI + required suites, so ANY new `.py` under `modules/gsd_x/goal/` changes the `engine:` digest | NOT a legacy-output change, but it (a) stales every recorded autonomy record (`autonomy_verdict`, sweep.py:128-135 compares `rec_engine != engine`) so `record-gates` must be re-run after the seam lands, and (b) is in `info_key` as the `engine` term (epoch.py:202-218), so retried gate attempts count as "new information". Planner must list this as a known, intended side effect and record it as an Owner-visible note. |

## 2. Every projection and consumer, and whether a new event type is observable (target 2)

All rows [VERIFIED] by reading the cited lines this session.

| Consumer | file:line | Reads | Observes a NEW event type? |
|---|---|---|---|
| `contract.project(log)` | contract.py:87-110 | `log.read()` then ladder on DECLARED/REVISED/BUDGET_SET/AUTHORITY_SET | Ignored; but `st.last_seq = ev.seq` (:109) and `st.events` include it. Raises `GoalNotDeclared` if `events[0].type != DECLARED` (:90), so a new event can never be seq 1. |
| `project_convergence(state)` | convergence.py:106-142 | 7 types | Ignored. Stores `"seq": ev.seq` in `cv.failures[id]` (:135): a seq-valued field. |
| `goal_closure(state, tree_hash, open_epochs)` | convergence.py:323-369 | `cv`, `state.revision`, tree string | Unobservable. The authority for `may_close`; compares `v.get("tree_hash") != tree_hash` (:350) and `v.get("revision") != state.revision` (:353). INHERITED proofs are invisible to it. |
| `reconcile.decide(ctx)` | reconcile.py:124-244 | `project_epochs`, `project_convergence`, `blocking_reason`, `goal_closure`, `ctx.*` | Unobservable. Priority chain: RECOVER (:131) -> HARVEST/WAIT per running epoch (:138-150) -> operator BLOCKED (:156) -> closure/CONVERGED/ESCALATE/READY_FOR_JUDGE (:161-171) -> `blocked_on` (:174) -> budget ESCALATE (:177) -> gate NEXT_EPOCH (:204-213) -> work NEXT_EPOCH (:223-235) -> ESCALATE (:239). `Decision` is a frozen dataclass (reconcile.py:49-58) whose `reason` text is printed by sweep (`d.reason[:160]`, sweep.py:390). |
| `reconcile._needs_a_gate_here` | reconcile.py:101-121 | `o.verdict["tree_hash"]`, `["revision"]` | Unobservable. Returns a reason STRING that flows into `Decision.reason`. |
| `project_epochs`, `open_epochs`, `info_key`, `scope_hash` | epoch.py:239-263, 202-218, 166-191 | 4 epoch types | Ignored. |
| `epoch.begin` | epoch.py:268-298 | `project_epochs` | Unobservable, BUT hard-enforces one open epoch per goal (:283-286) at the write authority (see G11). |
| `epoch.ingest_receipt` | epoch.py:322-370 | `project_epochs`, may re-`project(log)` (:333) | Unobservable. |
| `sweep.sweep_goal` | sweep.py:278-391 | `gc.project`, `gs.tree_id(root, paths)` (:286), `ep.scope_hash` (:309), `jd.current(state, tree, state.revision)` (:315), `rc.decide` (:308) | Unobservable. One decision per pass (:317-390). |
| `sweep.is_autonomous`, `_autonomy_event`, `autonomous_goals` | sweep.py:150-215 | scan `state.events` for `goal.autonomous` | Ignored. |
| `judge.judge`, `judge.current`, `judge.record` | judge.py:120-191, 73-94, 61-70 | `project_convergence`, `state.events` filtered by `JUDGED` | Ignored. Judge re-runs EVERY `SATISFIED` obligation serially (:147-179); no certificate path. |
| `intervention.project_operator`, `blocking_reason` | intervention.py:54-76, 107-116 | `if ev.type not in KINDS: continue` (:57-58) | Ignored. `OperatorState.last_seq` is a seq-valued field (:49, :72). |
| `evidence.project_hypotheses` | evidence.py:66-85 | `if ev.type != HYPOTHESIS: continue` (:69-70) | Ignored. `Hypothesis.history` stores `(ev.seq, ...)` (:81). |
| `brief.py` | brief.py:24, 56, 99 | `project_convergence(state)`; renders `o.done_gate` (:99) | Unobservable (uses projections only; `grep` of `.events` found no direct use in brief.py or cli.py). |
| `git_state.tree_id` / `blob_oid` / `pin_scheme` / `file_pin` | git_state.py:124-142, 62-75, 87-92, 101-121 | the working tree, never the log | Not log readers. `tree_id` returns `git:<HEAD^{tree}>` when the scope is clean (:129-133), `work:<sha256[:24]>` over scope paths when dirty (:134-142), and the CONSTANT `unknown:not-a-git-tree` on any git failure (:131). |
| `tools/gsd_x_goal.py status` | gsd_x_goal.py:138-170 | `cv.goal_closure(s, tree, ep.open_epochs(s))` | Prints `(events: {s.last_seq})` (:154) and JSON `"last_seq"` (:151): the ONLY CLI text that changes by event count. `export`/`restore` (:333-365) are type-agnostic (`e.to_dict()`, `lg.publish(raw)`). |
| `tools/gsdx_goal_timeline.py timeline()` | gsdx_goal_timeline.py:56-97 | every event | Adds a row `{"seq","type","t_s"}` per event (:71); instrument only. |
| `engine_identity.engine_identity` | engine_identity.py:34-39, 139-152 | the SOURCE files, not the log | Moves when any `.py` under `modules/gsd_x/goal/` is added (seeds `sorted(pkg.rglob("*.py"))` :39). |

`done_gate` is read by: judge.py:157,163,169,177; sweep.py:364; reconcile.py:212; brief.py:99; convergence.py:164,181,358. `gate_class` is read/validated at: convergence.py:45,89,119,168-179,271-274,305; sweep.py:267,352-365; providers/gate.py:29,110-111,204; mission/closure.py:49. `GATE_CLASSES = ("unit", "integration", "in_game", "live")` and `RUNTIME_GATE_CLASSES = frozenset({"in_game", "live"})` (convergence.py:45,47).

**Conclusion for the seam (D43):** no legacy function CALLS anything new, so "zero behaviour change" is true by construction PROVIDED (1) new types never reuse a legacy type string, (2) no legacy file is edited (a diff of `modules/gsd_x/goal/*.py` other than the NEW file must be empty), and (3) the invariant suite measures it instead of assuming it. Requirement (2) is the cheapest and strongest gate: `git diff --stat <base>..HEAD -- modules/gsd_x/` lists only added files and `.gitattributes` / fixtures / tools / registry. If the planner needs a legacy edit (e.g. to export a constant), that edit is itself the red case.

## 3. The five laws and the existing invariant-test style (target 3)

### 3.1 Laws, verbatim [VERIFIED: dataset lines 511-517]

| Law | Meaning (dataset, Spanish) | Executable in Phase 2? (recommendation, `[ASSUMED]`) |
|---|---|---|
| Semantic Conservation | ninguna transformacion puede perder una propiedad material del outcome | YES as a READ-side invariant over a log: every `goal.revised` whose acceptance/constraints drop an item carries `weakened` + `weakening_reason` (writer rule exists at contract.py:141-151; the invariant re-checks it at read, vacuous on the two recorded logs, driven red on a synthetic log). |
| Proof Conservation | ninguna evidencia valida se vuelve a pagar hasta que una dependencia causal la invalide | PARTIAL: a pure detector `duplicate_payment(ledger)` over the NEW proof events (a second `proof.produced` for the same claim+fingerprint with no `proof.invalidated` between). Vacuous on legacy logs. The behavioural half (not re-running a gate) is Phase 4; Phase 2 must say so in the gate name (`V-PCC-LAW-PROOF-CONSERVATION-LEDGER`), not claim more. |
| Work Conservation | ningun trabajo se repite sin informacion nueva | YES, measured: `epoch.begin` already refuses a repeated `info_key` that ended UNSUCCESSFUL (epoch.py:273-279). Invariant over a log: no two epochs share an `info_key` where the first ended in `UNSUCCESSFUL`. Run it on the recorded logs as a MEASUREMENT with a named-set of legacy exceptions (an older engine may predate the refusal), never as an assumed pass. |
| Concurrency by Proof | todo trabajo causalmente independiente debe poder solaparse cuando pueda demostrarse su independencia | Only the DEFINITION lands: `independent(a, b)` true only when both declare disjoint write sets and non-colliding resource classes; any undeclared set -> not independent. The scheduler that uses it is Phase 3. |
| Unknown Escalates | cuando la independencia, cobertura o validez no pueda demostrarse, se usa el camino fuerte/completo | YES, exhaustively: certificate validity is a pure function of 6 premises, each in {equal, changed, unknown}; 3^6 = 729 combinations enumerated in one gate (INHERITED iff all six equal). Plus both kill switches off => FULL for every combination. |

Dataset quote kept for provenance [VERIFIED: dataset line 520]: UCR-CIF "ya contiene precisamente la base de Proof Conservation ... Por tanto esto no seria una filosofia nueva. Seria hacer ejecutable Verification Amortization."

### 3.2 Test-suite style to copy [VERIFIED]

- Layout of `tools/test_gsd_x_goal_reconcile.py`: module docstring with the run command (:8), `ROOT = Path(__file__).resolve().parents[1]` + `sys.path.insert(0, str(ROOT))` (:16-17), `main()` with local `ok / bad / check(g, cond, ev, why)` closures (:58-71), gates named `V-RC-*`, temp dir `base = Path(tempfile.mkdtemp(prefix="gsdx_rc_"))` passed as `GoalLog(REPO, gid, base=base)` (:73, :34). Builders use only the public writers: `gc.declare`, `cv.set_plane` over `cv.PLANES`, `cv.accept_obligation`, `cv.satisfy` with `mcl.Verdict(...)` (:33-49).
- Summary line, verbatim shape, from every suite: `print(f"\nGSDX_RECONCILE_PASS={len(passes)}/{total}  threshold={total}/{total}")` (reconcile.py:198 of the suite file; the same line in chaos :276, cli :235, convergence :237, epoch :205, gate_provider :219, judge :194, sweep :193, sweep_all :143-144). Exit code is nonzero when `fails`.
- Hermetic HOME: `tools/test_family_injection.py:78-84`: `home = tempfile.mkdtemp(prefix="finj-home-")`, `env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")`, `os.environ.update(HOME=home, USERPROFILE=home)`, and the FIRST gate asserts it: `check("V-FINJ-HERMETIC-HOME", Path.home() == Path(home), Path.home())`. A gate that proves the redirect took effect is the pattern to copy. `log.goals_root()` falls back to `Path.home()/.claude/state/gsd-x/goals` unless `GSDX_GOALS_ROOT` is set (log.py:100-102), so BOTH must be redirected, and the sweep's autonomy record lands in the PARENT of a goals root named `goals` (`state_dir()`, sweep.py:52-55), so give the temp goals root a `goals` leaf under its own temp parent (test_sweep does `mkdtemp(...)/"goals"`, test_gsd_x_goal_sweep.py:75-77).
- Hermetic-by-construction instrument from Phase 1: `tools/gsdx_goal_timeline.py` refuses a goals root resolving under the live `~/.claude` (`REFUSED: fixture goals root ... resolves under the live ~/.claude`, :172-174). Copy that guard into the new suite as its own gate.
- Characterization-golden precedent [VERIFIED: tools/test_gsd_mission_legacy_characterization.py:1-24]: golden at `tools/fixtures/gsd_mission_legacy_golden.json`; "captured once with `--capture` (refused when the golden already exists); its `meta` names the source sha and HEAD it was taken on. A legitimate legacy change is `--amend <scenario> --why <text>`, ... recorded in meta.amendments"; gate `V-G23-GOLDEN-PRE-CHANGE`; "Mutants (always run): four in-process mutants route a legacy record toward v2 behaviour. Each must turn the comparison red, and the clean run after them must be green again, so a comparator that sees nothing -- or a mutant that leaks -- cannot pass." This is exactly the shape D43's red case needs. Reuse the pattern; do not invent a new one.
- `tools/mutation_drill.py` limits [VERIFIED: :1-40]: spec JSON `{"file","test","gate","old","new"}` (example r01-drill.json); control on a clean copy first; outcomes KILLED/SURVIVED/UNJUDGED/HARNESS/CONTROL_INVALID; a test beside its subject gets that directory plus `DEFAULT_SIBLINGS = ("modules", "vault/pricing", "vault/config")` (:53) and `copy_dirs`. A fixture under `tools/fixtures/` is therefore copied with the suite (the suite lives in `tools/`); a fixture elsewhere needs `copy_dirs`.

## 4. Legacy replay: the recorded corpus (target 4)

All counts [VERIFIED: Glob of `NNNNNN.json` files + `du -sb` this session; READ ONLY, nothing written under `~/.claude`].

| Goal | Store path | Events | Run artifacts | Size (apparent bytes) | Types present |
|---|---|---|---|---|---|
| g-002-router-surface | `C:\Users\User\.claude\state\gsd-x\goals\4a226561feb32dc7df40388410bbde2f67e83614\g-002-router-surface` | 50 (`000001.json`-`000050.json`) | `runs/`: 6 gate runs x 3 files (`.log`, `.result.json`, `.json`) = 18 files | 49,093 total; 44,384 without `runs/` | gate epochs only + `failure.recorded` (seq 48), `failure.dispositioned` (49), `goal.judged` (50); NO `goal.autonomous` |
| g-001-smoke-runner | `C:\Users\User\.claude\state\gsd-x\goals\1f924bcabb838f1387a2afe5729e29b61891a3b4\g-001-smoke-runner` | 123 (`000001.json`-`000123.json`) | `runs/` present (not enumerated) | 155,491 total; 119,193 without `runs/` | codex + claude-interactive + gate epochs; `failure.recorded` x4 (16,48,49,50), `failure.dispositioned` x4 (86-89), `obligation.dispositioned` x1 (51), `goal.autonomous` x2 (24, 91), `goal.judged` x2 (90, 123) |

(`du -sb` counts directory entries too, so the totals are an upper bound on file bytes; the without-`runs/` figures are the ones that matter for a fixture.)

Not present in EITHER recorded log (grep with the full alternation over `0*.json`, both dirs): `goal.revised`, `goal.budget_set`, `goal.authority_set`, `obligation.carried`, `operator.pause/resume/cancel/note`, `evidence.hypothesis`. Consequence: the recorded corpus cannot, alone, prove "old logs replay unchanged" for those 9 legacy type strings (`goal.revised`, `goal.budget_set`, `goal.authority_set`, `obligation.carried`, four `operator.*`, `evidence.hypothesis`; the other 13 of the 22 appear). Add a SYNTHETIC legacy generator that drives the public writers (`contract.revise`, `set_budget`, `set_authority`, `convergence.carry_obligation`, `intervention.intervene`, `evidence.record`) to cover them, and add a population-floor gate that the union of corpus types equals the set of legacy type constants DISCOVERED by scanning `modules/gsd_x/goal/*.py` (PR-COVERAGE-BY-CONSTRUCTION: do not hand-list the 22; the "other 13 appear" count is INFERRED from the judged gates and the greps, only the 9 absences were grepped directly).

Legacy shape variance to keep (it is why a real copy beats a rebuild): g-001's `goal.autonomous` (seq 24) carries only `{"enabled": true, "reason": ...}` with NO `root` (the writer now adds `root`, sweep.py:167-172), so `autonomous_goals` reports "autonomous but no root recorded" for it (sweep.py:208-210); three g-001 gate receipts lack `cost.seconds` (01-EVIDENCE.md:142); `gate_class` is absent on early `obligation.accepted` events (convergence.py:119 `d.get("gate_class", "")`).

Mechanism (recommended, `[ASSUMED]` design, each step has a precedent):
1. **Capture once, from the unmodified engine, before any seam code.** Copy ONLY the `NNNNNN.json` files (not `runs/`: `GoalLog.read()` ignores any name not matching `EVENT_RE`, log.py:41,157-160) into `tools/fixtures/gsdx_legacy_goals/<repo-id>/<goal-id>/`. Do the copy through a temp dir first and run `GoalLog(repo, goal, base=tmp).read()` on it so a broken chain REFUSES the capture (the `cmd_recorded` pattern, gsdx_goal_timeline.py:118-129: `shutil.copytree` into `tempfile.mkdtemp(prefix="gsdx_tl_copy_")`, then `GoalLog(...).read()`, `GoalLogError` -> REFUSED exit 2).
2. **Write `MANIFEST.json`** with sha256 per file plus the chain tip digest (g-002 tip = digest of seq 50; g-001 tip = digest of seq 123), the source store path, and the capture HEAD. The replay test verifies the manifest BEFORE reading.
3. **`.gitattributes`: add `tools/fixtures/gsdx_legacy_goals/** -text`.** This clone runs `core.autocrlf=true` (root `.gitattributes:3-7` says so and byte-pins `vendor/genesis-suite/**` for the same reason). The chain digest survives CRLF (it is over parsed canonical JSON, log.py:105-112), but a file-byte manifest does not. `.gitattributes` is not under `~/.claude`, so editing it is in scope.
4. **The test copies the committed fixture into a temp `GSDX_GOALS_ROOT/<repo>/<goal>` and reads that copy** (never the committed tree in place, never the live store) -- it is the same copy-then-verify discipline the CONTEXT asks for, with the committed tree as the "store".
5. **Prefix replay.** `contract.project(log)` reads from disk (contract.py:89), so a prefix of k events is a temp dir holding files 1..k (any prefix of a valid chain is a valid chain). Replaying ALL 173 prefixes costs about sum(k) = 50*51/2 + 123*124/2 = 1,275 + 7,626 = 8,901 small file copies; either accept it (seconds) or sample at epoch/judge boundaries plus every 5th event. For `decide`, the context needs a deterministic observation model: every epoch in state `running` at prefix k gets `Observation(OBS_RUNNING)` (epoch.py:61, 86-89), `tree_hash` fixed to a constant string, `scope_hash`/`engine` constants, `providers=("gate","codex","claude-headless")`, `now` constant, as `tools/test_gsd_x_goal_reconcile.py:52-55` does.
6. **Golden = the unmodified engine's outputs** for each prefix: `GoalState` scalar fields EXCLUDING `events`, `project_convergence` (obligation dispositions, verdict tree/revision, planes, failures), `goal_closure.blocking`/`may_close`, `project_epochs` (state, outcome, receipts, fence), `project_operator`, `project_hypotheses`, `jd.current`, `is_autonomous`, and `decide(ctx)` as `(kind, reason, epoch_id, provider, hypothesis, info_key, spec)`. Capture with a `--capture` flag that REFUSES when the golden exists and when the engine already names PCC (the `V-G23-GOLDEN-PRE-CHANGE` analog), recording `meta.source_head` and `meta.engine_identity` (call `engine_identity.engine_identity(ROOT)`, engine_identity.py:139).
7. **Secrets/PII pass before commit** (governance: `governance/REPO_SECURITY_GOVERNANCE.md` is "private by default; PII/secret pre-commit greps"). g-002's intent text names an Owner credentials tool and "list-accounts"; seq 1 was read in full (no secret, but Owner-private project prose). Keep the repo private (it is) and grep the fixture for key patterns (`HR-SECRET-004/005`) as a gate in the capture script.

Budget fact for the planner's "is a committed copy reasonable" question: **173 files, about 163 KB of JSON (44,384 + 119,193 bytes), plus a manifest.** Yes, reasonable. Alternative considered: `tools/gsd_x_goal.py export` (:333-342) writes ONE JSON per goal that `restore` (:345-365) republishes through `GoalLog.publish`; it is compact and already type-agnostic, but it re-serialises (`json.dumps(indent=2)`), so it is not a byte-copy of the recorded files; prefer the byte copy for "recorded by an older engine" fidelity, and use export/restore only as a SECOND transport round-trip gate (new events survive export -> restore).

## 5. Kill switches: existing patterns in `modules/gsd_x` (target 5)

[VERIFIED by grep over `modules/gsd_x` for `os.environ|getenv|_SWITCH|"off"`]:

| Pattern | Where | Parse | Default |
|---|---|---|---|
| Opt-out env switch `CPP_FAMILY_BASELINES` | cli.py:91, 112 | `os.environ.get(FAMILY_SWITCH, "").strip().lower() in ("off", "0", "false")` -> return `""` | ON; never raises; function documented `"" when ... the switch is off, or on any error -- never raises` (cli.py:99-108) |
| Opt-in env disable `CODEX_DISABLED` | codex.py:51, 70-71, 121 | `_truthy(v)`: `str(v or "").strip().lower() in ("1", "true", "yes", "on")` | not disabled |
| Kill-switch FILE (survives a scheduler that cannot set env) | codex.py:52-53 (`~/.hermes/codex.disabled`, env `CODEX_DISABLE_FLAG`), claude.py:37-38 (`GSDX_CLAUDE_DISABLE_FLAG`, `~/.claude/state/gsd-x/claude_epochs.disabled`) | file existence | not disabled |
| Env root redirects for tests | log.py:43 `GSDX_GOALS_ROOT`; judge.py:42 `EPOCH_ENV = "GSDX_GOAL_EPOCH"` (judge refuses inside an epoch, :125-128) | non-empty | unset |

The spec names `GSDX_FRONTIER=off` and `GSDX_PROOF_INHERITANCE=off`, i.e. the `CPP_FAMILY_BASELINES` shape (value `off`). Recommended contract for the two readers (`[ASSUMED]`, to be fixed in the spec): (1) read at CALL time, never import time (tests flip `os.environ` in-process); (2) strip + lower-case; (3) ON iff unset/empty or explicitly `on|1|true|yes`; ANY other non-empty value (including a typo such as `of`, `disabled`, `OFF `-after-strip is handled by rule 2) is treated as OFF, because the OFF path is the legacy/stronger path and "Unknown Escalates" (a typo must fail toward the proven path, the opposite of `CPP_FAMILY_BASELINES`, whose typo leaves the feature ON); (4) one shared parser for both switches; (5) the switch decides at the CONSUMER boundary (proof-state projection returns "no inheritance, whole-tree binding" when off; `decide()` takes the scalar path when `GSDX_FRONTIER` is off), and the events already in the log stay readable and replayable regardless of the switch (switch off ignores `proof.inherited`, never deletes or rewrites it). Caveat for the planner: the sweep runs as a scheduled task (`PP-GoalSweep`, 01-EVIDENCE.md:297), which cannot easily inherit an interactive env var; the Codex/Claude providers solved exactly that with flag files. Decide in the spec whether an optional flag file under `sweep.state_dir()` is in scope; the minimum is the env var the spec names.

In Phase 2 nothing consumes either switch yet, so "kill switch" gates are: (a) parser truth table (unset, `on`, `off`, `OFF`, ` off `, `0`, `false`, `of`, `banana` -> expected), (b) with a switch OFF the new proof-state projection returns the legacy answer for EVERY certificate (UNKNOWN -> FULL, `inheritance_enabled() == False`), (c) a mutant that ignores the switch is KILLED.

## 6. Gaps and ambiguities in spec §Semantics for the W1 audit to close (target 6)

Each item: the concrete question, the recommended answer, the reason. Facts are `[VERIFIED]` with file:line; recommended answers are `[ASSUMED]` design decisions for the spec amendment (the worker records each as a decision in STATE.md per the ULTRA Q&A rule). Items G1-G6 resolve D01; G7-G9 resolve D10; G10-G12 resolve D43/D44; G13-G18 are cross-cutting.

**G1. What is a "candidate" before Phase 4 builds snapshots?** The spec says proof states are "on every obligation at a candidate" but candidate snapshots are Phase 4 (D23). Recommended: in Phase 2 `candidate_id` is exactly today's `tree_hash` string (`git:<oid>` | `work:<hash>` | `unknown:...`, git_state.py:124-142) and a certificate's binding is `{"scheme": "tree" | "causal", "value": ...}`. The legacy whole-tree case is then the `tree` value of the SAME field Phase 4 fills with `causal`; no schema change later. Reason: it is the only identity that exists and the scheme tag makes "unknown premise set -> legacy whole-tree binding" a value, not a branch.

**G2. The `unknown:` tree compares equal to itself (pre-existing defect that D01 depends on).** `tree_id` returns the constant `"unknown:not-a-git-tree"` on any git failure (git_state.py:131), its docstring promises "so it cannot silently match another unknown" (:125-127), but `goal_closure` (convergence.py:350) and `_needs_a_gate_here` (reconcile.py:115) compare strings, so two unknowns match. A transient git failure (the `_git` loop returns `(127, "")` when neither executable runs, :24-32) therefore makes evidence taken during one outage satisfy closure during another. Recommended: the NEW proof-state projection treats any tree string starting `unknown:` as UNKNOWN (never FRESH, never INHERITED, never equal to anything) and the spec records the legacy defect as a new DENOMINATOR row (R12) for a RED-first fix in Phase 4 (where D01 closes), NOT in this seam, because fixing it changes a legacy output. Confidence: HIGH on the code reading; MEDIUM on severity (a real goal needs a git root, log.py:84-97, so only a git outage triggers it); no test was run to drive it.

**G3. Proof state is a projection on a NEW axis, never a write to `disposition`.** The name `STALE` already exists as an OBLIGATION disposition (`STALE = "STALE"`, mission/obligation.py:40; read at convergence.py:356 and mission/closure.py:80,245) and in structured_facts.py:305 with a precise meaning ("we cannot say the fact changed, only that we can no longer check it", :351-352). Recommended: `ProofState` is a separate closed vocabulary computed per `(claim_id, candidate_id)` by a pure function; the spec states it NEVER assigns `o.disposition`; closure in Phase 2 is untouched (`goal_closure` keeps its tree/revision equality, convergence.py:347-355). Phase 4 adds the closure clause behind `GSDX_PROOF_INHERITANCE`. Reason: `goal_closure` is the `may_close` authority; any edit to it is behaviour change.

**G4. State precedence and the legacy mapping.** Recommended automaton, per obligation, at candidate C with revision R, evaluated over the six premises {claim, revision, gate_pin, fingerprint, environment, policy}, each observed as `equal | changed | unknown`:
- `changed` on ANY premise -> STALE (a known invalidation beats an unknown one);
- else `unknown` on any premise, or `unknown:` tree, or switch off, or an empty premise set -> UNKNOWN;
- else (all six equal) -> INHERITED, but ONLY if a `proof.inherited` event names the certificate (an omitted gate with no event is UNKNOWN, never INHERITED: D45);
- FRESH = a `proof.produced` (or legacy `obligation.satisfied`) whose binding equals C and revision equals R;
- STALE and UNKNOWN both route to FULL re-run; they differ only in the recorded reason.
Legacy mapping (no PCC events at all): `obligation.satisfied` with `verdict.tree_hash == C` and `verdict.revision == R` and `o.revision == R` -> FRESH; satisfied with a different tree -> STALE (binding changed); `ACCEPTED` never judged -> no proof (state not applicable, not UNKNOWN); `STALE/CANDIDATE` dispositions -> no proof. This reproduces exactly `_needs_a_gate_here` (reconcile.py:110-121) and `goal_closure` (convergence.py:347-361); a gate asserts that equivalence on both recorded logs and the synthetic set.

**G5. SUPERSEDED has no producer.** The spec lists five states but the event list (dataset §43; ROADMAP Phase 4) has only `proof.produced/inherited/invalidated`. A state nothing can reach is the "status field nobody can transition" pattern (memory `feedback_status_field_nobody_can_transition.md`). Recommended: SUPERSEDED is DERIVED, not evented: a certificate is SUPERSEDED iff a later FRESH certificate for the same `claim_id` at an equal-or-later binding has strength >= its strength under a declared order (`unit < integration < in_game < live`; any empty/unknown class is incomparable and never supersedes). The spec must also say supersession never lowers strength (root function: "proof strength never decreases"). If the audit prefers an explicit `proof.superseded` event, it needs the same strength guard at write time.

**G6. Certificate validity: what is each premise compared against?** Concrete definitions to put in the spec:
- *claim*: `claim_id = sha256(canonical({id, plane, text, done_gate, gate_pin, gate_class}))[:24]`, NOT the obligation id. `accept_obligation` has no duplicate-id guard (convergence.py:160-184) and `project_convergence` assigns `cv.obligations[d["id"]] = GoalObligation(...)` (:117), so a second `obligation.accepted` with the same id REPLACES the obligation (new gate, new pin, disposition reset to ACCEPTED). A certificate keyed on the id alone would survive a re-accept with a different gate.
- *revision*: `GoalState.revision` (contract.py:75, 99); a certificate never crosses a revision (matches `evaluate`, convergence.py:264-267, and `carry_obligation`, :187-201, which resets SATISFIED to ACCEPTED, :131-132).
- *gate pin*: exact tuple equality of `_pin(...)` (convergence.py:102-103, 282) in the pin's own scheme (`pin_scheme`, git_state.py:87-92; `blob:` vs raw sha256); mixed schemes are refused, not guessed.
- *causal fingerprint*: G7.
- *environment*: nothing exists today (engine_identity.py:21-22: "What the digest does not cover: the interpreter, git, the environment"). Recommended minimal definition: `sha256(canonical({python: sys.version_info[:3], system: platform.system(), machine: platform.machine(), tools: contract.env_deps}))`; `ENVIRONMENT_SENSITIVE` with an empty `env_deps` -> UNKNOWN (not "compatible").
- *policy*: a module constant `POLICY_VERSION: int`; certificates record it; any difference -> changed (bumping it invalidates every inherited certificate on purpose).
- Time: `proof.produced.ts` is the writer's wall clock; TTL (TEMPORAL class) is judged against the injected `ctx.now`, never `time.time()`; a certificate dated in the future beyond a stated skew -> UNKNOWN.

**G7. Causal fingerprint: premise set and algorithm are unspecified.** Recommended: `cf1:` + sha256 over `canonical(sorted([[posix_relpath, blob_oid | "ABSENT"], ...]))` where `blob_oid` is `git_state.blob_oid` (eol-normalised, git_state.py:62-75) and paths are POSIX-relative to the scope root (as `scope_hash` does, epoch.py:189). Rules: (a) a missing premise file is the token `"ABSENT"`, NOT an exception (`file_pin` raises `FileNotFoundError`, git_state.py:117, so it cannot be reused for fingerprints); (b) a directory expands to its files excluding the existing debris set (`epoch._debris`, epoch.py:194-199) and `.git`; (c) an unreadable file, a symlink escaping the root, or a path with `..` / absolute / resolving outside the root (`is_relative_to`, as engine_identity.py:116-117 does) -> the whole fingerprint is UNKNOWN; (d) an EMPTY premise set is UNKNOWN (never "unchanged"); (e) in Phase 2 and 4 premises are gate pin files + declared `causal_paths` only (no adapter exists until Phase 7, and "an adapter at SHADOW contributes nothing" per the spec); (f) UNKNOWN in any component -> UNKNOWN fingerprint -> whole-tree binding.

**G8. How is a typed proof contract attached without touching `obligation.accepted`?** Recommended: a new additive event `obligation.contract` with `{"v": 1, "claim_id", "obligation", "elements": [{"oracle", "command", "gate_pin", "causal_paths", "env_deps", "freshness_class", "risk_tags", "nondeterministic", "inheritability"}], "combine": "AND"}`. `combine` is `AND` only in Phase 2: OR/SEQUENCE/QUORUM are dataset §10 and DENOMINATOR D11 (Phase 4); an unrecognised `combine` -> the contract is UNKNOWN -> FULL. `legacy_contract(obligation)` builds the one-element contract from the obligation's own fields: `oracle = gate_class`, `command = done_gate`, `gate_pin = gate_pin`, `causal_paths = []` (so the premise set is unknown and binding falls to whole-tree), `inheritability = "never"` until a causal set exists. A later contract event may only be equal-or-stronger than the earlier one (more risk tags, stricter freshness, more causal paths); a weakening is IGNORED and reported, mirroring `contract.revise`'s weakening refusal (contract.py:141-151). Reason: D10's disposition says "legacy = 1-element contract" and "conservative defaults" (dataset §42 line 1920).

**G9. Freshness is a SECOND axis; do not extend `GATE_CLASSES`.** The spec says "Freshness classes (extend gate_class)". `GATE_CLASSES = ("unit", "integration", "in_game", "live")` (convergence.py:45) is a closed tuple validated at acceptance (convergence.py:168-169) and at dispatch (providers/gate.py:110-111) and echoed in error text; adding members changes accepted inputs and refusal messages (behaviour). Recommended: `freshness_class(obligation, verdict, contract) -> Freshness` is a pure function in the new module; `GATE_CLASSES` is pinned by a gate. Mapping (legacy, no contract): derive from the VERDICT's `gate_class` (the observation actually made; stored at convergence.py:305), falling back to the obligation's: `unit` -> DETERMINISTIC (binding stays whole-tree until a causal set exists); `integration` -> ENVIRONMENT_SENSITIVE; `in_game`/`live` and ANY obligation on the REALITY plane -> FRESH_REQUIRED (never inherited; mirrors `RUNTIME_GATE_CLASSES` and `REALITY_PLANES`, convergence.py:47-48); an EMPTY class (legacy `obligation.accepted` events carry `d.get("gate_class", "")`, :119) -> UNKNOWN freshness -> FULL; TEMPORAL and COMPOSITIONAL have no legacy mapping (only a contract can declare them). Note sweep treats an empty class as `"unit"` at dispatch (sweep.py:365) but that is a dispatch default, not evidence of class; do not copy it into the proof policy.

**G10. "Security/authorization/tenant/destructive/migration/upload claims are FRESH_REQUIRED by policy": how is a claim recognised?** Free text is gameable and the spec names no mechanism. Recommended: a CLOSED declared vocabulary `risk_tags` on the contract element (`security, authorization, tenant, destructive, migration, upload, reality, authority`); a contract that omits the field -> freshness UNKNOWN -> FULL; a deterministic keyword scan of the obligation text may only ADD `FRESH_REQUIRED`, never remove it (asymmetric on purpose: "Unknown Escalates"). Legacy obligations have no contract and whole-tree binding, so the tags are moot for them.

**G11. Event vocabulary: what exactly lands now?** CONTEXT says Phase 2 lands "their event types and projections" for Phases 3-5, but the Reality Contract forbids scaffolding with no consumer. Recommended split: LAND (constants + payload validators + pure projection + tests): `obligation.contract` (D10), `proof.produced`, `proof.inherited`, `proof.invalidated` (D01/D45). FREEZE IN THE SPEC AS A TABLE (name, owner phase, required fields, `v`) without code: `candidate.promoted` (dataset §43 "snapshot promoted"), `review.received` (Phase 5, evidence_bundle ticket), `adapter.maturity` (Phase 7, append-only, D38), `continuation.sealed` (Phase 8). Frontier, critical path and scheduling decisions are PROJECTIONS, not events (dataset §43 lines 1943-1947). A discovered-not-listed collision gate (scan every `*.py` in `modules/gsd_x/goal/` for string constants shaped `"<ns>.<name>"`, assert uniqueness and disjointness from the 22 legacy strings) protects the frozen table from later phases. Flag for the planner: if the audit insists on code for the frozen four, add them with real projections; a bare constant is vapor.

**G12. Version marker and forward compatibility.** The envelope has no version field (log.py:115-123, 126-128); `data.v` is the only lever. Recommended: every new payload carries `"v": 1`; the new projection raises `GoalLogCorrupt` for a MALFORMED v1 payload of its own types (the repo convention: "The chain proves who wrote it, not that it is well formed", contract.py:101-103) but treats `v` greater than supported as UNKNOWN (reported, not raised). Reason: a raise inside any projection on the sweep path makes `autonomous_goals` SKIP the whole goal as "unreadable" (sweep.py:202-204) and `sweep` report `skipped` (:412-413); a newer engine's event must never be able to freeze an older engine's sweep. Legacy projections never see new types, so only the new module can raise.

**G13. `epoch.begin` enforces ONE open epoch per goal at the write authority, which contradicts D06/D25 and is not mentioned in the spec.** `still_open = [...]; if still_open: raise EpochError(...)` (epoch.py:280-286), `goal_closure` blocks on open epochs WHEN GIVEN them (convergence.py:331-332; `cmd_status` passes `ep.open_epochs(s)`, gsd_x_goal.py:142, but `decide` calls `goal_closure(st, ctx.tree_hash)` without them, reconcile.py:161), and `decide` WAITs on the first running epoch (reconcile.py:131-150). The spec's "WAIT only when the execution frontier is empty while epochs are in flight" cannot be implemented without relaxing `begin`. Recommended spec text: Phase 3 relaxes the rule under `GSDX_FRONTIER` to "a goal runs one epoch at a time UNLESS every open epoch and the new one declare provably independent write sets and non-colliding resource classes (Law 4); an undeclared set is a collision". Fences stay strictly increasing per goal (`max(...)+1`, epoch.py:290) and receipts are compared against their OWN epoch's fence (epoch.py:348-355), so N concurrent epochs hold distinct fences; only the docstring concept "a successor owns this lineage" needs rewording to (goal, epoch). Phase 2 lands text and one gate that pins today's rule (so Phase 3's change is a visible RED->GREEN).

**G14. What does "decide() keeps its signature and returns the frontier's first action" mean when `decide` is a priority chain with early exits?** Pin the contract (D43): `decide(ctx: Context) -> Decision` (reconcile.py:124), `Decision` is a frozen dataclass of exactly `kind, reason, epoch_id, spec, provider, hypothesis, info_key, packet` (:49-58), `Context` fields `state, tree_hash, scope_hash, observations, judge, now, budget, providers, blocked_on, engine` (:61-74). Recommended definition: a verbatim `decide_legacy` stays callable (the `GSDX_FRONTIER=off` path); `decide(ctx)` equals `decide_legacy(ctx)` on ALL fields including `reason` (sweep prints `reason`) whenever no PCC events exist; with the switch ON and PCC events present the first action may differ in exactly one way, a WAIT replaced by the first independent justified action. Order among independent actions is legacy order (insertion order of `cv.obligations`, which `ungated[0]` already uses, reconcile.py:203-204). Phase 2 lands the signature/field pin gate; Phase 3 lands the equivalence gate.

**G15. Read/write sets "derived mechanically": from what?** A gate epoch's spec stores `{"obligation", "tree_hash", "gate": {"id","command","class","files","pin_scheme"}}` (sweep.py:364-379); nothing declares what a gate WRITES (pytest writes `__pycache__`/`.pytest_cache`, the gate provider writes `runs/`). Recommended: with no declared sets, every action conflicts with every other (UNKNOWN is not independent), so the compiled frontier degenerates to one action and `decide` equals legacy. Independence is earned only through contract-declared `causal_paths` / `env_deps` / resource classes. This keeps Phase 3's first behaviour change small and makes "unsafe parallel writes admitted" a pure RED to drive.

**G16. Who may write `proof.produced` / `proof.inherited`? (builder cannot certify)** `satisfy()`'s docstring states the discipline: "the only production caller is sweep._apply_verdicts, which takes verdicts solely from a provider's gate receipt (pinned by tools/test_task_ledger_seam.py)" (convergence.py:289-295), and `source` records epoch/provider/handle (:307-308). Recommended spec text: `proof.produced` is appended only from the gate provider's receipt path with `source`; `proof.inherited` only by the reconciler/validator after RE-DERIVING the premises from the worktree; a worker epoch never writes either; an event is a CLAIM, and the state INHERITED is computed from caller-supplied OBSERVED premises (the projection takes them as an argument, keeping it pure), never from the event's own stored values. The log is authenticated by hash chain only; `actor` is a self-asserted string (log.py:180) -- the chain proves integrity, not authorship -- so any process with write access can append a forged event, and the defence is recompute-on-validate (Phase 5), not trust.

**G17. Engine-identity and autonomy-record ripple of landing any new `.py` in `modules/gsd_x/goal/`.** `engine_identity` seeds every `*.py` under the goal package (engine_identity.py:34-39); the sweep refuses to act until `record-gates` is re-run for the engine that would run (sweep.py:112-147), and `info_key` includes the engine term (epoch.py:202-218). So landing the seam changes the engine digest of THIS worktree. `[ASSUMED]` the live `PP-GoalSweep` scheduled task runs the main checkout's tree (not this worktree), so the live autonomy record is unaffected until merge; verify before merge. The planner should list "engine digest changes; re-run `record-gates` after merge" as an Owner-visible note and must NOT run `record-gates` against the live store from this worktree (it writes `autonomy_gates.json`, sweep.py:106-108).

**G18. Bookkeeping: which denominator rows can close in Phase 2?** ROADMAP.md:100-101: "A row listed in two phases is closed by the later one; the earlier one lands its part." DENOMINATOR phase columns: D01 `2,4`, D03 `2,10`, D10 `2,4`, D43 `2`, D44 `2`. So only D43 and D44 move to DONE here; D01/D03/D10 stay OPEN with "Phase 2 part landed" evidence (D03's baseline entries are Phase 10, R09). New rows to append (never delete): R12 (`unknown:` tree equality, G2), and any gap the auditor finds that is not a spec edit.

**G19. Auditor dispatch mechanics (the contract is read-only and tool-limited).** `agents/oneshot-architect-auditor.md:4`: tools `Read, Glob, Grep, Bash, WebFetch`, `model: opus`; "Read-only -- never writes code, never edits files" (:3, :519). So the CONTEXT's "durable-output clause (write findings to a file as it goes)" cannot be done BY the auditor: the orchestrating worker must persist the returned `## Audit Result` text to `02-AUDIT.md` the moment it returns. Its output contract (:521-548) is fixed: `**Gaps found:** <count>` + numbered gaps `[<category>] title / Where / Why this matters / Suggested fix`, categories `AUTH, ENV, PATH, EDGE, INTEGRATION, REALITY-CONTRACT, COMPLETION-GATE, ANTI-CRASH, APOLLO-GRAPHQL`; zero gaps is valid (:547). Put in the prompt: the amended spec path, the files in scope with the line anchors from section 2, the instruction "Prefer Read/Grep/Glob. Avoid Bash; if shell is needed use the PowerShell tool. Bash on Windows has a documented MSYS2 bridge hang." (global CLAUDE.md), a bound (no more than N files), and that GraphQL/AUTH categories do not apply. Pre-answer the ENV category in the spec so it is not a free gap: `GSDX_FRONTIER` and `GSDX_PROOF_INHERITANCE` by name, default ON/unset, parse rule (section 5), where documented, and the test that proves each. Dispatch ALONE in its batch (global CLAUDE.md Windows rule 4); STATE.md:36 records that subagents have no PowerShell tool, which is fine for a read-only auditor. Every numbered gap must get an injected spec edit or a dispositions row; a deterministic gate (count of gap numbers in `02-AUDIT.md` equals count of disposition rows in `02-EVIDENCE.md`) makes success criterion 1 mechanical.

## Architectural Responsibility Map

(No web tiers here; the tiers are the goal spine's own layers.)

| Capability | Primary owner | Secondary | Rationale |
|---|---|---|---|
| Durable truth: append, chain, CAS | `goal/log.py` `GoalLog` | -- | Only writer of events; D44 says no second store (log.py:1-29). |
| Proof state, certificate validity, freshness, legacy contract (pure read model) | NEW `goal/proof.py` | `git_state.blob_oid`, `convergence._pin` for comparisons | Same shape as `evidence.py` / `intervention.py`: own constants, own projection over `state.events`. |
| Closure authority (`may_close`) | `convergence.goal_closure` | judge | UNCHANGED in Phase 2; Phase 4 adds a switch-guarded clause. |
| Next action | `reconcile.decide` | `sweep.sweep_goal` | UNCHANGED; Phase 3 wraps behind `GSDX_FRONTIER`. |
| Independent certification | `judge.judge` | -- | UNCHANGED; Phase 5 adds VALIDATE. |
| Kill switches | the new module's readers (consumed at the consumer boundary) | -- | env-only per spec, shared parser. |
| Legacy-replay evidence | `tools/fixtures/gsdx_legacy_goals/` + new suites in `tools/` | `tools/mutation_drill.py` | Characterization-golden pattern already in repo. |

## Standard Stack

### Core
| Library | Version | Purpose | Why standard |
|---|---|---|---|
| Python stdlib only (`hashlib`, `json`, `dataclasses`, `pathlib`, `ast`, `tempfile`, `shutil`, `os`, `platform`, `sys`) | CPython 3.12 (`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, ROADMAP.md operating constraints) | the new module, the suites, the fixture capture | every goal-spine module is stdlib-only (log.py, epoch.py, git_state.py imports read); no dependency to vet |
| Existing in-repo owners: `modules.gsd_x.goal.{log,contract,convergence,epoch,reconcile,judge,git_state,sweep,evidence,intervention,engine_identity}`, `modules.gsd_x.mission.closure` | worktree at base `fbca24fc` + Phase 1 commits | reuse, never re-implement | REUSE -> EXTEND -> CONNECT before CREATE (auditor doctrine, agents/oneshot-architect-auditor.md:106) |
| `tools/mutation_drill.py` | in repo | mutation evidence in an isolated copy with a control | ROADMAP.md operating constraints: never `mutation_probe` live mode |

### Alternatives considered
| Instead of | Could use | Tradeoff |
|---|---|---|
| Byte-copied fixture of the recorded logs | `tools/gsd_x_goal.py export` JSON (one file per goal) | compact, round-trips through `restore`, but re-serialised so not "as recorded"; use as a second transport gate only |
| Committed fixture | generate everything with public writers | cannot reproduce older-engine shapes (no `root` on `goal.autonomous`, missing `cost.seconds`, absent `gate_class`) |
| One big suite | two suites (semantics, replay) | replay is heavier (many prefix copies); two keeps the per-task quick loop short |

**Installation:** none. **Version verification:** not applicable (no external packages).

## Package Legitimacy Audit

No external packages are installed or recommended in this phase (stdlib + in-repo modules only), so the `gsd_run query package-legitimacy check` gate has nothing to evaluate. **Packages removed due to [SLOP]:** none. **Packages flagged [SUS]:** none. (If the planner adds one, it is `[ASSUMED]` until verified and needs a `checkpoint:human-verify`.)

## Architecture Patterns

### System architecture diagram (data flow)

```
 writers (existing, UNCHANGED)                     NEW (Phase 2, additive)
 contract/convergence/epoch/judge/sweep/...         proof.py writers: obligation.contract,
        |  GoalLog.append(state.last_seq+1, ...)            proof.produced/inherited/invalidated
        v                                                   |  same GoalLog.append (CAS, chain)
 +-----------------------------+<---------------------------+
 | GoalLog  NNNNNN.json chain  |   read(): verifies seq gap / digest / prev_digest, ignores type+data
 +-----------------------------+
        | state = contract.project(log)  (last_seq, events; unknown types skipped)
        +--> project_convergence --> goal_closure --> reconcile.decide --> sweep   (legacy path, bit-identical)
        +--> project_epochs ------/                    judge.current / judge.judge
        +--> proof.project_*(state, observed_premises) --> ProofState per (claim_id, candidate)   (NEW, pure)
                      ^                                         |
                      |                                         +--> NOT consumed by closure/decide in Phase 2
        env: GSDX_FRONTIER / GSDX_PROOF_INHERITANCE  (read at call time; OFF => legacy answer)

 verification plane:  tools/fixtures/gsdx_legacy_goals (byte copy + MANIFEST) --copy--> temp GSDX_GOALS_ROOT
                      --prefix replay--> legacy projections + decide  ==  golden captured BEFORE the seam
```

### Recommended structure
```
modules/gsd_x/goal/proof.py                   # NEW: constants, validators, projections, switches
tools/test_gsd_x_goal_pcc_semantics.py        # NEW: truth tables, laws, switches, contract/freshness, scanners
tools/test_gsd_x_goal_pcc_replay.py           # NEW: golden replay, ignore-new-types, mutants, manifest
tools/fixtures/gsdx_legacy_goals/<repo>/<goal>/NNNNNN.json  + MANIFEST.json   # NEW (byte copy)
tools/fixtures/gsdx_legacy_replay_golden.json # NEW (captured pre-seam)
.gitattributes                                # EDIT: tools/fixtures/gsdx_legacy_goals/** -text
vault/liveness/reachability_registry.json     # EDIT: declare gsd_x/goal/proof PLANNED (+OWNER_QUEUE), precedent :442-453
vault/specs/gsdx-proof-conserving-convergence.md   # EDIT: §Semantics resolved + audit injections
```
Names are Claude's-discretion suggestions; the invariant is "no legacy file edited".

### Pattern 1: owner-module event + pure projection [VERIFIED shape: evidence.py:36, 66-85; intervention.py:54-76]
```python
# modules/gsd_x/goal/proof.py  (sketch of the SHAPE; values must be re-checked by the executor)
PRODUCED, INHERITED_EV, INVALIDATED = "proof.produced", "proof.inherited", "proof.invalidated"
CONTRACT = "obligation.contract"
NEW_TYPES = frozenset({CONTRACT, PRODUCED, INHERITED_EV, INVALIDATED})
SUPPORTED_V = 1

def project_proofs(state):                     # state: contract.GoalState
    out = {}
    for ev in state.events:
        if ev.type not in NEW_TYPES:           # foreign / legacy / future types: ignored, like intervention.py:57-58
            continue
        d = ev.data
        try:
            v = int(d["v"])
            if v > SUPPORTED_V:                # newer writer: UNKNOWN, never raise (G12)
                out.setdefault("unsupported", []).append(ev.seq); continue
            ...                                # fold into per-claim records
        except (KeyError, TypeError, ValueError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} ({exc})") from exc
    return out
```
The raise message format copies convergence.py:139-141 / epoch.py:256-258.

### Pattern 2: exhaustive truth table as the "Unknown Escalates" gate
Enumerate `itertools.product(("equal", "changed", "unknown"), repeat=6)` (729 combinations) over the six premises; assert `INHERITED` iff all equal AND an event exists; any `changed` -> STALE; else any `unknown` -> UNKNOWN; and with either switch off every combination -> not INHERITED. Positive control: one all-equal-with-event combination must be INHERITED (a gate that returns UNKNOWN for everything passes every refusal assertion, rule from `~/.claude/rules/generated-content-needs-an-evidence-gate.md`: "Pair every refusal with a control in which the fact exists and the claim is admitted").

### Pattern 3: characterization golden with refuse-to-recapture [VERIFIED: tools/test_gsd_mission_legacy_characterization.py:1-24]
`--capture` writes the golden once from the unmodified engine and REFUSES if it exists or if the engine already contains PCC; `--amend <scenario> --why <text>` is the only legitimate change; in-process mutants must turn the comparison red and the clean run afterwards green.

### Anti-patterns to avoid
- **Editing any legacy goal file** (even to export a constant or add a type to a ladder): it is the red case, and it voids "zero behaviour change" by construction.
- **Assigning a proof state to `o.disposition`** (name collision with `STALE`, mission/obligation.py:40).
- **A `compile_frontier` stub or an `inherit()` writer with no reader** in Phase 2: scaffold with no consumer (Reality Contract; liveness).
- **Hand-listing the legacy event types** in the test: discover them by scanning the package (PR-COVERAGE-BY-CONSTRUCTION, CLAUDE.md Liveness corollary).
- **Putting a new field in the envelope**: `Event.from_dict` drops unknown top-level keys (log.py:126-128) while `read()` still includes them in the digest check (log.py:171), so the field would verify and then vanish on any `Event` round-trip.
- **Interleaving new events and comparing seq-valued fields** (see pitfall 3).
- **Treating a green suite as proof of "no change"**: drive the mutants.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Durable append + ordering + tamper detection | a second file/DB/cache for proofs (D44) | `GoalLog.append` / `publish` | CAS, fsync, hash chain, three-outcome write (log.py:180-241) |
| Text-stable content id | raw sha256 of bytes | `git_state.blob_oid` | eol-normalised, equals `git hash-object` on any host (git_state.py:62-75) |
| Gate pin comparison | string equality of digests | `convergence._pin`, `git_state.pin_scheme`, `digest_matches` | scheme-aware, mixed schemes refused (git_state.py:87-98) |
| Canonical JSON | ad hoc `json.dumps` | same params as `log._canonical`: `sort_keys=True, ensure_ascii=False, separators=(",", ":")` (log.py:105-107) | one canonical form across the engine |
| Debris filtering | own ignore list | `epoch._debris` / `_DEBRIS_DIRS` (epoch.py:194-199) | already agreed with `scope_hash` |
| Tree identity | recompute | `git_state.tree_id` | the incumbent identity; its quirks are listed in G2 |
| Isolated mutation evidence | editing live files | `tools/mutation_drill.py` | isolated copy + control + live-file sha check (:13-22) |
| Golden capture/amend flow | a new comparator | the characterization pattern | already reviewed in this repo |
| Hash-verified copy of a store | `Copy-Item` and hope | `shutil.copytree` + `GoalLog.read()` + manifest sha256 | `cmd_recorded` pattern |
| Engine identity | new digest | `engine_identity.engine_identity` | already discovers its closure |

**Key insight:** the seam's value is not new machinery, it is a measured PROOF that nothing old moved. Spend the effort on the differential gate, not the projection.

## Runtime State Inventory

Not a rename/refactor phase, but it migrates nothing and writes into a live-looking store path, so the five categories are answered explicitly:

| Category | Items found | Action required |
|---|---|---|
| Stored data | Live goal store `~/.claude/state/gsd-x/goals/<repo>/<goal>/` holds g-001 (123 events) and g-002 (50 events) plus others; `autonomy_gates.json` and `sweep_heartbeat.json` sit in the parent (sweep.py:52-62, 218-222). | READ-ONLY. Capture a byte copy once; tests use a temp `GSDX_GOALS_ROOT`; guard SAME-before/after with `tools/gsdx_reality_baseline.py` fingerprint (Phase 1 used it, 01-EVIDENCE.md:139) if any command touches the live store. |
| Live service config | Scheduled task `PP-GoalSweep` runs the sweep (01-EVIDENCE.md:297); heartbeat file changes on every run. | None. `[ASSUMED]` it runs the main checkout, not this worktree; verify before merge (G17). |
| OS-registered state | The same scheduled task; no registration is created by this phase. | None. |
| Secrets / env vars | New env vars `GSDX_FRONTIER`, `GSDX_PROOF_INHERITANCE` (names from the spec). No secrets. | Document by name in spec + module docstring (pre-answers the auditor's ENV category). |
| Build artifacts | Adding a `.py` under `modules/gsd_x/goal/` changes `engine_identity` (engine_identity.py:39) and therefore any recorded autonomy record for THIS tree. | Record in EVIDENCE.md; re-run `record-gates` only after merge, never against the live store from here. |

## Common Pitfalls

### Pitfall 1: golden captured after the seam
**What goes wrong:** the golden is produced by the new engine, so it can only agree with it. **How to avoid:** capture first, commit the golden before the first new `.py`, record `meta.source_head`, and gate `V-PCC-GOLDEN-PRE-CHANGE` refuses a capture on a tree whose goal package names PCC. **Warning sign:** golden commit is later than the module commit in `git log`.

### Pitfall 2: `engine_identity` moves and everything keyed on it looks "new"
See G17. **Warning sign:** `tools/test_gsd_x_goal_engine_identity.py` (14/14) or sweep suites fail only after adding a file; they should not (the identity suite asserts closure membership by name, not file count, :63-77), but run them first.

### Pitfall 3: seq-valued fields shift when new events are interleaved
Fields that store a sequence number: `GoalState.last_seq` and `revisions: [(seq, revision)]` (contract.py:76, 79, 104), `cv.failures[id]["seq"]` (convergence.py:135), `OperatorState.last_seq` and `notes` tuples (intervention.py:49, 51, 62, 72), `Hypothesis.history` (evidence.py:60, 81). An "ignore new types" gate that inserts events mid-log must mask exactly this named list, or compare only append-at-end. **Warning sign:** a gate green at the end of the log and red with interleaving.

### Pitfall 4: CRLF rewrite of fixtures (autocrlf=true clone)
See section 4 step 3. **Warning sign:** the manifest sha256 differs between a fresh clone and the capture machine while the chain still verifies.

### Pitfall 5: an in-process mutant leaks into the clean run
The precedent runs a clean pass AFTER the mutants so a leak is visible (characterization test header :21-24). Restore every monkeypatch in `finally`.

### Pitfall 6: wide suites and the memory-pressure reaper
The mutation suite was killed by the harness reaper at 3.4-3.8 GB free (01-EVIDENCE.md:125, 130) and is UNKNOWN. Do not put `test_gsd_x_goal_mutation.py` in any Phase 2 gate; state it as carried (R11) and keep the new suites small. `test_gsd_x_goal_cli.py` alone is 53.4 s (01-EVIDENCE.md:113).

### Pitfall 7: a raising projection freezes the sweep for that goal
`autonomous_goals` catches `GoalLogError` and SKIPS the goal (sweep.py:202-204); `sweep` does the same (:410-413). Only the NEW module may raise on new types; legacy projections must stay ignoring.

### Pitfall 8: PowerShell 5.1 and JSON anchors
`mutation_drill.py` carries anchors in a JSON spec because PowerShell 5.1 strips double quotes from native argv (mutation_drill.py:39). Every drill is a committed `*.json` spec like `r01-drill.json`.

### Pitfall 9: heredoc / non-ASCII in commit messages
One msgfile per commit (`git commit -F`), verify `git log -1 --format=%s` (ROADMAP operating constraints; global anti-overlap caveat on the shared COMMIT_EDITMSG race).

## Code Examples

### Hermetic goal store (copy of the proven pattern)
```python
# Source: tools/test_gsd_x_goal_sweep.py:75-77 and tools/test_family_injection.py:78-84 (read this session)
home = tempfile.mkdtemp(prefix="pcc-home-")
os.environ.update(HOME=home, USERPROFILE=home)
goals_root = Path(tempfile.mkdtemp(prefix="pcc-goals-")) / "goals"
os.environ["GSDX_GOALS_ROOT"] = str(goals_root)
check("V-PCC-HERMETIC-HOME", Path.home() == Path(home), Path.home())
```

### Copy-then-verify a recorded goal
```python
# Source: tools/gsdx_goal_timeline.py:118-129 (read this session)
src = Path(store) / repo / goal
base = Path(tempfile.mkdtemp(prefix="gsdx_tl_copy_"))
shutil.copytree(src, base / repo / goal)
events = GoalLog(repo, goal, base=base).read()      # GoalLogError -> REFUSED, never "empty"
```

### Prefix of a valid chain is a valid chain
```python
# Source reasoning: log.py:152-178 (chain verified from GENESIS up to the last file present)
for k in boundaries:
    d = tmp / repo / goal; d.mkdir(parents=True)
    for n in range(1, k + 1):
        shutil.copy2(fixture / f"{n:06d}.json", d / f"{n:06d}.json")
    state = contract.project(GoalLog(repo, goal, base=tmp))
```

### Mutation drill spec (one per mutant class)
```json
{"file": "modules/gsd_x/goal/convergence.py", "test": "tools/test_gsd_x_goal_pcc_replay.py",
 "gate": "V-PCC-REPLAY-IGNORE-NEW-TYPES",
 "old": "            elif ev.type == FAILURE_DISPOSITIONED:",
 "new": "            elif ev.type == FAILURE_DISPOSITIONED or ev.type.startswith('proof.'):"}
```
(Shape from `.planning/workstreams/gsdx-pcc/phases/01-.../r01-drill.json`; the anchor must be re-read at execution time.)

## State of the Art

| Old approach | Current approach | Impact |
|---|---|---|
| Evidence valid iff `verdict.tree_hash == tree` (whole HEAD tree when clean) | certificate with causal fingerprint, whole-tree as the unknown fallback | Phase 4 behaviour; Phase 2 only defines it |
| `decide()` one action, WAIT on first running epoch | frontier first action, WAIT only when execution frontier empty | Phase 3 |
| Judge re-runs every satisfied gate serially (judge.py:147-179) | VALIDATE or REPLAY, replays bounded-concurrent | Phase 5 |

**Deprecated/outdated:** none removed in Phase 2 (zero behaviour change).

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | `changed` beats `unknown` in state precedence (STALE over UNKNOWN); both route FULL | G4 | cosmetic: only the recorded reason differs |
| A2 | Strength order `unit < integration < in_game < live`; empty/unknown incomparable | G5 | wrong order could let a weaker proof supersede a stronger; audit must confirm |
| A3 | SUPERSEDED is derived, not evented | G5 | if the Owner wants an explicit event, add a strength-guarded writer |
| A4 | Environment fingerprint = {python version, system, machine, declared tools} | G6 | too weak -> false INHERITED on a toolchain change; mitigated by ENVIRONMENT_SENSITIVE needing declared `env_deps` |
| A5 | Kill-switch parse: unset/empty/`on|1|true|yes` = ON, anything else = OFF | section 5 | differs from `CPP_FAMILY_BASELINES` (typo leaves ON); a typo disabling the optimisation is safe, a typo enabling it is not |
| A6 | Land only proof/contract events now; freeze Phase 3-8 events in the spec | G11 | CONTEXT wording says "land their event types"; planner must confirm or add real projections |
| A7 | The live `PP-GoalSweep` runs the main checkout, not this worktree | G17, Runtime State | if it runs this tree, landing the seam stales the live autonomy record immediately |
| A8 | `candidate_id` = today's `tree_hash` string in Phase 2 | G1 | Phase 4 may want a different key; scheme tag limits the damage |
| A9 | `risk_tags` closed vocabulary; text scan only escalates | G10 | vocabulary may miss a domain; the escalate-only scan is the backstop |
| A10 | `data.v` marker; `v` > supported -> UNKNOWN not raise | G12 | a malformed-vs-newer ambiguity could hide corruption; malformed v1 still raises |
| A11 | Prefix replay of all 173 prefixes (8,901 small copies) takes seconds | section 4 | unmeasured; sample at boundaries if it does not |
| A12 | `claim_id` composition `{id, plane, text, done_gate, gate_pin, gate_class}` | G6 | too narrow/broad changes when a certificate invalidates |
| A13 | Work Conservation may show legacy exceptions in g-001 (older engine) | section 3.1 | the gate must be a named-set measurement, not an assumed pass |
| A14 | `unknown:` equality only bites on a git outage | G2 | severity could be higher if non-git scope roots are used; not driven |
| A15 | Auditor output can be made mechanical by gap-count == disposition-count | G19 | the auditor's numbering may contain sub-items |

## Open Questions (RESOLVED -- see STATE.md Decisions, 2026-10-07 worker epoch 3)

All five are resolved by the worker's recorded decisions (STATE.md, "Phase 2 research open questions"): (1) land
only `obligation.contract` + `proof.*`, freeze the rest in the spec; (2) commit the byte copy behind a secret/PII
gate; (3) G2 -> DENOMINATOR R12, Phase 4; (4) env-only switches, unrecognised value = OFF; (5) mutation suite
excluded (R11).

1. **Land the Phase 3-8 events as code, or freeze them in the spec only?** Known: CONTEXT says Phase 2 lands "their event types and projections"; Reality Contract bars a constant with no projection. Unclear: whether the Owner's intent for D03/D43 needs the extra types now. Recommendation: spec table + collision gate now (G11); add code with real projections only if the audit demands it.
2. **Commit the recorded logs, or only a generator?** Known: 173 files, about 163 KB, Owner-private intent prose (g-002 seq 1), repo is private. Recommendation: commit the byte copy with the secret/PII grep gate; the generator covers the six uncovered legacy types.
3. **Fix the `unknown:` equality defect (G2) in this phase?** Recommendation: no (behaviour change); R12 row + Phase 4 RED.
4. **Flag file for the kill switches?** Recommendation: env only in Phase 2 as the spec states; decide the flag-file extension when Phase 3 lands the first consumer (the scheduler cannot set env interactively).
5. **`test_gsd_x_goal_mutation.py` count.** UNKNOWN (R11); Phase 2 neither asserts nor regresses it; run in-copy only if RAM allows, else record UNJUDGED.

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.12 | all suites | yes (ROADMAP path; Phase 1 ran suites with it) | 3.12 | -- |
| git (absolute path) | `tree_id`, `file_pin` in fixtures | yes (Phase 1 ran the CLI fixture through it) | -- | -- |
| Live goal store (read-only) | one-time fixture capture | yes: Glob listed both goals this session | 50 / 123 events | none needed after capture |
| `oneshot-architect-auditor` agent | ULTRA phase 4 | yes: `agents/oneshot-architect-auditor.md` exists in the worktree | opus | inline adversarial review, recorded as degraded |
| PowerShell tool | git/python from the worker | yes for the main session; subagents lack it (STATE.md:36) | -- | main session runs everything; auditor is read-only |
| Free RAM | suites | 3.4-3.8 GB measured in Phase 1 | -- | avoid the mutation suite (Pitfall 6) |
| `du`/POSIX tools | not required | n/a (only used by this research) | -- | -- |

**Missing with no fallback:** none. **Missing with fallback:** none identified.

## Validation Architecture

`workflow.nyquist_validation` is absent from `.planning/config.json` (verified: only `hooks` and `workflow.skip_discuss`), so this section is required.

### Test framework
| Property | Value |
|----------|-------|
| Framework | none (no pytest): plain Python script suites with `ok/bad/check` closures, one summary line `<SUITE>_PASS=n/m  threshold=n/m`, exit 1 on any FAIL (tools/test_gsd_x_goal_*.py, 17 incumbents) |
| Config file | none; each suite sets `sys.path` from `Path(__file__).resolve().parents[1]` |
| Quick run | `python tools/test_gsd_x_goal_pcc_semantics.py` + reconcile (1.3 s) + convergence (3.0 s) + epoch (0.4 s) = about 5 s cold; add `test_gsd_x_goal_judge.py` (9.0 s) when `judge.py` imports change (times from 01-EVIDENCE.md:108-124) |
| Full suite | all 17 incumbents (sum cold 154.1 s, 01-EVIDENCE.md:132) + both new suites + `python modules/liveness/reachability.py` |

### Phase requirements -> test map
| Req | Behaviour | Test type | Command / gate | Red case that MUST be driven and seen red |
|-----|-----------|-----------|----------------|-------------------------------------------|
| D01 | proof-state automaton: FRESH/INHERITED/SUPERSEDED/STALE/UNKNOWN, UNKNOWN->FULL | unit, exhaustive | `V-PCC-STATE-TRUTH-TABLE` (729 combos + positive control), `V-PCC-STATE-LEGACY-MAP` (equals `_needs_a_gate_here` / `goal_closure` on both recorded logs + synthetic), `V-PCC-STATE-NO-EVENT-NOT-INHERITED`, `V-PCC-STATE-UNKNOWN-TREE` (`unknown:` -> UNKNOWN even when equal), `V-PCC-STATE-NOT-IN-DISPOSITION` (static) | mutants: treat `unknown` as `equal`; INHERITED without event; assign `o.disposition`; each via drill spec, KILLED for the named gate |
| D01 | certificate validity six premises incl. re-accept changes `claim_id` | unit | `V-PCC-CERT-CLAIM-REACCEPT`, `V-PCC-CERT-GATE-PIN-SCHEME`, `V-PCC-CERT-REVISION`, `V-PCC-CERT-POLICY-BUMP`, `V-PCC-FINGERPRINT-*` (ABSENT token, outside-root path -> UNKNOWN, empty set -> UNKNOWN, CRLF==LF) | mutant: fingerprint raises on missing file / ignores `..` |
| D10 | legacy done_gate is a one-element contract; contract weakening ignored; freshness map | unit | `V-PCC-CONTRACT-LEGACY-ONE-ELEMENT` (every obligation in both logs + synthetic: 1 element, `command == done_gate`, `gate_pin` equal, whole-tree binding), `V-PCC-CONTRACT-WEAKENING-IGNORED`, `V-PCC-CONTRACT-MALFORMED-RAISES`, `V-PCC-CONTRACT-HIGHER-V-UNKNOWN`, `V-PCC-FRESHNESS-MAP`, `V-PCC-GATE-CLASSES-PINNED` | mutant: edit `GATE_CLASSES` (the "extend gate_class" misreading) -> pinned gate red; mutant: text scan removes FRESH_REQUIRED |
| D43 | legacy replay unchanged; `decide` signature kept; no legacy file edited | integration / differential | `V-PCC-REPLAY-G002`, `V-PCC-REPLAY-G001` (every sampled prefix vs golden), `V-PCC-REPLAY-SYNTHETIC` (the 9 uncovered legacy type strings), `V-PCC-REPLAY-IGNORE-NEW-TYPES` (append one event of each new type; legacy projections equal golden except `last_seq`/`len(events)`; interleaved variant masks the named seq list), `V-PCC-DECIDE-SIG`, `V-PCC-NO-LEGACY-EDIT` (PHASE-2-SCOPED: an EVIDENCE.md command, `git diff --name-status <pre-seam commit>..<phase end> -- modules/gsd_x` lists only `A` rows, plus the replay golden's `meta` recording sha256 of each legacy goal file at capture; do NOT make it a permanent suite gate, Phases 3-5 legitimately edit those files and would have to `--amend` the golden each time, which is the intended review point but must be a stated step), `V-PCC-GOLDEN-PRE-CHANGE`, `V-PCC-FIXTURE-MANIFEST` (flip one byte -> REFUSED), `V-PCC-HERMETIC-HOME`, `V-PCC-LIVE-STORE-UNTOUCHED` (fingerprint SAME), incumbent suites at Phase 1 counts | in-process mutants (always run, clean pass after): M1 a legacy projection raises on an unknown type; M2 `project_convergence` counts a new type; M3 `decide` consults a proof event; M4 obligation order changes. Each must turn REPLAY red. Plus one on-disk drill: `else: raise` appended to the `project_convergence` ladder |
| D44 | event log, not a second DB | invariant (static + dynamic) | `V-PCC-NO-SECOND-STORE` (AST scan of new modules: no `open(.., "w"/"a"/"x")`, `write_text`, `write_bytes`, `sqlite3`, `shelve`, `pickle.dump`, `os.replace`, `os.rename`, `tempfile` writes outside tests; only `GoalLog.append`; positive control: scanner flags a synthetic offender), `V-PCC-ADDITIVE-ONLY` (new types disjoint from the 22 legacy, discovered by AST scan; positive control), `V-PCC-PROJECTION-PURE` (dir listing + mtimes unchanged across a projection call), `V-PCC-ENVELOPE` (new events read back through `GoalLog.read()` with the 7-field envelope), `V-PCC-EXPORT-RESTORE-ROUNDTRIP` (new events survive `export` -> `restore`) | mutant: a projection writes a cache file -> `NO-SECOND-STORE`/`PROJECTION-PURE` red |
| D03 | five laws executable | unit | `V-PCC-LAW-SEMANTIC`, `V-PCC-LAW-PROOF-CONSERVATION-LEDGER`, `V-PCC-LAW-WORK-CONSERVATION` (named-set measurement on the corpus), `V-PCC-LAW-CONCURRENCY-DEF` (`independent()` false when any set undeclared), `V-PCC-LAW-UNKNOWN-ESCALATES` | each law has a synthetic violating log/input that turns its gate red; baseline entries are Phase 10 (R09) |
| D01/D43 | kill switches | unit | `V-PCC-SWITCH-PARSE` (unset, `on`, `off`, `OFF`, ` off `, `0`, `false`, `of`, `banana`), `V-PCC-SWITCH-OFF-IS-LEGACY` (every certificate combo -> not INHERITED when `GSDX_PROOF_INHERITANCE` off) | mutant: reader ignores the env var |
| (success criterion 1) | audit complete and injected | doc gate | `V-PCC-SPEC-RESOLVED` (each required §Semantics item has a resolved marker; the text "nothing below is final until the W1 audit" is replaced), `V-PCC-AUDIT-DISPOSED` (numbered gaps in `02-AUDIT.md` == disposition rows in `02-EVIDENCE.md`) | remove one disposition -> red |
| (liveness) | new module declared | tool | `python modules/liveness/reachability.py` -> `gate offenders: 0`, exit 0 | -- |

### Sampling rate
- **Per task commit:** quick run above (about 5-14 s).
- **Per wave merge:** all 17 incumbents + both new suites + liveness.
- **Phase gate:** full suite green with Phase 1 counts (reconcile 22, judge 11, convergence 29, sweep 14, epoch 19, chaos 15, mutation_safety 8, gate_provider 18, goal 26, bind_mission 10, claude_providers 20, cli 25, codex 18, engine_identity 14, gate_class 11, long_run 16, sweep_all 11; mutation suite UNKNOWN/R11) before `/gsd-verify-work`; plus the drills.

### Wave 0 gaps (must exist before any seam code)
- [ ] fixture capture tool/step + `tools/fixtures/gsdx_legacy_goals/**` + `MANIFEST.json` + `.gitattributes` `-text` line;
- [ ] `tools/fixtures/gsdx_legacy_replay_golden.json` captured from the UNMODIFIED engine (commit it BEFORE `proof.py`);
- [ ] `tools/test_gsd_x_goal_pcc_replay.py` RED-first: it must already fail for the right reason (missing module / missing golden) before the seam lands, as `903005c2 test(gsdx-pcc-01): RED -- V-RB gates ... (tool absent)` did in Phase 1;
- [ ] amended spec + `02-AUDIT.md` (audit text persisted by the orchestrator) before code, so the code implements the audited semantics.

## Security Domain

`security_enforcement` is absent from config (treated as enabled). This is an internal, offline, stdlib-only library plus test tooling: no network, no auth surface, no secrets handled.

| ASVS category | Applies | Standard control |
|---|---|---|
| V2 Authentication / V3 Session | no | -- |
| V4 Access control | partially | write authority is by code path, not identity: `actor` is a self-asserted string (log.py:180), the chain gives integrity not authorship; mitigation = recompute-on-validate (G16), never trust a stored `proof.inherited` |
| V5 Input validation | yes | payload validators with `v` marker (G12); causal paths rejected if absolute, containing `..`, or resolving outside the root (`is_relative_to`, engine_identity.py:116-117 pattern) |
| V6 Cryptography | yes | `hashlib.sha256` only; no hand-rolled hashing; canonical JSON params as `log._canonical` |
| V8 Data protection | yes | committed fixture carries Owner-private prose: private repo + key-pattern grep gate (HR-SECRET-004/005) |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Forged `proof.inherited` / `proof.produced` appended by a worker (builder self-certification) | Tampering / Spoofing | state computed from OBSERVED premises, event is a claim; producer authority named in spec (G16); judge recomputes (Phase 5) |
| Path traversal via declared `causal_paths` | Tampering / Info disclosure | relative-only, no `..`, resolve inside root, else UNKNOWN fingerprint |
| A newer-version event freezing an older sweep | Denial of service | `v` > supported -> UNKNOWN, not raise (G12, Pitfall 7) |
| Tampered fixture | Tampering | manifest sha256 verified before read; chain verified by `GoalLog.read()` |
| Writing the live store from a test | Tampering | hermetic HOME + `GSDX_GOALS_ROOT` + refusal when the root resolves under `~/.claude` + SAME fingerprint gate |

## Sources

### Primary (HIGH: read in source this session)
- `modules/gsd_x/goal/{log,contract,convergence,epoch,reconcile,judge,git_state,sweep,intervention,evidence,engine_identity,__init__}.py`; `modules/gsd_x/cli.py:80-140`; `modules/gsd_x/goal/providers/{codex,claude}.py` (grep); `modules/gsd_x/mission/obligation.py` (grep)
- `tools/gsd_x_goal.py:120-219, 320-390`, `tools/gsdx_goal_timeline.py:1-240`, `tools/test_gsd_x_goal_reconcile.py:1-120`, `tools/test_family_injection.py:60-110`, `tools/test_gsd_mission_legacy_characterization.py:1-200`, `tools/mutation_drill.py:1-80`
- `vault/specs/gsdx-proof-conserving-convergence.md`; `.planning/workstreams/gsdx-pcc/{ROADMAP,STATE,DENOMINATOR}.md`; `.../phases/01-.../01-EVIDENCE.md`, `r01-drill.json`; `02-CONTEXT.md`
- `agents/oneshot-architect-auditor.md`; `.gitattributes`; `vault/liveness/reachability_registry.json:436-457`
- Dataset `C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md` §1, §2 (453-527), §3-§6 (529-697), §9-§14 (784-1034), §42-§44 (1894-1983)
- Live store, READ ONLY: Glob of event files and `du -sb` of `~\.claude\state\gsd-x\goals\<repo>\g-00{1,2}-*`; full read of g-002 `000001.json` and g-001 `000024.json`

### Secondary / Tertiary
- None. No web or Context7 sources were needed (no external library). `01-PREMISES.md`, `REQUIREMENTS.md`, `tools/test_task_ledger_seam.py`, `brief.py` internals and the `test_gsd_x_goal_mutation.py` body were NOT read (read budget); claims that depend on them are marked or avoided.

## Metadata

**Confidence breakdown:**
- GoalLog / projections / consumers (sections 1-2): HIGH, every line read.
- Corpus facts (section 4): HIGH for counts (Glob), MEDIUM for byte sizes (`du -sb` includes directory entries).
- Test style and patterns (section 3): HIGH.
- Gap list recommendations (section 6): MEDIUM (design decisions, `[ASSUMED]` per the Assumptions Log).
- Not exercised: nothing was executed (read-only research); no suite was run, no replay was performed, G2 and A11 are unmeasured.

**Research date:** 2026-10-07. **Valid until:** the first commit that edits any `modules/gsd_x/goal/*.py` or the spec (line numbers are for base `fbca24fc` plus Phase 1 commits).

