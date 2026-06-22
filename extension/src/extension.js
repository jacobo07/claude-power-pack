"use strict";
// PP Sessions -- read-only side panel of resumable Claude Code panes.
// Single source of truth: ~/.claude/state/pane_map.json (generated from disk by
// tools/build_pane_map.ps1). This extension never derives pane data itself and
// never invents session ids -- it renders exactly what the map contains.

const vscode = require("vscode");
const fs = require("fs");
const os = require("os");
const path = require("path");

const MAP_JSON = path.join(os.homedir(), ".claude", "state", "pane_map.json");
const MAP_MD = path.join(os.homedir(), ".claude", "state", "pane_map.md");

function readMap() {
  try {
    const raw = fs.readFileSync(MAP_JSON, "utf8").replace(/^﻿/, "");
    const data = JSON.parse(raw);
    return Array.isArray(data.panes) ? data : { panes: [], counts: {} };
  } catch (e) {
    return { panes: [], counts: {}, error: String(e && e.message ? e.message : e) };
  }
}

const STATUS_ORDER = { RESUMABLE: 0, OLD: 1, STALE: 2 };
const STATUS_LABEL = {
  RESUMABLE: "Resumable (active)",
  OLD: "Resumable (old >48h)",
  STALE: "Transcript lost - new chat",
};

class PaneNode {
  constructor(pane) {
    this.kind = "pane";
    this.pane = pane;
  }
}
class GroupNode {
  constructor(status, panes) {
    this.kind = "group";
    this.status = status;
    this.panes = panes;
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
      const panes = this.map.panes || [];
      const byStatus = new Map();
      for (const p of panes) {
        const s = p.status || "STALE";
        if (!byStatus.has(s)) byStatus.set(s, []);
        byStatus.get(s).push(p);
      }
      const groups = [...byStatus.entries()]
        .sort((a, b) => (STATUS_ORDER[a[0]] ?? 9) - (STATUS_ORDER[b[0]] ?? 9))
        .map(([s, list]) => new GroupNode(s, list));
      return Promise.resolve(groups);
    }
    if (element.kind === "group") {
      return Promise.resolve(element.panes.map((p) => new PaneNode(p)));
    }
    return Promise.resolve([]);
  }

  getTreeItem(node) {
    if (node.kind === "group") {
      const item = new vscode.TreeItem(
        `${STATUS_LABEL[node.status] || node.status} (${node.panes.length})`,
        vscode.TreeItemCollapsibleState.Expanded
      );
      item.contextValue = "ppGroup";
      return item;
    }
    const p = node.pane;
    const topic = (p.topic || "").trim() || "(no topic)";
    const item = new vscode.TreeItem(
      `${p.repo} - ${topic}`,
      vscode.TreeItemCollapsibleState.None
    );
    item.description = p.lastActivity ? new Date(p.lastActivity).toLocaleString() : "";
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

function resumePane(p) {
  if (!p) return;
  const term = vscode.window.createTerminal({
    name: `${p.repo} ${String(p.sessionId).slice(0, 8)}`,
    cwd: p.cwd,
  });
  term.show(true);
  term.sendText(p.resumeCmd || "claude", true);
}

function activate(context) {
  const provider = new PaneProvider();
  const view = vscode.window.createTreeView("ppSessionsView", {
    treeDataProvider: provider,
    showCollapseAll: false,
  });
  context.subscriptions.push(view);

  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.command = "ppSessions.focus";
  const refreshStatus = () => {
    const n = (provider.map.counts && provider.map.counts.resumable) || 0;
    status.text = `$(comment-discussion) PP: ${n}`;
    status.tooltip = "PP Sessions - resumable Claude Code panes. Click to open the panel.";
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
    })
  );

  // Live refresh: watch pane_map.json for changes (regenerated by the hub).
  try {
    const watcher = fs.watch(path.dirname(MAP_JSON), (_evt, fname) => {
      if (fname === "pane_map.json") {
        provider.refresh();
        refreshStatus();
      }
    });
    context.subscriptions.push({ dispose: () => watcher.close() });
  } catch (_e) {
    // directory may not exist yet; degrade silently, manual refresh still works
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
