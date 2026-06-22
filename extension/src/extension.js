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
    })
  );

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
