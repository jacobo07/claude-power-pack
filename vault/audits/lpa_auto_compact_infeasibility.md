# BL-0056 — LPA Auto-Compact daemon: feasibility analysis

**Verdict:** Cannot deliver "true hands-off auto-`/compact`" via external PowerShell SendKeys daemon as MC-SYS-102 originally described. Architecture blockers below. Honest alternatives proposed.

---

## Why the proposed approach (PS + System.Windows.Forms.SendKeys) does not work

### Blocker 1 — `/compact` is a CHAT slash command, not a terminal command

Cursor's `/compact` runs through the **chat input pane** (where the user types prompts to Claude), NOT through any of the 5 terminal panes. The model's emission of `/compact focus on X` appears as ASSISTANT message text in chat history — Cursor does NOT auto-fill the user input box from assistant output.

For SendKeys to trigger `/compact`, it would need to:
1. **Detect** the assistant emitted the `/compact ...` line — requires either a Cursor extension (read chat history programmatically) or screen-scrape OCR.
2. **Type** the full string `/compact focus on <task>` into the chat input box (NOT just press Enter — the chat input is empty until typed).
3. **Press Enter** to submit.

A bare `SendKeys::Send("{ENTER}")` to whatever has focus does nothing useful — Enter on terminal pane runs `\n`, Enter on already-empty chat input is a no-op.

### Blocker 2 — Focus targeting is racy across 5 active terminals

Per memory `reference_cursor_state_vscdb` Owner runs 5 concurrent Cursor terminal slots. SendKeys hits whichever window has focus. If Owner is typing in another pane when watchdog fires, the daemon would fire keys into the wrong pane — destructive.

### Blocker 3 — xterm.js renderer state is not exposed

Per memory `reference_cursor_state_vscdb`: scroll position + input buffer live in xterm.js renderer state, NOT in `state.vscdb` (Cursor's SQLite). A daemon polling `state.vscdb` for chat input population would read stale/empty data. Reading the actual chat needs a Cursor extension hook (Cursor extension API), not external PowerShell.

---

## What CAN actually be delivered

### Option A — Filesystem-anchor daemon (proof-of-concept, no SendKeys)

A PowerShell script that watches `<cwd>/vault/progress.md` for tier-2 advisory entries (line containing `used: **70%**` or higher). When detected, drop a flag file `<cwd>/.compact-pending.flag` containing the suggested focus phrase. Owner sees the flag in any file explorer / has a desktop notification, knows compact is pending. STILL requires manual Enter — but the flag makes the trigger visible without scrolling chat.

This is REAL but does not deliver hands-off. It just makes the trigger more visible.

### Option B — Cursor extension (the only honest hands-off path)

Write a Cursor extension that:
1. Subscribes to chat-message events
2. Regex-matches `/compact focus on .+$` on assistant messages
3. Calls Cursor's `chat.submit` API directly to fire `/compact focus on <task>`
4. Drops audit row to `vault/progress.md`

This is feasible but requires Cursor Extension API access + npm package + Cursor restart to install. Out of single-conversation scope.

### Option C — Accept the ceiling

What's already shipped (MC-SYS-93) is the practical ceiling without Cursor-side integration. Math: 30h continuous session at ~3h between context-fill events = ~10 Enters. Not zero, but small. Owner Enter-cost ≈ 10s over 30h = 0.01% time overhead.

---

## Recommendation

**Go with Option C for now.** The cost (10 Enters in 30h) is small, and Options A/B are not single-PR efforts.

If Owner insists on Option B, the right next step is a separate Cursor extension repo, not a PowerShell hack. Cursor extension dev is a multi-session task with its own dependencies (TypeScript, Cursor APIs, install/sideload flow).

If Owner insists on Option A, I can ship a 30-line PowerShell file watcher that drops `.compact-pending.flag`, but this is BL-0049 #1 fiction-equivalent — labelling "auto-compact" when it's just "compact-trigger-visible". I will not ship that under the auto-compact label.

---

## What this seals

- BL-0056 = honest architectural analysis of LPA infeasibility
- BL-0049 #1 (self-mod guard) re-validated: even with permission rules, the harness cannot fire slash commands. External daemon hits a Cursor architecture wall, not a permission wall.
- MC-SYS-93 (model emits ready-to-Enter line) is the pragmatic ceiling.
