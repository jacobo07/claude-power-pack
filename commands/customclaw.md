---
name: cpp-customclaw
description: "Scan current project and generate a custom AI daemon command tailored to its stack"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# CustomClaw — Project-Aware Daemon Generator

Generate a custom Claude Code command (`.claude/commands/[name].md`) tailored to the current project's stack, structure, and tooling. The generated daemon includes guardrails, stack-specific best practices, and detected project commands.

---

## Step 1: Parse Arguments

Extract the daemon name from the user's invocation. The expected format is `/cpp-customclaw create [name]`.

**Argument parsing rules:**
1. Strip the keyword `create` if present — it is a subcommand, NOT the daemon name.
2. The daemon name is the FIRST argument that is NOT `create`.
3. Examples: `/cpp-customclaw create my-bot` → name is `my-bot`. `/cpp-customclaw my-bot` → name is `my-bot`. `/cpp-customclaw create` → no name, ask.

- If no name was provided after parsing, use AskUserQuestion: **"What should I name your custom daemon? (lowercase, hyphens allowed, e.g. `my-helper`)"**
- Validate the name:
  - Must match: `^[a-z][a-z0-9-]{0,29}$`
  - If invalid, ask again with: "Names must be lowercase letters, numbers, and hyphens only (max 30 chars). Try again?"
- Store as `DAEMON_NAME`.

Check if `.claude/commands/{DAEMON_NAME}.md` already exists in the project:
```bash
test -f ".claude/commands/${DAEMON_NAME}.md" && echo "EXISTS" || echo "NONE"
```
If EXISTS, use AskUserQuestion: **"A daemon named `{DAEMON_NAME}` already exists. Overwrite it, or pick a different name?"**

---

## Step 2: Validate Project Root

```bash
pwd
```
Store as `PROJECT_ROOT`.

Verify this looks like a project directory (not home dir or system path):
```bash
found=0; for f in .git package.json requirements.txt pyproject.toml mix.exs Cargo.toml go.mod pom.xml build.gradle Gemfile composer.json pubspec.yaml CMakeLists.txt Makefile; do test -e "$f" && echo "FOUND: $f" && found=1; done; [ "$found" = "0" ] && echo "NO_PROJECT_MARKERS"
```
If output is `NO_PROJECT_MARKERS`, warn the user: "This doesn't look like a project root — no manifest or .git found. Continue anyway?" via AskUserQuestion. If they decline, stop.

---

## Step 3: Scan Project Stack

### 3a. Primary Language/Framework Detection

Check ALL manifest files below (not just the first match). **Never read files >100KB.** **Never read files matching `*.env*`, `*secret*`, `*credential*`, `*password*`.**

Store results as `PRIMARY_LANGUAGE` (first detected) and `ALL_STACKS[]` (all detected). The PRIMARY_LANGUAGE drives the stack-specific rules; ALL_STACKS are listed in the Project Context section.

**Detection order:**

1. **`package.json`** → Node.js
   - Read it (max 50 lines). Look for:
     - `"typescript"` in devDependencies → TypeScript
     - `"next"` → Next.js | `"react"` → React | `"vue"` → Vue | `"express"` → Express | `"nestjs"` → NestJS | `"svelte"` → SvelteKit
     - `"scripts"` block → extract `test`, `build`, `lint`, `dev` commands
   - Store: `LANGUAGE=node`, `FRAMEWORK=[detected]`, `PACKAGE_MANAGER` from lockfile (package-lock.json→npm, yarn.lock→yarn, pnpm-lock.yaml→pnpm, bun.lockb→bun)

2. **`pyproject.toml`** or **`requirements.txt`** or **`Pipfile`** or **`setup.py`** → Python
   - Read whichever exists (max 50 lines). Look for:
     - `django` → Django | `flask` → Flask | `fastapi` → FastAPI | `streamlit` → Streamlit
     - `pytest` → test framework
   - Store: `LANGUAGE=python`, `FRAMEWORK=[detected]`

3. **`mix.exs`** → Elixir
   - Read it (max 50 lines). Look for:
     - `:phoenix` → Phoenix | `:phoenix_live_view` → LiveView | `:ecto` → Ecto
   - Store: `LANGUAGE=elixir`, `FRAMEWORK=[detected]`

4. **`Cargo.toml`** → Rust
   - Read it (max 50 lines). Look for key deps: `tokio`, `actix`, `axum`, `serde`
   - Store: `LANGUAGE=rust`, `FRAMEWORK=[detected or "none"]`

