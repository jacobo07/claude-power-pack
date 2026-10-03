---
covers: [mission-capsule-rollover, capsule-v2, cpp-gsd-long, kresume, kclear, safe-to-forget, resume-certified, mutation-gate, successor-claim, rollover-protocol]
status: SPEC (T0). Implementation T1-T7 in progress; T8 Production Reality HELD by Owner (2026-10-03, Q5)
date: 2026-10-03
mode: ULTRA-PLAN for ownership (this document), EXECUTION for every tranche
parents: vault/specs/interactive-context-rollover.md (P3 interactive), vault/specs/parent-context-epoch-rotation.md (mission epochs)
---

# Mission Capsule Rollover (capsule-v2) -- spec

## 1. Reality (measured 2026-10-03, read-only, HEAD 4c00eb1f)

- Mission rotation (`tools/gsd_mission.py supervise` + `tools/gsd_epoch.py decide_turn_end`): ROTATE ->
  `stop_owner` -> `launch_worker` with a <= 8 KB card via `--append-system-prompt`. The predecessor's
  state is a free-form `HANDOFF NOTE:` read from its transcript (`gsd_mission.py:1605`), labelled a
  claim. "RECONCILE BEFORE ACTING" is prose. S7 `identity_check` records a mismatch, gates nothing.
  Single-flight = CAS on (epoch, state) + `_Lock` + sweep lease. No capsule, no seal, no exam.
- Interactive rollover (`tools/rollover.py`, `/kclear`, `/kresume`): capsule `rollover-capsule-v1`
  keyed by session id; seal = write + read-back sha256 + ledger `capsule_sealed`; `gate()` judges
  the ledger receipt (SAFE_TO_FORGET / REFUSED / NO_CAPSULE); claim = O_EXCL `.claim`; `refresh`
  CONTINUE/RECOMPILE; 4-item exam; certify retires the capsule. Transport = exact-target C4 typing
  (orca-exact / tmux-exact), live and ON by default -- interactive only.
- Defects found in the interactive path (they would be inherited, so they are fixed in the shared owner):
  - **D1 no mutation gate.** "No file edit before RESUME_CERTIFIED" exists only in `commands/kresume.md`.
    No hook references certification.
  - **D2 stale certify.** `certify()` compares answers with the SEALED capsule and never requires
    refresh = CONTINUE: after a RECOMPILE, quoting the stale HEAD certifies.
  - **D3 answer leak.** `resume` prints goal, branch, HEAD and the first obligation, then asks for them.
  - **D4 substring pass.** `next` passes when the answer is any substring of the expected text (`"a"`).
  - **D5 unrecoverable claim.** The `.claim` marker has no lease, generation or takeover; a dead
    claimant locks every other successor out for the capsule's 24 h life.
- Goal Spine = `modules/gsd_x/goal` (optional `bind_mission` observer). Most missions are unbound, so
  the mission's goal pointer is the GSD workstream `STATE.md` (`init.manager.state_path`) and its next
  obligation is `init.manager.recommended_actions[0]`.
- Live missions: m-13177bed4fa3 (P3, InfinityOps product-surface), m-876f8b5a904a, m-f9ad30f21e85
  RUNNING; m-162e867ec4e7 BLOCKED. The production sweep runs `tools/gsd_mission.py` from this checkout:
  every edit reaches them on the next pass. Hence 3.1.

## 2. Ownership (EXTEND > MERGE > CONNECT > NEW)

| responsibility | owner | action |
|---|---|---|
| WHEN to rotate | `gsd_epoch.decide_turn_end` | REUSE, unchanged |
| capsule, seal, SAFE_TO_FORGET gate, claim, refresh, exam, certify | `tools/rollover.py` | EXTEND (kind-aware, v2 identity, lease, reality-bound certify) |
| mission facts -> capsule; pre-certification markers; chain audit | `tools/mission_capsule.py` | NEW thin adapter (no second engine) |
| process lifecycle, single-flight, launch, stop | `gsd_mission.supervise` | CONNECT: call sites only, behind 3.1 |
| mutation authority before certification | `hooks/capsule_mutation_guard.js` | NEW guard, dispatcher Bash + Edit chains |
| same-epoch turn continuation (Ralph) | `gsd_epoch.continue_worker` | UNCHANGED: no capsule, no gate |
| Goal Spine | `modules/gsd_x/goal` | REFERENCE only (`goal_ref` when bound) |

