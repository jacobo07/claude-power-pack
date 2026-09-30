#!/usr/bin/env node
/**
 * carrier_bash_guard.js -- runtime least privilege for CPP carrier agents.
 *
 * Spec: vault/specs/agent-capability-virtualization.md (S1, audit gap 4).
 *
 * A carrier's tool LIST is enforced by Claude Code through its frontmatter, but
 * Bash inside that list is all-or-nothing: a "read-only" verifier with Bash can
 * delete files, commit, push and reach the network. Measured 2026-09-30: for a
 * subagent's tool call the PreToolUse payload carries `agent_type`, so the class
 * boundary can be enforced here, at the effect, instead of described in prose.
 *
 *   cpp-carrier-investigator  has no Bash in its frontmatter; any Bash call is
 *                             a class escape and is denied.
 *   cpp-carrier-verifier      Bash only for observing and testing: every segment
 *                             of the command must match the allow-list, and no
 *                             output redirection to a file is allowed.
 *   anything else             not ours: allowed untouched.
 *
 * Fail-closed ONLY for a carrier (an unparseable verifier call is denied, since
 * failing open would be exactly the escape this exists to stop). For every other
 * caller it fails open, like every guard in this chain.
 *
 * Wired in hooks/hook-dispatcher.js 'PreToolUse-Bash-chain'.
 * Test: hooks/tests/test-carrier-bash-guard.js
 */
'use strict';

const CARRIER = /^cpp-carrier-(investigator|verifier|writer)$/;

// One segment = one command between ; && || | . Each must match one of these.
const ALLOW = [
  /^git\s+(status|log|diff|show|blame|rev-parse|ls-files|grep|branch\s+--show-current|cat-file|describe)\b/,
  /^git\s+-C\s+\S+\s+(status|log|diff|show|blame|rev-parse|ls-files|grep|cat-file|describe)\b/,
  /^(python3?|py)(\.exe)?\s+-m\s+pytest\b/,
  /^pytest\b/,
  /^(python3?|py)(\.exe)?\s+(\S*[\\/])?(test_[\w-]+|[\w-]+_test)\.py\b/,
  /^node(\.exe)?\s+(\S*[\\/])?test[\w.-]*\.js\b/,
  /^npm\s+(test|run\s+test)\b/,
  /^(ls|dir|pwd|cat|head|tail|wc|grep|rg|sort|uniq|diff|stat|file|which|echo|sha256sum|md5sum|tree|du|df)\b/,
  /^find\b(?!.*\s-(delete|exec|execdir|ok|fprint\w*)\b)/,
];

const REDIRECT = />/;
const SAFE_REDIRECTS = /\s*\d?>&\d|\s*\d?>\s*\/dev\/null/g;

/** Returns { allow: boolean, reason: string }. Pure; no I/O. */
function judge(agentType, toolName, command) {
  if (!CARRIER.test(agentType || '')) return { allow: true, reason: 'not a carrier' };
  const cls = agentType.replace('cpp-carrier-', '');
  if (cls === 'writer') return { allow: true, reason: 'writer class holds shell authority' };
  if (!['Bash', 'PowerShell'].includes(toolName)) return { allow: true, reason: 'not a shell tool' };
  if (cls === 'investigator') {
    return { allow: false, reason: 'investigator class has no shell authority (class escape)' };
  }
  if (typeof command !== 'string' || !command.trim()) {
    return { allow: false, reason: 'verifier: empty or unreadable command' };
  }
  if (/[`]|\$\(/.test(command)) {
    return { allow: false, reason: 'verifier: command substitution is not allowed' };
  }
  if (REDIRECT.test(command.replace(SAFE_REDIRECTS, ''))) {
    return { allow: false, reason: 'verifier: output redirection writes a file' };
  }
  const segments = command.split(/\|\||&&|;|\||\r?\n/).map((s) => s.trim()).filter(Boolean);
  for (const seg of segments) {
    const s = seg.replace(/^cd\s+\S+\s*$/, 'pwd');
    if (!ALLOW.some((re) => re.test(s))) {
      return { allow: false, reason: `verifier: "${seg.slice(0, 80)}" is not an observe/test command` };
    }
  }
  return { allow: true, reason: 'verifier: observe/test command' };
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

async function main() {
  let raw = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const c of process.stdin) raw += c;
  } catch { return emit({ continue: true }); }
  if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
  let req;
  try { req = JSON.parse(raw); } catch { return emit({ continue: true }); }
  let verdict;
  try {
    verdict = judge(req.agent_type, req.tool_name, (req.tool_input || {}).command);
  } catch (e) {
    verdict = CARRIER.test(req.agent_type || '')
      ? { allow: false, reason: `guard error on a carrier call: ${e && e.message}` }
      : { allow: true, reason: 'guard error, not a carrier' };
  }
  if (verdict.allow) return emit({ continue: true });
  return emit({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: `CARRIER-CLASS -- ${req.agent_type}: ${verdict.reason}. `
        + 'This carrier may only observe and test. Report what you needed to do as a finding '
        + 'for the parent instead of attempting it another way.',
    },
  });
}

if (require.main === module) main();
module.exports = { judge };