5. **`go.mod`** → Go
   - Read it (max 50 lines). Look for: `gin`, `echo`, `fiber`, `chi`
   - Store: `LANGUAGE=go`, `FRAMEWORK=[detected or "none"]`

6. **`pom.xml`** or **`build.gradle`** or **`build.gradle.kts`** → Java/Kotlin
   - Read first 50 lines. Look for: `spring-boot`, `quarkus`, `micronaut`
   - Store: `LANGUAGE=java`, `FRAMEWORK=[detected]`

7. **`Gemfile`** → Ruby
   - Read it (max 50 lines). Look for: `rails`, `sinatra`
   - Store: `LANGUAGE=ruby`, `FRAMEWORK=[detected]`

8. **Glob for `*.csproj` or `*.sln`** → C#/.NET
   - Store: `LANGUAGE=csharp`, `FRAMEWORK=dotnet`

9. **`pubspec.yaml`** → Dart/Flutter
   - Store: `LANGUAGE=dart`, `FRAMEWORK=flutter`

10. **`composer.json`** → PHP
    - Read it (max 50 lines). Look for: `laravel`, `symfony`
    - Store: `LANGUAGE=php`, `FRAMEWORK=[detected]`

11. **`CMakeLists.txt`** or **Glob for `*.cpp`, `*.c`, `*.h` in src/ or root** → C/C++
    - If `CMakeLists.txt` exists, read first 30 lines for project name and C++ standard
    - Store: `LANGUAGE=cpp`, `FRAMEWORK=[cmake or "none"]`

**If no manifest found:** `LANGUAGE=generic`, `FRAMEWORK=none`

**Multi-stack note:** If multiple stacks are detected (e.g., package.json + pyproject.toml in a full-stack app), set PRIMARY_LANGUAGE to the first detected and include ALL detected stacks in the generated Project Context section.

### 3b. Structure Pattern Detection

Use Glob to detect project shape:

```
Glob: pnpm-workspace.yaml, lerna.json, packages/*, apps/*
```
- If any match → `STRUCTURE=monorepo`

```
Glob: **/controllers/*, **/models/*, **/views/*
```
- If all three → `STRUCTURE=mvc`

```
Glob: **/routes/*, **/api/*
```
- If matches but no `views/` or `pages/` → `STRUCTURE=api-only`

```
Glob: frontend/*, client/*, backend/*, server/*
```
- If both front+back → `STRUCTURE=fullstack`

Default: `STRUCTURE=standard`

### 3c. Detect Test/Build/Lint Commands

Based on detected stack, identify the likely commands:

| Stack | Test | Build | Lint |
|-------|------|-------|------|
| Node/TS | `npm test` or from scripts | `npm run build` or from scripts | `npm run lint` or from scripts |
| Python | `pytest` | `python -m build` | `ruff check .` or `flake8` |
| Elixir | `mix test` | `mix compile` | `mix credo` |
| Rust | `cargo test` | `cargo build` | `cargo clippy` |
| Go | `go test ./...` | `go build ./...` | `go vet ./...` |
| Java | `mvn test` or `gradle test` | `mvn package` or `gradle build` | `mvn checkstyle:check` |
| Ruby | `bundle exec rspec` | N/A | `bundle exec rubocop` |
| C# | `dotnet test` | `dotnet build` | `dotnet format --verify-no-changes` |
| C/C++ | `make test` or `ctest` | `cmake --build build` or `make` | `cppcheck` or `clang-tidy` |
| PHP | `vendor/bin/phpunit` | N/A | `vendor/bin/phpstan` |
| Generic | `make test` | `make build` | `make lint` |

Override with actual scripts from package.json/Makefile if detected.

### 3d. Check Existing Governance

```
Glob: CLAUDE.md, .claude/**, .cursorrules, CONTRIBUTING.md
```
If `CLAUDE.md` exists, read first 100 lines. Store as `EXISTING_GOVERNANCE` to avoid contradictions.

---

## Step 4: Generate the Daemon File

Assemble the output file `.claude/commands/{DAEMON_NAME}.md` using the scan results. **Build the content as a string — do NOT output a template with placeholders. Replace ALL values with the actual detected results from Step 3.**

The generated file MUST contain these sections in order. Write each section with the real detected values:

### 4.0 Frontmatter
Write valid YAML frontmatter with:
- `name:` set to the DAEMON_NAME
- `description:` set to `"Custom AI assistant for [project folder name] — [LANGUAGE]/[FRAMEWORK]"`
- `allowed-tools:` list containing: Bash, Read, Write, Edit, Glob, Grep

