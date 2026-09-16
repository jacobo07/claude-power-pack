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
 * NOTE (R265, 2026-09-05): CLAUDE.md rule (H) has since been RETIRED, precisely
 * because this hook enforces it — its clauses (2) "never close on a passive
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
  /\bavisar[ée]\s+cuando\b/i,

  // --- SURVEILLANCE + CONDITIONAL TRIGGER (added 2026-09-11, KobiiSports) ---
  // MEASURED. A turn ended with a tool call and this text:
  //   "Mete la tarjeta en el lector ahora. Me quedo vigilando y, en cuanto
  //    aparezca, lanzo el formateo solo."
  // Dead screen. The Owner had to interrupt. classify() returned null in BOTH
  // tool-turn and text-only mode, while four positive controls in the same probe
  // fired correctly — so the miss was aperture, not wiring.
  //
  // THE CLASS THAT WAS MISSING IS NOT A LANGUAGE, IT IS A SYNONYM FAMILY.
  // Every pattern above encodes ESPERAR / WAIT. A passive wait does not have to
  // use the word "wait": it can be expressed as SURVEILLANCE ("me quedo
  // vigilando", "quedo pendiente", "estare atento", "watching for", "keep an eye
  // out") or as a CONDITIONAL TRIGGER ("en cuanto aparezca, lanzo", "as soon as
  // it lands, I'll run it"). Both hand the next move to an event outside the
  // agent's control, which is the exact damage. The probe measured 10 such
  // shapes passing clean, SIX OF THEM IN ENGLISH — so this was never the
  // Spanish-coverage gap it first looked like, and patching only the Spanish
  // side would have been this file's standing lesson unapplied a seventh time.
  //
  // The conditional-trigger pattern must NOT eat Spanish "en cuanto A" (= "as
  // regards"), which opens ordinary REPORTS: "En cuanto a los ficheros, 6 de 6
  // pasan." Hence the negative lookahead plus the requirement of a comma-clause
  // carrying a first-person present verb — an announcement defers an action,
  // a report states one.
  /\b(?:me\s+)?(?:quedo|quedamos)\s+(?:vigilando|mirando|observando|atent[oa]s?|pendientes?|al\s+tanto|a\s+la\s+escucha)\b/i,
  /\b(?:estar[ée]|estar[ée]mos|estoy|estamos|sigo|seguimos|seguir[ée])\s+(?:atent[oa]s?|pendientes?|vigilando|monitorizando|al\s+tanto)\b/i,
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
  // D6d — THE ENUMERATION IN THE FULL-STOP FORM. MEASURED 2026-09-15 (Jacobo,
  // KobiiCraft Core Files), on the exact bytes that escaped:
  //     "Now measuring what the feasibility owner actually reports for cantina
  //      — including whether N=2 is genuinely reachable via the optional-subset
  //      mechanism."
  // Dead screen; the Owner interrupted and reported it as the cross-repo hang.
  // classify() was replayed on those bytes with {toolTurn:true, endsOnText:true}
  // and returned PASS, so this was a PREDICATE hole, not a delivery failure —
  // the two are indistinguishable from outside and the replay is what separated
  // them.
  //
  // TWO enumerations failed at once, and neither could ever have answered:
  //   * the verb list had fifteen participles and not `measuring`;
  //   * the determiner list had thirteen determiners and not `what`.
  // The comment that used to stand here said, in its own words, that "an
  // enumerated allow-list of English determiners is exactly the shape this file
  // warns about — it answers for the members it lists and is silent for the
  // rest" — and then answered by appending one more member. That is the
  // ELEVENTH instance of this file's standing lesson and the second time it was
  // diagnosed correctly in writing and repaired by widening the list anyway.
  //
  // SO STOP SPELLING THE MEMBERS. Any present participle opening the sentence,
  // any object after it. The two enumerations are replaced by one shape.
  //
  // Why this does not cry wolf — the three guards that already stand around it:
  //   1. On a tool turn it is reachable ONLY behind `endsOnText` (D6): the turn
  //      produced no work after this text. Narration that is followed by a tool
  //      call never reaches here.
  //   2. A later sentence carrying a real result discharges the announcement
  //      (line ~560), so "Ahora reviso el gate. El resultado: 19 de 19." stays
  //      clean — the sealed ES-OK-09 case.
  //   3. Non-final sentences are already filtered by hasResult().
  // The residual false positive is a gerund-SUBJECT report ("Running the suite
  // gave 47/47."), and it is NOT new: the old list already held `running` + `the`
  // and has blocked that shape for 176 blocks across 415 runs without complaint.
  // Generalising extends an accepted trade-off to the members nobody enumerated;
  // it does not introduce a new class. hasResult() is deliberately NOT applied to
  // the final sentence here — the escaped closer carried "N=2", so a digit test
  // would have re-exempted the very bytes this repair exists to catch.
  // And the asymmetry settles it: a false positive costs one rewording, a false
  // negative costs the Owner a frozen screen and an ESC.
  //
  // The lookahead holds the -ing words that open a sentence as a NOUN rather
  // than as an announcement. It is itself an enumeration, which is why it is
  // kept to pronoun-ish words that cannot be read as an action, and why a miss
  // here fails toward accusing rather than excusing.
  //
  // SCOPED OFF THE COLON TIER, and this is the part I got wrong on the first
  // attempt. D6c further down already owns the structural gerund COLON closer and
  // has its own mutation drill. My first version left the terminator optional and
  // allowed ':' in the tail, so it ALSO matched every colon closer — which added
  // no coverage and SHADOWED the existing tier: test-closer-guard-gerund-colon.js
  // deletes D6c and requires its subject to escape, and with a looser duplicate
  // standing behind it the subject stayed blocked, so the drill reported
  // "gate measures nothing". A second, looser copy of a check does not merely cry
  // wolf — IT DISARMS THE DRILL THAT PROVES THE FIRST COPY WORKS, silently, while
  // every other test stays green. Hence the MANDATORY [.!?] and ':' excluded from
  // the tail: a colon closer falls through to D6c, where it belongs.
  /(?:^|[.!?]\s+)(?:now\s+|next\s+|first\s+|then\s+)?(?!nothing\b|something\b|anything\b|everything\b|during\b|morning\b|evening\b)[a-z]{3,}ing\s+\S[^.!?:]{0,160}[.!?]\s*$/i,

  // D6b — THE COLON CLOSER. MEASURED 2026-09-15 (Jacobo, GEO-audit R266) on the
  // exact bytes that escaped:
  //     "Checking staging's actual state:"
  // A colon promises that the thing follows. When the message ENDS there, the
  // promise is the whole closer and nothing was delivered — the purest form of
  // this class, and the one the Owner reports most often, because a colon reads
  // as "output is coming" far more strongly than a full stop does.
  //
  // Every pattern above requires a terminator in [.!?], so the colon form could
  // not match ANY of them. That is the tenth instance of this file's standing
  // lesson and the second found in one session: the guard enumerated how a
  // sentence ends and a whole punctuation mark was outside the enumeration.
  //
  // Anchored to `:\s*$`, so a colon that actually introduces content cannot
  // match — the list, table or code block after it is non-whitespace and the
  // anchor fails. That is what keeps this from firing on ordinary prose.
  /(?:^|[.!?]\s+|\n\s*)(?:now\s+)?(?:recording|writing|updating|adding|creating|running|checking|reading|committing|verifying|building|fixing|distilling|investigating|inspecting|generating|dispatching|restarting|deploying|uploading|auditing)\b[^.!?\n]{0,120}:\s*$/i,

  // D6c — THE STRUCTURAL COLON TIER. A gerund is MORPHOLOGY, not vocabulary:
  // `profiling` escaped D6b's enumerated list for the same reason `measuring`
  // escaped the full-stop list above. Owned and mutation-drilled by
  // test-closer-guard-gerund-colon.js, which deletes exactly this line and
  // requires its subject to escape again — so the line is load-bearing for that
  // gate as well as for the closer it catches.
  //
  // RESTORED 2026-09-15 after I deleted it by accident. Repairing D6b's
  // enumeration, I wrote a generalised colon pattern OVER this one, then reverted
  // my version back to the enumerated text — and the revert took D6c with it,
  // because my edit had replaced both tiers with a single line. The suite caught
  // it in one run ("could not find the D6c structural pattern to mutate"), which
  // is the argument for a drill that names the line it needs rather than merely
  // asserting behaviour: behaviour alone would still have looked green, since the
  // full-stop tier I had just added covered the colon case too.
  /(?:^|[.!?]\s+|\n\s*)(?:now\s+)?[a-z]{3,}ing\s+\w+\s+\w[^.!?\n]{0,120}:\s*$/i,


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
  /(?:^|[.!?]\s+)(?:(?:me|te|se|lo|la|le|los|las|les|nos|os)\s+){0,2}(?:corrijo|arreglo|reescribo|reviso|compruebo|verifico|actualizo|a[nñ]ado|genero|escribo|borro|quito|muevo|copio|despliego|ejecuto|lanzo|instalo|sello|anoto|preparo|cableo|empaqueto|miro|leo|busco|mido|cuento|aplico|pruebo|reintento|ajusto|edito|subo|guardo|limpio|repito|extraigo|pongo)\b[^.!?\d`]{0,110}[.!?]?\s*$/i,
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

// --- Aperture repairs (three defects MEASURED 2026-09-05, FIFA 11 Mod) -----
//
// A turn ended with:
//   "All three commits landed; tree clean apart from disposable `build/`.
//    Now the boot brief. §34 wants it minimal and self-contained — you should
//    not need any archaeology to run it."
// Zero tool calls. Dead screen. classify() returned null. Isolating one
// variable at a time turned up THREE independent defects, and that closer
// needed two of them at once to escape:
//
//   D1 APOSTROPHE. "I'll wait for the notification." fires PASSIVE_WAIT.
//      "I’ll wait for the notification." returns null. One codepoint apart:
//      U+0027 vs U+2019. Every pattern here spells it ASCII; the model emits
//      the typographic form by default. So the two classes that hinge on a
//      contraction were blind to the form actually written — including the
//      single most canonical dead-screen closer in the whole doctrine.
//   D2 ANCHOR. Every INTENT_NARRATION pattern ends `$`, so only the FINAL
//      sentence was ever inspected — while the header two hundred lines above
//      says "only the trailing ~2 sentences are inspected". Documented
//      aperture ≠ implemented aperture. Append ANY rationale sentence after an
//      announcement and it vanishes: "Let me check the ledger." fires,
//      "Let me check the ledger. It should be quick." does not.
//   D3 VERBLESS. Every pattern has a verb slot. Spanish and English both
//      announce with a bare noun phrase — "Now the boot brief.", "Next, the
//      ledger update.", "Ahora el brief de arranque." — and a sentence with no
//      verb cannot match a pattern built around one.
//
// This is this file's own standing lesson in its fifth and sixth instances,
// and the pair is the useful part. The first four were EXEMPTIONS (a case
// waved through) and one ANCHOR (a case never reached). D1 is neither: it is
// an ALPHABET the detector could not read. All three read identically from
// outside — a clean pass — which is why "no dead screens logged" was never
// evidence that there were none.
//
// D1 is fixed at the INPUT BOUNDARY, not in the patterns. Patching each regex
// would leave the next pattern anyone adds carrying the same bug.

function normalize(s) {
  return String(s || '')
    .replace(/[\u2018\u2019\u201B\u02BC\uFF07]/g, "'")  // ’ ‘ ‛ ʼ ＇ → '
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
// OPEN on a sequencing adverb, be short, and carry no finite verb — otherwise
// "Now the boot brief is on the card at D:\..." (an honest report opening the
// same way) would trip it. That exclusion is the whole reason this class is
// safe to add, and test-closer-guard-aperture.js drives both sides of it.
const VERBLESS_INTENT =
  /^(?:now|next|then|first|finally|ahora|luego|despu[ée]s|entonces|primero)[,:]?\s+(?:the|a|an|el|la|los|las|un|una)\s+[^.!?]{1,60}[.!?]$/i;

const HAS_FINITE_VERB =
  /\b(?:is|are|was|were|has|have|had|holds?|shows?|reads?|matches|sits|lands|exists?|says|means|carries|proves|remains|stands|looks|comes|goes|does|did|will|can|must|should|lives?|ships?|passes|fails)\b|\b(?:es|son|est[áa]|est[áa]n|queda|quedan|tiene|tienen|hay|muestra|confirma|existe|vale|sale|va|van|falta)\b/i;

// Same discipline the Spanish TIER B already uses: an announcement has no
// result in it, a report does.
//
// But a NUMBER IS NOT AUTOMATICALLY A RESULT, and getting that wrong is what
// the sealed ES-OK-09 case caught the moment the D2 window opened. Two closers
// with identical shape — announcement, then another sentence — must be judged
// in OPPOSITE directions:
//
//   fires:  "Now the boot brief. §34 wants it minimal and self-contained."
//           The second sentence CITES a spec. Nothing was produced. Dead screen.
//   passes: "Ahora reviso el gate. El resultado: 19 de 19 en verde."
//           The second sentence REPORTS the outcome of the announced action.
//
// The distinction is the one instrument-before-claim keeps arriving at from the
// other side: a number that POINTS (§34, HR-12, U-022, v3) versus a number that
// MEASURES (19 of 19, 1622673 B). Citation-shaped tokens are stripped before
// asking whether anything remains.
function hasResult(sentence) {
  const stripped = String(sentence)
    .replace(/[§#]\s*\d+[\w.-]*/g, '')      // §34, #12
    .replace(/\b[A-Z]{1,5}-\d+\b/g, '')     // U-022, HR-12, E-213
    .replace(/\bv\d+(?:\.\d+)*\b/gi, '');   // v2, v1.06
  return /[\d`]/.test(stripped);
}

