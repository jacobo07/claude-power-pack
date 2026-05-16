# Lazarus Shadow-Folder Engine — Operations Manual

**Status:** built + forensically verified, **NOT auto-deployed**.
**File:** `lib/lazarus/shadow_engine.js`
**Sandbox:** `tools/shadow_sandbox_test.py` (28/28 byte-exact assertions)
**Panic recovery:** `tools/lazarus-panic-restore.ps1`

## What it does

Hides the `.jsonl` transcripts of OTHER currently-alive Claude Code sessions from `~/.claude/projects/<project-id>/` by renaming them with a `.live-shadow-<ownerSid>` suffix the native `/resume` picker won't list. The other sessions keep writing through their already-open file handles (Claude Code uses `FILE_SHARE_DELETE` on Windows; rename does not invalidate descriptors). On exit / restore, we rename them back. **Net effect: native `/resume` shows only sessions that are not currently running in any window.**

## Why it isn't on by default

- Risk asymmetry: small UX win vs. potential to corrupt live transcripts.
- Forensic harness proved byte-exactness for the synthetic case (2 writers, 2-second sustained rename, 37 lines / 2433 bytes preserved per writer with monotonic seq, no gaps, no conflict files). That's strong evidence but not a license to mass-deploy without the Owner's explicit go-ahead per session.
- Locked behind `LAZARUS_SHADOW_FOLDER=1` env var. The CLI refuses to mutate state otherwise (exit 2).

## How to enable for ONE session (recommended path)

1. Stop using that terminal for active production work.
2. In the terminal you want to test in, set the env var:
   ```cmd
   set LAZARUS_SHADOW_FOLDER=1
   ```
   (PowerShell: `$env:LAZARUS_SHADOW_FOLDER="1"`)
3. Open `claude` in that terminal as usual.
4. Before typing `/resume`, manually invoke the engine to hide other live sessions:
   ```bash
   node ~/.claude/skills/claude-power-pack/lib/lazarus/shadow_engine.js shadow \
       --project-id <sanitized-cwd> --owner-sid <this-session-id>
   ```
   You'll get JSON output listing what was shadowed.
5. Type `/resume`. The picker will only see non-shadowed `.jsonl` files.
6. After `/resume` (whether you picked something or cancelled), restore:
   ```bash
   node ~/.claude/skills/claude-power-pack/lib/lazarus/shadow_engine.js restore \
       --project-id <sanitized-cwd> --owner-sid <this-session-id>
   ```
7. Observe the live sessions in other tabs for 5+ minutes. If they all kept writing correctly (check `~/.claude/projects/<pid>/<sid>.jsonl` line counts), the engine is safe in your environment.

## Auto-wiring path (NOT YET LANDED — requires Owner approval)

To make the engine fire continuously from the heartbeat hook:

```js
// In ~/.claude/hooks/lazarus-heartbeat.js, inside run() — after the
// pulse write but before the mirror block:
if (process.env.LAZARUS_SHADOW_FOLDER === '1') {
  try {
    const { shadow } = require(path.join(
      os.homedir(),
      '.claude/skills/claude-power-pack/lib/lazarus/shadow_engine.js',
    ));
    shadow({ projectId, ownerSid: sessionId });
  } catch { /* silent — shadow is best-effort */ }
}

// And in ~/.claude/hooks/lazarus-snapshot.js Stop hook:
if (process.env.LAZARUS_SHADOW_FOLDER === '1') {
  try {
    const { restore } = require(...);
    restore({ projectId, ownerSid: sessionId });
  } catch {}
}
```

After patching: only sessions started with `LAZARUS_SHADOW_FOLDER=1` in their env will participate. Sessions without the env var continue to behave normally.

## Panic recovery

If something dies leaving `.jsonl.live-shadow-*` files orphaned:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
    -File ~/.claude/skills/claude-power-pack/tools/lazarus-panic-restore.ps1
```

Add `-DryRun` to preview without mutating. Add `-ProjectId <pid>` to scope to one project.

The panic-restore script bypasses the `LAZARUS_SHADOW_FOLDER` kill-switch on purpose — it must work even when the engine itself is disabled.

## Conflict handling

If two sessions A and B both try to restore the same `<sid>.jsonl` simultaneously (race condition), the loser parks its shadow under `<sid>.jsonl.conflict.<iso-ts>` instead of overwriting. Manual reconciliation is then a `cat` and a rename. Forensic harness verified no conflicts under sustained 2-second rename window with 2 concurrent writers.

## What this can't do

- **Cannot intercept the moment `/resume` is invoked.** There is no pre-resume hook in Claude Code today. The shadow has to be active *continuously* for the picker to ever see a filtered list. That's why the auto-wiring runs from the PreToolUse hook every 30 seconds.
- **Cannot help on macOS/Linux without re-testing.** The byte-exactness proof is Windows-specific (NTFS + Node `createWriteStream` + `FILE_SHARE_DELETE`). Same code on POSIX should work because rename-while-open is well-defined there too, but the sandbox should be re-run on the target platform before deploying.

## Companion

For users who don't want to deploy the engine: `/lazarus fresh` lists the same filtered set of sessions as a text view. No filesystem mutation, no risk to live work, just a different UX from the native picker.
