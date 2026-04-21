# Omni-Verification Oracle (OVO) — Execution Protocol

> Canonical five-phase protocol executed by `/ovo-audit` (alias `/omni-verification-oracle-audit`). Loaded via `@modules/oracle/ovo-protocol.md` from the command body. ~200 lines. Deterministic, inline, zero sub-agents.

## What OVO is

A forensic integrity gate that reads the *delta* of this repo since the last audit, adversarially reviews it, renders the 5-advisor Council, stamps a verdict, and persists the result so that downstream gates (push/deploy hooks, baseline elevation) can trust "the oracle said yes" as a bounded claim.

OVO is **not** a re-scan of the whole codebase. It is a review of what *changed* plus the risk surface those changes opened. Running OVO on an unchanged tree is a no-op that still emits a fresh verdict — that is by design (push-gate TTL is 10 min, so a dormant repo still needs a heartbeat).

## When /ovo-audit runs

The command orchestrates these phases. Each phase has observable output the agent must produce before moving on. **No phase-skipping.**

```
A. Delta Forensics     → tools/oracle_delta.py --json
B. Adversarial Scan    → Mistakes #1-#39 checklist against delta
C. Council of 5        → tools/council_verdict.py --render (inline reasoning)
D. Verdict Stamp       → [COUNCIL_VERDICT: A+|A|B|REJECT] + record to jsonl
E. Vault & Propose     → --vault-post + baseline elevation proposal (A+ only)
```

---

## Phase A — Delta Forensics

**Goal:** know exactly what changed since the last audit, with minimum token spend.

**What the agent does:**
1. Read the JSON returned by `tools/oracle_delta.py --project . --json`. Capture the `delta_id`, `sha256_pre`, `changed[]`, `new[]`, `deleted[]`, and `council_block`.
2. For each entry in `changed[]`, read its 1-line cached `summary` first. Only raw-read a file if the summary is insufficient to judge blast radius.
3. For each entry in `new[]`, identify the **consumer**: grep for imports or references. If no consumer exists in the same session's proposed output, flag **Mistake #38 (Producer-Consumer Gap)** immediately — do not proceed to Phase B.
4. Cross-reference `semantic_dna` tags. A changed file that crossed from one tag cluster to another (e.g. `infrastructure` → `governance`) is a boundary-crossing event. Flag it.
5. If `cold_start: true`, note this in the Council context block — prior baseline does not exist, so every file is treated as "new" for the purposes of Phase B.

**Exit criterion:** a concise mental model of *what actually changed and who consumes it*. If the delta is empty, state so explicitly and continue — Phase B still runs (risk review of the current tree).

---

## Phase B — Adversarial Reasoning

**Goal:** hunt for delivery-blocking mistakes in the delta, before the Council ever sees it.

**Checklist (read against every changed/new file):**
- **Mistake #1 (Building Without Wiring):** is every new function/endpoint/event reachable from a real caller?
- **Mistake #16 (Scaffold Illusion):** does it compile *and* execute, or does it just lint clean?
- **Mistake #17 (Static ≠ Runtime):** was the change observed running, or only reasoned about?
- **Mistake #20 (Shell Escaping):** any deploy/remote command with unescaped variables?
- **Mistake #25-26 (Fragile Language / Missing LDR):** new critical-path code in a fragile language without a Language Decision Record?
- **Mistake #37 (Silent Quality Degradation):** fallback paths that degrade >10× or lose data without logging WARN and aborting?
- **Mistake #38 (Producer-Consumer Gap):** new data output (file, event, return value) with no consumer?
- **Mistake #39 (Synchronous Default Trap):** blocking I/O on an event-loop or tick thread?
- **Mistake #52 (Auditor Bug Misattributed):** any finding that cites an ad-hoc one-liner failure — re-verify via the canonical tool before promoting to a recommendation.

### Reality Contract enforcement (MC-OVO-24 — Zero-Stub + Zero-401 checks)

Reality Contract v7000+ is non-negotiable for any delta touching runtime code. Run BOTH checks and emit findings if either triggers:

**Zero-Stub check** — grep the delta for placeholder markers. ANY hit on a runtime-code file (not pure docs, not governance markdown) is a delivery blocker:
- `TODO:` / `FIXME:` / `XXX:` / `HACK:`
- `Coming Soon` / `Coming soon` / `coming-soon`
- `not implemented` / `NotImplementedError` / `raise "not implemented"`
- `pass  # stub` / `// TODO` / `/* TODO */`
- empty function bodies: `def foo(): pass\n` with no docstring AND no caller-facing contract, `function foo() {}` on exported symbols
- commented-out wiring: `# return result` / `// return result` on the happy path

Stub findings cap the verdict at **B** unless each stub has an explicit GitHub-issue reference AND an owner assignment in the same commit.

**Zero-401 check** — if the delta touches ANY of: auth handler, session middleware, API endpoint, command permission check — verify:
- No hardcoded `return 401` / `status_code=401` bypass path unconditional on the input
- No `if DEV_MODE: skip_auth()` / `if env == 'local': return 200` flags
- No commented-out auth checks (`// TODO: re-enable auth`)
- No "empty permission" defaults that resolve to allow on miss
- Every auth failure path has a corresponding logging emit at WARN+ level

401 findings are blockers regardless of verdict — a 401 in production IS a broken user promise per the Reality Contract, not a design decision. Route to Rejection Recovery.

