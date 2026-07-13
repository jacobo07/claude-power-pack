#!/usr/bin/env node
/**
 * test_design_hook.js -- done gate for the CDIO design-gate HOOK wiring (V-HOOK-*).
 *
 * The gate itself is proven by tools/test_design_gate.py. This suite proves the thing
 * that actually makes it a gate: that it FIRES BY ITSELF on a Write to a visual
 * surface, denies real slop, and -- critically -- never traps the agent.
 *
 * The escape-hatch gate (V-HOOK-DESIGNMD-EDITABLE) is the most important one here. A
 * gate that blocks writes because DESIGN.md is bad, while also blocking writes to
 * DESIGN.md, is a deadlock: the only way out would be to disable the gate, and a gate
 * that gets disabled is worse than no gate.
 *
 * Hermetic: every project fixture is a fresh temp dir. Run 3x -> identical.
 */
'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const hook = require('../hooks/cdio_visual_advisory.js');

let passes = 0;
let fails = 0;
const ok = (g, e) => { passes += 1; console.log(`  [PASS] ${g}: ${e}`); };
const bad = (g, d) => { fails += 1; console.log(`  [FAIL] ${g}: ${d}`); };

const PP_ROOT = path.resolve(__dirname, '..');
const TEMPLATE = path.join(PP_ROOT, 'modules', 'design-md', 'DESIGN.md.template');

const SLOP_DESIGN_MD = [
  '---',
  'name: SlopProject',
  'colors:',
  '  accent: "#8b5cf6"',
  '  neutral: "#ffffff"',
  'typography:',
  '  body-md:',
  '    fontFamily: Inter',
  '---',
  'No declared family, an inherited font stack, a purple accent on a white ground.',
  '',
].join('\n');

function project(name, designMdBody) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `ppdesign-${name}-`));
  fs.mkdirSync(path.join(dir, '.git'));            // project boundary
  fs.mkdirSync(path.join(dir, 'src'));
  if (designMdBody !== null) {
    fs.writeFileSync(path.join(dir, 'DESIGN.md'), designMdBody, 'utf8');
  }
  return dir;
}

const evt = (file, tool = 'Write', session = 'sess-test') => ({
  tool_name: tool,
  tool_input: { file_path: file },
  session_id: session,
});

