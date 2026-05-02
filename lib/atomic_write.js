// atomic_write.js — Node port of lib/atomic_write.py (BL-0014, MC-SYS-32).
//
// Same hardening goals as the Python version:
//   - Windows ERROR_SHARING_VIOLATION (EBUSY/EPERM with errno -4082 / WIN32:32)
//     when AV/indexer/Cursor holds the target — retry with exponential backoff.
//   - Partial-write torn files when the hook process is killed mid-write —
//     write to <target>.tmp.<pid>.<rand>, fsync, then atomic rename.
//   - Cross-process races between concurrent Cursor windows on shared files
//     (heartbeats, pending_resume.txt, last_session.json, kg-sync batches).
//
// API (all sync — hooks are short-lived processes):
//   atomicWriteBytes(filePath, buffer)
//   atomicWriteText(filePath, text)
//   atomicWriteJson(filePath, obj, indent = 2)
//   atomicAppendJsonl(filePath, row)
//
// CLI self-test:
//   node lib/atomic_write.js --self-test
//
// Module is dual-mode: require()-able and runnable.

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DEFAULT_MAX_RETRIES = 5;
const INITIAL_BACKOFF_MS = 25;

function tmpSibling(target) {
  const dir = path.dirname(target);
  const base = path.basename(target);
  const rand = crypto.randomBytes(4).toString('hex');
  return path.join(dir, `${base}.tmp.${process.pid}.${rand}`);
}

function sleepSync(ms) {
  // Block the event loop briefly. Acceptable in hooks (<5s total budget).
  const end = Date.now() + ms;
  // Atomics.wait would be cleaner but requires SharedArrayBuffer. Buffer-spin is fine here.
  while (Date.now() < end) { /* spin */ }
}

function isSharingViolation(err) {
  if (!err) return false;
  // Windows: errno -4048 (EPERM), -4082 (EBUSY), or err.code 'EPERM'/'EBUSY'.
  // Posix: 'EBUSY' is rare on rename. Be permissive: any of these triggers retry.
  return err.code === 'EPERM' || err.code === 'EBUSY' || err.code === 'EACCES';
}

function atomicWriteBytes(filePath, buffer, options) {
  const opts = options || {};
  const maxRetries = opts.maxRetries || DEFAULT_MAX_RETRIES;
  const target = path.resolve(filePath);
  const dir = path.dirname(target);

  fs.mkdirSync(dir, { recursive: true });

  const tmp = tmpSibling(target);
  // O_WRONLY | O_CREAT | O_EXCL — refuse to clobber any existing tmp sibling.
  // Node's fs.openSync uses binary mode by default on Windows (no \n -> \r\n
  // translation), unlike Python's os.open which does.
  const fd = fs.openSync(tmp, 'wx');
  try {
    fs.writeSync(fd, buffer, 0, buffer.length, 0);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }

  let lastErr = null;
  let backoff = INITIAL_BACKOFF_MS;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      fs.renameSync(tmp, target);
      return;
    } catch (err) {
      lastErr = err;
      if (isSharingViolation(err)) {
        sleepSync(backoff);
        backoff *= 2;
        continue;
      }
      // Other errors (ENOENT, EISDIR, etc.) — fail fast, clean up tmp.
      try { fs.unlinkSync(tmp); } catch { /* ok */ }
      throw err;
    }
  }
  try { fs.unlinkSync(tmp); } catch { /* ok */ }
  const e = new Error(`atomic_write: gave up after ${maxRetries} retries on ${target}`);
  e.cause = lastErr;
  throw e;
}

function atomicWriteText(filePath, text, options) {
  atomicWriteBytes(filePath, Buffer.from(text, 'utf8'), options);
}

function atomicWriteJson(filePath, obj, indent, options) {
  if (indent === undefined) indent = 2;
  atomicWriteText(filePath, JSON.stringify(obj, null, indent), options);
}

function atomicAppendJsonl(filePath, row, options) {
  const target = path.resolve(filePath);
  let existing = Buffer.alloc(0);
  if (fs.existsSync(target)) {
    existing = fs.readFileSync(target);
    if (existing.length && existing[existing.length - 1] !== 0x0a /* \n */) {
      existing = Buffer.concat([existing, Buffer.from('\n', 'utf8')]);
    }
  }
  const line = Buffer.from(JSON.stringify(row) + '\n', 'utf8');
  atomicWriteBytes(target, Buffer.concat([existing, line]), options);
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------

function selfTest() {
  const os = require('os');
  const failures = [];
  const tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), 'atomic-write-test-'));
  try {
    const f1 = path.join(tmpdir, 'a.txt');
    atomicWriteText(f1, 'hello\n');
    if (fs.readFileSync(f1, 'utf8') !== 'hello\n') failures.push('text round-trip mismatch');

    const f2 = path.join(tmpdir, 'nested', 'deep', 'b.json');
    atomicWriteJson(f2, { k: 1, v: 'x' });
    const parsed = JSON.parse(fs.readFileSync(f2, 'utf8'));
    if (parsed.k !== 1 || parsed.v !== 'x') failures.push('json round-trip mismatch');

    const f3 = path.join(tmpdir, 'ledger.jsonl');
    atomicAppendJsonl(f3, { row: 1 });
    atomicAppendJsonl(f3, { row: 2 });
    atomicAppendJsonl(f3, { row: 3 });
    const lines = fs.readFileSync(f3, 'utf8').split('\n').filter(Boolean);
    if (lines.length !== 3) {
      failures.push(`jsonl line count mismatch: got ${lines.length} lines, expected 3 (raw=${JSON.stringify(lines)})`);
    } else {
      const rows = lines.map(l => JSON.parse(l).row);
      if (rows[0] !== 1 || rows[1] !== 2 || rows[2] !== 3) failures.push(`jsonl order mismatch: ${JSON.stringify(rows)}`);
    }

    const leftover = fs.readdirSync(tmpdir, { recursive: true })
      .filter(p => p.includes('.tmp.'));
    if (leftover.length) failures.push(`tmp leftover after success: ${JSON.stringify(leftover)}`);

    const f4 = path.join(tmpdir, 'sub', 'c.txt');
    atomicWriteText(f4, 'first\n');
    atomicWriteText(f4, 'second\n');
    if (fs.readFileSync(f4, 'utf8') !== 'second\n') failures.push('overwrite mismatch');
  } finally {
    try { fs.rmSync(tmpdir, { recursive: true, force: true }); } catch { /* ok */ }
  }

  if (failures.length) {
    for (const f of failures) process.stderr.write(`FAIL: ${f}\n`);
    process.exit(1);
  }
  process.stdout.write('atomic_write.js self-test: PASS (4/4)\n');
  process.exit(0);
}

if (require.main === module) {
  if (process.argv.includes('--self-test')) selfTest();
  else process.stdout.write('Usage: node lib/atomic_write.js --self-test\n');
} else {
  module.exports = {
    atomicWriteBytes,
    atomicWriteText,
    atomicWriteJson,
    atomicAppendJsonl,
  };
}
