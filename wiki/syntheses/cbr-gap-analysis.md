---
type: synthesis
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-cbr-external-research, 2026-10-01-cbr-internal-inventory]
---

# Constitutive Baseline Ratchet: gaps and full potential

**Question (Owner, 2026-10-01):** research CBR like SDD-OS: all of its gaps and its full potential.

**What CBR is meant to do.** "si hago algo nuevo y no menciono ciertas cosas que tendria esa cosa en
ese baseline, se hacen automaticamente" (`docs/superpowers/specs/2026-09-24-family-baselines-design.md:24`).
Each system FAMILY (web, KobiiCraft mode, persistent-state SaaS, Wii homebrew) carries immutable
generations `B<n>` of rules. Lessons from finished work are auto-promoted into `B<n+1>`. A ratchet
forbids silent downgrade, and a done-gate asks APPLIED or NOT-APPLICABLE + reason for every entry.
Component page: [[constitutive-baseline-ratchet]].

**Method.**
- External benchmark: 32 requirements with evidence tiers, about 33 sources
  ([[2026-10-01-cbr-external-research]]). I verified 3 load-bearing claims myself; see "Evidence
  checks" below.
- Internal inventory with file:line evidence ([[2026-10-01-cbr-internal-inventory]]). I
  re-verified its key claims and corrected one.
- `wiki/tools/cbr_probe.py` drives the real `modules/tower` functions. Real data is read-only;
  every mutation runs on a temp copy, with a positive control per hole.
- Code references are @ `298975d`. The tower files are unchanged since `2a80b35` (2026-09-28).

## Answer in one paragraph

CBR has excellent machinery and almost no content flowing through it:
- **Machinery:** immutable, hash-anchored generations, an anti-downgrade diff that knows a rung is a
  kind not a strength, an honest check grammar, a bounded injector, and a done-gate that refuses to
  count prose as applied.
- **Content:** 4 hand-sealed `B0` generations of 15 rules each. Not one rule has a runnable check
  (31 prose, 29 empty). No `B1` has ever been written. Auto-promotion, the Owner's core ask, is not
  built. The done-gate and the ratchet have no production caller.

What IS live is the injection. The rules reach real sessions (35 deliveries in 20 sessions), and they
arrive with a sentence promising "the done-gate judges every active entry", which nothing does. So
today CBR is a per-family reminder of governance rules most of which are already loaded elsewhere,
stamped with a SHA as if it were a contract.

The external evidence says three things:
- Reminders like this move compliance on the targeted rule but not overall task success.
- Lift claimed without a counterfactual is usually wrong.
- Lessons promoted without a quality signal propagate their errors.

CBR's potential is real and unusually close: PP already has the counterfactual baseline sealed (O0),
3,914 deposits, and the ratchet code. What is missing is the middle: checkable rules, a gate that
runs, promotion with admission control, and one O1 measurement.

## Two things share the name

| channel | source of content | classifier | status |
|---|---|---|---|
| **Family baselines** (`family_block`, `modules/gsd_x/cli.py:99-153`) | `vault/tower/baselines/<family>/B0.json`, 60 Owner-sealed rules | `modules/tower/families.py::classify_prompt` (prompt vocabulary) | LIVE since `f4a71c8`, 2026-09-30 |
| **Mission Baseline Capsule** (`inherited_block`, `cli.py:59-88`) | fable_distillation deposits, all repos | `capsule.py` `_family_of` → `family_scan` (PERSISTENT_STATE hardcoded, `capsule.py:46`) | LIVE; built by scheduled task `PP-Tower-Capsules` |

Both write to one ledger, `~/.claude/state/tower/consumption.jsonl`, with different row shapes
([[2026-10-01-cbr-internal-inventory]] §5, §8).

## Verified defects

"probe" = `wiki/tools/cbr_probe.py`, run 2026-10-01. Each hole was checked against a control that
went red.

