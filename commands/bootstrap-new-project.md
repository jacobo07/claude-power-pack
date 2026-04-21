---
name: bootstrap-new-project
description: "Guided walkthrough to spin up a new project with Power Pack governance pre-wired. Eliminates the onboarding cliff — empty dir → working PROJECT.md + CLAUDE.md + first passing Gate 1 in under 10 min. For existing codebases, use /customclaw instead."
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# /bootstrap-new-project — Universal Project Bootstrapper (MC-OVO-22)

Runs in the CURRENT working directory. Target state: empty or near-empty dir. If `git rev-parse --is-inside-work-tree` succeeds AND `git ls-files | head -1` returns content → **route to `/customclaw`** (stack-detection on existing code).

Closes capability-audit Gap #6 (+6%): the cliff between "empty repo" and "Power-Pack-wired working project" becomes a single walkthrough.

---

## Step 1 — Stack Detection via Owner Answer

Ask the Owner ONE question (exactly this phrasing so answer is unambiguous):

> What will this project be? Pick a number or describe.
>
>  [1] Python CLI / daemon / API (FastAPI, Click, asyncio)
>  [2] TypeScript web app (Next.js / React / Vue / Svelte / Astro)
>  [3] Java Spring Boot service (or Paper plugin — answer [6])
>  [4] Elixir / OTP service (Phoenix optional)
>  [5] C / C++ systems code (or embedded — answer [7])
>  [6] Minecraft Paper plugin (Java 21, Maven)
>  [7] Embedded firmware (MCU, Wii homebrew, ESP32)
>  [8] Other — describe in one sentence

**If the Owner picks a number, set `STACK = <answer>` and proceed. If they describe something else, map to the closest stack + note the mapping in PROJECT.md.**

---

## Step 2 — Scaffold Based on `STACK`

For each stack, create the following files using the Write tool. Never use `git add -A` here; add files explicitly by name.

### Common to every stack
- `.gitignore` — language-specific patterns (use the closest template from `~/.claude/skills/claude-power-pack/modules/executionos-lite/overlays/<stack>.md` or a minimal template)
- `README.md` — project name + one-paragraph purpose + one-line "how to run"
- `PROJECT.md` — required fields:
  ```
  # <Project Name>
  **Purpose:** <1 sentence, observable outcome>
  **Out of scope:** <what this project does NOT do>
  **Stakeholders:** Owner + any collaborators
  **Success criterion:** <measurable — "X endpoint returns Y under Z load">
  ```
- `CLAUDE.md` — points at Power Pack:
  ```
  # <Project Name> — Claude Code instructions

  @~/.claude/skills/claude-power-pack/parts/core.md
  @~/.claude/skills/claude-power-pack/modules/executionos-lite/overlays/<stack>.md

  ## Stack-specific rules
  <copy the top 3-5 rules from the overlay>
  ```

### Stack-specific manifest + hello-world + pre-flight test

| Stack | Manifest | Hello file | Pre-flight test (must FAIL) |
|---|---|---|---|
| 1 Python | `pyproject.toml` + `requirements.txt` | `src/<name>/__init__.py` + `src/<name>/__main__.py` (prints "hello") | `tests/test_feature.py` asserts unreleased feature |
| 2 TS/Web | `package.json` + `tsconfig.json` | `src/index.ts` (console.log) or `pages/index.tsx` | `__tests__/feature.test.ts` asserts unreleased feature |
| 3 Spring Boot | `pom.xml` (or `build.gradle.kts`) | `src/main/java/.../Application.java` | `src/test/java/.../FeatureTest.java` |
| 4 Elixir | `mix.exs` | `lib/<name>.ex` + `lib/<name>/application.ex` | `test/<name>_test.exs` |
| 5 C/C++ | `Makefile` or `CMakeLists.txt` | `src/main.c` (printf hello) | `tests/test_feature.c` linked to `make test` |
| 6 Minecraft | `pom.xml` + `src/main/resources/plugin.yml` | `src/main/java/.../<Plugin>.java` with onEnable log | `src/test/java/.../PluginTest.java` |
| 7 Embedded | `Makefile` (devkitPro / PlatformIO) | `src/main.c` with blink-LED or log loop | manual — document in `README.md` |

**Why the pre-flight test must FAIL initially:** per `modules/executionos-lite/sovereign-feature-template.md`, the pre-flight test's initial failure defines the goal. Its eventual PASS defines completion of the first feature. DO NOT write a tautologically-passing test.

