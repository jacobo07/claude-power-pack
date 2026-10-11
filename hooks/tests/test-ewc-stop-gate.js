'use strict';
// Unit test: hooks/lib/ewc_gate.js (EWC Pre-Stop Unresolved Obligation Gate). Both poles per branch.
const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ewc-gate-'));
process.env.GSDX_GOALS_ROOT = path.join(tmp, 'goals');
process.env.GSD_LONG_RUN_STATE_DIR = path.join(tmp, 'state');
const gate = require('../lib/ewc_gate.js');

let pass = 0; let fail = 0;
function t(name, fn) { try { fn(); pass++; console.log('PASS ' + name); } catch (e) { fail++; console.log('FAIL ' + name + ': ' + e.message); } }

function transcript(name, text) {
  const p = path.join(tmp, name + '.jsonl');
  fs.writeFileSync(p, JSON.stringify({ type: 'user', message: { role: 'user', content: 'go' } }) + '\n'
    + JSON.stringify({ type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text }] } }) + '\n');
  return p;
}
const INCIDENT = '| Check | Result |\n|---|---|\n| Contrast | FAIL (RED) |\n| Spacing | WARN: 3 off-grid, fixable |\n\nThe evidence file was not written. Next iteration: fix contrast, I recommend doing it next.\n\nFinal approval is the Owner\'s.';
const CLEAN = 'All 12 checks pass (12/12 PASS, 0 FAIL, 0 WARN). Evidence written and everything committed.';

t('obligation id matches the Python implementation', () => {
  assert.strictEqual(gate.obligationId('Fix the contrast ratio! (RED)'), 's-313634782b');
});
t('incident text compiles to AGENT/NOW obligations (positive pole)', () => {
  const obs = gate.compileTurn(INCIDENT, gate.loadPatterns());
  assert.ok(obs.filter((o) => o.owner_class === 'AGENT' && o.actionability === 'NOW').length >= 4);
});
t('clean text compiles to nothing (negative pole)', () => {
  assert.strictEqual(gate.compileTurn(CLEAN, gate.loadPatterns()).length, 0);
});
t('evaluate: incident -> CONTINUE naming one obligation + next_action', () => {
  const g = gate.evaluate({ session_id: 's1', transcript_path: transcript('inc', INCIDENT) });
  assert.ok(g.verdict.startsWith('CONTINUE_'), g.verdict);
  assert.ok(g.ob && g.ob.id && g.ob.next_action);
});
t('evaluate: clean -> STOP_COMPLETE', () => {
  assert.strictEqual(gate.evaluate({ session_id: 's2', transcript_path: transcript('ok', CLEAN) }).verdict, 'STOP_COMPLETE');
});
t('evaluate: Owner-only -> STOP_HUMAN_GATE with <= 6 line package', () => {
  const g = gate.evaluate({ session_id: 's3', transcript_path: transcript('own', 'Everything passes and is committed. The publication approval is the Owner\'s decision to make: approve publishing the notes or hold.') });
  assert.strictEqual(g.verdict, 'STOP_HUMAN_GATE');
  assert.ok(g.package.length > 0 && g.package.length <= 6);
});
t('evaluate: missing transcript file -> STOP_UNKNOWN, never COMPLETE', () => {
  const g = gate.evaluate({ session_id: 's4', transcript_path: path.join(tmp, 'nope.jsonl') });
  assert.strictEqual(g.verdict, 'STOP_UNKNOWN');
});
t('evaluate: corrupt session ledger -> STOP_UNKNOWN even with a clean transcript', () => {
  const d = path.join(process.env.GSDX_GOALS_ROOT, 'abcdef0123456', gate.scopeId('s5'));
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, '000001.json'), '{not json');
  assert.strictEqual(gate.evaluate({ session_id: 's5', transcript_path: transcript('ok5', CLEAN) }).verdict, 'STOP_UNKNOWN');
});
t('evaluate: ledger gap -> STOP_UNKNOWN', () => {
  const d = path.join(process.env.GSDX_GOALS_ROOT, 'abcdef0123456', gate.scopeId('s6'));
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, '000002.json'), JSON.stringify({ type: 'obligation.accepted', data: {} }));
  assert.strictEqual(gate.evaluate({ session_id: 's6', transcript_path: transcript('ok6', CLEAN) }).verdict, 'STOP_UNKNOWN');
});
t('digest moves when an obligation is added and is stable otherwise', () => {
  const a = [{ id: 'a', actionability: 'NOW', severity: 'RED' }];
  const b = a.concat([{ id: 'b', actionability: 'NOW', severity: 'RED' }]);
  assert.strictEqual(gate.digestOf(a), gate.digestOf(a.slice()));
  assert.notStrictEqual(gate.digestOf(a), gate.digestOf(b));
});
t('recordDiagnosis writes an event evaluate reads back as AGENT/NOW', () => {
  assert.ok(gate.recordDiagnosis('s7', 'Stalled: no progress on x', 'Change strategy: diagnose x'));
  const g = gate.evaluate({ session_id: 's7', transcript_path: transcript('ok7', CLEAN) });
  assert.ok(g.verdict.startsWith('CONTINUE_'), g.verdict);
});

console.log(`EWC_GATE_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
