# Root Cause Taxonomy -- Systematic Claude Code Errors

Sealed 2026-06-03 (BL-PREMISE-001 + BL-SPEC-GATE-001). Derived from the
NEVER_AGAIN log (19 recurring entries) + the SCS lessons, **ranked by
actual recurrence**, not by assumption. Each class names its causal
mechanism and its structural fix in the PP stack.

> Written as a standalone file (not appended to `ukdl-universal.md`)
> because that file was under active multi-pane edit at seal time. A
> 1-line pointer can be added to the UKDL index when contention clears.

| Class | Mechanism | Structural fix |
|---|---|---|
| **CLASE 0** -- module built but not auto-activated cross-repo | unit V-gate passes in isolation; nothing calls the module on a real event | SCS C27 + an *activation* gate (a verify_spp row / hook / decorator that fires the module and observes its effect). **The single most-recurring PP error** (NEVER_AGAIN #1: "PP modules importable but no auto-activation cross-repo"). |
| **CLASE 1** -- plan assumes an API that does not exist | agent writes code against a function/signature without reading the source | SCS C28 (read source before code) + `modules.error_prevention.assert_premises` (verify_function_exists returns the REAL public API as the correction) + HR-PREMISE-001 |
| **CLASE 2** -- plan assumes repo state not verified | a "remaining gap" or "file at path X" treated as fact, not hypothesis | SCS C29 (inventory is a hypothesis) + `verify_file_exists` + HR-CONTEXT-001 |
| **CLASE 3** -- CLAUDE.md / config grows unbounded | every session appends without a router/firewall | CLAUDE.md Router + firewall (separate pane / Owner-side; out of scope of this seal) |
| **CLASE 4** -- tool call fails silently (sentinel) | `[Tool result missing due to internal error]` -> dead screen | T-TOOL-SENTINEL-RECOVERY-001 + Anti-Waiting (G): name the dropped frame, re-issue solo with a different tool family, never close with "Waiting..." |
| **CLASE 5** -- output does not satisfy the implicit contract | "DONE" declared without empirical verification | Output Contracts OQS >= 70 + Reality Contract (kernel vMAX-NULL-ERROR) + HR-OUTPUT-002 |

## META-FIX

The **Spec Gate** (BL-SPEC-GATE-001) for L/XL tasks + the **Premise
Verifier** (BL-PREMISE-001) together pre-empt CLASE 1, 2, and 5 in
cascade: the spec forces reading the source (CLASE 1), verifying repo
state (CLASE 2), and defines the done-gate (CLASE 5).

CLASE 0 is closed by wiring every new module with an activation gate,
never a bare library -- which is exactly why `premise_verifier` ships as
**Tool + HR + verify_spp row**, not as a module the agent must remember
to call. A premise verifier shipped as an orphan would itself be an
instance of the #1 error it exists to prevent.

## Recognizer

If a build adds an importable module with **zero references** in
settings.json / commands / agents / signals / a verify_spp row, it is a
**CLASE 0 orphan** -- wire it the same cycle or do not ship it.

Cross-ref: SCS C27 (Integration-Wiring-by-default), C28 (read source
before code), C29 (inventory is a hypothesis), C30 (extend the
chokepoint), C31 (Spec-Driven-for-L/XL + premise-verification).
