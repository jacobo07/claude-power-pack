# Zero-Fiction Standard (BL-0035 / MC-SYS-70)

Pre-commit doctrine. Not a runtime hook — runtime enforcement is already covered by `scaffold-auditor.js` (Reality Contract), `secret-scanner.js`, `quality-gate.js`, and the dual-threshold context-watchdog (BL-0033).

This file codifies what "Grade-S" means when CLAUDE.md says "DONE = QA Pipeline PASS with observed evidence."

---

## The Eight Marks (Grade-S Checklist)

A commit is Grade-S only when ALL eight are observable in the diff or accompanying artifact:

1. **No placeholders.** Zero `TODO` / `FIXME` / `HACK` / `Coming Soon` / `pass # TODO` / `raise NotImplementedError` / empty catch blocks / stub returns. Reality Contract.
2. **Self-test or smoke-test passed.** New code has a `--self-test` or a piped-stdin smoke run with output captured in the commit message OR a `vault/benchmarks/*.md` file.
3. **Empirical numbers, not estimates.** When claiming perf, RAM, or token counts, the number is from a real measurement. If estimated, label it `(estimate)` and explain.
4. **No fictional savings claims.** "19.7x", "30x sovereignty", and similar figures require a citation. If the citation doesn't exist, the claim doesn't ship. Per BL-0022.
5. **All shared-state writes route through `lib/atomic_write.{py,js}`.** Per BL-0014/0018. Plain `fs.writeFileSync` on shared files is a regression.
6. **Hooks have no RAM state.** Per BL-0017. If a hook claims to "remember" between calls, the memory is on disk under `_audit_cache/` or `vault/` or `/tmp/claude-*-<session>.json`.
7. **No auto-dispatch of slash commands.** Per BL-0003. Hooks ADVISE; user TYPES. Any "auto /clear / /compact / /kclear" claim is fiction; the realistic mechanism is `hookSpecificOutput.additionalContext`.
8. **Rejected items are documented.** When a sub-task is rejected (out of scope, fictional, no-op), the rejection is recorded — either in a BL row, the commit message, or a `vault/research/<topic>_extraction.md` file. Silent drops cause future audits to re-litigate.

---

## Pre-Commit Self-Audit (60-second pass)

Before `git commit`, run through these checks against the staged diff:

```
$ git diff --cached | grep -E "TODO|FIXME|HACK|Coming Soon|placeholder"   # mark 1
$ # mark 2: did I run a self-test? what was the exit code? captured where?
$ # mark 3: any "X faster" / "Y MB" claims? where's the measurement?
$ # mark 4: any "Nx" reduction claims? where's the citation?
$ git diff --cached -- '*.{js,py}' | grep -E "fs\.writeFileSync|os\.open"  # mark 5: needs atomic_write?
$ # mark 6: any module-level state in a hook?
$ # mark 7: any "hook will run /<cmd>" prose?
$ # mark 8: any rejected items not documented?
```

Eight grep-eligible questions, eight under-10-second answers. ~60 seconds total.

---

## Anti-Fiction Vocabulary

When the user requests something that violates one of the marks, the response uses these named patterns instead of inventing new ones:

| User asks | Honest response |
|---|---|
| "Make it Nx faster" without baseline | "Per mark 4, what's the baseline measurement we're comparing against?" |
| "Auto /clear at threshold" | "Per BL-0003 (mark 7), hooks cannot dispatch slash commands. Realistic: advisory via additionalContext." |
| "Cut RAM by Y%" without measurement | "Per mark 3, that needs a measured-before number. The harness binary is closed (BL-0017)." |
| "Hook should remember X across calls" | "Per BL-0017 (mark 6), hooks fork-and-die. Persistence goes to disk under `vault/` or `/tmp/`." |
| "Eliminate this guard for autonomy" | "Per CLAUDE.md Reality Contract, guards are load-bearing. I won't bypass — surface for explicit user authorization instead." |

---

## Snowball Effect (per CLAUDE.md anti-monolith ledger)

Every commit that passes the eight marks RAISES the baseline. Future features must be born at this standard or higher. Regression to a lower mark requires its own BL row explaining why.

This is how `claude-power-pack` got from 44% health (2026-04-23 doctor baseline) to the current 18-BL-laws-passing state in one week — by committing to Grade-S checks per commit, not by sprinting on volume.

---

## Cited evidence

- `vault/baseline_ledger.jsonl` — BL-0003, BL-0014, BL-0017, BL-0018, BL-0022 cited inline
- `modules/zero-crash/hooks/*.js` — Reality Contract guards
- `~/.claude/CLAUDE.md` — Reality Contract paragraph + Completion Gates
- `modules/omniram-sentinel/README.md` — disk-first / lazy-loading / atomic-persistence siblings
