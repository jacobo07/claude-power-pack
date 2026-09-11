#!/usr/bin/env node
/**
 * closer-guard.js â€” Stop hook. Kills the "dead screen" turn-ending classes.
 *
 * ORIGIN (2026-08-27, TUA-X): a turn ended with the text
 *   "Recording the session objective honestly."
 * and no tool call. The Owner saw a frozen screen waiting for an action that
 * was never going to arrive. The failure was ALREADY documented in the vault
 * (feedback-intent-narration-closer-deadscreen.md,
 *  feedback-empty-closer-deadscreen.md, global CLAUDE.md rules (H)/(G)) and it
 * recurred anyway.
 *
 * NOTE (R265, 2026-09-05): CLAUDE.md rule (H) has since been RETIRED, precisely
 * because this hook enforces it â€” its clauses (2) "never close on a passive
 * wait" and (3) "a turn must end with assistant text" are PASSIVE_WAIT and
 * EMPTY below. Its one non-enforceable clause (on a <task-notification>, Read
 * the output-file that same turn) was folded into CLAUDE.md rule (F). Rule (G)
 * still exists. Updating this reference is the point of UKDL T-392: when a
 * state changes, every pointer written about it in the old state is stale, and
 * the round that changes the state owns fixing them.
 *
 * That recurrence IS the finding: a rule that lives only in prose does not
 * fire. Prose is advisory to a model that is already mid-mistake. This hook
 * moves the rule from prose into the control flow, where it executes whether
 * or not the model remembered it.
 *
 * FIVE BANNED CLOSER CLASSES (all produce the same Owner-visible symptom).
 * The list GREW TWICE on 2026-09-02, both times from a real dead screen that
 * walked past every class then defined â€” which is this file's standing lesson:
 * A GUARD ENUMERATES SHAPES, AND AN UNENUMERATED SHAPE PASSES EVEN THOUGH THE
 * DAMAGE IS IDENTICAL. Expect a sixth; look at the borders, not the centre.
 *   4. RHETORICAL_QUESTION â€” a closing question of FACT, not of decision. The
 *                     Owner has nothing to answer, because a tool call would.
 *                     Added after the blanket "ends in ?" exemption was
 *                     measured producing the exact dead screen it exempted.
 *   5. NULL_ACK     â€” the whole turn dismisses a system event as needing no
 *                     reply ("No response requested."). A task-notification is
 *                     a WORK TRIGGER, not a message with a politeness slot.
 * Self-test: hooks/tests/test-closer-guard-nullack.js â€” two-way, 17/17. Half of
 * its cases MUST NOT fire, and that half is the half that matters: a gate
 * exercised only where it should trip would pass with every clause deleted.
 *   1. EMPTY        â€” turn ends with no assistant text at all.
 *   2. PASSIVE_WAIT â€” "awaiting", "standing by", "I'll wait", "in progress".
 *                     Implies the Owner must wait; usually the work is done
 *                     or the next step is the agent's.
 *   3. INTENT_NARRATION â€” a short trailing sentence announcing the next
 *                     action ("Recording X.", "Let me check Y.", "Now I'll
 *                     update Z.") with no tool call after it. The agent
 *                     described the move instead of making it.
 *
 * DESIGN CONSTRAINTS (deliberate, and each one is load-bearing):
 *   - Fail-open ABSOLUTE. Any parse error, missing transcript, unreadable
 *     line â†’ {continue:true}. A guard that breaks the session is worse than
 *     the bug it guards.
 *   - Never block twice in a row for the same session. If the model re-emits
 *     a bad closer after being told once, we let it through. An infinite
 *     block loop is itself a dead screen â€” the exact thing being prevented.
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
  // MEASURED 2026-09-11 (Jacobo). The line above matches "I'll wait" and "Ill
  // wait" and returns null on "I will wait" -- the UNCONTRACTED form of the
  // single most canonical dead-screen closer in this doctrine. On a text-only
  // turn INTENT_NARRATION happened to catch it, which is why it never showed;
  // on a TOOL-CALL turn only PASSIVE_WAIT runs, so the hole was wide open on
  // exactly the shape rule (G) was written for. Seventh instance of this
  // file's standing lesson, and the cheapest yet: the unenumerated shape was
  // one word away from an enumerated one.
  // The `(?!-)` is not decoration. `\b` fires inside a hyphenated word, so a
  // bare \bwait\b matches "I will wait-list the module" -- caught by this
  // class's own negative control, which is the argument for shipping one.
  /\b(?:i|we)\s+will\s+wait\b(?!-)/i,
  /\b(?:i'?m|i\s+am|we'?re|we\s+are)\s+waiting\b(?!-)/i,
  /\blet'?s\s+wait\b(?!-)/i,
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
  /\bavisar[Ã©e]\s+cuando\b/i,

  // --- SURVEILLANCE + CONDITIONAL TRIGGER (added 2026-09-11, KobiiSports) ---
  // MEASURED. A turn ended with a tool call and this text:
  //   "Mete la tarjeta en el lector ahora. Me quedo vigilando y, en cuanto
  //    aparezca, lanzo el formateo solo."
  // Dead screen. The Owner had to interrupt. classify() returned null in BOTH
  // tool-turn and text-only mode, while four positive controls in the same probe
  // fired correctly â€” so the miss was aperture, not wiring.
  //
  // THE CLASS THAT WAS MISSING IS NOT A LANGUAGE, IT IS A SYNONYM FAMILY.
  // Every pattern above encodes ESPERAR / WAIT. A passive wait does not have to
  // use the word "wait": it can be expressed as SURVEILLANCE ("me quedo
  // vigilando", "quedo pendiente", "estare atento", "watching for", "keep an eye
  // out") or as a CONDITIONAL TRIGGER ("en cuanto aparezca, lanzo", "as soon as
  // it lands, I'll run it"). Both hand the next move to an event outside the
  // agent's control, which is the exact damage. The probe measured 10 such
  // shapes passing clean, SIX OF THEM IN ENGLISH â€” so this was never the
  // Spanish-coverage gap it first looked like, and patching only the Spanish
  // side would have been this file's standing lesson unapplied a seventh time.
  //
  // The conditional-trigger pattern must NOT eat Spanish "en cuanto A" (= "as
  // regards"), which opens ordinary REPORTS: "En cuanto a los ficheros, 6 de 6
  // pasan." Hence the negative lookahead plus the requirement of a comma-clause
  // carrying a first-person present verb â€” an announcement defers an action,
  // a report states one.
  /\b(?:me\s+)?(?:quedo|quedamos)\s+(?:vigilando|mirando|observando|atent[oa]s?|pendientes?|al\s+tanto|a\s+la\s+escucha)\b/i,
  /\b(?:estar[Ã©e]|estar[Ã©e]mos|estoy|estamos|sigo|seguimos|seguir[Ã©e])\s+(?:atent[oa]s?|pendientes?|vigilando|monitorizando|al\s+tanto)\b/i,
  /\bme\s+mantengo\s+(?:al\s+tanto|atent[oa]|pendiente)\b/i,
  /\ben\s+cuanto\s+(?!a\s)[^.!?,]{1,60},\s*[^.!?]{0,40}\b(?:te\s+\w+|\w+o)\b/i,
  /\bwatching\s+(?:for|to\s+see)\b/i,
  /\bkeep(?:ing)?\s+an\s+eye\s+(?:on|out)\b/i,
  /\bon\s+the\s+lookout\b/i,
  /\bi(?:'ll| will)\s+(?:be\s+)?monitor(?:ing)?\b/i,
  /\bas\s+soon\s+as\s+[^.!?]{0,60},?\s*i(?:'ll| will)\b/i,
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
  // TIER A â€” unambiguous future-intent markers. Spanish announces the next
  // move with a periphrasis ("voy a", "paso a", "dejame") that no report ever
  // uses, so these fire regardless of what else the sentence carries.
  /(?:^|[.!?]\s+)(?:ahora\s+|luego\s+|despu[Ã©e]s\s+)?(?:voy|vamos)\s+a\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:paso|pasamos|procedo|procedemos)\s+a\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)d[Ã©e]jame\s+\w[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:contin[Ãºu]o|contin[Ãºu]amos|sigo|seguimos)\s+con\s+[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)(?:lo\s+siguiente|el\s+siguiente\s+paso)\s+es\s+[^.!?]{0,120}[.!?]?\s*$/i,
  /(?:^|[.!?]\s+)ahora\s+\w+o\b[^.!?]{0,120}[.!?]?\s*$/i,
  //
  // TIER B â€” a bare first-person-present action verb OPENING the final
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
  //
  // PROCLITIC PREFIX (added 2026-09-05, measured). The anchor used to run
  // straight into the verb, so TIER B could only ever see a sentence that OPENS
  // on the verb. Spanish puts the unstressed object pronoun BEFORE it, and that
  // is the ordinary word order, not an edge case: "Lo mido", "La reviso", "Me
  // pongo", "Se corrige", "Le anado". Six of the commonest closer shapes in the
  // Owner's own language walked past a class that had been written FOR that
  // language.
  //
  // MEASURED: the turn "Un detalle que decide un token visible: ... Lo mido con
  // calibracion diferencial contra el editor del mismo video." ended with zero
  // tool calls, produced the dead screen, and classify() returned null on it.
  //
  // This is the fourth instance of this file's own standing lesson, and the
  // sharpest: the previous three were an EXEMPTION that waved a case through.
  // This one is an ANCHOR that never let the case arrive. Both are aperture
  // defects and both read, from outside, as a clean pass. When you add a class
  // for a new language, the grammar of that language is part of the pattern --
  // porting a verb list is not porting a rule.
  /(?:^|[.!?]\s+)(?:(?:me|te|se|lo|la|le|los|las|les|nos|os)\s+){0,2}(?:corrijo|arreglo|reescribo|reviso|compruebo|verifico|actualizo|a[nÃ±]ado|genero|escribo|borro|quito|muevo|copio|despliego|ejecuto|lanzo|instalo|sello|anoto|preparo|cableo|empaqueto|miro|leo|busco|mido|cuento|aplico|pruebo|reintento|ajusto|edito|subo|guardo|limpio|repito|extraigo|pongo)\b[^.!?\d`]{0,110}[.!?]?\s*$/i,
];

// Null acknowledgement: the WHOLE turn is a dismissal of a system event as if it were a
// social remark needing no reply. This is not EMPTY (there IS text), not PASSIVE_WAIT
// (nothing is being waited for), not INTENT_NARRATION (no action is announced) and not a
// question â€” so it walked past all four classes and produced a dead screen anyway.
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
// nobody asked for a response in the first place â€” which is exactly why the phrase is
// wrong: a completed task is a WORK TRIGGER, not a message with a politeness slot.
const NULL_ACK = [
  /^no\s+(?:response|reply|action|further\s+action)\s+(?:is\s+)?(?:requested|required|needed|necessary)\.?$/i,
  /^(?:acknowledged|noted|received|confirmed)\.?$/i,
  /^(?:no\s+)?comment\.?$/i,
  /^nothing\s+(?:to\s+(?:do|add|report)|further)\.?$/i,
];

// --- Aperture repairs (three defects MEASURED 2026-09-05, FIFA 11 Mod) -----
//
// A turn ended with:
//   "All three commits landed; tree clean apart from disposable `build/`.
//    Now the boot brief. Â§34 wants it minimal and self-contained â€” you should
//    not need any archaeology to run it."
// Zero tool calls. Dead screen. classify() returned null. Isolating one
// variable at a time turned up THREE independent defects, and that closer
// needed two of them at once to escape:
//
//   D1 APOSTROPHE. "I'll wait for the notification." fires PASSIVE_WAIT.
//      "Iâ€™ll wait for the notification." returns null. One codepoint apart:
//      U+0027 vs U+2019. Every pattern here spells it ASCII; the model emits
//      the typographic form by default. So the two classes that hinge on a
//      contraction were blind to the form actually written â€” including the
//      single most canonical dead-screen closer in the whole doctrine.
//   D2 ANCHOR. Every INTENT_NARRATION pattern ends `$`, so only the FINAL
//      sentence was ever inspected â€” while the header two hundred lines above
//      says "only the trailing ~2 sentences are inspected". Documented
//      aperture â‰  implemented aperture. Append ANY rationale sentence after an
//      announcement and it vanishes: "Let me check the ledger." fires,
//      "Let me check the ledger. It should be quick." does not.
//   D3 VERBLESS. Every pattern has a verb slot. Spanish and English both
//      announce with a bare noun phrase â€” "Now the boot brief.", "Next, the
//      ledger update.", "Ahora el brief de arranque." â€” and a sentence with no
//      verb cannot match a pattern built around one.
//
// This is this file's own standing lesson in its fifth and sixth instances,
// and the pair is the useful part. The first four were EXEMPTIONS (a case
// waved through) and one ANCHOR (a case never reached). D1 is neither: it is
// an ALPHABET the detector could not read. All three read identically from
// outside â€” a clean pass â€” which is why "no dead screens logged" was never
// evidence that there were none.
//
// D1 is fixed at the INPUT BOUNDARY, not in the patterns. Patching each regex
// would leave the next pattern anyone adds carrying the same bug.

function normalize(s) {
  return String(s || '')
    .replace(/[\u2018\u2019\u201B\u02BC\uFF07]/g, "'")  // â€™ â€˜ â€› Ê¼ ï¼‡ â†’ '
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/\u00A0/g, ' ');
}

/** Last `n` sentences of `text`, nearest-last-first. idx 0 === final sentence. */
function lastSentences(text, n) {
  const parts = String(text).split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
  const out = [];
  for (let i = 0; i < n && i < parts.length; i++) {
    out.push({ text: parts[parts.length - 1 - i], idx: i });
  }
  return out;
}

