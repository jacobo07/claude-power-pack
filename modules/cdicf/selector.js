#!/usr/bin/env node
/*
 * modules/cdicf/selector.js — CDICF A4
 *
 * Given an intent, a project context and a set of Component Manifests, returns
 * the lowest-risk composition — or declines to return one.
 *
 * Usage:
 *   node modules/cdicf/selector.js --intent "<text>" --candidates <dir> [--context <json>] [--json]
 *
 * Exit codes:
 *   0  RECOMMEND        · 2 argv · 3 io
 *   20 ABSTAIN          — a decision, not a failure
 *   21 REQUIRE_APPROVAL — a candidate stands, but not unattended
 *
 * Non-zero here does not mean the run went wrong. It means "not an unattended
 * install", which is the only thing a calling script actually needs to branch on.
 *
 * ABSTENTION IS THE POINT
 * ----------------------
 * A selector that always returns something is a ranker, not a decision-maker.
 * The valuable answer is often "install nothing" — because no candidate clears
 * the accessibility floor, because the cheapest one still busts the budget,
 * because the licence needs an attribution this project cannot make, or because
 * the request is for a component that would paper over a problem elsewhere.
 * Every one of those is an explicit output with a code and a remedy. An empty
 * array is not an abstention; it is a silence that reads as "nothing matched"
 * when the truth may be "nothing should be installed here".
 *
 * WHY RELEVANCE IS NECESSARY, NOT WEIGHTED
 * ----------------------------------------
 * This estate has already been burned by a scorer whose factors were per-item
 * constants: maturity, bundle size and accessibility are properties of a
 * component and do not change with what was asked for, so a weighted sum of
 * them ranks the catalogue identically for every query. Relevance is the only
 * term that varies with the intent, so it is a HARD FILTER first and a weighted
 * term second. Zero relevance removes a candidate; it does not merely cost it
 * points it can win back by being popular.
 *
 * WHY THE VOCABULARY IS DISCOVERED
 * --------------------------------
 * Matching against a hand-written keyword list means an intent phrased in
 * unfamiliar words scores zero against everything — and zero never falls, so
 * that reads as "no component fits" when it actually means "the question was
 * not understood". The vocabulary is therefore derived from the candidate set
 * itself, and an intent sharing no term with it is reported as
 * NO_RECOGNISED_INTENT_TERMS: a distinct outcome from a considered abstention,
 * because the remedies are opposite. One says build nothing; the other says ask
 * again in different words.
 *
 * THIS MODULE NEVER INSTALLS
 * --------------------------
 * It returns a decision. It does not require the installer, does not touch the
 * filesystem outside reading the candidates it was pointed at, and has no path
 * that mutates a project. Recommendation and action are kept apart so that a
 * high-uncertainty call reaches a human before anything lands.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const { REDISTRIBUTION_BY_TIER } = require('../../lib/license_gate');
const { validate, loadSchema } = require('./validate_manifest');

/* Absolute thresholds. Never a ratio and never a percentile: a ratio is
 * satisfied by shrinking the candidate set, and a percentile always returns a
 * winner no matter how bad the field is. */
const MIN_SCORE = 0.45;
const APPROVAL_MARGIN = 0.05;

const WEIGHTS = {
  relevance:      0.34,
  identity_fit:   0.20,
  maturity:       0.12,
  accessibility:  0.12,
  bundle:         0.10,
  stack_fit:      0.06,
  reuse:          0.06,
};
const FAILURE_PENALTY = 0.05;        // per known failure
const FAILURE_PENALTY_MAX = 0.20;
const RELEVANT_FAILURE_MULTIPLIER = 2;

const MATURITY = { experimental: 0.15, beta: 0.45, stable: 0.85, mature: 1.0 };
const REUSE    = { prefer: 1.0, acceptable: 0.6, discouraged: 0.15, forbidden: 0 };
const WCAG_RANK = { fail: 0, unassessed: 0, A: 1, AA: 2, AAA: 3 };
const A11Y     = { none: 0, unassessed: 0, partial: 0.5, full: 1.0 };
const MOTION_RANK = { none: 0, low: 1, medium: 2, high: 3 };

const STOPWORDS = new Set([
  'a', 'an', 'the', 'for', 'with', 'and', 'or', 'of', 'to', 'in', 'on', 'that',
  'this', 'it', 'is', 'be', 'as', 'at', 'by', 'from', 'we', 'i', 'need', 'want',
  'add', 'use', 'using', 'some', 'my', 'our',
]);

