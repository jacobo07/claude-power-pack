# Handoff [S] -- universal baseline compiler -> baseline owners

Pillar: [S] universal baseline compiler. Terminal: MERGED_INTO_EXISTING_OWNER.

Owners (frozen): `tools/baseline_ledger.py`, `tools/family_baseline.py`.

Frozen rule: "audit trait->obligation derivation; extend only on a measured gap".

## What the audit found (evidence: `vault/programs/cognitive-economy/measure/s_demo/derive_stdout.txt`)

- Neither frozen owner derives obligations. `tools/baseline_ledger.py` is a per-project version ratchet
  (register / elevate / validate / Obsidian mirror); `tools/family_baseline.py` builds and verifies cited baseline
  generations over `modules/tower` (B0 from VERIFIED citations only, weakening detection, revert with authority).
- The trait->obligation derivation already exists in another owner: `modules/gsd_x/mission/obligation.py`, driven by
  `python tools/gsd_x_mission.py derive <root>`. It extracts facts from the intent and the project's own README
  (regex patterns that encode structures, not domain nouns), applies four operators (irreversibility, absent
  signal, measured failure, unfalsifiable parity), and refuses any candidate without a named consequence.
- Demonstrated on a real project's reality (the ABSW2-Wii README, on temp roots so nothing was written into the
  project): "faithful port ... identical to the original" -> 2 facts -> `DO-4 UNFALSIFIABLE_PARITY_CONSEQUENCE
  ACCEPTED`; the same port without a fidelity requirement -> 1 fact, nothing derived (correctly: no parity premise);
  "fix a typo" -> 0 facts, nothing derived (negative control).
- Liveness: `python modules/liveness/reachability.py` reports `gsd_x/mission/obligation` (and its whole package) as
  ORPHAN. Its live edge is a GSD capability (`capabilities/cpp-gsd-x-mission/capability.json`, `ship:pre`), which
  the PP scanner does not model, and the hook renders only where a project sets `gsd_x_mission.enabled`. So the
  capability exists, is tested, and is opt-in per project.

## Decision

No measured gap justifies a second derivation inside the baseline tools: building one would duplicate a live owner.
Nothing is extended. The finding is handed to the baseline owners so a future "universal baseline compiler" request
starts from `gsd_x_mission derive` rather than from `baseline_ledger.py`.

## What the owners keep

`tools/baseline_ledger.py`, `tools/family_baseline.py`, `modules/tower/*`, and `modules/gsd_x/mission/*` (its own
owner). Nothing edited by the campaign.
