# S1 floor decomposition (2026-10-07)

Class: `minimal-prompt@claude-power-pack` -- headless `claude -p "Reply with the single word OK."`, `--max-turns 1`,
claude-opus-5-5, cwd `~/.claude/skills/claude-power-pack`, laptop win32. Numbers: `S1-floor-reference.json`.

## How it was measured
- Probe: the existing `wiki/tools/listing_floor_probe.py`, extended with `--pair` (no second probe). ON = normal
  surfaces. OFF = same session with `--settings S1-off-settings.json` (`{"disableAllHooks": true}`); nothing in
  settings.json or `~/.claude` was edited.
- Window chars: `floor_regression_gate.read_window` + `classify`, grouped by `listing_floor_probe.layer_class`.
- `attribute()` trusts OFF only if its window was read and holds 0 hook chars; otherwise UNDECIDED, never 0.
- Command: `python wiki/tools/listing_floor_probe.py --label s1-floor --prompt "Reply with the single word OK." --pair
  --off-settings vault/programs/cognitive-economy/gen2/evidence/tranche/S1-off-settings.json --out
  vault/programs/cognitive-economy/gen2/evidence/tranche/S1-probe-pairs.jsonl` -> exit 0.

## Result (first-call tokens = input + cache_creation + cache_read)
| reading | tokens | source |
|---|---|---|
| ON | 105,454 | session 80072f9f |
| OFF (hooks disabled) | 102,403 | session a7e9e17f |
| CPP hooks added (ON - OFF) | 3,051 | MEASURED, OFF hook chars = 0 |
| host-forced | UNDECIDED | see below |

**Host-forced is UNDECIDED.** No kill switch removes the instruction files or the CPP share of the skill/agent
listings without editing `~/.claude` config. The OFF reading (102,403) still holds 133,536 chars of CPP instruction
files, so it is an upper bound on the host-forced floor, not the floor itself.

## Controllable parts, ranked (ON window chars)
| # | item | chars | tokens |
|---|---|---|---|
| 1 | `~/.claude/CLAUDE.md` | 39,809 | unmeasured |
| 2 | `~/.claude/rules/**` (25 files; largest 6,257 / 6,100) | 36,831 | unmeasured |
| 3 | `claude-power-pack/CLAUDE.md` (HARD RULES block 21,230) | 34,478 | unmeasured |
| 4 | skill_listing (at the 30,000 budget) | 29,999 | unmeasured |
| 5 | agent_listing | 25,996 | unmeasured |
| 6 | auto-memory `MEMORY.md` | 16,462 | unmeasured |
| 7 | `C:/Users/User/CLAUDE.md` | 5,956 | unmeasured |
| 8 | hooks (SessionStart 5,526 + UserPromptSubmit 2,246) | 7,772 | **3,051** |

Not controllable by CPP: system prompt 7,003 chars; harness_other 17,073 (deferred tools 11,971 + MCP
instructions 4,006 + env rows). Tool schemas are not in the window at all, so they sit inside the token totals only.

Estimate, not a measurement: hooks run at 2.55 chars/token. At that ratio the 133,536 chars of CPP instruction files
would be roughly 52k tokens. A real number needs an OFF switch for instruction files.

## Biggest controllable item: `~/.claude/CLAUDE.md` (39,809 chars) -- REJECTED
The packet forbids editing `~/.claude` config, and HR-001 stops writes there. Cutting it is the Owner's call.
Before: 39,809 chars (session 80072f9f). After: unchanged, because no edit was made. The next item an in-repo worker
could act on is #3, the project CLAUDE.md HARD RULES mirror. It is generated from `vault/hard_rules/HARD_RULES.md`
and includes auto-generated stubs HR-001..HR-007, one of them a test entry (HR-002 "...ZZZ"), so the fix belongs in
the compiler source, not the mirror.

## File-level listing script (`s1_files.py`, read-only)
```python
import glob, json, os, sys
for sid in sys.argv[1:]:
    p = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))[0]
    for line in open(p, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "assistant": break
        a = d.get("attachment") or {}
        if a.get("type") == "instructions":
            for f in a.get("files") or []: print("instr", f.get("type"), len(f.get("content") or ""), f.get("path"))
        elif a.get("type") in ("hook_additional_context", "hook_system_message"):
            c = a.get("content"); print("hook", a.get("hookName"), sum(len(x) if isinstance(x, str) else len(json.dumps(x)) for x in (c if isinstance(c, list) else [c])))
```
