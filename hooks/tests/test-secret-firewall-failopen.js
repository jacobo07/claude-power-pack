#!/usr/bin/env node
'use strict';
/**
 * test-secret-firewall-failopen.js -- V-SECRET-FAILOPEN
 *
 * Pins `skills/claude-power-pack/hooks/secret_firewall_gate.js` (HR-SECRET-001).
 * Before 2026-09-15 that gate had NO test at all, which is how the defect below
 * survived: it is invisible by construction.
 *
 * THE DEFECT. The gate fails open when its Python detector cannot run -- correct
 * and deliberate per HR-SECRET doctrine. But it did so by emitting a bare
 * `{continue:true}`, which is BYTE-IDENTICAL to "scanned, nothing found". So the
 * single case where the firewall is ABSENT looked exactly like the case where it
 * cleared the write.
 *
 * MEASURED that day, same payload, same gate, twice:
 *   host at 844 MB free of 32 GB -> 8218 ms, detector blew its 3000 ms budget,
 *                                   emitted {continue:true}, credential PASSED.
 *   host uncontended             ->  929 ms, detector 395 ms, DENIED on
 *                                   pattern anthropic_key.
 * Contention alone flipped a security verdict from deny to allow.
 *
 * ALL THREE BRANCHES ARE DRIVEN. R1 alone would pass with the fail-open branch
 * deleted; R2 alone would pass with a gate that blocks nothing; R3 alone would
 * pass with a gate that shouts on every write. Only the three together say the
 * gate discriminates.
 *
 * HR-SECRET-005: the credential here is clearly fake and real-shape on purpose.
 * It is built by concatenation so the literal never appears in this source.
 */

const { spawnSync } = require('child_process');
const os = require('os');
const path = require('path');

const GATE = path.join(
  os.homedir(), '.claude', 'skills', 'claude-power-pack', 'hooks', 'secret_firewall_gate.js',
);

let pass = 0;
let fail = 0;
const ok = (n, e) => { pass++; console.log(`  OK   ${n}  ${e}`); };
const bad = (n, e) => { fail++; console.log(`  FAIL ${n}  ${e}`); };

// Real-shape, obviously synthetic. Never written as one literal.
const FAKE = 'sk-' + 'ant-' + 'A'.repeat(50);

function callGate(content, env) {
  const payload = JSON.stringify({
    session_id: 'V-SECRET-FAILOPEN',
    tool_name: 'Write',
    cwd: os.homedir(),
    tool_input: { file_path: path.join(os.tmpdir(), 'canary.txt'), content },
  });
  const r = spawnSync(process.execPath, [GATE], {
    input: payload,
    encoding: 'utf8',
    timeout: 30000,
    windowsHide: true,
    env: { ...process.env, ...(env || {}) },
  });
  let out = null;
  try { out = JSON.parse((r.stdout || '').trim()); } catch (_) { /* reported below */ }
  return { raw: r.stdout || '', json: out, error: r.error };
}

const ctx = (o) => (o && o.hookSpecificOutput && o.hookSpecificOutput.additionalContext) || '';
const decision = (o) => (o && o.hookSpecificOutput && o.hookSpecificOutput.permissionDecision) || '';

// R1 -- the gate must actually detect. This is also the POSITIVE CONTROL for R3:
// without it, a gate whose detector never runs would pass R3 for the wrong reason.
function r1_denies() {
  const { json, raw } = callGate(`API_KEY = "${FAKE}"`);
  if (!json) return bad('V-SECRET-R1-DENIES', `unparseable stdout: ${raw.slice(0, 120)}`);
  if (decision(json) === 'deny' && /anthropic_key/.test(JSON.stringify(json))) {
    ok('V-SECRET-R1-DENIES', 'credential denied, pattern named');
  } else {
    bad('V-SECRET-R1-DENIES', `expected deny+pattern, got ${JSON.stringify(json).slice(0, 160)}`);
  }
}

// R2 -- and it must not cry wolf. A gate that shouted on every write would be
// switched off, and an off gate is the hole.
function r2_quiet_on_clean() {
  const { json, raw } = callGate('API_KEY = read_env("API_KEY")');
  if (!json) return bad('V-SECRET-R2-QUIET', `unparseable stdout: ${raw.slice(0, 120)}`);
  if (json.continue === true && !/NOT ENFORCED/.test(ctx(json)) && decision(json) !== 'deny') {
    ok('V-SECRET-R2-QUIET', 'clean write allowed with no false alarm');
  } else {
    bad('V-SECRET-R2-QUIET', `expected silent allow, got ${JSON.stringify(json).slice(0, 160)}`);
  }
}

// R3 -- THE CLAIM, INVERTED 2026-09-15 by explicit Owner decision.
//
// This assertion used to read `fail-open was lost -- HR-SECRET doctrine
// requires it` and it PASSED, which is why the behaviour survived: the suite
// was pinning the defect. Preserved here deliberately rather than deleted, so
// the diff between the two commits is the evidence that the contract changed on
// purpose and is not a regression someone should "fix" back.
//
// What changed the answer was the population, not the principle. 15,574 timeout
// events in the live dispatcher log, 256 of them this gate -- so the degraded
// path was ordinary operation, and an audible warning arrives after the write.
//
// Driving it by pointing PYTHON_BIN at a file that does not exist reproduces the
// starved-host outcome without needing to starve the host.
function r3_unenforced_denies() {
  const bogus = path.join(os.tmpdir(), 'definitely-not-a-python-' + process.pid + '.exe');
  const { json, raw } = callGate(`API_KEY = "${FAKE}"`, { PYTHON_BIN: bogus });
  if (!json) return bad('V-SECRET-R3-FAILCLOSED', `unparseable stdout: ${raw.slice(0, 120)}`);

  // The agent must NOT be halted. `continue:false` ends the turn at the tool
  // boundary with no assistant text and the Stop chain never runs, so
  // closer-guard cannot see it -- the documented dead screen. Denying the TOOL
  // and halting the AGENT are different things and only one of them is wanted.
  if (json.continue === false) {
    return bad('V-SECRET-R3-FAILCLOSED',
      `halted the agent instead of denying the tool -- dead-screen shape: ${JSON.stringify(json).slice(0, 160)}`);
  }
  const d = json.hookSpecificOutput && json.hookSpecificOutput.permissionDecision;
  if (d !== 'deny') {
    return bad('V-SECRET-R3-FAILCLOSED',
      `unenforced gate became permission -- expected deny, got ${JSON.stringify(json).slice(0, 160)}`);
  }
  const reason = (json.hookSpecificOutput && json.hookSpecificOutput.permissionDecisionReason) || '';
  // Assert on CONTENT, not on non-emptiness: the reason has to say the content
  // was never scanned, because that is the sentence the operator acts on.
  if (/NOT scanned/i.test(reason) && /HR-SECRET-001/.test(reason)) {
    ok('V-SECRET-R3-FAILCLOSED', 'denies the tool and says the content was never scanned');
  } else {
    bad('V-SECRET-R3-FAILCLOSED',
      `denied without saying why it could not clear the content: ${reason.slice(0, 160)}`);
  }
}

r1_denies();
r2_quiet_on_clean();
r3_unenforced_denies();

console.log(`SECRET_FAILOPEN_PASS=${pass}/${pass + fail}  threshold=3/3`);
process.exit(fail === 0 ? 0 : 1);
