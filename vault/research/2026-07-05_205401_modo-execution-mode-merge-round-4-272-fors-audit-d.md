# Merge Round 4 Playbook — PR #272, FORS Audit & Design-Stack Hardening

**Mode:** EXECUTION
**Date:** 2026-07-05
**Scope:** Landing the #272 merge cleanly on `main`, auditing the FORS-adjacent surface for conflict/CI hygiene, and hardening the front-end design stack (Tailwind v4 + Next.js 16 + visual-regression gates).

> This report is a synthesis of research learnings mapped onto the three execution pillars named in the prompt. It is organized so each pillar can be executed independently or as a coordinated round. Speculative/forward-looking items are flagged inline.

---

## 1. Executive Summary

Merge Round 4 has three coupled problems, each with a distinct failure mode:

| Pillar | Core risk | Primary control |
|---|---|---|
| **#272 merge** | Squash merge orphans any branch stacked on #272; force-push marks reviews stale | `git rebase --update-refs` + `--force-with-lease`; scope by pathspec |
| **FORS audit** | Long-lived branches accrue 40–60 % conflict probability in a high-change repo; CI race breaks `main` post-merge | 4-hour auto-rebase bot (unapproved PRs only), ≤200-line PRs, hot-spot file splitting, merge queue |
| **Design stack** | Tailwind v4 silently drops mis-named tokens; Next.js 16 renames middleware→proxy; visual regressions ship undetected | CSS-first `@theme` + semantic-token layer, `app/proxy.ts`, Chromatic/Percy determinism gates |

The through-line across all three is **determinism**: deterministic ref-updates in the merge, deterministic conflict-catching in the audit, and deterministic snapshots in the design stack. Non-determinism is the shared root cause of every failure mode below.

---

## 2. Pillar 1 — Landing PR #272 (Merge Mechanics)

### 2.1 The squash-merge stacking trap

A **squash merge creates a brand-new commit hash** on `main`. Any branch stacked on top of #272 is now rooted on a commit hash that no longer exists in the merged history — the dependent branch is **orphaned**, and a naive rebase will replay #272's already-merged commits as conflicts against `main`.

**Fix — `--update-refs`:**

```bash
git rebase --update-refs --onto <branch-1> main
```

- Introduced in **Git 2.38 (October 2022)**, `--update-refs` automatically **force-updates every local branch pointer** that references a commit being rewritten during the rebase — eliminating manual per-branch rebasing of the whole stack.
- Enable by default: `git config --global --add --bool rebase.updateRefs true` (or `[rebase] updateRefs = true` in `.gitconfig`).
- Disable per-invocation with `--no-update-refs`.

**Documented edge cases (verify before relying):**

| Behavior | Detail |
|---|---|
| **Worktree exclusion** | Branches **checked out in a worktree are NOT updated** by `--update-refs` (official git-rebase docs). Directly relevant here — InfinityOps doctrine uses per-branch worktrees (`io-*`). A worktree-pinned stacked branch will silently *not* re-point. |
| **Stability window** | The git-rebase manpage records **no `--update-refs` behavior change across 2.38 → 2.44** (2.44.0 released 2024-02-23). The feature is stable through that range — safe to standardize on. |
| **Equivalent-commit detection** | Git identifies rewritten-but-equivalent commits (E′ vs E) via a **patch-id checksum** computed from the introduced patch, not the SHA-1; clean cherry-picks are marked via `git log --cherry-mark`. This is why an already-merged #272 commit is dropped rather than re-conflicted on rebase. |
| **Empty-commit policy** | `--empty=(drop\|keep\|stop)` governs commits that become empty post-rebase. **`drop` is the default**; `ask` is a deprecated synonym of `stop`. Expect #272's squashed content to go empty on the dependent branch and drop cleanly. |

### 2.2 Push safety

