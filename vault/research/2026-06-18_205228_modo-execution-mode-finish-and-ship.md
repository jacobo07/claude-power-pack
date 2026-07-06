# The Ship Playbook: Finishing and Shipping Software with Confidence

*A synthesis of release-engineering research — deployment checklists, smoke gates, automated rollback, zero-downtime migrations, and push-to-deploy hooks — organized as an executable doctrine for "finish and ship" mode.*

---

## 1. Why Process, Not Talent, Decides the Ship

The headline finding from the **DORA State of DevOps Report** reframes the entire problem: elite teams deploy **multiple times per day** while holding a **change-failure rate below 5%**, and the differentiator is **process, not individual talent**. Shipping fast and shipping safely are not in tension — they are *both* downstream of disciplined, repeatable release mechanics.

The economics make the case for ceremony over heroics:

| Activity | Cost | Source |
|---|---|---|
| Checklist review before deploy | ~5 minutes | DeployHQ |
| Debugging a botched deploy | 2–4 hours | DeployHQ |
| 10 minutes of business-hours downtime (small SaaS) | thousands of dollars | DeployHQ |

The asymmetry is the whole argument: a 5-minute checklist guards against a 2–4 hour incident and a four-figure downtime bill. In **EXECUTION MODE — FINISH AND SHIP**, the temptation is to skip the ceremony. The data says the ceremony *is* the speed — it is what lets elite teams ship many times daily without the failure rate climbing.

---

## 2. The Three-Phase Release Checklist

Mature release checklists decompose into three sequential phases. Each phase is a gate; you do not advance until its items are green.

### 2.1 Pre-Deployment (build the confidence before you touch prod)

- **Code review** — the single most cost-effective defect-detection method (smoke testing is second; see §4).
- **Environment configuration** verified against target.
- **Build verification** — the artifact compiles and assembles cleanly.
- **Database migrations** that are **backward-compatible and tested** — non-negotiable (see §5).
- **Security / CVE scans** via **SAST** (static) and **DAST** (dynamic) tooling.

### 2.2 Deployment Execution (move the artifact, atomically)

- Deploy to **staging** first.
- Run **smoke tests** against staging.
- Take a **DB backup** before any schema change runs.
- Perform an **atomic deployment** — e.g., DeployHQ's **symlink flip**, which prevents partial deploys and enables **instant one-click rollback**.
- Run **migrations** in the controlled window.

### 2.3 Post-Deployment Validation (prove it lives)

- **HTTP 200 health checks** on the live endpoints.
- **Error-rate monitoring** via Sentry / Bugsnag / Rollbar for a **30-minute** soak.
- **Rollback path confirmed** — you do not declare success until you have re-verified that you can reverse.

> **Atomic deployment is the keystone.** A symlink-flip (or equivalent) means the live release pointer moves in a single operation. There is no window where half the new code is serving traffic, and reversal is just flipping the pointer back.

---

## 3. The Go/No-Go Gate: Binary or Nothing

A ship decision must be **binary** — pass/fail, never "mostly works." The research is emphatic on this. The industry-standard gate criteria:

**Immediate rejection (hard NO-GO) on any of:**
- Deploy failure
- 5xx on health check
- DB connection failure
- **Any P0 / critical-path failure** — 100% of P0 tests must pass

**Conditional acceptance permitted only for:**
- 1–2 **P1** failures, OR
- **< 20%** performance degradation

### 3.1 Three-Layer Gate Strategy

| Layer | Duration | Scope |
|---|---|---|
| Infrastructure | ~5 min | HTTP 200, health endpoint, DB connectivity |
| Component | ~10 min | Individual service/component behavior |
| Integration | ~15 min | End-to-end critical workflows |

Operationalize the "stop on first failure" discipline with **`pytest --maxfail=1`** — the gate aborts the instant a critical test breaks rather than burning time on a build already known to be unshippable.

---

## 4. Smoke Testing: Shallow, Broad, and Decisive

