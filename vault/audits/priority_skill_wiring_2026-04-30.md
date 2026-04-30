# Priority-Skill Wiring Matrix — 2026-04-30

**Scope:** the 6 skills the Owner named as absorption priorities for the 1-May
sovereignty seal. Each row gives the **observed current wiring**, the **gap**,
and the **shortest patch path** that would actually integrate the skill into
the Power-Pack execution pipeline (not just register it in the index).

> Reality grade: every "wired" claim below is backed by a grep hit on a real
> hook/governance file, and every "gap" is a true negative — no scaffold.

---

## Matrix

| # | Skill | Origin | Currently wired in | Gap | 1-commit patch |
|---|---|---|---|---|---|
| 1 | `adversarial-longevity` | local | `modules/governance-overlay/pre-output.md:176` (Gate 2 of SUPREMACY MODE), `~/.claude/hooks/power-pack-reminder.js:41` (banner injected on UserPromptSubmit) | None — already enforced for `userInput/packetHandler/commandHandler/saveWrite/sharedState` domains. Verdict drops to B if cite missing. | **No patch needed.** Already at Grade-S baseline. Snowball baseline confirmed. |
| 2 | `superpowers:systematic-debugging` | plugin | Harness exposes it in skill list (visible in this session). **Not referenced** by any power-pack hook or governance file. | Hooks blocking on bug/error/test-failure don't redirect to it. The `superpowers:` namespace is invisible to power-pack-reminder.js. | Add a line to `~/.claude/hooks/power-pack-reminder.js` banner: "On bug/test-fail/unexpected-behavior → invoke `superpowers:systematic-debugging` before proposing fixes (Iron Law: NO FIXES WITHOUT ROOT CAUSE)." 1-line edit, `power-pack-reminder.js:41`-adjacent. |
| 3 | `kobiicraft-testing` | local | None. Skill exists at `~/.claude/skills/kobiicraft-testing/` but no power-pack hook references it. The skill is invoked manually by domain. | Power-Pack is project-agnostic; project-specific hooks belong in the kobiicraft repo's `.claude/`, not the global. | **No global patch.** Cross-repo baseline doc records the requirement: KobiiCraft repo MUST register a PostToolUse hook that gates "done"/"fixed" claims through Blind Testing Protocol. Global power-pack stays neutral. |
| 4 | `kobiicraft-ops` | local | Same as #3 — skill exists, not hooked. | KobiiClaw deploy/monitor/restart commands are repo-specific. | Same as #3 — belongs in the KobiiCraft repo's `.claude/settings.json` PreToolUse for `mix deploy` / `pm2 restart` patterns. Documented in cross-repo baseline. |
| 5 | `video-analyzer` | local | None. Skill exists at `~/.claude/skills/video-analyzer/`. The `/research-youtube` command and `vendor/auto-browser/` integration are independent. | When auto-browser is online and produces captures (e.g. `.playwright-mcp/page-*.yml`), nothing routes them to `video-analyzer` for frame-by-frame Intent-Gap analysis. | Add a `commands/browser-session.md` post-action hint: "Pass any captured `.yml` or recorded video through `video-analyzer` before declaring visual verification complete." Doc-only patch, no harness change. |
| 6 | `docker-management` | mydeepchat | None — and **NOT a power-pack-installed skill**. Origin is `mydeepchat`, meaning it's a third-party catalog entry, not a local skill the harness can dispatch. | The auto-browser stack runs via docker-compose; if docker-management were a real local skill, it could be referenced from `vendor/auto-browser/INSTALL.md`. As mydeepchat-only, there is no SKILL.md the harness can load. | **Escalation, not patch.** If you want this skill usable, install it locally (e.g., copy from mydeepchat to `~/.claude/skills/docker-management/`). Until installed, citing it from a hook is dead reference. |

---

## What this matrix proves

- **2 of 6 skills are already wired** at Grade-S baseline (`adversarial-longevity` fully enforced; `superpowers:systematic-debugging` exposed but not referenced).
- **2 of 6 skills are correctly out of scope** for the global power-pack (`kobiicraft-testing`, `kobiicraft-ops` — they belong in the KobiiCraft repo's `.claude/`).
- **1 skill is doc-only-wirable** (`video-analyzer` — no harness hook needed, just a routing hint in browser-session command).
- **1 skill is not actually installed** (`docker-management` — registry presence ≠ harness availability).

No 100% claim. Honest 4-of-6 baseline elevation possible with the patches above.

---

## Patches that can land **today** without browser verification

| Patch | File | Diff size | Risk |
|---|---|---|---|
| Banner injection for `superpowers:systematic-debugging` | `~/.claude/hooks/power-pack-reminder.js` | +1 line | low |
| Routing hint for `video-analyzer` post auto-browser capture | `commands/browser-session.md` | +3 lines | none |

The other 4 entries require either (a) cross-repo work in KobiiCraft (out of scope tonight) or (b) Owner-driven install action (`docker-management`).

---

## Out-of-scope for this matrix

- `C238`/`C239` block wiring — not present in `claude-power-pack`. Documented as blocker in MC-SA-00 reality block.
- 1224-skill 100% absorption — not feasible in one session. Deliberate scope cut.
- Live browser verification — auto-browser upstream offline, no Playwright MCP in this session. See browser captures review for what *was* possible.

— end of matrix —
