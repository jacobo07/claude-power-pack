# `vault/research/` — Deep Research Agent output

Output directory for `modules/deep-research/deep_research.py` (the
sleepy recursive research agent).

## What lives here

| Pattern | Purpose | Commit? |
|---|---|---|
| `<YYYY-MM-DD_HHmmss>_<slug>.md` | Report — body + ## Sources + ## Run metadata | YES |
| `index.json` | JSONL append (one row per run) | YES |
| `<slug>.raw.jsonl` | Per-run forensic trace (queries + learnings) | NO (gitignored) |
| `.deep-research.lock` | Single-instance run lock (live during a run) | NO |
| `.auto-spawned.log` | Sleepy-auto-spawn log (Stop-hook decisions) | NO |
| `*.tmp.*` | Atomic-write intermediates (visible only mid-write) | NO |

The `.gitignore` in this directory enforces the policy.

## How to run

Manual:
```
python ~/.claude/skills/claude-power-pack/modules/deep-research/deep_research.py \
  --prompt "your research question" --depth 1 --breadth 2
```

Or use the skill:
```
/cpp-deep-research your research question
```

Or just type a >=80-word prompt that contains a research verb
(investiga / research / compara / analiza / deep dive / qué opciones /
mercado de / estado del arte) and the Stop hook fires the agent
automatically (in any session where the hook is registered).

## Cross-references

- Spec: `vault/specs/deep-research-agent.md`
- Plan: `vault/plans/deep-research-agent-2026-05-23.md`
- Skill: `commands/cpp-deep-research.md`
- Stop hook: `hooks/research-intent-detector.js`
- Forbidden runtime: `memory/feedback_no_n8n_ever.md` (the agent is the
  Python replacement for an n8n workflow — n8n is permanently banned)