**Smoke testing** (a.k.a. **Build Verification Testing / BVT**) is the ISTQB-defined "set of tests run on each build that verifies the basic functionality of the system under test." Its defining geometry is **shallow-but-broad**:

- It covers the **critical ~20%** of functionality — **auth, core navigation/workflows, critical integrations, data persistence** — that, **if broken, renders the other 80% of testing irrelevant**.
- Contrast with siblings: **sanity testing** is narrow/deep at change-level; **regression testing** is comprehensive.

### 4.1 The Cost-Effectiveness Pedigree

- **Microsoft research:** after code reviews, smoke testing is the **most cost-effective** defect-detection method. *(Original source: MSDN Library for Visual Studio 2005, "Guidelines for Smoke Testing," ms182613, dated 26 June 2007 — Wikipedia citation [10].)*
- **CI-maturity hallmark:** IEEE and Steve McConnell's *Code Complete* cite **daily builds + smoke tests** as signatures of CI maturity. Further authoritative backing: McConnell's *Rapid Development* (Microsoft Press, p. 405); Kaner/Bach/Pettichord, *Lessons Learned in Software Testing* (Wiley, 2002, p. 95); Dustin/Rashka/Paul, *Automated Software Testing* (Addison-Wesley, 1999, pp. 43–44).

### 4.2 Quality Targets

| Metric | Target |
|---|---|
| Execution time | **< 20 min** (ideally **< 15 min**); upper bound **< 30 min** |
| Critical-path coverage | **100%** |
| False-positive rate | **< 5%** |
| Test stability | **> 95%** |
| Automated smoke coverage (best practice) | **80%+** |

Supporting data points:
- Teams with **mature smoke-test documentation** report a **40–60% reduction** in time wasted testing unstable builds.
- **SmartBear State of Testing 2024:** **73%** of QA teams automate at least part of regression suites.
- **AI-native / self-healing** tools claim **95% accuracy** adapting to UI changes and an **81–88% reduction** in test-maintenance effort.

> In ship mode, the smoke suite is your go/no-go instrument. Keep it under 15 minutes so it never becomes the reason you skip it.

---

## 5. Zero-Downtime Database Migrations

Migrations are where "finish and ship" most often turns into "finish and roll back." The rules:

- **Backward compatibility is non-negotiable** — the old code must keep working against the new schema during the rollout window.
- **Online schema-change tools** make this safe by avoiding table locks:
  - **GitHub's `gh-ost`**
  - **Percona's `pt-online-schema-change`**
  - Mechanism: create a **ghost (shadow) copy** of the table, apply the schema change to the copy, backfill + sync, then **swap tables live**.
- Always take a **DB backup** immediately before the migration runs (§2.2).

This is the data-layer expression of the same atomic principle from §2: change happens on a shadow, the swap is a single operation, and the pre-swap state remains recoverable.

---

## 6. Rollback: Decouple Deploy from Release, Automate Recovery

### 6.1 Strategy Catalog

| Strategy | Mechanism | Authority |
|---|---|---|
| **Blue-green deployment** | Two identical environments; flip traffic | Martin Fowler |
| **Feature flags** | Decouple *deploy* from *release* — ship dark, flip on later | LaunchDarkly |
| **Kubernetes** | `kubectl rollout undo` | K8s native |
| **Spinnaker** | Multi-cloud pipeline orchestration | Netflix/Google |
| **Azure DevOps** | Release pipelines with **pre/post-deployment gates + approvals** (gate delay capped at **48 hours**) | Microsoft |

The **feature-flag** insight is the strategic one: when deploy and release are decoupled, a "rollback" can be a flag flip with **zero redeploy** — the safest possible reversal.

### 6.2 AWS CodeDeploy Automatic Rollback — The Both-or-Nothing Trap

Automatic rollback in CodeDeploy is a frequent silent-failure source because it requires **two** configurations set together:

1. **`automaticRollbackConfiguration`** — events: `DEPLOYMENT_FAILURE`, `DEPLOYMENT_STOP_ON_ALARM`, `DEPLOYMENT_STOP_ON_REQUEST`
2. **`alarmConfiguration`** — CloudWatch alarms referenced **by name**