// D7 (2026-09-15, Orca X). The head-clause twin of VERBLESS_INTENT above.
//
// VERBLESS_INTENT models the announcement as the WHOLE sentence: it caps the tail
// at 60 chars and requires the terminator. Append ", so <rationale>" and BOTH
// fail — the cap blows and the clause donates the finite verb that disarms the
// !HAS_FINITE_VERB test. The measured escape is in the D7 block in classify().
//
// So this variant drops the terminator and the cap and stops at the comma: it is
// only ever run against a HEAD already cut at the subordinator, where a length
// limit would just re-open the same hole one clause further along.
const VERBLESS_INTENT_HEAD =
  /^(?:now|next|then|first|finally|ahora|luego|despu[ée]s|entonces|primero)[,:]?\s+(?:the|a|an|el|la|los|las|un|una)\s+[^.!?,]{1,80}$/i;

// Subordinators only — the words that introduce commentary ON an announcement.
// `and` / `but` are deliberately absent: they coordinate two peers, so the text
// after them can be the delivery itself rather than a gloss on a promise.
const RATIONALE_CLAUSE =
  /,\s*(?:so|because|since|which|while|as|to|for|porque|para|que|mientras)\b/i;

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
  // D6. Absent => false, so a caller that cannot supply the order bit keeps the
  // pre-D6 behaviour instead of inheriting the stricter branch. This binding is
  // not optional bookkeeping: the branch below reads it, 'use strict' is on, and
  // an unbound read throws a ReferenceError that this hook's absolute fail-open
  // converts into SILENCE — a guard that is dead precisely where it was repaired.
  const endsOnText = !!(opts && opts.endsOnText);
  const t = normalize(text).trim();   // D1: see the aperture-repair block above
  if (!t) return { cls: 'EMPTY', snippet: '' };

  if (toolTurn) {
    const tail0 = t.slice(-320);
    for (const re of PASSIVE_WAIT) {
      if (re.test(tail0)) return { cls: 'PASSIVE_WAIT', snippet: tail0.slice(-140) };
    }

    // D6 / MEASURED 2026-09-15 (Jacobo, KobiiCraft Core Files). NINTH instance of
    // this file's standing lesson, and the largest aperture left in it.
    //
    // A turn ended with a PowerShell call, then this text, then nothing:
    //     "Checking staging's actual state:"
    // Dead screen; the Owner had to interrupt, and reported it as the cross-repo
    // hang. classify() RAN (the heartbeat advanced) and returned null, because
    // INTENT_NARRATION is exempt on any turn carrying a tool call.
    //
    // THE EXEMPTION'S PREMISE IS A POSITION CLAIM DECIDED BY A PRESENCE TEST.
    // The comment defending it says trailing narration is fine because "the work
    // followed" — true only when a tool_use block comes AFTER the final text.
    // `usedTool` cannot see order, so both of these were being waved through:
    //     text("Let me check X") -> tool_use            legitimate, work followed
    //     tool_use -> text("Let me check X") -> END     dead screen, nothing followed
    // They are opposite outcomes and the guard could not tell them apart, so it
    // exempted both — and the second is the single most common shape of the hang.
    //
    // `endsOnText` is that missing order bit, read from the chronologically last
    // assistant record in lastAssistantTurn(). Unknown stays false, so a parser
    // that cannot tell keeps today's behaviour (D4: a false accusation costs more
    // than a miss).
    if (!endsOnText) return null;

    // A closing QUESTION stays exempt on a tool turn: the decision-vs-fact
    // discriminator below is tuned for text-only turns, and re-opening it here
    // would risk firing on a legitimate Owner-only question that followed real
    // work. Narrow on purpose — this repair buys INTENT_NARRATION, nothing else.
    if (/\?\s*$/.test(t)) return null;

    // Fall through to the SENTENCE-WINDOW intent check below rather than
    // re-testing INTENT_NARRATION here. That path carries two guards this branch
    // must not lose: a later sentence bearing a real result discharges the
    // announcement (hasResult), and "Let me be clear/explain" is framing, not
    // work. A second, looser copy of the check is how a guard starts crying wolf,
    // and an off guard IS the dead screen.
  }

  // Whole-message match, capped short: a long substantive turn that happens to close on
  // "Noted." is fine — the failure is a turn that is NOTHING BUT the acknowledgement.
  // Skipped on a tool turn: a turn that did real work is not a null acknowledgement.
  if (!toolTurn && t.length <= 120) {
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
  // MEASURED 2026-09-14 (KobiiCraft Core Files), FALSE POSITIVE. The Owner was
  // handed two production options — revert the config, or move the job to
  // WorldGuard — and the turn closed "¿Cuál de las dos?". That is the most
  // Owner-only question there is, and the class fired on it, because `cu[áa]l`
  // sat in FACT_QUERY.
  //
  // The repair is NOT to drop `cuál`. An interrogative does not decide the
  // class: "¿cuál es el uuid?" is a fact and "¿cuál de las dos?" is a decision,
  // and they share the word. THE DISCRIMINATOR IS WHETHER THE TURN OFFERED THE
  // ALTERNATIVES. A question that selects among options the assistant just laid
  // out cannot be answered by a tool call, by construction — the tool has no
  // access to what the Owner wants.
  //
  // Deliberately narrow, because a wide exemption here would re-open the exact
  // dead screen this class was sealed for. The measured 2026-09-02 case,
  //   "Lanzo. Primero: ¿existe ya un verificador registrado ... o tengo que
  //    escribirlo?"
  // carries a disjunction too ("o tengo que"), so A BARE `o` MUST NOT EXEMPT.
  // It has no enumerated list and does not ask the Owner to pick among items
  // the turn presented, so it still blocks. That case is pinned as a red-branch
  // test; if this exemption ever swallows it, the test goes red.
  if (/\?\s*$/.test(t)) {
    const q = t.slice(-320);

    // Two or more enumerated items ANYWHERE in the message: "1. …" / "2) …",
    // with or without bold. Scanned over the whole text, not the tail, because
    // the options are stated above the question that closes on them.
    const enumerados = (t.match(/(?:^|\n)\s*(?:\*\*|__)?\d[.)]\s/g) || []).length;

    // Or the question itself names the act of choosing among presented items.
    const PIDE_ELEGIR = [
      /\bcu[áa]l\s+de\s+(las|los|ellas|ellos|est[ao]s)\b/i,
      /\bcu[áa]l\s+(prefieres|prefiere|eliges|elegimos|quieres|escoges)\b/i,
      /\b(ambas|ambos|las\s+dos|los\s+dos)\s*\?\s*$/i,
      /\bwhich\s+(of\s+(the|these|those)|one)\b/i,
      /\bwhich\s+(do|would)\s+you\b/i,
      /\b(opci[óo]n|option)\s+[ab12]\b/i,
    ];
    if (enumerados >= 2 || PIDE_ELEGIR.some((re) => re.test(q))) return null;

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

  // D2: the window is now the last THREE SENTENCES, tested one at a time — not
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
    // unfiltered behaviour — that is the shipped-and-proven path, and narrowing
    // it here would trade a known detection for an unknown one.
    if (s.idx > 0 && hasResult(s.text)) continue;

    // AN ANNOUNCEMENT FOLLOWED BY ITS OUTCOME IS A REPORT, NOT A DEAD SCREEN.
    // Sealed case ES-OK-09 — "Ahora reviso el gate de continuidad. El resultado:
    // 19 de 19 en verde." — must NOT fire, and it started firing the instant the
    // D2 window opened. That regression was caught by the suite, not by review,
    // which is the whole argument for rule (K): the widening looked obviously
    // safe and was not. Any LATER sentence carrying a real result discharges the
    // announcement. See hasResult() for why §34 is not such a result.
    if (window.some((o) => o.idx < s.idx && hasResult(o.text))) continue;

    // "Let me be clear:" / "Let me explain" are RHETORICAL framing, not
    // announcements of work. They were harmless while only the final sentence
    // was inspected; against a three-sentence window they would fire on
    // ordinary prose. A guard that cries wolf gets switched off with
    // CLAUDE_CLOSER_GUARD=off — and an off guard IS the dead screen.
    if (/^let me\s+(?:be\s+(?:clear|precise|specific|blunt|honest|direct)|explain|put|say|start|note)\b/i.test(s.text)) continue;

    for (const re of INTENT_NARRATION) {
      if (re.test(s.text)) return { cls: 'INTENT_NARRATION', snippet: s.text };
    }
    // D3: the verb elided entirely.
    if (VERBLESS_INTENT.test(s.text) && !HAS_FINITE_VERB.test(s.text)) {
      return { cls: 'INTENT_NARRATION', snippet: s.text };
    }

    // D7 — THE RATIONALE CLAUSE DISARMS D3. MEASURED 2026-09-15 (Jacobo, Orca X)
    // on the exact bytes of a turn that froze this very session:
    //     "Now the destructive module's pre-SIGKILL recheck, so the reason it logs is true."
    // An Edit ran, then this text, then nothing. The Owner reported it as the
    // cross-repo hang. Replayed with {toolTurn:true, endsOnText:true} beside two
    // known-red controls that both fired: PASS. D6 had landed forty minutes
    // earlier and does not reach it — a PREDICATE hole, not a delivery failure,
    // and only the replay separates those two.
    //
    // ONE COMMA IS THE ENTIRE BYPASS, and it defeats D3 twice over: the clause
    // supplies the finite verbs ("logs", "is") that !HAS_FINITE_VERB tests for,
    // and it blows the 60-char cap in VERBLESS_INTENT. Either alone was enough.
    //
    // This file already learned this AT SENTENCE LEVEL — D2 widened to a
    // three-sentence window precisely because "append any rationale SENTENCE
    // after an announcement" walked past a final-anchored regex. The identical
    // move INSIDE one sentence was left open, which makes this the twelfth
    // instance of the standing lesson: the aperture was documented, and the
    // repair was scoped to the altitude where the damage had been seen.
    //
    // THE ANNOUNCEMENT IS THE HEAD CLAUSE. Everything after the subordinator is
    // commentary on it, so judging the head is what stops a comma from being a
    // bypass. Two guards keep it from crying wolf: the head must ITSELF be
    // verbless (so "Now the tree is stable, so we can ship." passes on "is"), and
    // the FULL sentence must carry no evidence token — unlike D3, which
    // deliberately skips hasResult. A sentence that cites a measurement is a
    // report: "Now the gate, which passed 19/19, is sealed." passes on the digits
    // alone, without the head test ever mattering.
    // A PARENTHETICAL WEARS THE SAME COSTUME, and it is the false positive this
    // tier would otherwise ship: "Now the interesting part, as the docs explain,
    // is the cache." has a verbless head and a subordinator after the comma, and
    // it is ordinary prose. The discriminator is that a parenthetical CLOSES and
    // the sentence then resumes with a predicate about the head — so a second
    // comma followed by a finite verb means the head was a subject, not an
    // announcement. Found by writing the drill's green half before shipping,
    // which is the only reason it is not a live regression.
    const rationaleAt = s.text.search(RATIONALE_CLAUSE);
    if (rationaleAt > 0) {
      const head = s.text.slice(0, rationaleAt);
      const rest = s.text.slice(rationaleAt + 1);
      const closingComma = rest.indexOf(',');
      const parenthetical = closingComma >= 0 && HAS_FINITE_VERB.test(rest.slice(closingComma));
      if (
        !parenthetical &&
        VERBLESS_INTENT_HEAD.test(head) &&
        !HAS_FINITE_VERB.test(head) &&
        !hasResult(s.text)
      ) {
        return { cls: 'INTENT_NARRATION', snippet: s.text };
      }
    }
  }
  return null;
}

