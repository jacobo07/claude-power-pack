#!/usr/bin/env node
/**
 * closer-guard.js — Stop hook. Kills the "dead screen" turn-ending classes.
 *
 * ORIGIN (2026-08-27, TUA-X): a turn ended with the text
 *   "Recording the session objective honestly."
 * and no tool call. The Owner saw a frozen screen waiting for an action that
 * was never going to arrive. The failure was ALREADY documented in the vault
 * (feedback-intent-narration-closer-deadscreen.md,
 *  feedback-empty-closer-deadscreen.md, global CLAUDE.md rules (H)/(G)) and it
 * recurred anyway.
 *
 * That recurrence IS the finding: a rule that lives only in prose does not
 * fire. Prose is advisory to a model that is already mid-mistake. This hook
 * moves the rule from prose into the control flow, where it executes whether
 * or not the model remembered it.
 *
 * THREE BANNED CLOSER CLASSES (all produce the same Owner-visible symptom):
 *   1. EMPTY        — turn ends with no assistant text at all.
 *   2. PASSIVE_WAIT — "awaiting", "standing by", "I'll wait", "in progress".
 *                     Implies the Owner must wait; usually the work is done
 *                     or the next step is the agent's.
 *   3. INTENT_NARRATION — a short trailing sentence announcing the next
 *                     action ("Recording X.", "Let me check Y.", "Now I'll
 *                     update Z.") with no tool call after it. The agent
 *                     described the move instead of making it.
 *
 * DESIGN CONSTRAINTS (deliberate, and each one is load-bearing):
 *   - Fail-open ABSOLUTE. Any parse error, missing transcript, unreadable
 *     line → {continue:true}. A guard that breaks the session is worse than
 *     the bug it guards.
 *   - Never block twice in a row for the same session. If the model re-emits
 *     a bad closer after being told once, we let it through. An infinite
 *     block loop is itself a dead screen — the exact thing being prevented.
 *   - A closer ending in a QUESTION to the Owner is always allowed. That is
 *     a legitimate active handoff, not a passive wait.
 *   - Only the trailing ~2 sentences are inspected. Mid-message narration
 *     ("Let me check X" followed by an actual tool call earlier in the turn)
 *     is normal and must not trip the guard.
 *   - Escape hatch: CLAUDE_CLOSER_GUARD=off disables it.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const STATE_DIR = path.join(os.homedir(), '.claude', 'logs');
const STATE_FILE = path.join(STATE_DIR, 'closer-guard-state.json');

// --- Banned closer patterns ------------------------------------------------
// Anchored to the END of the message so mid-turn narration never trips them.

const PASSIVE_WAIT = [
  /\bawaiting\b/i,
  /\bstanding by\b/i,
  /\bi'?ll wait\b/i,
  /\bwaiting (?:for|on)\b/i,
  /\bwill notify me\b/i,
  /\bonce (?:it|that|this) (?:completes|finishes|lands)\b[^?]*$/i,
  /\bin progress\.?\s*$/i,
  /\bto be continued\b/i,
];

// Intent narration: a SHORT trailing sentence that announces an action.
// Gerund-initial ("Recording the ..."), "let me ...", "now I'll ...",
// "next, I'll ...", "proceeding to ...".
const INTENT_NARRATION = [
  /(?:^|[.!?]\s+)(?:now\s+)?let me\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:now|next)[,:]?\s+i(?:'ll| will)\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)i(?:'ll| will) (?:now )?(?:go ahead and )?\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)proceeding (?:to|with)\s+[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:recording|writing|updating|adding|creating|running|checking|reading|committing|verifying|building|fixing|distilling|investigating|inspecting|generating)\s+(?:the|a|an|my|this|that|it|out|up|through)\b[^.!?]{0,120}[.!?]\s*$/i,
];

function classify(text) {
  const t = (text || '').trim();
  if (!t) return { cls: 'EMPTY', snippet: '' };

  // A question to the Owner is a legitimate active closer, always.
  if (/\?\s*$/.test(t)) return null;

  // Inspect only the tail: last ~2 sentences (or 320 chars, whichever smaller).
  const tail = t.slice(-320);

  for (const re of PASSIVE_WAIT) {
    if (re.test(tail)) return { cls: 'PASSIVE_WAIT', snippet: tail.slice(-140) };
  }
  for (const re of INTENT_NARRATION) {
    if (re.test(tail)) return { cls: 'INTENT_NARRATION', snippet: tail.slice(-140) };
  }
  return null;
}

// --- Transcript reading ----------------------------------------------------

/** Last assistant message: its text, and whether it issued any tool_use. */
function lastAssistantTurn(transcriptPath) {
  const raw = fs.readFileSync(transcriptPath, 'utf8');
  const lines = raw.split(/\r?\n/);

  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;

    let rec;
    try { rec = JSON.parse(line); } catch { continue; }

    const msg = rec.message || rec;
    const role = msg.role || rec.type;
    if (role !== 'assistant') continue;

    const content = msg.content;
    if (!Array.isArray(content)) {
      return { text: typeof content === 'string' ? content : '', usedTool: false };
    }

    let text = '';
    let usedTool = false;
    for (const block of content) {
      if (!block || typeof block !== 'object') continue;
      if (block.type === 'text' && typeof block.text === 'string') text += block.text;
      if (block.type === 'tool_use') usedTool = true;
    }
    return { text, usedTool };
  }
  return null;
}

