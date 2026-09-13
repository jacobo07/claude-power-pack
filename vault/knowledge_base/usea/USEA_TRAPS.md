# USEA Traps — Phase VII (2026-09-13)

> **Staging file, not a second corpus.** These entries belong in
> `vault/knowledge_base/ukdl-universal.md`. They are parked here because that file
> currently holds ~70 uncommitted prose lines belonging to another author plus ~72
> auto-appended capture rows, and `tools/foreign_hunk_guard.py` returned
> `VERIFY_MISMATCH` twice — it could name the foreign lines but not subtract them.
> Absorbing another writer's seventy lines under this session's message is the exact
> defect the pathspec doctrine exists to prevent, so the append was backed out and
> verified gone (five distinct needles, all zero).
>
> **Merge instruction:** whoever next commits `ukdl-universal.md` — which means the
> author of those seventy lines, who has to commit them anyway — should move the
> section below into it and delete this file. One corpus, searched by rule id, is
> the whole point; a permanent second store would be the fragmentation this estate
> already refuses elsewhere.

---

## A Detector That Flagged Its Own Documentation

One trap, paid for by a failure observed the hour it was written. It generalises
well past the naming question that produced it.

### Traps

**`T-DETECTOR-FLAGS-ITS-OWN-DOCUMENTATION-001`** — A gate whose subject is a
confusion will fire on the prose that explains the confusion, because correct
disambiguation necessarily places the forbidden token beside the very vocabulary
the gate treats as evidence of the defect. WHY IT LOOKS CORRECT: the detector is
right about the neighbourhood. The words really are there, the window really does
carry them, and every clause behaves exactly as designed — it is the CLASS that is
missing, not the matching. ORIGEN: `tools/test_usea_identity.py` was written to stop
two four-letter acronyms in this repository being merged by a future rename, one
naming a live sealed corpus and the other a proposal that was measured and
rejected. It scored 8/8 against the tree that motivated it. One commit later it
scored 7/8, and the single offender was the sentence the gate existed to make
possible: a line in `RESUMPTION_FILE.md` warning a future session not to reconcile
the two. Its window carried the live system's vocabulary and none of the rejected
system's, which is precisely the misattribution signature. WHY THE RECORDED FIX WAS
THE WRONG ONE: this estate had already met the sibling — a document naming
quarantined literals vetoed like a real defect — and the prescription on file was to
describe the subject obliquely. Applied here that destroys the artifact, because a
disambiguation record that may not spell either name cannot disambiguate. The
prescription repaired the PROSE when the defect was in the DETECTOR, which is why
the class recurred. PREVENTION: give the detector an explicit class for deliberate
contrast, and scope that class to the hit's own LINE while topic detection stays
window-scoped — a window wide enough to establish what a passage is ABOUT is far too
wide to establish what a sentence INTENDS. Count the class in the report rather than
dropping it, so an exemption stays auditable; and keep the equivalence clause
separate, so contrast wording cannot launder an alias claim. Both poles of the new
clause are driven synthetically, including a control proving the original red branch
is still reachable through it. DETECTION, and it costs nothing: write the
documentation for the rule FIRST, then run the gate against that documentation. A
gate that cannot survive its own explanation is not finished. SCOPE: universal —
banned-token linters, secret scanners, slop detectors, deprecation sweeps, profanity
filters, any gate whose subject is a string its own docs must quote.

### Candidates REJECTED from this corpus (recorded to prevent re-derivation)

- **"Pathspec-scoped commits and hunk-scoped staging conflict, so the pathspec
  doctrine needs an exception"** — REJECTED as already owned. `git commit -- <path>`
  takes the WORKING TREE and discards a carefully built index, so the two prescribed
  mechanisms genuinely cannot both be obeyed — and `tools/test_commit_scope.py`
  already states the decision table and drives it: guard used, commit from the index
  with no pathspec; guard unused, commit with a pathspec at file granularity.
  Recorded only because it was independently re-derived this session, which is
  evidence the owner is correct and unread rather than absent.

- **"The capture bus writing into a hand-maintained corpus is a defect"** — NOT
  filed. The rows are the estate's own failure-capture layer doing its job, and a
  spec on file (`vault/specs/capture-layer-liveness.md`) shows that layer was silent
  for ~80 days and was deliberately repaired. Noisy diffs in a shared corpus are the
  cost of a producer that works. The real observation is narrower and belongs to the
  hunk guard, not here: its subtract step fails when the foreign lines are near-
  duplicates of rows already in the file, and it fails CLOSED, which is the correct
  half.
