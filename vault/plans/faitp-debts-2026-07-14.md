# FAITP debts — executed 2026-07-14

Follow-up to `faitp-round-2026-07-14.md` (commits f71e3b9 + 1292d80). Three debts, all closed.

## Premises the plan asserted, and what was actually true

A plan is a hypothesis about the repo. Both of this one's paths were wrong, and one of its
two problem statements was wrong. Verified before acting (HR-PREMISE-001):

| plan asserted | reality |
|---|---|
| `vault/knowledge_base/UKDL/ukdl_candidates_*.jsonl` | lives in `~/.claude/state/fable_distillation/` |
| `~/.claude/MEMORY.md` | lives in `~/.claude/projects/<slug>/memory/MEMORY.md`, and had grown to **23,068 B** |
| "candidates have no `status` field" | **they do.** It is a CONSTANT no producer can change |

## D1 — the UKDL queue

The debt was misdiagnosed as a missing field. Every row already carried
`"status": "candidate -- Owner promotes to ukdl-universal.md"` — stamped at write time,
mutable by nothing. **The missing thing was the state machine, not the schema.** Proof it was
lying: all three candidates had been promoted into `ukdl-universal.md` the previous turn and all
three rows still read `candidate`.

`modules/fable_distillation/ukdl_queue.py` adds the transition producer as an **append-only
sibling ledger** (`ukdl_transitions_*.jsonl`) — the same discipline `fd04_proofs` keeps toward
`deposits`; rows are never rewritten. Effective status is DERIVED as latest-transition-wins,
default `pending`. Promotion is **fail-closed on the lie that matters**: a promotion naming a rule
absent from the archive is refused (observed refusing `HR-DOES-NOT-EXIST-999` before the real
backfill ran). Three real promotions backfilled; **pending is now 0**.

Sealed as `T-UKDL-CANDIDATES-WRITE-ONLY-001`.

## D2 — MEMORY.md compaction, non-lossy by construction

23,068 B → **16,223 B** (ceiling 17,408). **Nothing deleted.** Every one of the 99 entries keeps
its row and its link; two new entries were added (101 total). The previous long-form hooks are
preserved **verbatim** in `MEMORY_ARCHIVE.md`, so a shortened hook is always recoverable, and the
detail was already in each linked topic file. `V-MEMORY-POINTERS` asserts entry count against the
archive AND resolves every local pointer — a broken link would be the orphan-pointer trap.

## D3 — the residual-move compiler

`modules/hard_rules/residual.py` implements `PR-PROHIBITIONS-DO-NOT-CONFLICT-001`. It joins the
prohibitions of the fired rules over a declared move universe and returns the surviving moves. It
**never outputs "the Hard Rules conflict"** — that sentence is the bug.

It refuses in three ways, on purpose, and each refusal is gated on real data:

- **`UNSAFE_JOIN`** — a MANDATE in the join. Mandates *can* genuinely contradict; treating one as a
  prohibition would manufacture a resolution that does not exist.
- **`UNDECIDABLE`** — a rule whose forbidden object cannot be determined. Guessing the scope of a
  STOP is precisely the recency bug.
- **`NO_RESIDUAL`** — a rule that forbids the residual itself: the seam the frontier answer named
  against its own design, surfaced rather than hidden.

Verified against the real SCS C92 shapes. The credential deadlock (HR-SECRET-007 + HR-SECRET-003 +
anti-waiting) resolves to a legal residual: modelling `CLOSE_WITH_PASSIVE_WAIT` as its own move class
is what dissolves it — the anti-waiting doctrine binds the *form of the closer*, not the state of
being blocked, exactly as the scope corollary predicts.

### The premise was measured, not assumed

Fable's load-bearing claim is that every Hard Rule is a prohibition. A deterministic classifier over
the live corpus: **156 rules — 126 prohibitions, 0 mandates, 30 undeterminable.** Zero mandates in
156 rules is independent support for the frontier claim, produced by a different actor than the one
that made it. The 30 undeterminable rules are fail-closed, not waved through, and they are the honest
gap (many are the heading-scrape rules SCS C92 already flagged).

**No difference from Fable to report.** The compiler reached the same reframing on the same cases.

## Not done, on purpose

`PR-PROHIBITIONS-DO-NOT-CONFLICT-001` stays a **Process Rule**. Promotion to Hard Rule requires a
REAL conflict to exercise the compiler in production — a passing fixture is not an incident. The
mechanism is now in place so the next real conflict can be the evidence.

## Gates

`tools/test_faitp_debts.py` — **14/14 ×3 hermetic**. `tools/test_faitp_contrast.py` — 7/7, unchanged.
