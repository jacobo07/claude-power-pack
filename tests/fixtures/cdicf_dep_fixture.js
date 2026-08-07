/*
 * Builds a REAL installed project for the E5 dependency-scope gate.
 *
 * The gate cannot be tested against a hand-written installed.json without
 * testing a fiction: the whole question is whether the scorer reads what the
 * installer actually wrote. So this emits through the real emitter and installs
 * through the real installer, and the Python suite then asks the scorer about
 * the result.
 *
 * The emitter hardcodes empty dependency arrays today, so the dependency is
 * injected into the entry the way a registry serving real shadcn components
 * would populate it. That injection is the only synthetic step.
 *
 * Usage: node cdicf_dep_fixture.js <targetDir> <depName> [--declare]
 *        --declare writes a package.json in the target declaring <depName>.
 */
'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..', '..');
const { emit } = require(path.join(ROOT, 'modules', 'cdicf', 'registry_emitter'));
const { loadSchema } = require(path.join(ROOT, 'modules', 'cdicf', 'validate_manifest'));
const { install } = require(path.join(ROOT, 'modules', 'cdicf', 'installer'));

const [target, dep] = process.argv.slice(2);
const declare = process.argv.includes('--declare');

const manifest = JSON.parse(fs.readFileSync(
  path.join(ROOT, 'modules', 'cdicf', 'examples', 'shadcn-ui.button.json'), 'utf8'));

const artDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cdicf-depfix-'));
fs.writeFileSync(path.join(artDir, 'button.tsx'),
  'export function Button(p) { return <button {...p} />; }\n');

const res = emit(manifest, { schema: loadSchema(), artifactsDir: artDir });
if (!res.ok) {
  process.stdout.write(JSON.stringify({ ok: false, where: 'emit', refusal: res.refusal }) + '\n');
  process.exit(1);
}

// What a registry that populates dependencies would ship.
const entry = res.entry;
entry.dependencies = [dep];

fs.mkdirSync(target, { recursive: true });
if (declare) {
  fs.writeFileSync(path.join(target, 'package.json'),
    JSON.stringify({ name: 'fixture', dependencies: { [dep]: '^1.0.0' } }, null, 2) + '\n');
}

const out = install(entry, res.install_manifest, target, {});
process.stdout.write(JSON.stringify({
  ok: !!out.ok,
  status: out.status || null,
  refusal: out.refusal || null,
  component: res.install_manifest.component,
}) + '\n');
process.exit(out.ok ? 0 : (out.refusal ? out.refusal.exit : 1));
