"use strict";
// PP Sessions -- read-only side panel of resumable Claude Code panes, grouped by
// repo. Single source of truth: ~/.claude/state/pane_map.json (generated from the
// transcripts on disk by tools/build_pane_map.ps1). This extension never derives
// pane data itself and never invents session ids.

const vscode = require("vscode");
const fs = require("fs");
const os = require("os");
const path = require("path");

const MAP_JSON = path.join(os.homedir(), ".claude", "state", "pane_map.json");
const MAP_MD = path.join(os.homedir(), ".claude", "state", "pane_map.md");
const TAB_ORDER_JSON = path.join(os.homedir(), ".claude", "state", "tab_order.json");

const { buildPayload } = require("./tab_order");

// Capture the real visual tab order (SCS C78 addendum v2). vscode.window.tabGroups
// is the ONLY source of the left-to-right tab order the Owner sees; build_pane_map.ps1
// cannot derive it (T-TAB-ORDER-EXTENSION-ONLY-001). We normalize the tab groups into
// the plain shape tab_order.js consumes, resolve the terminal flag, and ATOMICALLY
// write ~/.claude/state/tab_order.json (tmp + rename so a reader never sees a partial
// file). Fail-open: if tabGroups is unavailable or anything throws, we write nothing
// and the pane map falls back to lastActivity order with no error.
function captureTabOrder() {
  try {
    const api = vscode.window.tabGroups;
    if (!api || !Array.isArray(api.all)) return;
    const groups = api.all.map((g) => ({
      tabs: (g.tabs || []).map((t) => ({
        label: t.label,
        isActive: !!t.isActive,
        isTerminal: !!(vscode.TabInputTerminal && t.input instanceof vscode.TabInputTerminal),
      })),
    }));
    const payload = buildPayload(groups, new Date().toISOString());
    fs.mkdirSync(path.dirname(TAB_ORDER_JSON), { recursive: true });
    const tmp = TAB_ORDER_JSON + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(payload, null, 2), "utf8");
    fs.renameSync(tmp, TAB_ORDER_JSON);
  } catch (_e) {
    // never disrupt the editor; pane_map falls back to lastActivity silently
  }
}

function readMap() {
  try {
    const raw = fs.readFileSync(MAP_JSON, "utf8").replace(/^﻿/, "");
    const data = JSON.parse(raw);
    return Array.isArray(data.panes) ? data : { panes: [], counts: {} };
  } catch (e) {
    return { panes: [], counts: {}, error: String(e && e.message ? e.message : e) };
  }
}

class RepoNode {
  constructor(repo, panes) {
    this.kind = "repo";
    this.repo = repo;
    this.panes = panes;
  }
}
class PaneNode {
  constructor(pane) {
    this.kind = "pane";
    this.pane = pane;
  }
}

class PaneProvider {
  constructor() {
    this._onDidChange = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChange.event;
    this.map = readMap();
  }

  refresh() {
    this.map = readMap();
    this._onDidChange.fire();
  }

  getChildren(element) {
    if (!element) {
      // top level: one group per repo, repos sorted by their most-recent pane
      const panes = this.map.panes || [];
      const byRepo = new Map();
      for (const p of panes) {
        const r = p.repo || "(unknown)";
        if (!byRepo.has(r)) byRepo.set(r, []);
        byRepo.get(r).push(p);
      }
      const groups = [...byRepo.entries()].map(([r, list]) => {
        list.sort((a, b) => String(b.lastActivity).localeCompare(String(a.lastActivity)));
        return new RepoNode(r, list);
      });
      groups.sort((a, b) =>
        String(b.panes[0] && b.panes[0].lastActivity).localeCompare(
          String(a.panes[0] && a.panes[0].lastActivity)
        )
      );
      return Promise.resolve(groups);
    }
    if (element.kind === "repo") {
      return Promise.resolve(element.panes.map((p) => new PaneNode(p)));
    }
    return Promise.resolve([]);
  }

  getTreeItem(node) {
    if (node.kind === "repo") {
      const item = new vscode.TreeItem(
        `${node.repo}  (${node.panes.length})`,
        vscode.TreeItemCollapsibleState.Expanded
      );
      item.contextValue = "ppRepo";
      item.iconPath = new vscode.ThemeIcon("repo");
      return item;
    }
    const p = node.pane;
    const topic = (p.topic || "").trim() || "(no topic)";
    const item = new vscode.TreeItem(topic, vscode.TreeItemCollapsibleState.None);
    const age = typeof p.ageHours === "number" ? `${p.ageHours}h ago` : "";
    item.description = age;
    item.tooltip = new vscode.MarkdownString(
      `**${p.repo}**\n\n${topic}\n\n` +
        `- cwd: \`${p.cwd}\`\n` +
        `- session: \`${p.sessionId}\`\n` +
        `- status: **${p.status}** (confidence ${p.confidence})\n` +
        `- resume: \`${p.resumeCmd}\``
    );
    item.contextValue = "ppPane";
    item.iconPath = new vscode.ThemeIcon(
      p.status === "RESUMABLE" ? "debug-start" : p.status === "OLD" ? "history" : "circle-slash"
    );
    item.command = {
      command: "ppSessions.resume",
      title: "Resume",
      arguments: [p],
    };
    return item;
  }
}