No second capsule format, exam, reconciliation engine, SAFE_TO_FORGET or claim system. The free-form
note survives only as the capsule field `note` (a claim), never as the authority.

## 3. Contract

### 3.1 Protocol version (compatibility)
`rec.rollover_protocol == "capsule-v2"` is set ONLY by `gsd_mission.py arm --rollover-protocol capsule-v2`.
A record without it is legacy and every new branch is skipped for it -- P3 and the other live missions
finish on the semantics they were armed with. Nothing is migrated, stopped or rearmed. Default stays
legacy until >= 2 certified real rotations (Owner Q2); then default for NEW missions only.
Kill switch `CPP_CAPSULE_ROLLOVER=off`: v2 missions rotate the legacy way AND the guard allows.

### 3.2 Capsule v2 (control plane, bounded, references not dumps)
`schema: rollover-capsule-v2`, `kind: interactive|mission`, plus for missions: `run`
{lineage_id, mission_id, epoch (outgoing), successor_epoch, worker session}, `seal_origin`
(worker_handoff | supervisor_fallback | recovery), `degraded` (bool), `goal` = GSD STATE.md pointer,
`obligations` = GSD recommended actions (first = next), `goal_ref` (Goal Spine id + revision when bound),
`note` (predecessor claim, <= 2000 chars), `packet` (source-packet reference), `children`,
`transcript_mark` (size + mtime of the outgoing transcript at seal), `protocol: capsule-v2`.
Key: `mission-<mission_id>-e<epoch>`. v1 capsules stay readable as interactive.

### 3.3 State machine (rollover ledger + mission ledger)
```
RUNNING -(ROTATE)-> CAPSULE_SEALED(sha, read-back) -> SAFE_TO_FORGET | ROLLOVER_REFUSED(reasons)
SAFE_TO_FORGET -(re-gate immediately before stop: sha + transcript_mark unchanged)-> OUTGOING_STOPPED
-> LAUNCHED(precert marker written BEFORE spawn) -> SUCCESSOR_CLAIMED(generation g)
-> REALITY_REFRESHED(CONTINUE|RECOMPILE) -> RESUME_CERTIFIED | RESUME_FAILED
RESUME_CERTIFIED -> mutation authority restored (marker certified) -> RUNNING next epoch
```

### 3.4 Invariants
- **I1** No v2 successor mutates (Edit/Write/MultiEdit/NotebookEdit, or a shell command outside the
  observe allow-list) before RESUME_CERTIFIED. Enforced at the effect by the guard, not by the card.
- **I2** The outgoing worker is stopped only after `gate()` = SAFE_TO_FORGET on the capsule sealed for
  it, re-judged immediately before `stop_owner`, with its transcript unchanged since the seal.
- **I3** At most one successor holds a capsule claim; only the holder of the current generation may
  certify. A claim held by a dead process or past its lease is taken over (generation + 1); the old
  holder is fenced.
- **I4** Certification is judged against reality NOW (branch, HEAD of the capsule's tree; next
  obligation re-derived now), never against the sealed values; it needs a refresh in the same claim
  generation.
- **I5** A capsule that cannot be certified (no goal, no obligation) is refused before any claim.
- **I6** Tests never write the live state: every test sets `CPP_ROLLOVER_STATE_DIR` and the mission state dir.

### 3.5 Refusal and fallback (Owner Q6)
- Refused seal (children HOLD, obligations unknown, custody, repo unreadable): nothing is stopped; the
  pass is held and retried. A worker that ended its turn with no note is asked once (same-session
  continuation, handoff instruction) for one.
