---
date: 2026-10-03
source: vault/plans/skill-virtualization-k-slice-2026-10-03.md (K1-K5)
status: UKDL CANDIDATES -- ukdl-universal.md is dirty from a foreign pane; promote from here when it is clean
---

# Capped skill listing + commit-card aperture: lessons

## Evidence
- C6 (d9072185): 134 name-only overrides -> listing 29,991 -> 30,002 chars.
- K4 (4d1cfb83): 133 pageable skills moved behind a gateway (user-invocable-only) -> listing 30,000 -> 29,795
  chars; startup tokens 87,739 -> 89,844 (noise +-1.5k). Plugin descriptions refilled: described plugin
  entries 22 -> 50. Discovery: described entries 87 -> 103, name-only lines 179 -> 32.
- R1/R2/R3: user-invocable-only removes the name; per-run --settings merges skillOverrides with the user
  map; the Skill tool refuses a user-invocable-only skill ("disabled for model invocation").
- K1 (bf3d526a): 15/35 live commit judgements were `unknown`; `$paths='a','b'` was judged on 'a' only.

## Candidates

HARD RULE (CANDIDATE, 2 independent experiments): descriptor or name suppression in a capped eager listing
is NOT a token reduction while the listing's latent demand exceeds the freed space; claim a saving only
from model-visible startup tokens of a fresh session, never from settings entries or characters removed.

TRAP: projecting a listing change from the text that is SHOWN. The capped listing silently drops
descriptions (least-used first), so the dropped ones are invisible latent demand that refills any freed
space. Measure full demand (every installed skill, plugins included) before projecting a floor change.

TRAP: splitting skill-listing names at the first ':' merges every plugin skill (`plugin:skill`) into one
entry. Split at ': ' (name/description separator).

TRAP: a gateway built from `~/.claude/skills/*/SKILL.md` cannot page plugin or built-in skills (no file
there), and user-invocable-only blocks the Skill tool, so a gateway pages by Read only.

PROCESS: replay real commands through a pure planner with a frozen, anonymised fixture whose rows pin the
EXPECTED plan; gate on exact equality, not on the unknown count -- the count improved while G1 stayed a
wrong judgement.

TRAP (shell parsing in a guard): resolving a PowerShell variable from "the last assignment anywhere"
half-resolves lists (`'a','b'`), concatenations and loop-scoped assignments into a WRONG judgement. Resolve
only a single top-level literal assignment before the use, or report unknown.

TRAP (write attribution): a write made by a tool the session itself ran (`node gsd-tools.cjs`) looks
foreign to Edit/Write/redirect attribution -> false deny (300ac3a1). Open; not fixed.

## CBR
All EXPERIMENTAL. The universal guarantee worth ratcheting later is "capability available without
proportional residency, delivery certified" -- not any override list. Nothing promoted.