function tokens(text) {
  return String(text || '')
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(t => t.length > 2 && !STOPWORDS.has(t));
}

/* Every word the candidate set can be described by. Discovered, so it cannot
 * go stale relative to the catalogue it is meant to describe. */
function buildVocabulary(manifests) {
  const vocab = new Set();
  for (const m of manifests) {
    for (const t of tokens(m.identity.name)) vocab.add(t);
    for (const t of tokens(m.identity.id)) vocab.add(t);
    for (const t of tokens(m.identity.upstream_namespace)) vocab.add(t);
    for (const t of tokens(m.identity.local_namespace)) vocab.add(t);
    vocab.add(m.capability.component_type);
    vocab.add(m.capability.surface);
    for (const alt of m.selection.alternatives || []) for (const t of tokens(alt)) vocab.add(t);
  }
  return vocab;
}

function candidateTerms(m) {
  const t = new Set();
  for (const x of tokens(m.identity.name)) t.add(x);
  for (const x of tokens(m.identity.id)) t.add(x);
  for (const x of tokens(m.identity.upstream_namespace)) t.add(x);
  t.add(m.capability.component_type);
  t.add(m.capability.surface);
  for (const alt of m.selection.alternatives || []) for (const x of tokens(alt)) t.add(x);
  return t;
}

/*
 * Relevance of one candidate to the intent, in [0,1]. Only the intent terms the
 * catalogue actually knows are counted, so an unknown word neither helps nor
 * silently dilutes the score of every candidate equally.
 */
function relevanceOf(manifest, knownIntentTerms, intent) {
  if (!knownIntentTerms.length) return 0;
  const terms = candidateTerms(manifest);
  let hits = 0;
  for (const t of knownIntentTerms) if (terms.has(t)) hits += 1;
  let score = hits / knownIntentTerms.length;

  // An explicitly requested type or surface is a stronger signal than a word
  // that merely appears in a name, and an explicit mismatch is decisive.
  if (intent.component_type) {
    if (intent.component_type !== manifest.capability.component_type) return 0;
    score = Math.min(1, score + 0.25);
  }
  if (intent.surface) {
    if (intent.surface !== manifest.capability.surface) return 0;
    score = Math.min(1, score + 0.25);
  }
  return score;
}

/* ------------------------------------------------------------------------- *
 * Hard filters — absolute predicates, evaluated before any score exists.
 * A filtered candidate is never scored: a score it cannot act on is noise the
 * reader has to learn to ignore.
 * ------------------------------------------------------------------------- */

function hardFilters(m, ctx, relevance) {
  const out = [];

  if (m.selection.reuse_recommendation === 'forbidden') {
    out.push({ filter: 'REUSE_FORBIDDEN', detail: 'the manifest marks this component forbidden for reuse' });
  }

  if (m.lifecycle.state !== 'active') {
    out.push({ filter: 'LIFECYCLE', detail: `lifecycle.state is '${m.lifecycle.state}'` });
  }

  const posture = REDISTRIBUTION_BY_TIER[m.provenance.license_tier];
  if (posture === 'prohibited' && !ctx.allow_gateway) {
    // Adopting a restricted component propagates the restriction to whatever
    // the project itself ships. That is a licensing decision, not a ranking
    // one, so it is made before scoring and reversed only by an explicit flag.
    out.push({
      filter: 'LICENCE_PROHIBITED',
      detail: `license_tier ${m.provenance.license_tier} derives redistribution 'prohibited'; ` +
              'set context.allow_gateway to consider it as an upstream reference requiring approval',
    });
  }

  if (posture === 'unknown') {
    out.push({ filter: 'LICENCE_UNKNOWN', detail: 'redistribution posture cannot be derived; an unresolved licence is not a permissive one' });
  }

  if (m.provenance.notice_required && ctx.can_attribute === false) {
    out.push({ filter: 'ATTRIBUTION_IMPOSSIBLE', detail: 'the licence requires a notice this project has declared it cannot carry' });
  }

  if (ctx.stack) {
    if (ctx.stack.ssr === true && m.capability.ssr_support !== true) {
      out.push({ filter: 'STACK_INCOMPATIBLE', detail: 'the project renders on the server; this component does not support SSR' });
    }
    if (ctx.stack.rsc === true && m.capability.rsc_support !== true) {
      out.push({ filter: 'STACK_INCOMPATIBLE', detail: 'the project uses React Server Components; this component does not support them' });
    }
  }

  if (ctx.required_wcag) {
    const need = WCAG_RANK[ctx.required_wcag];
    const have = WCAG_RANK[m.quality.wcag_level];
    // `unassessed` ranks 0 deliberately. An unmeasured level is not a passing
    // one, and treating it as neutral is how an unknown quietly becomes a yes.
    if (!(have >= need)) {
      out.push({
        filter: 'ACCESSIBILITY_FLOOR',
        detail: `project requires WCAG ${ctx.required_wcag}; component is '${m.quality.wcag_level}'` +
                (m.quality.wcag_level === 'unassessed' ? ' (unassessed is not a pass)' : ''),
      });
    }
  }

  if (typeof ctx.bundle_budget_kb === 'number' && m.quality.bundle_cost_kb > ctx.bundle_budget_kb) {
    out.push({
      filter: 'BUDGET_EXCEEDED',
      detail: `${m.quality.bundle_cost_kb} kB exceeds the project's ${ctx.bundle_budget_kb} kB budget`,
    });
  }

  if (ctx.motion_budget && MOTION_RANK[m.capability.motion_budget] > MOTION_RANK[ctx.motion_budget]) {
    out.push({
      filter: 'MOTION_BUDGET',
      detail: `component motion budget '${m.capability.motion_budget}' exceeds the project's '${ctx.motion_budget}'`,
    });
  }

  if (relevance === 0) {
    out.push({ filter: 'NO_INTENT_MATCH', detail: 'shares no term with the intent, or contradicts an explicitly requested type or surface' });
  }

  return out;
}