- After the wall grace (30 min, `wall.grace_s`) with still no SAFE_TO_FORGET: the supervisor seals a
  mechanical capsule from DURABLE state only, `seal_origin: supervisor_fallback`, `degraded: true`.
  Allowed only if obligations derive from GSD, the repo reads, and children are not HOLD/UNKNOWN.
  Otherwise the mission goes BLOCKED with the reason and the worker is NOT stopped.
- Degraded capsule: the successor starts in RECOVERY; its exam adds `dirty` (current dirty-path count
  of the tree) so the uncommitted side effects are looked at before authority returns.
- A dead predecessor (PROCESS_RECOVERY) with no uncertified capsule: `seal_origin: recovery`, degraded.
- No certification within 30 min of the successor's ack -> mission BLOCKED (`resume_not_certified`).

### 3.6 Non-goals
No pane or keystroke transport for background workers (the C4 path stays interactive-only). No capsule
for same-session continuation. No change to WHEN (`decide_turn_end`). No Goal Spine writes.

## 4. Tranches (one causal invariant per commit)

| T | what | files | gate |
|---|---|---|---|
| T0 | this spec | vault/specs/mission-capsule-rollover.md | covers front matter |
| T1 | v2 schema + kind-aware completeness + keyed capsules, v1 compatible | tools/rollover.py, tools/test_rollover.py | test_rollover + new V-CAP2 cases |
| T2 | claim lease, generation, stale takeover, fencing (D5) | tools/rollover.py, tools/test_rollover_claim.py | race tests: two claimants, dead holder, lease expiry, stale certify refused |
| T3 | reality-bound certify, no answer leak, strict next (D2-D4) | tools/rollover.py, commands/kresume.md, tests | stale-HEAD certify RED before fix, GREEN after |
| T4 | mutation guard + dispatcher wiring (canonical + live, 2 lines each) | hooks/capsule_mutation_guard.js, hooks/tests/test-capsule-mutation-guard.js, hooks/hook-dispatcher.js | deny/allow/fail-closed drills + positive control |
| T5 | mission adapter: compile/seal/gate/fallback/recovery, precert markers | tools/mission_capsule.py, tools/test_mission_capsule.py | V-MCAP unit + crash points |
| T6 | gsd_mission wiring behind 3.1: arm flag, ROTATE gate, launch marker, v2 card, certify deadline | tools/gsd_mission.py, commands/cpp-gsd-long.md | test_gsd_mission + test_gsd_epoch unchanged green; legacy path byte-identical |
| T7 | fault matrix (12 crash boundaries + races) + chain audit CLI | tools/test_mission_capsule_faults.py | all boundaries resolve to one owner |
| T8 | Production Reality (HELD) | runbook in section 6 | `mission_capsule.py audit --mission <m>` |
| T9 | Knowledge Vault, UKDL, UCR-CIF, baseline ratchet | vault/ | -- |

## 5. Failure semantics
Every unknown resolves to: old epoch stays authoritative (nothing stopped), or the new successor owns
the transition (claimed + certified), or an explicit BLOCKED/HELD with its reason in the ledger.
Never two workers with mutation authority, never a stopped worker with no sealed capsule.

## 6. Production Reality (T8, HELD -- Owner Q5)
Arm a smoke mission in `gsd-long-smoke` with `--rollover-protocol capsule-v2 --wall 20,21,19`; let it run
>= 2 rotations; judge out of process with `python tools/mission_capsule.py audit --mission <m>`, which
checks the 20-point chain per rotation from the two ledgers and the host session list.

## 8. Phase-4 audit fixes (BINDING; supersede sections 3-6 where they disagree)

Audit 2026-10-03 (oneshot-architect-auditor, EXECUTE-WITH-FIXES, 25 gaps). Each line = gap -> fix.

