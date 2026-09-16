#!/usr/bin/env node
/**
 * Trace Flusher — Stop hook
 *
 * On session end: reads all pending trace JSONL files,
 * POSTs them to the VPS Agent Lightning trace receiver,
 * and cleans up on success.
 *
 * On failure: keeps buffer for next session (resilient).
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const os = require('os');

const TRACES_DIR = path.join(os.homedir(), '.claude', 'traces');
const VPS_HOST = process.env.TRACE_VPS_HOST || '204.168.166.63';
const VPS_PORT = process.env.TRACE_VPS_PORT || '9878';
const VPS_URL = `http://${VPS_HOST}:${VPS_PORT}/api/v1/traces/ingest`;
const FLUSH_TIMEOUT = 5000; // 5 seconds — keep Stop hook fast
const HARD_DEADLINE_MS = 10000; // hard ceiling — applied via Promise.race in both modes

// NOTE: the old top-level setTimeout(...process.exit) has been moved into the CLI
// entry block below. When this file is required as a module (by hook-dispatcher.js),
// blindly exiting the parent process would kill sibling hooks.

function getApiKey() {
  return process.env.OMNICAPTURE_API_KEY || '';
}

// BOUNDED READ (2026-09-15). MEASURED: with the VPS unreachable the buffer had
// grown to 394,476 traces, and this function -- fully SYNCHRONOUS -- spent 37 s
// parsing them on the interactive Stop boundary. Neither HARD_DEADLINE_MS nor
// the circuit breaker could prevent it (see runInner), so the cost grew without
// limit every session the VPS stayed down. That unbounded growth is why the
// freeze got progressively worse across every repo.
//
// The cap is on BYTES READ, not on traces parsed, because the byte count is
// knowable from statSync BEFORE paying to parse anything. Partial flushing is
// already correct by construction: `files` only ever lists files whose contents
// were actually read, and the caller deletes exactly that list on success, so a
// capped pass ships a prefix of the buffer and the remainder goes next time.
// Oldest-first keeps the backlog draining in order instead of starving the tail.
const MAX_FLUSH_BYTES = 8 * 1024 * 1024;

function readAllPending() {
  const traces = [];
  const files = [];

  try {
    if (!fs.existsSync(TRACES_DIR)) return { traces, files };

    const candidates = [];
    for (const entry of fs.readdirSync(TRACES_DIR)) {
      if (entry.startsWith('pending_') && entry.endsWith('.jsonl')) {
        const fullPath = path.join(TRACES_DIR, entry);
        try { candidates.push({ fullPath, st: fs.statSync(fullPath) }); }
        catch { /* vanished between readdir and stat */ }
      }
    }
    candidates.sort((a, b) => a.st.mtimeMs - b.st.mtimeMs);

    let budget = MAX_FLUSH_BYTES;
    for (const { fullPath, st } of candidates) {
      // Always admit the first file even if it alone exceeds the budget, or a
      // single oversized file would wedge the queue forever and never drain.
      if (budget < st.size && files.length > 0) break;
      try {
        const content = fs.readFileSync(fullPath, 'utf8');
        const lines = content.split('\n').filter(l => l.trim());
        for (const line of lines) {
          try {
            traces.push(JSON.parse(line));
          } catch { /* skip malformed lines */ }
        }
        files.push(fullPath);
        budget -= st.size;
      } catch { /* skip unreadable files */ }
    }
  } catch { /* traces dir doesn't exist */ }

  return { traces, files };
}

function postTraces(traces) {
  return new Promise((resolve, reject) => {
    const apiKey = getApiKey();
    if (!apiKey) {
      resolve(false); // No API key — skip flush, keep buffer
      return;
    }

    const url = new URL(VPS_URL);
    const body = JSON.stringify({ traces });

    const req = http.request({
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: FLUSH_TIMEOUT
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(res.statusCode >= 200 && res.statusCode < 300));
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
    req.write(body);
    req.end();
  });
}

function cleanupSequenceFiles() {
  try {
    const entries = fs.readdirSync(TRACES_DIR);
    for (const entry of entries) {
      if (entry.startsWith('seq_') && entry.endsWith('.txt')) {
        fs.unlinkSync(path.join(TRACES_DIR, entry));
      }
    }
  } catch { /* best effort */ }
}

async function fetchAndCacheSuggestions() {
  const apiKey = getApiKey();
  const autoApplyUrl = `http://${VPS_HOST}:${VPS_PORT}/api/v1/optimizations/auto-apply?threshold=0.9&min_traces=10`;

  return new Promise((resolve) => {
    const url = new URL(autoApplyUrl);
    const req = http.request({
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: 'GET',
      headers: {
        'Authorization': apiKey ? `Bearer ${apiKey}` : '',
      },
      timeout: 5000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const suggestions = JSON.parse(data);
          const cachePath = path.join(TRACES_DIR, 'agl_suggestions_cache.json');
          fs.writeFileSync(cachePath, JSON.stringify(suggestions));
          const count = (suggestions.auto_apply || []).length;
          if (count > 0) {
            process.stderr.write(`[Agent Lightning] Cached ${count} auto-apply suggestion(s) for next session\n`);
          }
        } catch { /* best effort */ }
        resolve();
      });
    });
    req.on('error', () => resolve());
    req.on('timeout', () => { req.destroy(); resolve(); });
    req.end();
  });
}