/* ------------------------------------------------------------------------- *
 * Soft scoring
 * ------------------------------------------------------------------------- */

/*
 * A known failure is "relevant" when it touches something the caller actually
 * cares about — not when it merely names the component.
 *
 * The component's own identity terms are excluded from the concern set,
 * because those are precisely the terms that made it match in the first place.
 * Without this, every failure whose text mentions the component by name flags
 * as relevant for every query that could have selected it, and the signal
 * becomes a constant. Observed on the real shadcn Button: intent "accessible
 * button primitive" marked a failure relevant purely because the sentence
 * contains the word "button". Declared `concerns` are never excluded — those
 * are deliberate.
 */
function relevantFailures(m, intentTerms, ctx) {
  const own = candidateTerms(m);
  const concern = new Set(intentTerms.filter(t => !own.has(t)));
  for (const c of ctx.concerns || []) for (const t of tokens(c)) concern.add(t);
  return (m.quality.known_failures || []).map(f => ({
    text: f,
    relevant: tokens(f).some(t => concern.has(t)),
  }));
}

function scoreOf(m, ctx, relevance, intentTerms) {
  const factors = {};
  factors.relevance     = relevance;
  factors.identity_fit  = Math.max(0, Math.min(100, m.selection.identity_fit_score)) / 100;
  factors.maturity      = MATURITY[m.quality.maturity] ?? 0;
  factors.accessibility = A11Y[m.capability.accessibility_level] ?? 0;
  factors.bundle = typeof ctx.bundle_budget_kb === 'number' && ctx.bundle_budget_kb > 0
    ? Math.max(0, 1 - (m.quality.bundle_cost_kb / ctx.bundle_budget_kb))
    : (m.quality.bundle_cost_kb === 0 ? 1 : 1 / (1 + m.quality.bundle_cost_kb / 25));
  factors.stack_fit = ((m.capability.ssr_support ? 0.5 : 0) + (m.capability.rsc_support ? 0.5 : 0));
  factors.reuse = REUSE[m.selection.reuse_recommendation] ?? 0;

  const contributions = Object.entries(WEIGHTS)
    .map(([name, w]) => ({ factor: name, weight: w, value: factors[name], contribution: w * factors[name] }));

  const failures = relevantFailures(m, intentTerms, ctx);
  const rawPenalty = failures.reduce(
    (acc, f) => acc + FAILURE_PENALTY * (f.relevant ? RELEVANT_FAILURE_MULTIPLIER : 1), 0);
  const penalty = Math.min(FAILURE_PENALTY_MAX, rawPenalty);

  const base = contributions.reduce((a, c) => a + c.contribution, 0);
  contributions.push({ factor: 'known_failures', weight: -1, value: failures.length, contribution: -penalty });
  // Ordered by absolute impact so "why this component" is answerable in the
  // order the answer actually mattered.
  contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  return { score: Number((base - penalty).toFixed(6)), factors, contributions, failures, penalty };
}