- **Always `git push --force-with-lease`, never `--force`.** `--force-with-lease` refuses the push if the remote moved since your last fetch, protecting a co-worker's concurrent commits on the shared branch. This aligns with the InfinityOps multi-pane doctrine (shared `.git/` index → pathspec-scoped commits + `--force-with-lease` only).
- **Force-push marks reviews outdated.** Any approved review on a dependent branch is invalidated by the rebase force-push — see §3.3 on why the auto-rebase bot must skip approved PRs.

### 2.3 Tooling that automates the cascade

If #272 sits under a deeper stack, hand the cascade to a tool rather than rebasing by hand:

- **Graphite**, **gh-stack**, **spr (0.13+)**, **Jujutsu (jj)**, **git-branchstack** — all automate the cascading rebase of a stacked-PR chain.
- These wrap the same `--update-refs` + `--force-with-lease` primitives; the value is orchestration and PR-retargeting, not new git mechanics.

### 2.4 #272 execution checklist

1. `git fetch origin && git status` — confirm `main` position (anti-overlap doctrine).
2. Determine whether anything is stacked on #272 (`gh pr list --base <272-branch>`).
3. If stacked and worktree-pinned → **do not trust `--update-refs`**; rebase each worktree branch explicitly.
4. Merge #272 (squash) → capture the new `main` SHA via `git cat-file` (never trust the PR label).
5. `git rebase --update-refs --onto <new-main-tip> <old-272-tip> <dependent>` for each dependent.
6. `git push --force-with-lease` per dependent.
7. Re-verify each dependent PR retargeted to `main`, CI green.

---

## 3. Pillar 2 — FORS Audit (Conflict & CI Hygiene)

The FORS audit surface is a long-lived, multi-contributor code area. The research gives a concrete, empirically-validated playbook for keeping such a surface mergeable.

### 3.1 The conflict-probability baseline

In a high-change repo (**100–200 commits/day, 25–30 contributors**), a branch left open **24 hours has a 40–60 % conflict probability**. This is the quantitative case for *not* letting a FORS-audit branch age — the audit should land in same-day increments, not accumulate.

### 3.2 The three interventions that worked (real-world data)

A production SaaS TypeScript monorepo (**28 contributors, 130 commits/day**) cut conflict resolution from **45 → 8 minutes/dev/day** via three changes — all directly applicable to a FORS audit:

| Intervention | Mechanism | Effect |
|---|---|---|
| **4-hour auto-rebase bot** | Rebases open branches onto latest `main` every 4 h | Caught **80 % of conflicts early**, while trivial to resolve |
| **200-line PR limit** | Hard cap on PR size | Google/Microsoft data: **>400-line PRs have 2–3× more defects and 4× review time** |
| **Hot-spot file split** | Split a shared API-types file | That single file caused **40 % of all conflicts** |

**Actionable FORS-audit corollary:** before starting, identify the FORS hot-spot file(s) — the ones that appear in the most recent conflict history — and consider splitting them *first*, so the audit's own edits don't collide with concurrent work.

### 3.3 Auto-rebase safety constraint

The auto-rebase bot **must only touch unapproved PRs**. Check `gh pr view --json reviewDecision` before rebasing — because a force-push (which rebase requires) **marks existing reviews as outdated**. Rebasing an already-approved PR silently discards its approval and re-opens the review cycle. This is the same review-invalidation mechanic as §2.2, applied to automation.

### 3.4 Keeping `main` green — merge queues

The classic race: PR-A and PR-B both pass CI independently, but merging A first breaks B's assumptions — B merges green and **breaks `main`**. A **merge queue** eliminates this:

- **GitHub native Merge Queue**, **GitLab Merge Trains**, **Aviator / Mergeable / Graphite** — each **speculatively rebases every queued PR onto latest `main` and re-runs ALL CI** before merging.
- **CI time multiplies queue wait:** 20-min CI × 5 queued PRs → the last PR waits **100 minutes**. **Keep CI under 10 minutes** or the queue becomes the bottleneck.

For InfinityOps' Elixir CI (which has documented `setup-beam`/OTP-version flakiness), the sub-10-minute target doubles as a flake-reduction forcing function: a fast suite reruns cheaply, so a queue-triggered environmental flake costs minutes, not the whole round.

