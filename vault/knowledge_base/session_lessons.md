# Session Lessons — Atomic Learning

Append-only log of concrete, non-derivable learnings per session.
One entry per `/kclear` with a `lesson` field. Keep each entry short and
self-contained — if a future reader can't grok it without the conversation,
rewrite it.

---

## 2026-04-22 — Shipped 5 MC-OVO cycles on claude-power-pack: sleepless_qa atomic landing (34 fi

**Session:** `kpp-supremacy-v7000-marathon`

Before promoting any inline-one-liner failure to an audit recommendation, run the canonical tool (--help / official CLI). Mistake #52: my ad-hoc script's bug got misattributed to the audited file.

---

## 2026-05-14 — Stop-hook PATH: bare `python` resolves to Store stub on Win11

**Session:** `kobiidistilleros-genesis-v82000`

Stop-chain hooks were emitting "command not found" because `hook-utils.js#getPythonCommand` returned bare `python` on win32. Windows 11's PATH includes a Microsoft Store stub `python.exe` that exits non-zero (it opens the Store), not the real interpreter under `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe`. Inline copies of the same pattern existed in `kobiiclaw-autoresearch.js`, `baseline-translator.js`, `dna-flywheel.js`, `session-init.js`.

Fix: `getPythonCommand()` now probes in priority — `$CLAUDE_PYTHON` → `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe` → `py -3` → bare `python`. Memoized after first resolution. Added matching `getNodeCommand()` returning `process.execPath` to neutralize the same risk for bare-`node` shell-outs. `kobiiclaw-autoresearch.js` (the Stop-chain offender) migrated to call the helper.

**Vaccine:** never write `const x = process.platform === 'win32' ? 'python' : 'python3'` inline; always import the helper. Reviewers reject bare-interpreter execSync templates outright.

---

## 2026-05-14 — RAM Shield (BL-0033 RAM channel)

**Session:** `kobiidistilleros-consolidation-v82001`

Two-stage RAM management for 30+h unattended sessions. `ram-watchdog.js` already advised at 1500 MB ("consider /kclear"). New `ram-shield.js` adds an *active* 2 GB trip: append a timestamped snapshot block to `<cwd>/vault/progress.md` (or `.claude/progress.md` fallback, or `~/.claude/state/progress.md` global), emit a `systemMessage` carrying the exact `/compact focus on …` line (task summary auto-derived from `git log -1 --pretty=%s`), and emit `hookSpecificOutput.additionalContext` with the literal `CONTEXT THRESHOLD CROSSED` phrase so BL-0033 fires Claude's next-turn `/compact` emission. Live empirical: 20 claude.exe procs at 7 GB tripped cleanly on smoke (synthetic session ID kept the real session's debounce flag clean).

**Schema-field uncertainty:** `ram-watchdog.js` header claims `additionalContext` is rejected on Stop; memory `BL-0040` claims it IS supported. `ram-shield.js` emits BOTH `systemMessage` (reliable) and `additionalContext` (BL-0033 channel) — if the harness drops the latter, the former still surfaces the human-readable instruction. **Vaccine:** when two governance artifacts disagree on a harness schema, ship both and let the harness pick.

**Process-name resolution:** `tasklist /FI "IMAGENAME eq claude.exe"` matches Claude Code on Windows (verified, not inferred — `ram-watchdog.js` already uses it). `process_name_candidates` config array `["claude.exe","claude","claude-code"]` covers Posix + future renames.

**CWD-relative snapshot path:** Stop hook stdin carries `cwd`; resolve project-local first (`vault/progress.md` then `.claude/progress.md`), global fallback last (`~/.claude/state/progress.md`). Never assume `process.cwd()` is the project root inside a hook.

---

