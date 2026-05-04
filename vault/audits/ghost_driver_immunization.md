# BL-0058 — Ghost-Input Driver: doctrine immunization

**Status:** ship complete (`tools/ghost_input_driver.ps1` + `tools/ghost_driver_test.py`). Acknowledged ceiling per BL-0056.

---

## What got shipped (BL-0057)

`tools/ghost_input_driver.ps1` — PowerShell daemon that polls
`vault/sleepy/context_snapshots.jsonl` for `tier=advisory` rows. On
detection: extracts cwd from row, derives task hint from that project's
`vault/progress.md` tail, fires `/compact focus on <hint>{ENTER}` via
`System.Windows.Forms.SendKeys.SendWait` to whatever window has FOREGROUND
focus.

**Two modes:**
- `-DryRun` (default): logs detections to `vault/audits/ghost_driver.log`,
  never sends keystrokes. SAFE to run anywhere.
- `-Live`: actually sends keystrokes. DANGEROUS — see brittleness below.

`tools/ghost_driver_test.py` — synthesizes a tier-2 advisory row in the
ledger so the driver pipeline can be verified WITHOUT crossing the real
70% context threshold.

---

## Confirmed Anthropic doctrine (re-verified 2026-05-04)

Subagent claude-code-guide quoted official docs at
https://code.claude.com/docs/en/hooks.md. Hook return fields are:
`additionalContext`, `permissionDecision`, `updatedInput`, `decision`,
`suppressOutput`, `continue`, `systemMessage`. **No** `executeCommand`,
`dispatch`, `slashCommand`. Changelog v2.1.84..v2.1.126 (latest 2026-05-02)
shows no new hook dispatch mechanism.

**Verdict: hooks cannot fire slash commands.** External SendKeys is the
ONLY remaining path until Anthropic ships a hook-side dispatch field.

---

## Brittleness (deliberate, documented, not fixable from this side)

1. **Focus race**: SendKeys hits whatever window has FOREGROUND. If Owner
   Alt-Tabs to a different pane between detection and the 1.5s grace
   window, keystrokes land in the wrong app. Mitigation: only run
   `-Live` when actively typing in Cursor.
2. **5-pane Cursor reality**: per memory `reference_cursor_state_vscdb`,
   Owner runs 5 concurrent Cursor terminals. Driver detects ONE advisory
   per ledger row but cannot tell which Cursor pane corresponds to which
   `cwd`. Misfire risk grows with pane count.
3. **No ack channel**: SendKeys is fire-and-forget. Cannot verify Cursor
   actually consumed the keystrokes or that `/compact` ran.
4. **Auto-spawn rejected**: NOT wired to SessionStart. Reason: 5 panes
   × 5 SessionStart fires = 5 concurrent daemons, each polling the same
   ledger, each potentially firing on the same advisory. Auto-spawn would
   amplify the focus-race problem 5×. Manual opt-in (Owner runs
   `pwsh tools/ghost_input_driver.ps1 -Live` once when starting a long
   session) is the safer design.
5. **Cursor extension is the real fix**: only a Cursor extension can
   submit `/compact` to the chat input safely. That is a separate,
   multi-session project (TypeScript + Cursor extension API), not a
   single-PR effort.

---

## Owner workflow (recommended)

For a long session where you want hands-off compact:

1. Open Cursor, start the long session in pane #1.
2. In a SEPARATE PowerShell window (NOT the Cursor pane):
   `pwsh tools/ghost_input_driver.ps1 -Live`
3. Keep Cursor pane #1 in focus while working. If you Alt-Tab away,
   accept that compact may misfire if it triggers right then.
4. Kill the daemon (Ctrl+C in its PS window) when session ends.

For testing without risk: run `-DryRun` (default) + use
`tools/ghost_driver_test.py` to inject synthetic advisories.

---

## Snowball baseline note

This does NOT establish "auto-compact" as the global Power-Pack standard.
It establishes "external SendKeys daemon with documented brittleness as
opt-in tooling for advanced users". MC-SYS-93 (model emits ready-to-Enter
line, Owner presses Enter) remains the default Power-Pack behavior because
it is robust across any Cursor configuration.

When Anthropic ships a hook dispatch field OR a Cursor extension built
on top of this driver becomes available, this doc gets superseded.