| # | defect | evidence |
|---|---|---|
| D1 | **The delivered prompt promises a gate that does not run.** The agent is told "The done-gate judges every active entry of this generation, shown here or not", and to write `NO APLICA: <reason>`. `donegate.judge` has no production caller, and no parser reads `NO APLICA`. | `modules/gsd_x/cli.py:143-145`; grep: callers are tests and the probe; `modules/liveness/reachability.py` lists `tower/donegate` and `tower/ratchet` as ORPHAN (inventory §5) |
| D2 | **Zero runnable checks.** 60 active entries: 31 prose, 29 empty, 0 `file`/`glob`/`regex`/`registry`/`test`. A wired gate could only answer UNJUDGED, so `would_block` is True for every family. | probe P1; P5 control: real `web_surface` B0 vs an empty repo → 15 UNJUDGED, `would_block=True`; `tools/test_tower_checks.py` V-TCHK-REAL-POPULATION |
| D3 | **Auto-promotion is not built, and `promote()` admits anything well-formed.** Only B0 exists (4×15, all `reviewed`). `ratchet.promote` has no caller; `tools/family_baseline.py` has no `promote` command. In the probe it accepted an origin pointing at a missing file and `check: glob:**`; the done-gate then scored that entry APPLIED_VERIFIED on a one-file repo. | probe P4; `ratchet.py:139-143,164-183` (reason + authority strings only, no `verify_origin`); `family_baseline.py:143-156` |
| D4 | **The ratchet licenses whatever is written down, and nothing runs it.** H1: any non-empty `reason`/`authority` (`"x"`/`"x"`) licenses a withdrawal. H2: `why`, `origin` and `class` are outside the diff and can be rewritten with nothing on the record. H3b: strip a child's `parent_sha256` and the same edit to both generations reads `ok=True` (control with anchor: TAMPERED). `verify_chain` runs only from the CLI and tests. | probe P3; `ratchet.py:72-99,110-112`. **Refuted:** editing the newest generation in place is caught (it is still diffed against its parent; probe H3). |
| D5 | **The gate, once wired, has two easy exits.** H5: fifteen `"n/a"` reasons turn `would_block` False. H6: `test:<file>` returns DELEGATED, which does not block, even when that test fails, because nothing runs it. | probe P5; `donegate.py:61-64,78`; `checks.py:153-155` |
| D6 | **Origins are rotting and are injected anyway.** 9 of 60 B0 entries now cite text that is gone (8 persistent_state, 1 wii_homebrew), likely because the cited rules moved to skills on 2026-09-29/30. The suite is red at HEAD, and every injection still carries the B0 SHA stamp. | `tools/test_baseline_generations.py` 15/16, `V-BGEN-REAL-B0-CITATIONS-HOLD` FAIL (re-run by me); inventory §12.3 |
| D7 | **Families come from prompt words, not from the repo.** In my 11 probe prompts, 6 disagree with what I would expect. Examples: "add a new game mode to the minecraft server" → none; "landing lobby for the new kobiicraft skywars arena" → web only (the anti-trigger `landing` vetoes KobiiCraft); "add a pricing tabla to the homepage" → also persistent_state; "build a SaaS app where users save invoices" → none. `repo_families(cwd)` exists but is not on the prompt path. | probe P2 (expectations are mine: *interpretation*); `families.py:88-99`; inventory §4 adds misses ("fix the login form on the site") and false hits on questions |
| D8 | **Selection ignores the prompt.** All entries are `reviewed` with no runnable check, so the rank ties: the same first 7-8 entries are shown every time, and the other 7-8 per family are never shown. | probe P1 (injected 7/7/7/8, deferred 8/8/8/7); `select.py:46-50` |
| D9 | **Only offers are measured.** Of the spec's seven telemetry rungs (offered → … → prevented a failure), only `offered` has a writer. There is no O1 after the sealed O0, and `test_tower_o4.py` prints "CLAIM NOT PROVEN (b) a real mission starts higher". 58% of capsule offer rows have state UNKNOWN. Test rows (`sid: vgate`) sit in the production ledger. | inventory §8; `vault/audits/ucr_cif/21_O0_RESULT.md` |
| D10 | **The capsule's inheritance is near-global.** 43 of 47 capsules carry one identical 6-lesson set; the other 4 differ by one lesson. 94% of the 3,914 deposits are `landed-commit` rows the lessons list drops, and `portability_proven` is true for 0. | measured by me (the inventory said 47/47; corrected); `capsule.py:121-125,182-191` |

## Scored against the engineer-grade checklist (32 items)

✗ = missing, ◐ = partial, ✓ = met. Tier = strength of the outside evidence
([[2026-10-01-cbr-external-research]] §10).

