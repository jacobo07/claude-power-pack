---
covers: [tco-meta, token-savings-loop, tco_meta, compounding-token-savings, intervention-ledger]
status: DRAFT (design approved 2026-09-28; spec awaiting Owner review)
owner: tools/tco_meta.py (new) -- reads through tools/tis_observed.py and tools/pricing_source.py
---

# TCO Meta -- a closed loop that compounds token savings

## 1. Problem

The estate MEASURES token spend well and ACTS on almost none of it:

- sensors exist: `tools/tis_observed.py` (canonical reader, one call counted once, three
  states), `tools/session_autopsy.py` (floor vs growth), `tools/token_corpus_audit.py`
  (waste patterns), `tools/token_ground_truth.py`, `tools/budget_monitor.py`;
- levers exist: `tools/tco_compact_gate.py`, `modules/cost_collapse/router.py`,
  `vault/config/model-routing.json`, RTK, `modules/token-optimizer/claudemd_linter.py`.

Nothing records "lever X was changed at time T", nothing measures what X did afterwards,
and nothing keeps what worked and undoes what did not. So a saving is never banked and
the next change is never judged against it. That missing loop is the whole of this spec;
no new sensor is built.

## 2. Objective (Owner, 2026-09-28: "all three, ranked"; "fully automatic")

Three measures, each per session, each from observed transcript usage:

| id | measure | per session | lower is better |
|---|---|---|---|
| `floor` | startup context | `SessionUsage.first_call_context` | yes |
| `resident` | quota pressure | `context_tokens / calls` (mean resident per call) | yes |
| `usd` | API list-price | `tis_observed.cost_usd` summed; **`sdk-cli` sessions only** | yes |

`usd` is measured only for `sdk-cli` (programmatic credit, billed at list price). An
interactive `cli` session on Max is not billed per token; pricing it would report money
that is not spent. An unpriced model makes `usd` UNMEASURED for that session, never 0.

Ranking across measures: each measure's relative change is normalised by its own noise
floor (section 5); the lever score is the sum of normalised expected gains. Units never
mix: tokens are never added to dollars.

## 3. Components (each one file, one purpose)

| file | purpose |
|---|---|
| `tools/tco_meta.py` | CLI + the tick: `tick`, `status`, `revert <id>`, `off` |
| `modules/tco_meta/ledger.py` | append-only JSONL ledger: observations, trials, verdicts |
| `modules/tco_meta/observe.py` | new transcripts -> observation rows (via `read_session`) |
| `modules/tco_meta/levers.py` | lever registry: detect / apply / revert / guard |
| `modules/tco_meta/judge.py` | stratified before/after comparison, noise floor, verdict |
| `modules/tco_meta/safety.py` | forbidden paths, lock, kill switch, host headroom, daily cap |
| `tools/test_tco_meta.py` | V-TCOMETA-* gates, synthetic ledgers, mutation drills |

State lives in `vault/tco_meta/`: `observations.jsonl`, `trials.jsonl`, `lock`.

## 4. Data flow -- one tick

Trigger: the SessionStart chain spawns `tools/tco_meta.py tick` **detached** (the tick
never runs inside the chain's 4000 ms deadline and never blocks a session). Also runnable
by hand. Every tick:

1. **Safety preconditions** -- kill switch `CPP_TCO_META=off` -> exit; host free memory
   < 2 GB -> exit `SKIPPED_HOST`; lock held by a live process -> exit. A lock whose holder
   is dead is taken over (kernel lock via `msvcrt.locking` / `fcntl`, released on death).
2. **Observe** -- every transcript modified since the last observed mtime is read with
   `tis_observed.read_session`; one row per session id (replaces an earlier row for the
   same id, since a live session keeps growing). Row carries: session id, project key,
   entrypoint, first-call timestamp, the three measures with their state, and the id of
   the trial live at the session's FIRST call.
3. **Judge** the open trial, if any (section 5).
4. **Start** a new trial if none is open, the daily cap (2 trials / 24 h) is not spent,
   and a lever's `detect()` returns a candidate: highest expected normalised gain wins.

Only one trial is ever live. A session is attributed to a trial only if its first call
is after the trial's `applied_at`: the floor is sampled at startup, so a session that
started before the change never saw it.

## 5. Judging

- **Strata** = (project key, entrypoint). Sessions from different projects carry
  different CLAUDE.md files; comparing across them measures the project mix.
- **Baseline** = per stratum, the 8 most recent sessions whose first call is before
  `applied_at` and after the previous trial's verdict time (so every baseline session ran
  under the current configuration, including all earlier KEEPs). **Trial** = sessions
  whose first call is after `applied_at`.
- A stratum counts once it has >= 3 sessions on each side. A trial needs >= 8 trial
  sessions across counted strata, or it stays OPEN. After 14 days still short: verdict
  `REVERT_UNJUDGED` -- an unmeasurable change is not kept on hope.
- **Noise floor (A/A)**: the baseline split in two halves by time; the relative difference
  of their medians is that measure's noise. A saving must exceed `max(2 x noise, 2 %)`.
