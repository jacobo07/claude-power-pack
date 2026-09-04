#!/usr/bin/env node
/**
 * Gate against the SILENT DEAD GATE class.
 *
 * MEASURED 2026-09-04 (FIFA 11 Mod). agent-solo-guard.js and
 * subagent-bash-avoidance-advisor.js were both dead for 99 days from TWO
 * independent causes that each, alone, was fatal and silent:
 *
 *   1. settings.json matched on "Task"; the harness had renamed the subagent
 *      tool to "Agent", so the hook was never invoked at all.
 *   2. The scripts themselves did `if (payload.tool_name !== "Task") exit(0)`,
 *      so even a correct matcher would have been thrown away one line in.
 *
 * Nothing was red. The Owner kept hitting agent hangs in every repo while
 * believing the doctrine was enforced. A gate that cannot fire is
 * indistinguishable, from the outside, from a gate that passes.
 *
 * WHY THIS CHECK IS STATIC. The obvious instrument -- "warn when a guard's log
 * goes stale" -- cannot work here: the guards' own tests write those logs, so
 * the check would be held green by its own suite and could never return the
 * other answer. This file reads configuration and source instead, which tests
 * cannot forge.
 *
 * WHAT IT CANNOT DO. CURRENT_TOOLS below is a maintained list, so a genuinely
 * new tool name reads as unknown until someone adds it. That is the correct
 * direction of failure: loud, and toward noticing. It fails toward a red, never
 * toward silence.
 *
 * Run: node test-matcher-liveness.js
 */

'use strict';

const fs = require('fs');
const path = require('path');

const HOOKS = path.join(__dirname, '..');
const SETTINGS = path.join(HOOKS, '..', 'settings.json');

// Tools this harness actually exposes (2026-09-04), plus the wildcard.
const CURRENT_TOOLS = new Set([
  'Agent', 'Artifact', 'AskUserQuestion', 'Bash', 'Edit', 'Glob', 'Grep',
  'ListAgents', 'PowerShell', 'Read', 'ReportFindings', 'ScheduleWakeup',
  'SendFeedback', 'Skill', 'ToolSearch', 'Workflow', 'Write',
  'CronCreate', 'CronDelete', 'CronList', 'DesignSync', 'EndConversation',
  'EnterPlanMode', 'EnterWorktree', 'ExitPlanMode', 'ExitWorktree', 'Monitor',
  'NotebookEdit', 'PushNotification', 'RemoteTrigger', 'SendMessage',
  'SendUserFile', 'TaskOutput', 'TaskStop', 'WebFetch', 'WebSearch', '*',
]);

// Retired names kept ONLY as aliases beside a live name. A matcher consisting
// of nothing but retired names is dead and must fail.
const LEGACY_ALIASES = new Set(['Task', 'MultiEdit']);

/**
 * The tool names a script GATES on, or null if it does not gate at all.
 *
 * A gate is a COMPARISON of tool_name against a string literal -- the shape that
 * killed agent-solo-guard (`tool_name !== "Task"`).
 *
 * REFINED after this check's first run produced a false positive.
 * research-domain-guard.js reads `tool_name` and uses it ONLY as a log field; it
 * never compares it, so it accepts every payload the matcher routes and is
 * perfectly alive. Merely mentioning tool_name is not gating on it, and naming
 * tools in a COMMENT is not gating either -- the first version swept quoted
 * words from the whole file and flagged a healthy guard.
 */
const GATE_RE = /tool_name\s*(?:!==?|===?)\s*["'][^"']+["']|(?:new\s+Set\()?\[[^\]]*\]\s*\)?\s*\.\s*(?:has|includes)\s*\([^)]*tool_name[^)]*\)|\.\s*(?:has|includes)\s*\(\s*(?:payload|hookData|input|data)?\.?\s*tool_name\s*\)/g;

