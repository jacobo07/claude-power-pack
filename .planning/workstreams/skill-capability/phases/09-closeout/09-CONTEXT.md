# Phase 9: Closeout - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44. ROADMAP "Host plane": pillar N and the `--final` run are LAPTOP-ONLY (R1 reads the settings file of
the host it runs on). On gex44 this phase finishes at "every pillar except N terminal, `--pillar <P>` PASS for each";
N stays open by design.
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Everything the closeout needs that IS producible on gex44, plus a laptop hand-off that makes the laptop step one command.

</domain>

<decisions>
## Implementation Decisions

### D-01 Producible on gex44 (do these)
- `reviews.ukdl.file` and `reviews.cbr.file` (CE clause L8, tools/test_cognitive_economy_program.py ~253): write
  `vault/programs/skill-capability/reviews/ukdl.md` (UKDL candidates learned this run — they go to this program's own
  candidates file, NEVER into `vault/knowledge_base/ukdl-universal.md`, which is read-only for this program) and
  `reviews/cbr.md` (case-based review: per pillar, what was predicted, what the terminal was, what evidence moved it).
  Sources: every phase SUMMARY / REVIEW / VERIFICATION and STATE.md decisions; traps worth keeping include: diff options
  after `--` become pathspecs (WR-02 ph1), a verdict must depend on every provenance clause (WR-01 ph2), zero/absent is
  UNMEASURED (WR-03 ph2), an untimed row is UNMEASURED not "not delivered" (W1 ph3), the L5 gate argv must read only
  committed files because `--final` re-runs it on another plane, hook-generated docs stubs must not ride a commit.
- `deltas.product` and `deltas.intelligence` (L8: both non-empty): each entry names a change and its evidence path.
- Ledger edits: only `reviews` and `deltas`; frozen asserted equal to the FROZEN_AT copy; `retained` untouched (it was
  declared at P0 and is checked by R1 on the laptop).
### D-02 Laptop hand-off (do not run on gex44)
- `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md`: the exact command sequence for the Owner on the laptop — fetch
  the branch from the gex44 bare repo (`mission/skill-capability`; note the push from this run was refused by the
  ovo-push-gate hook, see STATE.md, so the Owner pushes or fetches the run branch `mission/skill-capability-run`), run
  every owner-bundle item, run `python tools/test_skill_capability_program.py --final`, then write state.N and
  `CLOSE.md` with the pasted output. List every `[X]` line of `owner-bundle.md` in order with its pillar.
- Owner boundary 4 (push only once no foreign commits interleave) and N's rule ("push happens only once no foreign
  commits interleave") are recorded there as the Owner's step, not done here.
### D-03 Gate on gex44
- A pre-final check (script or documented command list) that runs `--pillar <P>` for every pillar A..M and `--selftest`,
  and prints which pillars are terminal; it must report N as open (expected), never as PASS. Record its output in
  `vault/programs/skill-capability/evidence/pre-final-gex44.md`.

### Claude's Discretion
Review file layout; whether the pre-final check is a script or a recorded command block.

</decisions>

<code_context>
## Existing Code Insights
- R1 retained settings: `tools/test_skill_capability_program.py` `check_retained` (~66-93), --final only.
- L8 reviews/deltas: CE verifier ~253-258.
</code_context>

<specifics>
## Specific Ideas
- CBR table columns: pillar | predicted | terminal | evidence (paths) | what surprised us.
</specifics>

<deferred>
## Deferred Ideas
- state.N, `--final`, CLOSE.md, push -> laptop (Owner).
</deferred>
