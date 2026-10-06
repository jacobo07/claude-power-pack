#!/usr/bin/env node
'use strict';
// V-SSINPROC-* -- the SessionStart in-process lane (C1, vault/plans/pillar-k-resident-prefix-2026-10-05.md,
// audit vault/plans/_audit-hub-reliability-2026-10-06.md gaps 1-5, 9).
//
// Hermetic: USERPROFILE / HOME / TEMP / TMP point at a scratch tree BEFORE anything is required, so the
// floor log, the dispatcher error log, the restart marker, the capsules and the hub log all live there.
// The repo dispatcher is copied into <tmp>/hooks next to a copy of the live host-memory-floor.js, and
// session_cards.js into <tmp>/skills/claude-power-pack/hooks, i.e. the live layout its relative paths
// expect. Every switch is driven from both poles; every ordering claim has a control.
const fs = require('fs');
const os = require('os');
const path = require('path');

const PP = path.resolve(__dirname, '..');
const LIVE_FLOOR = path.join(os.homedir(), '.claude', 'hooks', 'host-memory-floor.js');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ssinproc-'));
for (const k of ['USERPROFILE', 'HOME', 'TEMP', 'TMP']) process.env[k] = tmp;
for (const k of ['CLAUDE_HOST_MEM_FLOOR_INPROC', 'CLAUDE_SESSION_CARDS_INPROC', 'PP_SESSION_CARDS_DONE',
  'CLAUDE_HOST_MEM_FLOOR', 'CPP_ROLLOVER_ACTIVE']) delete process.env[k];

let pass = 0, fail = 0;
function check(id, ok, ev) {
  if (ok) { pass++; console.log('  PASS ' + id); } else { fail++; console.log('  FAIL ' + id + ' -- ' + ev); }
}

if (!fs.existsSync(LIVE_FLOOR)) {
  console.log('  FAIL V-SSINPROC-PRECONDITION -- live floor missing: ' + LIVE_FLOOR);
  process.exit(1);
}
const HOOKS = path.join(tmp, 'hooks');
const PPH = path.join(tmp, 'skills', 'claude-power-pack', 'hooks');
fs.mkdirSync(HOOKS, { recursive: true });
fs.mkdirSync(PPH, { recursive: true });
fs.copyFileSync(path.join(PP, 'hooks', 'hook-dispatcher.js'), path.join(HOOKS, 'hook-dispatcher.js'));
fs.copyFileSync(LIVE_FLOOR, path.join(HOOKS, 'host-memory-floor.js'));
fs.copyFileSync(path.join(PP, 'hooks', 'session_cards.js'), path.join(PPH, 'session_cards.js'));

const STATE = path.join(tmp, '.claude', 'state');
fs.mkdirSync(path.join(STATE, 'rollover', 'capsules'), { recursive: true });
const CWD = path.join(tmp, 'repo');
fs.mkdirSync(CWD);
const MARKER = path.join(STATE, 'restart_pending.json');
const writeMarker = () => fs.writeFileSync(MARKER, JSON.stringify({ cwd: CWD, branch: 'b1', timestamp: '2026-10-06T10:00:00' }));

const disp = require(path.join(HOOKS, 'hook-dispatcher.js'));
const CHAIN = disp.CHAIN_MAP['SessionStart-chain'];
const FLOOR_STEP = './host-memory-floor.js';
const ctxOf = (o) => (o && o.hookSpecificOutput && o.hookSpecificOutput.additionalContext) || '';
const payload = (extra) => JSON.stringify(Object.assign({ session_id: 'aaaa1111-2222', cwd: CWD, source: 'startup' }, extra || {}));
function run(env, raw, event) {
  delete process.env.PP_SESSION_CARDS_DONE;
  for (const k of ['CLAUDE_HOST_MEM_FLOOR_INPROC', 'CLAUDE_SESSION_CARDS_INPROC', 'CLAUDE_HOST_MEM_CRIT_MB']) delete process.env[k];
  Object.assign(process.env, env || {});
  return disp.sessionStartInProcess(event || 'SessionStart-chain', CHAIN, raw);
}

// Precondition: the real chain still lists the floor, so "it left the chain" is a claim that can fail.
check('V-SSINPROC-CHAIN-HAS-FLOOR', CHAIN.some((s) => s.script === FLOOR_STEP), JSON.stringify(CHAIN));

// 1. Both halves in-process, floor forced CRITICAL, restart marker present: floor first, then the card.
writeMarker();
let r = run({ CLAUDE_HOST_MEM_CRIT_MB: '999999' }, payload());
check('V-SSINPROC-FLOOR-FIRST', /SUELO DE MEMORIA/.test(ctxOf(r.pre[0])), JSON.stringify(r.pre).slice(0, 200));
check('V-SSINPROC-CARD-SECOND', /\[\/restart resume\]/.test(ctxOf(r.pre[1])), JSON.stringify(r.pre).slice(0, 300));
check('V-SSINPROC-FLOOR-LEFT-CHAIN', !r.chain.some((s) => s.script === FLOOR_STEP) && r.chain.length === CHAIN.length - 1,
  JSON.stringify(r.chain.map((s) => s.script)));
