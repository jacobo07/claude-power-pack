---
type: improvement
created: 2026-09-30
updated: 2026-10-02
sources: [2026-09-30-yt-9uojngzcjo, 2026-09-30-system-prompts-leaks, 2026-10-02-token-economy-internal-inventory]
status: IDEA
effort: M
graduated_to:
---

# Audit the always-loaded prefix

## Measurement — 2026-09-30 (bytes on disk, for a session in the PP repo)

| file group | bytes |
|---|---:|
| `~/.claude/CLAUDE.md` (global) | 40,117 |
| PP project `CLAUDE.md` @ `8574446` | 35,364 |
| `~/.claude/rules/**/*.md` (23 files) | 70,023 |
| project `MEMORY.md` (auto-memory index) | 15,677 |
| `C:\Users\User\CLAUDE.md` | 6,025 |
| **total** | **167,206** |

Not counted: SessionStart / UserPromptSubmit hook injections, the skill list, MCP instructions, and
the harness base prompt. Bytes are not tokens; the ratio was not measured.

For scale, the reported Claude Code base prompt for Opus 5.5 is 368,457 bytes including tool
definitions ([[2026-09-30-system-prompts-leaks]], manifest @ `b632b67`).

## Question

How much of the ~167 KB is (a) needed on every call, (b) better as an on-demand skill, or
(c) repeating something the harness prompt already says?

## Evidence for acting

- "Keep CLAUDE.md short … point to reference files" ([[2026-09-30-yt-9uojngzcjo]]).
- PP has already moved 9 rules into skills (2026-09-29/30); those stubs are 590-730 bytes each, down
  from 3-7 KB. The same move is open for the 14 rules still loaded in full.
- The global CLAUDE.md is 39,810 characters and 292 lines (measured 2026-09-30): 190 characters
  under the harness's 40.0k-character warning (Owner memory, `reference_claude_md_40k_char_warning.md`)
  and about 3× its own "CLAUDE.md < 100 lines" rule.

## Measured value of acting — 2026-10-02

- Floor delta when each part is switched off (neutral cwd, baseline 91.9k): CLAUDE.md + rules
  44.7k, skills listing 6.5k, hooks 4.8k, MCP 2.0k, plugins 1.4k; harness + tool schemas 34.5k
  not movable ([[2026-10-02-token-economy-internal-inventory]]).
- Upper bound over 7 d: -20k per call ≈ 6.3 % of estimated spend, -40k ≈ 12.6 %; the largest
  reachable lever found ([[token-economy-levers]]).
- Since 2026-09-30 nine rules moved to skills; six of those moves have no ablation, and moved rules
  auto-invoke 0/8 (same inventory). Quality risk is the open question.

## Proposed steps

1. Classify each always-loaded block as a, b or c. For c, diff against the reported base prompt.
2. Move every b to a skill with a stub, as was done for the 2026-09-29/30 rules.
3. Re-measure; record the drop here.

Concept: [[lean-always-loaded-context]].