### 4.1 Header
Write a level-1 heading with the daemon name, followed by a note: "Auto-generated by CustomClaw for a [LANGUAGE]/[FRAMEWORK] project ([STRUCTURE] structure)."

### 4.2 Project Context
Write a "Project Context" section stating the detected language, framework, and structure. If a package manager was detected, include it. If key dependencies were found, list them. Only include what was actually detected — omit lines where no data was found.

### 4.3 Guardrails
Write a "Guardrails" section with these exact behavioral limits (note: these are behavioral guidelines that the AI assistant reading this file will follow — they are not mechanically enforced by the CLI):
- **Max iterations:** 15 for standard projects, 25 for monorepos
- **Retry limit:** 3 per operation
- **Forbidden files:** .env, .env.*, files with "secret", "credential", "password" in their name
- **Size limit:** Skip files >100KB
- **Stop conditions:** change implemented + test passes + build succeeds + no TODO/FIXME in changed code

### 4.4 Execution Protocol
Write the OBSERVE → PLAN → EXECUTE → VERIFY → HARDEN protocol with the actual detected test, build, and lint commands substituted into the VERIFY step.

### 4.5 Stack-Specific Rules
Write a section titled "[LANGUAGE]-Specific Rules" using the rules from Section 4a below, selecting the block that matches the detected LANGUAGE.

### 4.6 Project Commands
Write a table with the actual detected test, build, lint, and dev commands.

### 4.7 Hard Rules
Write these immutable rules:
- Never invent data not read from a verified source
- Never assume a file or function exists without checking first
- Never present approximations as implementations
- Never report "done" without running verification commands and showing output
- Placeholders (TODO, FIXME) are blockers — replace them before finishing
- Commented-out code is not delivered code — wire it in or remove it
- Every external call needs: try/catch, finite timeout, at least 1 retry

### 4.8 Existing Project Rules (conditional)
ONLY if a CLAUDE.md was found in Step 3d: add a section noting that existing governance rules take precedence over this file's rules.

### 4a. Stack-Specific Rules (inject based on LANGUAGE):

**Node/TypeScript:**
```
- Use strict TypeScript — avoid `any` unless truly unavoidable, prefer `unknown`
- Prefer named exports over default exports
- Use async/await over raw Promises; never use callbacks
- Before claiming done: `npx tsc --noEmit` must pass with 0 errors
- Prefer ESM imports (`import`) over CommonJS (`require`)
- Lock file must be committed — never `.gitignore` it
```

**Python:**
```
- Use type hints on all function signatures
- Prefer f-strings over .format() or concatenation
- Use pathlib.Path over os.path for file operations
- Virtual environment: never install globally. Check for venv/poetry/pipenv first
- Before claiming done: `pytest` must pass, `ruff check .` should show 0 errors
- Use context managers (with) for file and connection handling
```

**Elixir:**
```
- Pattern match over conditionals — use `case`/`with` not nested `if`
- Let it crash — don't rescue exceptions that supervisors should handle
- Use pipe operator `|>` for data transformations
- All public functions need @spec and @doc
- Before claiming done: `mix test` and `mix compile --warnings-as-errors` must pass
- Use Ecto changesets for all data validation, never raw SQL
```

**Rust:**
```
- Prefer `.expect("reason")` over `.unwrap()` for debugging clarity
- Use `Result<T, E>` for fallible operations, not panics
- Derive traits (Clone, Debug, Serialize) explicitly — no unnecessary derives
- Before claiming done: `cargo test` and `cargo clippy -- -D warnings` must pass
- Minimize `unsafe` blocks — document every one with a SAFETY comment
```

**Go:**
```
- Always handle errors — never use `_` for error returns
- Use `fmt.Errorf("context: %w", err)` for error wrapping
- Prefer table-driven tests
- Before claiming done: `go test ./...` and `go vet ./...` must pass
- Use `context.Context` for cancellation and timeouts on all I/O operations
```

**Java:**
```
- Use Optional<T> over null returns for methods that may not produce a value
- Prefer records for immutable data classes (Java 16+)
- Use try-with-resources for all closeable resources
- Before claiming done: `mvn test` or `gradle test` must pass
- Follow existing naming conventions in the project (check existing classes first)
```

**C/C++:**
```
- Use RAII for resource management — no manual new/delete without a wrapper
- Prefer smart pointers (unique_ptr, shared_ptr) over raw pointers
- Use const correctness — mark everything const that can be
- Before claiming done: `cmake --build build` and `ctest` (or `make test`) must pass
- Enable warnings: `-Wall -Wextra -Werror` for CI builds
- Prefer standard library containers over C arrays
```

