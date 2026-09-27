# Context Rent — plan (2026-09-27)

Status: APPROVED 2026-09-27 ("yy") with defaults D1-D4, plus one Owner amendment:
**the rollover sequence runs /kclear BEFORE /clear.** /kclear (session_checkpoint.py) is the capsule
writer; the safe-to-forget gate requires its output to exist and read back before /clear is typed.
A failed /kclear aborts the rollover — the context is never destroyed without a checkpoint.
Extends `vault/specs/parent-context-epoch-rotation.md` (Ralph half, G0-G7) — does not replace it.

## Incident reality (measured, session 04b41ed7, KobiiSports Resort; commit 7c4e7b2 in THAT repo)
Instrument: transcript usage deduped by message.id; control = all 262 multi-line ids carry identical
usage + requestId.

| | reported | measured (dedup) |
|---|---|---|
| model calls | 794 | **327** (814 usage lines) |
| cache read | 326 M | **132.4 M** |
| cache create | 3.6 M | **1.35 M** (all 1h TTL) |
| output | 832 k | **323 k** (visible ~117 k by chars/4; residual 206 k INFERRED) |
| avg / max resident | 410 k | 409 k / 674 k |

Reported totals are 2.51x double-counted (per content-block line). Shares roughly survive.
**Floor:** call #1 = 192 k resident. The FRESH session that read RESUMPTION_RECON.md (80e869fd) opened at
176 k; this session at 214 k. Rent = 47 % floor (192 k x 326) + 53 % growth above floor (71 M).
Fresh epochs can only remove the 53 %; the floor needs its own lever.
Floor composition (chars, ESTIMATED tokens ~chars/4): ~/.claude/rules 260 KB (~65 k) — unwatched by any
linter; global CLAUDE.md 40,117 (~10 k); PP CLAUDE.md 35 k; home CLAUDE.md 6 k; MEMORY.md 15 k;
remainder (system, tools, skill/agent listings, hook injections) UNMEASURED.

## token_autopsy defects
1. `token_autopsy.py:135-136` sums usage per line (no dedup) -> 2.5x.
2. `:254-270` never bills cache reads, then subtracts 0.9 x input price per read -> negative totals.
3. `:34-40` no entry for claude-opus-5-5 -> silently priced at the default (Sonnet) rate.
4. cache creation priced at base input regardless of TTL.
Same no-dedup defect in token_corpus_audit.py, token_ground_truth.py, cognitive_os/economics.py.
tis_observed.py already dedups correctly and documents the 2.5x — it becomes the single reader.
Prior RCA `weekly-limit-burn-rca-2026-06-30.md` summed per-turn usage — re-measure.

## Owners (D2A)
- Transcript usage reader: EXTEND tis_observed.py (single owner); CONNECT the 4 no-dedup readers.
- Cost: EXTEND token_autopsy -> typed categories + versioned rate card with provenance, UNKNOWN allowed.
- Session Autopsy / context rent: EXTEND token_autopsy (not a new module).
- Ordinary-session rollover: EXTEND context-watchdog.py Tier2 (today: types `/compact`) with a
  fresh-epoch branch; rehydrate via SessionStart source=clear in session_start_hub.js.
- Capsule compiler: CONNECT daif/session_continuity_compiler.py + gsd_x goal/brief.py (G7).
- /kclear: EXTEND session_checkpoint.py as the capsule writer. /kresume: NEW only as a thin command.
- Ralph: parent-context-epoch-rotation.md slices (G0 hung sweep first).
- Always-on budget: EXTEND claude_md_firewall.js aperture to rules/ + all always-on files.
- Ratchet: modules/tower (family entry). UBC: stays deferred (not built) — REJECT building it here.
- KobiiSports relay a/b/c: REJECT here (owned by that repo's session); CPP generalizes the lesson into
  gsd_mission preflight (quota verdict, progress = new commit or changed digest).

## Phases
P0 metrology · P1 session autopsy + floor attribution · P2 always-on floor · P3 interactive fresh
epochs (shadow -> opt-in) · P4 Ralph G0/G2/G7 + preflight · P5 baseline (KV, UKDL, tower, liveness).

## Owner decisions (defaults apply on approval)
D1 rules/ floor: propose per-file dispositions with evidence; apply each only on Owner yes.
D2 interactive rollover: ship SHADOW + one real drill; active only by opt-in.
D3 KobiiSports relay fixes: out of scope here.
D4 money: dollars only from a rate card with cited provenance; otherwise tokens + UNKNOWN.
