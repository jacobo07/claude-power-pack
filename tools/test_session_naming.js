#!/usr/bin/env node
'use strict';
/**
 * test_session_naming.js — V-gates for the LIVE forward-path /resume title
 * (session-title-lib.js decideTitle + mark-live-session.js).
 *
 * Scope: the forward path ONLY. The RETROACTIVE path is owned by
 * tools/rename_sessions.py + tools/test_rename_sessions.py (do not duplicate).
 *
 * Every gate calls the shipped code: decideTitle / markOwnSession in-process,
 * and the SessionEnd gates spawn the real hook with a real stdin payload.
 * Hermetic: throwaway .jsonl fixtures under a temp dir, removed on exit. AAA.
 *   node tools/test_session_naming.js   ->  exit 0 iff all V-gates pass
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');
const lib = require('../hooks/session-title-lib.js');
const HOOK = path.join(__dirname, '..', 'hooks', 'mark-live-session.js');
const { markOwnSession } = require(HOOK);

let passes = 0, fails = 0;
const _ok = (g, e) => { passes++; console.log(`  PASS ${g}  ${e}`); };
const _fail = (g, e) => { fails++; console.log(`  FAIL ${g}  ${e}`); };
const check = (g, cond, evidence) => (cond ? _ok(g, evidence) : _fail(g, evidence));

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'pp-sessname-'));
let n = 0;
const newSid = () => `${String(++n).padStart(8, '0')}-1111-2222-3333-444444444444`;
const fixture = (sid, lines) => {
  const p = path.join(TMP, sid + '.jsonl');
  fs.writeFileSync(p, lines.map(o => JSON.stringify(o)).join('\n') + '\n', 'utf-8');
  return p;
};
const user = text => ({ type: 'user', message: { role: 'user', content: text } });
const title = (sid, t) => ({ type: 'custom-title', customTitle: t, sessionId: sid });
const shown = fp => (lib.lastCustomTitle(fp) || {}).rawTitle;
const sessionEnd = (sid, fp, reason) => execFileSync(process.execPath, [HOOK], {
  input: JSON.stringify({ session_id: sid, transcript_path: fp, hook_event_name: 'SessionEnd', reason }),
  timeout: 10000,
});

try {
  // V-AI-TITLE-SOURCE: the base is the clean ai-title, not the raw first prompt.
  {
    const sid = newSid();
    const fp = fixture(sid, [user('Staged Python diff to generate ONE happy-path test scaffold'),
      { type: 'ai-title', aiTitle: 'Add happy-path test scaffold' }]);
    const t = lib.deriveReadableTitle(fp, sid);
    check('V-AI-TITLE-SOURCE', t === 'Add happy-path test scaffold', `"${t}"`);
  }

  // V-TRUNCATE: an ai-title over MAX_LABEL is cut with "…".
  {
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'ai-title', aiTitle: 'This ai-title is deliberately much longer than sixty characters to force truncation' }]);
    const t = lib.deriveReadableTitle(fp, sid);
    check('V-TRUNCATE', t.length <= lib.MAX_LABEL && t.endsWith('…'), `"${t}" (${t.length})`);
  }

  // V-DEFER-FOR-AI-TITLE: no custom-title and no ai-title yet -> write nothing,
  // because any custom-title stops the harness generating the ai-title.
  // Control: after DEFER_PROMPTS prompts it falls back to the first prompt.
  {
    const sid = newSid();
    const fp = fixture(sid, [user('Arregla los nombres de las sesiones en resume')]);
    const early = lib.decideTitle(fp, sid, 'live');
    const fp2 = fixture(newSid(), [user('Arregla los nombres de las sesiones en resume'), user('sigue'), user('y los tests')]);
    const late = lib.decideTitle(fp2, 'x', 'live');
    check('V-DEFER-FOR-AI-TITLE', early === null && late === '⚡ Arregla los nombres de las sesiones en resume',
      `early=${early} late="${late}"`);
  }

  // V-FIRST-PROMPT-SKIPS-WRAPPERS: the caveat wrapper, a bare /clear, and the
  // expanded skill body are skipped; a slash command's args are the prompt.
  {
    const sid = newSid();
    const fp = fixture(sid, [
      user('<local-command-caveat>The command below was run directly in Claude Code, not sent to you as a request.</local-command-caveat>'),
      user('<command-name>/clear</command-name>\n<command-message>clear</command-message>\n<command-args></command-args>'),
      user('<command-message>kresume</command-message>\n<command-name>/kresume</command-name>\n<command-args>focus on Read-only hub critical-path delta</command-args>'),
      { type: 'user', isMeta: true, message: { role: 'user', content: '# /kresume — successor side of a context rollover' } },
      { type: 'user', message: { role: 'user', content: [{ type: 'tool_result', content: 'ok' }] } },
    ]);
    const s = lib.scanPrompts(fp);
    check('V-FIRST-PROMPT-SKIPS-WRAPPERS', s.title === 'Read-only hub critical-path delta' && s.prompts === 1,
      `title="${s.title}" prompts=${s.prompts}`);
  }

  // V-SHORT-ARGS-KEEP-COMMAND: "/cpp-gsd-long unattended" is the title, not "unattended".
  {
    const sid = newSid();
    const fp = fixture(sid, [user('<command-name>/cpp-gsd-long</command-name>\n<command-args>unattended</command-args>')]);
    const s = lib.scanPrompts(fp);
    check('V-SHORT-ARGS-KEEP-COMMAND', s.title === '/cpp-gsd-long unattended', `title="${s.title}"`);
  }

  // V-FILLER-SKIPPED: "/kresume" with no args, "continue" and a "!" command are
  // passed over; the first prompt with a topic names the session.
  {
    const sid = newSid();
    const fp = fixture(sid, [
      user('<command-message>kresume</command-message>\n<command-name>/kresume</command-name>'),
      user('continue'),
      user('<bash-input> python tools/mission_spend.py session-declare</bash-input>'),
      user('que es lo que tenemos que optimizar de las skills?'),
      user('y'),
    ]);
    const t = lib.decideTitle(fp, sid, 'live');
    check('V-FILLER-SKIPPED', t === '⚡ que es lo que tenemos que optimizar de las skills?', `"${t}"`);
  }

  // V-FILLER-ONLY-BRANCH: only nudges -> the git branch names it. Control:
  // with no branch either, the nudge beats a bare hash.
  {
    const sid = newSid();
    const withBranch = fixture(sid, [{ type: 'system', gitBranch: 'feature/invoice-audit' },
      user('go ahead'), user('sí, hazlo'), user('sigue')]);
    const sidB = newSid();
    const noBranch = fixture(sidB, [{ type: 'system', gitBranch: 'main' },
      user('go ahead'), user('sí, hazlo'), user('sigue')]);
    const a = lib.decideTitle(withBranch, sid, 'live');
    const b = lib.decideTitle(noBranch, sidB, 'live');
    check('V-FILLER-ONLY-BRANCH', a === '⚡ feature/invoice-audit' && b === '⚡ go ahead', `branch="${a}" none="${b}"`);
  }

  // V-FILLER-LAUNCH-COMMAND: a nudge-only session launched with a command is
  // named by it. Control: /kresume names no task, so the branch wins there.
  {
    const cmd = n => `<command-message>${n}</command-message>\n<command-name>/${n}</command-name>`;
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'system', gitBranch: 'sprint/acmf' },
      user(cmd('gsd-map-codebase')), user('go'), user('sí'), user('sigue')]);
    const sidB = newSid();
    const fpB = fixture(sidB, [{ type: 'system', gitBranch: 'sprint/acmf' },
      user(cmd('kresume')), user('continue'), user('sí'), user('sigue')]);
    const a = lib.decideTitle(fp, sid, 'live');
    const b = lib.decideTitle(fpB, sidB, 'live');
    check('V-FILLER-LAUNCH-COMMAND', a === '⚡ /gsd-map-codebase' && b === '⚡ sprint/acmf', `cmd="${a}" kresume="${b}"`);
  }

  // V-STORED-FILLER-UPGRADED: an old "continue" title and a branch stand-in are
  // both replaced once a real prompt exists; a short human name is kept.
  {
    const sid = newSid();
    const fp = fixture(sid, [user('continue'), user('Migra la tabla de pedidos a Postgres'), title(sid, 'continue')]);
    const sidB = newSid();
    const fpB = fixture(sidB, [{ type: 'system', gitBranch: 'feature/orders' },
      user('Migra la tabla de pedidos a Postgres'), title(sidB, '⚡ feature/orders')]);
    const sidC = newSid();
    const fpC = fixture(sidC, [user('Migra la tabla de pedidos a Postgres'), title(sidC, 'Wii')]);
    const a = lib.decideTitle(fp, sid, 'live');
    const b = lib.decideTitle(fpB, sidB, 'live');
    const c = lib.decideTitle(fpC, sidC, 'live');
    check('V-STORED-FILLER-UPGRADED',
      a === '⚡ Migra la tabla de pedidos a Postgres' && b === a && c === '⚡ Wii',
      `filler="${a}" branch="${b}" human="${c}"`);
  }

  // V-FENCED-PROMPT: a "```text" ai-title is ignored and the fenced prompt's
  // first line becomes the title.
  {
    const sid = newSid();
    const fp = fixture(sid, [user('```text\nAudita el pipeline de facturas\n```'), { type: 'ai-title', aiTitle: '```text' },
      title(sid, '⚡ ```text')]);
    const t = lib.decideTitle(fp, sid, 'live');
    check('V-FENCED-PROMPT', t === '⚡ Audita el pipeline de facturas', `"${t}"`);
  }

  // V-JUNK-REPLACED: a stored wrapper-text title is replaced by the ai-title.
  {
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'ai-title', aiTitle: 'Token audit' },
      title(sid, '⚡ The command below was run directly in Claude Code, not sent…')]);
    const t = lib.decideTitle(fp, sid, 'live');
    check('V-JUNK-REPLACED', t === '⚡ Token audit', `"${t}"`);
  }

  // V-HASH-FALLBACK: a junk title with nothing derivable degrades to the hash.
  {
    const sid = newSid();
    const fp = fixture(sid, [title(sid, '⚡ The command below was run directly in Claude Code, not sent…')]);
    const t = lib.decideTitle(fp, sid, 'live');
    check('V-HASH-FALLBACK', t === '⚡ ' + sid.slice(0, 8), `"${t}"`);
  }

  // V-SELF-HEAL: a legacy "⚡ <hash>" upgrades to the ai-title, then is idempotent.
  {
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'ai-title', aiTitle: 'Real session topic' }, title(sid, '⚡ ' + sid.slice(0, 8))]);
    const first = markOwnSession(sid, fp, 'live');
    const second = markOwnSession(sid, fp, 'live');
    check('V-SELF-HEAL', first === '⚡ Real session topic' && second === null && shown(fp) === first,
      `1st="${first}" 2nd=${second}`);
  }

  // V-RESPECT-CTRLR: a human Ctrl+R name is never overwritten.
  {
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'ai-title', aiTitle: 'auto generated' }, title(sid, 'My Hand Named Session')]);
    const t = lib.decideTitle(fp, sid, 'live');
    check('V-RESPECT-CTRLR', t === '⚡ My Hand Named Session', `"${t}"`);
  }

  // V-FINISHED-ON-CLEAR: SessionEnd reason=clear through the real hook process
  // turns "⚡ X" into "X ✓ terminada". Control: reason=other only drops the ⚡.
  {
    const sid = newSid();
    const fp = fixture(sid, [{ type: 'ai-title', aiTitle: 'Fix resume titles' }, title(sid, '⚡ Fix resume titles')]);
    sessionEnd(sid, fp, 'clear');
    const sidB = newSid();
    const fpB = fixture(sidB, [{ type: 'ai-title', aiTitle: 'Fix resume titles' }, title(sidB, '⚡ Fix resume titles')]);
    sessionEnd(sidB, fpB, 'other');
    check('V-FINISHED-ON-CLEAR', shown(fp) === 'Fix resume titles ✓ terminada' && shown(fpB) === 'Fix resume titles',
      `clear="${shown(fp)}" other="${shown(fpB)}"`);
  }

  // V-FINISHED-NO-TITLE-YET: a session cleared before any title existed still
  // gets the suffix on its derived name.
  {
    const sid = newSid();
    const fp = fixture(sid, [user('Revisar el informe de costes')]);
    sessionEnd(sid, fp, 'prompt_input_exit');
    check('V-FINISHED-NO-TITLE-YET', shown(fp) === 'Revisar el informe de costes ✓ terminada', `"${shown(fp)}"`);
  }

  // V-RESUME-FINISHED: resuming a finished session makes it live again, and a
  // dead-sweep never strips the finished suffix.
  {
    const sid = newSid();
    const fp = fixture(sid, [title(sid, 'Fix resume titles ✓ terminada')]);
    const dead = lib.decideTitle(fp, sid, 'dead');
    const live = markOwnSession(sid, fp, 'live');
    check('V-RESUME-FINISHED', dead === null && live === '⚡ Fix resume titles', `dead=${dead} live="${live}"`);
  }
} finally {
  try { fs.rmSync(TMP, { recursive: true, force: true }); } catch { /* best effort */ }
}

console.log(`\nSESSION_NAMING_PASS=${passes}/${passes + fails}  threshold=${passes + fails}/${passes + fails}`);
process.exit(fails === 0 ? 0 : 1);