**Provenance stamps** (appended to the Council block so downstream audits can prove the gates ran):
- `[ZERO_STUB: clean|N findings|skipped-docs-only]`
- `[ZERO_401: clean|N findings|not-applicable]`

Full registry at `./modules/governance-overlay/mistakes-registry.md`. For projects with custom visual/audio stacks (KobiiCraft, KobiiSports) also cross-check `~/.claude/knowledge_vault/gex44_antipatterns/`.

**What the agent emits:** a ≤5-bullet "adversarial findings" block. Each bullet names the mistake number, the file path, and the specific line-of-concern. Zero bullets is a valid emission *only* if the delta is genuinely clean — do not manufacture findings, but do not omit real ones.

**Exit criterion:** either no adversarial findings, or all findings are addressed *in the proposed output* (not as a follow-up). If an adversarial finding cannot be addressed in this turn, the Council verdict cannot exceed **B** — OVO blocks.

---

## Phase C — Council of 5

**Goal:** perspective-diversity review of the proposed output, with the delta + adversarial findings as context.

Render the Council block exactly per `modules/governance-overlay/council.md`:

```
[COUNCIL BLOCK]
Prior antipatterns considered: <top-3 from visual-antipatterns.md>
Recurring mistakes: <top-3 from mistake-frequency.json>

• Contrarian: <what breaks this? one failure mode OR "no contrarian objection">
• First Principles: <reuse-vs-reinvent; flag new-and-duplicated surfaces>
• Expansionist: <what unlocks next; what constraint is lifted ecosystem-wide>
• Outsider: <would a senior engineer unfamiliar with this codebase approve?>
• Executor: <ship-now vs more-work; concrete 30-second verification command>
```

Helper: `python tools/council_verdict.py --render --project claude-power-pack` prints the template with Howard's Loop pre-injected. The agent replaces each `<…>` with real reasoning. **No hedging. A position, not an analysis.**

**Breadcrumb protection:** OVO's own render writes `_audit_cache/.council_rendered_<delta_id>`. Governance-overlay `pre-output.md §13` observes the breadcrumb (mtime <60s) and skips re-rendering. One render per turn.

---

## Phase D — Verdict Stamp

**Goal:** persist a signed verdict to the append-only gate log.

Grading rubric (verbatim from `council.md`):

| Grade | Criteria |
|-------|----------|
| **A+** | All 5 advisors unconditionally approve. Zero open objections. |
| **A**  | ≤1 advisor raises a minor caveat addressed in the response. |
| **B**  | ≥2 advisors raise caveats, OR any one raises a major concern. **BLOCK.** |
| **REJECT** | Any advisor identifies a correctness bug, security hole, or scaffold illusion. **BLOCK.** |

Agent emits the banner, then runs:

```bash
python tools/oracle_delta.py --project . \
  --record-verdict <VERDICT> --delta-id <ID> --council-text "<block>"
```

The wrapper:
- Rejects writes if the Phase A breadcrumb is older than 120s (no orphan verdicts).
- Hashes the Council text into `advisor_block_hash` so downstream gates can prove the Council actually ran for this verdict.
- Appends one line to `vault/audits/verdicts.jsonl`.

**B or REJECT** → route to `modules/governance-overlay/post-output.md § Rejection Recovery`. Maximum 3 iterations per task (per `post-output.md`); after the third, HALT and register the failure in GAL.

---

## Phase E — Vault & Propose Elevation

**Goal:** freeze the post-state and, on A+, surface (not execute) a baseline elevation.

1. `python tools/oracle_delta.py --project . --vault-post` — rebuilds the source_map, freezes `snapshots/source_map_post_<ISO>.json`, patches `sha256_post` onto the last verdict record.
2. `python tools/oracle_delta.py --project . --report-md vault/audits/ovo_<ISO>_<VERDICT>.md` — writes the human-readable report.
3. **On A+ verdict only,** print the proposed elevation command:
   ```bash
   python tools/baseline_ledger.py --elevate claude-power-pack --axis k_qa --baseline <N>
   ```
   where `<N>` is the current axis value + the verdict delta negotiated with Owner. **Never auto-execute** — ledger writes are global state and require a human keystroke.

---

## Failure modes OVO must defend

- **Cold start** (`_audit_cache/source_map.json` missing): Phase A auto-builds, reports `cold_start: true`, Council weighted accordingly (no false-baseline reasoning).
- **Stale breadcrumb**: Phase D refuses to record a verdict without a <120s Phase A breadcrumb. Agent must re-run Phase A if the turn ran long.
- **Missing verdicts.jsonl**: the push-gate hook fails **closed** (blocks). Agent must run `/ovo-audit` end-to-end before retrying push.
- **Concurrent sessions**: `vault/audits/verdicts.jsonl` is the single source of truth. Any session pushing reads the same file. No in-memory state.
- **Dishonest self-grading**: will surface on the next session as Mistake #17 — grading mismatch between claim and runtime evidence.

---

## Non-goals

- OVO is **not** a full-repo re-audit. Use `python tools/audit_cache.py --build` for that (forensic-tier, ~20s).
- OVO does **not** replace the 5-gate completion cascade (tsc/lint/build/tests/scaffold). It runs *after* the cascade — a clean cascade is assumed before Phase A.
- OVO does **not** fix what it finds. It grades, records, and gates. Fixing is a separate turn, then re-run `/ovo-audit`.
- OVO's Council does **not** call external models. Deterministic inline reasoning only.
