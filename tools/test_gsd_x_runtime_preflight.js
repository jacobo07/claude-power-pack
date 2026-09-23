#!/usr/bin/env node
/**
 * test_gsd_x_runtime_preflight.js -- drives BOTH poles of the runtime preflight,
 * plus the branch that says "I could not measure this".
 *
 * WHY EACH CASE EXISTS, since a list of green ticks explains nothing:
 *
 *  - A gate that refuses everything satisfies every refusal assertion and is
 *    indistinguishable from one that works. So the UNMET case is paired with a
 *    SATISFIED case built from a program that demonstrably runs on this host.
 *  - Instrument failure and subject failure must not share an answer. Pointing
 *    the probe at a gsd-core that is not there must produce UNMEASURABLE, never
 *    UNMET -- otherwise a broken harness reads as a verdict about the host.
 *  - Absence is not satisfaction. A manifest that declares no requirements has
 *    not passed; it was never asked, and saying SATISFIED there would hand every
 *    undeclared capability a clean bill.
 *  - UNMEASURABLE must OUTRANK UNMET in the aggregate, because a run that could
 *    not measure proves nothing about the entries it never reached.
 *  - Execution is authoritative and resolution is diagnostic. The two genuinely
 *    disagree (an absolute path does not resolve through a PATH scan yet spawns
 *    perfectly), and deciding on resolution would report a working host broken.
 *
 * Fixtures are synthetic and built in a temp dir: a fixture that copies the real
 * manifest would inherit its debt, so the GREEN pole would go red for reasons
 * that have nothing to do with the clause under test.
 *
 * Read-only with respect to the repo. Exit 0 all pass, 1 any fail, 2 harness.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const SUBJECT = path.join(__dirname, 'gsd_x_runtime_preflight.js');
const REAL_MANIFEST = path.join(
  __dirname, '..', 'capabilities', 'cpp-gsd-x-mission', 'capability.json'
);
const GSD_LIB = 'C:/Users/User/.claude/gsd-core/bin/lib';

let pass = 0;
let fail = 0;
const skipped = [];
const ok = (gate, evidence) => { pass++; console.log(`ok   ${gate}  ${evidence}`); };
const no = (gate, why) => { fail++; console.log(`FAIL ${gate}  ${why}`); };
// A case whose FIXTURE cannot be built on this host is not a pass. It is counted
// separately and printed, so a run that quietly measured less than it claims is
// visible in the summary line rather than hidden inside a green total.
const skip = (gate, why) => { skipped.push(gate); console.log(`skip ${gate}  ${why}`); };

// Preconditions are HARNESS failures, never findings about the subject.
for (const p of [SUBJECT, REAL_MANIFEST]) {
  if (!fs.existsSync(p)) {
    console.log(`HARNESS-FAILED: required input missing: ${p}`);
    process.exit(2);
  }
}

const PF = require(SUBJECT);

// Per-PID temp dir: this host runs dozens of concurrent sessions, and a shared
// fixture path produces an unattributable failure in exactly one of them.
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), `gsdxpf-${process.pid}-`));
const writeManifest = (name, obj) => {
  const p = path.join(TMP, name);
  fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8');
  return p;
};

try {
  // -- V-GSDXPF-RED-REAL-HOST ------------------------------------------------
  // Today's truth, through the real manifest and the real surface.
  {
    const out = PF.run({ manifest: REAL_MANIFEST, gsdLib: GSD_LIB });
    const shell = out.results.find((r) => r.id === 'posix-shell');
    if (out.verdict === PF.UNMET && shell && shell.state === PF.UNMET) {
      ok('V-GSDXPF-RED-REAL-HOST',
        `UNMET, and it names posix-shell (exit would be ${PF.EXIT[out.verdict]})`);
    } else {
      no('V-GSDXPF-RED-REAL-HOST',
        `expected UNMET naming posix-shell; got ${out.verdict} / ${JSON.stringify(shell)}`);
    }
  }

  // -- V-GSDXPF-GREEN-CONTROL ------------------------------------------------
  // The positive control. `process.execPath` is a program that certainly runs
  // here -- it is running this test. If SATISFIED is unreachable, the detector
  // is worthless and every refusal above is meaningless.
  {
    const m = writeManifest('green.json', {
      id: 'synthetic-green',
      runtimeRequirements: {
        onUnmet: 'refuse-activation',
        requirements: [
          { id: 'this-node', kind: 'executable', name: process.execPath, probeArgs: ['--version'] },
        ],
      },
    });
    const out = PF.run({ manifest: m, gsdLib: GSD_LIB });
    if (out.verdict === PF.SATISFIED) {
      ok('V-GSDXPF-GREEN-CONTROL', 'a runnable program yields SATISFIED -- refusal is not universal');
    } else {
      no('V-GSDXPF-GREEN-CONTROL',
        `SATISFIED unreachable; detector refuses everything. got ${JSON.stringify(out)}`);
    }
  }

  // -- V-GSDXPF-EXECUTION-IS-AUTHORITATIVE -----------------------------------
  // B decides, A only informs -- driven through the INJECTED surface, because on
  // win32 the two answers cannot be made to disagree with a real fixture.
  //
  // Two earlier versions of this case chased a real "present but unresolvable"
  // program and both failed honestly, each refuting a premise of mine:
  //   1. `process.execPath` -- node.exe carries a PATHEXT extension and its dir
  //      IS on PATH, so it resolved.
  //   2. Git's `sh.exe` by absolute path -- resolveExecutableBinary tries a name
  //      that already carries a PATHEXT-listed extension AS-IS first, so any
  //      absolute path to an existing .exe resolves whatever PATH holds.
  // On win32 execTool hands the declared name to spawnSync and libuv runs the
  // same PATH+PATHEXT search the resolver does, so the disagreement is
  // structurally unreachable here; it is a POSIX behaviour (documented at
  // shell-command-projection.cjs:725-728, where execTool does NOT consult the
  // resolver at all). Hunting for it on this host was testing a world that
  // cannot occur. The decision RULE is what matters and it is injectable, so
  // drive it directly -- and drive both directions, or "always SATISFIED" and
  // "always UNMET" would each pass a single-direction assertion.
  {
    const satisfiedDespiteNullResolve = PF.probeRequirement(
      { id: 'posix-shaped', kind: 'executable', name: 'anything', probeArgs: [] },
      {
        resolveExecutableBinary: () => null,
        execTool: () => ({ exitCode: 0, stdout: '', stderr: '', error: null }),
      }
    );
    const unmetDespiteGoodResolve = PF.probeRequirement(
      { id: 'resolved-but-dead', kind: 'executable', name: 'anything', probeArgs: [] },
      {
        resolveExecutableBinary: () => 'C:/somewhere/anything.exe',
        execTool: () => ({ exitCode: 127, stdout: '', stderr: 'anything: not found', error: { code: 'ENOENT' } }),
      }
    );

    if (satisfiedDespiteNullResolve.state === PF.SATISFIED
        && unmetDespiteGoodResolve.state === PF.UNMET) {
      ok('V-GSDXPF-EXECUTION-IS-AUTHORITATIVE',
        'resolved=null + exit 0 -> SATISFIED, and resolved=path + ENOENT -> UNMET; the probe decides');
    } else {
      no('V-GSDXPF-EXECUTION-IS-AUTHORITATIVE',
        `the verdict is following resolution, not execution: `
        + `${satisfiedDespiteNullResolve.state} / ${unmetDespiteGoodResolve.state}`);
    }
  }

  // -- V-GSDXPF-UNMEASURABLE-BAD-INSTRUMENT ----------------------------------
  // The instrument, not the host. Must NOT be UNMET.
  {
    const out = PF.run({
      manifest: REAL_MANIFEST,
      gsdLib: path.join(TMP, 'no-such-gsd-lib'),
    });
    if (out.verdict === PF.UNMEASURABLE && PF.EXIT[out.verdict] === 2) {
      ok('V-GSDXPF-UNMEASURABLE-BAD-INSTRUMENT',
        'missing gsd-core -> UNMEASURABLE exit 2, not a verdict about the host');
    } else {
      no('V-GSDXPF-UNMEASURABLE-BAD-INSTRUMENT',
        `instrument failure reported as a finding: ${out.verdict} (${out.why})`);
    }
  }

  // -- V-GSDXPF-ABSENCE-IS-NOT-SATISFACTION ----------------------------------
  {
    const m = writeManifest('undeclared.json', { id: 'synthetic-undeclared' });
    const out = PF.run({ manifest: m, gsdLib: GSD_LIB });
    if (out.verdict === PF.UNMEASURABLE) {
      ok('V-GSDXPF-ABSENCE-IS-NOT-SATISFACTION',
        'no runtimeRequirements -> UNMEASURABLE, never a clean bill');
    } else {
      no('V-GSDXPF-ABSENCE-IS-NOT-SATISFACTION',
        `an undeclared manifest passed as ${out.verdict}`);
    }
  }

  // -- V-GSDXPF-UNMEASURABLE-OUTRANKS-UNMET ----------------------------------
  {
    const m = writeManifest('mixed.json', {
      id: 'synthetic-mixed',
      runtimeRequirements: {
        requirements: [
          { id: 'missing-file', kind: 'file', path: path.join(TMP, 'definitely-absent') },
          { id: 'weird', kind: 'quantum-flux' },
        ],
      },
    });
    const out = PF.run({ manifest: m, gsdLib: GSD_LIB });
    const unmet = out.results.find((r) => r.id === 'missing-file');
    const weird = out.results.find((r) => r.id === 'weird');
    if (out.verdict === PF.UNMEASURABLE
        && unmet && unmet.state === PF.UNMET
        && weird && weird.state === PF.UNMEASURABLE) {
      ok('V-GSDXPF-UNMEASURABLE-OUTRANKS-UNMET',
        'aggregate UNMEASURABLE while the per-item UNMET is still reported');
    } else {
      no('V-GSDXPF-UNMEASURABLE-OUTRANKS-UNMET',
        `expected UNMEASURABLE aggregate; got ${out.verdict} / ${JSON.stringify(out.results)}`);
    }
  }

  // -- V-GSDXPF-ISOLATION ----------------------------------------------------
  // One malformed entry must not stop the others being judged, or a single bad
  // shape silently leaves the rest unmeasured behind a confident-looking verdict.
  {
    const m = writeManifest('isolation.json', {
      id: 'synthetic-isolation',
      runtimeRequirements: {
        requirements: [
          { id: 'broken', kind: 'executable' },
          { id: 'good', kind: 'executable', name: process.execPath, probeArgs: ['--version'] },
        ],
      },
    });
    const out = PF.run({ manifest: m, gsdLib: GSD_LIB });
    const good = out.results.find((r) => r.id === 'good');
    if (out.results.length === 2 && good && good.state === PF.SATISFIED) {
      ok('V-GSDXPF-ISOLATION', 'a malformed entry did not prevent the next one being judged');
    } else {
      no('V-GSDXPF-ISOLATION', `isolation broken: ${JSON.stringify(out.results)}`);
    }
  }
} finally {
  try { fs.rmSync(TMP, { recursive: true, force: true }); } catch (e) { /* temp dir */ }
}

console.log(
  `GSDXPF_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`
  + (skipped.length ? `  SKIPPED=${skipped.length} [${skipped.join(', ')}]` : '')
);
process.exit(fail === 0 ? 0 : 1);
