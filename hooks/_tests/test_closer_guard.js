/* V-CLOSER-GUARD — behavioural gate for closer-guard.js
 * Evidence-first: every case asserts the OBSERVED verdict, not the intent. */
const path = require('path');
const fs = require('fs');
const os = require('os');
const G = require(path.join(os.homedir(), '.claude', 'hooks', 'closer-guard.js'));

let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log(`  OK   ${id} :: ${ev}`); };
const no = (id, d) => { fail++; console.log(`  FAIL ${id} :: ${d}`); };

function expectBlocked(id, text, wantCls) {
  const v = G.classify(text);
  if (v && v.cls === wantCls) ok(id, `${wantCls}`);
  else no(id, `expected ${wantCls}, got ${v ? v.cls : 'null (allowed)'}`);
}
function expectAllowed(id, text) {
  const v = G.classify(text);
  if (!v) ok(id, 'allowed');
  else no(id, `expected allow, got BLOCK ${v.cls}`);
}

console.log('\n-- MUST BLOCK --');
// The exact closer that caused the 2026-08-27 dead screen.
expectBlocked('V-CG-REAL-INCIDENT',
  'The FIOS message resolves - and it corrects my own prior fix. Recording the session objective honestly.',
  'INTENT_NARRATION');
expectBlocked('V-CG-LETME', 'Root cause found. Let me check the anchor.', 'INTENT_NARRATION');
expectBlocked('V-CG-NOWILL', 'Commit landed. Now I\'ll update the README.', 'INTENT_NARRATION');
expectBlocked('V-CG-GERUND', 'Committing the routing layer now.', 'INTENT_NARRATION');
expectBlocked('V-CG-AWAIT', 'Tests are running. Awaiting the completion notification.', 'PASSIVE_WAIT');
expectBlocked('V-CG-STANDBY', 'Deploy triggered. Standing by.', 'PASSIVE_WAIT');
expectBlocked('V-CG-INPROG', 'Commit and push in progress.', 'PASSIVE_WAIT');
expectBlocked('V-CG-EMPTY', '', 'EMPTY');
expectBlocked('V-CG-WS', '   \n  ', 'EMPTY');

console.log('\n-- MUST ALLOW (false-positive guard) --');
expectAllowed('V-CG-QUESTION', 'I can route these two ways. Which do you want?');
expectAllowed('V-CG-QUESTION-AFTER-INTENT',
  'Next I\'ll wire the ledger - but should it live in the PP repo or TUA-X?');
expectAllowed('V-CG-DELIVERABLE',
  'Routing shipped: 1,738 EVA_HIGH_VALUE, 409 MULTI_SOURCE, nothing diverted. Commit 68434f5.');
expectAllowed('V-CG-MIDTURN-NARRATION',
  'Let me check the anchor. It exists at line 241, so the insert landed cleanly and the six rules are in place.');
expectAllowed('V-CG-SUMMARY',
  'The probe returned 4/4 extractable answers averaging 7,225 characters - the richest lens in the corpus.');
expectAllowed('V-CG-PLAIN-FACT', 'No guard exists; the only match was an unrelated removed file.');

console.log('\n-- FAIL-OPEN --');
const r1 = G.run({});
if (r1 && r1.continue === true) ok('V-CG-NO-INPUT', 'fail-open on empty input');
else no('V-CG-NO-INPUT', JSON.stringify(r1));

const r2 = G.run({ transcript_path: 'C:/nope/does/not/exist.jsonl' });
if (r2 && r2.continue === true) ok('V-CG-MISSING-FILE', 'fail-open on missing transcript');
else no('V-CG-MISSING-FILE', JSON.stringify(r2));

console.log('\n-- END-TO-END via transcript + ANTI-LOOP --');
const tmp = path.join(process.env.TEMP || os.tmpdir(), 'cg_tx_test.jsonl');
const mk = (blocks) => JSON.stringify({ type: 'assistant', message: { role: 'assistant', content: blocks } });

// Case A: text-only bad closer -> BLOCK
fs.writeFileSync(tmp, mk([{ type: 'text', text: 'Recording the session objective honestly.' }]) + '\n');
const a = G.run({ transcript_path: tmp, session_id: 'sessA' });
if (a && a.decision === 'block') ok('V-CG-E2E-BLOCK', 'blocked with reason');
else no('V-CG-E2E-BLOCK', JSON.stringify(a));

// Anti-loop: identical closer, same session -> must ALLOW the 2nd time
const a2 = G.run({ transcript_path: tmp, session_id: 'sessA' });
if (a2 && a2.continue === true) ok('V-CG-ANTILOOP', 'second identical block released');
else no('V-CG-ANTILOOP', `infinite block loop! ${JSON.stringify(a2)}`);

// Case B: same bad text BUT a tool_use present -> must ALLOW
fs.writeFileSync(tmp, mk([
  { type: 'text', text: 'Recording the session objective honestly.' },
  { type: 'tool_use', name: 'Write', input: {} },
]) + '\n');
const b = G.run({ transcript_path: tmp, session_id: 'sessB' });
if (b && b.continue === true) ok('V-CG-TOOLCALL-EXEMPT', 'turn with tool_use never blocked');
else no('V-CG-TOOLCALL-EXEMPT', JSON.stringify(b));

try { fs.unlinkSync(tmp); } catch { }

console.log(`\nCLOSER_GUARD_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