function gatedNames(src) {
  const gates = [...src.matchAll(GATE_RE)];
  if (gates.length === 0) return null;
  const quoted = new Set();
  for (const g of gates) {
    const from = Math.max(0, g.index - 200);
    const window = src.slice(from, g.index + g[0].length + 60);
    for (const m of window.matchAll(/["']([A-Za-z_][A-Za-z_]{1,24})["']/g)) quoted.add(m[1]);
  }
  return quoted;
}

let pass = 0;
let fail = 0;
const note = (ok, label, detail) => {
  if (ok) { pass += 1; } else { fail += 1; console.log(`  FAIL  ${label}: ${detail}`); }
};

// --- 0. Positive control ----------------------------------------------------
// Without this, a detector that had quietly stopped detecting would report the
// same clean green as a healthy repo -- the very disease this file is about.
// These drive the red branch on synthetic sources every run.
{
  const DEAD = 'if (payload.tool_name !== "Task") { process.exit(0); }';
  const FIXED = 'const T = new Set(["Task", "Agent"]);\nif (!T.has(payload.tool_name)) process.exit(0);';
  const LOGS_ONLY = 'const tool = (hookData && hookData.tool_name) || "";\nlog({ tool });';

  const dead = gatedNames(DEAD);
  note(!!dead && dead.has('Task') && !dead.has('Agent'),
       'positive control: dead gate', 'detector no longer sees `tool_name !== "Task"`');

  const fixed = gatedNames(FIXED);
  note(!!fixed && fixed.has('Agent'),
       'positive control: revived gate', 'detector no longer sees the Set form');

  note(gatedNames(LOGS_ONLY) === null,
       'positive control: log-only use is not a gate',
       'detector would re-raise the research-domain-guard false positive');
}

// This file is mirrored into claude-power-pack/hooks/_tests/, where there is no
// settings.json beside it. Say so out loud and keep the positive controls above
// meaningful, rather than reporting a green that checked nothing.
if (!fs.existsSync(SETTINGS)) {
  console.log(
    `MATCHER_LIVENESS=${pass}/${pass + fail}  ` +
    '(positive controls only: no settings.json at ' + SETTINGS + ')');
  process.exit(fail === 0 ? 0 : 1);
}

const settings = JSON.parse(fs.readFileSync(SETTINGS, 'utf8'));

const entries = [];
for (const [event, matchers] of Object.entries(settings.hooks || {})) {
  for (const m of matchers || []) {
    if (!m || typeof m.matcher !== 'string') continue;
    const names = m.matcher.split('|').map((s) => s.trim()).filter(Boolean);
    entries.push({ event, matcher: m.matcher, names, hooks: m.hooks || [] });
  }
}
note(entries.length > 0, 'settings.json parsed', 'no matchers found at all');

// --- 1. Every matcher must name at least one tool that still exists ---------
for (const e of entries) {
  const live = e.names.filter((n) => CURRENT_TOOLS.has(n) || n.startsWith('mcp__'));
  const unknown = e.names.filter(
    (n) => !CURRENT_TOOLS.has(n) && !LEGACY_ALIASES.has(n) && !n.startsWith('mcp__'));

  note(live.length > 0, `${e.event} matcher '${e.matcher}'`,
       'names no tool that exists -- this hook can never be invoked');
  note(unknown.length === 0, `${e.event} matcher '${e.matcher}'`,
       `unrecognised tool name(s): ${unknown.join(', ')} -- either a typo or a ` +
       'rename this list has not caught up with');
}

// --- 2. A script's own tool_name gate must accept its matcher's names -------
// Cause (2) above. A matcher can be perfect and the script still discard the
// payload on its first line.
for (const e of entries) {
  for (const h of e.hooks) {
    const cmd = typeof h.command === 'string' ? h.command : '';
    const found = cmd.match(/([\w.-]+)\.js/g);
    if (!found) continue;
    const file = path.join(HOOKS, found[found.length - 1]);
    if (!fs.existsSync(file)) continue;

    const gated = gatedNames(fs.readFileSync(file, 'utf8'));
    if (gated === null) continue;   // reads tool_name but never gates on it

    const liveNames = e.names.filter((n) => CURRENT_TOOLS.has(n) && n !== '*');
    if (liveNames.length === 0) continue;

    note(liveNames.some((n) => gated.has(n)),
         `${path.basename(file)} vs matcher '${e.matcher}'`,
         `the matcher routes ${liveNames.join('|')} to this script, but its ` +
         'tool_name gate accepts none of those names -- it will discard every ' +
         'payload the way agent-solo-guard did for 99 days');
  }
}

console.log(`MATCHER_LIVENESS=${pass}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
