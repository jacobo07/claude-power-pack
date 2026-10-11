---
covers: [ccr, cognitive-runtime-mod, ctx-rent-a2, ssm, tool-linker, skill-linker, constitution-linker, memory-linker, epoch-compiler]
status: APPROVED 2026-10-11, Owner "y go p95" (38M total; goal ccr = 38M - ctx-rent-a2 remainder 1.12M = 36.9M)
amends: vault/plans/context-rent-a2-2026-10-11.md (goal ctx-rent-a2)
---
# CCR: the CPP Cognitive Runtime as a Claude Code mod (Amendment A3 of ctx-rent-a2)

Backup of the inline Master Plan. The chat message is the approval surface.

## 0. Reality delta (2026-10-11, bounded scan)
- Host: Claude Code **2.1.296**, `C:\Users\User\.local\bin\claude.exe`, Windows 11. 33 live `claude` processes.
- Mods API: function-hook plugins, `register(on, options)`, `($, e, next)` chain. Five tiers, from outermost to innermost:
  `prepend` and `append` (managed, admin-listed), then `user`, then `builtin`, then `core`. Source:
  `bundled-skills/2.1.296/.../types/claude-code.d.ts`.
- Hook budget: 10 s per dispatch, a 1 s grace for `.catch`, 5 s linger. **A hook that fails is skipped (fail OPEN) unless
  its `.catch` refuses.** `engine.create` has no budget.
- Caching: `prompt.section`, `prompt.context`, `prompt.attachment`, `tool.describe`, `command.describe` and
  `config.describe` cache for the session, until `$.ui.invalidate`.
- The "74,203 to 10,133" ablation is **NOT found in repo**; treat it as UNVERIFIED. The repo's own measurement
  (ctx-rent-a2 slice A, 4de21ba8): fresh floor **122,093**, which splits into 32,664 host-cached and 89,427 CPP
  session floor. CPP files are 139.8K chars (61 % of attributed). Host listings are 57.5K (25 %). The low-floor
  launch flags are in `tools/gsd_mission.py:750`: `--setting-sources=local --strict-mcp-config
  --disable-slash-commands --tools=...`.
- Existing owner: goal **ctx-rent-a2** (cap 14M, approved P95). Slices A (census) and B (floor reduction, in progress
  today: the rules stubs are already collapsed into the skill index) are underway. C through L are planned. The CCR
  mod is the **execution backend of ctx-rent-a2**, not a new programme.
- Madzia = the KobiiMii character work in the KSR repo. Its goal will be resolved at slice Z, not before.

## A. Mods capability matrix (types-verified; RUNTIME-VERIFY in M1)
| Surface | Arrives | Authority | CCR use |
|---|---|---|---|
| prompt.compose | sections[{id,text,scope}], model, tools (names), outputStyle | ADD/REMOVE/REWRITE/REORDER sections | the engine's safety sections are a PROTECTED floor by CCR policy; CCR adds a `ccr:image` section (scope session) |
| prompt.section | name, text | REWRITE / DROP (null) per section (`memory`, `env_info_*`, …) | **Memory Linker**: replaces `memory` with a paged subset |
| prompt.context | blocks (claudeMd, userEmail, currentDate…), instructionFiles[{path, kind, content, parent}] | ADD/DROP/REWRITE per block; claudeMd rebuildable per file; once per conversation | **Constitution Linker**: per-file closure; kind=Managed is never touched |
| prompt.attachment | type, origin{engine\|hook(event)\|plugin}, text | REWRITE / DROP (text null), cached | **Attachment Firewall**: skill/deferred-tool listings, advisory hook context (this session: a 10.7 KB UserPromptSubmit payload) |
| tool.describe | tool, description | REWRITE, `isDeferred` true/false (moves the tool behind ToolSearch); cached | **Tool Linker** = deferral. A tool is never deleted; ToolSearch is the page fault |
| tool.call / tool.check | tool, input, agentId | DENY / REWRITE / ANSWER / OBSERVE | page-fault telemetry; never weakens a deny (managed and PreToolUse deny first) |
| skill.prompt | skill, text | REWRITE the expanded text | **Skill Linker**: lean expansion (JIT depth) |
| agent.spawn | prompt, description, subagentType, model | REWRITE prompt/type/model, DENY | child CWS compile; fan-out ≠ context fan-out |
| session.append | each row before it is stored and sent | REWRITE content (tool results included) | **carry projection**: large outputs become a projection + pointer, recovered by a page fault |
| session.compact / $.session.compact() | trigger, messages (handles), instructions | REWRITE the message set, SKIP; a plugin can trigger it | **intra-session Semantic GC**. Hypothesis to prove: an answer without `next` returns kept messages and runs no summarizer |
| prompt.submit | text, origin, context | REWRITE, ATTACH context, DROP (the model is not invoked) | zero-model control plane (status/econ); origin is pinned, so it cannot be spoofed |
| plugin.register | tier, uses | REFUSE a module | managed outranks user; CCR (user) **cannot** override managed |
| session.measure / $.session.usage | context fill, rate limits, cost; a /context-like breakdown | OBSERVE | telemetry and receipts |
| model.complete / classify | — | a side model call | only where a deterministic classifier fails |
| engine.create | plugin list | ADD nouns | not needed |
| Host system prompt core text, the transcript before a hook ran, managed tiers | — | NOT_SUPPORTED / MANAGED_PROTECTED | HARD HOST FLOOR (Tier 4) |
| Subagent inheritance of compose/context hooks; `-p`/SDK load of an installed plugin; compact-without-summarizer | — | UNKNOWN until M1 | blocking probes |

