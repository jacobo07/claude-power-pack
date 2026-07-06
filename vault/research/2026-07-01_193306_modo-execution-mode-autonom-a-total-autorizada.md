# Claude Code Auto Mode: Anatomy of "Total Autonomy" and Why It Is a Governed Illusion

## Framing Note

The trigger for this report — *"MODO: EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA"* — is precisely the mental model that Claude Code's Auto Mode architecture is engineered to refute. There is no switch that grants an agent unbounded execution. What the product ships is a *governed* autonomy: a server-side classifier, a four-tier precedence stack, non-configurable circuit breakers, and a set of protected paths that no configuration short of a deliberate `bypassPermissions` escape hatch can dissolve. This report synthesizes the current research into that architecture, treating "total autonomy" not as a state that can be authorized but as an asymptote the system deliberately never reaches. Every claim below is drawn directly from the documented behavior of the feature.

---

## 1. What Auto Mode Is

Auto Mode is Anthropic's shift of Claude Code from an *assistant that asks at every step* to an *autonomous agent that self-approves the majority of intermediate actions*. Industry coverage (AI Business) framed it as "no babysitting Claude" and positioned it as Anthropic's competitive answer to OpenAI's agentic offerings — a paradigm shift from assistant to agent.

Mechanically, Auto Mode inserts a **server-side classifier** into the tool-call path. Instead of prompting the human on each action, the classifier decides whether an action is safe to auto-approve. It **allows** low-risk, reversible operations (working-directory edits, lock-file installs) and **blocks** the irreversible, destructive, or externally-visible class of actions.

### Canonical block examples

| Category | Representative action blocked |
|---|---|
| Remote code execution | `curl \| bash` |
| Destructive VCS | `git reset --hard`, force-push to `main` |
| Production exposure | prod deploys |
| Externalized / irreversible effects | actions leaving the sandbox or trust boundary |

### Version gating

Auto Mode is **not universally available** — its enablement is tightly version- and provider-gated:

| Provider / surface | Requirement |
|---|---|
| Baseline availability | Claude Code **v2.1.83+** |
| Bedrock / Vertex / Foundry | env var `CLAUDE_CODE_ENABLE_AUTO_MODE=1`, **v2.1.158+** |
| Bedrock/Vertex/Foundry model support | **Sonnet 5, Opus 4.7, Opus 4.8 only** |
| Anthropic API | **Opus 4.6+ / Sonnet 4.6+** |

The provider matrix matters: on the cloud-provider surfaces the model set is explicitly restricted, whereas on the first-party Anthropic API a broader recent-model floor applies.

---

## 2. The Precedence Stack: Four Tiers After the Permissions System

The single most important structural fact is that Auto Mode's classifier does **not** sit at the top of the decision chain. It is subordinate to the permissions system, and internally it resolves conflicts through a strict, ordered cascade. Understanding this order is the difference between a durable guarantee and a soft preference.

**Evaluation order (highest authority first):**

1. **`permissions.deny`** — the managed permissions layer. Blocks *before* the classifier ever runs. Unoverridable. This is the only hard guarantee for boundaries you truly need enforced.
2. **`hard_deny`** (v2.1.136+) — unconditional within the classifier. Ignores `allow` and ignores explicit user intent. A genuine wall.
3. **`soft_deny`** — the destructive-action tier. Blocks by default but is **overridable**.
4. **`allow` exceptions** — override a matching `soft_deny`.
5. **Explicit user intent** — overrides *remaining* soft blocks (but never `hard_deny` or `permissions.deny`).

The crucial asymmetry: a conversational "yes, do it" can dissolve a `soft_deny`, but it is inert against `hard_deny` and against the managed `permissions.deny`. If you want a boundary that survives cajoling, compaction, and clever prompting, it must live at tier 1 or tier 2 — **a deny rule is the only hard guarantee.**

### Configuration sources and the anti-injection rule

Configuration is read from a defined set of scopes:

- `~/.claude/settings.json`
- `.claude/settings.local.json`
- Managed settings
- `--settings` / Agent SDK

