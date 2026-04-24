#!/usr/bin/env node
/*
 * report.js — Detailed Drill-down Report (MC-OVO-83)
 *
 * Renders either:
 *   summary  — one-line-per-subsystem table (default)
 *   detail   — full evidence for subsystem #N (or by id)
 *
 * Input: JSON array of score payloads from score.js (via --from <file>
 * or stdin), plus optional --detail <index|id>. Consumed by audit_all.js.
 *
 * Output: plain-text report to stdout. ANSI colors applied only if
 * stdout is a TTY; otherwise plain for grep/pipeline safety.
 */

'use strict';

const fs = require('fs');

const ANSI = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  red: '\x1b[31m', green: '\x1b[32m', yellow: '\x1b[33m',
  cyan: '\x1b[36m', gray: '\x1b[90m',
};

function colorize(s, code) {
  if (!process.stdout.isTTY) return s;
  return `${code}${s}${ANSI.reset}`;
}

function scoreColor(n) {
  if (n >= 90) return ANSI.green;
  if (n >= 75) return ANSI.cyan;
  if (n >= 50) return ANSI.yellow;
  return ANSI.red;
}

function verdictLabel(n) {
  if (n >= 90) return 'GREEN';
  if (n >= 75) return 'YELLOW';
  if (n >= 50) return 'ORANGE';
  return 'RED';
}

function parseArgs(argv) {
  const out = { from: null, detail: null, json: false, help: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--from') out.from = argv[++i];
    else if (a === '--detail') out.detail = argv[++i];
    else if (a === '--json') out.json = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else {
      process.stderr.write(`report.js: unknown arg ${a}\n`);
      process.exit(2);
    }
  }
  return out;
}

function helpText() {
  return [
    'report.js — Audit reporter',
    'Usage: node report.js [--from <file>] [--detail <N|id>] [--json]',
  ].join('\n');
}

function readInput(args) {
  const raw = args.from ? fs.readFileSync(args.from, 'utf8') : fs.readFileSync(0, 'utf8');
  const trimmed = raw.trim();
  if (!trimmed) {
    process.stderr.write('report.js: empty input\n');
    process.exit(2);
  }
  const data = JSON.parse(trimmed);
  // Normalize: accept either an envelope {reports: [...], root, ...} or a bare array.
  if (Array.isArray(data)) return { reports: data, root: null, scanned_at: null };
  if (!Array.isArray(data.reports)) {
    process.stderr.write('report.js: input missing reports[]\n');
    process.exit(2);
  }
  return data;
}

function pad(s, n) {
  s = String(s);
  return s.length >= n ? s.slice(0, n) : s + ' '.repeat(n - s.length);
}

function renderSummary(envelope) {
  const { reports, root, scanned_at } = envelope;
  const lines = [];
  const header = colorize('Unified Audit — /audit-all', ANSI.bold);
  lines.push(header);
  if (root) lines.push(colorize(`root: ${root}`, ANSI.dim));
  if (scanned_at) lines.push(colorize(`scanned: ${scanned_at}`, ANSI.dim));
  lines.push('');

  const rows = [['#', 'ID', 'STACK', 'THRASH', 'DRIFT', 'COMPL', 'ENV', 'OVERALL', 'STATUS']];
  reports.forEach((r, idx) => {
    const s = r.scores || {};
    rows.push([
      String(idx + 1),
      r.subsystem_id || '?',
      r.stack || '?',
      String(s.edit_thrashing ?? '-'),
      String(s.drift ?? '-'),
      String(s.completion ?? '-'),
      String(s.env_mapping ?? '-'),
      String(r.overall ?? '-'),
      verdictLabel(r.overall ?? 0),
    ]);
  });

  const widths = rows[0].map((_, c) => Math.max(...rows.map((row) => String(row[c]).length)));
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const parts = row.map((v, c) => pad(v, widths[c]));
    if (i === 0) {
      lines.push(colorize(parts.join('  '), ANSI.bold));
    } else {
      const overall = Number(row[7]);
      const col = scoreColor(overall);
      const coloredOverall = colorize(parts[7], col);
      const coloredStatus = colorize(parts[8], col);
      parts[7] = coloredOverall;
      parts[8] = coloredStatus;
      lines.push(parts.join('  '));
    }
  }

  lines.push('');
  const total = reports.length;
  const red = reports.filter((r) => (r.overall ?? 0) < 50).length;
  const orange = reports.filter((r) => (r.overall ?? 0) >= 50 && (r.overall ?? 0) < 75).length;
  const yellow = reports.filter((r) => (r.overall ?? 0) >= 75 && (r.overall ?? 0) < 90).length;
  const green = total - red - orange - yellow;
  lines.push(`Subsystems: ${total}  `
    + `${colorize('GREEN', ANSI.green)}: ${green}  `
    + `${colorize('YELLOW', ANSI.cyan)}: ${yellow}  `
    + `${colorize('ORANGE', ANSI.yellow)}: ${orange}  `
    + `${colorize('RED', ANSI.red)}: ${red}`);
  lines.push('');
  lines.push(colorize('drill down with: /audit-all <N>  (or by id: /audit-all <id>)', ANSI.dim));
  return lines.join('\n');
}

function renderDetail(envelope, selector) {
  const { reports } = envelope;
  let report = null;
  const asNum = Number(selector);
  if (!Number.isNaN(asNum) && asNum >= 1 && asNum <= reports.length) {
    report = reports[asNum - 1];
  } else {
    report = reports.find((r) => r.subsystem_id === selector);
  }
  if (!report) {
    return `report.js: no subsystem matches selector "${selector}"`;
  }

  const lines = [];
  lines.push(colorize(`Subsystem: ${report.subsystem_id} (${report.stack})`, ANSI.bold));
  lines.push(colorize(`path: ${report.subsystem_path}`, ANSI.dim));
  lines.push(colorize(`scored: ${report.scored_at}`, ANSI.dim));
  lines.push('');

  const s = report.scores || {};
  const overall = report.overall ?? 0;
  const overallStr = colorize(`${overall} (${verdictLabel(overall)})`, scoreColor(overall));
  lines.push(`OVERALL: ${overallStr}`);
  lines.push('');

  const labels = {
    edit_thrashing: 'Edit-Thrashing',
    drift:          'Drift',
    completion:     'Completion',
    env_mapping:    'Env Mapping',
  };
  for (const key of Object.keys(labels)) {
    const v = s[key];
    const col = scoreColor(v ?? 0);
    lines.push(colorize(`— ${labels[key]}: ${v ?? '-'}%`, col));
    const ev = (report.evidence || {})[key];
    if (ev) lines.push(colorize(formatEvidence(ev), ANSI.dim));
    lines.push('');
  }
  return lines.join('\n');
}

function formatEvidence(ev) {
  return JSON.stringify(ev, null, 2)
    .split('\n')
    .map((ln) => '  ' + ln)
    .join('\n');
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(helpText() + '\n');
    return 0;
  }
  const envelope = readInput(args);
  if (args.json) {
    process.stdout.write(JSON.stringify(envelope, null, 2) + '\n');
    return 0;
  }
  const out = args.detail != null ? renderDetail(envelope, args.detail) : renderSummary(envelope);
  process.stdout.write(out + '\n');
  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { renderSummary, renderDetail, verdictLabel };
