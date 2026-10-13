# Phase 5 Context -- W4 Judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency

Mission rows owned: D15 (judge VALIDATE vs REPLAY), D16 (bounded parallel replay), D17 (reviewer concurrency),
R05 (evidence_bundle A->B->A hole). Depends on Phase 4 (proof inheritance, candidate snapshots), which left
`judge.py` untouched, so closure is necessary-not-sufficient until this phase lands.

## Scope (ROADMAP Phase 5)

1. The judge validates an inherited certificate independently, or replays the gate. Both paths exist and the
   judge chooses per obligation from evidence it derived itself.
2. Independent replays run concurrently under a bound that is lowered under memory pressure.
3. Reviewers bind to a candidate; a review is staled exactly where bytes moved. The A->B->A hole in
   `tools/evidence_bundle.py` (known limit comment at `collect`, :140-141) is closed.
4. RED-first: builder self-certification; gate weakening accepted; stale review surviving mutation.

Out of scope: Phase 6 (mutant farm), Phase 7 adapters, any edit to `GATE_CLASSES`, any new store (S13), any
change to Phase 2 semantics S1-S16, Phase 3's frontier contract or Phase 4's inheritance contract.

## RED list (verbatim from the packet, each gets a gate that is driven red first)

- **builder self-certification**: a worker epoch (or any actor) writes a `proof.inherited` event for a claim whose
  premises it did not earn; the judge must not PASS on that event. Also: judge inside an epoch stays UNJUDGEABLE on
  the VALIDATE path.
- **gate weakening accepted**: a gate edited after acceptance must be REFUSED on the VALIDATE path exactly as on
  REPLAY (the pin is re-verified at the judged tree before any validate or replay).
- **stale review surviving mutation**: after a reviewed artifact changes, the review reads STALE; a mutant that
  skips the staleness comparison must be KILLED by a gate (mutation_drill, isolated copy, valid control).
- **A->B->A in evidence_bundle (success criterion 2)**: bytes A are ticketed, a concurrent writer makes B and puts
  A back, the reply arrives. Today the receipt carries A's hashes and passes. After this phase a review whose reader
  could have seen B is STALE.

## Gray areas decided (no Owner questions)

| # | Decision | Reason |
|---|---|---|
| 1 | VALIDATE lives in `judge.py` beside REPLAY, same `judge()` entry, receipt keeps its shape; only a validated gate row carries `mode: VALIDATE`. REPLAY rows stay byte-identical to today. | One judge, one receipt, legacy equality when no PCC events exist (S9). |
| 2 | The judge never reads a `proof.inherited` event as a fact. It re-derives the six premises at the judged worktree with `inherit.observe_current` + `proof.observe_premises/state_from_premises`, and re-checks `inherit.ineligible`. The event is only a claim that the sweep opted in. | S3: "the event is a CLAIM"; defence is recompute-on-validate (Phase 5). |
| 3 | Any doubt (changed, unknown, ineligible, switch off, unknown candidate) -> REPLAY. VALIDATE can only turn a replay into a skip, never a refusal into a pass. | Unknown Escalates. |
| 4 | An all-VALIDATED goal may PASS without any gate being run at this tree. The receipt says how many were validated and names each certificate. | S9 explicitly allows it; the pin and premises are re-verified, which is the independent evidence. |
| 5 | Parallel replay reuses `frontier.gate_unit` + `proof.independent` for the pairwise rule and `frontier.bound` (posture, `max_parallel`) for the ceiling. The judge reads the budget from `state.budget`. Default posture ECONOMY = bound 1 = today's serial loop. | Phase 3 seam; no new store or posture. |
| 6 | Memory pressure only LOWERS the bound: free RAM < 1536 MB -> 1, < 3072 MB -> at most 2, unreadable -> 1. `GSDX_REPLAY_MAX` (env, positive int) can lower it further. `GSDX_FRONTIER` off -> 1. | The laptop is RAM-starved; unknown escalates to the safe side. |
| 7 | Result order is the obligation order, whatever the completion order. A timeout/OSError row stays UNJUDGEABLE and outranks a REFUSED row, as today. | Receipt equality between serial and parallel is itself a gate. |
| 8 | A->B->A closure = two layers: (a) the ticket takes the bytes it hashes once, hashes that buffer and stores it as a read-only snapshot; a reply that echoes the snapshot line is bound to the snapshot bytes, not the live tree. (b) a reply that does not echo it is a live read and must prove the live files did not move: a per-file stat journal (`mtime_ns`, size, inode, and ctime on POSIX) taken at ticket time is compared at reply time. | A content hash cannot see A->B->A; a snapshot makes it irrelevant, a journal makes the live read conservative. The residual (a writer that restores mtime on Windows) is recorded, not hidden. |
| 9 | `review.received` lands as code in `proof.py` (same move as `candidate.promoted` in Phase 4): the frozen-table row moves to the landed table in spec S7, and the Phase 2 vocabulary gate's expected lists are updated in the same commit. Required fields stay `claim_id, candidate, ticket`; `verdict, artifacts, reviewer, worker, read_from` are additional. | Frozen-table law: a type in code must be declared as landed. |
| 10 | A review is VALID iff its artifact hashes equal the current bytes, the reviewer is not the worker, and (for a live read) the journal held. It is STALE only for the reviews whose own artifacts moved. A valid non-APPROVE review blocks. | "staled exactly where bytes moved". |
| 11 | Reviewer concurrency = many tickets per claim in flight, each its own nonce; the goal log CAS (`LostRace`) arbitrates; the writer re-projects and retries a bounded 3 times. Nothing is serialised by a lock file. | S13: the log is the only store. |
| 12 | New modules are wired in the SAME commit (judge -> `tools/gsd_x_goal.py judge`; review -> a `review` subcommand), else declared in the liveness registry. | Liveness Standard. |
| 13 | Mutation drills are written as JSON under `drills/` and run one per call; the goal mutation suite is NOT run on the laptop. If a plan edits an anchor line that suite uses, re-anchor with the same mutant and gate, record it, list the suite UNRUN. Anchors on `judge.py` (`if moved:`, `if environ.get(EPOCH_ENV):`, `if actual != tree_hash:`, `if not satisfied:`, the `current()` equality line) are left textually intact by design. | Packet rule and the Phase 4 incident. |

## Reuse (no new stores)

`proof.py` (ledger, `observe_premises`, `state_from_premises`, `independent`, `append_pcc`), `inherit.py`
(`observe_current`, `ineligible`, `inherited_ids`), `frontier.py` (`gate_unit`, `bound`), `candidate.py` snapshots,
`git_state.py` (`tree_id`, `digest_matches`, `blob_oid`).
