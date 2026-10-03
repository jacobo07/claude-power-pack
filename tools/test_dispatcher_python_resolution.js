#!/usr/bin/env node
'use strict';
// V-DISPATCHER-PY
//
// hook-dispatcher.js runs every chain step only if fs.existsSync(step.exe). On a
// POSIX host without CLAUDE_PY_EXE the Python interpreter used to resolve to the
// bare name 'python3', and existsSync('python3') is a relative-path check -- so
// EVERY Python step was skipped with "interpreter missing: python3", including the
// critical context-watchdog.py. Measured 2026-10-03 on GEX44 (Linux), where
// /usr/bin/python3 existed the whole time.
//
// This gate drives resolvePyExe() against a fake PATH, so it runs the same on a
// Windows or a Linux host. The regression case is the absolute-path assertion; the
// controls prove the resolver can return each of its other answers.

const fs = require('fs');
const os = require('os');
const path = require('path');

const { resolvePyExe } = require(path.resolve(__dirname, '..', 'hooks', 'hook-dispatcher.js'));

let pass = 0, fail = 0;
const ok = (id, ev) => { pass++; console.log('  OK   ' + id + '  ' + ev); };
const no = (id, ev) => { fail++; console.log('  FAIL ' + id + '  ' + ev); };
const check = (id, cond, ev) => (cond ? ok : no)(id, ev);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dispatcher-py-'));
const emptyDir = path.join(tmp, 'empty');
const binDir = path.join(tmp, 'bin');
const noHome = path.join(tmp, 'home-without-python');
fs.mkdirSync(emptyDir); fs.mkdirSync(binDir); fs.mkdirSync(noHome);
for (const name of ['python3', 'python.exe']) {
  const p = path.join(binDir, name);
  fs.writeFileSync(p, '#!/bin/sh\n');
  fs.chmodSync(p, 0o755);
}
const PATH = [emptyDir, binDir].join(path.delimiter);

if (typeof resolvePyExe !== 'function') {
  no('V-DISPATCHER-PY-EXPORTED', 'resolvePyExe is not exported by hook-dispatcher.js');
} else {
  ok('V-DISPATCHER-PY-EXPORTED', 'resolvePyExe exported');

  // Regression: a PATH hit must come back ABSOLUTE, or runChain's existsSync skips it.
  const posix = resolvePyExe({ env: { PATH }, platform: 'linux', home: noHome });
  check('V-DISPATCHER-PY-POSIX-ABSOLUTE', path.isAbsolute(posix) && fs.existsSync(posix),
    'linux PATH hit -> ' + posix);
  check('V-DISPATCHER-PY-POSIX-PICKS-PYTHON3', path.basename(posix) === 'python3',
    'skips the empty dir, takes python3 from the second PATH entry');

  const win = resolvePyExe({ env: { Path: PATH }, platform: 'win32', home: noHome });
  check('V-DISPATCHER-PY-WIN-PATH', path.isAbsolute(win) && path.basename(win) === 'python.exe',
    'win32 PATH hit (Path spelling) -> ' + win);

  // Controls: each other answer is reachable.
  check('V-DISPATCHER-PY-EXPLICIT-WINS',
    resolvePyExe({ env: { CLAUDE_PY_EXE: '/opt/py/bin/python3', PATH }, platform: 'linux', home: noHome }) === '/opt/py/bin/python3',
    'CLAUDE_PY_EXE beats PATH');

  const home = path.join(tmp, 'home-with-python');
  const installed = path.join(home, 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe');
  fs.mkdirSync(path.dirname(installed), { recursive: true });
  fs.writeFileSync(installed, ''); fs.chmodSync(installed, 0o755);
  check('V-DISPATCHER-PY-HOME-INSTALL', resolvePyExe({ env: { PATH }, platform: 'win32', home }) === installed,
    'home-dir install beats PATH');

  // Honest miss: nothing on PATH -> the bare name, so the "interpreter missing" log is true.
  check('V-DISPATCHER-PY-MISS-IS-BARE', resolvePyExe({ env: { PATH: emptyDir }, platform: 'linux', home: noHome }) === 'python3',
    'no interpreter anywhere -> bare name');

  // A directory named python3 is not an interpreter.
  const dirOnly = path.join(tmp, 'dironly');
  fs.mkdirSync(path.join(dirOnly, 'python3'), { recursive: true });
  check('V-DISPATCHER-PY-DIR-IS-NOT-EXE', resolvePyExe({ env: { PATH: dirOnly }, platform: 'linux', home: noHome }) === 'python3',
    'a directory on PATH named python3 is skipped');
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(`DISPATCHER_PY_PASS=${pass}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
