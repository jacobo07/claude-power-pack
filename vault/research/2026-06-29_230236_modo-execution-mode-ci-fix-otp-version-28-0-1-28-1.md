# Execution Runbook & Research Report — CI Fix: `otp-version` `28.0.1` → `28.1` in `ci.yml`

**Mode:** EXECUTION — scoped CI fix on a clean branch off `main`
**Repo:** InfinityOps (`io-sos` worktree; canonical `github.com/jacobo07/InfinityOps`)
**Date:** 2026-06-29
**Author context:** This runbook synthesizes the upstream OTP/setup-beam research with InfinityOps repo doctrine. It is **verify-first**: Step 0 gates every subsequent step, because both the research and prior memory contain a stale-premise trap that could make this a no-op.

---

## 1. Executive Summary & Verdict

| Item | Finding |
|---|---|
| **Requested change** | Bump `otp-version` from `28.0.1` to `28.1` in `ci.yml`, on a fresh branch off `main`. |
| **Is the change technically sound?** | **Yes.** OTP 28.1 is a real, released maintenance patch (tag `OTP-28.1`, 2025-09-17) within the ubuntu-24.04 supported band (24.3–29). It is a safe, low-risk bump. |
| **Does the empirical root cause hold up?** | **Yes — but the *mechanism* in prior notes is inverted and must be re-stated.** The failure on 28.0.1 is **a missing function** (`re:import/1` does **not** exist in 28.0.x), not a removed/deprecated one. OTP 28.1 *adds* it. See §4. |
| **Critical gating risk** | Memory marks this as **"RESUELTO #260"**. If #260 is already merged to `main`, `ci.yml` on `main` may **already** read `28.1` and this task is a **no-op**. **Do not edit before reading `origin/main:ci.yml`.** |
| **Recommended target value** | `'28.1'` (quoted string) to honor the task. **Consider `'28.1.1'`** (released 2025-10-20) as optional hardening — it adds the dirty-scheduler and SSL fixes. See §6. |
| **Verdict** | **PROCEED with Step 0 verification.** Apply the one-line bump only if `main` still shows `28.0.1`. Branch scoped off `origin/main`, single-file commit, CI-green gate. |

---

## 2. The Change Itself (exact diff)

The intended edit is a single token in the `with:` block of the `erlef/setup-beam` step. Expected before/after:

```yaml
# BEFORE
      - uses: erlef/setup-beam@v1
        with:
          otp-version: '28.0.1'
          elixir-version: '1.18.3'

# AFTER
      - uses: erlef/setup-beam@v1
        with:
          otp-version: '28.1'
          elixir-version: '1.18.3'
```

**Non-negotiable formatting rules (from setup-beam doctrine):**

- The value **must be a quoted YAML string** — `'28.1'`, never bare `28.1`. Unquoted, YAML parses `23.0`→`23`; the same class of bug applies to any trailing-zero/float-looking version. Quoting is mandatory even where it currently "happens to work."
- **Bump every occurrence.** InfinityOps runs **two apps** (`infinity_mie` + `infinity_os`) that go "both apps red" together. The OTP pin may appear in a matrix list, twice (one per job), or in a reusable workflow. Grep all of `.github/workflows/*.yml` for `otp-version` and `28.0.1` before editing — a partial bump leaves one app red and re-triggers the exact symptom.

---

## 3. The Verify-First Gate (Step 0 — DO THIS BEFORE ANY EDIT)

This task carries **two** stale-premise traps that InfinityOps memory explicitly warns about (*"directivas describen bugs ya fixed; git log + read first"* and *"premisa 'usa latest' STALE → `git diff origin/main` del workflow primero"*).

**Step 0 procedure (PowerShell, absolute git path per Windows doctrine):**

```powershell
$g = 'C:\Program Files\Git\cmd\git.exe'
Set-Location 'C:\Users\User\Apps\io-sos'
& $g fetch origin
# Read the workflow AS IT EXISTS ON main, not the working tree:
& $g show origin/main:.github/workflows/ci.yml
```

Then `Grep` the working tree for every pin site:

```
pattern: otp-version|28\.0\.1|28\.1   path: .github/workflows   (-n)
```

**Decision matrix:**

| `origin/main:ci.yml` shows | Action |
|---|---|
| `28.1` (or `28.1.1`) already | **STOP — no-op.** Report "#260 already landed this; `main` is on 28.1." Do not open a redundant PR. |
| `28.0.1` still | **PROCEED** to §5 branch + edit. |
| File path differs (e.g. `infinity-mie.yml` + `infinity-os.yml`, or a reusable `_setup-beam.yml`) | Re-target. Edit **all** pin sites; the "both apps red" symptom means both jobs share the pin source. |

