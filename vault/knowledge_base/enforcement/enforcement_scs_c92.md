# SCS C92 — Enforcement-Systems-Active: the brakes are reconnected

> Sealed 2026-07-12. Predecessor: SCS C91 (SQI-Executable).
> Origin: the AKOS Macro Knowledge Audit (42 projects, 439,343 files inventoried).

## The finding this answers

The system does not have a knowledge problem. It has ~311 doctrinal units, 147 hard
rules, and 11,091 learning-class files. It has an **enforcement problem**, and the
audit's single sharpest sentence is that *a documented rule failing to prevent the
thing it documents* is the most-repeated failure on the disk.

**The kill switch could not fire.** Verified independently on this disk before any
code was written:

| Branch the global router named | Reality |
|---|---|
| `vault/knowledge_base/ukdl-universal.md` → `§ HARD-RULES` | The file exists (247,496 B). It contains **zero** headings matching HARD-RULES. The anchor does not resolve. |
| the file that *does* hold `## §HARD-RULES` | `core/HARD-RULES.md` — **369,933 B**, against the Read tool's 256 KB hard limit. Unreadable. |

Four trigger classes (production write, deploy, done-claim, plugin install) depended
on it. It fired zero times.

## What shipped

| # | System | Module | Gate |
|---|---|---|---|
| P1 | Rule Compiler | `modules/rule_compiler` | corpus → validated DB + **2,154 B** digest (cap 4,096) + rejection report |
| P2 | Artifact Done-Gate | `modules/done_gate` | done is an artifact on disk, never an exit code |
| P3 | Sweep Enforcer | `modules/sweep_enforcer` | a prevention rule is unsealable until it survives its own sweep |
| P4 | Reference Linter | `modules/refcheck` | every path a doc names is resolved; credentials flagged |

**Gate:** `python tools/test_enforcement_systems.py` → `ENFORCEMENT_PASS=19/19`, ×3
hermetic, exit 0. Every gate is asserted in BOTH directions — a gate observed only to
PASS is not a gate, it is a function that returns True.

**Kill switch:** `~/.claude/CLAUDE.md` router now points at
`~/.claude/knowledge_vault/core/HARD-RULES-DIGEST.md`, which exists, is 2,154 B, and
was read with the Read tool without hitting a limit.

## Corpus, compiled

156 rules across two archives and three schemas → **143 binding, 13 rejected.**

The rejected set includes the 5 the audit named, plus `HR-005` (its ACTION is a
markdown table fragment). `HR-002` — TRIGGER `"Test recognizer for pipeline"`,
EVIDENCE a literal `ZZZ`, sealed at **SEVERITY: CRITICAL** — is now inert. A rejected
rule is not deleted from its archive; it is denied the ability to fire, and listed
with a per-field reason so it can be repaired.

Boilerplate is detected by **measurement, not blacklist**: an ACTION shared verbatim
by two or more rules is template filler by definition, because a real action is
rule-specific. That is how `HR-006`/`HR-007` were caught.

## What the systems found on first contact with this repository

**1. The Sweep Enforcer caught itself.** Its first real sweep — HR-4/U-25, "vault
writes must be atomic (`os.replace`), never append-mode" — found **35 append-mode
writes** across `modules/` and `tools/`. One of them was `tools/rule_sweep.py`, the
enforcer's own ledger, written twenty minutes earlier. Fixed. The other 34 are
reported, not silently absorbed into the diff.

**2. U-2's exact shape, still live.** Fourteen hand-copied `_atomic_write*` helpers
exist in this repo. Thirteen use `os.replace`. One —
`modules/cpc_os/work_state_saver.py:193` — delegates correctly on the happy path but
its bare-except fallback degrades to a **non-atomic `path.write_text`**, reopening the
corruption window the rule exists to close. A convention repeated by hand in N places,
missed in one. **Owner call:** the fallback should probably raise rather than degrade.

**3. The audit's numbering was wrong, and following it would have made things worse.**
The report proposed appending U-23…U-26 believing the ledger held 22 entries. It held
**24**. Appending as written would have manufactured four fresh collisions on top of
the two it was meant to fix. And the report had the U-17 duplicate backwards: the
**first** copy is the damaged one (its backtick code spans were eaten), the second is
intact — "keep the more complete version" applied literally would have destroyed the
good copy and kept the mangled one.

**4. U-16 was never a duplicate.** It was an **ID collision between two distinct
lessons** (a subscription freshness gate, and the heredoc/merger-race corruption).
Deleting one would have destroyed a real lesson. It was renumbered to **U-25**, not
deleted. The ledger is now U-1…U-29, every id unique, zero gaps, nothing lost.

**5. The file was a victim of the bug it records.** `## How to extend this file` was
wedged *between* the two U-16 entries — displaced exactly as U-16's own heredoc/merger
lesson predicts. Repaired with an atomic `os.replace`, which is what that lesson
prescribes.

**6. A trigger class with no rules.** `PLUGIN-INSTALL` — one of the four the router
fires on — matched **zero** binding rules in the corpus. The kill switch fires on
plugin installs and finds nothing to enforce. Not a bug; a genuine gap.

**7. The Secret Firewall would have missed both real credentials.** Its
`generic_secret` pattern requires a 16+ character value and matches only
`secret|password|api_key|access_token`. The two live leaks on this disk were an
`auth_token` browser cookie (key absent from that alternation) and a **12-character**
`.env` password (under the length floor). Both would have passed. P4 adds a
corpus-scoped layer rather than widening the firewall's shared thresholds — which
could not be changed without a sweep of their own.

## Lessons sealed

`U-26` a rule archive is a machine artifact, not prose · `U-27` an auto-generated rule
must pass a schema gate or be rejected · `U-28` a queue with a pending flag needs a
depth alarm on the day it is created · `U-29` governance volume is not governance.

## The boundary that held

P1–P4 are all **gates**, and none of them are documents. That is the entire thesis:
adding a 27th universal lesson to a ledger nobody reads is, by this audit's own
finding, the least effective action available. The only intervention on this disk with
a demonstrated success record — the Windows Bash-bridge rule — worked because it was
promoted into an **always-loaded active gate**, not because it was written well.

**Not built, deliberately.** P5 (outbox drain, 38,847 envelopes) and P6 (`gov-audit`)
are outside this build's scope. The 34 remaining append-mode sites were reported
rather than swept into an unrelated 34-file diff — the collapse proposal (one shared
atomic-append helper) is the recommendation, and it is the Owner's call.