// --- Transcript reading ----------------------------------------------------

/** The last assistant TURN: all of its text, and whether it issued any tool_use.
 *
 * D4 — A TURN IS MANY RECORDS, AND THIS READ ONE. MEASURED 2026-09-14 (Jacobo/Neom).
 *
 * The previous body scanned backwards for the FIRST record with role==='assistant'
 * and returned it. That is not a turn. Claude Code appends ONE RECORD PER CONTENT
 * BLOCK, so a turn that writes a paragraph and then calls a tool lands as two
 * records — text-only, then tool-only — and the last of them carries `text: ''`
 * with `usedTool: true`. Which is, exactly and by construction, the
 * SILENT_TOOL_STOP signature.
 *
 * Measured by calling this very function on the live transcript's own bytes:
 *     lastAssistantTurn(...) -> { textLen: 0, usedTool: true, lastTool: 'PowerShell' }
 *     assistant records in that same turn: 51  (8 of them carrying text)
 * Eight text-bearing records, and the guard reported a turn with no text at all.
 * It blocked three consecutive turns that each ended in several paragraphs of
 * prose, in a session doing nothing wrong.
 *
 * THIS IS THIS FILE'S STANDING LESSON IN A NEW FAMILY, AND THE FAMILY IS THE POINT.
 * Every previous instance was about the PATTERNS: an exemption that waved a case
 * through, an anchor that never let one arrive, an alphabet the regexes could not
 * read, a language they did not speak. All of those made the guard SILENT. This one
 * is the opposite failure and it lives one layer down, in the INPUT: the patterns
 * were fine and the subject handed to them was a fragment. A detector reading the
 * wrong UNIT does not go quiet — it ACCUSES. And a false accusation costs more than
 * a miss, because it also teaches the Owner to reach for CLAUDE_CLOSER_GUARD=off,
 * and an off guard is the dead screen this file exists to prevent. Check the
 * aperture of the READ before ever touching a regex.
 *
 * The turn boundary: walk back over assistant records, and over `user` records that
 * are TOOL RESULTS — those are the harness answering, still inside the turn. Stop at
 * the first genuine human message. Concatenate every text block found, in order.
 *
 * What this does NOT weaken: the sealed 2026-09-02 case (an Edit landed and the turn
 * carried zero text anywhere) still has zero text after aggregation, so
 * SILENT_TOOL_STOP still fires on it. The class now means what its own guidance text
 * always claimed — "a tool call and NOTHING ELSE" — measured over the whole turn
 * instead of over whichever fragment happened to be appended last.
 */