> **Why this gate is hard-required:** the current branch is `feat/sos-batch1`, which branched for SOS work and may predate #260. The working-tree `ci.yml` could lag `main` in either direction. Reading `origin/main` is the only authority.

---

## 4. Technical Grounding — Reconciling the `re:import/1` Diagnosis

Prior memory recorded the root cause as *"OTP 28.0.x sin `:re.import/1`"* and noted *"el runtime imprime el remedio"* (the runtime printed the fix). The upstream research **confirms the fix direction and corrects the mechanism narrative**:

| Claim in prior notes | Upstream reality | Reconciliation |
|---|---|---|
| "28.0.x **lacks** `re:import/1`" | **Correct.** `re:import/1` was **introduced** by **OTP-19730** in **erts-16.1**, which ships **with OTP 28.1**. OTP 28.0.x bundles erts-16.0 → the function does not exist. | The undefined-function crash on `28.0.1` is a genuine **missing-API** error, healed by upgrading to the OTP that introduces it. |
| (implied) "28.1 removed something" | **Wrong framing.** There is **no `re:import/1` removal or deprecation** anywhere in the OTP 28.1 changelog. OTP-19730 is an **addition** (export/import support for compiled regexes, to move them safely between node instances). | The bump is additive, not a workaround for a removal. The fix *grants* the function rather than dodging a deprecation. |
| "fix = `28.0.1` → `28.1`" | **Correct and minimal.** 28.1 is the first OTP release containing erts-16.1. | Confirmed: 28.1 is the floor that makes `re:import/1` resolvable. |

**Consequence for scope:** because the failing call is almost certainly inside a **dependency** (project code rarely calls `re:import/1` directly — it is a compiled-regex transport primitive), do **not** chase the symptom in app source. The toolchain bump is the correct and sufficient remedy. If the crash persists after the bump, the next probe is `mix deps.tree` to find which dep introduced the `re:import/1` call, not an app-code edit.

**OTP 28.1 — full release facts (for the PR body / audit trail):**

- Git tag `OTP-28.1`, released **2025-09-17** by Henrik Nord; **predecessor OTP 28.0.4**; first maintenance patch for the OTP 28 series.
- **Only** documented *potential incompatibility*: **OTP-19756** (kernel) — the `inet_dns_tsig`/`inet_res` TSIG timestamp fix that corrected two **undocumented** error atoms to `notauth` and `notzone`. This touches DNS TSIG validation only; **no impact** on a typical Phoenix/Oban/Broadway CI build.

---

## 5. Branch-off-`main` Execution (scoped, single-file, pathspec)

Per InfinityOps multi-pane doctrine (*"branching off a dirty parent bundles unmerged commits; cherry-pick / branch off `origin/main` for scoped fixes"*) and the pathspec-scoped-commit rule:

```powershell
$g = 'C:\Program Files\Git\cmd\git.exe'
Set-Location 'C:\Users\User\Apps\io-sos'

# 1. Authoritative base — branch directly off the remote main, NOT off feat/sos-batch1
& $g fetch origin
& $g switch -c fix/ci-otp-28-1 origin/main

# 2. (Edit ci.yml here via the Edit tool — single token, all pin sites)

# 3. Scoped commit — pathspec restricts to the workflow file only
$msg = 'C:\Users\User\Apps\io-sos\_commitmsg.txt'
[System.IO.File]::WriteAllText($msg, "ci: bump otp-version 28.0.1 -> 28.1 (erts-16.1 introduces re:import/1)`n", (New-Object System.Text.UTF8Encoding($false)))
& $g commit -F $msg -- .github/workflows/ci.yml

