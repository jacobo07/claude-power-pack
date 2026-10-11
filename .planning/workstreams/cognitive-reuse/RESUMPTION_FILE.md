# RESUMPTION — cognitive-reuse (read cold, act)

**Identity.** Worktree `C:\Users\User\Apps\_wt-cognitive-reuse`, branch `sprint/cognitive-reuse`. Work by absolute path; git via `& 'C:\Program Files\Git\cmd\git.exe' -C <wt>`. Thesis: CPP never pays twice for validated cognitive work; "assimilated" is computed from coverage. Binding: `OWNER-PROMPT.md`, spec `vault/specs/cognitive-work-reuse.md`.

**State.** Sealed: P1 forensics audit, P2 spec, P3 `modules/cognitive_os/coverage.py` (manifest, BEGIN/FILE/COMMIT ledger, 9-state verdict, ensure(), CLI) + `tools/test_corpus_reuse.py` 20/20; `test_cognitive_os_build.py` 68/68. Pending: P4-P9. Anchor: `git log --oneline -3`.

**Decisions.** Content sha256 is identity. Kill switch `PP_CORPUS_REUSE=off` -> UNKNOWN. Ledger `vault/cognitive_os/coverage_ledger.jsonl` (default). UNKNOWN is never PASS. `.gf_*` zero-byte deletion only after Graphify producer fix and a re-list.

**Next 3.** (1) P4: lock via `knowledge_acquisition/runlock.py` around record, atomic ledger append, concurrent-writer test (case M), `verify` rebuild (N). (2) P5: CO-03/FD-00 consult + fail-open sentinel hook incl. subagent spawns, hook-boundary proof. (3) P6 honest backfill.

**Start.** Read this, STATE.md, run `python tools/test_corpus_reuse.py`, continue P4. Hard stop on Owner-authorization needs.
