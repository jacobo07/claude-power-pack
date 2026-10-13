#!/usr/bin/env node
/**
 * Gate for creative_grounding.js (UserPromptSubmit, advisory, fail-open).
 *
 * Drives both branches, against a temporary FTS5 index built here (so it does not depend on the live AKOS store):
 *   fires   - a creative prompt (ES and EN) injects hits whose ids exist in the index
 *   silent  - a non-creative prompt, a prompt about the hook itself, a missing index, a corrupt index,
 *             and AKOS_GROUNDING=0 all emit nothing and exit 0
 * A hook that never fires and a hook that always fires both fail here.
 *
 * Run: node test-creative-grounding.js
 */
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const HOOK = path.join(__dirname, '..', 'creative_grounding.js');
const LEX_SRC = 'C:/Users/User/Desktop/Cursor Projects/AKOS/akos/retrieval/lexicon.json';
let pass = 0;
let fail = 0;

function ok(name, cond, detail) {
  if (cond) { pass += 1; console.log('  PASS ' + name); } else { fail += 1; console.log('  FAIL ' + name + (detail ? ' :: ' + detail : '')); }
}

// Arrange: a fake AKOS root with the real lexicon and a tiny index of the real schema
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'cg-'));
fs.mkdirSync(path.join(root, 'akos', 'retrieval'), { recursive: true });
fs.mkdirSync(path.join(root, 'datasets', 'indexes'), { recursive: true });
fs.copyFileSync(LEX_SRC, path.join(root, 'akos', 'retrieval', 'lexicon.json'));
const idx = path.join(root, 'datasets', 'indexes', 'akos_search.sqlite');
const db = new DatabaseSync(idx);
db.exec(`CREATE VIRTUAL TABLE chunks USING fts5(sid UNINDEXED, source UNINDEXED, type UNINDEXED, tier UNINDEXED,
  confidence UNINDEXED, origin, content, tokenize = "unicode61 remove_diacritics 2");`);
const ins = db.prepare('INSERT INTO chunks VALUES (?,?,?,?,?,?,?)');
ins.run('akos:u-native', 'akos', 'strategy', 1, 0.9, 'native-image-ads.txt', 'Native image ads for apparel brands: show the knit garment on a textured surface.');
ins.run('01ds:copy/hooks.md#0', '01ds', 'dataset', 2, 0.5, 'copy/hooks.md', 'Un gancho de anuncio para moda de mujer en Meta.');
ins.run('akos:u-mc', 'akos', 'strategy', 3, 0.3, 'mc.txt', 'Minecraft server plugin configuration.');
db.close();
const SIDS = new Set(['akos:u-native', '01ds:copy/hooks.md#0', 'akos:u-mc']);

function run(prompt, env) {
  const r = spawnSync(process.execPath, [HOOK], {
    // generous: on a saturated host a bare `node -e 0` spawn measured 6.8 s; a timeout must not read as a verdict
    input: JSON.stringify({ prompt }), encoding: 'utf8', timeout: 90000,
    env: Object.assign({}, process.env, { AKOS_ROOT: root, AKOS_INDEX: idx, AKOS_GROUNDING: '' }, env || {}),
  });
  let ctx = '';
  if (r.stdout) { try { ctx = JSON.parse(r.stdout).hookSpecificOutput.additionalContext; } catch (_e) { ctx = '<<unparseable>>'; } }
  if (r.status === null) { console.log('  NOTE spawn timed out (host load), signal=' + r.signal); }
  return { code: r.status, ctx };
}

console.log('creative_grounding');
let r = run('Haz el anuncio del cárdigan de punto para Meta y escribe el copy');
const cited = (r.ctx.match(/(akos|01ds):\S+/g) || []);
ok('ES creative prompt fires with ids', r.code === 0 && cited.length >= 2, r.ctx.slice(0, 200));
ok('every injected id exists in the index', cited.length > 0 && cited.every((s) => SIDS.has(s)), cited.join(','));
ok('relevant unit ranks first', cited[0] === 'akos:u-native' || cited[0] === '01ds:copy/hooks.md#0', cited[0]);
ok('injection tells the model to cite and to write a pack', /Cite the ids/.test(r.ctx) && /evidence --task/.test(r.ctx));

r = run('write ad copy for a knit cardigan, three headlines');
ok('EN creative prompt fires', r.code === 0 && /akos:u-native/.test(r.ctx));

r = run('arregla el test de phase_status que falla con StopIteration');
ok('non-creative prompt is silent', r.code === 0 && r.ctx === '');

r = run('el hook del power pack dispatcher tarda 3 s, mira la cadena');
ok('prompt about hooks/pipeline is silent', r.code === 0 && r.ctx === '');

r = run('Haz el anuncio del cárdigan', { AKOS_GROUNDING: '0' });
ok('kill switch AKOS_GROUNDING=0 is silent', r.code === 0 && r.ctx === '');

r = run('Haz el anuncio del cárdigan', { AKOS_INDEX: path.join(root, 'missing.sqlite') });
ok('missing index is silent and exits 0', r.code === 0 && r.ctx === '');

const bad = path.join(root, 'corrupt.sqlite');
fs.writeFileSync(bad, 'not a database');
r = run('Haz el anuncio del cárdigan', { AKOS_INDEX: bad });
ok('corrupt index is silent and exits 0 (fail-open)', r.code === 0 && r.ctx === '');

// The hook's own cost (lexicon + index open + query), measured in-process. Process spawn time is host load,
// which the dispatcher deadline bounds for every member alike; this checks only what the hook adds.
process.env.AKOS_ROOT = root;
process.env.AKOS_INDEX = idx;
delete require.cache[require.resolve(HOOK)];
const mod = require(HOOK);
const t = Date.now();
const hits = mod.search('Haz el anuncio del cárdigan de punto para Meta');
ok('in-process search costs under the 3000 ms chain deadline with margin', hits.length > 0 && Date.now() - t < 2500,
  (Date.now() - t) + ' ms');

// The dispatcher runs this hook IN-PROCESS through run(): pin that contract and the registration.
const out = mod.run({ prompt: 'Haz el anuncio del cárdigan de punto para Meta' });
ok('run() returns the injection object in-process', !!(out && /akos:u-native|01ds:copy/.test(out.hookSpecificOutput.additionalContext)));
ok('run() is silent on a non-creative prompt', mod.run({ prompt: 'arregla el test de phase_status' }) === null);
ok('run() never throws on garbage input', mod.run(null) === null && mod.run({ prompt: 42 }) === null);
const disp = fs.readFileSync(path.join(require('os').homedir(), '.claude', 'hooks', 'hook-dispatcher.js'), 'utf8');
const bundle = (disp.match(/'UserPromptSubmit-default':\s*\[([\s\S]*?)\]/) || [])[1] || '';
ok('registered in the in-process UserPromptSubmit-default bundle', /creative_grounding\.js/.test(bundle));
const chain = (disp.match(/'UserPromptSubmit-chain':\s*\[([\s\S]*?)\n  \],/) || [])[1] || '';
ok('NOT also a spawned chain member (would run twice)', !/script:\s*'[^']*creative_grounding\.js'/.test(chain));

fs.rmSync(root, { recursive: true, force: true });
console.log(`CREATIVE_GROUNDING_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