**Generic (fallback):**
```
- Follow the existing code style in this project
- Read at least 3 existing files to learn conventions before writing new code
- Prefer editing existing files over creating new ones
- Before claiming done: run `make test` if Makefile exists, or any test script found
- When in doubt about a convention, check what the project already does
```

---

## Step 5: Confirm and Write

Before writing, summarize for the user via AskUserQuestion:

**"I've scanned your project and I'm ready to create your custom daemon:**
- **Name:** `{DAEMON_NAME}`
- **Detected stack:** {LANGUAGE}/{FRAMEWORK}
- **Structure:** {STRUCTURE}
- **Test command:** `{TEST_COMMAND}`
- **Build command:** `{BUILD_COMMAND}`
- **Output path:** `.claude/commands/{DAEMON_NAME}.md`

**Create it?"**

If approved:

1. Create the directory if needed:
```bash
mkdir -p .claude/commands
```

2. Use the Write tool to create `.claude/commands/{DAEMON_NAME}.md` with the assembled template from Step 4, replacing all `{PLACEHOLDERS}` with actual detected values.

---

## Step 6: Print the Empowering Explanation

After successfully writing the file, print this explanation to the console. Replace placeholders with actual values.

---

### What Just Happened

You now have a **personal assistant** that already knows your project inside and out.

**Think of it like hiring a kitchen helper who already toured your kitchen before their first day:**

- They know where your pots and pans are (your **{FRAMEWORK}** project structure)
- They know your family's favorite recipes (your **{TEST_COMMAND}** and **{BUILD_COMMAND}** commands)
- They have a kitchen timer set so they never leave the stove on forever (max **{MAX_ITERATIONS}** rounds of work, then they stop and tell you what's left)
- They know the spice cabinet with grandma's secret recipes is off-limits (your `.env` files and passwords are never touched)

### How to Use Your New Assistant

Open a terminal inside this project and type:

```
/[DAEMON_NAME]
```

Then tell it what you need, just like you'd ask a coworker:
- "Fix the login bug" — it reads the relevant code first, then fixes it, then runs your tests
- "Add a search feature" — it plans the changes, shows you the plan, waits for your OK, then builds it
- "Refactor the database layer" — it understands your stack and follows its specific rules

**Your assistant follows a simple rhythm, like a carpenter:**
1. **Measure** — reads the code to understand what's there (never guesses)
2. **Mark** — tells you what it plans to change (and waits for your nod on big changes)
3. **Cut** — makes the changes following your project's style
4. **Sand** — runs your tests and checks to make sure everything is smooth
5. **Seal** — double-checks for exposed secrets or rough edges

### The Safety Rails

Like a **fence around a construction site**, your assistant has boundaries:

- **It won't run forever** — after {MAX_ITERATIONS} rounds, it stops and reports what's done and what's left, like a worker clocking out and leaving notes for the next shift
- **It won't touch your secrets** — `.env` files and passwords are behind a locked door it doesn't have the key to
- **It won't guess** — if it's unsure, it reads the code or asks you, like a builder checking the blueprints instead of winging it
- **It won't skip inspection** — every time it says "done", it has already run `{TEST_COMMAND}` and shown you the results, like a mechanic test-driving before returning your car

### Want to Customize It?

Your assistant's "brain" is a simple text file at:
```
.claude/commands/{DAEMON_NAME}.md
```

You can edit it anytime, like tuning a recipe:
- **Stricter?** Lower `max_iterations` to 10 — your assistant does less per session but stays focused
- **More freedom?** Add more tools to the `allowed-tools` list — like giving your helper access to more kitchen gadgets
- **New rules?** Add them under "Hard Rules" — your assistant reads these every time it starts working

---

## Error Handling

At each step, if something fails:

- **Step 3 scan fails for a file:** Log "Could not read {file}, skipping" and continue to next manifest. After all checks, if LANGUAGE is still unset, use `generic`.
- **No manifest found at all:** Generate the daemon with generic/language-agnostic rules. Note in the output: "I couldn't detect a specific stack, so I created a general-purpose assistant. Edit `.claude/commands/{DAEMON_NAME}.md` to add stack-specific rules."
- **Write fails:** Report the exact error. Suggest the user create the directory manually: `mkdir -p .claude/commands` and retry.
- **User is in wrong directory:** If `PROJECT_ROOT` is a home directory (`~`, `/home/user`, `C:\Users\user`) with no project files, warn clearly and ask to `cd` into the project first.
