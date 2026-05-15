// <module>/mark.js
// Prefixes the `summary` record of given sessions in-place. NEVER renames/moves files.
const fs = require('fs');
const path = require('path');
const RE = /^🟡 \[PRE-REBOOT \d\d:\d\d\] /;

function _rewrite(dir, sid, fn) {
  const f = path.join(dir, sid + '.jsonl');
  if (!fs.existsSync(f)) return;
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  let changed = false;
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    let o; try { o = JSON.parse(lines[i]); } catch (_) { continue; }
    if (o.type === 'summary' && typeof o.summary === 'string') {
      const next = fn(o.summary);
      if (next !== o.summary) { o.summary = next; lines[i] = JSON.stringify(o); changed = true; }
      break;
    }
  }
  if (changed) {
    // In-place content swap on the SAME file handle — preserves file identity
    // (inode/NTFS file-index). No tmp, no rename, no shadow basename: this is
    // strictly stronger than the v3 contract and keeps the *.jsonl untouched
    // by name. fd-truncate+write keeps the OS file object stable.
    const fd = fs.openSync(f, 'r+');
    try {
      const buf = Buffer.from(lines.join('\n'), 'utf8');
      fs.ftruncateSync(fd, 0);
      fs.writeSync(fd, buf, 0, buf.length, 0);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
  }
}
function mark(dir, sids, when) {
  const hh = String(when.getHours()).padStart(2, '0');
  const mm = String(when.getMinutes()).padStart(2, '0');
  const tag = `🟡 [PRE-REBOOT ${hh}:${mm}] `;
  sids.forEach(s => _rewrite(dir, s, v => RE.test(v) ? v : tag + v));
}
function unmark(dir, sids) {
  sids.forEach(s => _rewrite(dir, s, v => v.replace(RE, '')));
}
module.exports = { mark, unmark };