check('V-SSINPROC-DONE-FLAG-SET', process.env.PP_SESSION_CARDS_DONE === '1', String(process.env.PP_SESSION_CARDS_DONE));
check('V-SSINPROC-MARKER-CONSUMED-ONCE', !fs.existsSync(MARKER), 'marker still present');

// Control for 1: a healthy floor emits nothing, so the card is FIRST -- the floor slot is not padding.
writeMarker();
r = run({ CLAUDE_HOST_MEM_CRIT_MB: '1', CLAUDE_HOST_MEM_WARN_MB: '1' }, payload());
delete process.env.CLAUDE_HOST_MEM_WARN_MB;
const ctxs = r.pre.map(ctxOf).filter(Boolean);
check('V-SSINPROC-HEALTHY-FLOOR-SILENT', ctxs.length === 1 && /\[\/restart resume\]/.test(ctxs[0]), JSON.stringify(ctxs));

// 2. Floor switch off: the spawned step stays in the chain and no floor output is produced here.
r = run({ CLAUDE_HOST_MEM_FLOOR_INPROC: 'off', CLAUDE_HOST_MEM_CRIT_MB: '999999' }, payload());
check('V-SSINPROC-FLOOR-SWITCH-OFF', r.chain.some((s) => s.script === FLOOR_STEP)
  && !r.pre.some((o) => /SUELO DE MEMORIA/.test(ctxOf(o))), JSON.stringify(r.pre).slice(0, 200));

// 3. Cards switch off: no card, no flag, marker left for the hub.
writeMarker();
r = run({ CLAUDE_SESSION_CARDS_INPROC: 'off' }, payload());
check('V-SSINPROC-CARDS-SWITCH-OFF', !r.pre.some((o) => /restart resume/.test(ctxOf(o)))
  && process.env.PP_SESSION_CARDS_DONE !== '1' && fs.existsSync(MARKER), JSON.stringify(r.pre).slice(0, 200));

// 4. Any other chain is untouched (same array, nothing run).
r = run({}, payload(), 'UserPromptSubmit-chain');
check('V-SSINPROC-OTHER-CHAINS-UNTOUCHED', r.pre.length === 0 && r.chain === CHAIN, String(r.pre.length));

// 5. Rollover card on source=clear, ahead of the /restart card (the successor's order).
fs.writeFileSync(path.join(STATE, 'rollover', 'capsules', 'c1.json'),
  JSON.stringify({ session_cwd: CWD, obligations: [{ title: 'next thing' }] }));
// Floor forced quiet: this case measures CARD order, and a starved host's real floor warning
// (correctly) precedes every card.
r = run({ CLAUDE_HOST_MEM_CRIT_MB: '1', CLAUDE_HOST_MEM_WARN_MB: '1' }, payload({ source: 'clear' }));
delete process.env.CLAUDE_HOST_MEM_WARN_MB;
const cardText = r.pre.map(ctxOf).filter(Boolean).join('\n');
check('V-SSINPROC-ROLLOVER-BEFORE-RESTART', cardText.indexOf('ROLLOVER') === 0
  && cardText.indexOf('ROLLOVER') < cardText.indexOf('[/restart resume]'),
  'text=' + cardText.slice(0, 160) + ' pre=' + JSON.stringify(r.pre).slice(0, 200) + ' log='
  + (fs.readFileSync(path.join(tmp, 'pp-session-hub.log'), 'utf8').trim().split('\n').slice(-2).join(' | ')));
// Control: the same capsule on source=startup is not a crossing.
r = run({}, payload());
check('V-SSINPROC-ROLLOVER-ONLY-ON-CLEAR', !r.pre.map(ctxOf).join('').includes('ROLLOVER'), 'rollover on startup');

// 6. BOM-prefixed payload still parses: the floor's log row carries the session id (audit gap 5).
r = run({}, '﻿' + payload({ session_id: 'bbbb2222-3333' }));
let floorLog = {};
try { floorLog = JSON.parse(fs.readFileSync(path.join(tmp, '.claude', 'logs', 'host-memory-floor.json'), 'utf8')); } catch (_) { /* stays {} */ }
const last = (floorLog.recent || []).slice(-1)[0] || {};
check('V-SSINPROC-BOM-PAYLOAD-SID', last.sid === 'bbbb2222-3333', JSON.stringify(last));

