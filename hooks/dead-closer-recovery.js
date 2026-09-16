#!/usr/bin/env node
/**
 * dead-closer-recovery.js — UserPromptSubmit backstop for the dead-screen closer.
 *
 * WHY THIS EXISTS (measured 2026-09-14, Jacobo, Orca X session 1cf22fab):
 *
 *   1354 [assistant] tool_use
 *   1355 [user]      tool_result  is_error=true  "The user doesn't want to proceed"
 *   1356 [user]      "[Request interrupted by user for tool use]"
 *   1359 [assistant] text "No response requested."      <-- dead screen
 *
 * closer-guard.js classifies those exact bytes as NULL_ACK and returns
 * decision:'block'. Replayed against the real transcript it BLOCKS, and a
 * control closer passes. The logic was never the problem.
 *
 * It never ran. closer-guard-heartbeat.json sat at 17:42:08 and did not advance
 * again until a manual replay at 17:51 — the dead turn fell inside that gap.
 * A turn that follows a USER INTERRUPT does not reliably reach the Stop chain.
 *
 * That is the whole defect, and it is structural rather than textual: the Stop
 * event cannot cover a turn that never completes normally, and a user interrupt
 * — a rejected tool call, ESC, a Ctrl+C — is the single most likely way to
 * arrive at a dead screen. So the guard was perfect and unreachable in exactly
 * its highest-value case. "Check a hook's EVENT before its logic"
 * (~/.claude/CLAUDE.md, Windows Bash Bridge § TWO families, two events).
 *
 * THE FIX IS AN EVENT, NOT A PATTERN. UserPromptSubmit provably fires (it is
 * how SDD-OS and correction-guard reach the model). When the user types again,
 * the escaped closer is still the last assistant turn — so it is detectable
 * after the fact, and the next turn can be made to open by repairing it.
 *
 * This hook NEVER blocks the user's prompt. It injects context and counts the
 * event, so a class that was previously invisible now leaves a trace.
 *
 * PATTERNS ARE IMPORTED, NEVER COPIED. classify() and lastAssistantTurn() come
 * from closer-guard.js itself; a copy would be correct today and wrong on the
 * day either side changes, with nothing to say which day that was
 * (rules/real-context-reachability.md § "Extract the shared rule").
 *
 * Fail-open ABSOLUTE. Kill switch: CLAUDE_DEAD_CLOSER_RECOVERY=off
 * Red branch: hooks/tests/test-dead-closer-recovery.js (both poles + control).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const LOG_FILE = path.join(os.homedir(), '.claude', 'logs', 'dead-closer-recovery.json');

/** Count every judgement, not just the firing ones — a counter that stops
 *  advancing is a hook that stopped running, which is the failure this whole
 *  file exists to make visible. Telemetry never costs a session.
 *
 *  AMENDED 2026-09-14 (Jacobo, second incident, same day). The paragraph above
 *  was the intent and the code did not implement it: FOUR early returns in run()
 *  left no trace at all — no transcript_path, transcript missing, guard import
 *  failure, no assistant turn. A `--resume` produces the second of those, and a
 *  resume is exactly when an escaped closer is most likely to be sitting in the
 *  previous turn. So the instrument built to answer "did it run?" was blind to
 *  the only ways it stops running, and a bail was indistinguishable from a
 *  clean pass — the identical shape to the defect the file exists to fix
 *  (rules/instrument-before-claim.md § "a gate that cannot fire is
 *  indistinguishable from a gate that passes").
 *
 *  Also: this file is ONE counter shared by every concurrent pane on the host,
 *  so an aggregate cannot attribute a run to a session. The `recent` ring makes
 *  the next incident diagnosable instead of ambiguous
 *  (rules/concurrent-writers-shared-tree.md). */
const MAX_RECENT = 40;

