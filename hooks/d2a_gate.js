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
// MAX_LEN was 8000 and it SKIPPED anything longer. That silently exempted the
// single class of proposal D2A exists for: the multi-system corpus brief, which
// runs tens of KB. Fifteen consecutive mega-corpus proposals landed
// majority-owned in this estate and this gate could not have fired on one of
// them. Measured 2026-08-18 on a 26,034-byte 25-system brief: silent.
// The original concern was real but is a property of what the ENGINE receives,
// not of what the gate is allowed to look at -- so consider long prompts and
// truncate before the engine instead of skipping them.
const MAX_LEN = 400000;         // consider up to this
const ENGINE_INPUT_CAP = 8000;  // ...but never feed more than this to the engine
// Above this length a brief inevitably contains negative-guard vocabulary as
// SUBJECT MATTER ("extend", "rollback", "test", "reference" appear in any
// serious architecture document), so NOT_CREATION stops being an intent signal.
const MEGA_LEN = 4000;

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

// Global twins of the positive patterns, used only to measure how SUSTAINED the
// creation signal is in a long brief. Separate constants because a /g regex
// carries lastIndex state, and sharing one with the .test() calls above would
// make those calls order-dependent.
const CREATE_VERB_G = new RegExp(CREATE_VERB.source, 'gi');
const ARCH_NOUN_G = new RegExp(ARCH_NOUN.source, 'gi');

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
function countMatches(re, s) {
  return (String(s).match(re) || []).length;
}

function isCreationProposal(prompt) {
  const p = String(prompt || '');
  if (p.length < MIN_LEN || p.length > MAX_LEN) return false;
  if (!CREATE_VERB.test(p) || !ARCH_NOUN.test(p)) return false;

  // Short prompt: NOT_CREATION is a reliable intent signal — one occurrence
  // means the Owner is acting on something that already exists. Unchanged
  // behaviour, and what V-D2A-GATE-KEYWORD-SCOPE pins.
  if (p.length <= MEGA_LEN) return !NOT_CREATION.test(p);

  // Long brief: require the creation signal to be SUSTAINED rather than
  // incidental, so a long bug report or postmortem (which also names systems)
  // still stays silent. A genuine multi-system proposal names its architecture
  // nouns repeatedly; a report about one broken thing does not.
  return countMatches(ARCH_NOUN_G, p) >= 6 && countMatches(CREATE_VERB_G, p) >= 3;
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
      // Truncate here rather than refusing the prompt upstream: the engine is
      // bag-of-words over the proposal's vocabulary, so the head of a brief
      // carries its subject matter, and a giant paste never reaches python.
      input: String(prompt).slice(0, ENGINE_INPUT_CAP),
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
 * The UNKNOWN advisory. Fired when the engine could not confidently name a
 * parent on a LARGE multi-system brief. It deliberately asserts nothing about
 * ownership — it says ownership is undetermined and names the instrument that
 * can determine it, because the single-proposal path scores a whole family as
 * one bag of words and cannot resolve a 25-system brief by construction.
 */
function buildDeferAdvisory(v) {
  const d = v.dupe || {};
  const parent = d.parent_id ? `${d.parent_id} (${d.parent_name})` : 'an existing system';
  return `D2A ownership advisory (SCS C85, level-2 — never blocks):\n`
    + `VERDICT: UNDETERMINED, not novel. Coverage capped at ${d.coverage_pct != null ? d.coverage_pct : '?'}% `
    + `by the plausibility floor against ${parent} `
    + `[sem=${d.semantic} func=${d.functional} arch=${d.architectural}].\n`
    + `A capped verdict means a parent's vocabulary matched but precision was too low to name it. `
    + `It is NOT evidence that this proposal is new — treat it as UNKNOWN.\n`
    + `WHY THIS FIRED: the prompt is a multi-system proposal, and the single-proposal path scores `
    + `an entire family as one bag of words, so it cannot resolve ownership per system.\n`
    + `REQUIRED NEXT ACTION before building anything:\n`
    + `  1. Decompose the brief into one {name, description} per proposed system.\n`
    + `  2. python modules/duplicate_to_advantage/d2a_engine.py --family-file <f>.json --repo-evidence\n`
    + `  3. Check vault/audits/apir/NON_DUPLICATION_LEDGER.md — a DO-NOT-BUILD row reopens only on `
    + `measured evidence, never on a new name.\n`
    + `  4. HR-NOVELTY-001 requires the 13-question proof against a DISCOVERED sweep before any new `
    + `institutional system is admitted.\n`
    + `Base rate: fifteen consecutive mega-corpus proposals in this estate measured majority- or `
    + `fully-owned once measured. That is the correct prior, not an accusation.`;
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

    // THREE outcomes, not two. `deferred` is the plausibility floor saying "a
    // parent's vocabulary matched but precision was too low to name it" — that
    // is UNKNOWN, and UNKNOWN is the opposite of novel. Collapsing it into the
    // `!is_duplicate` silence made a majority-owned brief indistinguishable
    // from a genuinely-new one, which is the favourable-reading-of-absence this
    // estate forbids everywhere else. Measured 2026-08-18 on a 25-system brief:
    // coverage 45%, deferred, is_duplicate=False -> gate silent -> the corpus
    // read as novel until a manual audit found 22 of 25 already owned.
    //
    // Scoped to long briefs on purpose: on a short proposal DEFER is cheap to
    // re-ask and an advisory would be noise, but on a multi-system brief the
    // false-NEW authorizes an entire family build. False positives are the
    // expensive failure (T-D2A-GATE-KEYWORD-SCOPE-001) — so this fires only
    // where a false negative is more expensive still.
    if (!v.dupe.is_duplicate) {
      if (v.dupe.deferred && String(prompt).length > MEGA_LEN) {
        return {
          hookSpecificOutput: {
            hookEventName: 'UserPromptSubmit',
            additionalContext: buildDeferAdvisory(v),
          },
        };
      }
      return {};                                      // genuinely new -> silence
    }
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

module.exports = { run, isCreationProposal, buildAdvisory, buildDeferAdvisory };

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
