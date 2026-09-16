#!/usr/bin/env node
/**
 * Proves a global rule file is actually inherited, rather than merely written.
 *
 * A rule that exists and reaches nobody is a document. The claim "future projects inherit this" rests
 * on one mechanism: learning-sentinel.js reads ~/.claude/rules at SessionStart and pushes each .md
 * body into the session context. No registry, no manifest -- a directory glob. That is a good design
 * and it is also the thing that could quietly stop being true: a refactor that switched to a
 * hardcoded list, or narrowed the filter, would leave every existing rule working while silently
 * orphaning every new one.
 *
 * So this drills the mechanism itself rather than asserting that a file exists. Three checks:
 *
 *   1. the hook still enumerates the directory (structurally, by reading its source);
 *   2. the enumeration it performs actually picks up every .md now present -- driven against a
 *      temporary file this test creates and deletes, so it cannot pass by naming a file that
 *      happens to be listed somewhere;
 *   3. a positive control, because an enumeration that matched nothing would otherwise report a
 *      clean bill over an empty set, which is the failure this whole file exists to notice.
 *
 * Run: node ~/.claude/hooks/tests/test-global-rule-inheritance.js
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const RULES_DIR = path.join(os.homedir(), '.claude', 'rules');
const SENTINEL = path.join(os.homedir(), '.claude', 'hooks', 'learning-sentinel.js');

let failures = 0;

function ok(name, evidence) {
  console.log(`  PASS  ${name}${evidence ? ` — ${evidence}` : ''}`);
}

function fail(name, diagnostic) {
  failures += 1;
  console.error(`  FAIL  ${name} — ${diagnostic}`);
}

console.log('test-global-rule-inheritance');

// 1. The mechanism is a glob of the rules directory, read out of the hook's own source. Asserted
//    structurally because the alternative -- trusting a comment -- is what this is guarding against.
let sentinelSource = '';
try {
  sentinelSource = fs.readFileSync(SENTINEL, 'utf8');
} catch (error) {
  fail('learning-sentinel.js is readable', String(error && error.message));
}

if (sentinelSource) {
  // Why not a single tidy pattern: the first draft used [^)]* to span the path.join arguments, which
  // cannot cross the nested os.homedir() call -- so it reported the hook as broken on its very first
  // run. The instrument was wrong, not the subject, which is the whole reason this file matches three
  // independent anchors instead of one clever one.
  const globsRulesDir =
    /RULES_DIR\s*=\s*path\.join\(/.test(sentinelSource) &&
    /['"]rules['"]\s*\)/.test(sentinelSource) &&
    /readdirSync\(RULES_DIR\)/.test(sentinelSource) &&
    /endsWith\(['"]\.md['"]\)/.test(sentinelSource);
  if (globsRulesDir) {
    ok('the session hook enumerates ~/.claude/rules/*.md rather than a fixed list');
  } else {
    fail(
      'the session hook enumerates ~/.claude/rules/*.md rather than a fixed list',
      'RULES_DIR glob not found in learning-sentinel.js — a new rule file may no longer be inherited, ' +
        'which looks identical from the outside to one that is'
    );
  }
  // 2026-09-16 -- STRENGTHENED, and the reason matters more than the change.
  //
  // This used to grep for the literal `ctx.push(\`### Global Rule: ${rf}` and it
  // was RIGHT to fail when that disappeared: a hook that names files instead of
  // delivering them satisfies every enumeration check while inheriting nothing.
  // Its own diagnostic said so -- "enumerating the files is not the same as
  // delivering them" -- and that objection is what turned a truncation into a
  // relocation rather than being argued away.
  //
  // What changed underneath: inlining every rule body put ~148 KB through the
  // hook's stdout, whose OS pipe buffer is 4-64 KB. On Windows that write is
  // SYNCHRONOUS, so once the buffer fills with no reader it blocks the event
  // loop and no timer can bound it -- the 40-minute SessionStart stall. The
  // bodies cannot travel inline. They now travel in a bundle file and the
  // emission carries a pointer to it.
  //
  // So the assertion moved from SOURCE SHAPE to DELIVERY, which is both what the
  // original intended and harder to satisfy by accident: a source grep passes on
  // a hook that builds the string and never emits it, while this requires the
  // bytes to exist somewhere a reader can reach.
  const emitsInline = /### Global Rule: \$\{(rf|f)\}/.test(sentinelSource);
  const writesBundle = /inherited-global-rules\.md/.test(sentinelSource)
    && /writeFileSync\(/.test(sentinelSource);
  if (emitsInline && writesBundle) {
    ok('each rule body is delivered — inline while it fits, by bundle file beyond that');
  } else {
    fail(
      'each rule body is delivered — inline while it fits, by bundle file beyond that',
      `the delivery site changed shape (inline=${emitsInline} bundle=${writesBundle}); ` +
        'enumerating the files is not the same as delivering them'
    );
  }
}

// 2. Drive the enumeration against a file the hook has never seen. Naming an existing rule would
//    prove only that the existing rules are listed somewhere, which is the weaker claim.
function enumerate() {
  return fs
    .readdirSync(RULES_DIR)
    .filter((f) => f.endsWith('.md'))
    .sort();
}

const probeName = `zz-inheritance-probe-${process.pid}.md`;
const probePath = path.join(RULES_DIR, probeName);
try {
  const before = enumerate();

  // 3. Positive control on the population. An enumeration that returned nothing would satisfy every
  //    "is my file absent" style check and report a clean sweep over an empty set.
  if (before.length >= 3) {
    ok('the enumeration finds the existing rules', `${before.length} files`);
  } else {
    fail(
      'the enumeration finds the existing rules',
      `only ${before.length} found — too few to distinguish a working glob from a broken one`
    );
  }

  fs.writeFileSync(probePath, '# probe\n', 'utf8');
  const after = enumerate();
  if (after.includes(probeName)) {
    ok('a newly added rule file is picked up with no registration');
  } else {
    fail(
      'a newly added rule file is picked up with no registration',
      'the glob did not see a file created moments earlier, so inheritance is not automatic'
    );
  }

  // 3b. DRIVE IT. Everything above reads source or reads the directory; neither
  //     can tell a hook that delivers from one that merely could. So run the
  //     real hook with a real payload and require the bytes to arrive -- and
  //     require the EMISSION to stay under the pipe budget in the same breath,
  //     because satisfying either one alone is how this regressed.
  try {
    const { execFileSync } = require('child_process');
    const raw = execFileSync(process.execPath, [SENTINEL], {
      input: JSON.stringify({
        hook_event_name: 'SessionStart', session_id: 'inheritance-probe',
        cwd: process.cwd(), source: 'startup',
      }),
      encoding: 'utf8',
      timeout: 20000,
    });
    const emitted = JSON.parse(raw);
    const ctx = (emitted.hookSpecificOutput && emitted.hookSpecificOutput.additionalContext) || '';
    const emissionBytes = Buffer.byteLength(ctx, 'utf8');

    const bundlePath = path.join(os.homedir(), '.claude', 'state', 'inherited-global-rules.md');
    const bundle = fs.existsSync(bundlePath) ? fs.readFileSync(bundlePath, 'utf8') : '';
    const delivered = new Set(
      (bundle.match(/^### Global Rule: (.+)$/gm) || []).map(l => l.replace(/^### Global Rule: /, ''))
    );
    for (const l of ctx.split('\n')) {
      const m = /^### Global Rule: (.+)$/.exec(l);
      if (m) delivered.add(m[1]);
    }
    // The probe file is created moments before and is legitimately absent from a
    // bundle written earlier in the same run; judge the stable population.
    const expected = after.filter(f => f !== probeName);
    const missing = expected.filter(f => !delivered.has(f));

    if (missing.length === 0) {
      ok('every rule body actually reaches a reader',
        `${expected.length} delivered (emission ${emissionBytes} B + bundle ${bundle.length} B)`);
    } else {
      fail('every rule body actually reaches a reader',
        `${missing.length} rule(s) enumerated but delivered NOWHERE: ${missing.join(', ')} — ` +
        'neither inline nor in the bundle file, which is a rule that exists and reaches nobody');
    }

    // The constraint that forced the bundle in the first place. Without this the
    // obvious "fix" to the check above is to inline everything again, which
    // restores the SessionStart stall.
    if (emissionBytes <= 4096) {
      ok('the emission stays inside the pipe budget', `${emissionBytes} B <= 4096 B`);
    } else {
      fail('the emission stays inside the pipe budget',
        `${emissionBytes} B exceeds the 4096 B undrained-pipe buffer — on Windows that write is ` +
        'SYNCHRONOUS and blocks the event loop with no timer able to bound it');
    }
  } catch (error) {
    fail('every rule body actually reaches a reader',
      `could not drive the hook: ${error && error.message} — this judged nothing`);
  }

  // The rule this drill was built for. Checked last, so a failure above is not mistaken for this one.
  if (after.includes('destructive-state-authorization.md')) {
    ok('the destructive-state authorization rule is in the inherited set');
  } else {
    fail(
      'the destructive-state authorization rule is in the inherited set',
      'the file is missing from ~/.claude/rules, so no future session receives it'
    );
  }
} catch (error) {
  fail('the rules directory can be enumerated and written', String(error && error.message));
} finally {
  try {
    if (fs.existsSync(probePath)) {
      fs.unlinkSync(probePath);
    }
  } catch {
    console.error(`  WARN  could not remove probe file ${probePath} — remove it by hand`);
  }
}

// 4. Inheriting the FILE is not inheriting the LESSON. A rule that says "refuse when the state the user
//    saw has changed" and stops there leaves the harder question unasked -- whether anything can move
//    between that check and the irreversible step. Those are different properties, and a destructive
//    feature can satisfy the first completely while losing data to the second.
//
//    These rules are agent-injected prose, not an executable gate, so the honest enforcement is that the
//    delivered text still carries the questions. Matched against a SYNTHETIC body as well as the real
//    one: a drill pointed only at the real file would pass vacuously the day someone rewrote it, and a
//    drill pointed only at a defect has an interest in that defect surviving.
function demandsEffectIntervalAnalysis(body) {
  // Whitespace-collapsed before matching: prose wraps, and a predicate that broke when a sentence was
  // reflowed would report missing doctrine on a rule that still states it. The synthetic green half below
  // caught exactly that -- its phrase spanned a line break and the literal-space pattern missed it.
  const lowered = body.toLowerCase().replace(/\s+/g, ' ');
  return (
    /between the final check and the (destruction|effect)/.test(lowered) &&
    /re-?authorize/.test(lowered) &&
    /(subprocess|await|process boundary)/.test(lowered)
  );
}

const STALE_ONLY_RULE = [
  '# Destructive guard',
  'Capture what the user observed and refuse the operation when the current state no longer matches it.',
  'The authoritative side compares, never the client. Report the refusal in its own words.'
].join('\n');

const INTERVAL_AWARE_RULE = [
  '# Destructive guard',
  'Capture what the user observed and refuse when the current state no longer matches.',
  'A precondition covers the effect only if the state cannot move between the final check and the',
  'destruction: enumerate every await and subprocess in that interval, and re-authorize each batch',
  'member against its own destruction.'
].join('\n');

try {
  // The red branch, on a subject that cannot be fixed out from under the assertion.
  if (demandsEffectIntervalAnalysis(STALE_ONLY_RULE)) {
    fail(
      'a stale-only destructive rule is recognised as incomplete',
      'the predicate accepted a rule that never mentions the validate-to-effect interval, so it would ' +
        'report a clean bill over doctrine that cannot prevent the race'
    );
  } else {
    ok('a stale-only destructive rule is recognised as incomplete');
  }
  // The green half, so a predicate that rejected everything could not pass the red branch and look real.
  if (demandsEffectIntervalAnalysis(INTERVAL_AWARE_RULE)) {
    ok('an interval-aware destructive rule is recognised as complete');
  } else {
    fail(
      'an interval-aware destructive rule is recognised as complete',
      'the predicate rejects text that does state the interval requirement, so it cannot distinguish'
    );
  }

  const destructiveRule = fs.readFileSync(
    path.join(RULES_DIR, 'destructive-state-authorization.md'),
    'utf8'
  );
  if (demandsEffectIntervalAnalysis(destructiveRule)) {
    ok('the inherited destructive rule forces the validate-to-effect question');
  } else {
    fail(
      'the inherited destructive rule forces the validate-to-effect question',
      'the rule is inherited but no longer asks what can move between the final check and the effect, ' +
        'which is the half a sequential stale test cannot cover'
    );
  }
} catch (error) {
  fail('the destructive rule can be read and evaluated', String(error && error.message));
}

if (failures > 0) {
  console.error(`test-global-rule-inheritance: ${failures} failed`);
  process.exit(1);
}
console.log('test-global-rule-inheritance: all passed');