// D6 — THE READ IS O(WHOLE SESSION) AND THE ANSWER IS IN THE LAST 4%.
// MEASURED 2026-09-14 (Jacobo/Neom), on this estate's own dispatcher log.
//
// A turn ends at the last human message, so the only bytes that can change the
// verdict are the ones after it. Measured on the live 25.9 MB transcript of the
// session that reported the dead screen:
//     bytes actually needed (since the last human message) = 978.5 KB  (3.695%)
//     readFileSync of the whole file                       = 166 ms   (87% of run())
// And on this estate's largest transcript, 95.2 MB:
//     readFileSync alone = 5386 ms   against a dispatcher budget of 8000 ms
// i.e. on a long session the guard could spend most of its budget BEFORE looking
// at a single character, and a killed child reports exactly what a clean pass
// reports — the silent-dead-gate shape this file already carries a heartbeat for.
// `hook-dispatcher-errors.log` holds 48 ETIMEDOUT entries for this script.
//
// So: read a WINDOW off the end. The window is sized in megabytes, not turns,
// because a turn's length is not knowable before reading it.
//
// WHICH DIRECTION THIS FAILS IN IS THE WHOLE ARGUMENT FOR ITS SAFETY. If the
// window is too small to reach the last human message, the walk simply runs out
// of lines and returns MORE text than the real turn (the tail of earlier turns
// gets aggregated in). More text can only make EMPTY and SILENT_TOOL_STOP LESS
// likely to fire, and every other class matches against the END of the joined
// text, which is unchanged. So a short window degrades toward a MISS, never
// toward a FALSE ACCUSATION — which is the ordering D4 paid for.
const TAIL_BYTES = Math.max(
  262144,
  parseInt(process.env.CLAUDE_CLOSER_GUARD_TAIL_BYTES || '', 10) || 4 * 1024 * 1024
);

