#!/usr/bin/env node
/*
 * tests/selector.test.js — CDICF A4
 *
 * The load-bearing cases are the abstentions. A selector that always returns a
 * winner is a ranker; the decisions worth having are the ones where it declines,
 * and each must arrive as an explicit code and remedy rather than as an empty
 * array a caller has to interpret.
 *
 * Run:
 *   node --test tests/selector.test.js
 */

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { select, MIN_SCORE } = require('../modules/cdicf/selector');

const ROOT     = path.join(__dirname, '..');
const SELECTOR = path.join(ROOT, 'modules', 'cdicf', 'selector.js');
const EXAMPLES = path.join(ROOT, 'modules', 'cdicf', 'examples');

const SHADCN     = JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'shadcn-ui.button.json'), 'utf8'));
const REACT_BITS = JSON.parse(fs.readFileSync(path.join(EXAMPLES, 'react-bits.split-text.json'), 'utf8'));

const clone = (o) => JSON.parse(JSON.stringify(o));

/*
 * Synthetic candidates, built by overriding the real shadcn manifest so they
 * still satisfy every A2 invariant — a fixture that could not pass validation
 * would be testing the validator, not the selector.
 */
function make(overrides) {
  const m = clone(SHADCN);
  for (const [section, fields] of Object.entries(overrides)) {
    Object.assign(m[section], fields);
  }
  return m;
}

const HEADING = make({
  identity: { id: 'primitives/text-heading', name: 'Text Heading' },
  selection: { identity_fit_score: 70, alternatives: [] },
  quality: { known_failures: [] },
});

const intent = (text, extra) => Object.assign({ text }, extra || {});

/* ---------------- The licence boundary ----------------------------------- */

test('V-SEL-01 — a PROHIBITED component never reaches the ranking', () => {
  // Arrange — a relevant restricted component alongside a relevant lawful one.
  const candidates = [HEADING, REACT_BITS];

  // Act
  const res = select(intent('split text heading'), candidates, {});

  // Assert — filtered before scoring, and named in the rejections.
  assert.equal(res.ranked.some(r => r.id === 'motion-gateway/split-text'), false);
  const rej = res.rejected.find(r => r.id === 'motion-gateway/split-text');
  assert.ok(rej, 'a filtered candidate must be reported, never silently dropped');
  assert.equal(rej.filter, 'LICENCE_PROHIBITED');
  // And it carries no score at all — a number nobody may act on is noise.
  assert.equal(rej.score, undefined);
});

test('V-SEL-02 — allow_gateway admits it to the ranking but forces approval', () => {
  const res = select(intent('split text'), [REACT_BITS], { allow_gateway: true });

  assert.equal(res.decision, 'REQUIRE_APPROVAL');
  assert.equal(res.ranked[0].id, 'motion-gateway/split-text');
  assert.ok(res.approval_required_because.some(a => /may not be redistributed/.test(a)));
  assert.match(res.note, /Nothing is installed by this module/);
});

/* ---------------- Abstention is a first-class decision -------------------- */

test('V-SEL-03 — abstention is an explicit output with a code and a remedy', () => {
  const res = select(intent('button'), [make({
    quality: { wcag_level: 'fail' },
    selection: { reuse_recommendation: 'acceptable' },
  })], { required_wcag: 'AA' });

  assert.equal(res.decision, 'ABSTAIN');
  assert.ok(res.abstention, 'an abstention must be an object, not an empty array');
  assert.equal(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.dominant_filter, 'ACCESSIBILITY_FLOOR');
  assert.match(res.abstention.remedy, /WCAG/);
  assert.deepEqual(res.ranked, []);
});

test('V-SEL-04 — no candidate clears the accessibility floor', () => {
  const res = select(intent('button'), [
    make({ quality: { wcag_level: 'A' }, selection: { reuse_recommendation: 'acceptable' } }),
    make({ identity: { id: 'primitives/button-b' }, quality: { wcag_level: 'fail' },
           selection: { reuse_recommendation: 'acceptable' } }),
  ], { required_wcag: 'AAA' });

  assert.equal(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.dominant_filter, 'ACCESSIBILITY_FLOOR');
  assert.equal(res.filter_counts.ACCESSIBILITY_FLOOR, 2);
});