Entries are **additive across scopes** — a developer-level `allow` can override an org-level `soft_deny`, precisely because a `soft_deny` is not a hard boundary. This is a feature (local flexibility) and a risk (local weakening) simultaneously.

Two deliberate anti-self-escalation defenses close the obvious attack surface:

- **`autoMode.allow` / `soft_deny` / `hard_deny` are IGNORED when read from a checked-in `.claude/settings.json`.** A repository cannot inject its own allow rules into a cloning developer's session.
- **Claude Code v2.1.142+ ignores `defaultMode: auto` from repo-level `.claude/settings.json`** — a repo cannot self-grant Auto Mode to whoever opens it.

Together these mean the trust decision stays with the human operating the machine, not with the code being operated on.

---

## 3. Protected Paths: The Fixed Perimeter

Independent of the classifier tiers, a set of **protected paths** is *never* auto-approved in any mode:

`.git`, `.claude`, `.npmrc`, `.bashrc`, and similar sensitive dotfiles/config locations.

The single exception is **`bypassPermissions`**, which as of **v2.1.126** stopped prompting for these paths entirely. This makes `bypassPermissions` the true "total autonomy" mode — and it is exactly the mode a responsible operator should treat as radioactive, because it removes the last standing guard on the files that define identity, credentials, and history.

---

## 4. Configuration Surface: Trust Slots and Sensitivity Slots

The classifier is not meant to be fought with per-command allow rules. The **primary, intended tuning field is `autoMode.environment`** — free-prose describing trusted repos, buckets, and internal domains. This is the field that *fixes most false positives*, because it teaches the classifier what "your normal" looks like rather than whitelisting individual commands.

As of **v2.1.195**, `claude auto-mode defaults` enumerates two families of configuration slots:

### Trust slots (what the agent may treat as safe)

| Slot | Default |
|---|---|
| Trusted repo | working repo |
| Source control | working repo + remotes |
| Trusted internal domains | None configured |
| Trusted cloud buckets | None configured |
| Key internal services | None configured |
| Internal package registry | None configured |

Only *repo* and *source control* default to something concrete (the working repo and its remotes); everything else defaults to **"None configured,"** meaning the classifier will treat those categories conservatively until you describe them.

### Sensitivity slots (what the agent must treat as dangerous)

| Slot | Default behavior |
|---|---|
| PII / regulated-data locations | broad heuristic |
| Sensitive remote targets | broad heuristic — **any host/namespace named `prod`/`production` is sensitive** |
| Protected IaC scopes | broad heuristic |

The sensitivity slots default to *broad* heuristics — the system errs toward suspicion. This is the design philosophy in miniature: trust is opt-in and narrowly declared; danger is assumed by default and widely construed. The `prod`/`production` naming heuristic is a concrete example — merely naming a target `prod` recruits it into the sensitive-remote-target set automatically.

---

## 5. The `$defaults` Splice: A Silent Footgun

A subtle but high-consequence mechanic governs how custom rule arrays interact with built-in rules. In any `environment`, `allow`, `soft_deny`, or `hard_deny` array:

- Including the literal string **`"$defaults"`** *splices in* the built-in rules alongside your custom entries.
- **Omitting `"$defaults"` REPLACES the entire default list.**

The failure mode is severe and silent: a `soft_deny` array written *without* `$defaults` discards the built-in protections — force-push, `curl|bash`, prod-deploy rules all vanish — because the operator's intent was "add one rule" but the semantics were "replace all rules." Anyone authoring custom classifier arrays must include `"$defaults"` unless they *deliberately* intend a full replacement.

### `classifyAllShell`

`autoMode.classifyAllShell: true` (requires **v2.1.193+**) **suspends every Bash/PowerShell allow rule**, forcing the classifier to evaluate *all* shell commands from scratch. This is the "trust nothing at the shell layer" switch — maximally conservative, useful when shell allow rules have accreted beyond what you can audit.

---

## 6. The Compaction Hazard: Why Conversational Boundaries Are Not Guarantees

