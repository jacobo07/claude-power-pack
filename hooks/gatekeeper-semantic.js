#!/usr/bin/env node
/**
 * Gatekeeper Semantic Firewall — Token Shield v160.0 (soft-mode).
 *
 * PreToolUse hook for Read / Grep. If the target file is indexed in
 * `<project>/_audit_cache/source_map.json` and its current SHA-256 still
 * matches the cached hash, injects the cached neural_summary + semantic_dna
 * as advisory context. Claude may still Read the raw file — this is
 * advisory (soft-mode), never blocking.
 *
 * Circuit breaker: accumulates planned `size_bytes` per session in
 * `_audit_cache/turn_plan.json`; above 40 KB emits a SELECTIVE READ PLAN
 * warning in additionalContext.
 *
 * Cache is written by: python tools/audit_cache.py --project <root> --build
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { readStdin, outputPreToolUse } = require('./hook-utils');

const CACHE_REL = path.join('_audit_cache', 'source_map.json');
const INSIGHTS_REL = path.join('_audit_cache', 'insights.json');
const TURN_PLAN_REL = path.join('_audit_cache', 'turn_plan.json');
const CIRCUIT_BREAKER_BYTES = 40 * 1024;
const MAX_INSIGHTS_PER_FILE = 3;

function sha256Trunc(filePath) {
  try {
    const bytes = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(bytes).digest('hex').slice(0, 16);
  } catch {
    return null;
  }
}

function findProjectRoot(startDir) {
  let dir = path.resolve(startDir);
  while (dir && dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, CACHE_REL))) return dir;
    dir = path.dirname(dir);
  }
  return null;
}

function loadInsightsForPath(projectRoot, relPath) {
  try {
    const raw = fs.readFileSync(path.join(projectRoot, INSIGHTS_REL), 'utf-8');
    const db = JSON.parse(raw);
    if (!db || !Array.isArray(db.entries)) return [];
    return db.entries
      .filter(e => e && e.path === relPath)
      .slice(0, MAX_INSIGHTS_PER_FILE);
  } catch {
    return [];
  }
}

function updateTurnPlan(projectRoot, sessionId, relPath, sizeBytes) {
  const planPath = path.join(projectRoot, TURN_PLAN_REL);
  let plan = { session_id: sessionId, bytes: 0, reads: [] };
  try {
    if (fs.existsSync(planPath)) {
      const prior = JSON.parse(fs.readFileSync(planPath, 'utf-8'));
      if (prior.session_id === sessionId) plan = prior;
    }
  } catch {}
  plan.bytes += sizeBytes || 0;
  plan.reads.push(relPath);
  try {
    fs.mkdirSync(path.dirname(planPath), { recursive: true });
    fs.writeFileSync(planPath, JSON.stringify(plan));
  } catch {}
  return plan.bytes;
}

(async () => {
  try {
    const input = await readStdin(2000);
    const toolName = input.tool_name;
    if (toolName !== 'Read' && toolName !== 'Grep') {
      return outputPreToolUse('allow');
    }

    const toolInput = input.tool_input || {};
    const target = toolInput.file_path || toolInput.path;
    if (!target) return outputPreToolUse('allow');

    const cwd = input.cwd || process.cwd();
    const projectRoot = findProjectRoot(cwd);
    if (!projectRoot) return outputPreToolUse('allow');

    let cache;
    try {
      cache = JSON.parse(fs.readFileSync(path.join(projectRoot, CACHE_REL), 'utf-8'));
    } catch {
      return outputPreToolUse('allow');
    }

    const absTarget = path.isAbsolute(target) ? target : path.resolve(cwd, target);
    let rel = path.relative(projectRoot, absTarget).replace(/\\/g, '/');
    if (!rel || rel.startsWith('..')) return outputPreToolUse('allow');

    const entry = cache.files && cache.files[rel];
    if (!entry) return outputPreToolUse('allow');

    const currentHash = sha256Trunc(absTarget);
    if (!currentHash) return outputPreToolUse('allow');

    const totalBytes = updateTurnPlan(projectRoot, input.session_id, rel, entry.size_bytes);
    const breaker = totalBytes > CIRCUIT_BREAKER_BYTES
      ? `\n\n[CIRCUIT BREAKER] Planned raw-reads this turn = ${totalBytes} bytes (threshold ${CIRCUIT_BREAKER_BYTES}). Consider: python tools/audit_cache.py --project . --summary <path>`
      : '';

    if (currentHash !== entry.sha256) {
      return outputPreToolUse('allow',
        `[Token Shield] ${rel} changed since last index — cache is stale. Refresh: python tools/audit_cache.py --project . --build${breaker}`
      );
    }

    const dna = (entry.semantic_dna || []).join(' ');
    const neural = entry.neural_summary || entry.summary || '';
    const deps = (entry.depends_on || []).slice(0, 5).join(', ') || '(none)';

    const insights = loadInsightsForPath(projectRoot, rel);
    const insightsBlock = insights.length
      ? '\nInsights:\n' + insights
          .map(i => `  - [${i.category}] ${i.title}: ${(i.body || '').split('\n')[0].slice(0, 140)}`)
          .join('\n')
      : '';

    const ctx = [
      `[Token Shield v160.0 — cached summary for ${rel}]`,
      `DNA: ${dna || '(none)'}`,
      `Neural: ${neural}`,
      `Size: ${entry.size_bytes}B | ${entry.loc} LOC | Hash: ${entry.sha256}`,
      `Deps: ${deps}${insightsBlock}`,
      ``,
      `Use raw Read only if you need exact code; otherwise this cached summary may suffice.`,
      breaker,
    ].join('\n').trim();

    outputPreToolUse('allow', ctx);
  } catch {
    outputPreToolUse('allow');
  }
})();