/* ------------------------------------------------------------------------- *
 * Decision
 * ------------------------------------------------------------------------- */

function abstain(code, reason, remedy, extra) {
  return Object.assign({ decision: 'ABSTAIN', abstention: { code, reason, remedy }, ranked: [] }, extra || {});
}

/*
 * select(intent, manifests, context) -> decision object
 *
 * intent:  { text, component_type?, surface? }
 * context: { stack?:{ssr,rsc}, required_wcag?, bundle_budget_kb?, motion_budget?,
 *            can_attribute?, allow_gateway?, concerns?:[], already_uses?:[],
 *            unresolved_ux_findings?:[] }
 */
function select(intent, manifests, context) {
  const ctx = context || {};
  const intentObj = typeof intent === 'string' ? { text: intent } : (intent || {});
  const rejected = [];

  const valid = [];
  const schema = loadSchema();
  for (const m of manifests || []) {
    const r = validate(m, schema);
    if (!r.valid) {
      // Not skipped silently: a manifest that cannot be trusted is reported, or
      // its absence from the ranking reads as "considered and not chosen".
      rejected.push({
        id: (m && m.identity && m.identity.id) || '<unidentified>',
        filter: 'MANIFEST_INVALID',
        detail: r.errors.slice(0, 3).map(e => e.rule || e.path).join('; '),
      });
    } else {
      valid.push(m);
    }
  }

  if (!valid.length) {
    return abstain('NO_CANDIDATES',
      manifests && manifests.length
        ? 'every candidate failed manifest validation'
        : 'no candidates were supplied',
      'supply a validated candidate set before asking for a recommendation',
      { rejected });
  }

  // A guidance overlay laid over an unresolved usability problem hides the
  // problem and adds a component. The remedy is not a better tour.
  const wantsGuidance = /\b(tour|walkthrough|onboarding|coach\s?mark|product\s?tour)\b/i.test(intentObj.text || '')
    || intentObj.surface === 'onboarding';
  const uxFindings = ctx.unresolved_ux_findings || [];
  if (wantsGuidance && uxFindings.length) {
    return abstain('REMEDY_NOT_A_COMPONENT',
      `the project declares ${uxFindings.length} unresolved usability finding(s) on this surface; ` +
      'a guidance overlay would conceal them rather than resolve them',
      'resolve the declared findings first, then re-ask — a tour is worth installing over an interface that already works',
      { rejected, findings: uxFindings });
  }

  const vocabulary = buildVocabulary(valid);
  const intentTerms = tokens(intentObj.text);
  const knownIntentTerms = intentTerms.filter(t => vocabulary.has(t));

  // Distinct from "nothing fits". If the catalogue recognises none of the
  // words, the question was not understood, and the remedy is to ask again.
  if (!knownIntentTerms.length && !intentObj.component_type && !intentObj.surface) {
    return abstain('NO_RECOGNISED_INTENT_TERMS',
      `none of the intent's terms appear anywhere in the ${valid.length}-component catalogue`,
      'rephrase using the catalogue\'s own vocabulary, or pass component_type / surface explicitly',
      { rejected, intent_terms: intentTerms, catalogue_size: valid.length });
  }

  const survivors = [];
  for (const m of valid) {
    const relevance = relevanceOf(m, knownIntentTerms, intentObj);
    const filters = hardFilters(m, ctx, relevance);
    if (filters.length) {
      rejected.push({ id: m.identity.id, filter: filters[0].filter, detail: filters[0].detail, all_filters: filters.map(f => f.filter) });
      continue;
    }
    survivors.push(Object.assign({ manifest: m, id: m.identity.id, name: m.identity.name },
      scoreOf(m, ctx, relevance, intentTerms)));
  }

  if (!survivors.length) {
    // Name the filter that actually emptied the field. "No candidate matched"
    // is not actionable; "every candidate failed the accessibility floor" is.
    const counts = {};
    for (const r of rejected) counts[r.filter] = (counts[r.filter] || 0) + 1;
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const topCount = entries[0][1];
    const tied = entries.filter(e => e[1] === topCount).map(e => e[0]);

    // Naming a "dominant" filter when nothing dominates is worse than naming
    // none: the remedy that follows is right for one candidate and wrong for
    // the rest. Observed on the real two-component catalogue, where a licence
    // refusal and an intent mismatch each removed one candidate and the output
    // advised only the licence remedy.
    const dominant = tied.length === 1 ? tied[0] : null;
    const fallback = 'relax the binding constraint, or build the component rather than adopt one';
    return abstain('ALL_FILTERED',
      dominant
        ? `all ${valid.length} candidates were removed by hard filters; the most common was ${dominant} (${topCount})`
        : `all ${valid.length} candidates were removed by hard filters, and no single filter dominates — ` +
          `${tied.join(', ')} each removed ${topCount}`,
      dominant
        ? (REMEDY_BY_FILTER[dominant] || fallback)
        : (tied.map(t => REMEDY_BY_FILTER[t]).filter(Boolean).join('  ALSO: ') || fallback),
      { rejected, filter_counts: counts, dominant_filter: dominant, tied_filters: tied });
  }

  // Deterministic ordering. Prior adoption is a TIEBREAK only and never a
  // scored term, so a component cannot win on being already popular.
  const adopted = new Set(ctx.already_uses || []);
  survivors.sort((a, b) =>
    b.score - a.score ||
    b.factors.relevance - a.factors.relevance ||
    b.factors.identity_fit - a.factors.identity_fit ||
    a.manifest.quality.bundle_cost_kb - b.manifest.quality.bundle_cost_kb ||
    a.failures.length - b.failures.length ||
    (adopted.has(b.id) ? 1 : 0) - (adopted.has(a.id) ? 1 : 0) ||
    a.id.localeCompare(b.id));

  const ranked = survivors.map((s, i) => ({
    rank: i + 1,
    id: s.id,
    name: s.name,
    score: s.score,
    why: explainOne(s, i, survivors, adopted),
    factors: s.contributions,
    known_failures: s.failures,
  }));

  const best = survivors[0];
  if (best.score < MIN_SCORE) {
    return abstain('BELOW_THRESHOLD',
      `the best candidate (${best.id}) scores ${best.score}, below the ${MIN_SCORE} floor`,
      'no component here is a good enough fit to adopt; build it, or restate the intent',
      { rejected, ranked });
  }

  const runnerUp = survivors[1];
  const margin = runnerUp ? Number((best.score - runnerUp.score).toFixed(6)) : null;
  const approval = [];
  if (REDISTRIBUTION_BY_TIER[best.manifest.provenance.license_tier] === 'prohibited') {
    approval.push('the winning component may not be redistributed; it can only be referenced upstream');
  }
  if (best.manifest.selection.reuse_recommendation === 'discouraged') {
    approval.push('the manifest discourages reuse of the winning component');
  }
  if (best.failures.some(f => f.relevant)) {
    approval.push('the winning component has a known failure relevant to this intent or context');
  }
  if (margin !== null && margin < APPROVAL_MARGIN) {
    approval.push(`the top two candidates are within ${margin} — the choice is not clearly determined`);
  }
  if (best.manifest.provenance.confidence !== 'VERIFIED') {
    approval.push(`provenance confidence is ${best.manifest.provenance.confidence}, not VERIFIED`);
  }

  return {
    decision: approval.length ? 'REQUIRE_APPROVAL' : 'RECOMMEND',
    abstention: null,
    recommended: { id: best.id, name: best.name, score: best.score, margin },
    approval_required_because: approval,
    ranked,
    rejected,
    abstention_conditions: best.manifest.selection.abstention_conditions || [],
    note: 'This is a recommendation. Nothing is installed by this module.',
  };
}