function main() {
  console.log('V-HOOK gates (CDIO design gate wiring)');

  // --- V-HOOK-DENIES-SLOP: the hook must be observed REFUSING, unprompted --------
  {
    const dir = project('slop', SLOP_DESIGN_MD);
    const surface = path.join(dir, 'src', 'hero.tsx');
    const out = hook.run(evt(surface, 'Write', 's1'));
    const hso = out.hookSpecificOutput || {};
    if (hso.permissionDecision === 'deny'
        && /BLOCK/.test(hso.permissionDecisionReason || '')
        && /font-stack-intent/.test(hso.permissionDecisionReason || '')) {
      ok('V-HOOK-DENIES-SLOP', 'Write to hero.tsx DENIED against a slop DESIGN.md');
    } else {
      bad('V-HOOK-DENIES-SLOP', `expected deny, got ${JSON.stringify(out).slice(0, 160)}`);
    }

    // --- V-HOOK-BLOCK-NOT-THROTTLED: a refusal must refuse EVERY time ------------
    const again = hook.run(evt(surface, 'Write', 's1'));
    if ((again.hookSpecificOutput || {}).permissionDecision === 'deny') {
      ok('V-HOOK-BLOCK-NOT-THROTTLED', 'second identical write still denied');
    } else {
      bad('V-HOOK-BLOCK-NOT-THROTTLED',
          'the throttle swallowed a BLOCK -- a refusal that goes quiet is not a refusal');
    }

    // --- V-HOOK-DESIGNMD-EDITABLE: the escape hatch (no deadlock) ----------------
    const fix = hook.run(evt(path.join(dir, 'DESIGN.md'), 'Edit', 's1'));
    if (!fix.hookSpecificOutput || !fix.hookSpecificOutput.permissionDecision) {
      ok('V-HOOK-DESIGNMD-EDITABLE',
         'editing DESIGN.md is never denied -- the denied write is always fixable');
    } else {
      bad('V-HOOK-DESIGNMD-EDITABLE',
          'DEADLOCK: the gate blocks the very file that would fix the block');
    }
  }

  // --- V-HOOK-APPROVES-CLEAN: a clean system must not be denied ------------------
  {
    const dir = project('clean', fs.readFileSync(TEMPLATE, 'utf8'));
    const out = hook.run(evt(path.join(dir, 'src', 'landing.tsx'), 'Write', 's2'));
    const hso = out.hookSpecificOutput || {};
    if (!hso.permissionDecision && /APPROVE/.test(hso.additionalContext || '')) {
      ok('V-HOOK-APPROVES-CLEAN', 'clean DESIGN.md -> no deny, verdict surfaced');
    } else {
      bad('V-HOOK-APPROVES-CLEAN', `expected APPROVE advisory, got ${JSON.stringify(out).slice(0, 160)}`);
    }
  }

  // --- V-HOOK-NO-SYSTEM-ADVISES: never force the system on a repo that never opted in
  {
    const dir = project('nosystem', null);
    const out = hook.run(evt(path.join(dir, 'src', 'dashboard.tsx'), 'Write', 's3'));
    const hso = out.hookSpecificOutput || {};
    if (!hso.permissionDecision && /no DESIGN\.md/.test(hso.additionalContext || '')) {
      ok('V-HOOK-NO-SYSTEM-ADVISES', 'no DESIGN.md -> advisory, never a deny');
    } else {
      bad('V-HOOK-NO-SYSTEM-ADVISES', `expected advisory, got ${JSON.stringify(out).slice(0, 160)}`);
    }
  }

  // --- V-HOOK-BOUNDARY: a surface is judged against ITS OWN project, never a parent
  {
    const outer = project('outer', SLOP_DESIGN_MD);
    const inner = path.join(outer, 'packages', 'inner');
    fs.mkdirSync(path.join(inner, 'src'), { recursive: true });
    fs.mkdirSync(path.join(inner, '.git'));       // inner is its own project, no DESIGN.md
    const out = hook.run(evt(path.join(inner, 'src', 'hero.tsx'), 'Write', 's4'));
    const hso = out.hookSpecificOutput || {};
    if (!hso.permissionDecision) {
      ok('V-HOOK-BOUNDARY', 'inner project not judged against the outer project\'s DESIGN.md');
    } else {
      bad('V-HOOK-BOUNDARY', 'a surface was denied against a DESIGN.md across a .git boundary');
    }
  }

  // --- V-HOOK-INERT: non-visual writes are untouched -----------------------------
  {
    const dir = project('inert', SLOP_DESIGN_MD);
    const a = hook.run(evt(path.join(dir, 'src', 'utils.py'), 'Write', 's5'));
    const b = hook.run(evt(path.join(dir, 'README.md'), 'Write', 's5'));
    const c = hook.run({ tool_name: 'Read', tool_input: { file_path: path.join(dir, 'x.tsx') } });
    if (Object.keys(a).length === 0 && Object.keys(b).length === 0 && Object.keys(c).length === 0) {
      ok('V-HOOK-INERT', 'python / readme / Read -> {} (no noise on non-visual work)');
    } else {
      bad('V-HOOK-INERT', 'the hook fired on a non-visual surface');
    }
  }

  // --- V-HOOK-FAIL-OPEN: garbage in must never block -----------------------------
  {
    const cases = [null, undefined, {}, { tool_name: 'Write' }, { tool_input: {} },
                   { tool_name: 'Write', tool_input: { file_path: '' } }];
    let clean = true;
    for (const c of cases) {
      let r;
      try { r = hook.run(c); } catch (e) { clean = false; break; }
      if (r && r.hookSpecificOutput && r.hookSpecificOutput.permissionDecision) clean = false;
    }
    if (clean) {
      ok('V-HOOK-FAIL-OPEN', 'malformed input -> {} , never a throw, never a deny');
    } else {
      bad('V-HOOK-FAIL-OPEN', 'a broken gate must stand down, not block');
    }
  }

  const total = passes + fails;
  console.log(`\nHOOK_PASS=${passes}/${total}  threshold=${total}/${total}`);
  return fails === 0 ? 0 : 1;
}

process.exit(main());