/** The last `TAIL_BYTES` of a file, starting at a line boundary. */
function readTail(filePath) {
  const size = fs.statSync(filePath).size;
  if (size <= TAIL_BYTES) return fs.readFileSync(filePath, 'utf8');

  const start = size - TAIL_BYTES;
  const buf = Buffer.allocUnsafe(TAIL_BYTES);
  const fd = fs.openSync(filePath, 'r');
  try { fs.readSync(fd, buf, 0, TAIL_BYTES, start); } finally { fs.closeSync(fd); }

  // Drop the leading partial line AND any partial UTF-8 sequence with it: the
  // window boundary can land mid-codepoint, and a lone replacement character at
  // the head of a JSON line makes that line unparseable — which the loop already
  // skips, but dropping it here keeps the fragment out of the text entirely.
  const s = buf.toString('utf8');
  const nl = s.indexOf('\n');
  return nl === -1 ? '' : s.slice(nl + 1);
}

function lastAssistantTurn(transcriptPath) {
  const raw = readTail(transcriptPath);
  const lines = raw.split(/\r?\n/);

  const chunks = [];
  let usedTool = false;
  let productiveTool = false;
  let lastTool = '';
  let sawAssistant = false;

  // D6 (2026-09-15, Jacobo) — POSITION, NOT PRESENCE. See the block above
  // classify(). `usedTool` answers "did this turn call a tool?"; the tool-turn
  // exemption needs "did a tool call come AFTER the last text?". Only the second
  // separates ordinary narration (text -> tool_use -> work) from the dead screen
  // (tool_use -> text -> END). Set once, from the chronologically LAST assistant
  // record — walking backwards, that is the FIRST one met.
  let endsOnText = null;

  // D5 (see the block above run()): ids whose tool_result came back `is_error`.
  // Walking backwards, results are met BEFORE the tool_use they answer, so the
  // set is already complete by the time each tool_use block is inspected.
  const erroredIds = new Set();

  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;

    let rec;
    try { rec = JSON.parse(line); } catch { continue; }

    const msg = rec.message || rec;
    const role = msg.role || rec.type;

    if (role === 'user') {
      const c = msg.content;
      const isToolResult = Array.isArray(c)
        && c.some((b) => b && typeof b === 'object' && b.type === 'tool_result');
      if (isToolResult) {
        for (const b of c) {
          if (!b || typeof b !== 'object' || b.type !== 'tool_result') continue;
          if (b.is_error === true && b.tool_use_id) erroredIds.add(b.tool_use_id);
        }
        continue;                   // harness answering the agent: same turn
      }
      break;                        // a real human message: the turn started after it
    }

    if (role !== 'assistant') continue;
    sawAssistant = true;

    const content = msg.content;
    if (!Array.isArray(content)) {
      if (typeof content === 'string' && content) chunks.unshift(content);
      // A string-content record carries no tool_use, so it ends on text.
      if (endsOnText === null && typeof content === 'string' && content.trim()) {
        endsOnText = true;
      }
      continue;
    }

    let recText = '';
    // D6: compare the LAST non-empty text block against the LAST tool_use block
    // of this record. Computed in the same pass; committed only for the
    // chronologically last assistant record, which is the first one this
    // backwards walk meets.
    let lastTextIdx = -1;
    let lastToolIdx = -1;
    for (let k = 0; k < content.length; k++) {
      const block = content[k];
      if (!block || typeof block !== 'object') continue;
      if (block.type === 'text' && typeof block.text === 'string') {
        recText += block.text;
        if (block.text.trim()) lastTextIdx = k;
      }
      // `lastTool` exists ONLY to give the anti-loop fingerprint something that can
      // DIFFER between two text-free turns. See the fingerprint comment in run().
      // Walking backwards, the FIRST tool_use met is the chronologically last one.
      if (block.type === 'tool_use') {
        usedTool = true;
        lastToolIdx = k;
        if (!lastTool && block.name) lastTool = String(block.name);
        // A call that was REFUSED or that errored did no work, so it cannot
        // buy the turn an exemption. A call with no result recorded at all is
        // counted as productive: at Stop that shape is ambiguous, and D4's
        // lesson is that a false accusation costs more than a miss.
        if (!block.id || !erroredIds.has(block.id)) productiveTool = true;
      }
    }
    // A record with neither block leaves endsOnText null, which downstream reads
    // as "does not end on text" — i.e. the pre-D6 behaviour. Same D4 reasoning:
    // the ambiguous shape must not inherit the new, stricter branch.
    if (endsOnText === null && (lastTextIdx >= 0 || lastToolIdx >= 0)) {
      endsOnText = lastTextIdx > lastToolIdx;
    }
    if (recText) chunks.unshift(recText);
  }

  if (!sawAssistant) return null;
  return {
    text: chunks.join('\n'),
    usedTool,
    productiveTool,
    lastTool,
    endsOnText: endsOnText === true,
  };
}