// 7. Per-session instrument: every in-process run logs `cards DONE via=inproc sid=`.
const hubLog = fs.readFileSync(path.join(tmp, 'pp-session-hub.log'), 'utf8');
check('V-SSINPROC-CARDS-DONE-LINE', /cards DONE via=inproc sid=bbbb2222-3333 n=\d/.test(hubLog), hubLog.slice(-300));

// 9. End to end through the dispatcher's MAIN path (the prepend lives there, not in the lane function):
// the copied dispatcher runs as a real process against a stand-in hub that reports the handshake flag.
// Order in the emitted context must be floor < card < hub, and the hub must see PP_SESSION_CARDS_DONE.
fs.writeFileSync(path.join(PPH, 'session_start_hub.js'),
  "process.stdin.resume();process.stdin.on('end',()=>{process.stdout.write(JSON.stringify({continue:true,"
  + "additionalContext:'STANDIN-HUB flag='+(process.env.PP_SESSION_CARDS_DONE||'unset')}));process.exit(0);});");
// On a starved host the REAL 4 s chain deadline can reap even the stand-in (measured: 1.9 % free, hub=-1
// while floor and card arrived). So a run is judged for order/handshake only if the stand-in SETTLED
// (no CHAIN-DEADLINE-ABANDONED in the scratch error log); up to 3 attempts. An abandoned run is not
// thrown away: it is the case C1 exists for, and must still carry floor + card. 3/3 abandoned is
// INCONCLUSIVE and fails -- never a pass.
const { spawnSync } = require('child_process');
const ERRLOG = path.join(tmp, '.claude', 'logs', 'hook-dispatcher-errors.log');
const e2e = (extraEnv) => {
  const env = Object.assign({}, process.env, { CLAUDE_HOST_MEM_CRIT_MB: '999999' }, extraEnv || {});
  delete env.PP_SESSION_CARDS_DONE;
  let abandoned = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    writeMarker();
    try { fs.rmSync(ERRLOG, { force: true }); } catch (_) { /* absent */ }
    const p = spawnSync(process.execPath, [path.join(HOOKS, 'hook-dispatcher.js'), '--event=SessionStart-chain'],
      { input: payload({ session_id: 'cccc3333-4444' }), env, encoding: 'utf8', timeout: 60000, windowsHide: true });
    const o = String(p.stdout || '');
    let log = '';
    try { log = fs.readFileSync(ERRLOG, 'utf8'); } catch (_) { /* no errors logged */ }
    if (!/CHAIN-DEADLINE-ABANDONED/.test(log)) return { o, settled: true, attempt, abandoned };
    abandoned = abandoned || o;
  }
  return { o: '', settled: false, attempt: 3, abandoned };
};
let res = e2e();
if (res.settled) {
  const o = res.o;
  const iF = o.indexOf('SUELO DE MEMORIA'), iC = o.indexOf('[/restart resume]'), iH = o.indexOf('STANDIN-HUB');
  check('V-SSINPROC-E2E-ORDER', iF >= 0 && iC > iF && iH > iC, `floor=${iF} card=${iC} hub=${iH} out=${o.slice(0, 160)}`);
  check('V-SSINPROC-E2E-HANDSHAKE', o.includes('STANDIN-HUB flag=1'), o.slice(-160));
} else {
  check('V-SSINPROC-E2E-ORDER', false, 'INCONCLUSIVE: stand-in hub abandoned by the 4 s deadline in 3/3 attempts (host)');
}
if (res.abandoned !== null) {
  check('V-SSINPROC-E2E-CARDS-SURVIVE-ABANDON', /SUELO DE MEMORIA/.test(res.abandoned)
    && res.abandoned.includes('[/restart resume]') && !res.abandoned.includes('STANDIN-HUB'), res.abandoned.slice(0, 200));
} else {
  console.log('  NOTE V-SSINPROC-E2E-CARDS-SURVIVE-ABANDON not observed this run (no abandonment); C5 drill owns it');
}
// Control: cards switch off -> the hub child sees no flag (so a real hub would compose the cards).
res = e2e({ CLAUDE_SESSION_CARDS_INPROC: 'off' });
check('V-SSINPROC-E2E-NO-FLAG-WHEN-OFF', res.settled && res.o.includes('STANDIN-HUB flag=unset')
  && !res.o.includes('[/restart resume]'), res.settled ? res.o.slice(-200) : 'INCONCLUSIVE: 3/3 abandoned (host)');

// 10. C5 DRILL -- deterministic red pole: a stand-in hub that sleeps 8 s, twice the chain deadline,
// is ALWAYS abandoned, whatever the host's load. The cards and the floor must still be delivered,
// the abandonment must be logged naming the hub, and the cards line must carry its timings. The
// positive control is case 9 (a settled stand-in hub appears after the card, with the flag).
fs.writeFileSync(path.join(PPH, 'session_start_hub.js'),
  "setTimeout(()=>{process.stdout.write(JSON.stringify({continue:true,additionalContext:'SLOW-HUB'}));"
  + "process.exit(0);},8000);process.stdin.resume();");
