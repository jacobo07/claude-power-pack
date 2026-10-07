# E4 receipt -- UKDL staging (tools/ceps.py)

Verdict: **UNDECIDED**

## What changed
- `tools/ceps.py:502` distribute() stages the UKDL entry via `_stage_ukdl_draft` instead of `_atomic_append(UKDL_PATH, ...)`; `result['ukdl']` now means staged, `result['ukdl_draft']` carries the draft id.
- `tools/ceps.py:928` `_stage_ukdl_draft` writes a `kind=ukdl_entry` draft into the existing DRAFTS_DIR (id = sha1 of the line, so staging is idempotent; returns '' unless the file is on disk).
- `tools/ceps.py:955` `promote_ukdl_draft` is the only code path that appends to the tracked UKDL; moves the draft to `confirmed/`.
- `tools/ceps.py:975` / `:992` `migrate_pending_ukdl`: lines added vs `git show HEAD:<path>`, compared with line endings stripped; dry-run unless apply; a line is removed only after its draft is observed on disk; the blank separator distribute() wrote is removed with it; non-CEPS lines stay.
- `tools/ceps.py:1054` CLI `--migrate-pending-ukdl [--apply] [path]` (prints JSON counts) and `:1060` `promote-ukdl <draft-id>`.
- `tools/ceps.py:890` confirm_draft refuses a UKDL draft (it would otherwise record a bogus event from an empty snippet).
- `tools/test_ceps_drafts.py` new, 9 V-CEPS-* gates, all paths redirected into a tmpdir.

## Commands (exit codes)
- `python -m py_compile tools/ceps.py` -> 0
- `python tools/test_ceps_drafts.py` -> 0
- `MUTANT (direct append restored) python tools/test_ceps_drafts.py` -> 1
- `python tools/test_ceps_drafts.py (after restore)` -> 0
- `python tools/test_ceps_admission.py` -> 1
- `python tools/test_ceps_closed_loop.py` -> 0
- `python tools/test_ceps_corrections.py` -> 1
- `python tools/test_ceps_edge_cases.py` -> 0
- `python tools/test_ceps_full_cycle.py` -> 1
- `python tools/ceps.py --migrate-pending-ukdl (dry-run, real file, read-only)` -> 0
- real `vault/knowledge_base/ukdl-universal.md` sha256 unchanged across the whole run: True

## Mutation
- Restored the direct `_atomic_append(UKDL_PATH, ukdl_entry)` in distribute(): test exit 1 (RED as required). Restored from saved bytes; re-run exit 0.

## Physical tool calls
- 2 at receipt time: 1 read-only inspection of ceps.py, 1 driver that patched, tested, mutated, committed and wrote this receipt.

## Semantic boundaries (named decisions)
- UKDL drafts share the existing DRAFTS_DIR / list_drafts set, distinguished by `kind=ukdl_entry`; promotion is a separate verb (`promote-ukdl`), not `confirm`.
- 'Uncommitted' = added relative to HEAD (difflib over EOL-stripped lines); modified committed lines count as added only if the replacement is CEPS-shaped.
- CEPS shape = `^- [cat/subsystem] `id` -- rule$`, exactly what distribute() wrote.
- Migration was NOT run with --apply against the real file; only the read-only dry-run, per the brief. The coordinator runs `python tools/ceps.py --migrate-pending-ukdl --apply` in the main tree.
- Did not touch ukdl-universal.md; did not grep other callers of `distribute()['ukdl']` (budget) -- the key keeps its bool type, meaning changed to 'staged'.


## Open regressions (why the verdict is UNDECIDED, not PASS)
- `tools/test_ceps_full_cycle.py` exit 1: FileNotFoundError reading `<tmp>/ukdl.md`. It asserts the OLD contract (distribute appends to UKDL). Expected consequence of E4; the test must be updated to assert a staged draft instead. Not done (budget).
- `tools/test_ceps_corrections.py` 7/9: LEAVES-PENDING and DISMISSABLE fail. Probable cause (not verified): confirm_draft -> record_error -> distribute now stages a `kind=ukdl_entry` draft into the same DRAFTS_DIR, so list_drafts() still shows one pending item after confirm/dismiss. Fix options for the coordinator: those two gates count only correction drafts (exclude `kind=ukdl_entry`), or UKDL drafts get a subdirectory. That is a decision about what "pending" means, so it is left open.
- `tools/test_ceps_admission.py` 19/20: the failing gate was not identified in the captured tail. Whether it fails on the parent commit was NOT measured, so do not attribute it to E4 or clear it without a baseline run.
- Physical tool calls: 3 in total (1 inspection, 1 driver, 1 for this addendum). The session cap stopped the fixes.
COMMITS: 873e3e23