// --- Anti-loop state -------------------------------------------------------

// --- Heartbeat -------------------------------------------------------------
//
// MEASURED 2026-09-14 (Jacobo/Neom). A dead screen was reported and it took four
// tool calls to FAIL to answer the only question that mattered: DID THIS GUARD
// RUN AT THAT STOP? It could not be answered, and not for want of logging — the
// answer does not exist. STATE_FILE is written on a block, and on a clean stop
// ONLY when a previous streak needs clearing. So the overwhelmingly common
// outcome, "ran and judged the turn clean", leaves no trace at all.
//
// That makes a LIVE guard and a DEAD one byte-identical from outside — the exact
// shape of rules/instrument-before-claim.md ("a gate that cannot fire is
// indistinguishable from a gate that passes") and of CLAUDE.md rule (K)
// `silent-dead-gate`. This file has enumerated eight aperture defects in its own
// patterns; every one of them was found because someone happened to be looking.
// None would have been visible in a log.
//
// It is not hypothetical here. The same dispatcher log carries 45 ETIMEDOUT
// entries for THIS script, every one of which kills the child, drops its stdout,
// and reports precisely what a clean pass reports. For those 45 turns the guard
// was off and nothing said so.
//
// So: one line per INVOCATION, whatever the verdict. `runs` is the positive
// control — a number that stops advancing is a guard that stopped running, and
// that is a question a human can now answer with one read instead of four.
// Fail-open like everything else: telemetry never costs a session.
const HEARTBEAT_FILE = path.join(STATE_DIR, 'closer-guard-heartbeat.json');