### 3.5 FORS audit execution checklist

1. Pull the recent conflict log; identify the top hot-spot file(s). Split if one file dominates.
2. Cap each audit PR at ≤200 lines; decompose the audit into scoped slices.
3. Enable the 4-hour auto-rebase, gated on `reviewDecision != APPROVED`.
4. Route landings through a merge queue (native GitHub Merge Queue is the lowest-friction start).
5. Verify CI wall-time < 10 min; if not, that is the first thing to fix before queueing.

---

## 4. Pillar 3 — Design-Stack Hardening

Three sub-surfaces: the Tailwind v4 token model, the Next.js 16 routing rename, and the visual-regression gate.

### 4.1 Tailwind CSS v4 — CSS-first token architecture

Tailwind v4 **eliminates the JavaScript config file** (`tailwind.config.ts/js`). `theme.extend` is replaced by a **CSS-first `@theme` directive** parsed by a **Rust engine** that reads native CSS variables.

**Strict namespace rules — mis-named variables are silently ignored:**

| Legacy config key | v4 CSS variable namespace | Example utility generated |
|---|---|---|
| `theme.colors` | `--color-*` | `bg-brand-500` |
| `theme.spacing` | `--spacing-*` | `p-xl` |
| `theme.borderRadius` | `--radius-*` | `rounded-*` |
| `theme.fontFamily` | `--font-*` | `font-*` |
| `theme.fontSize` | `--text-*` | `text-*` |
| `theme.boxShadow` | `--shadow-*` | `shadow-*` |

> **Silent-failure warning:** an incorrectly-named variable produces **no error** — the compiler just skips it and the utility never generates. This is the single highest-risk foot-gun in the v4 migration and belongs in the FORS-audit checklist for any design-token PR.

**Migration path:**
- `npx @tailwindcss/upgrade@next` — official upgrader, but **outputs verbose nested CSS that needs manual cleanup**.
- `@config` directive can bridge to a legacy JS config **but degrades build performance** — treat as a temporary crutch, not a destination.

**Two-layer token architecture (best practice):**

1. **Static `@theme` tokens** — the raw palette / design language; auto-generate utilities (`p-xl`, `bg-brand-500`).
2. **Dynamic semantic tokens** — `--color-surface`, `--color-text-primary`, `--surface-primary`, defined in `:root` / `.dark` **outside** `@theme`.

Dark mode then **swaps variable values in `.dark`** — **zero `dark:` prefixes, zero component-code changes**.

**Color model — OKLCH over hex/HSL:**
- OKLCH (L 0–1, C 0–0.4, H 0–360) is **perceptually uniform** — equal lightness *looks* equally bright across hues, so status colors carry **equal visual weight**.
- Tailwind v4 handles opacity modifiers (`bg-brand-500/50`) automatically via CSS **`color-mix()`** — no RGB comma-separated channel values required.

*(InfinityOps note: this dovetails with the existing §33 palette-guard and §99 muted-over-danger offline-state rules — semantic tokens are the clean home for `--muted`.)*

### 4.2 Tailwind v4 breaking changes to audit

| Change | Impact | Fix |
|---|---|---|
| `@apply` **restricted to the importing file** | Breaks component libraries built on `@apply` | Move variants into JS via **Tailwind Variants (`tv`)** or **class-variance-authority (CVA)** |
| **Config `safelist` removed** | Dynamic CMS class names get purged | `@source "safelist.txt"` |
| **v3-era Node.js theme-evaluation plugins fail** | Plugins requiring runtime Node theme access break under the Rust engine | Replace with v4-native equivalents |

**Token pipeline (cross-platform):** Tokens Studio (Figma → JSON export) + **Amazon Style Dictionary** (`npx style-dictionary build`) outputs CSS vars / JS modules across web/iOS/Android from one source of truth.

### 4.3 Next.js 16 — the middleware→proxy rename

