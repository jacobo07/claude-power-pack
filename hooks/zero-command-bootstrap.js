#!/usr/bin/env node
/**
 * zero-command-bootstrap.js - SessionStart hook (Zero-Command Plan, Component A).
 *
 * Source of truth: PP repo (claude-power-pack/hooks/).
 * Deployment path: ~/.claude/hooks/zero-command-bootstrap.js (copied by
 * tools/settings_merger.py register-zero-command during Owner-authorized install).
 *
 * Companion to auto-vault-bootstrap.js (vault extraction) but covers the
 * Spec Kit auto-stub path: if cwd looks like an active dev project
 * (.git + a recognized manifest) AND lacks .specify/, drop a pre-stubbed
 * constitution.md so the Spec Kit JIT chain can begin without an Owner
 * command.
 *
 * Decision tree (idempotent via .pp-onboarded marker):
 *   1. cwd/.pp-onboarded exists                          -> silent no-op
 *   2. cwd missing .git                                  -> silent no-op
 *   3. cwd has .git + manifest + no .specify/            -> stub constitution.md
 *   4. Touch .pp-onboarded with timestamp + actions log  -> done
 *
 * Boilerplate (stdin read, BOM-strip, JSON parse, top-level catch, logErr)
 * lives in hooks/_shared/hook-runtime.js. See that file for the contract.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const PP_ROOT = path.normalize(
  path.join(os.homedir(), '.claude/skills/claude-power-pack')
);
const rt = require(path.join(PP_ROOT, 'hooks/_shared/hook-runtime'));
const CONSTITUTION_TEMPLATE = path.join(
  PP_ROOT, 'vault/templates/speckit/constitution.md.template'
);
const logErr = rt.makeLogErr('zero-command-bootstrap');

// Onboarding is BY PROJECT TYPE (PR-PP-ONBOARDING-BY-PROJECT-TYPE-001).
// A repo that already carries its own governance substrate has opted out, and
// stamping ours over it is not onboarding — it is a second, competing law
// system in one tree. KobiiSports Resort is the worked example: it forked the
// pattern deliberately (.ksr_vault/ + DNA-RAG-01 + N-Laws) and ~75 of 86
// modules correctly have no footprint there. Scoring that fork against the
// full capability set would report health as 87% non-compliance.
const FORK_MARKERS = Object.freeze(['.ksr_vault', '.specify', '.governance']);

function forkMarkerIn(cwd) {
  for (const m of FORK_MARKERS) {
    try {
      if (fs.existsSync(path.join(cwd, m))) return m;
    } catch (_) { /* unreadable entry -> treat as absent, never throw */ }
  }
  return null;
}

// The capability record lives in its OWN marker, never in .pp-onboarded.
// .pp-onboarded is this hook's idempotency latch: writing a capability payload
// there would make the hook a permanent no-op in every repo it touched, which
// turns an onboarding step into an onboarding block.
function writeCapabilities(cwd, manifest, capabilities, declined) {
  const payload = {
    schema_version: 1,
    recorded_at: new Date().toISOString(),
    project_type: manifest,
    capabilities,
    declined,
  };
  fs.writeFileSync(path.join(cwd, '.pp-capabilities'),
                   JSON.stringify(payload, null, 2), 'utf8');
}

function stubConstitution(cwd) {
  if (!fs.existsSync(CONSTITUTION_TEMPLATE)) return { skipped: 'template-missing' };

  const specifyMem = path.join(cwd, '.specify', 'memory');
  fs.mkdirSync(specifyMem, { recursive: true });

  const constitutionPath = path.join(specifyMem, 'constitution.md');
  if (fs.existsSync(constitutionPath)) return { skipped: 'already-present' };

  const tpl = fs.readFileSync(CONSTITUTION_TEMPLATE, 'utf8');
  const projectName = path.basename(cwd);
  const stubbed = tpl.replace(/\[PROJECT_NAME\]/g, projectName);
  fs.writeFileSync(constitutionPath, stubbed, 'utf8');
  return { stubbed: constitutionPath };
}

rt.runHook(logErr, async (event) => {
  // Env-payload fallback (BL-SESSION-FOLD-001): the hub detached-spawns this
  // hook with no stdin, passing cwd via PP_EVT_CWD. The standalone entry
  // still supplies cwd via stdin.
  const cwd = (event && event.cwd) || process.env.PP_EVT_CWD;
  if (!cwd) return;

  const marker = path.join(cwd, '.pp-onboarded');
  if (fs.existsSync(marker)) return;

  if (!fs.existsSync(path.join(cwd, '.git'))) return;

  const manifest = rt.detectManifest(cwd);
  if (!manifest) return;

  const log = {
    timestamp: new Date().toISOString(),
    session: event.session_id || 'unknown',
    cwd,
    manifest,
    actions: [],
  };

  const capabilities = [];
  const declined = [];

  const fork = forkMarkerIn(cwd);
  if (fork) {
    // Not a failure and not a gap — a correct fork. Recorded so a later
    // coverage audit reads it as a decision rather than as missing coverage.
    declined.push({ capability: 'speckit-constitution', reason: `fork marker ${fork}` });
    log.actions.push({ component: 'A-stub-constitution', skipped: `fork:${fork}` });
  } else {
    try {
      const result = stubConstitution(cwd);
      if (result.stubbed) capabilities.push('speckit-constitution');
      else declined.push({ capability: 'speckit-constitution', reason: result.skipped });
      log.actions.push({ component: 'A-stub-constitution', ...result });
    } catch (e) {
      log.actions.push({ component: 'A-stub-constitution', error: String(e && e.message || e) });
      logErr('stub-constitution', e);
    }
  }

  // Universal tier: value does not depend on the stack, and these are already
  // live as global hooks — recorded so the marker states what this repo
  // actually gets, not what the Power Pack could theoretically offer it.
  capabilities.push('ceps-capture', 'cross-project-baseline', 'spec-gate');

  try {
    writeCapabilities(cwd, manifest, capabilities, declined);
  } catch (e) {
    logErr('write-capabilities', e);
  }

  try {
    fs.writeFileSync(marker, JSON.stringify(log, null, 2), 'utf8');
  } catch (e) {
    logErr('write-marker', e);
  }
});
