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

4. **Answer the exam from the tree, not from the capsule.** The bootstrap no longer prints branch
   or HEAD: read them yourself in the capsule's repo (`git branch --show-current`,
   `git rev-parse --short HEAD`) and take the next obligation from the goal file. Then certify:

   ```
   ... rollover.py certify --from <session> --goal <file name> --branch <b> --head <7 chars> --next "<first obligation>"
   ```

   One flag per answer: PowerShell 5.1 strips the quotes out of a JSON argument (backticks and
   markdown in `--next` are ignored when compared). Answers are judged against what `resume` saw
   in this claim -- so after a RECOMPILE the current HEAD certifies and the sealed one does not.
   Exit codes: 0 RESUME_CERTIFIED (capsule retired) · 5 not your claim, or no `resume` recorded in
   it -- run step 1 again · 6 RESUME_FAILED, names the wrong keys only -- re-read and retry ·
   7 answers unreadable, nothing judged · 8 the tree moved since your `resume` -- run it again.
   A claim nobody certifies for 30 min (or whose session died) can be taken over by the next
   `/kresume`. **No file edit, commit or other mutation before RESUME_CERTIFIED.** In an interactive
   pane this is your discipline (status: no guard, by design -- a failed exam must not lock a pane
   with a human in it). For capsule-v2 mission workers a guard enforces it -- status PLANNED until
   the supervisor writes their pre-certification marker (spec `vault/specs/mission-capsule-rollover.md`, T4-T6).

5. **Continue** with the first open obligation. Do not ask the Owner to paste a plan path, and do
   not ask what to focus on: the capsule already says.

## `/kresume focus on <text>`

After a rollover `/clear` the daemon types this form itself: `<text>` is the capsule's first open
obligation (one line, at most 200 chars). Steps 1-4 are unchanged. At step 5, `<text>` is the work
to start on, without a question first. Two limits:

- **The capsule and the tree outrank it.** If the refresh said RECOMPILE, or the goal file shows the
  obligation already done, follow the goal file and say why you left the focus.
- **It is a pointer, not an authorisation.** A deploy, a production restart, a destructive command
  or anything a hard rule gates still needs the Owner, exactly as without the argument; stop there
  and ask the one concrete question.