function record(sid, cls, fired) {
  try {
    let s = { judged: 0, fired: 0 };
    try { s = JSON.parse(fs.readFileSync(LOG_FILE, 'utf8')) || s; } catch { /* first run */ }
    s.judged = (s.judged || 0) + 1;
    if (fired) {
      s.fired = (s.fired || 0) + 1;
      s.lastFiredIso = new Date().toISOString();
      s.lastFiredClass = cls;
      s.lastFiredSession = sid;
    }
    const iso = new Date().toISOString();
    s.lastRunIso = iso;
    s.lastVerdict = cls || 'CLEAN';
    s.lastSession = sid;
    // Per-outcome tally: a rising BAIL_* count is a wiring problem, a rising
    // CLEAN count is a healthy estate. One aggregate cannot tell them apart.
    s.byVerdict = s.byVerdict || {};
    const key = cls || 'CLEAN';
    s.byVerdict[key] = (s.byVerdict[key] || 0) + 1;
    s.recent = Array.isArray(s.recent) ? s.recent : [];
    s.recent.push({ iso, sid, verdict: key, fired: !!fired });
    if (s.recent.length > MAX_RECENT) s.recent = s.recent.slice(-MAX_RECENT);
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    fs.writeFileSync(LOG_FILE, JSON.stringify(s), 'utf8');
  } catch { /* never costs a session */ }
}

const INTERRUPT = /\[Request interrupted by user/i;

/** Did the user deliberately stop the previous turn AFTER the last assistant
 *  message? A deliberate interrupt that leaves a tool-only turn is the user's
 *  own choice, not a dead screen, and firing on it would be pure noise on every
 *  ESC. Text-bearing classes still fire: "No response requested." is a dead
 *  screen whether or not an interrupt preceded it — that is the measured case. */
function interruptedAfterLastAssistant(transcriptPath) {
  try {
    const lines = fs.readFileSync(transcriptPath, 'utf8').split('\n').filter(Boolean);
    let lastAssistant = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
      let r; try { r = JSON.parse(lines[i]); } catch { continue; }
      const m = r && r.message;
      if (!m || m.role !== 'assistant' || !Array.isArray(m.content)) continue;
      const meaningful = m.content.some(
        (b) => b.type === 'tool_use' || (b.type === 'text' && String(b.text || '').trim())
      );
      if (meaningful) { lastAssistant = i; break; }
    }
    if (lastAssistant < 0) return false;
    for (let i = lastAssistant + 1; i < lines.length; i++) {
      if (INTERRUPT.test(lines[i])) return true;
    }
  } catch { /* fall through */ }
  return false;
}

function buildContext(cls, snippet) {
  const shown = String(snippet || '').trim().slice(-160);
  return (
    'DEAD-CLOSER RECOVERY — your PREVIOUS turn ended on a banned closer (' + cls + ') ' +
    'and the Stop guard never saw it, because a turn following a user interrupt does ' +
    'not reach the Stop chain. The user was left looking at a frozen screen and had to ' +
    'type again to unstick you.\n' +
    'That closing text was: "' + shown + '"\n' +
    'This turn, do ALL of:\n' +
    '  1. Do NOT repeat that closer. Never end a turn with a null acknowledgement ' +
    '("No response requested.", "Understood.", "Noted."), a passive wait ("Awaiting…", ' +
    '"Standing by…", "I\'ll wait…"), or empty text.\n' +
    '  2. If a tool call was rejected or interrupted, SAY SO in a sentence, say what you ' +
    'inferred from it, and offer the next concrete step. A rejection is information, not a ' +
    'reason to go silent.\n' +
    '  3. End this turn with either a concrete deliverable or a concrete question the user ' +
    'can answer. Never with a passive wait.\n' +
    'Rule: ~/.claude/CLAUDE.md → Anti-"Waiting…" doctrine (A)-(K).'
  );
}