const REMEDY_BY_FILTER = {
  ACCESSIBILITY_FLOOR:    'no candidate meets the required WCAG level; lower the requirement deliberately or build an accessible component',
  BUDGET_EXCEEDED:        'every candidate exceeds the bundle budget; raise the budget deliberately or build something lighter',
  ATTRIBUTION_IMPOSSIBLE: 'every candidate requires a notice this project cannot carry; resolve the attribution constraint first',
  LICENCE_PROHIBITED:     'every candidate is redistribution-restricted; set allow_gateway to consider upstream references, with approval',
  STACK_INCOMPATIBLE:     'no candidate supports this rendering model; check the stack declaration before relaxing it',
  MOTION_BUDGET:          'every candidate exceeds the motion budget; raise it deliberately or choose a static treatment',
  NO_INTENT_MATCH:        'nothing in the catalogue addresses this intent; this is a gap to build, not a search to retry',
  LIFECYCLE:              'the only matches are deprecated, retired or quarantined; do not adopt them',
};

function explainOne(s, i, all, adopted) {
  const top = s.contributions.filter(c => c.contribution > 0).slice(0, 2)
    .map(c => `${c.factor} ${c.value.toFixed ? c.value.toFixed(2) : c.value}`);
  const drags = s.contributions.filter(c => c.contribution < 0)
    .map(c => `${c.factor} -${Math.abs(c.contribution).toFixed(3)}`);
  const parts = [`ranked ${i + 1} at ${s.score}`, `carried by ${top.join(' and ')}`];
  if (drags.length) parts.push(`held back by ${drags.join(', ')}`);
  if (i > 0) {
    const ahead = all[i - 1];
    const diff = Number((ahead.score - s.score).toFixed(6));
    parts.push(diff === 0
      ? `tied with ${ahead.id} on score; ordered behind it by the deterministic tiebreak`
      : `behind ${ahead.id} by ${diff}`);
  }
  if (adopted.has(s.id)) parts.push('already used in this project (tiebreak only, not scored)');
  return parts.join('; ');
}

