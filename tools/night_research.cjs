'use strict';
// Night Research runner core (T10 item 34, genesis-night-research -> WRAP). Called by
// tools/night_research_runner.py, never directly by a scheduler: the Python side owns the host
// check and the question queue. One JSON request on stdin, one JSON reply on stdout.
//
//   {"mode": "status"|"run", "stateDir": "...", "timezone": "...", "maxPassesPerNight": n,
//    "theme": {"id": "...", "question": "..."}, "claude": "claude", "timeoutMs": n,
//    "now": <epoch ms, fixture only>, "fixture": true|false}
//
// The vendored module owns the gate (window, pause, gaming, pass budget, single-flight lock) and
// the report format (sources unverified, reward 0, promotion none). This file only supplies the
// worker: one read-only headless `claude -p` with web tools, whose answer must be the JSON shape
// parseCandidate reads. `fixture` swaps in a deterministic worker for tests; it is refused unless
// the caller also sets CPP_NIGHT_RESEARCH_FIXTURE=1, so no scheduler can reach it by accident.
const path = require('path');
const { spawn } = require('child_process');

const nr = require(path.resolve(__dirname, '..', 'vendor', 'genesis-suite', 'modules', 'genesis-night-research', 'index.cjs'));

const SHAPE = 'Reply with ONE JSON object and nothing else: {"summary": "...", "hypothesis": "...", ' +
  '"candidateImprovement": "...", "experimentProposal": "...", "limitations": "...", ' +
  '"sources": [{"url": "https://...", "claim": "what this page supports"}]}. At most MAXSRC sources; every source must be a ' +
  'page you actually opened. You are researching only: do not modify any file.';

function claudeWorker(req) {
  return ({ question, maxSources, signal, deadlineMs }) => new Promise((resolve) => {
    const prompt = `${question}\n\n${SHAPE.replace('MAXSRC', String(maxSources))}`;
    const args = ['-p', '--output-format', 'json', '--no-session-persistence', '--permission-mode', 'default',
      '--allowedTools', 'WebSearch', 'WebFetch', '--disallowedTools', 'Edit', 'Write', 'NotebookEdit', 'Bash'];
    const child = spawn(req.claude || 'claude', args, { stdio: ['pipe', 'pipe', 'pipe'] });
    let out = '';
    let err = '';
    const kill = () => { try { child.kill('SIGTERM'); } catch (_e) { /* already gone */ } };
    signal.addEventListener('abort', kill, { once: true });
    const timer = setTimeout(kill, Math.max(1000, deadlineMs - Date.now()));
    child.stdout.on('data', (c) => { out += c; });
    child.stderr.on('data', (c) => { err += c; });
    child.on('error', (e) => { clearTimeout(timer); resolve({ ok: false, error: `spawn: ${e.message}` }); });
    child.on('close', (code) => {
      clearTimeout(timer);
      let j;
      try { j = JSON.parse(out); } catch (_e) { return resolve({ ok: false, error: `rc=${code} unparseable: ${(out || err).slice(0, 300)}` }); }
      if (code !== 0 || j.is_error) return resolve({ ok: false, error: `rc=${code} ${String(j.result).slice(0, 300)}` });
      const text = String(j.result || '');
      const m = text.match(/\{[\s\S]*\}/);
      const models = Object.keys(j.modelUsage || {});
      resolve({ ok: true, text: m ? m[0] : text, actualModel: models.length === 1 ? models[0] : null,
        usage: j.usage || null, monetaryCost: null });
    });
    child.stdin.end(prompt);
  });
}

function fixtureWorker() {
  return async ({ question }) => ({ ok: true, actualModel: 'fixture', usage: null, monetaryCost: null,
    text: JSON.stringify({ summary: `fixture answer to: ${question}`, hypothesis: 'h', candidateImprovement: 'c',
      experimentProposal: 'e', limitations: 'fixture', sources: [{ url: 'https://example.org/a', claim: 'a' }] }) });
}

async function main() {
  let raw = '';
  for await (const c of process.stdin) raw += c;
  let req;
  try { req = JSON.parse(raw.replace(/^﻿/, '')); } catch (e) { return out({ outcome: 'BAD_REQUEST', error: e.message }); }
  if (req.fixture && process.env.CPP_NIGHT_RESEARCH_FIXTURE !== '1') return out({ outcome: 'REFUSED', error: 'fixture worker outside a test' });
  const base = { stateDir: req.stateDir, timezone: req.timezone, maxPassesPerNight: req.maxPassesPerNight,
    maxWorkerMs: req.timeoutMs, isGaming: false, theme: req.theme };
  if (req.now != null) {
    if (!req.fixture) return out({ outcome: 'REFUSED', error: 'a clock override is fixture-only' });
    base.now = req.now;
  }
  if (req.mode === 'status') {
    const s = nr.status({ ...base, isPaused: require('fs').existsSync(path.join(req.stateDir, 'paused.flag')) });
    return out({ outcome: 'OK', status: s });
  }
  const worker = req.fixture ? fixtureWorker() : claudeWorker(req);
  try {
    const r = await nr.runPass({ ...base, worker });
    return out({ outcome: 'OK', result: r });
  } catch (e) {
    return out({ outcome: 'FAILED', error: String((e && e.message) || e) });
  }
}

function out(v) { process.stdout.write(JSON.stringify(v)); }

main();