- **Verdict**:
  - target measure improved beyond the noise floor AND no other measure worsened beyond
    its noise floor AND the lever's quality guard is clean -> `KEEP`;
  - anything else -> `REVERT`, reason recorded (`NO_EFFECT`, `REGRESSED:<measure>`,
    `QUALITY:<signal>`, `UNJUDGED`).
- **KEEP is the compounding step**: the kept state becomes the next trial's baseline,
  and the ledger's cumulative saving adds the measured (not expected) delta.

## 6. Levers (v1)

Each lever declares: target measure, `detect()` -> candidate or None, the exact key it
writes, `apply()`, `revert()`, and a lever-specific quality guard.

| lever | measure | writes | detect | quality guard |
|---|---|---|---|---|
| `plugin-prune` | floor | one key in `~/.claude/settings.json` `enabledPlugins` | an enabled plugin whose skills had 0 invocations in 30 days of transcripts | any transcript line showing an attempt to use a skill of the disabled plugin -> REVERT |
| `compact-threshold` | resident | `WARN_PCT` in `vault/tco_meta/overrides.json`, read by `tco_compact_gate.py` | median resident per call > 40 % of window | CEPS error rate per session rises beyond noise -> REVERT |
| `subagent-routing` | usd | one route in `vault/config/model-routing.json` | an `sdk-cli`/subagent task class routed to a model more expensive than the class's routing default | completion-gate block rate on those sessions rises -> REVERT |

**Excluded from v1 automation, deliberately**: `~/.claude/CLAUDE.md` and project
CLAUDE.md prose, `~/.claude/rules/*` (its reduction is an Owner decision already pending
in `vault/plans/context-rent-2026-09-27.md`), MEMORY.md content. These are doctrine text,
not keyed settings, and no key-level revert exists for a prose edit.

## 7. Safety -- because it runs unattended

- **Forbidden paths** (refused by `safety.py` before any write, and asserted by a test
  that drives a lever at each): `~/.claude/rules/**`, `~/.claude/CLAUDE.md`, any
  `CLAUDE.md`, `vault/hard_rules/**`, `hooks/secret_firewall*`, `hooks/cascade*`,
  `modules/secret_firewall/**`, `modules/cascade_prevention/**`, `settings.json`
  `permissions`/`hooks` keys, MEMORY.md.
- **Key-level writes, key-level reverts.** A lever changes one key. On apply it records
  the key's prior value and the value it wrote. On revert it restores the prior value
  **only if the key still holds the value it wrote**; if someone changed it since, the
  revert is refused as `REVERT_CONFLICT` and surfaced -- it never overwrites newer work.
  Whole-file byte restore is not used: it would destroy concurrent edits to the file.
- **Atomic writes** (temp file + replace), JSON re-parsed after write; parse failure ->
  immediate restore of the key.
- **One live trial, 2 starts / 24 h, kill switch, host-headroom skip.**
- **Cooldown**: a reverted lever+candidate is not retried for 30 days.
- **Every decision is a ledger row** with reason and the numbers it used; `status`
  renders them. Nothing is decided off-ledger.

## 8. Report -- `tco_meta.py status`

Open trial (lever, candidate, applied_at, sessions so far per stratum), history of
verdicts with deltas and noise floors, cumulative MEASURED saving per measure, and
counts of observed sessions by state (MEASURED / MEASURED_ZERO / UNMEASURED). Every
figure names its instrument.

## 9. Tests (`tools/test_tco_meta.py`, V-TCOMETA-*)

Synthetic homes and ledgers only; never the Owner's real settings or transcripts.

- judge: real effect -> KEEP; pure noise -> REVERT(NO_EFFECT); saving on target but a
  regression elsewhere -> REVERT(REGRESSED); too few sessions -> OPEN; 14 days short ->
  REVERT_UNJUDGED; a session started before `applied_at` is not attributed.
- levers: apply/revert round-trip is exact on the key; revert after a foreign change
  -> REVERT_CONFLICT and the foreign value survives; each forbidden path refused.
- safety: kill switch, lock held, dead-holder takeover, daily cap, host skip.
- observe: dedupe per session id; UNMEASURED transcript never becomes zero; `usd`
  absent for `cli` sessions.
- **Mutation drills** (each must turn a named gate red, restore verified by SHA-256):
  KEEP without the noise-floor check; revert without the conflict check; forbidden-path
  list emptied; quality guard ignored.

## 10. Done

`python tools/test_tco_meta.py` exit 0 with every mutation drill red-then-restored;
`python modules/liveness/reachability.py` names no unreachable tco_meta module; one real
`tick` on this host produces observation rows from real transcripts and a `status`
report. **Not claimed by done**: that any saving has been realised -- that needs real
trials to run to a verdict over days, and is reported by `status` when it happens.

## 11. Known limits

- Session-to-session variance is large; `resident` and `usd` need many sessions per
  verdict. Early trials will mostly be `floor` (the low-noise measure).
- Attribution assumes nothing else changed the floor during a trial. Other panes edit
  the same estate; a trial overlapping a manual CLAUDE.md change is confounded. The
  ledger records the floor of the baseline and trial so a jump unrelated to the lever
  is visible, but it cannot be excluded automatically.