> **Either one missing breaks the feature entirely.** You can have alarms with no rollback config, or rollback config pointed at no alarms — both look configured and neither works.

Additional CodeDeploy specifics:
- **`ignorePollAlarmFailure: false`** → if CodeDeploy **can't read alarm state** (IAM permission gap, deleted alarm), the deploy is **marked failed** — the safe default.
- **`ignorePollAlarmFailure: true`** → proceeds anyway, **defeating the safety net**.
- Up to **10 CloudWatch alarms** per deployment group.
- The CodeDeploy **service role needs CloudWatch permissions** to read alarm state.

### 6.3 Tuning Alarms to Avoid False-Positive Rollbacks

A rollback that fires on noise is worse than no rollback — it erodes trust and reverts good deploys. Three patterns prevent this:

1. **Multi-datapoint evaluation:** `evaluation-periods 3, datapoints-to-alarm 2` — fires only when **2 of the last 3** one-minute datapoints breach, not a single spike.
2. **Absolute counts at low traffic, not percentages:** at **0.5 RPS, a single 5xx = 3.3%** error rate — a percentage threshold would trip constantly. Use **counts**.
3. **Scope to the target group, not the whole ALB:** alarm on `HTTPCode_Target_5XX_Count`, **not** overall ALB 5xx, to exclude downstream noise.

**Recommended thresholds:**

| Metric | Threshold | Treat-missing-data |
|---|---|---|
| 5xx | `Sum > 5` | `notBreaching` |
| p95 `TargetResponseTime` | `> 0.8s` (800 ms) | `notBreaching` |

**The noise math:** an alarm firing **once/week** on noise trips **~14%** of deploys; **once/month** trips **~3%**. Tune to the once-a-month end of that band.

### 6.4 Blue/Green ASG Timing — The Termination-Wait Window

For blue/green EC2/ASG deployments, alarms get their chance to fire during the **original instance termination wait time** (`terminationWaitTimeInMinutes`):

- When an alarm fires **inside this window**, the ALB listener **swaps the target group back to blue**, and the green ASG is terminated.
- **Recommended floors:** **15 min** (internal APIs) to **20–30 min** (customer-facing) — long enough to catch five-minute metrics with **≥2 evaluation periods**. **Never set to zero.**
- **Payoff:** automatic rollback yields **~90-second recovery** vs. **~25 minutes manual**.
- **Verify it actually works:** force the alarm during an in-progress deploy with
  `aws cloudwatch set-alarm-state --state-value ALARM`
  and confirm the rollback fires. An untested rollback is a hypothesis, not a safety net.

---

## 7. Push-to-Deploy: The Git Hook Mechanics

The lightweight ship pattern — `git push production main` triggers a live deploy — rests on **push-triggered hooks**, and the details are where it silently breaks.

### 7.1 The Five Push-Triggered Hooks

All five — **`pre-receive`, `update`, `post-receive`, `post-update`, `push-to-checkout`** — **always execute in `$GIT_DIR`** (not the worktree root) and run on the **remote** via `git-receive-pack`.

| Hook | Runs | Can abort push? | Receives |
|---|---|---|---|
| `pre-receive` | once, before updates | **Yes** — non-zero exit rejects **all** ref updates atomically | old+new OIDs on stdin |
| `update` | per-ref | Yes (per ref) — enforces fast-forward-only / access control | per-ref values |
| `post-receive` | once, after **all** updates | **No** | `<old-oid> SP <new-oid> SP <ref-name>` lines on stdin |
| `post-update` | once, after updates | No | (superseded by post-receive) |
| `push-to-checkout` | on push to checked-out branch | customizes `updateInstead` | — |

`post-receive` **supersedes `post-update`** by giving both old and new values, making it the canonical deployment/notification hook. *(githooks doc last updated Git 2.54.0, 2026-04-20; default post-receive is empty; Git ships a sample `post-receive-email` in `contrib/hooks`.)*

### 7.2 The Canonical Push-to-Deploy Recipe

