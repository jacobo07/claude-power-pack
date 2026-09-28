# exp-successor-packet-001 — WITHDRAWN before any run

Registered 2026-09-28T16:52:42.462Z (sha256 `da1288b45b49283e97ae49e3bcae952031dc2a57383e7145b99a7a1da7da068d`).
**No run was dispatched and no output was seen.** Withdrawn on inspection of the registered
material, because the candidate arm could not have tested what it was registered to test:

| case | candidate packet | why it could not carry the answer |
|---|---|---|
| reuse-refusal | PARTIAL, 7,530 bytes | `tools/verified_reuse.py` cut at the whole-file excerpt budget before line 170, where the answer is |
| handoff-and-cap | PARTIAL, 1,055 bytes (manifest only) | `tools/gsd_mission.py` blocked whole: one line matches the vendor's credential-assignment filter, so none of its 100,299 bytes were excerpted |

Running it would have measured "a card that points at missing evidence", not the placement
question. Its successor, exp-successor-packet-002, uses Task Context selectors (the region the
work is about, hash-bound per range) and refuses to register unless every candidate packet is
COMPLETE — the exact defect above, made a precondition.

The registration and material are kept unchanged beside this note, so the withdrawal can be checked.
The dry-run placement numbers were re-measured under 002.
