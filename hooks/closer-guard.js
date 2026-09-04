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
 * FIVE BANNED CLOSER CLASSES (all produce the same Owner-visible symptom).
 * The list GREW TWICE on 2026-09-02, both times from a real dead screen that
 * walked past every class then defined — which is this file's standing lesson:
 * A GUARD ENUMERATES SHAPES, AND AN UNENUMERATED SHAPE PASSES EVEN THOUGH THE
 * DAMAGE IS IDENTICAL. Expect a sixth; look at the borders, not the centre.
 *   4. RHETORICAL_QUESTION — a closing question of FACT, not of decision. The
 *                     Owner has nothing to answer, because a tool call would.
 *                     Added after the blanket "ends in ?" exemption was
 *                     measured producing the exact dead screen it exempted.
 *   5. NULL_ACK     — the whole turn dismisses a system event as needing no
 *                     reply ("No response requested."). A task-notification is
 *                     a WORK TRIGGER, not a message with a politeness slot.
 * Self-test: hooks/tests/test-closer-guard-nullack.js — two-way, 17/17. Half of
 * its cases MUST NOT fire, and that half is the half that matters: a gate
 * exercised only where it should trip would pass with every clause deleted.
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

  // --- SPANISH (added 2026-09-04, Jacobo/Neom) -----------------------------
  // See the ES block above INTENT_NARRATION for why these were missing.
  /\b(?:quedo|sigo|seguimos|estoy|estamos)\s+(?:a\s+la\s+espera|esperando)\b/i,
  /\ba\s+la\s+espera\s+(?:de|del)\b/i,
  /\besperando\s+(?:a\s+)?(?:que|la|el|los|las)\b/i,
  /\ben\s+(?:curso|progreso|marcha)\.?\s*$/i,
  /\bte\s+(?:aviso|digo|cuento)\s+cuando\b/i,
  /\bcuando\s+(?:termine|acabe|complete|aterrice)\s+te\s+\w+/i,
  /\bavisar[ée]\s+cuando\b/i,
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

  // --- SPANISH (added 2026-09-04, Jacobo/Neom) -----------------------------
  // MEASURED. A turn ended with "Corrijo la consulta y cuento." and no tool
  // call. Dead screen. This hook was wired and block:true, and it returned
  // clean, because every pattern above is ENGLISH and the Owner's repos are
  // written in Spanish. The class could only ever answer "clean" on a Spanish
  // turn: its green carried no information at all.
  //
  // The file already carried Spanish in RHETORICAL_QUESTION, added the one
  // time a Spanish dead screen was measured. Patching only the class where
  // the damage was seen is this file's own lesson unapplied a third time.
  //
  // TIER A — unambiguous future-intent markers. Spanish announces the next
  // move with a periphrasis ("voy a", "paso a", "dejame") that no report ever
  // uses, so these fire regardless of what else the sentence carries.
  /(?:^|[.!?]\s+)(?:ahora\s+|luego\s+|despu[ée]s\s+)?(?:voy|vamos)\s+a\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:paso|pasamos|procedo|procedemos)\s+a\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)d[ée]jame\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:contin[úu]o|contin[úu]amos|sigo|seguimos)\s+con\s+[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:lo\s+siguiente|el\s+siguiente\s+paso)\s+es\s+[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)ahora\s+\w+o\b[^.!?]{0,120}[.!?]?\s*$/i,
  //
  // TIER B — a bare first-person-present action verb OPENING the final
  // sentence. This is the shape that actually bit ("Corrijo la consulta"),
  // and it is the dangerous one to encode: Spanish drops the subject pronoun,
  // so an honest REPORT opens identically ("Confirmo que las dos raices
  // existen", "Mido 904 MB libres"). Two constraints keep it honest, and
  // test-closer-guard-espanol.js drives both sides:
  //   1. The verb list holds only verbs that act on the world. Reporting and
  //      opinion verbs are deliberately absent -- above all "creo" ("I
  //      believe"), "confirmo", "concluyo", and the noun-ambiguous "registro"
  //      / "monto" / "paso".
  //   2. The remainder of the sentence must carry NO evidence token (no digit,
  //      no backtick). An announcement has no result in it; a report does.
  //      That single clause is what lets "Mido si esos errores son de ahora."
  //      fire while "Mido 904 MB libres de 32 GB." passes untouched.
  /(?:^|[.!?]\s+)(?:corrijo|arreglo|reescribo|reviso|compruebo|verifico|actualizo|a[nñ]ado|genero|escribo|borro|quito|muevo|copio|despliego|ejecuto|lanzo|instalo|sello|anoto|preparo|cableo|empaqueto|miro|leo|busco|mido|cuento|aplico|pruebo|reintento|ajusto|edito|subo|guardo|limpio|repito)\b[^.!?\d`]{0,110}[.!?]?\s*$/i,
];

// Null acknowledgement: the WHOLE turn is a dismissal of a system event as if it were a
// social remark needing no reply. This is not EMPTY (there IS text), not PASSIVE_WAIT
// (nothing is being waited for), not INTENT_NARRATION (no action is announced) and not a
// question — so it walked past all four classes and produced a dead screen anyway.
//
// MEASURED 2026-09-02 (KobiiCraft Core Files). A background `<task-notification>` arrived
// with status=completed; the entire assistant turn was:
//     "No response requested."
// Zero tool calls. The task had finished cleanly and its output was sitting on disk; the
// next action was mine. The Owner saw a frozen screen and had to interrupt.
//
// Deliberately NARROW: only self-directed dismissals of a notification, never the ordinary
// human acknowledgements ("understood", "got it", "sounds good"), which are legitimate
// replies to a PERSON and whose blocking would be noise. The distinguishing mark is that
// nobody asked for a response in the first place — which is exactly why the phrase is
// wrong: a completed task is a WORK TRIGGER, not a message with a politeness slot.
const NULL_ACK = [
  /^no\s+(?:response|reply|action|further\s+action)\s+(?:is\s+)?(?:requested|required|needed|necessary)\.?$/i,
  /^(?:acknowledged|noted|received|confirmed)\.?$/i,
  /^(?:no\s+)?comment\.?$/i,
  /^nothing\s+(?:to\s+(?:do|add|report)|further)\.?$/i,
];

// `opts.toolTurn` = the turn ALSO issued a tool call.
//
// MEASURED 2026-09-04 (FIFA 11 Mod). The call site below used to hand a
// tool-call turn straight to `null` whenever it carried any text, so classify()
// was NEVER RUN on such a turn and PASSIVE_WAIT could not fire on it. That is
// the THIRD instance of this file's own twice-written lesson, "a guard's
// exemption is where its defect lives" — a blanket exemption standing between
// the detector and the case it was built for.
//
// The fix is deliberately narrow. On a tool-call turn:
//   - INTENT_NARRATION is LEGITIMATE and stays exempt. "Now I'll check X."
//     followed by an actual tool call is ordinary agentic narration; the
//     announced action happened. Blocking it would be a false positive on
//     nearly every working turn.
//   - RHETORICAL_QUESTION / NULL_ACK likewise stay exempt: a turn that did real
//     work is not a null acknowledgement.
//   - PASSIVE_WAIT is NEVER legitimate as a final message, tool call or not.
//     "Standing by" after a tool call is the same dead screen as "standing by"
//     alone — arguably worse, because the tool call makes it look alive.
function classify(text, opts) {
  const toolTurn = !!(opts && opts.toolTurn);
  const t = (text || '').trim();
  if (!t) return { cls: 'EMPTY', snippet: '' };

  if (toolTurn) {
    const tail0 = t.slice(-320);
    for (const re of PASSIVE_WAIT) {
      if (re.test(tail0)) return { cls: 'PASSIVE_WAIT', snippet: tail0.slice(-140) };
    }
    return null;
  }

  // Whole-message match, capped short: a long substantive turn that happens to close on
  // "Noted." is fine — the failure is a turn that is NOTHING BUT the acknowledgement.
  if (t.length <= 120) {
    for (const re of NULL_ACK) {
      if (re.test(t)) return { cls: 'NULL_ACK', snippet: t };
    }
  }

  // A question to the Owner is a legitimate active closer — but ONLY when it is a
  // DECISION only the Owner can make ("¿lo lanzo?", "which of these do you want?").
  // A question of FACT is answerable with a tool call, so ending the turn on one is
  // INTENT_NARRATION wearing a question mark: the Owner has nothing to answer and the
  // screen dies.
  //
  // MEASURED 2026-09-02 (KobiiCraft Core Files). This closer passed the old blanket
  // exemption and produced the exact dead screen this hook exists to kill:
  //   "Lanzo. Primero: ¿existe ya un verificador registrado para la superficie de
  //    login, o tengo que escribirlo?"
  // Zero tool calls. The answer was one Grep away. The Owner had to interrupt.
  // The lesson generalises: A GUARD'S EXEMPTION IS WHERE ITS DEFECT LIVES.
  if (/\?\s*$/.test(t)) {
    const q = t.slice(-320);
    const FACT_QUERY = [
      /¿\s*(existe|hay|est[áa]|est[áa]n|cu[áa]l|cu[áa]nt[oa]s|d[óo]nde)\b/i,
      /\b(o\s+)?tengo\s+que\s+\w+/i,
      /\bdo\s+I\s+(need|have)\s+to\b/i,
      /\b(is|are)\s+there\b/i,
      /\bdoes\s+\w+\s+exist\b/i,
      /\b(what|where|how\s+many)\s+(is|are|does)\b/i,
    ];
    if (!FACT_QUERY.some((re) => re.test(q))) return null;
    return { cls: 'RHETORICAL_QUESTION', snippet: q.slice(-160) };
  }

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
  RHETORICAL_QUESTION:
    'This turn is about to end on a question of FACT, not a decision. You asked ' +
    'something you can answer yourself with a tool call (does X exist? is there a ' +
    'Y? do I have to write it?). The Owner has nothing to answer, so the screen ' +
    'freezes. A question mark does not make narration into a handoff.',
  SILENT_TOOL_STOP:
    'This turn is about to end on a SILENT TOOL STOP: your last message was a ' +
    'tool call and NOTHING ELSE. The tool succeeded, the turn is over, and the ' +
    'Owner is looking at an executed action with no sentence attached — they ' +
    'cannot tell whether you finished, crashed, or are still thinking. A tool ' +
    'call is work, not a report. Say what landed and what comes next.',
  NULL_ACK:
    'This turn is about to end on a NULL ACKNOWLEDGEMENT: the whole message ' +
    'dismisses a system event as needing no reply. A background task-notification ' +
    'is a WORK TRIGGER, not a message with a politeness slot — status=completed ' +
    'means its output is on disk RIGHT NOW and the next action is yours. Read the ' +
    'output-file named in the notification and continue, in THIS turn.',
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

    // A tool-call turn that ALSO carries text is ordinary agentic work — exempt.
    // A tool-call turn carrying NO text is not. At Stop the loop is already over,
    // so a silent tool-only final message is not "work in progress": it is the
    // Owner staring at an executed action with no sentence attached.
    //
    // MEASURED 2026-09-02 (KobiiCraft Core Files). This exemption was blanket, and
    // it passed the exact dead screen this hook exists to kill: an Edit landed on
    // MapRejectionGate.java, the turn ended with zero text, the Owner saw a frozen
    // screen and had to interrupt. NULL_ACK then caught only the SECOND screen (the
    // "No response requested." reply to the nudge) — the first one was invisible.
    //
    // Same lesson as the question-mark exemption 130 lines above, which this file
    // had ALREADY written down as "a guard's exemption is where its defect lives"
    // while still carrying this second blanket pass. Writing a lesson beside one
    // exemption does not apply it to the others.
    // 2026-09-04: `null` here was the blanket pass. A tool-call turn WITH text
    // now goes through classify() in tool-turn mode (PASSIVE_WAIT only) instead
    // of skipping detection entirely. See the note above classify().
    const verdict = turn.usedTool
      ? ((turn.text || '').trim()
          ? classify(turn.text, { toolTurn: true })
          : { cls: 'SILENT_TOOL_STOP', snippet: '' })
      : classify(turn.text);
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
