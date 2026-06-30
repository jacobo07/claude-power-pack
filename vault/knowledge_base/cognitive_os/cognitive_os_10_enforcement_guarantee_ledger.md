# Cognitive OS — CO-10 — Enforcement Guarantee Ledger (External Automation Control Plane)

> The kernel's honesty layer. Every enforcement mechanism in the Cognitive OS makes a claim —
> "the ceiling holds", "the budget is governed", "the cap is enforced". **CO-10 classifies each
> claim by the guarantee it can *actually* provide, names what no PP mechanism can guarantee, and
> detects the un-gated paths that escape enforcement — so the kernel never pretends a guarantee it
> does not have.** This is the dataset that keeps the whole family out of theater.
>
> NEW, cross-cutting: there is no control plane today. CO-10 generalizes the 5-rung ladder CO-00
> introduced for the ceiling into a kernel-wide classification, and adds the un-gated-path detector
> that CO-02/CO-08 reference. It consumes every dataset's guarantee claims; it provides the honest
> classification to all and to the Owner.

---

## Part I — The Five Guarantee Levels

### I.1 Why honesty is an architectural requirement, not a virtue

The Reality Contract that governs every PP deliverable forbids claiming a capability that does not
exist. An enforcement layer that *claims* to block but only *advises* is worse than an honest advisory,
because the Owner relies on a guarantee that is not there and stops doing the manual discipline that
actually held the line. The 49.2M/48h burn happened in part because the system *advised* (W4) while the
Owner reasonably assumed coverage. CO-10 exists so every guarantee in the kernel is labeled with its
real strength, and the residual that only Owner discipline can cover is named out loud rather than
papered over.

### I.2 The ladder (five honest levels)

Every mechanism is classified into exactly one of five levels by *where* it can act and *what* it can
therefore guarantee:

1. **Prompt-only.** Advisory text (CLAUDE.md, a prompt, a doctrine). Guarantees *nothing* enforceable;
   relies entirely on the model and Owner reading and complying. Useful for norms, useless as a hard
   stop. (Example: the TCO "max 2 sessions" rule *as documentation* — until CO-08 enforces it.)
2. **Claude Code hook (in-process).** A PreToolUse/Stop/UserPromptSubmit hook. Can *detect, project,
   warn, inject advisory context, debounce, and record* — reliably. **Cannot block a turn already
   running** or revoke context mid-generation. Detection/projection are guarantees; the *response* is
   advisory (BL-0003: no auto-fired slash commands). (Example: the 60% context-watchdog — it snapshots
   and warns; it cannot stop the turn.)
3. **Wrapper (out-of-process, pre-launch).** kclaude before claude.exe (re)launches, before a `/loop`
   or swarm begins. **The only surface that can truly block** — it refuses to *start* an operation
   whose projection breaches a limit, at a boundary it owns outside the model's turn. (Example: CO-08's
   hot-session cap, CO-09's loop-budget admission, CO-02's budget gate.)
