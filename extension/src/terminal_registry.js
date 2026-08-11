"use strict";
// Pure, vscode-free transform of a window's terminal list into the per-window
// registry written to ~/.claude/state/terminals/<key>.json.
//
// WHY THIS EXISTS: vscode.window.terminals is the ONLY authoritative list of what
// is open right now, and it is reachable only from inside an extension -- the same
// constraint that produced tab_order.js (T-TAB-ORDER-EXTENSION-ONLY-001).
// build_pane_map.ps1 infers openness from %TEMP% beacons, so a terminal that never
// wrote one cannot be counted at all. Measured 2026-08-11: CursorProjects had 6
// terminals open and 4 counted; Jacobo had 2 open and 3 counted.
//
// ONE FILE PER WINDOW: every Cursor window runs its own extension host, so a single
// shared path would be clobbered by whichever host wrote last and four windows would
// report as one. The workspace folder path is the key and joins straight to
// pane_map's `cwd`.
//
// No vscode dependency -> unit-testable under plain node (mirrors tab_order.js).

// A pane terminal is named `<base> <sid8>` by extension.js::termName and by
// vscode_autorun.py::_term_label, i.e. the session id is the LAST 8-hex token.
// Taking the last match rather than the first keeps a topic that happens to contain
// a hex-looking word ("deadbeef", "facade00") from being read as the session id.
const SID_TOKEN_RE = /[0-9a-f]{8}/gi;

function sidPrefixOf(name) {
  const m = String(name || "").match(SID_TOKEN_RE);
  return m && m.length ? m[m.length - 1].toLowerCase() : "";
}

function terminalsToRows(terminals) {
  // terminals: [{ name, processId }] -- plain shape, no vscode.
  const out = [];
  const ts = Array.isArray(terminals) ? terminals : [];
  for (let i = 0; i < ts.length; i++) {
    const t = ts[i] || {};
    const name = String(t.name || "");
    out.push({
      name: name,
      sidPrefix: sidPrefixOf(name),
      processId: Number.isFinite(t.processId) ? t.processId : null,
      index: i,
    });
  }
  return out;
}

function registryKey(workspacePath) {
  // Same sanitisation build_pane_map.ps1 applies to a cwd ("[^a-zA-Z0-9]" -> "-"),
  // so both sides derive the key independently and no mapping has to be passed.
  return String(workspacePath || "").replace(/[^a-zA-Z0-9]/g, "-");
}

function buildPayload(workspacePath, terminals, hostPid, nowIso) {
  const cwd = String(workspacePath || "");
  const parts = cwd.split(/[\\/]/).filter(Boolean);
  return {
    generatedAt: nowIso,
    source: "vscode.window.terminals",
    cwd: cwd,
    repo: parts.length ? parts[parts.length - 1] : "",
    // The extension host's own pid. A registry file outlives a crashed window, so
    // the consumer requires this process to still be alive before trusting the
    // rows -- otherwise a dead window would pin its terminals live forever, the
    // same latching defect as $inSnap (T-REVIVAL-SELF-REINFORCING-LOOP-001).
    hostPid: Number.isFinite(hostPid) ? hostPid : null,
    terminals: terminalsToRows(terminals),
  };
}

module.exports = { sidPrefixOf, terminalsToRows, registryKey, buildPayload };

// --- self-test: `node terminal_registry.js --selftest` -> exit 0 iff the transform
// holds. Hermetic (no vscode, no disk). Consumed by tools/test_terminal_registry.py.
if (require.main === module && process.argv.includes("--selftest")) {
  const assert = require("assert");
  let ok = 0;
  function check(name, fn) {
    try {
      fn();
      ok++;
      console.log("  OK   " + name);
    } catch (e) {
      console.log("  FAIL " + name + ": " + (e && e.message));
      process.exitCode = 1;
    }
  }

  const terms = [
    { name: "claude-power-pack - por favor vuelve a h d38e0a8e", processId: 111 },
    { name: "CursorProjects - deadbeef topic 2ad805db", processId: 222 },
    { name: "Last session", processId: 333 },
  ];
  const payload = buildPayload(
    "C:\\Users\\User\\Desktop\\Cursor Projects\\Jacobo",
    terms,
    4242,
    "2026-08-11T00:00:00.000Z"
  );

  check("V-SELFTEST-FIELDS", () => {
    for (const k of ["generatedAt", "source", "cwd", "repo", "hostPid", "terminals"]) {
      assert.ok(Object.prototype.hasOwnProperty.call(payload, k), "missing " + k);
    }
  });
  check("V-SELFTEST-REPO", () => assert.strictEqual(payload.repo, "Jacobo"));
  check("V-SELFTEST-HOSTPID", () => assert.strictEqual(payload.hostPid, 4242));
  check("V-SELFTEST-COUNT", () => assert.strictEqual(payload.terminals.length, 3));
  check("V-SELFTEST-SID-LAST-TOKEN", () => {
    // "deadbeef" precedes the real id and must NOT win.
    assert.strictEqual(payload.terminals[0].sidPrefix, "d38e0a8e");
    assert.strictEqual(payload.terminals[1].sidPrefix, "2ad805db");
  });
  check("V-SELFTEST-NO-SID-IS-EMPTY", () =>
    assert.strictEqual(payload.terminals[2].sidPrefix, "")
  );
  check("V-SELFTEST-PROCESSID", () => {
    assert.strictEqual(payload.terminals[0].processId, 111);
    assert.strictEqual(terminalsToRows([{ name: "x" }])[0].processId, null);
  });
  check("V-SELFTEST-KEY", () =>
    assert.strictEqual(
      registryKey("C:\\Users\\User\\Desktop\\Cursor Projects\\Jacobo"),
      "C--Users-User-Desktop-Cursor-Projects-Jacobo"
    )
  );
  check("V-SELFTEST-EMPTY-SAFE", () => {
    const p = buildPayload("", null, null, "t");
    assert.strictEqual(p.terminals.length, 0);
    assert.strictEqual(p.hostPid, null);
  });

  if (process.exitCode === 1) {
    console.log("TERMINAL_REGISTRY_SELFTEST=FAIL");
  } else {
    console.log("TERMINAL_REGISTRY_SELFTEST=PASS ok=" + ok);
  }
}
