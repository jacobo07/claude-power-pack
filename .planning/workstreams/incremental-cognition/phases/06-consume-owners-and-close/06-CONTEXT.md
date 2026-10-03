# Phase 6: Consume owners and close - Context

**Gathered:** 2026-10-03 (GEX44, orchestrator; discuss skipped via workflow.skip_discuss)
**Status:** Ready for planning (J, M externally blocked on this host -- see evidence)
**Mode:** Auto-generated from ROADMAP + frozen rules J, M, N. Pillars J, M, N.

<domain>
## Phase Boundary

Goal: J and M closed by R2 against CE/SC ledgers on HEAD; UKDL 3-level and CBR reviews; deltas; done-gate.
Depends on: CE and SC landing their ledger commits on this line of history.

Frozen rules (immutable):
- **J** consume CE D, E, I; the Ralph fresh worker with an 8 KB card is the zero-transcript path. Predicted
  MERGED_INTO_EXISTING_OWNER. R2: needs `owner_ledger` evidence for CE D, E, I at a commit reachable from HEAD.
- **M** dispositions only: CE Q/N/O/M and the pre-registration pattern of this verifier already own them; an
  unrestricted optimizer is rejected. Predicted MERGED_INTO_EXISTING_OWNER. R2: CE Q, N, O, M.
- **N** closeout: candidates go to `vault/programs/incremental-cognition/ukdl-candidates.md`; promotion into
  `ukdl-universal.md` and CBR is reviewed, never silent. Predicted MERGED_INTO_EXISTING_OWNER
  (owners `vault/knowledge_base/ukdl-universal.md`, `tools/baseline_ledger.py`).
</domain>

<evidence>
## Measured on GEX44, 2026-10-03

- `vault/programs/cognitive-economy/ledger.json` and `vault/programs/skill-capability/ledger.json` at HEAD: every
  pillar's `terminal` is null. CE's phase-1 commit `21671d6c` is NOT in this clone (`git cat-file -t` -> not a
  valid object); `origin/feature/knowledge-acquisition` has no CE ledger. => R2 for J and M (and H, I) cannot be
  satisfied on this host now. This is EXTERNAL to this program: the CE/SC missions run on the laptop.
- Done-gate wiring: L8 (`--final`) needs `reviews.ukdl` and `reviews.cbr` each `{file}` that exists, and
  non-empty `deltas.product` and `deltas.intelligence`. Never edit `vault/knowledge_base/ukdl-universal.md`
  (ROADMAP operating constraint) -- candidates file only.
</evidence>

<decisions>
## Implementation Decisions

- **J and M:** do NOT write terminals. Write `vault/programs/incremental-cognition/evidence/JM-blocked.md` naming
  the exact R2 inputs needed (ledger path, pillar, the terminal each frozen rule expects) and a `[J]` / `[M]`
  owner-bundle line: "after CE lands D, E, I (J) and Q, N, O, M (M) on a commit reachable from this branch,
  run `python3 tools/test_incremental_cognition_program.py --pillar J` after adding owner_ledger evidence".
  Optionally add a small helper `tools/ic_r2_evidence.py` that, given a commit, reads the owner ledger at that
  commit (reusing `test_incremental_cognition_program.OwnerLedgers`) and PRINTS the owner_ledger evidence rows to
  paste -- read-only, tested on the real fa9ae2ed pole (pillar A open) if present, else on a fake.
- **N (this run's closeout, partial):** write `vault/programs/incremental-cognition/ukdl-candidates.md` with
  three levels (universal / domain / project) of candidate learnings from THIS run, each citing evidence
  (e.g. stale env installs silently disable a fix that exists in the repo -- a7 at 0119999 lacked
  provider_breaker; host-written refusal rows; plane-dependent test reds such as node v18). Write the CBR review
  file `vault/programs/incremental-cognition/reviews/cbr.md` and the UKDL review file
  `vault/programs/incremental-cognition/reviews/ukdl.md` (each: what was reviewed, verdict per candidate:
  PROMOTE-PROPOSED / HOLD / REJECT, reviewer = this run, promotion itself left to the Owner -> `[N]` line).
  Set ledger `reviews.ukdl` / `reviews.cbr` to `{file, sha256}` and append concrete `deltas.product` /
  `deltas.intelligence` entries for what phases 1-5 actually shipped (only shipped and tested things).
  `state.N` stays OPEN (promotion is reviewed by the Owner; CE T institutional GC is external).
- Run `python3 tools/test_incremental_cognition_program.py --status` and `--final`; record the exact output in
  evidence. `--final` is EXPECTED to FAIL (open pillars) -- report the failure list honestly; never paper over it.
- Ledger edits: only `reviews`, `deltas` (and never `frozen`); after editing, `--selftest` must still PASS and
  `--status` must show no violations.
- Commits: explicit pathspec, `git commit -F <msgfile>`, plain single git commands, verify `git log -1`. Never push.

### Claude's Discretion
Wording of candidates; helper script shape.
</decisions>
