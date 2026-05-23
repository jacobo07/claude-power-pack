// <module>/lib/registry.js
const fs = require('fs');
const os = require('os');
const path = require('path');

let ROOT = path.join(os.homedir(), '.claude', 'lazarus');
function _setRoot(p) { ROOT = p; }
function _file() { return path.join(ROOT, 'terminal_registry.json'); }

function readAll() {
  try {
    const j = JSON.parse(fs.readFileSync(_file(), 'utf8'));
    return Array.isArray(j.rows) ? j.rows : [];
  } catch (_) { return []; }
}

function _writeAtomic(rows) {
  fs.mkdirSync(ROOT, { recursive: true });
  const tmp = _file() + '.tmp.' + process.pid;
  fs.writeFileSync(tmp, JSON.stringify({ version: 4, rows }, null, 2));
  fs.renameSync(tmp, _file());
}

function upsert(row) {
  const rows = readAll().filter(r => r.slot !== row.slot);
  rows.push({ ...row, ts: new Date().toISOString() });
  _writeAtomic(rows);
}

function snapshotPrereboot() {
  fs.mkdirSync(ROOT, { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'terminal_registry.prereboot.json'),
    JSON.stringify({ version: 4, rows: readAll() }, null, 2));
}

module.exports = { readAll, upsert, snapshotPrereboot, _setRoot };
