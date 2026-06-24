"use strict";
// Cold-start restore decision for PP Sessions (SCS C50 Option C).
//
// No vscode dependency -> unit-testable under plain node.
//
// The PP Sessions extension auto-launches `claude --resume` for a repo's open
// panes ONLY on a true cold start: a window opened with the pty host gone, so
// zero terminals are live. On a Reload Window the persistent-sessions pty host
// has already reconnected the terminals (liveTerminalCount > 0), so this returns
// NOTHING -- that is what prevents the double-pane bug SCS C50 sealed. We never
// invent a session id; every launched pane comes from pane_map.json (disk truth)
// and only panes flagged `live` (an open tab at the last map build) are restored.

function norm(p) {
  // Case/separator-insensitive path key for matching a pane cwd to a workspace
  // folder. Backslashes, no trailing slash, lowercase.
  return String(p || "").replace(/[\/\\]+/g, "\\").replace(/\\+$/, "").toLowerCase();
}

function panesToRestore(map, cwds, liveTerminalCount, opts) {
  // Returns the de-duplicated list of {sessionId, cwd, repo, resumeCmd} to
  // launch. Empty when auto-restore is disabled, when any terminal is live
  // (reload, not cold start), when there is no workspace folder, or when the
  // map holds no live pane for this window's repo.
  const options = opts || {};
  if (options.enabled === false) return [];
  if ((liveTerminalCount || 0) > 0) return [];          // reload guard
  const folders = (cwds || []).map(norm).filter(Boolean);
  if (!folders.length) return [];
  const wanted = new Set(folders);
  const out = [];
  const seen = new Set();
  const panes = (map && map.panes) || [];
  for (const p of panes) {
    if (!p || !p.live) continue;                        // only open tabs at risk
    if (!wanted.has(norm(p.cwd))) continue;             // only this window's repo
    const sid = p.sessionId;
    if (!sid || seen.has(sid)) continue;                // dedupe by session
    seen.add(sid);
    out.push({
      sessionId: sid,
      cwd: p.cwd,
      repo: p.repo || "",
      resumeCmd: p.resumeCmd || ("claude --resume " + sid),
    });
  }
  return out;
}

module.exports = { norm, panesToRestore };
