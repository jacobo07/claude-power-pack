# Cross-Repo Grade-S Baseline — 2026-04-30

**Purpose:** define what "Grade-S" means for any skill shipped from any repo
that the Power-Pack indexes. The Power-Pack is the **agnostic engine** —
domain skills (KobiiCraft, MundiCraft, Helsinki ops, etc.) live in their
own repos, and adopt this baseline by reference, not by file move.

> **No file moves.** This doc is the contract. Each downstream repo wires
> the contract into its own `.claude/` and is audited against it.

---

## The 5 Grade-S axes

| # | Axis | Concrete requirement | Verifiable how |
|---|---|---|---|
| 1 | **Indexable** | `<skill>/SKILL.md` (or `instructions.md`) exists with YAML frontmatter `name:` + `description:` | scanner finds the skill, frontmatter parses |
| 2 | **Hooked or declared not-hookable** | Either (a) referenced from a real PreToolUse / PostToolUse / UserPromptSubmit hook in the harness, or (b) declared "manual-invoke only" in `description` | grep on hook files; banner in description |
| 3 | **Reality-Contract clean** | Zero `TODO/FIXME/HACK/PLACEHOLDER/Coming Soon/pass # TODO/raise NotImplementedError`, no commented-out wiring, no empty catch blocks | `scaffold-auditor.js` Stop hook passes |
| 4 | **Cite-or-die when in scope** | Skills touching gameplay/animation/camera/audio/particles/input → `game-feel-codex` (Gate 1). Touching userInput/packetHandler/commandHandler/saveWrite/sharedState → `adversarial-longevity` (Gate 2). Touching assets/UI/shaders/render → `voice-spec-lock` (Gate 3) | OVO Council verdict ≥ A; missing cite ⇒ REJECT |
| 5 | **Verification-before-completion** | Skill must declare an empirical evidence check before claiming "done". For domain skills: blind-test runner (Mineflayer for MC, Playwright for web, etc.). For meta-skills: CLI exit-code + observable artifact. | Test artifact + log line in completion gate |

A skill at Grade-S satisfies all 5 axes. A < 5/5 score routes to Rejection Recovery.

---

## How downstream repos adopt this

### Required actions per repo

1. **Register hooks in the repo's `.claude/settings.json`** that gate the harness on cite-or-die, scaffold-auditor, and skill-specific verification (e.g., KobiiCraft → Mineflayer blind test before declaring "fixed").
2. **Mirror `~/.claude/hooks/power-pack-reminder.js` semantics** in the repo's local hook so banner injection happens consistently across windows.
3. **Reference this doc** by absolute path (`~/.claude/skills/claude-power-pack/vault/audits/cross_repo_grade_s_baseline_2026-04-30.md`) from the repo's CLAUDE.md so future sessions load the contract.

### KobiiCraft / MundiCraft adoption (specific)

- `kobiicraft-testing` skill must be enforced via a **PostToolUse Bash hook** that, on any `mvn package` or `pterodactyl-deploy`, dispatches the Mineflayer blind-test runner and blocks the "done" claim until the bot reports green. Today: skill exists, hook does not. **Patch path:** add hook entry to KobiiCraft repo's `.claude/settings.json`.
- `kobiicraft-ops` skill must be enforced via a **PreToolUse Bash hook** that intercepts `pm2 restart` / `mix deploy` patterns and forces the routed sub-task to read `kobiicraft-ops/SKILL.md` first.
- C238 / C239 issue blocks: not addressed by this contract until the issue text is provided. The contract enables them; it does not implement them.

---

## Snowball baseline

Grade-S today is the floor for tomorrow. When a skill clears all 5 axes
**and** shows up cleanly in 3 consecutive OVO `A` verdicts, it gets
elevated to Grade-S+ via `tools/baseline_ledger.py --elevate`. The ledger
becomes the next baseline. **No regression past Grade-S** — that is the
non-negotiable invariant.

---

## What this contract does NOT do

- Doesn't move any KobiiCraft / MundiCraft files into the Power-Pack repo. Domain code stays in its repo.
- Doesn't run KobiiCraft tests from this repo. Tests live in the KobiiCraft repo and are gated there.
- Doesn't commit anything to the KobiiCraft remote. Adoption is a separate session in that repo.
- Doesn't validate the contract against Helsinki / Bernabéu live state. That requires the auto-browser stack online and a URL the Owner provides.

---

## Verification command for this contract

```bash
# Run any time the contract changes — emits the active Grade-S floor.
python ~/.claude/skills/claude-power-pack/tools/baseline_ledger.py --show k_qa
```

— end of contract —
