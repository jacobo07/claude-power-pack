---
type: concept
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-cbr-external-research, 2026-10-01-cbr-internal-inventory]
---

# Maturity transfer (capabilities, not lessons)

**Owner's question (2026-10-01):** can a very developed system (Orca X, KobiiCraft) raise the
maturity baseline, and drive autonomous feature brainstorming, for every other piece of software,
"and not only lessons"?

## The distinction

| | lesson | capability (maturity) |
|---|---|---|
| comes from | an incident | the mature system's source: what it does that a young one doesn't |
| form | "never X" / "when X, don't break Y" | "a system with trait T has capability C at level L" |
| applies by | family vocabulary in a prompt | **traits**: what the target system *is* |
| safe to auto-apply | often, as a constraint | no: a feature changes the product, so it is a **proposal** |

What PP transfers today is entirely the left column:
- 10 global rule files carry Orca X incident evidence (`~/.claude/knowledge_vault/rules-evidence/`,
  grep 2026-10-01).
- The CBR B0 rules are restated governance ([[cbr-gap-analysis]]).
- The capsule carries deposit lessons.
- "Hidden Invention", the closest designed concept to the right column, is in the backlog with no
  code (`docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md:323-325`).

## Why traits, not families

*Interpretation.* Orca X (desktop fork) and a SaaS share no family, but can share traits: holds user
work across restarts, runs effects on someone's behalf. Abstracted procedures transfer across tasks;
detailed trajectories do not; mismatched transfer harms hard cases ([[2026-10-01-cbr-external-research]]
§7f). Industry scorecards apply checks by filters, not by one exclusive type (§8a).

## Pipeline (proposed, not built)

1. **Harvest** the mature repo's capabilities from source, by level (L1 works · L2 survives failure ·
   L3 operable · L4 evolvable · L5 product · LG governed) with enabling traits and a portable form.
   The inventory must come from code, not description (rule `capability-preserving-compaction`).
2. **Profile** the target: traits present / absent, capabilities it already has.
3. **Gap diff**: catalogue entries whose traits the target has and whose capability it lacks.
   Each becomes a ranked **proposal** with evidence, accepted or rejected with a reason.
   This is the "autonomous brainstorming": grounded in a system that exists, so it cannot invent
   features no mature system has.
4. **Ratchet** accepted proposals into per-trait CBR generations. Rejections teach the catalogue
   what does not transfer.

Measure before scaling: record acceptance, and later whether an accepted capability prevented
anything (CBR fix #3, [[cbr-gap-analysis]]).

## Pilot

KobiiCraft (source) → KobiiSports Resort (target), 2026-10-01: a hard pair (Paper server vs Wii
project), chosen so that most direct transfer *should* fail. Results:
[[maturity-transfer-pilot-kobiicraft-ksr]].

What the pilot changed in this model:
- **Traits are judged per plane** (product vs dev/infra). 11 of 23 transfers needed
  T-LIVE-SERVICE, which KSR has only on its infra plane.
- **The unit is the portable form, not code.**
- **L2-L4 transfer well; L5 feature ideas are few and are Owner decisions.**
- **Maturity is a vector, and transfer runs both ways.**
