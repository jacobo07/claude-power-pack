'use strict';
/**
 * V-SELFHEAL-* -- drills for hooks/wrapper-selfheal.js.
 *
 * Both poles on every clause. The dispatch is INJECTED, so no drill ever
 * rewrites the Owner's real settings.json; the subject is the decision, and
 * the decision is what the mutation drill breaks.
 *
 * The wiring assertion deliberately matches the require CALL and not the
 * filename: this estate has already shipped a wiring check that a mention in a
 * neighbouring assignment satisfied, and its 11/11 green was on screen while
 * the invocation was gone.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

const MOD = path.join(__dirname, '..', 'wrapper-selfheal.js');
const DISPATCHER = path.join(__dirname, '..', 'hook-dispatcher.js');
const { selfHeal, COOLDOWN_MS } = require(MOD);

let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log(`PASS ${id}: ${ev}`); };
const no = (id, ev) => { fail++; console.log(`FAIL ${id}: ${ev}`); };

const CLEAN = JSON.stringify({
  hooks: {
    UserPromptSubmit: [{ hooks: [{ type: 'command', command: 'node C:\\x\\hook-dispatcher.js --event UserPromptSubmit' }] }],
  },
}, null, 2);

// Assembled rather than written literally: a file carrying the infected shape
// is the thing the detector hunts, and it should not sit at rest in the tree.
const WRAP = 'conhost.exe' + ' --headless ' + 'cmd.exe /d /c C:\\Users\\U\\.orca\\agent-hooks\\claude-hook.cmd';
const INFECTED = JSON.stringify({
  hooks: {
    PreToolUse: [{ matcher: '*', hooks: [{ type: 'command', command: WRAP }] }],
  },
}, null, 2);

function world(name) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'selfheal-' + name + '-'));
  const settings = path.join(root, 'settings.json');
  const stateDir = path.join(root, 'state');
  const calls = [];
  const base = {
    settings, stateDir, fixer: path.join(root, 'fixer.py'),
    dispatch: (cmd, args) => calls.push({ cmd, args }),
  };
  return { root, settings, stateDir, calls, base };
}

// Two writes in the same millisecond can share an mtime, which would make a
// genuine change read as unchanged and pass the wrong case for the wrong
// reason. Every rewrite moves mtime explicitly.
let tick = 0;
function put(file, body) {
  fs.writeFileSync(file, body, 'utf8');
  tick += 5;
  const when = new Date(Date.now() + tick * 1000);
  fs.utimesSync(file, when, when);
}

// --- 1. clean registry: no dispatch -----------------------------------------
{
  const w = world('clean');
  put(w.settings, CLEAN);
  const r = selfHeal(w.base);
  if (r.status === 'clean' && w.calls.length === 0) ok('V-SELFHEAL-CLEAN', 'clean registry -> no repair dispatched');
  else no('V-SELFHEAL-CLEAN', JSON.stringify(r) + ' calls=' + w.calls.length);
}

// --- 2. infected registry: the fixer is dispatched, with --apply ------------
{
  const w = world('infected');
  put(w.settings, INFECTED);
  const r = selfHeal(w.base);
  const c = w.calls[0];
  if (r.status === 'dispatched' && r.allocator === 'conhost-headless'
      && w.calls.length === 1 && c.args[0] === w.base.fixer && c.args.includes('--apply')) {
    ok('V-SELFHEAL-DETECTS', 'infected -> dispatched ' + path.basename(c.args[0]) + ' --apply');
  } else no('V-SELFHEAL-DETECTS', JSON.stringify(r) + ' calls=' + JSON.stringify(w.calls));
}

// --- 3. the cheap path: an unmoved file is not re-scanned -------------------
{
  const w = world('unchanged');
  put(w.settings, CLEAN);
  selfHeal(w.base);
  const r = selfHeal(w.base);
  if (r.status === 'unchanged') ok('V-SELFHEAL-UNCHANGED', 'second call on an unmoved file short-circuits');
  else no('V-SELFHEAL-UNCHANGED', JSON.stringify(r));
}

// --- 4. a moved file IS re-scanned (the re-infection case) ------------------
{
  const w = world('rescan');
  put(w.settings, CLEAN);
  const first = selfHeal(w.base);
  put(w.settings, INFECTED);
  const second = selfHeal(w.base);
  if (first.status === 'clean' && second.status === 'dispatched' && w.calls.length === 1) {
    ok('V-SELFHEAL-RESCANS', 'clean -> re-infected -> repair dispatched on the next event');
  } else no('V-SELFHEAL-RESCANS', JSON.stringify(first) + ' then ' + JSON.stringify(second));
}

// --- 4b. THE SHAPE THAT ACTUALLY EXISTS: wrapper split across command+args --
// Regression, measured on this guard's first live run. Claude Code stores the
// executable and its arguments in separate fields, so `conhost` and
// `--headless` never share a string and a raw-text pattern sees nothing. The
// guard called eleven wrapped events healthy while the Owner's screen cleared
// on every tool call.
{
  const w = world('structured');
  put(w.settings, JSON.stringify({
    hooks: {
      PreToolUse: [{
        matcher: '*',
        hooks: [{
          type: 'command',
          command: 'C:\\WINDOWS\\System32\\' + 'conhost' + '.exe',
          args: ['--headless', 'C:\\WINDOWS\\System32\\cmd.exe', '/d', '/c',
                 '%USERPROFILE%\\.orca\\agent-hooks\\claude-hook.cmd'],
        }],
      }],
    },
  }, null, 2));
  const r = selfHeal(w.base);
  if (r.status === 'dispatched' && w.calls.length === 1) {
    ok('V-SELFHEAL-STRUCTURED-ARGS', 'a wrapper split across command+args is detected');
  } else no('V-SELFHEAL-STRUCTURED-ARGS', JSON.stringify(r) + ' -- the live shape must not read as healthy');
}

// --- 4c. a registry that does not parse is scanned as text, never called clean
{
  const w = world('unparseable');
  put(w.settings, '{ "hooks": { broken ' + WRAP);
  const r = selfHeal(w.base);
  if (r.status === 'dispatched') ok('V-SELFHEAL-RAW-FALLBACK', 'unparseable registry falls back to a text scan');
  else no('V-SELFHEAL-RAW-FALLBACK', JSON.stringify(r));
}

// --- 5. cooldown: a second infection inside the window does not re-dispatch --
{
  const w = world('cooldown');
  put(w.settings, INFECTED);
  const t0 = 1000000;
  selfHeal(Object.assign({}, w.base, { now: () => t0 }));
  put(w.settings, INFECTED + '\n');
  const r = selfHeal(Object.assign({}, w.base, { now: () => t0 + COOLDOWN_MS - 1 }));
  if (r.status === 'cooling' && w.calls.length === 1) ok('V-SELFHEAL-COOLDOWN', 'one dispatch per cooldown window');
  else no('V-SELFHEAL-COOLDOWN', JSON.stringify(r) + ' calls=' + w.calls.length);
}

// --- 6. ...and it releases once the window passes ---------------------------
{
  const w = world('cooldown-release');
  put(w.settings, INFECTED);
  const t0 = 2000000;
  selfHeal(Object.assign({}, w.base, { now: () => t0 }));
  put(w.settings, INFECTED + '\n');
  const r = selfHeal(Object.assign({}, w.base, { now: () => t0 + COOLDOWN_MS + 1 }));
  if (r.status === 'dispatched' && w.calls.length === 2) ok('V-SELFHEAL-COOLDOWN-RELEASES', 'still infected after the window -> dispatched again');
  else no('V-SELFHEAL-COOLDOWN-RELEASES', JSON.stringify(r) + ' calls=' + w.calls.length);
}

// --- 7. a BOM is not a finding, and must not blind the detector -------------
{
  const w = world('bom');
  put(w.settings, '\ufeff' + INFECTED);
  const r = selfHeal(w.base);
  if (r.status === 'dispatched') ok('V-SELFHEAL-BOM', 'UTF-8 BOM does not hide the wrapper');
  else no('V-SELFHEAL-BOM', JSON.stringify(r));
}

// --- 8. negative control: the detector is not just matching "conhost" -------
{
  const w = world('mention');
  put(w.settings, JSON.stringify({
    hooks: { Stop: [{ hooks: [{ type: 'command', command: 'node check.js --note "conhost wrappers are banned"' }] }] },
  }, null, 2));
  const r = selfHeal(w.base);
  if (r.status === 'clean' && w.calls.length === 0) ok('V-SELFHEAL-NO-FALSE-POSITIVE', 'a mention of conhost without --headless is not an infection');
  else no('V-SELFHEAL-NO-FALSE-POSITIVE', JSON.stringify(r));
}

// --- 9. an allocator it cannot repair is REPORTED, never silently dispatched -
{
  const w = world('unfixable');
  put(w.settings, JSON.stringify({
    hooks: { Stop: [{ hooks: [{ type: 'command', command: 'cmd.exe /c start C:\\x\\hook.cmd' }] }] },
  }, null, 2));
  const r = selfHeal(w.base);
  if (r.status === 'unfixable' && r.allocator === 'cmd-start' && w.calls.length === 0) {
    ok('V-SELFHEAL-UNFIXABLE-REPORTED', 'a new allocator shape is named, not mistaken for healthy');
  } else no('V-SELFHEAL-UNFIXABLE-REPORTED', JSON.stringify(r));
}

// --- 9b. the estate's own zero-flash pattern is NOT an allocator ------------
// Regression: -WindowStyle was in ALLOCATORS and matched the real, healthy
// settings.json on this guard's first live run, which made `clean` unreachable
// on this host. A hidden window is how you AVOID the defect, not the defect.
{
  const w = world('windowstyle');
  put(w.settings, JSON.stringify({
    hooks: { SessionStart: [{ hooks: [{ type: 'command', command: 'powershell -NoProfile -WindowStyle Hidden -File C:\\x\\h.ps1' }] }] },
  }, null, 2));
  const r = selfHeal(w.base);
  if (r.status === 'clean' && w.calls.length === 0) ok('V-SELFHEAL-HIDDEN-IS-NOT-ALLOCATOR', '-WindowStyle Hidden reads as healthy');
  else no('V-SELFHEAL-HIDDEN-IS-NOT-ALLOCATOR', JSON.stringify(r));
}

// --- 9c. the live registry, as it actually is, must read as clean -----------
// The drills above all use fixtures I chose. This one asks the real file the
// guard will meet on every event, so a pattern that is wrong about THIS host
// cannot pass by being right about my fixtures.
{
  const live = path.join(process.env.USERPROFILE || os.homedir(), '.claude', 'settings.json');
  if (!fs.existsSync(live)) {
    no('V-SELFHEAL-LIVE-READS-CLEAN', 'HARNESS: no live settings.json to read');
  } else {
    const w = world('live');
    put(w.settings, fs.readFileSync(live, 'utf8'));
    const r = selfHeal(w.base);
    if (r.status === 'clean') ok('V-SELFHEAL-LIVE-READS-CLEAN', 'the real registry reads clean (copy, never the original)');
    else no('V-SELFHEAL-LIVE-READS-CLEAN', 'the live registry reads ' + JSON.stringify(r)
      + ' -- either it is infected, or the detector is wrong about this host');
  }
}

// --- 10. fail-open: a missing settings.json is a no-op, never a throw -------
{
  const w = world('missing');
  let threw = null;
  let r = null;
  try { r = selfHeal(w.base); } catch (e) { threw = e; }
  if (!threw && r.status === 'no-settings' && w.calls.length === 0) ok('V-SELFHEAL-FAILOPEN', 'no settings.json -> no-settings verdict, no throw');
  else no('V-SELFHEAL-FAILOPEN', threw ? 'threw ' + threw.message : JSON.stringify(r));
}

// --- 11. a corrupt stamp costs one scan, never a crash ----------------------
{
  const w = world('badstamp');
  put(w.settings, CLEAN);
  fs.mkdirSync(w.stateDir, { recursive: true });
  fs.writeFileSync(path.join(w.stateDir, 'wrapper-selfheal.json'), '{not json', 'utf8');
  let threw = null, r = null;
  try { r = selfHeal(w.base); } catch (e) { threw = e; }
  if (!threw && r.status === 'clean') ok('V-SELFHEAL-BAD-STAMP', 'unparseable stamp -> rescan, no throw');
  else no('V-SELFHEAL-BAD-STAMP', threw ? 'threw ' + threw.message : JSON.stringify(r));
}

// --- 12. WIRED: assert the require CALL, not a mention of the filename ------
{
  let src = '';
  try { src = fs.readFileSync(DISPATCHER, 'utf8'); } catch (_) { /* reported below */ }
  const called = /require\(\s*['"]\.\/wrapper-selfheal\.js['"]\s*\)\s*\.\s*selfHeal\s*\(/.test(src);
  const mentioned = src.includes('wrapper-selfheal.js');
  if (called) ok('V-SELFHEAL-WIRED', 'hook-dispatcher.js invokes selfHeal(), not merely names the file');
  else no('V-SELFHEAL-WIRED', mentioned
    ? 'the filename appears but selfHeal() is never CALLED -- a mention is not an invocation'
    : 'hook-dispatcher.js does not reference the guard at all');
}

console.log(`SELFHEAL_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
