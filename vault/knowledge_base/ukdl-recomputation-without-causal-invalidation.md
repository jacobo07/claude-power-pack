# UKDL entry: RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION

Merge target: `ukdl-universal.md`, appended after `HR-CANDIDATE-DEFAULT-ENVELOPE-IS-NEVER-OWNER-AUTHORITY`. It is a separate file because that file carried another writer's uncommitted lines (~1,500 on 2026-10-24) and the patch `vault/salvage/residual-fsck-ukdl-entry.patch` no longer applied. When this entry is merged, delete this file and the patch in the same commit. Plan aa97ebf8 R6, goal ctx-rent-a2.

### RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION

A derived answer (a refusal, a count, a "remaining", a resumption brief) is read without checking whether the inputs it was derived from moved, or whether it had a per-subject view at all. Dedupe 2026-10-23: no existing entry covers it; the denominator entries (coverage over a discovered population) are a neighbour, not this.

**Symptom** (all 2026-10-23): 58 identical E4b2 refusals, because the arm path re-ran the same admission with no invalidator on the floors it read; ASER capsules "3 unexplained" because events were counted per day instead of joined per capsule; ctx-rent-a2's lease remainder (1,119,722, lease scope) read as programme headroom (executable 17,119,722, programme scope) because the two denominators were unlabelled; a RESUMPTION_FILE saying "do Slice B" days after Slice B was applied.
**Root cause**: the answer is stored or recomputed without naming its inputs, so nothing can say "an input moved, recompute" or "no input moved, do not retry". Counts grouped by a convenient key (day) rather than the subject (capsule) are the same defect: the view is not keyed by what it describes.
**Guard**: label every denominator by scope (2259ca87); one disposition per sealed capsule, joined capsule -> claim -> verdict (fa840b3c); goal-settle never re-charges a pane's prebind history without a mark (7eafc2b0); `tools/cpp_fsck.py` checks stranded leases, parked-chain polling, unclassified dirty worktrees, resumption anchors outside HEAD, capsules without disposition and unlabelled denominators, read-only, UNKNOWN never PASS (`tools/test_cpp_fsck.py`).
**Trap 1**: a hand-written view with a "coherence anchor" proves nothing until something compares the anchor with HEAD. The anchor line is a claim; the ancestry check is the evidence.
**Trap 2**: a retry that re-reads the same inputs is not a new attempt. Counting retries without a declared input difference reports 58 attempts of one question.