# 4. Verify the subject landed under YOUR file (message-leg race guard)
& $g log -1 --format='%s'
```

**Doctrine guardrails applied:**

- **Branch off `origin/main`**, never off the dirty `feat/sos-batch1` working tree (which carries `M vault/progress.md` + untracked `vault/handoffs/` — those must **not** ride along).
- **Pathspec `-- .github/workflows/ci.yml`** on the commit — closes the shared-index file-leg contamination risk.
- **Commit message via UTF-8-no-BOM temp file** (`WriteAllText` + `UTF8Encoding($false)`) — avoids the BOM-in-subject trap recorded in BIS/SOS memory.
- **All git via the absolute `git.exe` path under PowerShell** — bare `git` is not on the `-NonInteractive` PATH on this host and silently falls back to the MSYS2 Bash bridge (the documented hang).

---

## 6. Pin-Value Recommendation — `'28.1'` vs `'28.1.1'` vs strict

The task names `28.1`. Two adjacent decisions are worth making explicitly rather than by default:

| Option | Behavior under setup-beam | Recommendation |
|---|---|---|
| `otp-version: '28.1'`, **loose** (default `version-type`) | Resolves by semver to the **highest 28.1.z** available — today that floats to **28.1.1**. Non-deterministic over time. | Acceptable but **drifts**. Matches the task literally. |
| `otp-version: '28.1'`, **`version-type: strict`** | Exact match to a build literally named `28.1`. | Deterministic, pins the task target exactly. **Preferred if you want 28.1-and-only-28.1.** |
| `otp-version: '28.1.1'`, **strict** | Pins the **2025-10-20** follow-up patch. | **Optional hardening.** 28.1.1 adds **OTP-19799** (`erlang:suspend_process()` no longer fails on dirty schedulers) and **OTP-19774** (SSL `max_fragment_length` regression introduced by an OTP-27 optimization). Touches only 5 apps (diameter-2.5.2, erts-16.1.1, kernel-10.4.1, ssl-11.4.1, xmerl-2.1.7) — all `re:import/1`-neutral, so it preserves the fix while being marginally more robust. |

**My recommendation:** ship **`otp-version: '28.1'` with `version-type: strict`** to satisfy the task deterministically. If the CI ever needs the dirty-scheduler/SSL fixes, a follow-up bumps the patch to `'28.1.1'`. Keep this PR to the **single token** — adding `version-type: strict` is a one-line, in-scope hardening if it isn't already present; do not expand further.

> **Elixir compatibility check (must-verify, flagged):** OTP 28 requires a recent Elixir. Confirm `elixir-version` in the same `with:` block is on a line that supports OTP 28 (Elixir **1.18.3+** is the safe floor for OTP 28; *I am flagging this as a verification point, not asserting the exact minor* — read the actual `elixir-version` value and cross-check against the Elixir/OTP compatibility table). Bumping OTP without a compatible Elixir reintroduces a different build failure. This is the most likely "the bump didn't fix it" trap after Step 0.

---

## 7. setup-beam Environment Sanity (context that makes the bump safe)

These facts confirm 28.1 will actually install on the runner and need no other change:

- **OS↔OTP band:** `ubuntu-24.04` supports **OTP 24.3–29** (x86_64 + arm64). **28.1 sits inside this band** — no runner-image change required. (`ubuntu-22.04`: 24.2–29; `ubuntu-26.04`: 26–29; `windows-2022/2025`: 21*–29; `macОS-14/15/26`: 25–29.) Confirm the `runs-on:` is one of these.
- **Binary source:** setup-beam pulls pre-built binaries from **`builds.hex.pm`** by default. If the OTP-28.1 asset 404s or the mirror is flaky in CI, the documented fallback is a newline-separated, ordered `hexpm-mirrors` list — `https://builds.hex.pm` then `https://cdn.jsdelivr.net/hex`. Keep this in the back pocket; do **not** add it pre-emptively (scope creep).
- **Action pin (out of scope, note only):** the workflow uses `erlef/setup-beam@v1` (movable latest-1.y.z; current release `v1.12.0`). Immutable pinning would be `@v1.12.0`. This is a **separate** supply-chain hardening decision — **do not bundle it** into this CI-fix PR.
- **Self-hosted runners** would need `ImageOS` env (e.g. `ubuntu24`) for asset download — only relevant if `runs-on:` is self-hosted; GitHub-hosted runners set this automatically.

---

## 8. Verification Gates (DONE = CI green on both apps, observed)

Per InfinityOps Gate 7 / Ley 25 (*DONE = QA pipeline PASS with observed evidence*; compiles ≠ works):

1. **Push the scoped branch** and open the PR against `main`.
2. **Watch the actual run** — `gh run list` / `gh run view` (via PowerShell, not the Bash bridge; `gh run view --log` is large — prefer per-job `gh api .../jobs/<id>/logs` as memory records).
3. **Both jobs must turn green** — `infinity_mie` *and* `infinity_os`. A single green is insufficient; the symptom was bilateral.
4. **Grep the install log** for the resolved OTP line — confirm setup-beam reports `OTP 28.1` (not a silently-floated 28.1.1 under loose, if you chose strict).
5. **Confirm the original crash class is gone** — the `re:import/1` undefined-function error must not appear in either app's `mix test` / `mix compile` output.
6. **No new flake** — if a *different* failure appears (e.g. `DatasetCollector` plaintext-ban flake, a known seed-dependent flake unrelated to this change), `gh run rerun --failed` and confirm it's environmental, not introduced.

**Do not mark done on a green-compile assumption.** The evidence is the run log, not the diff.

---

## 9. Risk Register & Rollback

