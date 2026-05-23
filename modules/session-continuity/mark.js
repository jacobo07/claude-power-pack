// <module>/mark.js
// Prefixes the `summary` record of given sessions via atomic same-name replace
// (tmp + rename onto the SAME <id>.jsonl basename). NEVER moves to a shadow name.
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
    // Atomic same-name replace: write a sibling tmp then rename it onto the
    // SAME basename <id>.jsonl. This is NOT a shadow rename (the final name
    // stays <id>.jsonl, so the native picker still lists it) and it closes the
    // zero-byte data-loss window that an in-place fd-truncate+write would open
    // if the process died mid-write. Same pattern as lib/registry.js and the
    // spec's "Atomic tmp+rename" data-flow. Same-volume rename is atomic.
    const tmp = f + '.mtmp.' + process.pid;
    fs.writeFileSync(tmp, lines.join('\n'));
    fs.renameSync(tmp, f); // SAME basename <id>.jsonl → not a shadow; atomic same-volume
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
