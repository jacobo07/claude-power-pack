---
title: Stop-hook fires inside subprocess sessions — env-var recursion guard required
date: 2026-05-23
incident: V2 empirical run of the deep-research agent — recursive spawn explosion
scope: any PP-shipped Stop hook that triggers a subprocess invocation of
       claude.exe (or any harness with its own Stop chain)
status: SEALED
---

## Trigger

The deep-research agent's V2 empirical test (synthetic 92-word Spanish
prompt with "investiga / compara / Estado del arte") fired the Stop
hook correctly:

1. `research-intent-detector.js` detected the intent, spawned
   `python deep_research.py` detached.
2. The python child called `claude.exe -p` with the
   `generate_serp_queries` user message.
3. **`claude.exe -p` runs the FULL Stop-hook chain in its own
   subprocess session.** The generate_serp_queries text contains the
   literal word "research" (it says "research the topic") AND
   exceeds 80 words.
4. The Stop hook in the subprocess matched the intent regex AND the
   breadth gate → spawned ANOTHER detached deep-research run.
5. The second run hit the single-instance lock (held by run #1) and
   wrote a 1 KB "deep_research locked" template report at
   `vault/research/<ts>_given-the-following-prompt-from-the-user-generate-.md`.
6. Each subsequent LLM call in the original run repeated step 3-5.

Result on disk: two ~1 KB locked-template reports with prompt-slugs
derived from the generate_serp_queries USER MESSAGE — not the actual
user's research prompt. The Reality Contract surfaced the bug
(reports were honestly labelled "locked", URLs were empty) but the
intent was wrong.

## The rule

Any Stop hook that spawns a subprocess calling `claude.exe` (or any
binary that has its own Stop-hook chain) MUST guard against
self-recursion via an env-var sentinel:

### 1. The subprocess spawner sets the sentinel

```python
sub_env = os.environ.copy()
sub_env["CLAUDEPP_<FEATURE>_RUNNING"] = "1"
subprocess.run(..., env=sub_env)
```

For deep-research: `CLAUDEPP_DEEPRESEARCH_RUNNING=1`. The sentinel
name MUST be feature-specific so multiple guards (deep-research,
session-snapshot, future features) compose cleanly.

### 2. The Stop hook checks the sentinel FIRST

```javascript
if (process.env.CLAUDEPP_<FEATURE>_RUNNING === '1') {
    // We're inside a subprocess belonging to this feature's run.
    // Skip silently — never log, never spawn, never inspect the
    // session jsonl (which would be the subprocess's own jsonl,
    // not the user's).
    process.exit(0);
}
```

The check MUST be the FIRST statement of `main()`, before any
other work (jsonl read, regex match, etc.). Anything else risks
either firing or doing unnecessary IO inside a guarded subprocess.

### 3. The driver also sets it (belt-and-suspenders)

```python
def main(argv):
    # ... arg parsing ...
    os.environ["CLAUDEPP_<FEATURE>_RUNNING"] = "1"  # propagates to
                                                     # all children
    # ... actual work ...
```

This way ANY indirect spawn (a sub-tool, a future hook, a child
process the driver creates downstream) also inherits the flag.
Setting it only in the immediate subprocess.run env leaves a gap
for grand-children.

## Why `--bare` alone doesn't fix it

claude.exe has a `--bare` flag that skips hooks. But `--bare` ALSO
disables OAuth keychain reads, forcing `ANTHROPIC_API_KEY` env auth.
For PP installs that rely on the Owner's existing keychain login
(the common case — most users haven't configured an API key),
`--bare` breaks auth before it prevents recursion. The env-var
sentinel is portable across both auth paths.

## Detection in advance (future)

When a new PP feature adds a Stop hook that ALSO spawns a
claude.exe subprocess, the spec MUST include:

1. The sentinel env-var name (feature-specific).
2. The first-statement check in the hook.
3. The subprocess-env setter in the driver.
4. An empirical test that fires the hook with the sentinel set
   and confirms silent exit.

Empirical test recipe:
```
CLAUDEPP_<FEATURE>_RUNNING=1 sh -c \
  'echo "{...}" | node hooks/<hook>.js; echo guarded_exit=$?'
# expect: exit 0, no log entry written, no subprocess spawned.
```

## Cross-references

- Empirical incident: `claude-power-pack/vault/plans/deep-research-agent-2026-05-23.md`
  status row for Paso V2 (records the spurious 1 KB locked reports
  before the fix).
- Fix in production:
  - `claude-power-pack/hooks/research-intent-detector.js:main()` — first
    statement is the sentinel check.
  - `claude-power-pack/modules/deep-research/deep_research.py:_llm_claude_cli`
    — sets the env var when spawning claude.exe.
  - `claude-power-pack/modules/deep-research/deep_research.py:main()` —
    sets `os.environ` flag for full child propagation.
- Sister Windows-subprocess lesson:
  `vault/lessons/windows-argv-limit-stdin-fix.md` — both caught in the
  same V2 empirical run.

## Vaccine

Any future PP feature that ships a Stop hook + a subprocess invocation
of claude.exe (or any binary with hook-firing semantics) MUST include
all three components above. Missing any one is REJECTED.