// --- Anti-loop state -------------------------------------------------------

function readState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return {}; }
}

function writeState(state) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(STATE_FILE, JSON.stringify(state), 'utf8');
  } catch { /* fail-open: state is an optimisation, not a requirement */ }
}

// --- Reason text -----------------------------------------------------------

const GUIDANCE = {
  EMPTY:
    'This turn is about to end with NO assistant text. The Owner will see a ' +
    'blank/frozen screen with no idea what happened or what comes next.',
  PASSIVE_WAIT:
    'This turn is about to end on a PASSIVE WAIT closer. It tells the Owner ' +
    'to wait, when the work is either already done or the next step is yours. ' +
    'That reads as a frozen screen.',
  INTENT_NARRATION:
    'This turn is about to end on an INTENT-NARRATION closer: you DESCRIBED ' +
    'the next action instead of EXECUTING it, and no tool call followed. The ' +
    'Owner is now staring at a stated intention that will never happen.',
};

function buildReason(cls, snippet) {
  return [
    `CLOSER GUARD — ${cls}.`,
    GUIDANCE[cls],
    snippet ? `Your closing text was: "...${snippet.trim()}"` : '',
    '',
    'Do ONE of these before ending the turn:',
    '  1. If you named a next action — DO IT NOW with a tool call. Do not ' +
    're-describe it.',
    '  2. If the work is finished — state the concrete outcome (what landed, ' +
    'what it proves).',
    '  3. If you are genuinely blocked — ask the Owner a direct question they ' +
    'can act on.',
    '',
    'Banned as final text: "awaiting", "standing by", "in progress", ' +
    '"I\'ll wait", and any bare "Doing X." with no tool call after it.',
  ].filter(Boolean).join('\n');
}

// --- Main ------------------------------------------------------------------

function run(input) {
  try {
    if (String(process.env.CLAUDE_CLOSER_GUARD || '').toLowerCase() === 'off') {
      return { continue: true };
    }

    const transcriptPath = input && input.transcript_path;
    if (!transcriptPath || !fs.existsSync(transcriptPath)) return { continue: true };

    const turn = lastAssistantTurn(transcriptPath);
    if (!turn) return { continue: true };

    // A turn that issued a tool call is not a dead-screen closer.
    if (turn.usedTool) return { continue: true };

    const verdict = classify(turn.text);
    if (!verdict) return { continue: true };

    // Anti-loop: never block the same session twice consecutively.
    const sid = (input && input.session_id) || 'unknown';
    const state = readState();
    const prev = state[sid];
    const fingerprint = verdict.cls + '|' + (turn.text || '').trim().slice(-80);

    if (prev && prev.blocked && prev.fingerprint === fingerprint) {
      // Already told it once and it repeated. Let it through rather than
      // trapping the Owner in a block loop — that would be the same disease.
      state[sid] = { blocked: false, fingerprint, ts: Date.now() };
      writeState(state);
      return { continue: true };
    }

    state[sid] = { blocked: true, fingerprint, ts: Date.now() };
    writeState(state);

    return {
      decision: 'block',
      reason: buildReason(verdict.cls, verdict.snippet),
    };
  } catch (_) {
    return { continue: true }; // fail-open ABSOLUTE
  }
}

module.exports = { run, classify, lastAssistantTurn };

// --- Dual-mode entry point (matches scaffold-auditor.js contract) ----------
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 5000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    let data = {};
    try { data = JSON.parse(input || '{}'); } catch { /* fail-open */ }
    try { console.log(JSON.stringify(run(data))); } catch {
      console.log(JSON.stringify({ continue: true }));
    }
    process.exit(0);
  });
}