test('V-SEL-05 — an unassessed accessibility level is not a pass', () => {
  // The quiet failure this guards: an unmeasured value treated as neutral
  // becomes a yes, and nobody notices because nothing was ever measured.
  const res = select(intent('button'), [make({
    quality: { wcag_level: 'unassessed' },
    selection: { reuse_recommendation: 'acceptable' },
  })], { required_wcag: 'AA' });

  assert.equal(res.decision, 'ABSTAIN');
  assert.match(res.rejected[0].detail, /unassessed is not a pass/);
});

test('V-SEL-06 — every candidate busting the bundle budget is an abstention, not a cheapest-of-bad pick', () => {
  const res = select(intent('button'), [
    make({ quality: { bundle_cost_kb: 90 } }),
    make({ identity: { id: 'primitives/button-heavy' }, quality: { bundle_cost_kb: 140 } }),
  ], { bundle_budget_kb: 40 });

  assert.equal(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.dominant_filter, 'BUDGET_EXCEEDED');
  assert.match(res.abstention.remedy, /raise the budget deliberately|build something lighter/);
});

test('V-SEL-07 — a cheaper candidate still wins when one actually fits', () => {
  // The companion to V-SEL-06: abstention is for an empty field, not a
  // substitute for choosing well when a choice exists.
  const res = select(intent('button'), [
    make({ identity: { id: 'primitives/button-heavy' }, quality: { bundle_cost_kb: 140 } }),
    make({ identity: { id: 'primitives/button-light' }, quality: { bundle_cost_kb: 3 } }),
  ], { bundle_budget_kb: 40 });

  assert.notEqual(res.decision, 'ABSTAIN');
  assert.equal(res.ranked[0].id, 'primitives/button-light');
  assert.equal(res.rejected[0].filter, 'BUDGET_EXCEEDED');
});

test('V-SEL-08 — an attribution the project cannot make removes the candidate', () => {
  const res = select(intent('button'), [make({})], { can_attribute: false });

  assert.equal(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.dominant_filter, 'ATTRIBUTION_IMPOSSIBLE');
});

test('V-SEL-09 — a tour over unresolved UX findings is refused as the wrong remedy', () => {
  const tour = make({
    identity: { id: 'onboarding/product-tour', name: 'Product Tour' },
    capability: { surface: 'onboarding', component_type: 'block' },
  });

  const res = select(intent('add an onboarding tour to the dashboard'), [tour], {
    unresolved_ux_findings: [
      'users cannot find the primary action without being told where it is',
      'the empty state explains nothing about what to do first',
    ],
  });

  assert.equal(res.decision, 'ABSTAIN');
  assert.equal(res.abstention.code, 'REMEDY_NOT_A_COMPONENT');
  assert.match(res.abstention.reason, /conceal/);
  assert.match(res.abstention.remedy, /resolve the declared findings first/);
  assert.equal(res.findings.length, 2);
});

test('V-SEL-10 — the same tour IS recommendable once the findings are resolved', () => {
  const tour = make({
    identity: { id: 'onboarding/product-tour', name: 'Product Tour' },
    capability: { surface: 'onboarding', component_type: 'block' },
  });
  const res = select(intent('add an onboarding tour to the dashboard'), [tour],
    { unresolved_ux_findings: [] });

  assert.notEqual(res.decision, 'ABSTAIN');
  assert.equal(res.ranked[0].id, 'onboarding/product-tour');
});

/* ---------------- Not understanding is not the same as not fitting -------- */

test('V-SEL-11 — an unrecognised intent is reported as such, not as "nothing fits"', () => {
  // Zero relevance everywhere can mean two opposite things, and the remedies
  // are opposite too: build nothing, versus ask again in different words.
  const res = select(intent('quantum flux capacitor manifold'), [HEADING, make({})], {});

  assert.equal(res.decision, 'ABSTAIN');
  assert.equal(res.abstention.code, 'NO_RECOGNISED_INTENT_TERMS');
  assert.notEqual(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.catalogue_size, 2);
  assert.match(res.abstention.remedy, /rephrase/);
});