```bash
# On production:
git init --bare ~/project.git

# post-receive hook (executable!):
git --work-tree=/var/www/html --git-dir=$HOME/project.git checkout -f

# On dev machine:
git remote add production user@server:project.git
git push production main
```

**Branch-gate the hook** so feature/test branches deploy nothing:

```bash
while read oldrev newrev ref; do
  if [[ $ref =~ refs/heads/main$ ]]; then   # or .*/master$
    git --work-tree=/var/www/html --git-dir=$HOME/project.git checkout -f
  fi
done
```

Only the **designated production branch** triggers the checkout — pushing `feature/x` is a no-op deploy.

### 7.3 The Four Gotchas That Silently Break It

1. **Executable bit required:** without `chmod +x`, Git **silently ignores** the hook. Sample hooks ship with a **`.sample` suffix** that must be removed to activate. *(Hooks dir overridable via `core.hooksPath`.)*

2. **Inherited Git env vars poison foreign checkouts:** push hooks inherit exported `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE`. Critically, **`GIT_INDEX_FILE=.git/index` is relative to the working dir** — a checkout into `/var/www/html` **fails** unless you **`unset GIT_INDEX_FILE`** (or clear via `$(git rev-parse --local-env-vars)`) before invoking Git against the foreign worktree.

3. **`receive.denyCurrentBranch`:** by default Git **rejects** pushes to the currently checked-out branch of a **non-bare** repo (`error: refusing to update checked out branch`), because it would desync index/work-tree from HEAD. Values:

   | Value | Behavior |
   |---|---|
   | `refuse` (default) | rejects + squelches message |
   | `warn` | allows, warns |
   | `ignore` | allows but leaves work tree **stale/inconsistent** |
   | `updateInstead` | updates branch/HEAD **and** working dir atomically |

   This is *why* the **bare-repo** pattern (`git init --bare`) is standard — a bare repo has no checked-out branch to conflict with.

4. **`updateInstead` safety semantics:** `receive.denyCurrentBranch=updateInstead` updates **both** the branch/HEAD and the working directory **atomically** on push — but **only** when HEAD and the working dir match the pre-push state. **If the remote's working tree has local changes, the push is rejected**, making it safe for pushing directly to webservers. Behavior is customizable via the **`push-to-checkout`** hook.

> **Access control note:** the **`update`** hook (per-ref, fast-forward-only enforcement) is the recommended layer for access policy, ideally paired with **git-shell** to restrict wire access without handing out filesystem ownership.

---

## 8. The Consolidated Ship Checklist

Pulling every learning into one executable gate sequence:

### Pre-Deploy
- [ ] Code review complete (most cost-effective defect filter)
- [ ] SAST + DAST / CVE scans clean
- [ ] Build verified, environment config confirmed
- [ ] DB migration is **backward-compatible** and tested; online tool (`gh-ost`/`pt-osc`) staged if schema changes
- [ ] Feature flags wired for any risky path (deploy ≠ release)

### Deploy
- [ ] Deployed to **staging**; smoke suite green there
- [ ] **DB backup** taken
- [ ] **Atomic** deploy (symlink flip / blue-green) — no partial state
- [ ] Migration run inside the window
- [ ] Push-to-deploy hook: executable bit set, branch-gated, `GIT_INDEX_FILE` unset, bare repo

### Go/No-Go Gate (binary)
- [ ] 100% of P0 / critical-path tests pass (`pytest --maxfail=1`)
- [ ] HTTP 200 health check; DB connects; no 5xx
- [ ] Smoke suite under 15 min, false-positive rate < 5%
- [ ] Conditional accept only for ≤2 P1 failures or <20% perf degradation

### Rollback Readiness
- [ ] **Both** `automaticRollbackConfiguration` **and** `alarmConfiguration` set (CodeDeploy)
- [ ] `ignorePollAlarmFailure: false`; service role has CloudWatch perms
- [ ] Alarms: `eval-periods 3 / datapoints 2`, absolute counts, target-group-scoped, `treat-missing notBreaching`
- [ ] `terminationWaitTimeInMinutes` ≥ 15 (internal) / 20–30 (customer-facing), **never 0**
- [ ] Rollback **tested** via forced `set-alarm-state ALARM`
- [ ] One-click / pointer-flip reversal confirmed