- The middleware system is renamed to a **proxy file: `app/proxy.ts`**, exporting a **`proxy` function** with a **negative-matcher config** for i18n/locale routing.
- Directly relevant to the InfinityOps `/en/` mirror and Spanish-locale routing — any middleware-based locale logic must migrate to `app/proxy.ts`.
- Cross-check against the existing production doctrine that a `proxy.ts` host-rewrite can shadow `/api/*` (documented prod-404 root cause) — the rename does not change that hazard, it renames the file that carries it.

### 4.4 Visual-regression gate — Chromatic vs Percy

| Dimension | **Chromatic** | **Percy** |
|---|---|---|
| Builder | Storybook team | BrowserStack |
| Browsers | **Chromium-only** | **Cross-browser** (Chrome/Firefox/Safari) |
| Integration | Native first-party Storybook; doubles as Storybook host | Plugin-based (`@percy/cli` + `@percy/storybook`) |
| Free tier | **5,000 snapshots/month** | **5,000 snapshots/month** |
| CI integrations | GitHub/GitLab/Bitbucket/CircleCI | Same |
| Snapshot economy | **TurboSnap** (only stories affected by the code change) | `defer-uploads` responsive merging |

**Snapshot-budget math:** a 60-component / 180-story library × 3 viewports = **540 snapshots/build** → ~**9 builds/month** on the free tier. TurboSnap is the mitigation that makes this viable in a monorepo.

**Chromatic GitHub Actions config:**
```yaml
- uses: chromaui/action@latest
  with:
    projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
    exitZeroOnChanges: true   # non-blocking; posts PR status check
    autoAcceptChanges: main
    onlyChanged: true         # TurboSnap
# fetch-depth: 0 REQUIRED — TurboSnap needs full git history for its diff graph
```

**Percy config:** `npx percy storybook ./storybook-static`, configured via `.percy.yml`:
```yaml
version: 2
snapshot:
  widths: [375, 1024, 1280]
  min-height: ...
  percyCSS: |          # hide dynamic elements
    .timestamp { visibility: hidden; }
# 0.1% pixel-diff tolerance to suppress false positives
```

### 4.5 Determinism — the discipline that makes the gate trustworthy

**False positives stem from:** timestamps, random data, animations, web fonts, and OS/browser anti-aliasing. Mitigations:

- **Deterministic story args** (no `Math.random`, no `Date.now`).
- **MSW** (`msw-storybook-addon`) to mock API responses.
- **Global CSS injection in `preview.js`** to disable transitions/animations.
- **Storybook `play` functions** to stabilize interactive states.
- **`percyCSS` / `waitForSelector`** to hide dynamic nodes and wait for settle.

**2026 agent-driven triage:** both Chromatic and Percy now ship **production-ready MCP servers**. Chromatic's is a Storybook addon — **`@storybook/addon-mcp` since Storybook 10.3**, exposing an endpoint at **`localhost:6006/mcp`** — enabling agent-driven visual-diff triage.

**Cautionary precedent:** the **Nectar Design system paused its `chromatic.yml` workflow on 2026-05-08 (ADR 0017)** due to free-tier quota exhaustion, substituting **Lost Pixel + Percy**. The lesson: the 5,000-snapshot free tier is a real ceiling — architect the snapshot budget (TurboSnap + viewport discipline) *before* wiring the gate into required CI, or plan the Lost-Pixel fallback.

---

## 5. Cross-Pillar Synthesis — One Discipline, Three Faces

| | Non-determinism source | Deterministic control |
|---|---|---|
| **#272 merge** | SHA churn from squash orphans stacks | `--update-refs` (patch-id equivalence), `--force-with-lease` |
| **FORS audit** | Time-decay conflict probability, CI race | 4-h auto-rebase, ≤200-line PRs, merge queue re-running all CI |
| **Design stack** | Timestamps/fonts/anti-aliasing/animations | MSW, animation-disable, pixel tolerance, TurboSnap |

Every failure mode in this round is a determinism gap. Close the gap and the round is mechanical.

---

## 6. Recommended Execution Order

