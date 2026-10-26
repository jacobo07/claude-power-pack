---
covers: [ctx-rent-obs-t3, context-rent-observatory, top-level-boot-floor, c3-contract]
status: AWAITING OWNER APPROVAL (2026-10-26). Nothing armed, no authority moved, no pane launched.
mode: EXECUTION (W8-W11). No ULTRA-PLAN.
parent: vault/plans/context-rent-observatory-t2-2026-10-25.md; finding vault/programs/ctx-rent-obs/ESTATE.md
---

# Context Rent Observatory, tranche 3: the top-level boot floor

## 0. Verdict
- ESTATE (W6) puts top-level sessions at 92.5% of the week's processed tokens (35,586 calls, mean floor 108,197).
  Each 10K off that floor is ~356M processed per week. Worker routing is worth ~107M at best. This is the lever.
- B2 attributes ~46-48K of a ~104K boot to named sources (skill listing 8,361, agent listing 7,598, PP CLAUDE.md 6,350,
  global CLAUDE.md 5,323, MEMORY.md 4,825, host prompt 4,065) and leaves ~52K unattributed. No source above 10K.
- So the floor is many medium sources plus one large unknown. Tranche 3 attributes the unknown, measures removal of
  the two largest removable groups with mechanisms that already exist, and ends in a **proposal**. It edits nothing.

## 1. Facts this plan rests on
| fact | source |
|---|---|
| top-level 257 sessions, 35,586 calls, mean floor 108,197 in week 10-18..10-25 (laptop) | `ctx-rent-obs/ESTATE.md`, `b2/estate-week.json` (7c4d9be7) |
| background worker boot attribution, ~52K unattributed | `ctx-rent-obs/B2.md` (066a6e92) |
| laptop interactive call-1 floor 106,769 (36d35fab) | `b1/slice-b-census.laptop.json` (e2dc477a) |
| `tools/context_floor_census.py <sids> --json` and `tools/floor_regression_gate.py --probe [--cwd]` | t2 plan section 1 |
| t2 ran 8,839,459 against 4.0M because it ran inline in a ~150-190K/call coordinator pane | `ctx-rent-obs/STATUS.md` tranche 2 |

## 2. Boundaries
- **ccr-vm T0B** task 1 measures host floor against total CPP floor on a bare headless call. Tranche 3 does not; it
  measures removal of single source groups on a loaded pane. If T0B lands first, W8 cites its host floor.
- **No config edit.** Removing a source for real touches `~/.claude` (HR-001) and changes behaviour; W10 proposes,
  the Owner decides, a later tranche executes.
- Run by a **fresh** pane (section 6), never by the pane that wrote this plan.

## 3. Work units (laptop plane; pathspec commits under `vault/programs/ctx-rent-obs/b3/` and `STATUS.md` only)

### W8 Top-level boot attribution (no model probes)
1. Commit `b3/selection.json` first: N >= 6 top-level laptop transcripts from the last 7 days, at least 3 repos, rule
   stated (e.g. 2 newest per repo with >= 20 calls).
2. `context_floor_census.py <sids> --json b3/toplevel-boot-census.json --top 20`.
3. Add what the census does not see: hook `additionalContext` blocks recorded in each transcript (SessionStart,
   first UserPromptSubmit), always-loaded `~/.claude/rules/*.md`, MCP server instructions, deferred-tool listing.
   chars/3.6 per block, marked ESTIMATE; the call-1 total stays the only measured figure.
4. `B3.md`: per source, size and repo spread; the remainder labelled UNATTRIBUTED, never folded into a named row.

### W9 C3: frozen removal contracts (at most 2)
1. Pick the 2 largest source **groups** from W8 that a flag of the installed binary already removes. Read
   `claude --help` at run time; name only a flag it prints. No settings, env file or hook edit. None found:
   verdict UNMEASURABLE, stop W9.
2. Commit `b3/contracts/C3a.json` (and C3b) FIRST: group, flag, instrument, frozen saving band from W8, pass rule
   (probe reaches its first tool call and answers the fixed probe prompt correctly).
3. 2 matched pairs each via `floor_regression_gate.py --probe --cwd <repo>`.
4. Verdict CERTIFIED / REFUTED / UNMEASURABLE in a commit after the contract commit.

### W10 Reduction proposal (no edits)
`b3/PROPOSAL.md`: ranked candidates. Each row: source, saving per call (measured from W9, or ESTIMATE from W8),
weekly processed value (x 35,586 calls, labelled processed not billed: cache reads bill lower), behaviour risk (what a
session loses), the exact edit and its revert. The Owner picks; nothing applies here.

### W11 Receipt
`STATUS.md` tranche 3 section; the pane books its own spend: `goal-settle --goal ctx-rent-obs --session <sid>`
with a UTC cut or `--measured` from `session_tokens`.

## 4. Done-gates
- **W8:** `B3.md` with N >= 6, selection committed before the census, UNATTRIBUTED stated as a number.
- **W9:** each verdict commit after its contract commit, or UNMEASURABLE with the reason.
- **W10:** every row names its evidence class (measured / ESTIMATE) and its revert.

## 5. Budget (processed input incl. cache reads; fresh pane ~105-110K/call)
| unit | P50 | P80 | P95 |
|---|---:|---:|---:|
| W8 attribution | 0.6M | 0.9M | 1.2M |
| W9 C3 (<= 8 probes, 0.2-0.45M each) | 1.6M | 2.4M | 3.2M |
| W10 proposal | 0.3M | 0.4M | 0.6M |
| W11 receipt | 0.2M | 0.3M | 0.4M |
| **total** | **2.7M** | **4.0M** | **5.4M** |

- **HARD AUTHORITY asked:** 4,000,000 (P80). Programme 17,714,380 settled + 4,000,000 = **21,714,380**.
- **Lineage:** t2 ran 2.2x its P80, all of it coordinator-pane carriage. The control is section 6, not a wider band.
- **Stop-loss:** pane meters `session_tokens` after every unit and stops at 4.0M, not after; a unit over 2x its P80;
  3 epochs without a commit; a C3 contract edited after its data was read.
- **Payback:** a single 10K reduction accepted by the Owner returns the tranche in under one day of estate traffic
  (processed). Billed payback is not derived.

## 6. Launch and Owner boundaries
- Capital: `approve ctx-rent-obs only` on the t3 packet. Nothing launches before that.
- Then the Owner opens a **new** pane in this repo (Sonnet) with:
  `Read vault/plans/context-rent-observatory-t3-2026-10-26.md and execute section 3. Meter session_tokens after each unit; stop at the 4.0M ceiling.`
- No settings, hooks, rules, CLAUDE.md or MEMORY.md edits in this tranche.