// Terminal/tab name = pane_map topic (truncated), prefixed by the repo, with the
// 8-hex session id appended as tab_order.js's join key. Mirrors
// vscode_autorun.py::_term_label so extension-created tabs and auto-task tabs read
// identically (T-TERMINAL-NAME-FROM-PROFILE-001). Fail-open: no topic -> repo
// name; no repo -> "claude" -- never an empty terminal name.
const TERM_LABEL_MAX = 40;
function termName(p) {
  const sid8 = String((p && p.sessionId) || "").slice(0, 8);
  const topic = ((p && p.topic) || "").trim();
  const repo = ((p && p.repo) || "").trim();
  let base = topic ? (repo ? `${repo} - ${topic}` : topic) : repo || "claude";
  base = base.slice(0, TERM_LABEL_MAX).trim();
  return `${base} ${sid8}`.trim();
}

function resumePane(p) {
  if (!p) return;
  const term = vscode.window.createTerminal({
    name: termName(p),
    cwd: p.cwd,
  });
  term.show(true);
  term.sendText(p.resumeCmd || "kclaude", true);
}

const { panesToRestore } = require("./restore_guard");

// Cold-start guarded restore (SCS C50 Option C). On a true cold start (no live
// terminals) auto-launch `claude --resume` for this repo's open panes; on a
// reload (terminals already reconnected by persistent sessions) do nothing, so
// no pane is ever duplicated.
const RESTORE_SETTLE_MS = 2500;

function currentCwds() {
  return (vscode.workspace.workspaceFolders || []).map((f) => f.uri.fsPath);
}

function runColdStartRestore(provider, opts) {
  const force = !!(opts && opts.force);
  const cfg = vscode.workspace.getConfiguration("ppSessions");
  const enabled = force || cfg.get("autoRestoreOnColdStart", true);
  provider.map = readMap(); // freshest disk truth
  const liveTerms = force ? 0 : (vscode.window.terminals || []).length;
  const panes = panesToRestore(provider.map, currentCwds(), liveTerms, { enabled });
  for (const p of panes) {
    const term = vscode.window.createTerminal({
      name: termName(p),
      cwd: p.cwd,
    });
    term.show(false);
    term.sendText(p.resumeCmd, true);
  }
  if (panes.length) {
    vscode.window.showInformationMessage(
      `PP Sessions: cold-start restored ${panes.length} pane(s).`
    );
  }
  return panes.length;
}

function activate(context) {
  const provider = new PaneProvider();
  const view = vscode.window.createTreeView("ppSessionsView", {
    treeDataProvider: provider,
    showCollapseAll: true,
  });
  context.subscriptions.push(view);

  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.command = "ppSessions.focus";
  const refreshStatus = () => {
    const panes = provider.map.panes || [];
    const repos = new Set(panes.map((p) => p.repo)).size;
    status.text = `$(comment-discussion) PP: ${panes.length}`;
    status.tooltip = `PP Sessions -- ${panes.length} resumable panes across ${repos} repos. Click to open.`;
    status.show();
  };
  refreshStatus();
  context.subscriptions.push(status);

  context.subscriptions.push(
    vscode.commands.registerCommand("ppSessions.refresh", () => {
      provider.refresh();
      refreshStatus();
    }),
    vscode.commands.registerCommand("ppSessions.resume", (p) => resumePane(p)),
    vscode.commands.registerCommand("ppSessions.copyResume", (node) => {
      const p = node && node.pane ? node.pane : node;
      if (p && p.resumeCmd) {
        vscode.env.clipboard.writeText(p.resumeCmd);
        vscode.window.showInformationMessage(`Copied: ${p.resumeCmd}`);
      }
    }),
    vscode.commands.registerCommand("ppSessions.openMap", () => {
      vscode.window.showTextDocument(vscode.Uri.file(MAP_MD));
    }),
    vscode.commands.registerCommand("ppSessions.focus", () => {
      vscode.commands.executeCommand("ppSessionsView.focus");
    }),
    vscode.commands.registerCommand("ppSessions.restoreColdStart", () =>
      runColdStartRestore(provider, { force: true })
    )
  );

  // SCS C50 Option C: guarded auto-restore on cold start. Delayed so persistent
  // sessions can reconnect terminals first on a reload (then liveTerminalCount>0
  // and we correctly skip). Fail-open: never block startup.
  setTimeout(() => {
    try {
      runColdStartRestore(provider);
    } catch (_e) {
      // never block startup
    }
  }, RESTORE_SETTLE_MS);

  // SCS C78 addendum v2: record the real visual tab order for build_pane_map.ps1.
  // Capture once at startup, then on every tab-group / tab change (reorder, open,
  // close, active switch). Fail-open: absent API -> tab order simply not recorded.
  captureTabOrder();
  try {
    if (vscode.window.tabGroups) {
      context.subscriptions.push(
        vscode.window.tabGroups.onDidChangeTabGroups(() => captureTabOrder()),
        vscode.window.tabGroups.onDidChangeTabs(() => captureTabOrder())
      );
    }
  } catch (_e) {
    // tabGroups API absent -> fail-open, tab order not recorded
  }

  // Live refresh: watch pane_map.json (regenerated by build_pane_map.ps1 / hub).
  try {
    const watcher = fs.watch(path.dirname(MAP_JSON), (_evt, fname) => {
      if (fname === "pane_map.json") {
        provider.refresh();
        refreshStatus();
      }
    });
    context.subscriptions.push({ dispose: () => watcher.close() });
  } catch (_e) {
    // directory may not exist yet; manual refresh still works
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