function heartbeat(sid, cls) {
  try {
    let h = {};
    try { h = JSON.parse(fs.readFileSync(HEARTBEAT_FILE, 'utf8')); } catch { /* first run */ }
    const now = new Date().toISOString();
    h.runs = (typeof h.runs === 'number' ? h.runs : 0) + 1;
    h.lastRunIso = now;
    h.lastSessionId = sid;
    h.lastVerdict = cls || 'CLEAN';
    if (cls) {
      h.blocks = (typeof h.blocks === 'number' ? h.blocks : 0) + 1;
      h.lastBlockIso = now;
      h.lastBlockClass = cls;
    }
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(HEARTBEAT_FILE, JSON.stringify(h), 'utf8');
  } catch { /* fail-open ABSOLUTE: a heartbeat must never cost a turn */ }
}

function readState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return {}; }
}

// D7 — AN ANTI-LOOP MEMO IS NOT AN ARCHIVE, AND THIS ONE NEVER FORGOT.
// MEASURED 2026-09-14 (Jacobo/Neom): 85 KB, 636 entries, 588 of them (92%)
// written by this file's OWN TEST SUITE — `test-sts-*`, `antiloop-*`,
// `chain-probe-*`. Parsed AND rewritten in full on every single Stop, in every
// repo, forever, to answer one question about ONE session id.
//
// The state's entire purpose is "did I just block this same session on this same
// text?", which is meaningful for minutes and meaningless after that. Nothing
// ever pruned it because nothing ever hurt: it grows by a few hundred bytes a
// day and would have been megabytes before anyone noticed, at which point the
// guard would be timing out on its own bookkeeping — the same silent-dead-gate
// ending as D6, reached from the other side.
//
// Pruned on WRITE rather than on read, so the cost is paid on the rare path (a
// block) instead of the common one, and a reader never has to trust the pruner.
const STATE_MAX_AGE_MS = 6 * 60 * 60 * 1000;   // an anti-loop streak cannot outlive a session
const STATE_MAX_ENTRIES = 64;