This is the most operationally dangerous property, and it deserves emphasis for anyone tempted by "total autonomy."

The classifier treats **conversational boundaries** — statements like *"don't push,"* *"wait until I review"* — as **block signals**. But critically, these are **re-read from the transcript on each check.** They are not compiled into durable rules; they are re-derived from conversation history every time.

The consequence: **during context compaction, a spoken boundary can be silently lost.** If the turn where you said "don't push to main" gets summarized away, the boundary it encoded evaporates, and the classifier no longer sees the block signal. The action you forbade an hour ago can quietly become auto-approvable.

**The only durable protection is a deny rule** (`permissions.deny` / `hard_deny`), which lives in configuration, not conversation, and therefore cannot be compacted out of existence. In an "autonomy total" posture — long-running, unsupervised, context-churning — this is *the* failure mode to design against. Speak your boundaries, yes; but *encode* the ones that matter.

---

## 7. Circuit Breakers: The Non-Configurable Backstop

Auto Mode has hard-coded self-arrest thresholds that no configuration can raise or lower:

| Trigger | Threshold | Effect |
|---|---|---|
| Consecutive blocks | **3** | Pause; revert to prompting |
| Total blocks (session) | **20** | Pause; revert to prompting |

Both thresholds are **non-configurable**. When Auto Mode hits a wall of blocks — a sign it is either misconfigured or attempting something the classifier persistently distrusts — it *stops auto-approving and hands control back to the human.* This is the mechanical embodiment of "total autonomy is not a real state": the system is built to demote itself back to supervised operation the moment its own judgment is repeatedly contested.

---

## 8. Observability and Tooling

Autonomy without observability is negligence, and the tooling reflects that.

### CLI surface

| Command | Purpose |
|---|---|
| `claude auto-mode defaults` | Print the Trust-slot and Sensitivity-slot entry types (v2.1.195) |
| `claude auto-mode config` | Inspect / manage configuration |
| `claude auto-mode critique` | **Flags ambiguous, redundant, or false-positive-prone rules** in your config |

The `critique` subcommand is the underrated one — it audits your own rule set for the exact pathologies (ambiguity, redundancy, false-positive bait) that make an autonomous agent misbehave.

### Denial visibility and reaction

- Denials appear in the **`/permissions` "Recently-denied" tab**; press **`r`** to retry a denied action.
- The **classifier reason is shown in the transcript** since **v2.1.193** — you can see *why* an action was blocked, not merely *that* it was.
- Programmatic reaction is available through the **`PermissionDenied` hook**, letting you script responses to denials (log, alert, escalate, adapt).

---

## 9. Documented Risks of Removing the Human

Anthropic's own positioning, and the surrounding coverage, are candid about the cost of removing supervision at each intermediate step:

- **Increased hallucinations** when the human is no longer validating intermediate reasoning.
- **Degraded code quality on complex programming tasks** — the compounding-error problem, where an unreviewed wrong step becomes the foundation for the next.

The paradigm shift (assistant → autonomous agent) buys throughput at the cost of the per-step human check that catches drift early. Auto Mode's classifier defends against *destructive* and *irreversible* actions; it does **not** defend against *quietly wrong* ones. A hallucinated but non-destructive edit sails through auto-approval. This is the residual risk that no classifier tier addresses, and it is why "AUTONOMÍA TOTAL" on a complex build is a quality gamble even when it is a safety non-event.

---

## 10. Practical Doctrine for an "Execution Mode" Posture

Synthesizing the above into actionable guidance for anyone actually running Auto Mode aggressively:

