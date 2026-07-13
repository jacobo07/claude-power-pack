# Plan — DAIF Session Continuity Cognitive Compiler (2026-07-13)

Scope: build the compiler DAIF-08 Part XI specifies. Do not expand the corpus.

## Sources read before implementing (PASO -1)

- `daif_08_context_runtime_v1.txt` Part XI (lines 203-221) — the proving vertical.
  - 11.3 — the eight required contents of a resume pack.
  - 11.5 — the done-gate: six conjunctive clauses, no partial credit.
  - 11.6 — the seventh clause: FAIL VISIBLY when fidelity cannot be guaranteed.
  - 11.7 — no savings figure asserted in advance.
- `daif_07_obligation_fabric_v1.txt` Part II (the obligation object's slots), Part III
  (the taxonomy — kind determines closure semantics), Part IV (intake gate: a candidate
  must name closure condition + owner + origin, and de-duplication keeps one obligation
  with N source pointers), Part XII (survival is CLOSEABILITY, not a surviving name;
  the gate is binary; the survival drill is adversarial).
- `daif_01_type_system_v1.txt` Part II — the eight typed fields. A HARD constraint is
  `Strength = hard` (may never be silently violated, `Override-policy = no-silent-override`).
  A process rule is `Strength = soft` (tradeable under record). `unknown` is a value;
  an absent field is a defect.

## Units

- SC1 `modules/daif/obligation_extractor.py` — real `.jsonl` in, Obligation objects out.
- SC2 `modules/daif/constraint_extractor.py` — project CLAUDE.md + hard-rule archives in,
  Constraint objects out, each with the file:line it was extracted from.
- SC3 `modules/daif/session_continuity_compiler.py` — the package, written to
  `vault/sessions/continuity_<session_id>.json`.
- SC3b `modules/daif/resume_reader.py` — stdlib-only, repo-independent. Reads ONLY the
  package. This is the far side of the boundary: a fresh OS process with no session, no
  transcript, no repository.
- SC4 `tools/test_daif_session_compiler.py` — 9 V-gates.

## What the reset drill measures, and what it does not

Measured mechanically (fresh process, package as its only input):
clause 1 (100% hard constraints survive), clause 2 (100% open obligations survive),
clause 5 (every critical claim carries an evidence pointer), clause 6 (a source that
changed while the session was down is detected, by sha256 of each constraint source),
plus DAIF-07 12.5 closeability and a no-invention check.

NOT measured: clauses 3 and 4 are behavioral (the resumed actor identifies state
correctly and continues without indiscriminate re-reading). They require the two-arm
LLM trial of 11.7. The package declares them unverified rather than claiming them.

No savings figure. The only numbers this ships are the survival percentages the drill
measures.