### Post-Deploy
- [ ] HTTP 200 health checks live
- [ ] Error-rate monitoring (Sentry/Bugsnag/Rollbar) for **30 min**
- [ ] Rollback path re-confirmed before declaring done

---

## 9. Closing Doctrine

The thread through every learning is the same principle expressed at four layers:

| Layer | Atomic mechanism | Reversal |
|---|---|---|
| File/release | Symlink flip | Flip back (one click) |
| Data | Ghost-table swap (`gh-ost`) | Pre-swap backup |
| Traffic | Blue-green target-group swap | ALB listener swap to blue (~90s) |
| Feature | Flag flip | Flag flip (no redeploy) |

**Ship mode is not the absence of process — it is process made fast.** Elite teams ship many times a day *because* the checklist, the binary gate, the under-15-minute smoke suite, and the tested automatic rollback are all in place. Each costs minutes; each saves hours. The discipline is what makes "FINISH AND SHIP" a safe sentence rather than a gamble.

The single most important guardrail to verify before you push: **automatic rollback must be tested, not assumed** — force the alarm, watch it revert, *then* ship. An untested safety net is just a story you tell yourself about the deploy you're about to regret.

## Sources

- <https://testsigma.com/blog/software-release-checklist/>
- <https://checkoff.ai/blog/software-release-checklist>
- <https://www.deployhq.com/blog/the-ultimate-deployment-checklist-ensuring-smooth-and-successful-releases>
- <https://articles.mergify.com/software-deployment-checklist/>
- <https://learn.microsoft.com/en-us/azure/devops/pipelines/release/approvals/?view=azure-devops>
- <https://stackharbor.com/en/knowledge-base/awsdeploy-rollback-automation-cloudwatch/>
- <https://docs.aws.amazon.com/codedeploy/latest/userguide/monitoring-cloudwatch-events.html>
- <https://docs.aws.amazon.com/codedeploy/latest/userguide/monitoring-create-alarms.html>
- <https://kindatechnical.com/aws-codedeploy/automating-rollbacks.html>
- <https://stackharbor.com/en/knowledge-base/awsdeploy-blue-green-ec2-asg/>
- <https://git-scm.com/docs/githooks>
- <https://www.digitalocean.com/community/tutorials/how-to-use-git-hooks-to-automate-development-and-deployment-tasks>
- <https://gist.github.com/noelboss/3fe13927025b89757f8fb12e9066f2fa>
- <https://dev.to/copyleftdev/mastering-git-hooks-a-cheat-sheet-for-cicd-ninjas-3057>
- <https://www.geeksforgeeks.org/git/customizing-git-hooks-for-workflow-automation/>
- <https://stackoverflow.com/questions/12265729/what-are-the-consequences-of-using-receive-denycurrentbranch-in-git>
- <https://stackoverflow.com/questions/34696771/how-does-receive-denycurrentbranch-updateinstead-interact-with-the-index>
- <https://git-annex.branchable.com/tips/making_a_remote_repo_update_when_changes_are_pushed_to_it/>
- <https://www.geeksforgeeks.org/software-engineering/smoke-testing-software-testing/>
- <https://yrkan.com/blog/smoke-test-checklist-docs/>
- <https://www.virtuosoqa.com/testing-guides/smoke-testing>
- <https://www.baserock.ai/blog/smoke-testing>
- <https://scholar.google.com/>
- <https://dx.doi.org/>
- <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf>
- <https://en.wikipedia.org/wiki/Smoke_testing_(software)>

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — FINISH AND SHIP
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, regex-fallback, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 459.4 s
- **Errors during run:** 1
- **Started at:** 2026-06-18T18:52:28Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://lobehub.com/skills/openclaw-skills-verification-befo...': page-fetch: https://lobehub.com/skills/openclaw-skills-verification-before-completion: HTTP Error 429: Too Many Requests`

</details>
