#!/usr/bin/env node
'use strict';
// ---------------------------------------------------------------------------
// claude_md_linter_stop.js - Stop-hook size advisory for ~/.claude/CLAUDE.md
//   (CLAUDE.md Router M3, 2026-06-04, BL-CLAUDEMD-ROUTER).
//
// When the global CLAUDE.md approaches / crosses the 40,000-char Claude Code
// performance-warning threshold, surface a non-blocking advisory so the file
// gets trimmed before the warning bites. Cheap: ONE file read in JS, no
// subprocess. Fail-open: any error / no file -> silent {continue:true}.
//
// Thresholds align with trim_claude_md.py (recalibrated to the operative-
// safety floor): WARN at MARGIN (one append below the limit), ALERT at HARD.
// The literal plan said 38,000 for "early warning", but the file's operative
// floor is ~39,658 (always-on safety doctrine), so 38k would fire every Stop
// (alert fatigue). Recalibrated to MARGIN (39,750), reported in SCS C36.
//
// Owner-side registration (HR-001): add to settings.json "Stop" array (or the
// hook-dispatcher Stop-chain). See commands/auto-reset.md style block in M5.
// ---------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');

const HARD = 40000;
const MARGIN = 39750;
const CM = path.join(os.homedir(), '.claude', 'CLAUDE.md');
const BOM = 0xFEFF;

function emit(o) { try { process.stdout.write(JSON.stringify(o)); } catch (e) { void e; } }

function main() {
  try { fs.readFileSync(0, 'utf8'); } catch (e) { void e; }  // drain stdin
  let n;
  try {
    let t = fs.readFileSync(CM, 'utf8');
    if (t.charCodeAt(0) === BOM) { t = t.slice(1); }
    n = t.length;
  } catch (e) { emit({ continue: true }); return; }  // no file -> silent

  if (n >= HARD) {
    emit({ continue: true, additionalContext:
      `[claude_md_linter] ~/.claude/CLAUDE.md = ${n} chars >= ${HARD} `
      + `(Claude Code performance warning ACTIVE). Run `
      + `python tools/trim_claude_md.py --dry-run then --apply.` });
  } else if (n >= MARGIN) {
    emit({ continue: true, additionalContext:
      `[claude_md_linter] ~/.claude/CLAUDE.md = ${n} chars, approaching the `
      + `${HARD} limit. Trim provenance from the next append `
      + `(python tools/trim_claude_md.py --apply).` });
  } else {
    emit({ continue: true });
  }
}

main();
