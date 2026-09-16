/**
 * gui-app-console-inherit-guard — PreToolUse (Bash|PowerShell), block:true
 *
 * WHY THIS EXISTS
 * A desktop app launched from the agent's shell becomes a CHILD of that shell and inherits its
 * console, so everything the app writes to stdout/stderr lands in the Owner's terminal pane. On
 * 2026-09-08 that dumped Orca's `[pty] hidden-delivery gate …` diagnostic — a legitimate, already
 * rate-limited field log — straight into the Owner's working pane, mid-session. The app was fine.
 * The launch was wrong.
 *
 * `Start-Process` does NOT save you: it still parents the process to the shell. On Windows the
 * fix is to hand the launch to the shell process (`explorer.exe <path>`), which re-parents it and
 * detaches the console. Verified by measurement: after routing through explorer, the app's main
 * pid reported a parent that was already gone, not the agent's powershell pid.
 *
 * A memory already recorded this trap and it was violated anyway, which is the whole argument for
 * a mechanical gate rather than another note.
 *
 * SCOPE (deliberately narrow, to stay false-positive free)
 * Only launches of a packaged desktop build are blocked: an .exe under a packaging output dir
 * (win-unpacked / dist-ship / dist-release) or an Orca app binary. CLI tools are untouched.
 * Inspection verbs (Get-/Test-/Stop-/Copy-/Remove-Item, hashing, signature checks) are not
 * launches and are explicitly allowed.
 *
 * Input  (PreToolUse contract): { tool_name:"Bash"|"PowerShell", tool_input:{ command:"..." } }
 * Output: stdout JSON { decision:"block", reason } + exit 2 on block; else exit 0.
 * Kill switch: CLAUDE_GUI_LAUNCH_GUARD=off
 * Tests: node ~/.claude/hooks/tests/test-gui-app-console-inherit-guard.js
 */
"use strict";

const PACKAGED_EXE_RE =
  /(?:win-unpacked|dist-ship|dist-release)[\\/][^"'\s]*\.exe|["'][^"']*\borca(?:[ _-]?x)?\.exe["']/i;

// Verbs that mention an executable without starting it. Without these, every `Test-Path …\Orca X.exe`
// and every `Stop-Process` cleanup would trip the guard, and a guard that cries wolf gets disabled.
const NON_LAUNCH_VERB_RE =
  /\b(?:Test-Path|Get-Item|Get-ChildItem|Get-FileHash|Get-AuthenticodeSignature|Select-String|Copy-Item|Move-Item|Remove-Item|Stop-Process|Get-Process|Get-CimInstance|Where-Object|robocopy)\b/i;

// The launch shapes that inherit the console.
const LAUNCH_SHAPE_RE = /\bStart-Process\b|(?:^|[;&|(]\s*)&\s*["'][^"']*\.exe["']|\bcmd(?:\.exe)?\s+\/c\b/i;

function isExplorerRouted(command) {
  return /\bexplorer(?:\.exe)?\b/i.test(command);
}

function buildReason(command) {
  return [
    "GUI-APP LAUNCH WOULD INHERIT THE OWNER'S CONSOLE.",
    "",
    "This command starts a packaged desktop build as a child of the agent shell, so the app's",
    "stdout/stderr (diagnostics, warnings) will print into the Owner's terminal pane and keep",
    "printing for the life of the app. `Start-Process` does not detach it — the parent is still",
    "this shell.",
    "",
    "PIVOT — re-parent the launch through the Windows shell:",
    '  & explorer.exe "<absolute path to the .exe>"',
    "",
    "Then PROVE it detached instead of assuming:",
    "  Get-CimInstance Win32_Process -Filter \"Name='<app>.exe'\" | Select ProcessId,ParentProcessId",
    "  (the main pid's parent must not be this shell's pid)",
    "",
    "Inspecting the binary (Test-Path / Get-FileHash / Stop-Process / …) is never blocked.",
    "Kill switch: CLAUDE_GUI_LAUNCH_GUARD=off",
    "",
    `Command: ${String(command).slice(0, 300)}`,
  ].join("\n");
}

// --- Runner (pure; no process.exit, so tests can drive both branches) ------

function run(input, opts) {
  try {
    const platform = (opts && opts.platform) || process.platform;
    if (platform !== "win32") return { block: false, why: "not-windows" };
    if (String(process.env.CLAUDE_GUI_LAUNCH_GUARD || "").toLowerCase() === "off") {
      return { block: false, why: "kill-switch" };
    }
    const tool = input && input.tool_name;
    if (tool !== "Bash" && tool !== "PowerShell") return { block: false, why: "not-a-shell-tool" };

    const command = (input && input.tool_input && input.tool_input.command) || "";
    if (!command) return { block: false, why: "no-command" };
    if (!PACKAGED_EXE_RE.test(command)) return { block: false, why: "no-packaged-exe" };
    if (isExplorerRouted(command)) return { block: false, why: "explorer-routed" };
    if (!LAUNCH_SHAPE_RE.test(command)) return { block: false, why: "not-a-launch-shape" };
    if (NON_LAUNCH_VERB_RE.test(command)) return { block: false, why: "inspection-only" };

    return { block: true, why: "would-inherit-console", reason: buildReason(command) };
  } catch (error) {
    // Fail open, absolutely: a broken guard must never be able to stop the session.
    return { block: false, why: `guard-error:${error && error.message}` };
  }
}

module.exports = { run, PACKAGED_EXE_RE, LAUNCH_SHAPE_RE };

if (require.main === module) {
  let raw = "";
  const t = setTimeout(() => { process.exit(0); }, 5000);
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (c) => { raw += c; });
  process.stdin.on("end", () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(raw || "{}"); } catch { process.exit(0); }
    const r = run(data);
    if (r.block) {
      // 2026-09-15 MUTE-GATE FIX: harness reads fd 2 on exit 2. stderr FIRST,
      // or the block arrives with no reason and forces a blind retry.
      try { process.stderr.write(String(r.reason) + "\n"); } catch {}
      try { process.stdout.write(JSON.stringify({ decision: "block", reason: r.reason })); } catch {}
      process.exit(2);
    }
    process.exit(0);
  });
}