- **G1/G2 obligations.** The adapter runs ONE `init.manager` query at seal time (rotations are rare) and
  renders strings: `recommended_actions[i]` -> `"<action> phase <n>: <phase_name>"`; when there is none
  (a phase mid-execution, disk_status `partial`), the first phase not complete -> `"continue phase <n>:
  <name>"`. `state_path` is resolved against the work tree. Fixture with a partial phase.
- **G3 I2 restated.** No transcript re-check. The seal is taken only when the host lists the owner
  idle/done (its turn ended) or, for a fallback, past grace; before `stop_owner` the supervisor ledgers
  `outgoing_stop_authorized` bound to the capsule sha and records `capsule_key` on the mission; later
  passes that retry an unfinished stop reuse that authorization and never re-judge.
- **G4 holds stick.** A record field `capsule_hold` {reason, since}; `plan_next` checks it before
  `unblock`, like `gsd_hold`. Both BLOCKED reasons (fallback impossible, resume_not_certified) set it.
- **G5 clocks.** The fallback clock starts at the FIRST refused seal of the epoch, not at the wall
  notice. A fallback capsule is degraded and does not require an idle owner, so an overdue worker is
  still stopped (the m-916e905e23d4 enforcement survives for v2).
- **G6 identity.** `capsule_key` lives on the mission record from `outgoing_stop_authorized` until
  certification and is carried through every replace/retry; successors look up by that field, never by
  epoch arithmetic. `successor_epoch` is informational.
- **G7 binding window.** The precert marker is keyed `<mission_id>` (one per mission) and carries the
  worker name `<mission>-e<epoch>`. The guard matches a session by: owner session id, pending bg_id
  prefix, or -- while no bg_id is bound -- the host registry record of the session naming that worker,
  falling back to the launch cwd only inside the launch window (<= 300 s). Legacy sessions in the same
  cwd outside the window are allowed (test).
- **G8/G9 wiring.** Guard is pure node, non-mission fast path = one stat of the marker dir, wired
  `block: true, critical: true` in Bash and Edit chains of BOTH dispatchers; end-to-end deny through the
  dispatcher, ETIMEDOUT drill. MCP: v2 workers launch with MCP stripped (`--strict-mcp-config`), so no
  `mcp__*` tool exists to bypass I1. Remaining fail-open: a dispatcher chain abandoned at the harness
  deadline (stated, not hidden).
- **G10** Own allow-list: exact rollover.py / mission_capsule.py resume|certify|status, cd/Set-Location,
  git observe verbs, PowerShell read cmdlets; no test runners, no `sort -o`, no `--output`, no redirection.
- **G11** `arm --rollover-protocol capsule-v2` refuses permission modes that cannot run a shell
  (anything but `auto`/`bypassPermissions`).
- **G12** Mission resume/certify require `CLAUDE_CODE_SESSION_ID` (no ppid fallback) and that it is the
  mission's current worker (owner or pending bg_id). Whether the host sets it inside `--bg` shells is
  UNKNOWN until T8; if unset the successor cannot certify and the mission BLOCKs -- fail-closed.
- **G13** File kill switch `<rollover state>/capsule-v2.off`, read by the guard and gsd_mission; the env
  var stays as an extra override.
- **G14** Mission capsules live in `mission-capsules/`; interactive discovery (`newest_capsule`, hub,
  autotype) enumerates `capsules/` only. Test.
- **G15/G16/G17 exam.** RESUME_FAILED names the wrong KEYS, never expected values. The bootstrap omits
  branch/HEAD; the first obligation stays visible (it is also the autotype focus) and is accepted as a
  known non-secret: `next` checks agreement with the goal file NOW, not secrecy. Answers are normalized
  (markdown, backticks, quotes stripped). Certify judges against the refresh SNAPSHOT recorded on the
  claim; if HEAD/branch moved since that refresh, exit 8 "refresh again" (distinct from a wrong answer).
- **G18** Claim, takeover, refresh-note and certify all run under the claim lock with a generation
  check. Lease = 30 min = the certify window. Takeover only on expired lease or provably dead holder.