| # | requirement (abridged) | tier | CBR | why |
|---|---|---|---|---|
| 1 | Immutable generations; each project records the generation it attests against | B | ◐ | Immutable, SHA-stamped in every injection; no project records an attested generation |
| 2 | Upgrade = diff B_n → B_n+1 | B | ✗ | No upgrade flow; only B0 exists |
| 3 | Floating vs pinned propagation, per entry | B | ✗ | "Baseline Propagation Set" is doc only (inventory §10) |
| 4 | New entries judge new work, not the legacy estate | B | ✗ | — |
| 5 | Raising existing projects needs an owner + deadline | B | ✗ | — |
| 6 | Deliver as default (scaffold/library) over instruction | B | ✗ | Instruction only |
| 7 | Machine-checkable entries preferred and labelled | A/B | ◐ | Grammar and ranking prefer runnable checks; 0 of 60 have one (D2) |
| 8 | Enforcement is blocking or off, no warning tier | B | ✗ | Advisory text + report-only gate (D1) |
| 9 | Deliver at plan/diff time | A-/B | ◐ | Prompt-time, yes; nothing at diff time |
| 10 | Hard cap, ordered by consequence | **A** | ◐ | Cap 8 / 1,400 chars; order is by checkability, and ties (D8) |
| 11 | Inject only what the agent would not do anyway | **A** | ✗ | No test; origins are governance rules, many already in always-loaded context |
| 12 | Abstract procedure + a check | **A** | ◐ | Abstract, yes; check, no |
| 13 | Promotion is PROVISIONAL, confirmed or evicted by outcomes | **A** | ✗ | `status: auto` exists; no outcome signal; promotion unbuilt (D3) |
| 14 | Admission control on the promotion channel | **A** | ✗ | D3 |
| 15 | Truthful per-entry provenance | B | ◐ | origin + quote, verified at B0 build; 9/60 rotted (D6); rewritable (D4 H2) |
| 16 | Stale-justification detection | C | ◐ | Detector exists as a test; not at injection; red unnoticed |
| 17 | Expiry on every waiver | C | ✗ | N/A has no date |
| 18 | Recipient "not useful" demotion signal | B | ✗ | — |
| 19 | No silent downgrade; reasoned demotion on the record | B | ◐ | Diff logic is strong; any string is an authority; orphan (D4) |
| 20 | Anti-gaming | C | ◐ | CHECK_CHANGED blocks swapping a check for a trivial one; a NEW trivial check is free (D3) |
| 21 | APPLIED needs evidence, not a tick | **A** | ◐ | Only static checks can produce APPLIED; N/A is free text (D5); unwired |
| 22 | Done-gate list short (do-confirm, 5-9 killer items) | A/C | ✗ | All 15 per family are judged |
| 23 | Families multi-label | A/B | ◐ | Supported; anti-trigger vetoes drop real labels (D7) |
| 24 | Explicit conflict rule between families | B | ✗ | Backlog B3 (precedence vs project CLAUDE.md), no code |
| 25 | Family declared + validated, UNKNOWN reachable | B | ◐ | `repo_family_report` has UNJUDGED; not used on the prompt path |
| 26 | Human owner + review cadence | B | ◐ | Owner sealed B0; `review` CLI; no cadence |
| 27 | Per-entry telemetry: injected, applied, waived, failed later | B | ◐ | Injected ids only (D9) |
| 28 | Lift against a counterfactual | **A** | ◐ | O0 sealed (36 pairs, 540 verdicts); no O1 |
| 29 | Per-entry outcome metric | A/C | ✗ | — |
| 30 | Perception is not lift | **A** | ✓ | The repo says so itself: "Lift verificado = 0", "CLAIM NOT PROVEN" |
| 31 | Size growth monitored, consolidation scheduled | **A** | ✗ | — |
| 32 | Push, not pull | A/B | ✓ | Hook-injected, LIVE |