/* ------------------------------------------------------------------------- *
 * CLI
 * ------------------------------------------------------------------------- */

function loadCandidates(dir) {
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.json'))
    .sort()
    .map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

const USAGE =
  'selector.js — recommend a component, or decline to.\n\n' +
  'Usage: node modules/cdicf/selector.js --intent "<text>" --candidates <dir> [options]\n\n' +
  '  --context <file.json>  project context (stack, required_wcag, budgets, concerns)\n' +
  '  --type <t>             require a component_type\n' +
  '  --surface <s>          require a surface\n' +
  '  --json                 machine-readable decision\n\n' +
  'Exit: 0 RECOMMEND, 2 argv, 3 io, 20 ABSTAIN, 21 REQUIRE_APPROVAL.\n' +
  'Non-zero means "not an unattended install", not "the run failed".\n';

function main(argv) {
  const args = argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(USAGE);
    process.exit(args.length ? 0 : 2);
  }
  const flagArg = (flag) => {
    const i = args.indexOf(flag);
    if (i === -1) return null;
    const v = args[i + 1];
    if (!v || v.startsWith('-')) { process.stderr.write(`selector.js: ${flag} requires a value\n`); process.exit(2); }
    return v;
  };

  const intentText = flagArg('--intent');
  const candDir = flagArg('--candidates');
  if (!intentText || !candDir) {
    process.stderr.write('selector.js: --intent and --candidates are required\n');
    process.exit(2);
  }

  let candidates, ctx = {};
  try {
    candidates = loadCandidates(candDir);
    const ctxFile = flagArg('--context');
    if (ctxFile) ctx = JSON.parse(fs.readFileSync(ctxFile, 'utf8'));
  } catch (e) {
    process.stderr.write(`selector.js: ${e.message}\n`);
    process.exit(3);
  }

  const res = select(
    { text: intentText, component_type: flagArg('--type'), surface: flagArg('--surface') },
    candidates, ctx);

  if (args.includes('--json')) {
    process.stdout.write(JSON.stringify(res, null, 2) + '\n');
  } else if (res.decision === 'ABSTAIN') {
    process.stdout.write(
      `ABSTAIN  [${res.abstention.code}]\n` +
      `  reason   ${res.abstention.reason}\n` +
      `  remedy   ${res.abstention.remedy}\n` +
      `  rejected ${res.rejected.length}\n`);
  } else {
    process.stdout.write(
      `${res.decision}  ${res.recommended.id}  (${res.recommended.score})\n` +
      res.ranked.map(r => `  ${r.rank}. ${r.id.padEnd(28)} ${String(r.score).padEnd(8)} ${r.why}\n`).join('') +
      (res.approval_required_because.length
        ? '  approval needed:\n' + res.approval_required_because.map(a => `    - ${a}\n`).join('')
        : '') +
      `  rejected ${res.rejected.length}\n`);
  }

  process.exit(res.decision === 'RECOMMEND' ? 0 : (res.decision === 'ABSTAIN' ? 20 : 21));
}

if (require.main === module) main(process.argv);

module.exports = {
  select, hardFilters, scoreOf, relevanceOf, buildVocabulary, tokens,
  MIN_SCORE, APPROVAL_MARGIN, WEIGHTS, REMEDY_BY_FILTER,
};