1. **Encode boundaries that matter as deny rules, not conversation.** Anything you'd be genuinely harmed by — `permissions.deny` (tier 1) or `hard_deny` (tier 2). Conversational "don't do X" is compaction-fragile.
2. **Tune with `environment` prose first, allow-rules last.** Describing trusted repos/buckets/domains fixes most false positives at the root; per-command allow-lists accrete into unauditable sprawl.
3. **Always include `"$defaults"`** in any custom `allow`/`soft_deny`/`hard_deny`/`environment` array unless you *intend* to nuke the built-ins.
4. **Run `claude auto-mode critique`** against your config before a long autonomous run — it flags the false-positive-prone and redundant rules that will otherwise cause mid-run block cascades.
5. **Respect the circuit breakers as signal, not obstacle.** Hitting 3 consecutive blocks means your config or your plan is wrong — diagnose, don't brute-force. (You *can't* raise the threshold anyway.)
6. **Never confuse `bypassPermissions` with Auto Mode.** Auto Mode keeps the protected-path perimeter and the classifier; `bypassPermissions` removes them. The former is governed autonomy; the latter is the thing that removes the guard on `.git`, `.claude`, and `.npmrc`.
7. **Watch the transcript reason strings (v2.1.193+)** and wire the `PermissionDenied` hook if the run is truly unattended — it is your only programmatic feedback channel when no human is watching.

---

## 11. Synthesis: "Total Autonomy" Is Architecturally Impossible by Design

The phrase that opened this report asks the system to grant something it is specifically built never to grant. Every layer of the design is a deliberate refusal of totality:

- The **classifier** blocks the irreversible/destructive/external class regardless of intent.
- The **four-tier precedence** places `permissions.deny` and `hard_deny` above user intent, so even an explicit human command cannot dissolve the hardest boundaries.
- **Protected paths** stay guarded in every mode except the explicitly-named escape hatch.
- **Repo-injected auto mode and repo-injected allow rules are ignored**, so autonomy can never be self-granted by the artifact being worked on.
- **Non-configurable circuit breakers** force a demotion back to supervised operation the moment the agent's judgment is repeatedly contested.
- And the **compaction hazard** ensures that even the *softest* form of autonomy — an agent honoring your spoken wishes — is honestly disclosed as fragile, with the durable alternative (deny rules) named plainly.

The correct reading of "EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA" is therefore not a license but a **configuration posture**: run with Auto Mode enabled, tune the trust and sensitivity slots to your real environment, encode your true red lines as deny rules, and accept that the system will — by design, and for your benefit — refuse to be *totally* autonomous. The autonomy on offer is real, substantial, and productivity-transforming. It is also, deliberately and permanently, bounded.

## Sources

- <https://code.claude.com/docs/en/permission-modes>
- <https://www.tesery.com/es-es/blogs/tesla-model-3-s-x-y-cybertruck-guides/unlocking-autonomy-how-to-engage-full-self-driving-mode-in-your-tesla>
- <https://marcmarpal.com/knowledge/8176/anthropic-auto-mode-means-no-more-babysitting-claude/>
- <https://code.claude.com/docs/en/auto-mode-config>
- <https://medium.com/@dan.avila7/step-by-step-complete-auto-mode-configuration-in-claude-code-2ca3a0267a08>
- <https://spybara.com/anthropic/claude-code/>

_Note: 3 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA
- **Depth / breadth:** 2 / 3
- **Queries used:** 2 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 260.8 s
- **Errors during run:** 4
- **Started at:** 2026-07-01T17:33:06Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://www.tesla.com/ownersmanual/modely/es_mx_0126/GUID-2C...': page-fetch: https://www.tesla.com/ownersmanual/modely/es_mx_0126/GUID-2CB60804-9CEA-4F4B-8B04-09B991368DC5.html: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.tesla.com/ownersmanual/models/es_mx/GUID-B3EF4EA...': page-fetch: https://www.tesla.com/ownersmanual/models/es_mx/GUID-B3EF4EAF-6B25-4590-9DDC-B8767F143377.html: HTTP Error 403: Forbidden`
- `fetch_page 'https://github.com/johnzfitch/claude-wiki/blob/master/02-Cla...': page-fetch: https://github.com/johnzfitch/claude-wiki/blob/master/02-Claude-Code-CLI/auto-mode-config-f0dacf5866.md: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://github.com/bartvanhoey/claude-code-docs/blob/main/do...': page-fetch: https://github.com/bartvanhoey/claude-code-docs/blob/main/docs/auto-mode-config.md: HTTP Error 404: Not Found`

</details>