**Totals: 2 met, 15 partial, 15 missing.** Of the 9 items backed by tier-A evidence alone (bold),
1 is met (#30), 4 partial (#10, #12, #21, #28) and 4 missing (#11, #13, #14, #31). The pattern differs from [[sdd-os-gap-analysis]]: there, the template allowed
things nothing required. Here, the code requires the right things of content that does not exist
yet.

## Evidence checks I ran on the external research

- OpenSSF Scorecard (arXiv 2210.14884): abstract confirmed verbatim, "the number of reported
  vulnerabilities increased rather than reduced as the aggregate security score … increased", R²
  9-12%.
- Agent memory (arXiv 2505.16067): "experience-following" and "error propagation" confirmed. The
  abstract does **not** directly state that quality-gated memory beats accumulating everything;
  it says experience quality must be regulated. Weaker than the research file states.
- Infer diff-time vs batch (CACM 2019): "70% fix rate" vs "0% fix rate" seen consistently in search
  results for the paper and its author manuscript. The full text was unreachable (403/404), so this
  is snippet-verified.
- Two widely repeated figures the research flagged as untraceable are not used here.

## Full potential: what CBR becomes if the middle is built

Each item names the outside evidence it rests on and what PP already has toward it.

1. **A real counterfactual, cheaply.** O0 is sealed with its hash. One O1 run, plus randomly
   withholding one entry per family per project, gives per-entry lift at portfolio scale. Almost
   no tool in the external survey measures this way (§9).
2. **Rules that check themselves.** Fitness functions and Google's "build error or nothing" say an
   entry worth keeping is a check (§1d, §4a). The grammar is already built and honest. The work is
   content: rewriting each of the 60 rules as a check, or labelling it MANUAL with a short do-confirm
   question.
3. **A learning loop that does not poison itself.** Promote deposits as PROVISIONAL into `B<n+1>`,
   and let later task outcomes confirm or evict them (§6d, §7f). The deposit stream exists (3,914
   rows), and the ratchet can already record a reasoned demotion.
4. **Placement over volume.** At diff time, the same analysis got a 70% fix rate vs 0% in batch
   (§1e). A family entry with a regex check could run on Edit/Write for that family's files, not only
   as a paragraph at prompt time.
5. **Defaults instead of reminders.** Google moved readiness checklists into frameworks (§2b). The
   end state for a mature family is a scaffold or skill that makes compliance the starting point.
   `B<n>` then becomes the spec those defaults are tested against.
6. **Repos that know their generation.** Copier-style: each repo records the `<family>/B<n>` it
   was attested against, and an upgrade shows only the delta (§3a). The stamp is already in every
   injection and verdict.

## What to change, ranked

Rank = strength of evidence × how directly it changes outcomes × cost. None of this is approved;
each item needs an improvement page and an Owner decision.

1. **Make the delivered text true, and fix the red suite.** Cost: S.
   - Drop "The done-gate judges every active entry" from `cli.py:144`, or wire `judge()`
     report-only into the Stop path so the sentence becomes true.
   - Re-anchor or revert the 9 QUOTE_MISSING entries through the ratchet (`revert`, with a reason).
   - Refuse to inject an entry whose origin does not verify.
2. **Turn rules into checks, or shrink the gate.** Cost: M.
   - Per family, convert what can become `file`/`glob`/`regex` (O0 found 49 of 60 are
     process/rendered/design, so most cannot).
   - Mark the rest MANUAL.
   - Keep a do-confirm list of 5-9 killer items for the gate (#7, #21, #22).
3. **Measure before growing.** Cost: M. Folds into [[measure-knowledge-store-consultation]].
   - Run O1 against the sealed O0 hash.
   - Parse `NO APLICA` and applied evidence from transcripts into per-entry rungs.
   - Withhold one entry per family to get a control (#27-#29).
   - Move test rows out of the production ledger.
4. **Build promotion with admission control.** Cost: M-L.
   - `promote()` requires `verify_origin` = VERIFIED, a check or a MANUAL label, and an evidence
     ref (commit/incident).
   - Entries enter as `provisional` and are confirmed or evicted by outcomes.
   - Authority comes from an allowlist.
   - Diff `why`/`origin`/`class` as well; treat an unanchored child as not ok.
   - Run `verify_chain` in a gate (#13, #14, #19).
5. **Classify by the repo first, then the prompt.** Cost: S-M.
   - Use `repo_families(cwd)`, cached, as the base set, and let prompt words add to it.
   - Turn anti-triggers from a veto into a demotion, and fix the English gaps ("minecraft server",
     "game mode", "SaaS").
   - Add a conflict rule (#23-#25).
6. **Select by consequence and relevance.** Rank by severity and by prompt overlap, not ties, so
   the same 7-8 rules stop monopolising the slot (#10). Cost: S.
7. **Long term: defaults over reminders.** Per mature family, a scaffold or skill that implements
   the checkable entries by construction (#6). Cost: L.
8. **Housekeeping.** Cost: S each.
   - `vault/specs/gsd-x-n8.RESUMPTION.md:182` and `family-baselines.RESUMPTION.md:29-32` are stale.
   - `ABANDONED_BY_DEADLINE` is missing from `capsule.py`.
   - The capsule's family layer is hardcoded to PERSISTENT_STATE.

## Open questions and pending Owner decisions

- **Pending in the repo:**
  - The three spec readings in `vault/tower/HANDOFF_W14_CONSTITUTIVE.md` §5. These cover the
    8/1,400 ceiling, which the spec treats as a compiler failure and the code as deferral, and the
    undefined `class` C|D.
  - P3b, stopped with three options (`vault/audits/ucr_cif/17_P3B_RESULT_STOPPED.md:58-65`).
  - The contradicted B0 entry `wii_homebrew-no-posix-headers`.
- **Is CBR mostly a duplicate?** Most B0 origins are rules already in always-loaded context or
  skills. If so, the injection is cost without lift, by checklist #11. Unmeasured.
- **Should promotion be built at all before O1 exists?** The evidence favours measuring the 60
  rules already shipped first.
- **When is a family mature enough to become a scaffold** (item 7), and who owns each family's
  `B<n>` between Owner reviews?
