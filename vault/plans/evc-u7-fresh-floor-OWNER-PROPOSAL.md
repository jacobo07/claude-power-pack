# EVC U7 -- fresh-floor breakdown and cut (OWNER PROPOSAL; no global file edited)

Measured 2026-10-10 (chars; ~4 chars/token is an assumption, not measured):

| Contributor | Chars | Lines |
|---|---|---|
| `~/.claude/CLAUDE.md` (global) | 40,117 | 292 |
| PP repo `CLAUDE.md` | 40,832 | 365 |
| TUA-X/PP `MEMORY.md` (auto-memory index) | 20,845 | 145 |

Largest sections of the global CLAUDE.md (chars): Parallel Subagent Limit on Windows 13,610 (34%); Root + history 4,706;
PRE-BASH SELF-AUDIT RITUAL 3,103; HARD RULES ROUTER 2,074; PowerShell->ssh BOM hang 1,572; PP Activation Criteria 1,563;
Context Pressure Response 1,195.

## Proposed cut (Owner decides; worker did not apply any of it)
1. Move "Parallel Subagent Limit on Windows" (13.6k) to a vault lesson, leave a 600-char rule + link: about -13k chars (~-3.3k tokens/call).
2. Move "Root + history" (4.7k) to the vault: -4.5k.
3. Both CLAUDE.md files exceed the 40k-char warning; a cut of 1+2 brings the global to ~22k.
4. Per-call effect: every call re-reads the first-call context, so each 1k tokens cut saves ~1k x calls per session (cache-read priced, not full price).

NOT_PROVEN: the token saving (chars-to-tokens ratio and cache pricing not measured here). Rules inside the cut sections that hooks
do not already enforce could regress; test with a fresh session before adopting.
