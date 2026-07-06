"use strict";
// Pure, vscode-free transform of Cursor's editor tab groups into the ordered
// pane-recovery overlay written to ~/.claude/state/tab_order.json.
//
// No vscode dependency -> unit-testable under plain node (mirrors restore_guard.js).
// extension.js normalizes vscode.window.tabGroups.all into the plain shape this
// module consumes, calls tabsToOrder(), and writes the JSON. build_pane_map.ps1
// then leads the pane map with panes in the real left-to-right visual tab order.
//
// The real tab order is ONLY reachable from inside an extension via
// vscode.window.tabGroups; build_pane_map.ps1 cannot derive it. See
// T-TAB-ORDER-EXTENSION-ONLY-001.

// A pane terminal created by PP Sessions is named `${repo} ${sid8}` (extension.js
// resumePane / runColdStartRestore). The 8-hex session-id prefix in the tab label
// is the join key back to a pane in pane_map.json.
const SID_PREFIX_RE = /[0-9a-f]{8}/i;

function sidPrefixOf(label) {
  const m = SID_PREFIX_RE.exec(String(label || ""));
  return m ? m[0].toLowerCase() : "";
}

function tabsToOrder(groups) {
  // groups: [{ tabs: [{ label, isActive, isTerminal }] }] -- plain shape, no vscode.
  // Returns [{ label, group_index, tab_index, is_active, is_terminal, sidPrefix }]
  // in exact left-to-right visual order (group order, then tab order within group).
  const out = [];
  const gs = Array.isArray(groups) ? groups : [];
  for (let gi = 0; gi < gs.length; gi++) {
    const tabs = gs[gi] && Array.isArray(gs[gi].tabs) ? gs[gi].tabs : [];
    for (let ti = 0; ti < tabs.length; ti++) {
      const t = tabs[ti] || {};
      const label = String(t.label || "");
      out.push({
        label: label,
        group_index: gi,
        tab_index: ti,
        is_active: !!t.isActive,
        is_terminal: !!t.isTerminal,
        sidPrefix: sidPrefixOf(label),
      });
    }
  }
  return out;
}

function buildPayload(groups, nowIso) {
  return {
    generatedAt: nowIso,
    source: "vscode.window.tabGroups",
    tabs: tabsToOrder(groups),
  };
}

module.exports = { sidPrefixOf, tabsToOrder, buildPayload };

// --- self-test: `node tab_order.js --selftest` -> exit 0 iff the transform holds.
// Hermetic (no vscode, no disk). Consumed by tools/test_tab_order.py V-TAB-ORDER-WRITTEN.
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
  const groups = [
    {
      tabs: [
        { label: "claude-power-pack 1022d113", isActive: true, isTerminal: true },
        { label: "TUA-X 9f8e7d6c", isActive: false, isTerminal: true },
      ],
    },
    { tabs: [{ label: "README.md", isActive: false, isTerminal: false }] },
  ];
  const order = tabsToOrder(groups);
  check("V-SELFTEST-COUNT", () => assert.strictEqual(order.length, 3));
  check("V-SELFTEST-FIELDS", () => {
    const req = ["label", "group_index", "tab_index", "is_active", "is_terminal", "sidPrefix"];
    for (const e of order) {
      for (const k of req) {
        assert.ok(Object.prototype.hasOwnProperty.call(e, k), "missing " + k);
      }
    }
  });
  check("V-SELFTEST-ORDER", () => {
    assert.strictEqual(order[0].group_index, 0);
    assert.strictEqual(order[0].tab_index, 0);
    assert.strictEqual(order[1].tab_index, 1);
    assert.strictEqual(order[2].group_index, 1);
  });
  check("V-SELFTEST-SIDPREFIX", () => {
    assert.strictEqual(order[0].sidPrefix, "1022d113");
    assert.strictEqual(order[1].sidPrefix, "9f8e7d6c");
    assert.strictEqual(order[2].sidPrefix, ""); // README.md -> no session id
  });
  check("V-SELFTEST-ACTIVE", () => assert.strictEqual(order[0].is_active, true));
  if (process.exitCode === 1) {
    console.log("TAB_ORDER_SELFTEST=FAIL");
  } else {
    console.log("TAB_ORDER_SELFTEST=PASS ok=" + ok);
  }
}
