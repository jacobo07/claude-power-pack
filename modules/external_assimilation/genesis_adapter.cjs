'use strict';
// Adapter for vendor/genesis-suite (MIT) and vendor/context-budget (MIT). One entry point:
// one JSON request on stdin, one JSON reply on stdout. See vendor/README.md Rule 3.
//
// Request:  {"package":"genesis-suite"|"context-budget", "module":"<export key>",
//            "fn":"<export name>", "args":[...],
//            "factory":{"fn":"<export name>","args":[...]}?, "method":"<name>"?}
//   - without factory: calls modules[module][fn](...args)
//   - with factory:    obj = modules[module][factory.fn](...factory.args); obj[method](...args)
// Reply:    {"outcome":"OK","value":<json>} | {"outcome":"SUBJECT_INVALID","error":...}
//           | {"outcome":"BRIDGE_FAILED","error":...}
// SUBJECT_INVALID = the upstream function ran and refused its input (it threw).
// BRIDGE_FAILED   = the call could not be made (engine, unknown export, bad request).
// Only exported functions are callable; nothing is evaluated.
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', 'vendor');
const PACKAGES = {
  'genesis-suite': () => require(path.join(ROOT, 'genesis-suite', 'index.cjs')).modules,
  'context-budget': () => ({ contextBudget: require(path.join(ROOT, 'context-budget', 'lib', 'context-budget.cjs')) }),
};

function engineOk(range, version) {
  // Supports the "^a.b.c || ^x.y.z" shape the vendored packages declare.
  const v = version.replace(/^v/, '').split('.').map(Number);
  return String(range).split('||').some((part) => {
    const m = part.trim().match(/^\^(\d+)\.(\d+)\.(\d+)$/) || part.trim().match(/^>=(\d+)(?:\.(\d+))?(?:\.(\d+))?$/);
    if (!m) return false;
    const r = [Number(m[1]), Number(m[2] || 0), Number(m[3] || 0)];
    if (part.trim().startsWith('>=')) return v[0] > r[0] || (v[0] === r[0] && (v[1] > r[1] || (v[1] === r[1] && v[2] >= r[2])));
    return v[0] === r[0] && (v[1] > r[1] || (v[1] === r[1] && v[2] >= r[2]));
  });
}

function toJson(value) {
  return JSON.parse(JSON.stringify(value, (_k, v) => (typeof v === 'bigint' ? String(v) : v)));
}

async function handle(req) {
  const pkgName = req.package || 'genesis-suite';
  if (!PACKAGES[pkgName]) return { outcome: 'BRIDGE_FAILED', error: `unknown package ${pkgName}` };
  const meta = require(path.join(ROOT, pkgName, 'package.json'));
  const range = meta.engines && meta.engines.node;
  if (range && !engineOk(range, process.version)) {
    return { outcome: 'BRIDGE_FAILED', error: `engine: node ${process.version} outside ${range}`, reason: 'engine' };
  }
  const mods = PACKAGES[pkgName]();
  const mod = mods[req.module];
  if (!mod) return { outcome: 'BRIDGE_FAILED', error: `unknown module ${req.module}` };
  let target = mod;
  let fnName = req.fn;
  if (req.factory) {
    const f = mod[req.factory.fn];
    if (typeof f !== 'function') return { outcome: 'BRIDGE_FAILED', error: `unknown factory ${req.factory.fn}` };
    try {
      target = await f(...(req.factory.args || []));
    } catch (e) {
      return { outcome: 'SUBJECT_INVALID', error: String((e && e.message) || e), stage: 'factory' };
    }
    fnName = req.method;
  }
  const fn = target && target[fnName];
  if (typeof fn !== 'function') {
    if (!req.factory && fnName in mod) return { outcome: 'OK', value: toJson(mod[fnName]) };
    return { outcome: 'BRIDGE_FAILED', error: `not callable: ${req.module}.${fnName}` };
  }
  try {
    const value = await fn.apply(target, req.args || []);
    return { outcome: 'OK', value: toJson(value === undefined ? null : value) };
  } catch (e) {
    return { outcome: 'SUBJECT_INVALID', error: String((e && e.message) || e) };
  }
}

function main() {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => { raw += c; });
  process.stdin.on('end', async () => {
    let reply;
    try {
      const req = JSON.parse(raw.replace(/^﻿/, ''));
      reply = await handle(req);
    } catch (e) {
      reply = { outcome: 'BRIDGE_FAILED', error: `bad request: ${String((e && e.message) || e)}` };
    }
    process.stdout.write(JSON.stringify(reply));
  });
}

module.exports = { handle, engineOk };
if (require.main === module) main();