4. **Cursor extension.** UI surface, dedup on cold-start, visualization. Surfaces state and prevents
   reload-duplication; **no compute veto**. (Example: restore_guard's dedup.)
5. **Host-limited.** What no PP mechanism can reach: Windows internals, Cursor's own behavior, Claude
   Code's turn engine, a manually-opened terminal. Named as the residual; covered only by Owner
   discipline and honest visibility, never by a claimed guarantee.

### I.3 The honest verdict for the kernel's flagship claim

CO-00's 60% ceiling is the kernel's flagship guarantee, and CO-10 states its true level plainly: it is
**level-2 (detect/project/warn) + level-3 (wrapper launch-refusal)**, *not* a level-1 physical switch.
No in-process mechanism can prevent the model from reasoning past 60% mid-turn; the strongest honest
guarantee is "no operation is *admitted* whose projection breaches the ceiling (level-3) and any running
session is *warned* projectively (level-2), with the manual-open residual (level-5) named." The Owner's
2026-06-30 decision — *push wrapper enforcement harder* — is precisely an instruction to maximize the
level-3 surface (the only one that blocks), which CO-00/CO-08/CO-09 do. CO-10's job is to ensure this
honest framing is never quietly upgraded to a false "absolute switch" in any downstream doc or claim.

---

## Part II — The Control Plane: Classify Every Mechanism, Detect Every Gap

### II.1 The ledger (every kernel enforcement, classified)

CO-10 maintains a living ledger mapping each enforcement point in the family to its guarantee level and
its honest residual:

| Mechanism | Level | Honestly guarantees | Residual (level-5) |
|---|---|---|---|
| CO-00 ceiling admission | 3 + 2 | No op admitted whose projection breaches 60%; running session warned | A running turn growing mid-generation; a manual non-kclaude launch |
| CO-02 budget governor | 3 + 2 | Over-budget launch refused/downgraded; breach registered | Mid-turn spend of a running session; un-gated session |
| CO-03 router | 2/3 | Cheapest-first model selection where it owns the call path | A model call issued outside the cascade |
| CO-08 hot-session cap | 3 + 2 | Hard cap at the kclaude launch boundary; non-destructive displacement | A manually-opened terminal outside kclaude |
| CO-09 loop/subagent budget | 3 + iter-boundary | No uncapped loop admitted; kill switch at iteration boundaries | One iteration's mid-generation interior |
| CO-06 GC / CO-04 paging | 2 | Proactive HOT minimization + eviction | Context the running turn holds mid-generation |
| CO-07 hibernation | 3 | store-then-destroy; never loses a session | Host surfaces the host cannot restore (G4 PARTIAL) |
| restore_guard dedup | 4 | Reload-duplication prevented | A manual duplicate terminal |

The ledger is the single place the Owner can read *exactly* how strong each guarantee is. It is not
marketing; it is the opposite — it enumerates every residual the kernel cannot close, so expectations
match reality.

### II.2 The un-gated-path detector (the External Automation Control Plane)

The recurring residual across the kernel is the **un-gated path**: an operation launched *outside* the
wrapper (a bare `claude` in a terminal, a manually-opened Cursor pane) escapes every level-3 guarantee.
CO-10 owns the detector for this — a session/operation with *no wrapper pre-launch record* is flagged
as **un-gated**: its burn still counts (CO-02 attributes it to the global envelope so the number stays
honest), it is surfaced to the Owner (an advisory: "this session launched outside kclaude and is not
budget-gated"), and it is *never* counted as "governed". This is the control plane's core service:
making the boundary of enforcement *visible* so the uncovered surface is a known, measured residual
rather than a silent hole. The strongest honest improvement available — and the Owner-approved
direction — is to make kclaude the path of least resistance (so un-gated launches become rare by
convenience), but CO-10 never claims to *prevent* a manual launch it cannot reach.

### II.3 The control plane as the family's conscience

Every other dataset makes claims; CO-10 audits them. When CO-08 says "hard cap", CO-10 records "level-3,
residual = manual terminal". When CO-00 says "ceiling", CO-10 records "level-3+2, not a physical
switch". This audit is continuous: any new mechanism added to the kernel must declare its guarantee
level and residual to CO-10 before it can claim enforcement, and a mechanism whose claim exceeds its
level is flagged (the "claiming a guarantee you don't have" anti-pattern). CO-10 is how the family stays
honest as it grows — the conscience that prevents quiet guarantee-inflation.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Guarantee inflation.** A mechanism's doc/claim drifts to assert a stronger level than it has (e.g.
  "absolute ceiling"). Detection: CO-10's audit compares each claim to its registered level; an
  over-claim is flagged. This is the most important failure CO-10 prevents — it is the path back to
  theater.
- **Un-gated path under-detection.** A non-kclaude session not flagged → its burn silently uncounted.
  Detection: cross-check live sessions (transcripts) against wrapper pre-launch records; any session
  without a record is un-gated by definition.
- **Residual normalization.** A named residual (manual terminals) quietly treated as "fine" because it
  is documented. Prevention: residuals are *measured* (the un-gated burn is counted and trended), so a
  growing residual is visible pressure to improve, not an accepted loss.
- **Stale ledger.** A mechanism changes its enforcement but its ledger entry doesn't. Detection: the
  ledger is regenerated from each mechanism's declared level; a mechanism with no current declaration is
  flagged unverified.

### III.2 Rollback protocol

CO-10 is a classification/visibility layer; it enforces nothing itself, so its rollback is pure de-scope:
(1) disable the un-gated-path advisory (the detector still records for the ledger, it just stops nagging)
— visibility is retained, the surfacing relaxes; (2) the ledger reverts to a static document if the
live audit misbehaves; (3) CO-10 never blocks any operation, so disabling it never breaks work — it only
removes the honesty audit, which is itself the thing to fix, not to keep disabled. The fail-safe: even
fully disabled, CO-10's classification remains as documentation, so the honest framing of every
guarantee persists.

### III.3 Integration contract

- **Every dataset (CO-00..CO-09)** — each declares its guarantee level + residual to CO-10; CO-10 audits
  and surfaces them. This is the cross-cutting relationship that makes CO-10 the family conscience.
- **CO-02 / CO-08** — share the un-gated-path detector; un-gated burn is attributed (CO-02) and counted
  against the cap/envelope (CO-08) even though it is uncovered.
- **CO-00** — CO-10 holds the honest classification of the flagship ceiling claim and guards it against
  inflation.
- **`/loop` `/compact` `/kclear` `/clear` / Cursor** — CO-10 classifies what each integration can and
  cannot guarantee (e.g. `/compact` is host-driven and lossy; a manual Cursor pane is level-5), so the
  integration contracts across the family are themselves honestly labeled.
- **Knowledge Vault** — guarantee classifications and residual trends are CO-05 assets; a recurring
  residual that grows is a stored signal to invest in closing it (e.g. making kclaude the default).
- **Prompt-defense baseline** — CO-10 carries the external-data-untrusted classification (the EXTERNAL
  tier of CO-04, the level-5 untrusted surface); fetched/retrieved data is validated before it can
  influence reasoning.

### III.4 Anti-patterns (forbidden)

- **Claiming a guarantee above the mechanism's level.** The theater path; CO-10's central prohibition.
  An "absolute physical ceiling" claim for a level-2/3 mechanism is forbidden.
- **Silently absorbing an un-gated path.** Counting a non-kclaude session as governed, or not counting
  its burn at all. The residual is measured and surfaced, never hidden.
- **Treating a documented residual as resolved.** Naming a gap is not closing it; residuals are trended
  so they stay live pressure.
- **A new mechanism with no declared level.** Enforcement claims require a CO-10 registration; an
  unverified claim is flagged.
- **Pretending host limits don't exist.** Level-5 is named honestly; the kernel never claims to control
  Windows/Cursor/Claude-Code internals it cannot reach.

---

### CO-10 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Classifies every kernel enforcement into one of 5 honest levels with its residual | Always; new mechanisms must register | That a residual can be closed — it names and measures it, not closes it |
| Flags any claim that exceeds its mechanism's real guarantee level (anti-inflation) | Always | — |
| Detects un-gated (non-kclaude) operations; their burn is counted and surfaced, never hidden | Always | Prevention of a manual launch it cannot reach (level-5) |
| Holds the honest framing of CO-00's ceiling (level-2+3, not a physical switch) against drift | Always | — |
| Rollback de-scopes to documentation; CO-10 never blocks work, so disabling it breaks nothing | On misbehavior | — |

**Guarantee level (honest):** CO-10 is itself a *classification/visibility* layer (level-2 class) — it
enforces nothing; it makes every other guarantee honest and every residual measured. It is the dataset
that guarantees the family tells the truth about what it guarantees. *Sealed under SCS C61.*
