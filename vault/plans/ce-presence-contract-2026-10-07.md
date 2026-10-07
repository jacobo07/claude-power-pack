---
covers: [ce-presence-contract, baseline-resolver, route-null-default, misconfiguration-immunity, legacy-exception, cognitive-ci-route-null]
status: PROPOSED (awaiting one Owner approval; phrase at the end)
extends: goal ce-a3 (Amendment A3 5617f901) + CAA plan 3fe39764 (PROPOSED) + cep-gen4 f14f33a5 (APPROVED)
source: interactive planner pane 77cfae43, read-only scan, 2026-10-07
---

# CE Presence Contract: absent configuration resolves to the certified baseline, never to the host maximum

## 1. Verified reality (MEASURED from source unless marked)

Root cause, as written in code: `tools/gsd_mission.py:271`, "None -> the host's own defaults for that setting".
Every optimisation field on a mission record is opt-in, so an omitted field means host maximum:

| Field on the record | When absent, the worker gets | Evidence |
|---|---|---|
| `worker_profile` / admitted route | `claude --bg` full session (first-call floor 110,835) instead of slim-t2 (13,507) | `slim_profile()` :697-704, `route-floors.json` |
| `model` | host default model (Opus, 1M) | `worker_argv` :771-774 (only `if rec.get("model")`) |
| `autocompact` | `AUTOCOMPACT_SAFETY_NET = "600k"` | :656, :781 |
| `wu_packet` | generic `/gsd-autonomous` briefing; admission not judged | `admission_refusal` :1425-1427 |
| `continue_max_tokens` | unset (no continuation ceiling) | set only by `envelope` :1339 |
| `token_estimate` | **auto envelope since 03e1b0c3 (T1c)**: the only default-on CE layer | `_auto_budget` :1229-1254 |
| arm surface | `/cpp-gsd-long` sets none of the above (its only mention: "--autocompact 600k stays on") | `commands/cpp-gsd-long.md:23` |

This is exactly the reported incident: route unset, `--bg`, Opus, 1M context, 600k compaction, generic briefing, no continuation ceiling, only the token estimate active.
The Owner's decision 2026-10-07 ("the new grammar should always be used automatically", memory `compiled-grammar-default`) is recorded but **not implemented in any code path**.

Error class (iteration protocol): CLASE 2. The system assumed "CE installed" meant "CE wired". Absence was never treated as a policy question.

Hard premise: `slim_argv` passes `--disable-slash-commands` (:713). A `/gsd-*` resume **cannot** run on a slim worker. Slim is only valid for compiled packet units.

## 2. Ownership: extend, do not create (HR-NOVELTY-001)