| Risk | Likelihood | Mitigation |
|---|---|---|
| **#260 already merged → redundant PR** | Medium | Step 0 reads `origin/main:ci.yml` first. No-op detected → stop, report. |
| **Partial pin bump (one app left on 28.0.1)** | Medium | Grep **all** `.github/workflows/*.yml` for `28.0.1`; bump every site. |
| **Elixir version incompatible with OTP 28** | Medium | §6 verification — confirm `elixir-version` ≥ OTP-28-supporting floor before relying on the bump. |
| **Loose resolution floats to 28.1.1 unexpectedly** | Low | Use `version-type: strict` if 28.1-exact matters; otherwise accept 28.1.1 knowingly. |
| **Unquoted version misparse** | Low | Always `'28.1'` quoted. |
| **`re:import/1` crash persists post-bump** | Low | Then the call site is a dep on an even-newer API — probe `mix deps.tree`, not app source; this would be a *new* finding, not this fix failing. |
| **Mirror 404 on 28.1 asset** | Low | Add ordered `hexpm-mirrors` fallback (`builds.hex.pm` → `cdn.jsdelivr.net/hex`) only if observed. |

**Rollback:** the change is a single reversible token. If CI regresses unexpectedly, `git revert` the one commit; the prior pin `28.0.1` is restored with no migration or state to unwind. This is a fully reversible, low-blast-radius change.

---

## 10. Surprising Findings & Contrarian Recommendations

1. **The "removal" framing was inverted — and that matters for trust in the memory note.** OTP 28.1 *introduces* `re:import/1` (OTP-19730 / erts-16.1); nothing was removed. The fix works by **gaining** an API, not dodging a deprecation. *Recommendation:* correct the InfinityOps memory note (`feedback_ci_elixir_setup_beam_env_failure.md`) so the next agent doesn't hunt for a phantom "removed API." The empirical fix direction is right; the causal story should be re-stated as "28.0.x lacks `re:import/1`; erts-16.1 / OTP 28.1 adds it."

2. **Adopt `version-type: strict` repo-wide as the standing convention** (not just here). The default `loose` resolution silently floats `28.1`→`28.1.1`, `1.18`→highest-1.18.z, etc. For a Holding-OS control plane where reproducibility is doctrine, strict + exact pins (with a `version-file`/`.tool-versions` as the single source of truth) eliminates an entire class of "it built yesterday" drift. *This is the higher-leverage fix behind the one-line bump.*

3. **Consider jumping straight to `28.1.1`.** It is a strict superset of 28.1 for our purposes (preserves `re:import/1`, adds the dirty-scheduler `suspend_process` fix and the SSL `max_fragment_length` regression fix) and only touches 5 low-risk apps. If the CI ever exercises SSL fragmentation or dirty-scheduler-heavy NIF work, 28.1.1 is the safer floor at zero additional cost.

4. **Separate the action pin from the toolchain pin.** `erlef/setup-beam@v1` is movable. Pinning it to `@v1.12.0` (immutable) is real supply-chain hardening — but it is a *different* PR. Bundling it here would violate the scoped-commit discipline and muddy the CI-fix audit trail.

---

## 11. One-Line Status (for the closing report)

> **Step 0 gates everything:** read `origin/main:.github/workflows/ci.yml`. If it already shows `28.1`/`28.1.1`, this is a **no-op (#260 landed)** — report and stop. If it shows `28.0.1`, branch `fix/ci-otp-28-1` off `origin/main`, bump every `otp-version` pin site to `'28.1'` (strict), verify `elixir-version` ≥ OTP-28 floor, pathspec-scoped single-file commit, and gate DONE on **both** `infinity_mie` and `infinity_os` jobs going green with the `re:import/1` crash absent from the logs.

## Sources

- <https://www.erlang.org/news/181>
- <https://www.erlang.org/patches/otp-28.1>
- <https://erlangforums.com/t/erlang-otp-otp-28-1-released/5069>
- <https://elixirforum.com/t/patch-package-otp-28-1-1-released/73011>
- <https://devtalk.com/t/erlang-otp-28-1-released/215042>
- <https://github.com/erlef/setup-beam>
- <https://github.com/Passw/erlef-setup-beam>
- <https://whitespace.moe/erlef/setup-beam>
- <https://erlangforums.com/t/setup-beam-set-up-your-beam-based-github-actions-workflow/1690>
- <https://github.com/erlef/setup-beam/blob/main/README.md>
- <https://www.erlang.org/downloads/28>
- <https://www.erlang.org/downloads>
- <https://dev.to/abreujp/guia-completo-instalando-elixir-no-ubuntulinux-2404-3k04>

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — CI fix: otp-version 28.0.1 → 28.1 en ci.yml (branch limpio off main)
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 373.2 s
- **Errors during run:** 2
- **Started at:** 2026-06-29T21:02:36Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `web_search 'setup-beam erlang OTP 28.0.1 "re:import/...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://codeberg.org/mkljczk/setup-beam...': page-fetch: https://codeberg.org/mkljczk/setup-beam: HTTP Error 403: Forbidden`

</details>