- **G19** The guard applies to mission successors only. Interactive /kresume keeps D1 as a stated
  limit (the pane has a human; a failed exam must not lock it).
- **G20** `renew_mission` carries `rollover_protocol`.
- **G21** No transcript and owner DEAD/idle by the host -> degraded `recovery` capsule allowed;
  children named lost.
- **G22** The v2 block is placed before GSD facts and the note in the card; max-size card test.
- **G23** Before T6: characterization of the legacy path (argv, card bytes, ledger event order per
  supervise branch, record without `rollover_protocol`) captured on the pre-change code; plus a mutant
  routing legacy to v2 that must go red.
- **G24** Adapter and tests resolve state dirs at call time and pass them explicitly; the guard honours
  `CPP_ROLLOVER_STATE_DIR` and `CLAUDE_STATE_DIR`; a sentinel asserts live dirs untouched.
- **G25** rollover.py owns the precert marker (create, certify-flip); mission_capsule only asks it to
  create one. One authority for "certified".

## 7. Rollback
Every tranche is additive behind 3.1 and the kill switch. Guard rollback: remove its two dispatcher
lines (canonical and live) or `CPP_CAPSULE_ROLLOVER=off`. `git revert` per tranche.

## 9. T5 as built -- the seam T6 calls (status IMPLEMENTED: no production caller yet)

| T6 call site (gsd_mission) | adapter call | guarantees / failure meaning |
|---|---|---|
| ROTATE decided, owner idle/done | `mc.compile_mission_capsule(rec, origin="worker_handoff", note=, transcript=, packet=, work_dir=)` | identity from rec (key `mission-<id>-e<epoch>`, lineage as `renew_mission`); obligations from `gsd_long_run.gsd_manager` NOW (G1/G2); gaps left absent, never filled. ValueError only for a record with no identity or an unknown origin (caller bug) |
| right after | `mc.seal_mission(cap)` | `SAFE_TO_FORGET` / `REFUSED`(reasons) / `UNKNOWN` (seal row not written: treat as refused). Same `capsule_sealed` row as the interactive seal |
| fallback past grace / dead owner | same with `origin="supervisor_fallback"` / `"recovery"` | degraded; eligibility IS `rollover.completeness` (children HOLD/UNKNOWN, unreadable repo, no obligations refuse). No readable transcript = custody UNKNOWN = refused, for every origin but `recovery` (G21: children named lost, custody stated unchecked). Transcript found by session id when not passed. The G5 first-refusal clock is T6 state |
| immediately before `stop_owner` | `mc.gate_before_stop(key)` | exactly `rollover.gate` (bytes as sealed, fresh, not certified). No transcript re-check: G3 supersedes I2; T6 ledgers `outgoing_stop_authorized`. Anything but SAFE_TO_FORGET: do not stop |
| before `launch_worker` spawns | `mc.arm_successor(rec)` | `rollover.precert_arm`: replaces any earlier marker (never inherits a certification). If it raises, do NOT spawn |
| after `parse_launch` / at ack | `mc.bind_successor(mid, worker, bg_id=)` / `(owner_session=)` | merging update, only onto THIS worker's uncertified marker; refused when none is armed, it names another worker, or it is certified |
| the successor itself | `python tools/mission_capsule.py resume|certify --mission <m>` | G12 identity (owner or bg-id prefix), GSD asked NOW, refused before claiming when GSD has no obligation; certify = `rollover.certify_flow`, which lifts the marker |

T6 adds to the record: `rollover_protocol`, `capsule_key` (G6, the CLI refuses without it), `capsule_hold`
(G4), the first-refused-seal time (G5). `mc.worker_name` mirrors `gsd_mission.worker_name` and is pinned
to it by V-MCAP-IDENTITY. Gates: `tools/test_mission_capsule.py` (V-MCAP), `tools/test_rollover_capsule_v2.py`
(V-CAP2), and G23 unchanged (`tools/test_gsd_mission_legacy_characterization.py`, never re-captured).