writeMarker();
try { fs.rmSync(ERRLOG, { force: true }); } catch (_) { /* absent */ }
{
  const env = Object.assign({}, process.env, { CLAUDE_HOST_MEM_CRIT_MB: '999999' });
  delete env.PP_SESSION_CARDS_DONE;
  const p = spawnSync(process.execPath, [path.join(HOOKS, 'hook-dispatcher.js'), '--event=SessionStart-chain'],
    { input: payload({ session_id: 'dddd4444-5555' }), env, encoding: 'utf8', timeout: 60000, windowsHide: true });
  const o = String(p.stdout || '');
  let log = '';
  try { log = fs.readFileSync(ERRLOG, 'utf8'); } catch (_) { /* nothing logged */ }
  check('V-SSINPROC-DRILL-CARDS-SURVIVE-SLOW-HUB', /SUELO DE MEMORIA/.test(o) && o.includes('[/restart resume]')
    && !o.includes('SLOW-HUB'), o.slice(0, 200));
  check('V-SSINPROC-DRILL-ABANDON-LOGGED', /CHAIN-DEADLINE-ABANDONED/.test(log) && log.includes('session_start_hub.js')
    && log.includes('dddd4444-5555'), log.slice(-300));
  const hubLogNow = fs.readFileSync(path.join(tmp, 'pp-session-hub.log'), 'utf8');
  check('V-SSINPROC-DRILL-CARDS-TIMED', /cards DONE via=inproc sid=dddd4444-5555 n=1 ms=\d+ \(rollover=\d+ mission=\d+ restart=\d+ workstate=\d+\)/
    .test(hubLogNow), hubLogNow.trim().split('\n').slice(-2).join(' | '));
}

// 11. Before-pool attribution, driven deterministically: a chain whose clock started 5 s ago has no
// budget left, so runChain takes the before-pool branch every time. The line must name the
// in-process lane's halves (the 13:25:32 case read as "critical lane" with no critical step).
// Control: without inprocMs the line keeps its old shape (no attribution invented).
(async () => {
  const rest = CHAIN.filter((s) => s.script !== FLOOR_STEP && !s.critical);
  try { fs.rmSync(ERRLOG, { force: true }); } catch (_) { /* absent */ }
  await disp.runChain('SessionStart-chain', rest, payload({ session_id: 'eeee5555-6666' }),
    { startedAt: Date.now() - 5000, inprocMs: { floor: 11, cards: 4321 } });
  let log = '';
  try { log = fs.readFileSync(ERRLOG, 'utf8'); } catch (_) { /* nothing logged */ }
  check('V-SSINPROC-BEFORE-POOL-ATTRIBUTED', /before pool/.test(log)
    && log.includes('in-process lane (floor 11ms, cards 4321ms) + critical lane used'), log.slice(-300));
  try { fs.rmSync(ERRLOG, { force: true }); } catch (_) { /* absent */ }
  await disp.runChain('SessionStart-chain', rest, payload({ session_id: 'eeee5555-7777' }),
    { startedAt: Date.now() - 5000 });
  try { log = fs.readFileSync(ERRLOG, 'utf8'); } catch (_) { log = ''; }
  check('V-SSINPROC-BEFORE-POOL-PLAIN-WITHOUT-LANE', /before pool/.test(log) && !log.includes('in-process lane')
    && log.includes('critical lane used'), log.slice(-300));
  finish();
})();

function finish() {

// 8. The hub honours the flag (never both), and composes the cards without it (no gap).
writeMarker();
process.env.PP_SESSION_CARDS_DONE = '1';
const hub = require(path.join(PP, 'hooks', 'session_start_hub.js'));   // arms a hard exit; we exit first
const skipped = hub.hubCards(JSON.parse(payload()));
check('V-SSINPROC-HUB-SKIPS-WHEN-DONE', skipped === null && fs.existsSync(MARKER), String(skipped));
delete process.env.PP_SESSION_CARDS_DONE;
const composed = hub.hubCards(JSON.parse(payload())) || '';
check('V-SSINPROC-HUB-COMPOSES-WITHOUT-FLAG', composed.includes('[/restart resume]') && !fs.existsSync(MARKER),
  composed.slice(0, 120));

console.log('SSINPROC_PASS=' + pass + '/' + (pass + fail));
try { fs.rmSync(tmp, { recursive: true, force: true }); } catch (_) { /* scratch; the OS reaps it */ }
process.exit(fail ? 1 : 0);
}