// --- Circuit breaker (LATENCY FIX 2026-09-04) -----------------------------
// MEASURED: this hook cost 11,557 ms of a 54,907 ms Stop-chain -- the single
// largest contributor to a frozen screen at EVERY turn-end. The cause is not that
// it is slow code; it is that it performs BLOCKING NETWORK I/O on the interactive
// path. When the VPS is down or far away, a remote host's availability silently
// becomes the agent's responsiveness, and the Owner reads it as a hang.
//
// The traces are already durable (buffered on disk, flushed next session), so the
// correct behaviour when the VPS is unreachable is to STOP ASKING for a while --
// not to re-pay the timeout on every single turn. One failure opens the breaker for
// COOLDOWN_MS; a success closes it immediately.
//
// Fail-open ABSOLUTE and directional: if the breaker file cannot be read we treat
// the breaker as CLOSED (attempt the flush), i.e. exactly the behaviour before this
// existed. A broken breaker must never silently stop telemetry forever.
const BREAKER_PATH = path.join(TRACES_DIR, 'vps_breaker.json');
const COOLDOWN_MS = 15 * 60 * 1000;

function breakerOpen() {
  try {
    const raw = fs.readFileSync(BREAKER_PATH, 'utf8');
    const st = JSON.parse(raw);
    if (!st || typeof st.failedAt !== 'number') return false;
    return (Date.now() - st.failedAt) < COOLDOWN_MS;
  } catch { return false; }   // unreadable/absent -> attempt (pre-existing behaviour)
}

function tripBreaker() {
  try {
    fs.mkdirSync(TRACES_DIR, { recursive: true });
    fs.writeFileSync(BREAKER_PATH, JSON.stringify({ failedAt: Date.now(), host: VPS_HOST }), 'utf8');
  } catch { /* best effort: the breaker is an optimisation, not a requirement */ }
}

function clearBreaker() {
  try { if (fs.existsSync(BREAKER_PATH)) fs.unlinkSync(BREAKER_PATH); } catch { /* best effort */ }
}

// --- Core processing (extracted so hook-dispatcher.js can require this module) ---
async function runInner(data) {
  try {
    // ORDER INVERTED 2026-09-15 -- this is the actual latency fix.
    //
    // The breaker used to be consulted AFTER readAllPending(), justified by "with
    // nothing to send there is no network call to skip, so the cheap path stays
    // cheap either way". That is true for a small buffer and false for a large
    // one: readAllPending() is the expensive step, not the POST. MEASURED with a
    // 394,476-trace backlog it cost 37 s, so the breaker -- whose entire purpose
    // is to stop re-paying for an unreachable VPS -- was opening the gate only
    // after the bill had been paid, on EVERY turn boundary in EVERY repo.
    //
    // It also defeated HARD_DEADLINE_MS: readAllPending() is SYNCHRONOUS, so it
    // blocks the event loop and the Promise.race deadline timer cannot fire until
    // it has already finished. A 10 s "hard ceiling" observed a 37 s run. A guard
    // downstream of the cost it is meant to bound cannot fire -- three layers of
    // protection existed here and all three sat on the wrong side of the work.
    //
    // Consulting the breaker first costs one small readFileSync and makes the
    // skip path ~1 ms. Fail-open direction is unchanged: an unreadable breaker
    // still reads as CLOSED, so a broken breaker can never silence telemetry.
    if (breakerOpen()) {
      process.stderr.write(
        `[Agent Lightning] VPS breaker OPEN (last failure < ${COOLDOWN_MS / 60000}m ago) — `
        + `skipping flush; buffer untouched\n`);
      return { continue: true };
    }

    const { traces, files } = readAllPending();
    if (traces.length === 0) return { continue: true };

    const success = await postTraces(traces);
    if (success) { clearBreaker(); } else { tripBreaker(); }
    if (success) {
      for (const f of files) {
        try { fs.unlinkSync(f); } catch { }
      }
      cleanupSequenceFiles();
      process.stderr.write(`[Agent Lightning] Flushed ${traces.length} traces to VPS\n`);
    } else {
      process.stderr.write(`[Agent Lightning] VPS unreachable — ${traces.length} traces buffered for next session\n`);
    }
  } catch (_) { /* silent */ }
  return { continue: true };
}

function run(data) {
  // Wrap in Promise.race so any hang is bounded even when bundled by dispatcher.
  const deadline = new Promise(resolve => {
    setTimeout(() => {
      process.stderr.write('[Agent Lightning] Hard timeout — trace-flusher bailing\n');
      resolve({ continue: true });
    }, HARD_DEADLINE_MS);
  });
  return Promise.race([runInner(data), deadline]);
}

// --- Dual-mode entry point ---
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 8000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    let data = {};
    try { data = JSON.parse(input); } catch (_) { /* keep empty */ }
    run(data).then(out => {
      try { process.stdout.write(JSON.stringify(out)); } catch { }
      process.exit(0);
    }).catch(() => {
      try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
      process.exit(0);
    });
  });
} else {
  module.exports = { run };
}