function pruneState(state) {
  const now = Date.now();
  const vivos = Object.keys(state).filter((k) => {
    const e = state[k];
    return e && typeof e.ts === 'number' && (now - e.ts) < STATE_MAX_AGE_MS;
  });
  if (vivos.length <= STATE_MAX_ENTRIES) {
    const out = {};
    for (const k of vivos) out[k] = state[k];
    return out;
  }
  vivos.sort((a, b) => state[b].ts - state[a].ts);
  const out = {};
  for (const k of vivos.slice(0, STATE_MAX_ENTRIES)) out[k] = state[k];
  return out;
}

function writeState(state) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(STATE_FILE, JSON.stringify(pruneState(state)), 'utf8');
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
    //
    // D5 — A REJECTED TOOL CALL IS NOT WORK. MEASURED 2026-09-14 (Jacobo).
    //
    // The Owner rejected an Edit; the turn then ended on the single sentence
    // "No response requested." and the screen died. That closer is NULL_ACK —
    // a class this file added on 2026-09-02 for this exact shape — and it was
    // never tested, because the turn carried a `tool_use` block and every class
    // but PASSIVE_WAIT is exempt on a tool turn. Measured on the live
    // transcript:
    //     classify("No response requested.")                  -> NULL_ACK
    //     classify("No response requested.", {toolTurn:true}) -> null
    //
    // The patterns were right, the read unit was right (D4 had just fixed it),
    // and the turn was still waved through — because the EXEMPTION'S PREMISE
    // was false. `usedTool` answers "was a call ISSUED?"; the exemption needs
    // "did a call SUCCEED?". A refused call did nothing, so the turn that
    // carried it is a text-only turn and owes the Owner a sentence.
    //
    // This is this file's standing lesson in an eighth instance and a third
    // family. The first six were the PATTERNS (an exemption, an anchor, an
    // alphabet, a language); D4 was the READ UNIT; this one is the PREDICATE
    // the exemption is written on. A guard can enumerate every shape, read the
    // right bytes, and still pass the case — if the question it asks to decide
    // whether to look is the wrong question. Same defect class, measured the
    // same day, as the admission gate in tools/usea_outcome_contrast.py: TEST
    // FOR THE STATE THAT PERMITS, NEVER FOR THE ONE THAT REFUSES.
    //
    // Red branch: hooks/tests/test-closer-guard-rejected-tool.js (both poles).
    const didWork = turn.usedTool && turn.productiveTool !== false;
    const verdict = didWork
      ? ((turn.text || '').trim()
          ? classify(turn.text, { toolTurn: true, endsOnText: turn.endsOnText === true })
          : { cls: 'SILENT_TOOL_STOP', snippet: '' })
      : classify(turn.text);
    const sid = (input && input.session_id) || 'unknown';

    // EVERY judged turn, not just the blocked ones. See heartbeat() for why the
    // clean case is the one that had to start leaving a trace. Placed after the
    // verdict and before every `return`, so no exit path is unrecorded — the
    // early returns ABOVE this line (guard disabled, no transcript, unreadable
    // turn) are deliberately excluded: those are "did not judge", which is
    // different evidence from "judged and found nothing".
    heartbeat(sid, verdict && verdict.cls);

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
    // the constant "SILENT_TOOL_STOP|" — every silent stop in a session collided with
    // every other one, an hour and fifty good turns apart. The second one was read as
    // "it repeated itself after being told once" and WAVED THROUGH.
    //
    // Evidence: ~/.claude/logs/closer-guard-state.json carried three REAL session
    // UUIDs (4d17ab74…, 86038923…, 2ad9818d…) with "blocked":false against that exact
    // fingerprint. `blocked:false` is written on one code path only — the anti-loop
    // branch. Those are three dead screens this guard consciously let past, which is
    // the precise failure it exists to prevent.
    //
    // Two changes: (1) the key now carries the last tool name, so two text-free stops
    // can differ at all; (2) a STREAK replaces the single boolean, so a genuine
    // repeat-loop still escapes after MAX_STREAK consecutive blocks while ordinary
    // recurrences hours apart are each blocked on their own merits.
    //
    // Generalises: A DE-DUPLICATION KEY BUILT FROM A FIELD THAT IS EMPTY BY
    // CONSTRUCTION IDENTIFIES NOTHING — it merges the whole class into one instance
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
      // trapping the Owner in a block loop — that would be the same disease.
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

module.exports = { run, classify, lastAssistantTurn, readTail, pruneState, TAIL_BYTES };

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
