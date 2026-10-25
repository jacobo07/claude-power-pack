#!/usr/bin/env node
/**
 * corpus-reuse-sentinel.js -- UserPromptSubmit + PreToolUse(Agent|Task) hook.
 *
 * When a prompt, or a subagent spawn prompt, names a registered corpus root, inject the coverage
 * ledger briefing (what was already read, how deeply, which artifacts, what remains) BEFORE the
 * work is paid for again. The python side (modules/cognitive_os/corpus_delivery.py) decides; this
 * file only moves bytes. Spec: vault/specs/cognitive-work-reuse.md.
 *
 * Fail-open: an internal error exits 0 and never blocks the turn. But never silent: a spawn
 * failure or timeout is appended to vault/cognitive_os/delivery.jsonl as FAILED, so silence can be
 * told apart from "nothing to say" (case L). Kill switch: PP_CORPUS_REUSE=off.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const STATE = process.env.PP_CORPUS_STATE_DIR || path.join(ROOT, 'vault', 'cognitive_os');
const LOG = path.join(STATE, 'delivery.jsonl');
const PY = process.env.PP_PYTHON || 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';

function failed(event, detail) {
  try {
    fs.mkdirSync(path.dirname(LOG), { recursive: true });
    fs.appendFileSync(LOG, JSON.stringify({
      ts: new Date().toISOString(), event, outcome: 'FAILED', detail: String(detail).slice(0, 300),
    }) + '\n');
  } catch (_e) { /* counting is best effort */ }
}

function main() {
  if ((process.env.PP_CORPUS_REUSE || '').toLowerCase() === 'off') return;
  let raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch (_e) { return; }
  let payload = {};
  try { payload = JSON.parse(raw || '{}'); } catch (_e) { return; }
  const event = payload.hook_event_name || 'unknown';
  if (event === 'PreToolUse' && !/^(Agent|Task)$/.test(payload.tool_name || '')) return;
  const r = spawnSync(PY, ['-m','modules.cognitive_os.corpus_delivery'], {
    input: raw, cwd: ROOT, encoding: 'utf8', timeout: 4000, windowsHide: true,
    env: Object.assign({}, process.env, { PYTHONPATH: ROOT, PYTHONIOENCODING: 'utf-8' }),
  });
  if (r.error || r.status !== 0) { failed(event, r.error ? r.error.message : 'exit ' + r.status + ' ' + (r.stderr || '')); return; }
  const ctx = (r.stdout || '').trim();
  if (!ctx) return;
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: event, additionalContext: ctx } }));
}

try { main(); } catch (e) { failed('main', e && e.message); }
process.exit(0);
