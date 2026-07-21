#!/usr/bin/env node
/**
 * d2a_gate.js — D2A duplicate advisory (SCS C85 addendum).
 *
 * Fires on UserPromptSubmit. When the Owner's prompt is a proposal to CREATE a
 * new system / dataset / module, run the D2A Engine and — only if the proposal
 * duplicates something the ecosystem already owns — surface the DUPE VERDICT
 * and the recommended BUILD CONTRACT alternative BEFORE Claude starts building.
 *
 * Why UserPromptSubmit and not PreToolUse: a PreToolUse hook receives
 * { tool_name, tool_input } and never sees the Owner's prompt text. The
 * objective ("the Owner sees the verdict before Claude builds", triggered by
 * creation keywords in the Owner's own words) is only implementable on the
 * prompt surface. Precedent: prd-keyword-sentinel.js.
 *
 * Honest contract (GK-12 / CO-10 ladder — mirrors graph_first_gate.js):
 *   - Level-2 (detect + advise). NEVER denies, NEVER blocks, NEVER exits 2.
 *   - Fail-open ABSOLUTE: any error, missing engine, unparseable input, python
 *     failure, timeout -> empty stdout, exit 0. Claude continues untouched.
 *   - Silence on novel: a genuinely-new proposal produces zero output.
 *   - Scope (T-D2A-GATE-KEYWORD-SCOPE-001): intercepts CREATION of a new
 *     system/dataset only. Never use, query, extend, wire, fix, or refactor of
 *     an existing one. A false positive is worse than a false negative.
 *   - Throttled per (session, proposal) so a repeated prompt nudges once.
 *
 * Dual-mode: exports { run, isCreationProposal } for unit tests, and runs as a
 * standalone stdin->stdout CLI child (the shell-free CHAIN_MAP path).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

const PP_ROOT = path.join(os.homedir(), '.claude', 'skills', 'claude-power-pack');
const ENGINE = path.join(PP_ROOT, 'modules', 'duplicate_to_advantage', 'd2a_engine.py');
const STATE_DIR = path.join(os.homedir(), '.claude', 'state', 'd2a');
const THROTTLE_MS = 15 * 60 * 1000;
const MIN_LEN = 12;          // shorter than this carries no proposal substance
const MAX_LEN = 8000;        // never feed a giant paste to the engine

// A creation VERB. Deliberately narrow: the act of bringing a new thing into
// existence, in English or Spanish.
const CREATE_VERB = /\b(create|build|implement|design|scaffold|author|introduce|stand\s+up|from\s+scratch|construye|construir|crea|crear|implementa|implementar|dise[nñ]a|dise[nñ]ar|desde\s+cero)\b/i;

// An ARCHITECTURE OBJECT. The thing being created must be a system-level noun;
// "create a variable" / "build the docs" must not trip the gate. Includes the
// component nouns the PP ecosystem actually names systems after (router,
// governor, detector...), so "crear un router de modelos" is caught.
const ARCH_NOUN = /\b(system|dataset|datasets|engine|module|framework|family|pipeline|kernel|layer|subsystem|architecture|suite|router|planner|orchestrator|compiler|scheduler|registry|governor|detector|harness|optimizer|sistema|motor|m[oó]dulo|arquitectura|capa|familia|enrutador|planificador)\b/i;

// NEGATIVE guards. Any of these means the Owner is acting on something that
// ALREADY exists -> D2A has nothing to say. Checked before the positives.
// (T-D2A-GATE-KEYWORD-SCOPE-001: false positives are the expensive failure.)
const NOT_CREATION = /\b(extend|extiende|extender|modify|modifica|update|actualiza|fix|arregla|repair|refactor|rename|wire|wiring|activa|activate|enable|test|tests|debug|document|read|query|consulta|use|usa|run|ejecuta|delete|remove|elimina|revert|rollback|migrate|port)\b/i;

function readStdin() {
  try { return fs.readFileSync(0, 'utf8'); } catch (_) { return ''; }
}

function pickPython() {
  const cands = [
    'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
    'python', 'python3',
  ];
  for (const c of cands) {
    try { execFileSync(c, ['--version'], { stdio: 'ignore', windowsHide: true }); return c; } catch (_) { /* next */ }
  }
  return 'python';
}

/**
 * True only when the prompt proposes creating a NEW architecture-level thing.
 * Requires (creation verb) AND (architecture noun) AND NOT (an act on an
 * existing thing). Conjunctive by design — see the scope trap.
 */
function isCreationProposal(prompt) {
  const p = String(prompt || '');
  if (p.length < MIN_LEN || p.length > MAX_LEN) return false;
  if (NOT_CREATION.test(p)) return false;
  return CREATE_VERB.test(p) && ARCH_NOUN.test(p);
}

