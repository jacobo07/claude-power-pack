"use strict";
// SessionEnd graceful-beacon hook -- Workspace Recovery Control Plane (SCS C83).
//
// Writes power_beacon.write_graceful_exit on a CLEAN session close so the LAST
// word on disk is "graceful". Without it, the active beacon (written at
// SessionStart by session_start_hub.js) is never overwritten, so power_beacon
// .classify_startup reads EVERY next startup as "ungraceful-shutdown" -- even a
// normal quit. This hook is the graceful counterpart the G6 dataset (6.6/6.7)
// names; it makes the graceful-reopen vs ungraceful-shutdown distinction real.
//
// Fail-open ABSOLUTE: any error is noted to a best-effort log and swallowed --
// the session still ends. Detached fire-and-forget; consumes no stdout.
//
// Owner-side registration (HR-001: auto-mode cannot self-register ~/.claude
// hooks). Two one-time steps:
//   1) Copy-Item this file to ~/.claude/hooks/ (canonical->live mirror,
//      T-HOOK-DISPATCHER-DRIFT-001).
//   2) Add to ~/.claude/settings.json  "hooks"."SessionEnd":
//        { "hooks": [ { "type": "command",
//          "command": "node \"%USERPROFILE%\\.claude\\hooks\\session_end_graceful_beacon.js\"" } ] }
//      (or fold into the existing SessionEnd entry).
const cp = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const LOG = path.join(os.tmpdir(), "pp-graceful-beacon.log");

function note(stage, err) {
  // A fail-open swallow must still be OBSERVABLE (never a bare empty catch): one
  // best-effort diagnostic line. If even that write fails there is nothing left
  // to fall back to -- return the terminal error so the caller ends quietly.
  try {
    const msg = err && err.message ? err.message : String(err);
    fs.appendFileSync(LOG, `${new Date().toISOString()} [${stage}] ${msg}\n`);
    return null;
  } catch (terminal) {
    return terminal;
  }
}

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch (e) {
    note("stdin", e);
    return "";
  }
}

function resolvePython() {
  const cand = path.join(process.env.LOCALAPPDATA || "",
    "Programs", "Python", "Python312", "python.exe");
  try {
    if (fs.existsSync(cand)) return cand;
  } catch (e) {
    note("resolve-python", e);
  }
  return "python"; // fall back to PATH
}

(function main() {
  try {
    let sid = process.env.PP_EVT_SID || "";
    let cwd = process.env.PP_EVT_CWD || "";
    const raw = readStdin();
    if (raw) {
      try {
        const j = JSON.parse(raw);
        sid = j.session_id || j.sessionId || sid;
        cwd = j.cwd || cwd;
      } catch (e) {
        note("parse-stdin", e); // env fallback already set
      }
    }
    const ppRoot = path.join(os.homedir(), ".claude", "skills", "claude-power-pack");
    const stateDir = path.join(os.homedir(), ".claude", "state");
    // JSON.stringify safely quotes each value into the python literal.
    const code =
      "from modules.session_resilience.power_beacon import write_graceful_exit\n" +
      "write_graceful_exit(" + JSON.stringify(stateDir) + ", " +
      "session_id=(" + JSON.stringify(sid) + " or None), " +
      "cwd=(" + JSON.stringify(cwd) + " or None))\n";
    const child = cp.spawn(resolvePython(), ["-c", code], {
      cwd: ppRoot,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }),
      detached: true,
      stdio: "ignore",
      windowsHide: true,
    });
    child.on("error", (err) => note("spawn", err));
    try {
      child.unref();
    } catch (e) {
      note("unref", e);
    }
  } catch (e) {
    note("main", e); // never block session end
  }
  process.exit(0);
})();