test('V-SEL-12 — relevance is necessary, not merely weighted', () => {
  // A flawless component that has nothing to do with the request must be
  // FILTERED, not ranked low. A weighted-only relevance term lets a component
  // win on maturity and polish for a query it does not answer at all.
  const perfect = make({
    identity: { id: 'primitives/unrelated-widget', name: 'Unrelated Widget' },
    selection: { identity_fit_score: 100, alternatives: [] },
    quality: { known_failures: [], bundle_cost_kb: 0 },
  });
  const res = select(intent('text heading'), [HEADING, perfect], {});

  assert.equal(res.ranked.length, 1);
  assert.equal(res.ranked[0].id, 'primitives/text-heading');
  assert.equal(res.rejected.find(r => r.id === 'primitives/unrelated-widget').filter, 'NO_INTENT_MATCH');
});

/* ---------------- Ranking quality ---------------------------------------- */

test('V-SEL-13 — every ranked position explains itself', () => {
  const res = select(intent('text heading button'), [
    HEADING,
    make({ identity: { id: 'primitives/button-b' }, selection: { identity_fit_score: 40 } }),
  ], {});

  assert.ok(res.ranked.length >= 2);
  for (const r of res.ranked) {
    assert.match(r.why, /ranked \d+ at /, `rank ${r.rank} has no explanation`);
    assert.match(r.why, /carried by /);
    assert.ok(Array.isArray(r.factors) && r.factors.length, 'factors must be enumerated');
    // Ordered by impact, so "why this one" is answerable in the order it mattered.
    const impacts = r.factors.map(f => Math.abs(f.contribution));
    assert.deepEqual(impacts, impacts.slice().sort((a, b) => b - a));
  }
  assert.match(res.ranked[1].why, /behind primitives\/|tied with primitives\//);
});

test('V-SEL-14 — two equivalent candidates order deterministically', () => {
  const a = make({ identity: { id: 'primitives/alpha', name: 'Text Heading' }, quality: { known_failures: [] } });
  const b = make({ identity: { id: 'primitives/beta', name: 'Text Heading' }, quality: { known_failures: [] } });

  const first  = select(intent('text heading'), [a, b], {});
  const second = select(intent('text heading'), [b, a], {});

  assert.equal(first.ranked[0].score, first.ranked[1].score, 'the fixtures must actually tie');
  assert.deepEqual(first.ranked.map(r => r.id), ['primitives/alpha', 'primitives/beta']);
  assert.deepEqual(second.ranked.map(r => r.id), first.ranked.map(r => r.id),
    'input order must not change the outcome');
  assert.match(first.ranked[1].why, /tied with/);
});

test('V-SEL-15 — a relevant known failure costs more than an irrelevant one', () => {
  const base = { identity: { id: 'primitives/a', name: 'Text Heading' }, quality: { known_failures: [] } };
  const clean     = make(base);
  const irrelevant = make({ identity: { id: 'primitives/b', name: 'Text Heading' },
    quality: { known_failures: ['the border radius is not themeable'] } });
  const relevant   = make({ identity: { id: 'primitives/c', name: 'Text Heading' },
    quality: { known_failures: ['the heading is announced twice by screen readers'] } });

  const res = select(intent('text heading'), [clean, irrelevant, relevant],
    { concerns: ['screen readers announce content correctly'] });

  const by = Object.fromEntries(res.ranked.map(r => [r.id, r]));
  assert.ok(by['primitives/a'].score > by['primitives/b'].score, 'any known failure must cost something');
  assert.ok(by['primitives/b'].score > by['primitives/c'].score, 'a relevant failure must cost more');
  assert.equal(res.ranked[0].id, 'primitives/a');
  assert.equal(by['primitives/c'].known_failures[0].relevant, true);
});

test('V-SEL-16 — prior adoption breaks ties only, and never outranks a better fit', () => {
  const popular = make({ identity: { id: 'primitives/popular', name: 'Widget' },
    selection: { identity_fit_score: 10, alternatives: [] }, quality: { known_failures: [] } });
  const better  = make({ identity: { id: 'primitives/better', name: 'Text Heading Widget' },
    selection: { identity_fit_score: 90, alternatives: [] }, quality: { known_failures: [] } });

  const res = select(intent('text heading widget'), [popular, better],
    { already_uses: ['primitives/popular'] });

  assert.equal(res.ranked[0].id, 'primitives/better',
    'an already-used component must not win on being already used');
  // It is not a scored factor at all — no contribution names it.
  assert.equal(res.ranked.every(r => r.factors.every(f => f.factor !== 'already_uses')), true);
});

/* ---------------- Thresholds and approval --------------------------------- */

test('V-SEL-17 — a field of poor fits abstains on an absolute floor, not a percentile', () => {
  // A percentile always crowns someone. An absolute floor can return nobody,
  // and a ratio would be satisfied by shrinking the candidate set.
  const weak = make({
    identity: { id: 'primitives/weak', name: 'Text' },
    quality: { maturity: 'experimental', wcag_level: 'A', bundle_cost_kb: 200,
               known_failures: ['a', 'b', 'c', 'd'] },
    capability: { accessibility_level: 'none', ssr_support: false, rsc_support: false },
    selection: { identity_fit_score: 5, reuse_recommendation: 'discouraged', alternatives: [] },
  });
  const res = select(intent('text'), [weak], {});

  assert.equal(res.decision, 'ABSTAIN');
  assert.equal(res.abstention.code, 'BELOW_THRESHOLD');
  assert.ok(res.ranked[0].score < MIN_SCORE);
  assert.match(res.abstention.remedy, /build it/);
});

test('V-SEL-18 — a close call requires approval instead of being decided silently', () => {
  const a = make({ identity: { id: 'primitives/alpha', name: 'Text Heading' },
    selection: { identity_fit_score: 71, alternatives: [] }, quality: { known_failures: [] },
    provenance: { confidence: 'VERIFIED', license_fingerprint: 'a'.repeat(64) } });
  const b = make({ identity: { id: 'primitives/beta', name: 'Text Heading' },
    selection: { identity_fit_score: 70, alternatives: [] }, quality: { known_failures: [] },
    provenance: { confidence: 'VERIFIED', license_fingerprint: 'b'.repeat(64) } });

  const res = select(intent('text heading'), [a, b], {});

  assert.equal(res.decision, 'REQUIRE_APPROVAL');
  assert.ok(res.recommended.margin < 0.05);
  assert.ok(res.approval_required_because.some(x => /not clearly determined/.test(x)));
});

test('V-SEL-19 — unverified provenance never becomes an unattended recommendation', () => {
  const res = select(intent('text heading'), [HEADING], {});
  assert.equal(res.decision, 'REQUIRE_APPROVAL');
  assert.ok(res.approval_required_because.some(x => /confidence is OBSERVED/.test(x)));
});

/* ---------------- Input honesty ------------------------------------------- */

test('V-SEL-20 — an invalid manifest is reported, not silently skipped', () => {
  // Silently dropping it would make the ranking read as "considered and not
  // chosen" when the truth is "never looked at".
  const broken = clone(SHADCN);
  delete broken.provenance.license_tier;

  const res = select(intent('text heading'), [HEADING, broken], {});
  const rej = res.rejected.find(r => r.filter === 'MANIFEST_INVALID');
  assert.ok(rej, 'an unvalidatable candidate must appear in the rejections');
  assert.equal(res.ranked.some(r => r.id === 'primitives/button'), false);
});

test('V-SEL-21 — an empty candidate set abstains explicitly', () => {
  const res = select(intent('anything'), [], {});
  assert.equal(res.decision, 'ABSTAIN');
  assert.equal(res.abstention.code, 'NO_CANDIDATES');
  assert.deepEqual(res.ranked, []);
});

/* ---------------- The engine never acts ----------------------------------- */

test('V-SEL-22 — selecting installs nothing and touches no project', () => {
  const cwd = process.cwd();
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-sel-'));
  try {
    process.chdir(scratch);
    const res = select(intent('text heading'), [HEADING], {});
    assert.notEqual(res.decision, undefined);
    assert.deepEqual(fs.readdirSync(scratch), [], 'selection must not write anything');
  } finally {
    process.chdir(cwd);
  }
  // Structural, not merely behavioural: the selector has no path to the installer.
  const src = fs.readFileSync(path.join(ROOT, 'modules', 'cdicf', 'selector.js'), 'utf8');
  assert.equal(/require\(['"]\.\/installer/.test(src), false,
    'the selector must not be able to install; recommendation and action stay apart');
});

/* ---------------- Findings from real-input verification ------------------- */

test('V-SEL-24 — a failure that merely names the component is not a relevant failure', () => {
  // Found by running the engine on the real catalogue rather than on fixtures.
  // The intent that selects a component necessarily contains its own name, so
  // any failure text mentioning that name flagged as relevant for every query
  // — a constant wearing the costume of a signal.
  const m = make({
    identity: { id: 'primitives/button-x', name: 'Button' },
    quality: { known_failures: ['a child that swallows onClick silently disables the button'] },
  });
  const res = select(intent('accessible button primitive'), [m], {});

  assert.equal(res.ranked[0].known_failures[0].relevant, false,
    'the component naming itself must not make its own failure "relevant"');

  // A declared concern is deliberate and DOES make it relevant — but only on a
  // term the failure actually contains. Matching is lexical, not semantic:
  // "clicks must always fire" shares no token with a failure written about
  // `onClick`, and the engine says so rather than inferring the connection.
  const concerned = select(intent('accessible button primitive'), [m],
    { concerns: ['onClick handlers must always fire'] });
  assert.equal(concerned.ranked[0].known_failures[0].relevant, true);

  const nearMiss = select(intent('accessible button primitive'), [m],
    { concerns: ['clicks must always fire'] });
  assert.equal(nearMiss.ranked[0].known_failures[0].relevant, false,
    'lexical matching has a real limit, and it is asserted rather than papered over');
});

test('V-SEL-25 — when no filter dominates, none is named and every remedy is given', () => {
  // Also from the real catalogue: one candidate removed by licence and one by
  // intent mismatch. Reporting "the most common was LICENCE_PROHIBITED (1)"
  // attaches a remedy that is right for one candidate and wrong for the other.
  const res = select(intent('split'), [HEADING, REACT_BITS], {});

  assert.equal(res.abstention.code, 'ALL_FILTERED');
  assert.equal(res.dominant_filter, null, 'a 1-1 split has no dominant filter');
  assert.deepEqual(res.tied_filters.sort(), ['LICENCE_PROHIBITED', 'NO_INTENT_MATCH']);
  assert.match(res.abstention.reason, /no single filter dominates/);
  assert.match(res.abstention.remedy, /ALSO/, 'both remedies must reach the caller');
});

/* ---------------- CLI ------------------------------------------------------ */

test('V-SEL-23 — the CLI signals the three decisions with distinct exit codes', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-cand-'));
  fs.writeFileSync(path.join(dir, 'heading.json'), JSON.stringify(HEADING));

  const approval = spawnSync(process.execPath,
    [SELECTOR, '--intent', 'text heading', '--candidates', dir], { encoding: 'utf8' });
  assert.equal(approval.status, 21, approval.stderr);
  assert.match(approval.stdout, /REQUIRE_APPROVAL\s+primitives\/text-heading/);

  const abstain = spawnSync(process.execPath,
    [SELECTOR, '--intent', 'quantum flux manifold', '--candidates', dir], { encoding: 'utf8' });
  assert.equal(abstain.status, 20);
  assert.match(abstain.stdout, /ABSTAIN\s+\[NO_RECOGNISED_INTENT_TERMS\]/);
  assert.match(abstain.stdout, /remedy/);

  const verified = clone(HEADING);
  verified.provenance.confidence = 'VERIFIED';
  verified.provenance.license_fingerprint = 'c'.repeat(64);
  fs.writeFileSync(path.join(dir, 'heading.json'), JSON.stringify(verified));
  const ok = spawnSync(process.execPath,
    [SELECTOR, '--intent', 'text heading', '--candidates', dir, '--json'], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  assert.equal(JSON.parse(ok.stdout).decision, 'RECOMMEND');
});
