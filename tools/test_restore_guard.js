"use strict";
// V-gates for the PP Sessions cold-start guarded restorer (SCS C50 Option C).
// Pure node, no vscode. Run: node tools/test_restore_guard.js -> RG_PASS=N/N
const path = require("path");
const { norm, panesToRestore } = require(
  path.join(__dirname, "..", "extension", "src", "restore_guard")
);

let pass = 0, fail = 0;
function check(gate, cond, ev) {
  if (cond) { pass++; console.log("OK   " + gate + ": " + ev); }
  else { fail++; console.log("FAIL " + gate + ": " + ev); }
}

const CWD = "C:\\Users\\User\\Desktop\\Cursor Projects\\GEO-audit";
const map = { panes: [
  { repo: "GEO-audit", cwd: CWD, sessionId: "sidA", live: true, resumeCmd: "claude --resume sidA" },
  { repo: "GEO-audit", cwd: CWD, sessionId: "sidB", live: true, resumeCmd: "claude --resume sidB" },
  { repo: "GEO-audit", cwd: CWD, sessionId: "sidA", live: true, resumeCmd: "claude --resume sidA" }, // dup sid
  { repo: "GEO-audit", cwd: CWD, sessionId: "sidC", live: false, resumeCmd: "claude --resume sidC" }, // closed
  { repo: "Other", cwd: "C:\\x\\Other", sessionId: "sidD", live: true, resumeCmd: "claude --resume sidD" },
]};
const sids = (r) => r.map((x) => x.sessionId).sort();

// V-RG-COLDSTART: 0 terminals -> live + cwd-matched + deduped sessions.
const cold = panesToRestore(map, [CWD], 0, { enabled: true });
check("V-RG-COLDSTART", JSON.stringify(sids(cold)) === JSON.stringify(["sidA", "sidB"]),
  "cold start -> " + JSON.stringify(sids(cold)));

// V-RG-RELOAD-GUARD: any live terminal -> restore NOTHING (no duplicate panes).
check("V-RG-RELOAD-GUARD", panesToRestore(map, [CWD], 2, { enabled: true }).length === 0,
  "liveTerminalCount=2 -> [] (reload, persistent sessions own it)");

// V-RG-DEDUPE: sidA appears twice in the map, launched once.
check("V-RG-DEDUPE", cold.filter((p) => p.sessionId === "sidA").length === 1,
  "duplicate sidA collapsed to one launch");

// V-RG-NONLIVE-EXCLUDED: a closed (live:false) pane is never auto-restored.
check("V-RG-NONLIVE-EXCLUDED", !cold.some((p) => p.sessionId === "sidC"),
  "live:false pane excluded");

// V-RG-CWD-FILTER: another repo's pane never leaks into this window.
check("V-RG-CWD-FILTER", !cold.some((p) => p.sessionId === "sidD"),
  "Other-repo pane excluded from GEO-audit window");

// V-RG-NO-WORKSPACE: no workspace folder -> nothing.
check("V-RG-NO-WORKSPACE", panesToRestore(map, [], 0, { enabled: true }).length === 0,
  "no workspace folder -> []");

// V-RG-DISABLED: opt-out returns nothing even on a cold start.
check("V-RG-DISABLED", panesToRestore(map, [CWD], 0, { enabled: false }).length === 0,
  "autoRestoreOnColdStart=false -> []");

// V-RG-NORM: forward-slash + trailing-slash + case all match one folder.
check("V-RG-NORM",
  norm("C:/Users/User/Desktop/Cursor Projects/GEO-audit/") ===
  norm("C:\\Users\\User\\Desktop\\Cursor Projects\\GEO-audit"),
  "path normalization equates slash/case/trailing variants");

// V-RG-NORM-MATCH: a slash/case-variant workspace cwd still matches the map.
const variant = panesToRestore(
  map, ["c:/users/user/desktop/cursor projects/geo-audit"], 0, { enabled: true });
check("V-RG-NORM-MATCH", JSON.stringify(sids(variant)) === JSON.stringify(["sidA", "sidB"]),
  "lowercase/forward-slash workspace cwd matches map");

// V-RG-RESUMECMD-FALLBACK: a pane with no resumeCmd gets a synthesized one.
const noCmd = panesToRestore(
  { panes: [{ repo: "R", cwd: CWD, sessionId: "sidZ", live: true }] },
  [CWD], 0, { enabled: true });
check("V-RG-RESUMECMD-FALLBACK",
  noCmd.length === 1 && noCmd[0].resumeCmd === "kclaude --resume sidZ",
  "missing resumeCmd -> 'kclaude --resume sidZ'");

const total = pass + fail;
console.log("RG_PASS=" + pass + "/" + total + "  threshold=" + total + "/" + total);
process.exit(fail === 0 ? 0 : 1);
