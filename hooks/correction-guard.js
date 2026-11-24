#!/usr/bin/env node
/**
 * correction-guard.js — UserPromptSubmit hook for Rule 6 of Anti-Antipattern Protocol.
 *
 * Rule: When the user corrects the agent, quote their exact ask verbatim,
 * confirm understanding, THEN act. Do NOT proceed with silent retries.
 *
 * This hook is ADDITIVE (non-blocking): if the incoming prompt matches a
 * correction pattern, inject `hookSpecificOutput.additionalContext` so the
 * agent receives an explicit reminder alongside the user's message. No
 * blocking, no rewriting — just a nudge that raises the rule to top-of-mind.
 *
 * Patterns are conservative (avoid false positives): short prompts containing
 * explicit correction markers in ES or EN.
 *
 * Log: ~/.claude/state/correction-guard.log (JSON-per-line)
 *
 * Enrolled via ~/.claude/settings.json UserPromptSubmit.
 * Derived from claude-doctor v0.0.3 audit 2026-04-23 (KobiiCraft workspace
 * recorded 22 repeated-instructions events across 76 sessions).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = process.env.HOME || process.env.USERPROFILE || os.homedir();
const LOG_FILE = path.join(HOME, '.claude', 'state', 'correction-guard.log');
const MAX_LEN_FOR_SHORT_CORRECTION = 300;

const CORRECTION_REGEXES = [
  // "no es" alone matched every Spanish question ("no es mejor...?"): it was all
  // 31 of the fires left after the para/stop fix. Now it needs the object.
  /\bno[,.]?\s+(?:(?:es|era)\s+)?(?:eso|as[ií]|lo\s+que|verdad|correct[oa])\b/i,
  // "así no." / "eso no" closing a clause ("no, así no"); "eso no es malo" stays quiet.
  /\b(?:as[ií]|eso)\s+no\s*(?:[.!,;]|$)/i,
  /\beso\s+(es|est[áa])\s+(mal|incorrecto|erroneo|err[oó]neo)\b/i,
  /\b(est[áa]s?|est[aáé]n?)\s+(mal|equivocad)/i,
  // Imperative only: the word opens the prompt or a clause AND closes it
  // ("Para.", "stop!", "para, eso no", "detente ya"). The old /\b(para|...)\b/
  // fired on the Spanish preposition "para" anywhere: 201 of 220 injections in
  // 14 days (state/correction-guard.log, 2026-11-24), each one context rent.
  /(?:^|[.!?;,\n]\s*)(?:para|detente|stop)(?:\s+(?:ya|eso|lo|it|that|now|please|por\s+favor))?\s*(?:[.!,;]|$)/i,
  /\bya\s+(dije|lo\s+dije|hab[ií]a\s+dicho)\b/i,
  /\b(that'?s|this\s+is)\s+(wrong|incorrect|not\s+right)\b/i,
  /\bstop\s+doing\b/i,
  /\byou'?re\s+(missing|ignoring|skipping)\b/i,
  /\bwe\s+already\s+said\b/i,
];

function logLine(decision, matched, promptLen) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    fs.appendFileSync(LOG_FILE,
      JSON.stringify({ ts: new Date().toISOString(), pid: process.pid, decision, matched, promptLen }) + '\n');
  } catch (_) {}
}

function main() {
  let raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch { process.exit(0); }
  if (!raw) process.exit(0);

  let event;
  try { event = JSON.parse(raw); } catch { process.exit(0); }

  const prompt = (event.prompt || '').toString();
  const promptLen = prompt.length;

  if (promptLen === 0 || promptLen > MAX_LEN_FOR_SHORT_CORRECTION) {
    logLine('skip', null, promptLen);
    process.exit(0);
  }

  const matched = CORRECTION_REGEXES.find(rx => rx.test(prompt));
  if (!matched) {
    logLine('pass', null, promptLen);
    process.exit(0);
  }

  const reminder =
    `⚠️ CORRECTION DETECTED (R6 — Anti-Antipattern Protocol)\n` +
    `The user's prompt contains a correction marker. Before responding:\n` +
    `  1. Quote the user's exact ask verbatim (don't paraphrase).\n` +
    `  2. Confirm understanding — state what you believe they want.\n` +
    `  3. THEN act. No silent retries of the previous approach.\n` +
    `Rule: ~/.claude/CLAUDE.md → Anti-Antipattern Protocol, R6.`;

  const output = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: reminder,
    },
  };
  process.stdout.write(JSON.stringify(output) + '\n');
  logLine('inject', matched.toString(), promptLen);
  process.exit(0);
}

main();