---

## Step 3 — Install Base Dependencies

Run the stack's install command and capture stdout. Fail loud on error.

| Stack | Command |
|---|---|
| 1 Python | `python -m venv .venv && source .venv/bin/activate && pip install -e . -r requirements.txt` |
| 2 TS/Web | `npm install` or `pnpm install` (detect from lockfile if Owner pre-placed one) |
| 3 Spring Boot | `mvn dependency:resolve` |
| 4 Elixir | `mix deps.get` |
| 5 C/C++ | `make deps` if target exists, else skip |
| 6 Minecraft | `mvn clean package` (also validates plugin.yml) |
| 7 Embedded | stack-specific (`make` warmup or `pio lib install`) |

---

## Step 4 — First Gate (Static + Build)

Run Gate 1 (static) and Gate 2 (build). Capture stdout. Paste evidence into the commit message.

| Stack | Gate 1 (static) | Gate 2 (build) |
|---|---|---|
| 1 Python | `python -m compileall src/` AND `python -c "import ast; [ast.parse(open(f).read()) for f in glob.glob('src/**/*.py', recursive=True)]"` | `python -m build` if pyproject has build backend, else skip |
| 2 TS/Web | `npx tsc --noEmit` | `npm run build` |
| 3 Spring Boot | `mvn compile` | `mvn package -DskipTests` |
| 4 Elixir | `mix compile --warnings-as-errors` | (compile IS build in Elixir) |
| 5 C/C++ | `make -n all` (dry run) | `make all` |
| 6 Minecraft | `mvn compile` | `mvn clean package` |
| 7 Embedded | `make -n` | `make` |

**On failure:** iterate until pass. Don't commit until Gate 1+2 pass.

---

## Step 5 — First Commit

```bash
git init -b main
git add <each file by name>     # no `git add -A` — explicit list
git commit -m "chore(init): bootstrap <STACK> project via /bootstrap-new-project

Stack:           <STACK>
Gate 1 (static): PASS — <evidence line>
Gate 2 (build):  PASS — <evidence line>
Gate 3-5:        deferred to first feature commit

Pre-flight test intentionally failing per sovereign-feature-template.md.
First feature should transition pre-flight from FAIL → PASS.

[COUNCIL_VERDICT: A]"
```

---

## Step 6 — Power Pack Link Verification

```bash
grep -q "claude-power-pack/parts/core.md" CLAUDE.md && echo "OK: core.md linked"
grep -q "overlays/" CLAUDE.md && echo "OK: overlay linked"
```

Both must print OK. If either fails, re-edit CLAUDE.md.

---

## Step 7 — Remote (optional, Owner-initiated)

Do NOT auto-create a remote. Tell the Owner:

> Repo bootstrapped locally. To push to GitHub, create the remote repo at github.com, then run:
> `git remote add origin <url> && git push -u origin main`

---

## Step 8 — Final Report to Owner

Emit a 6-line summary:

```
Bootstrap complete.
  Stack:       <detected>
  Files:       <count> (CLAUDE.md, PROJECT.md, README.md, manifest, hello, pre-flight test)
  Gate 1+2:    PASS
  Pre-flight:  FAIL (expected — feature goal marker)
  Next:        `/gsd:new-project` or `/bmad:workflow-init` to define first milestone
  Power Pack:  wired via CLAUDE.md
```

---

## Exit Criteria (all MUST be true)

- [ ] Target dir has ≥5 files (CLAUDE.md, PROJECT.md, README.md, manifest, hello-world)
- [ ] Gate 1 and Gate 2 pass, evidence in commit message
- [ ] Pre-flight test exists AND fails (exit non-zero)
- [ ] `git log --oneline -1` shows the bootstrap commit with `[COUNCIL_VERDICT: A]`
- [ ] `CLAUDE.md` contains a `@~/.claude/skills/claude-power-pack/parts/core.md` reference
- [ ] No `TODO`, `FIXME`, `Coming Soon`, or placeholder strings in any generated file

---

## Non-goals (explicit)

- This command does NOT create the remote GitHub repo (requires Owner credentials).
- This command does NOT run Gates 3-5 (scaffold audit, tests, E2E) — those kick in on first feature commit, not bootstrap.
- This command does NOT install language runtimes (Python, Node, JDK, Elixir) — assumes they are on the `$PATH`.
- This command does NOT substitute for `/customclaw` on an existing codebase.
