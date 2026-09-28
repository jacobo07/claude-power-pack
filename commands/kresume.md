---
name: kresume
description: Continue from the capsule a previous session sealed with /kclear — claim it, refresh reality, pass the resume exam before any edit (P3 rollover, successor side)
allowed-tools:
  - Bash
  - PowerShell
  - Read
---

# /kresume — successor side of a context rollover

Spec: `vault/specs/interactive-context-rollover.md`. Pairs with `/kclear`, which seals the capsule.
The sequence is `/kclear` → (verdict SAFE_TO_FORGET) → `/clear` → `/kresume`.

## What you do

1. **Claim and refresh.** Run (PowerShell on Windows):

   ```
   & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\rollover.py" resume
   ```

   It claims the newest sealed, unretired capsule for this directory (one successor only; a
   second claim is refused and names the holder), compares it with the tree NOW, and prints the
   bootstrap, the reality-refresh verdict and the exam.
   Exit 4 = nothing to resume. Exit 5 = another session already claimed it — stop and say so.

2. **Read the goal file** the bootstrap names. Nothing else yet.

3. **If the refresh says RECOMPILE**, the tree moved since the seal (a commit, another pane, a
   deleted goal file). Re-derive the next step from the goal file and `git log`, not from the
   capsule's obligation list.

4. **Answer the exam** from what you just read, then certify:

   ```
   ... rollover.py certify --from <session> --answers '{"goal":"<file name>","branch":"<b>","head":"<7 chars>","next":"<first obligation>"}'
   ```

   RESUME_CERTIFIED retires the capsule. RESUME_FAILED lists what disagreed — re-read and retry.
   **No file edit, commit or other mutation before RESUME_CERTIFIED.**

5. **Continue** with the first open obligation. Do not ask the Owner to paste a plan path.