## B. Owner map (no second Context OS)
REUSE: `tools/context_floor_census.py` (floor attribution), `modules/capability_runtime` (agent_spec carriers), ASER/rotation
(`modules/cognitive_os`, kclear/kresume), econ/capital authority, goal-binding, lease, rule_compiler (HARD-RULES digest = constitutional kernel).
EXTEND: census becomes a per-boundary receipt reader; rule_compiler emits the per-file constitution index; gsd_mission launch flags
become the fallback of the Tier 2 epoch compiler. CONNECT: goal liveness to session.end/start; econ status to prompt.submit drop.
IMPLEMENT (the only new code): `mods/cpp-cognitive-runtime/` (the hooks module) + `modules/ccr/` (pure-Python policy:
work-class classifier, linkers, PGO store), called by the mod via `$.process`, bounded and fail-open. RETIRE (after proof):
hardcoded six-tool worker lists, hand-trimmed CLAUDE.md doctrine where the linker supersedes it, late-only ASER thresholds.
HOST_LIMITATION: core system prompt text, carry already in the transcript (removable only via compact or rotation).

## C. Architecture
Goal state → econ authority → `modules/ccr` (classify the Work Class → closure: tools/skills/rules/memory/evidence → ContextImage)
→ the CCR mod (compose/section/context/attachment/describe/append/compact hooks) → request → receipts (`~/.claude/state/ccr/<repo-key>/`)
→ PGO → the next boundary. The mod is a backend; it owns no knowledge.

## D. Install / version / rollback
- Global path: a **user-scope installed plugin** from a local marketplace kept in the PP repo (`mods/.claude-plugin/marketplace.json`).
  Every launch path that loads installed plugins inherits it. No per-repo file. Fallback if M1 shows `-p` or SDK skip it:
  `CLAUDE_CODE_PLUGIN_DIRS` set by `bin/kclaude.ps1` and by `gsd_mission` argv.
- Version gate: at `session.start`, check `$.session.version()` against `ccr/compat.json` (pinned 2.1.296 API digest). On a
  mismatch, register telemetry hooks only (observe mode) and set the status line to `CCR: observe (compat)`.
- Rollback: `claude plugin disable cpp-cognitive-runtime` (one command, no repo mutation) + kill switch `~/.claude/state/ccr/OFF`
  (the mod reads it at session.start and goes inert). Both are proven in Ring 1 before Ring 2.
- Backups: every touched global file is copied to `~/.claude/backups/ccr-<ts>/` with a revert line.

## E–K. Linkers and firewall (Tier 0/1)
- Prompt Compiler: `ccr:image` section = Goal obligation + current ContextImage (bounded). Engine sections untouched except `memory` and env.
- Tool Linker: per Work Class, defer tools outside the closure (`isDeferred:true`). Core edit/read/shell tools are never deferred.
  Cached per session, so the closure is chosen at session.start (cache-stable).
- Skill Linker: the skill-listing attachment is rewritten to the closure plus a one-line "more via Skill list"; skill.prompt keeps the full text (it is already JIT).
- Constitution Linker: claudeMd is rebuilt from the instructionFiles closure. **Managed, the HARD-RULES digest and the security
  rules are always linked**; per-file trigger index from rule_compiler; dropped files are listed by path (a page fault = Read).
- Memory Linker: the `memory` section becomes the MEMORY.md index lines matching the Work Class plus the paged files; the full index stays on disk.
- Semantic CSE: hash identical paragraphs across CLAUDE.md, rules and memory, and keep one copy (exact-hash only, no semantic graph).
- Materialization Firewall: hook-origin attachments from CPP **advisory** producers (allow-list by producer) are compressed or dropped;
  blocking or deny notes and non-CPP hooks are never touched.