| Responsibility | Canonical owner | Status |
|---|---|---|
| Worker launch / argv | `tools/gsd_mission.py` `launch_worker` → `worker_argv` / `slim_argv` | LIVE |
| Route admission (ADMISSIBLE/DEFER/RECOMPILE/ESCALATE) | `tools/route_admission.py` | LIVE, packet missions only |
| Mission defaults | `vault/config/mission-budget-defaults.json` (extend into the versioned baseline policy) | LIVE (budget keys only) |
| Floors per profile | `vault/config/route-floors.json` | LIVE |
| Model table | `vault/config/model-routing.json` (single authority; CAA T3 retires the stale `cost_collapse/router.py` IDs) | SPLIT-BRAIN |
| Session / goal budget | `hooks/session_budget_guard.js` + `tools/mission_spend.py` GoalLedger | LIVE / PARTIAL (canary #2 6.9% overshoot, cc2a2a73) |
| Cheap Architecture Admission, binding, Agent deny, coordinator cap, floor | CAA plan T0-T5 inside `ce-a3` | PROPOSED |
| Zero-model coordinator, estate envelope law, worker write access | cep-gen4 P0/S4/S9 | APPROVED, in flight (pane 0f9b771b) |
| Cost ladder | `tools/cost_to_completion.py` | DORMANT (no caller) |
| Champion/challenger replay | `tools/estate_shadow.py` | PARTIAL |
| Continuation | `tools/gsd_epoch.py`, capsule-v2, `kclear`/`kresume_courier.py` | LIVE |

The only responsibility no plan owns is **policy resolution of absent fields at launch**. Nothing new is created: one function plus one config extension inside existing owners.

## 3. Execution entry points

| # | Entry | CE active automatically today | Missing-field default | Silent expensive fallback? | Host limit |
|---|---|---|---|---|---|
| 1 | `/cpp-gsd-long` → `gsd_mission.arm` → `launch_worker` | auto envelope only | `--bg`, host Opus, 600k, generic, no ceiling | **YES** | none |
| 2 | Budget renewal `renew_mission` | carries envelope keys only if they were set | same as 1 | **YES** | none |
| 3 | Relay / context-wall successor (`gsd_epoch`, capsule-v2) | same argv path | same as 1 | **YES** | none |
| 4 | Packet mission (`envelope --wu-packet` + `admit --route`) | slim + admission + session envelope | n/a (opt-in) | no, but opt-in | slim cannot run slash commands |
| 5 | `tranche_driver.py --manifest` | coordinator declare + admission | n/a (opt-in) | no, but opt-in | — |
| 6 | Interactive pane (`kclaude.ps1` → claude.exe) | guard only if bound (`CPP_GOAL`/cwd/budget file) | user's `/model`, full prefix, no admission | YES (unbound) | **model and context are the host's/Owner's choice; CPP cannot rewrite a live interactive model** |
| 7 | Agent / subagent spawn | goal-admission Agent lane (partial: subagents not counted as requesters) | floors 25k-97k per spawn | partly | — |
| 8 | `/kclear` → `/kresume` | capsule continuity | no baseline record carried | n/a | — |
| 9 | Scheduled (wscript tasks, Cron, /loop) | UNVERIFIED (not scanned) | UNVERIFIED | UNVERIFIED | — |
| 10 | GEX44 | no admission (A3:25), spend UNKNOWN | — | UNKNOWN | needs an Owner step on GEX44 `~/.claude` |
| 11 | Another repo with CPP installed | global hooks apply; mission machinery applies by cwd | same as 1 / 6 | same as 1 / 6 | — |

Entries 1-3 converge on `launch_worker` → `worker_argv`. **One resolver there covers every mission path regardless of prompt text.** That premise is to be confirmed by a caller grep before the first edit.

## 4. Presence Contract architecture

**Resolver.** `resolve_baseline(rec)` lives in `gsd_mission.py` and is called once at the top of `launch_worker`, before argv is built. It works per field:

- Explicit value on the record (Owner/operator directive) → kept. Source: `explicit`.
- Absent → the policy value for the record's Work Class. Source: `policy@<version>`.
- Policy unreadable → built-in safe values (Sonnet, a bounded ceiling, never 600k/Opus). Source: `builtin`.

Misconfiguration immunity follows: the fail-closed direction is "cheap", the opposite of today.

**Work Class**, deterministic from the record (no model call):
- `COMPILED_UNIT`: has `wu_packet` → slim-t2 + route admission (already certified).
- `GSD_RESUME`: `/gsd-*` command, no packet → `--bg` (slash commands needed), but Sonnet, the policy ceiling, policy `continue_max_tokens`, and capsule continuation.
- `OTHER`: same BASIC tier as `GSD_RESUME`.
- **Compiled-grammar arm** (dossier + packet per unit) becomes the default for `GSD_RESUME` **only for phase kinds with measured evidence**. Today that is the SCAN phase, n=1 (EDD 3.31M vs 32.06M). Build phases stay BASIC until measured. Per the memory note, a sampled-quality audit and a legacy kill switch are kept.

**Capability tier recorded, never claimed:** `BASIC` (model + ceiling + continuation + envelope) or `COMPILED` (adds packet + slim + admission). The evidence on the record defines the tier.

**Legacy exception.** The combination `--bg` + Opus + ≥600k needs `legacy_reason` from a closed enum:
- `host_limitation`
- `uncertified_work_class`
- `quality_requirement`
- `novel_architecture`
- `safe_deopt:<trigger>`

Without one, under `enforce`, the launch is refused with the exact command to fix it. This is a deny, never a silent downgrade of an explicit Owner value.

**Safe deopt.** Escalate only the missing dimension. The model goes up via `safe_deopt:proof_failed|two_strikes` and the ceiling via `safe_deopt:context_miss`. Each is one field, recorded, and never raises the goal cap. This re-uses the CAA deopt triggers.

**Provenance.** `rec["baseline"] = {version, tier, work_class, src:{field:explicit|policy|builtin}, legacy_reason}` plus a ledger row `baseline_resolved`. This makes "which baseline and why" one field read.

**Rollout switch.** `CPP_CE_BASELINE=shadow|enforce|off`, the same pattern as `CPP_MISSION_BOUNDED_RENEWAL`.
- `shadow`: records and applies the non-refusing defaults (model, ceiling, continuation), and only logs would-be legacy denials.
- `enforce`: also refuses unexplained legacy launches.
- `off`: byte-identical legacy argv, pinned by the existing golden tests (the rollback).

**Inheritance.**
- Renewal and relay carry `baseline.version` and re-resolve absent fields. A renewal is never silently legacy (mirrors capsule-v2 G20).
- `/kresume` capsules gain the `baseline` block.
- The policy file is versioned, so Champion = the current version and Challenger = the next, replayed through `estate_shadow`.

**Interactive, Agents, binding, coordinator, floor, Boundary/Read/ZRT, regret.** These are CAA T0-T5 and cep-gen4 S4/S9, approved or proposed and folded by reference. This plan does not re-plan them; it sequences them after U6.

## 5. Units (inside goal `ce-a3`, `--parallel-unit presence`; goal singleflight enforces no collision)

| Unit | Route (self-hosted) | Work | Proof | Cap |
|---|---|---|---|---|
| **U6a** resolver + policy | compiled packet, slim-t2 Sonnet, worktree `Apps/pp-ce-presence` (headless cannot write under `~/.claude`) | `resolve_baseline`, policy keys in `mission-budget-defaults.json`, wiring in `launch_worker`, closed legacy enum, switch | new `test_gsd_mission_baseline.py` V-BASE-*; mutants: resolver call removed → red; builtin fallback = Opus → red; explicit value overridden → red; existing goldens green under `off` | 2.0M |
| **U6b** arm + inheritance | **armed with NO route/model/autocompact: the negative canary dogfoods U6a** | `/cpp-gsd-long` prose retired ("600k stays on" → resolver), renewal/relay/capsule carry `baseline`, `cpp-gsd-long.md` loses the manual-flag guidance (prompt extinction) | `test_gsd_mission_envelope`, `capsule_v2`, `epoch` suites green; renewal golden shows `baseline_resolved` | 0.8M |
| **U6c** canaries (real workers) | slim / BASIC per resolver | negative (no route, no CE words), misconfiguration (policy file renamed → builtin cheap), legacy exception (`legacy_reason=quality_requirement` launches `--bg` Opus and is recorded), project-install (one non-PP repo, plain task) | first-call floor + model + autocompact read from the worker's **raw transcript**, not the record (Production Reality); compared with the incident mission's measured floor (found from the ledger in U6c, UNKNOWN until then) | 1.5M |
| **U6d** CI + knowledge + enforce | slim | Cognitive CI clause in `cep_gen2 --tranche`; reachability registry; UKDL HR/PR/T drafts via CEPS; KV root-cause record; flip default to `enforce` after the negative canary passes | `reachability.py` exit 0; `cep_gen2 --tranche ce-a3` clause PASS; `node ~/.claude/hooks/tests/run-all.js` green | 0.7M |
| then | CAA T0-T5 as proposed (8.8M of the 9.9M ledger) | | | |

U6 total: 5.0M + 1.0M reserve = **6.0M**. Two-strike rule per unit (Regla 12 / HR-ONESHOT-003).

UKDL candidates (drafts, evidence-bound):
- HR: missing route is not permission for maximal-cost execution.
- PR: resolve the baseline before worker launch.
- T: CE installed but not wired into mission admission (field opt-in = host maximum).
- T: a slim worker cannot run a slash-command resume.

## 6. How this mission avoids the architecture it removes

This planner pane is the anti-pattern: interactive, Opus 1M, unbound. After approval it:

1. Runs `mission_spend.py session-declare` (stop 0.6M), bound to `ce-a3`.
2. Writes the U6a packet and route.
3. Arms U6a as a compiled slim mission.
4. Writes `RESUMPTION_FILE.md`.
5. Exits.

Successor units run in fresh short contexts. U6b onwards are armed **without** route/model fields, so the mission's own launches are the self-hosting proof. No Agents and no parent relay: units chain through mission state, and the receipt read is deterministic.

## 7. Master Done-Gate (scoped; owner per row)

| Condition | Evidence | Owner |
|---|---|---|
| Presence / no prompt dependency / route resolution / baseline before launch / misconfiguration | U6c negative + misconfiguration canaries, raw transcripts | U6 |
| Model routing default, context ceiling, continuation policy applied | worker transcript: model id, `--autocompact`, `continue_max_tokens` | U6 |
| Slim routing + packets for certified class | COMPILED_UNIT launch argv + admission row | U6 (existing path, now default) |
| Legacy exception + safe deopt | U6c legacy canary; deopt field test | U6 |
| Cognitive CI (route-null regression) | V-BASE mutants red | U6d |
| Cross-session inheritance | renewal/relay/kresume carry `baseline` | U6b |
| Self-hosting | U6b-U6d armed with no route | U6 |
| Cognitive deflation | first-call floor and model, canary vs incident, MEASURED | U6c |
| Interactive binding, Agent deny, coordinator, floor, regret, champion/challenger, Boundary admission, planner extinction | CAA T0-T5 gates | CAA |
| Zero-model coordinator, parentless tranche, estate envelope law | cep-gen4 S4/S9 gates | gen4 |
| KV / UKDL / CBR | CEPS drafts + `router_freshness_gate` | U6d + CAA T5 |
| **Deferred, named:** GEX44 cross-machine; cross-account; scheduled entry points (UNVERIFIED); within-epoch compaction; SSM/ContextImage/ZRT/Read Extinction "at least one" rows | each is a separate measured tranche after U6+CAA; within-epoch compaction is host-limited | Owner accepts deferral |

Done = every in-scope row MEASURED; the deferred rows stay listed as DEFERRED, never PASS.

## 8. Owner authority needed (single approval)

1. Fold U6 into `ce-a3` and raise its cap by 6.0M (9.9M → 15.9M worker spend).
2. Approve the CAA plan as proposed, sequenced after U6.
3. Accept the deferred rows (GEX44 cross-machine, cross-account, scheduled entry points, within-epoch compaction).
4. After U6d, Owner-side `Copy-Item` of any changed live file under `~/.claude` (HR-001). U6 itself touches only the repo.

Approval phrase: **"go presence: ce-a3 +6M, CAA after, deferrals accepted"**