function run(input) {
  const sid0 = (input && input.session_id) || 'unknown';

  // EVERY exit below is recorded with its own reason. A bail and a clean pass
  // used to be the same silence; they need opposite fixes, so they must be
  // different evidence. BAIL_* means the hook could not judge — that is NOT a
  // statement about the previous turn, and it must never read as one.
  if (String(process.env.CLAUDE_DEAD_CLOSER_RECOVERY || '').toLowerCase() === 'off') {
    record(sid0, 'BAIL_KILLSWITCH', false);
    return { continue: true };
  }

  // ---------------------------------------------------------------------
  // MIGA DE FRONTERA — va ANTES que el transcript, y esa es toda la idea.
  //
  // Medido 2026-09-14 (sesion aba4a63f): un turno interrumpido NO SE PERSISTE.
  // Ni el prompt del Owner, ni el marcador de interrupcion, ni el cierre muerto
  // que congelo la pantalla. Todo lo de abajo lee el transcript, asi que en el
  // caso de MAS valor lee el turno ANTERIOR — sano — y devuelve CLEAN. Eso paso
  // dos veces seguidas y por eso el Owner tuvo que escribir para desatascarme.
  //
  // La miga la escribe PreToolUse y la borra PostToolUse, asi que sobrevivir
  // hasta aqui solo tiene UNA causa: la ultima herramienta del turno anterior se
  // propuso y nunca completo. Evidencia que yo fabrico antes de perderla, en vez
  // de evidencia que espero que alguien haya guardado.
  try {
    const crumb = require('./turn-boundary-breadcrumb.js').consumeStale(sid0);
    if (crumb) {
      // Una REPETICION es su propia evidencia: significa que la presentacion
      // anterior no produjo ni una sola llamada completada — entrega rota, no
      // estado sano. Colapsarla con la primera vuelve invisible exactamente el
      // fallo que esta linea existe para medir (2026-09-15).
      const rep = crumb.presented > 1;
      record(sid0, 'INTERRUPTED_TURN_UNOBSERVED' + (rep ? '/repeat' : ''), true);

      // Una repeticion PROBADA no puede recibir el mismo texto que la primera.
      // El comentario de arriba ya dice que un /repeat significa "la presentacion
      // anterior no produjo ni una sola llamada completada" — y aun asi este
      // mensaje era byte-identico con presented=1 y con presented=7. Eso es el
      // reintento ciego que la Regla 12 me prohibe a MI, cometido por el guardia
      // que la aplica. Medido 2026-09-15 en logs/dead-closer-recovery.json:
      // 16 firings de esta clase, 7 de ellos /repeat (44%), todos con el mismo
      // texto; esta sesion aporto dos y el Owner tuvo que escribir dos veces.
      // En una repeticion se ESCALA, y la escalada es estructural (prohibir la
      // herramienta que murio), no mas consejo.
      const pivot = !rep ? '' :
        '\n\nESCALADA — REPETICION #' + crumb.presented + '.\n' +
        'El aviso de arriba ya se presento ' + (crumb.presented - 1) + ' vez(es) y no ' +
        'produjo NI UNA llamada completada. Repetirlo es el reintento ciego que la ' +
        'Regla 12 prohibe, asi que este turno cambia de forma por obligacion:\n' +
        '  A. PROHIBIDA `' + crumb.tool + '` como PRIMERA accion del turno. Usa otro ' +
        'mecanismo: Read antes de escribir, PowerShell, o un fichero NUEVO.\n' +
        '  B. Si `' + crumb.tool + '` es imprescindible, primero Read del path exacto y ' +
        'luego UNA sola llamada consolidada — nunca la misma llamada tal cual.\n' +
        '  C. ESTE ES EL ULTIMO RESCATE AUTOMATICO. MAX_PRESENTATIONS=2 en ' +
        'turn-boundary-breadcrumb.js, asi que la miga se descarta despues de este ' +
        'aviso: si el turno vuelve a morir en `' + crumb.tool + '`, NADA lo va a ' +
        'cazar y el Owner se queda otra vez ante una pantalla congelada. Si sospechas ' +
        'que el bloqueo es del entorno (permiso sin responder, ESC, un gate), cierra ' +
        'el turno con una pregunta concreta al Owner nombrando `' + crumb.tool + '` y ' +
        'el path exacto, en vez de gastar el ultimo intento a ciegas.\n';

      return {
        continue: true,
        hookSpecificOutput: {
          hookEventName: 'UserPromptSubmit',
          additionalContext:
            'FRONTERA DE TURNO — tu turno anterior murio en una llamada a `' + crumb.tool + '` que ' +
            'se propuso y nunca completo (rechazada, interrumpida o ESC). Ese turno NO queda en el ' +
            'transcript, asi que ningun guardia pudo verlo: el Owner se quedo mirando una pantalla ' +
            'congelada y tuvo que escribir para desatascarte.\n' +
            'Este turno, obligatorio:\n' +
            '  1. NO cierres con un acuse vacio ("No response requested.", "Entendido.", "Noted.") ' +
            'ni con una espera pasiva ("Waiting...", "Standing by", "quedo a la espera"). Un rechazo ' +
            'es INFORMACION, no una razon para callarse.\n' +
            '  2. Di en una frase que esa llamada no se ejecuto y que inferiste de ello.\n' +
            '  3. NO reintentes la misma llamada tal cual: cambia de forma o pregunta (Regla 12).\n' +
            '  4. Cierra con un entregable concreto o con una pregunta que el Owner pueda responder.\n' +
            'Regla: ~/.claude/CLAUDE.md -> doctrina Anti-"Waiting..." (A)-(K).' + pivot,
        },
      };
    }
  } catch { /* fail-open absoluto: la miga jamas cuesta una sesion */ }

  const transcriptPath = input && input.transcript_path;
  if (!transcriptPath) { record(sid0, 'BAIL_NO_TRANSCRIPT_PATH', false); return { continue: true }; }
  if (!fs.existsSync(transcriptPath)) {
    // The `--resume` case: the harness handed us a path that is not on disk yet.
    // Do NOT guess at "the newest .jsonl in the project dir" — on a multi-pane
    // host that reads ANOTHER pane's turn and would correct this session for a
    // closer it never wrote (rules/concurrent-writers-shared-tree.md). Refusing
    // and saying so is the honest outcome; the count is what makes it visible.
    record(sid0, 'BAIL_TRANSCRIPT_MISSING', false);
    return { continue: true };
  }

  // Import rather than reimplement — see the header note.
  let guard;
  try { guard = require('./closer-guard.js'); } catch {
    record(sid0, 'BAIL_GUARD_IMPORT', false);
    return { continue: true };
  }
  if (!guard || typeof guard.classify !== 'function' || typeof guard.lastAssistantTurn !== 'function') {
    // A rename on the closer-guard side degrades to "cannot judge", loudly,
    // instead of to "never fires" (CLAUDE.md rule (K), silent-dead-gate).
    record(sid0, 'BAIL_GUARD_API', false);
    return { continue: true };
  }

  const turn = guard.lastAssistantTurn(transcriptPath);
  if (!turn) { record(sid0, 'BAIL_NO_ASSISTANT_TURN', false); return { continue: true }; }

  // The SAME predicate the Stop guard decides on (closer-guard.js D5): a
  // rejected call did no work, so the turn that carried it is a text-only turn.
  const didWork = turn.usedTool && turn.productiveTool !== false;
  const text = (turn.text || '').trim();
  const verdict = didWork
    ? (text ? guard.classify(turn.text, { toolTurn: true })
            : { cls: 'SILENT_TOOL_STOP', snippet: '' })
    : guard.classify(turn.text);

  const sid = (input && input.session_id) || 'unknown';

  if (!verdict || !verdict.cls) { record(sid, null, false); return { continue: true }; }

  // A deliberate interrupt leaving a tool-only turn is the user's choice.
  if (verdict.cls === 'SILENT_TOOL_STOP' && interruptedAfterLastAssistant(transcriptPath)) {
    record(sid, verdict.cls + '/interrupt-suppressed', false);
    return { continue: true };
  }

  record(sid, verdict.cls, true);
  return {
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: buildContext(verdict.cls, verdict.snippet || text),
    },
  };
}

module.exports = { run, buildContext, interruptedAfterLastAssistant, LOG_FILE };

if (require.main === module) {
  let input = '';
  const t = setTimeout(() => {
    try { process.stdout.write(JSON.stringify({ continue: true })); } catch { }
    process.exit(0);
  }, 5000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(input || '{}'); } catch { /* fail-open */ }
    try { process.stdout.write(JSON.stringify(run(data)) + '\n'); } catch {
      try { process.stdout.write(JSON.stringify({ continue: true }) + '\n'); } catch { }
    }
    process.exit(0);
  });
}
