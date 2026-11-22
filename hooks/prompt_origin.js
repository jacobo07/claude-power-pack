'use strict';
/**
 * prompt_origin.js -- which part of a UserPromptSubmit prompt the Owner wrote (JS twin of
 * modules/gsd_x/prompt_origin.py, for hooks that run IN-PROCESS in the dispatcher and cannot afford a python child).
 *
 * Subagent hand-backs, compaction summaries, task notifications and skill bodies reach UserPromptSubmit without the
 * Owner typing them (measured 2026-11-22: 53/106 live design routes, efaae877). Classify the Owner's words only.
 * Parity with the python rule is pinned by tools/test_prompt_origin_parity.py (V-POP-*): change both or neither.
 */
const MACHINE_PREFIXES = [
  'another claude session sent a message',
  'this session is being continued from a previous conversation',
  '<task-notification>',
  'base directory for this skill',
  'userpromptsubmit hook additional context',
  'caveat: the messages below were generated',
];
const LEADING_REMINDERS = /^\s*(?:<system-reminder[^>]*>[\s\S]*?<\/system-reminder>\s*)+/;

/** The Owner-written part of a prompt, or '' when the whole turn is machine-originated. */
function ownerText(prompt) {
  if (typeof prompt !== 'string') return '';
  const rest = prompt.replace(LEADING_REMINDERS, '').replace(/^[ \t\r\n"']+/, '');
  const low = rest.slice(0, 200).toLowerCase();
  if (!rest || MACHINE_PREFIXES.some((p) => low.startsWith(p))) return '';
  return rest;
}

module.exports = { ownerText, MACHINE_PREFIXES };

if (require.main === module) {   // parity CLI: stdin JSON list of prompts -> stdout JSON list of ownerText results
  const fs = require('fs');
  const cases = JSON.parse(fs.readFileSync(0, 'utf8') || '[]');
  process.stdout.write(JSON.stringify(cases.map(ownerText)));
}
