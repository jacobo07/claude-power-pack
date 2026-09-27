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

## State (update after every sealed unit)
- P0 SEALED 8c39c27: token_ground_truth + token_corpus_audit dedup (economics inherits);
  tools/test_usage_dedup.py 8/8, red 1/8 before. token_autopsy.py is being fixed by ANOTHER live
  pane (uncommitted, 22:51) -- do not touch; told it via cross-session msg that it prices all
  writes at the 5m rate (1h = 1.6x). Rate card verified vs pricing page 2026-09-27 (Opus 5.5
  cache read 0.05x = $0.20). June RCA used token_ground_truth -> absolutes ~2.5x high, ratios ok.
- P1 SEALED (this commit): tools/session_autopsy.py + test 11/11, wired in /cost-autopsy.
  Incident (API-list equivalent): $43.74 = read $26.48 / 1h-write $10.79 / output $6.47;
  floor re-read ~$12.57; 2 TTL-expiry rewrites 455 k tokens; fresh-epoch saving UPPER BOUND
  $14.18 (32%). Floor and rollover are levers of the same size.
- NEXT: P1b floor attribution (which sources make the ~190 k floor; one headless probe costs
  subscription quota -> Owner memory says defer model experiments until the limit resets);
  then P2 firewall aperture over rules/ + all always-on files; then P3.

## P2 facts + D1 proposal (awaiting Owner yes per option)
- ~/.claude/rules: 22 files, 259,068 chars, **0 carry `paths:`** -> all load on every call of
  every project. `## Source` incident narratives = 57,027 chars (22 %, ~14 k tokens/call):
  evidence, not rule text. Largest: guard-event-reachability 68 % Source (18.4 k chars).
- Harness re-injected skill listings in incident history: 9 x ~5.5 k chars (~12 k tokens) --
  small, same order as hook noise. (A first census over-captured agent listings to line end;
  that figure was discarded.)
- Option A (recommended): move each `## Source` section to
  vault/knowledge_base/rules-evidence/<rule>.md, leave one line "Source: <path>" in the rule.
  Rule text untouched, -14 k tokens on every call everywhere.
- Option B (not recommended): `paths:`-scope or relocate project-born rules. Saves more but
  defeats cross-project inheritance, the point of the Constitutive Baseline Ratchet.
- Option C (later): condense rule text only with ablation / guard-test evidence.
- Still unmeasured: ~100 k of the floor that is not files (system prompt, tool schemas,
  listings). Measuring needs one headless probe on subscription quota -> deferred.

## Owner decisions (defaults apply on approval)
D1 rules/ floor: propose per-file dispositions with evidence; apply each only on Owner yes.
D2 interactive rollover: ship SHADOW + one real drill; active only by opt-in.
D3 KobiiSports relay fixes: out of scope here.
D4 money: dollars only from a rate card with cited provenance; otherwise tokens + UNKNOWN.