// A noun-phrase announcement with the verb elided. Deliberately narrow: it must
// OPEN on a sequencing adverb, be short, and carry no finite verb â€” otherwise
// "Now the boot brief is on the card at D:\..." (an honest report opening the
// same way) would trip it. That exclusion is the whole reason this class is
// safe to add, and test-closer-guard-aperture.js drives both sides of it.
const VERBLESS_INTENT =
  /^(?:now|next|then|first|finally|ahora|luego|despu[Ã©e]s|entonces|primero)[,:]?\s+(?:the|a|an|el|la|los|las|un|una)\s+[^.!?]{1,60}[.!?]$/i;

const HAS_FINITE_VERB =
  /\b(?:is|are|was|were|has|have|had|holds?|shows?|reads?|matches|sits|lands|exists?|says|means|carries|proves|remains|stands|looks|comes|goes|does|did|will|can|must|should|lives?|ships?|passes|fails)\b|\b(?:es|son|est[Ã¡a]|est[Ã¡a]n|queda|quedan|tiene|tienen|hay|muestra|confirma|existe|vale|sale|va|van|falta)\b/i;

// Same discipline the Spanish TIER B already uses: an announcement has no
// result in it, a report does.
//
// But a NUMBER IS NOT AUTOMATICALLY A RESULT, and getting that wrong is what
// the sealed ES-OK-09 case caught the moment the D2 window opened. Two closers
// with identical shape â€” announcement, then another sentence â€” must be judged
// in OPPOSITE directions:
//
//   fires:  "Now the boot brief. Â§34 wants it minimal and self-contained."
//           The second sentence CITES a spec. Nothing was produced. Dead screen.
//   passes: "Ahora reviso el gate. El resultado: 19 de 19 en verde."
//           The second sentence REPORTS the outcome of the announced action.
//
// The distinction is the one instrument-before-claim keeps arriving at from the
// other side: a number that POINTS (Â§34, HR-12, U-022, v3) versus a number that
// MEASURES (19 of 19, 1622673 B). Citation-shaped tokens are stripped before
// asking whether anything remains.
function hasResult(sentence) {
  const stripped = String(sentence)
    .replace(/[Â§#]\s*\d+[\w.-]*/g, '')      // Â§34, #12
    .replace(/\b[A-Z]{1,5}-\d+\b/g, '')     // U-022, HR-12, E-213
    .replace(/\bv\d+(?:\.\d+)*\b/gi, '');   // v2, v1.06
  return /[\d`]/.test(stripped);
}

// `opts.toolTurn` = the turn ALSO issued a tool call.
//
// MEASURED 2026-09-04 (FIFA 11 Mod). The call site below used to hand a
// tool-call turn straight to `null` whenever it carried any text, so classify()
// was NEVER RUN on such a turn and PASSIVE_WAIT could not fire on it. That is
// the THIRD instance of this file's own twice-written lesson, "a guard's
// exemption is where its defect lives" â€” a blanket exemption standing between
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
//     alone â€” arguably worse, because the tool call makes it look alive.
function classify(text, opts) {
  const toolTurn = !!(opts && opts.toolTurn);
  const t = normalize(text).trim();   // D1: see the aperture-repair block above
  if (!t) return { cls: 'EMPTY', snippet: '' };

  if (toolTurn) {
    const tail0 = t.slice(-320);
    for (const re of PASSIVE_WAIT) {
      if (re.test(tail0)) return { cls: 'PASSIVE_WAIT', snippet: tail0.slice(-140) };
    }
    return null;
  }

  // Whole-message match, capped short: a long substantive turn that happens to close on
  // "Noted." is fine â€” the failure is a turn that is NOTHING BUT the acknowledgement.
  if (t.length <= 120) {
    for (const re of NULL_ACK) {
      if (re.test(t)) return { cls: 'NULL_ACK', snippet: t };
    }
  }

  // A question to the Owner is a legitimate active closer â€” but ONLY when it is a
  // DECISION only the Owner can make ("Â¿lo lanzo?", "which of these do you want?").
  // A question of FACT is answerable with a tool call, so ending the turn on one is
  // INTENT_NARRATION wearing a question mark: the Owner has nothing to answer and the
  // screen dies.
  //
  // MEASURED 2026-09-02 (KobiiCraft Core Files). This closer passed the old blanket
  // exemption and produced the exact dead screen this hook exists to kill:
  //   "Lanzo. Primero: Â¿existe ya un verificador registrado para la superficie de
  //    login, o tengo que escribirlo?"
  // Zero tool calls. The answer was one Grep away. The Owner had to interrupt.
  // The lesson generalises: A GUARD'S EXEMPTION IS WHERE ITS DEFECT LIVES.
  if (/\?\s*$/.test(t)) {
    const q = t.slice(-320);
    const FACT_QUERY = [
      /Â¿\s*(existe|hay|est[Ã¡a]|est[Ã¡a]n|cu[Ã¡a]l|cu[Ã¡a]nt[oa]s|d[Ã³o]nde)\b/i,
      /\b(o\s+)?tengo\s+que\s+\w+/i,
      /\bdo\s+I\s+(need|have)\s+to\b/i,
      /\b(is|are)\s+there\b/i,
      /\bdoes\s+\w+\s+exist\b/i,
      /\b(what|where|how\s+many)\s+(is|are|does)\b/i,
    ];
    if (!FACT_QUERY.some((re) => re.test(q))) return null;
    return { cls: 'RHETORICAL_QUESTION', snippet: q.slice(-160) };
  }

  // D2: the window is now the last THREE SENTENCES, tested one at a time â€” not
  // one regex anchored to the very end of the message. The old form could only
  // ever see the FINAL sentence, so any announcement followed by a rationale
  // clause walked past it. Widened to 600 chars because three sentences of
  // ordinary prose do not fit in 320.
  const tail = t.slice(-600);

  // PASSIVE_WAIT keeps its whole-tail match: it is never legitimate anywhere
  // near the end of a turn, and several of its patterns carry their own anchors.
  for (const re of PASSIVE_WAIT) {
    if (re.test(tail)) return { cls: 'PASSIVE_WAIT', snippet: tail.slice(-140) };
  }

  const window = lastSentences(tail, 3);

  for (const s of window) {
    // A non-final sentence must carry no result token. An announcement has no
    // evidence in it; a report does. The FINAL sentence keeps its original
    // unfiltered behaviour â€” that is the shipped-and-proven path, and narrowing
    // it here would trade a known detection for an unknown one.
    if (s.idx > 0 && hasResult(s.text)) continue;

    // AN ANNOUNCEMENT FOLLOWED BY ITS OUTCOME IS A REPORT, NOT A DEAD SCREEN.
    // Sealed case ES-OK-09 â€” "Ahora reviso el gate de continuidad. El resultado:
    // 19 de 19 en verde." â€” must NOT fire, and it started firing the instant the
    // D2 window opened. That regression was caught by the suite, not by review,
    // which is the whole argument for rule (K): the widening looked obviously
    // safe and was not. Any LATER sentence carrying a real result discharges the
    // announcement. See hasResult() for why Â§34 is not such a result.
    if (window.some((o) => o.idx < s.idx && hasResult(o.text))) continue;

    // "Let me be clear:" / "Let me explain" are RHETORICAL framing, not
    // announcements of work. They were harmless while only the final sentence
    // was inspected; against a three-sentence window they would fire on
    // ordinary prose. A guard that cries wolf gets switched off with
    // CLAUDE_CLOSER_GUARD=off â€” and an off guard IS the dead screen.
    if (/^let me\s+(?:be\s+(?:clear|precise|specific|blunt|honest|direct)|explain|put|say|start|note)\b/i.test(s.text)) continue;

    for (const re of INTENT_NARRATION) {
      if (re.test(s.text)) return { cls: 'INTENT_NARRATION', snippet: s.text };
    }
    // D3: the verb elided entirely.
    if (VERBLESS_INTENT.test(s.text) && !HAS_FINITE_VERB.test(s.text)) {
      return { cls: 'INTENT_NARRATION', snippet: s.text };
    }
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
    let lastTool = '';
    for (const block of content) {
      if (!block || typeof block !== 'object') continue;
      if (block.type === 'text' && typeof block.text === 'string') text += block.text;
      // `lastTool` exists ONLY to give the anti-loop fingerprint something that can
      // DIFFER between two text-free turns. See the fingerprint comment in run().
      if (block.type === 'tool_use') { usedTool = true; if (block.name) lastTool = String(block.name); }
    }
    return { text, usedTool, lastTool };
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
    'Owner is looking at an executed action with no sentence attached â€” they ' +
    'cannot tell whether you finished, crashed, or are still thinking. A tool ' +
    'call is work, not a report. Say what landed and what comes next.',
  NULL_ACK:
    'This turn is about to end on a NULL ACKNOWLEDGEMENT: the whole message ' +
    'dismisses a system event as needing no reply. A background task-notification ' +
    'is a WORK TRIGGER, not a message with a politeness slot â€” status=completed ' +
    'means its output is on disk RIGHT NOW and the next action is yours. Read the ' +
    'output-file named in the notification and continue, in THIS turn.',
};

function buildReason(cls, snippet) {
  return [
    `CLOSER GUARD â€” ${cls}.`,
    GUIDANCE[cls],
    snippet ? `Your closing text was: "...${snippet.trim()}"` : '',
    '',
    'Do ONE of these before ending the turn:',
    '  1. If you named a next action â€” DO IT NOW with a tool call. Do not ' +
    're-describe it.',
    '  2. If the work is finished â€” state the concrete outcome (what landed, ' +
    'what it proves).',
    '  3. If you are genuinely blocked â€” ask the Owner a direct question they ' +
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

    // A tool-call turn that ALSO carries text is ordinary agentic work â€” exempt.
    // A tool-call turn carrying NO text is not. At Stop the loop is already over,
    // so a silent tool-only final message is not "work in progress": it is the
    // Owner staring at an executed action with no sentence attached.
    //
    // MEASURED 2026-09-02 (KobiiCraft Core Files). This exemption was blanket, and
    // it passed the exact dead screen this hook exists to kill: an Edit landed on
    // MapRejectionGate.java, the turn ended with zero text, the Owner saw a frozen
    // screen and had to interrupt. NULL_ACK then caught only the SECOND screen (the
    // "No response requested." reply to the nudge) â€” the first one was invisible.
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
    const sid = (input && input.session_id) || 'unknown';

    // A CLEAN stop ends the streak. Without this the counter below could only ever
    // rise, so one bad closer early in a session permanently degraded the guard for
    // the rest of it.
    if (!verdict) {
      try {
        const st = readState();
        if (st[sid] && (st[sid].blocked || st[sid].streak)) {
          st[sid] = { blocked: false, fingerprint: '', streak: 0, ts: Date.now() };
          writeState(st);
        }
      } catch (_) { /* fail-open */ }
      return { continue: true };
    }

    // --- Anti-loop -----------------------------------------------------------
    // BUG FIXED 2026-09-04 (measured in production state, not theorised).
    // The key used to be `cls + '|' + turn.text.slice(-80)`. But EMPTY and
    // SILENT_TOOL_STOP are DEFINED BY THE ABSENCE OF TEXT, so their key collapsed to
    // the constant "SILENT_TOOL_STOP|" â€” every silent stop in a session collided with
    // every other one, an hour and fifty good turns apart. The second one was read as
    // "it repeated itself after being told once" and WAVED THROUGH.
    //
    // Evidence: ~/.claude/logs/closer-guard-state.json carried three REAL session
    // UUIDs (4d17ab74â€¦, 86038923â€¦, 2ad9818dâ€¦) with "blocked":false against that exact
    // fingerprint. `blocked:false` is written on one code path only â€” the anti-loop
    // branch. Those are three dead screens this guard consciously let past, which is
    // the precise failure it exists to prevent.
    //
    // Two changes: (1) the key now carries the last tool name, so two text-free stops
    // can differ at all; (2) a STREAK replaces the single boolean, so a genuine
    // repeat-loop still escapes after MAX_STREAK consecutive blocks while ordinary
    // recurrences hours apart are each blocked on their own merits.
    //
    // Generalises: A DE-DUPLICATION KEY BUILT FROM A FIELD THAT IS EMPTY BY
    // CONSTRUCTION IDENTIFIES NOTHING â€” it merges the whole class into one instance
    // and the guard suppresses itself.
    const MAX_STREAK = 2;
    const state = readState();
    const prev = state[sid];
    const body = (turn.text || '').trim();
    const fingerprint = verdict.cls + '|'
      + (body ? body.slice(-80) : 'tool:' + (turn.lastTool || 'unknown'));

    const streak = (prev && prev.fingerprint === fingerprint && prev.streak) ? prev.streak : 0;

    if (streak >= MAX_STREAK) {
      // Told it twice and it still repeats verbatim. Let it through rather than
      // trapping the Owner in a block loop â€” that would be the same disease.
      state[sid] = { blocked: false, fingerprint, streak: 0, ts: Date.now() };
      writeState(state);
      return { continue: true };
    }

    state[sid] = { blocked: true, fingerprint, streak: streak + 1, ts: Date.now() };
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