// Per-(session, proposal) throttle. A miss returns false = "advise now".
// Any fs error fails toward advising once, never toward a block-like failure.
function throttled(sessionId, prompt) {
  try {
    const safe = String(sessionId || 'nosess').replace(/[^a-zA-Z0-9]+/g, '') || 'nosess';
    const h = crypto.createHash('sha1').update(String(prompt)).digest('hex').slice(0, 12);
    const marker = path.join(STATE_DIR, `.d2a_${safe}_${h}`);
    try {
      const st = fs.statSync(marker);
      if (Date.now() - st.mtimeMs < THROTTLE_MS) return true;
    } catch (_) { /* no marker — fall through to stamp + advise */ }
    try {
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(marker, '');
    } catch (_) { /* best-effort */ }
    return false;
  } catch (_) {
    return false;
  }
}

// Invoke the engine. Returns the parsed D2AVerdict dict, or null on ANY failure.
function askEngine(prompt) {
  try {
    if (!fs.existsSync(ENGINE)) return null;
    const out = execFileSync(pickPython(), [ENGINE, '--stdin', '--json'], {
      input: prompt,
      encoding: 'utf8',
      timeout: 8000,
      maxBuffer: 4 << 20,
      windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
    });
    const v = JSON.parse(out);
    return (v && typeof v === 'object') ? v : null;
  } catch (_) {
    return null;   // engine missing / python broken / timeout / bad JSON -> silence
  }
}

function buildAdvisory(v) {
  const d = v.dupe || {};
  const c = v.contract || {};
  const rec = v.recommended || {};
  const pct = typeof d.coverage_pct === 'number' ? d.coverage_pct : 0;
  const parent = d.parent_id ? `${d.parent_id} (${d.parent_name})` : 'an existing system';
  const secondary = Array.isArray(d.secondary_parents) && d.secondary_parents.length
    ? ` Secondary: ${d.secondary_parents.join(', ')}.` : '';
  const anti = c.anti_inflation && typeof c.anti_inflation === 'object'
    ? Object.values(c.anti_inflation).filter(Boolean).length : 0;

  return `D2A duplicate advisory (SCS C85, level-2 — never blocks, PR-DUPLICATE-TO-ADVANTAGE-001):\n`
    + `DUPE VERDICT: this proposal is ~${pct}% covered by ${parent}.${secondary}\n`
    + `Ninguna duplicidad termina en rechazo — the engine mapped the gap and scored the alternatives.\n`
    + `RECOMMENDED ACTION: ${rec.operation || 'n/a'} — ${rec.name || 'n/a'} (ratio ${rec.ratio != null ? rec.ratio : 'n/a'})\n`
    + `BUILD CONTRACT: ${c.build || 'n/a'}\n`
    + `  artifact : ${c.artifact || 'n/a'} (lives in: ${c.lives_in || 'n/a'})\n`
    + `  reinforces: ${c.reinforces || 'n/a'}\n`
    + `  retires  : ${c.retires || 'n/a'}\n`
    + `  anti-inflation: ${anti}/10 rules pass\n`
    + `Do NOT build the proposal as stated until the Owner has seen this. Present the verdict, `
    + `then follow the BUILD CONTRACT (extend before create; a Part or rule before a dataset). `
    + `The Owner may override and proceed — this is advisory, not a block.`;
}

/**
 * run(input) — hook body. `input` is the parsed UserPromptSubmit JSON
 * ({ prompt, session_id, cwd, ... }). ALWAYS returns an object; NEVER throws.
 */
function run(input) {
  try {
    const data = input && typeof input === 'object' ? input : {};
    const prompt = typeof data.prompt === 'string' ? data.prompt : '';
    const sessionId = data.session_id || data.sessionId || '';

    if (!isCreationProposal(prompt)) return {};       // not a creation proposal -> silence
    if (throttled(sessionId, prompt)) return {};

    const v = askEngine(prompt);
    if (!v || !v.dupe) return {};                     // engine failed -> fail-open silence
    if (!v.dupe.is_duplicate) return {};              // genuinely new -> silence, Claude continues
    if (!v.contract || !v.recommended) return {};     // no alternative to offer -> silence

    return {
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: buildAdvisory(v),
      },
    };
  } catch (_) {
    return {};   // fail-open absolute
  }
}

module.exports = { run, isCreationProposal, buildAdvisory };

// --- Standalone CLI (shell-free CHAIN_MAP child) --------------------------
if (require.main === module) {
  let raw = '';
  try {
    raw = readStdin();
  } catch (_) { raw = ''; }
  let data = {};
  try { data = JSON.parse(raw || '{}'); } catch (_) { data = {}; }
  let out = {};
  try { out = run(data) || {}; } catch (_) { out = {}; }
  try {
    // Emit nothing at all when silent, so the dispatcher merges no empty frame.
    process.stdout.write(Object.keys(out).length ? JSON.stringify(out) : '');
  } catch (_) { /* stdout closed — still exit clean */ }
  process.exit(0);   // NEVER exit 2 — the D2A gate never blocks
}