1. **Land #272 first** (§2.4) — smallest blast radius; unblocks anything stacked. Verify the new `main` SHA via `git cat-file`, not the PR label.
2. **Stand up the merge queue + CI-time check** (§3.4) *before* the FORS-audit PRs, so every audit slice lands green-by-construction.
3. **Slice the FORS audit** into ≤200-line PRs; split the hot-spot file(s) first (§3.2).
4. **Design-stack migration as its own slice set** — Tailwind token-namespace audit (§4.1–4.2) and the Next.js `proxy.ts` rename (§4.3) are independent and can run in parallel with FORS once the queue exists.
5. **Wire the visual-regression gate last** (§4.4–4.5), non-blocking (`exitZeroOnChanges: true`) at first, with a pre-computed snapshot budget to avoid the Nectar-style quota wall.

---

## 7. Open Risks & Flags

- **[Verify per-host]** `--update-refs` worktree exclusion is the highest-probability silent failure in this round given InfinityOps' per-branch worktree pattern. Do not assume the stack re-pointed — check each worktree branch tip explicitly.
- **[Speculative]** The design-stack agent-triage MCP servers (`@storybook/addon-mcp`, Percy MCP) are new (2026); production reliability at scale is not yet broadly documented. Treat agent-driven visual triage as advisory, human-confirmed, until proven.
- **[Budget]** The 5,000-snapshot/month free tier is a hard ceiling. At 540 snapshots/build you get ~9 builds/month — insufficient for a busy merge queue. Decide TurboSnap-only vs. paid tier vs. Lost-Pixel fallback *before* making the gate a required check.
- **[Silent]** Tailwind v4 mis-named tokens produce no error. Add an explicit `grep`-based token-namespace lint to the FORS-audit gate so a dropped utility can't ship unnoticed.

---

*End of report. All eleven research learnings are incorporated across §2 (six merge/rebase/queue learnings), §4.1–4.2 (three Tailwind/Next.js learnings), and §4.4–4.5 (three Chromatic/Percy/determinism learnings).*

## Sources

- <https://codewithyoha.com/blogs/mastering-git-advanced-workflows-with-merge-queues-stacked-prs>
- <https://stacked-pr.github.io/>
- <https://www.davepacheco.net/blog/2025/stacked-prs-on-github/>
- <https://github.github.com/gh-stack/guides/workflows/>
- <https://how2.sh/posts/how-to-optimize-conflict-resolution-workflows-for-high-change-projects/>
- <https://git-scm.com/docs/git-rebase>
- <https://git-scm.com/book/en/v2/Git-Branching-Rebasing>
- <https://medium.com/@bruce.ho98/a-better-way-to-rebase-stacked-prs-aa9b4dc600f1>
- <https://andrewlock.net/working-with-stacked-branches-in-git-is-easier-with-update-refs/>
- <https://stackoverflow.com/questions/79704467/git-rebase-on-branch-that-has-been-rebased-using-update-refs-inside-of-worktre>
- <https://www.oneminutebranding.com/blog/tailwind-v4-design-tokens>
- <https://nicolalazzari.ai/articles/integrating-design-tokens-with-tailwind-css>
- <https://medium.com/@yh_tan/building-with-next-js-16-tailwind-v4-sanity-f493df98b8dc>
- <https://marceloretana.com/learn/build-a-design-system-with-tailwindcss>
- <https://www.iamuvin.com/blog/design-building-design-system-tailwind-nextjs>
- <https://teachmeidea.com/visual-regression-testing-percy-chromatic/>
- <https://codex.danielvaughan.com/2026/05/05/codex-cli-visual-regression-testing-percy-chromatic-playwright-mcp/>
- <https://beefed.ai/en/visual-regression-storybook-percy-chromatic>
- <https://medium.com/@sohail_saifi/visual-regression-testing-percy-vs-chromatic-vs-backstopjs-0291477a23ef>
- <https://github.com/tknatwork/nectar-design>

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — Merge Round 4: #272 + FORS audit + design stack
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 567.7 s
- **Errors during run:** 1
- **Started at:** 2026-07-05T18:54:01Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-07-05. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`

</details>