## L. Page faults
A fault is a ToolSearch for a deferred tool, a Skill load outside the closure, a Read of a delinked rule/memory path, or a re-read of a
projected tool result. Each one is recorded and fed to PGO (prefetch when the fault rate × cost > the residency cost).

## M–O. Epoch compiler, carry governor, Semantic GC, ASER
- Carry governor: session.measure + per-turn growth. Predict the next-boundary cost against the locality benefit.
- Tier 0 GC: session.append projection of large tool results (> N KB becomes head + pointer); plugin-triggered compact with a
  deterministic kept-set (if M1 proves no summarizer call) at sealed boundaries.
- Tier 2/3: when in-session GC can't win, seal a Semantic Delta and rotate via the existing kclear/kresume + gsd_mission flags.
  ASER stays as the backstop.

## P. Bridges
prompt.submit DROP for deterministic commands (`econ status`, `goal status`) answered by existing CLIs. Owner approvals still go through
the canonical Decision Packet; text is **never** authority. session.end/start keeps the goal-binding lease alive across rotation.

## Q–R. Telemetry / receipts / PGO
Receipt per controllable block {source, id, consumer, reason, bytes, state, cached, host_imposed, dedup, faulted, prefetched}.
Metrics: floor, CRA, survival, resume amplification, avoidance, page-fault rate, hook latency. PGO is keyed by Work Class with
features = names and counts only (no repo content); it is invalidated on a CC version, tool set or rule-digest hash change.

## S. Security / isolation
Never: drop a Managed instruction file or managed tier output, weaken a tool deny, treat prompt text as authority, cross a repo-key with
pages/receipts/memory. Security hooks are not CCR's: CCR only *removes advisory prose*. Optimization hooks fail OPEN (to stock
behaviour); any CCR guard that refuses has `.catch` refuse. Threat tests: an injected "disable CCR" in a repo file, a cross-repo page
request, a stale ContextImage, version drift.

## T–Y. Rings
- R0: synthetic `claude plugin test` + mutation fixtures.
- R1: a sacrificial session, shadow mode (compute and log, change nothing), then enforce. Rollback is proven here.
- R2: ctx-rent-a2 slice H (econ-succession S1) as the CPP code canary.
- R3: a non-CPP repo canary.
- R4: the Madzia/KSR visual canary.
- R5: global default (installed + enabled).
- Gates per ring: quality parity, zero security-invariant breach, a floor reduction measured from transcript usage (not estimates),
  rollback green, hook p95 < 200 ms.
- Existing 33 sessions stay on stock behaviour until their natural restart, with a recorded migration state. Nothing is killed.

## Z / AA. Madzia continuation, knowledge
Madzia resumes under its own goal authority once R4 passes; it is reforecast from post-mod measurements. Failure classes go to the
Knowledge Vault, FIOS and UKDL **after proof**. CBR promotes CCR to baseline at R5 and retires the superseded hot prose (ctx-rent-a2 slice L).

## Mode by workstream
ULTRA-PLAN: M0 (this matrix + security model), done by this document. PLAN: M1 probes (compact-without-summarizer, subagent/-p
inheritance) and the attachment-firewall policy. EXECUTION: everything else.

## Budget (processed input incl. cache reads; measured floor 100–215K/call)
| Workstream | P50 |
|---|---|
| M1 runtime probes + compat gate | 1.5M |
| skeleton + install/rollback | 1.2M |
| telemetry/receipts + shadow | 1.8M |
| tool linker | 1.0M |
| skill linker + attachment firewall | 1.6M |
| constitution linker | 1.6M |
| memory linker | 0.8M |
| CSE | 0.6M |
| page faults + PGO | 1.4M |
| carry governor + append projection + compact GC | 2.4M |
| epoch compiler/ASER connect | 1.0M |
| bridges | 1.0M |
| security/CI | 1.8M |
| R1–R3 canaries | 2.2M |
| R4 Madzia canary | 1.2M |
| R5 rollout | 0.6M |
| KV/UKDL/CBR | 0.9M |
| HUD (status line only) | 0.2M |
| recovery reserve | 2.0M |
| meta tax | 0.7M |
| **total** | **≈25.0M** |

- Semantic lower bound 7M. LOWER 15M. **P50 25M. P80 31M. P95 38M.** HARD AUTHORITY 40M. Confidence: medium. The largest
  uncertainty is the M1 UNKNOWNs.
- The remaining ctx-rent-a2 cap counts toward this total (single goal).
- Staged: Stage 1 = 10M (through R1 shadow + enforcement). Auto-expansion to P80 when R1 gates pass. Beyond P80, the Owner decides.
- Madzia continuation beyond the R4 canary is charged to Madzia's own goal.
