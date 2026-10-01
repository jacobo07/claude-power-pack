---
covers: [security-scan, security_scan, gap-4, se-gap-4, d7, sast, sca, semgrep, osv-scanner]
tier: T2
status: SPEC (nothing below is implemented unless marked LIVE)
owner_decisions: 2026-10-01 ("gap 4")
---

# Security scanning of the user's code: SAST + dependency CVEs (Gap 4, v1)

Source: `vault/audits/se-capability-gaps-2026-09-30.md` row 4, backlog D7.

## Problem (verified 2026-10-01)

`secret_firewall` is PP's only security capability. Nothing looks for injectable queries, unsafe
deserialisation, shell injection or other code-level flaws in what the agent writes, and nothing
checks the project's dependencies against known vulnerabilities. On this host semgrep, bandit,
osv-scanner, pip-audit, trivy and grype were all absent (checked 2026-10-01; only `npm` exists).

## Tools (installed for this gap)

| tool | why this one | install |
|---|---|---|
| osv-scanner v2.6.0 | one binary, one database (OSV) for PyPI, npm, Go, Cargo, Maven and more lockfiles, instead of one auditor per ecosystem | official GitHub release, SHA-256 checked against the release's `SHA256SUMS`, `C:\Users\User\Apps\osv-scanner\` |
| semgrep | multi-language SAST, rules fetched from the Semgrep registry at run time (`p/default`), not vendored into the repo | its own venv, `C:\Users\User\Apps\semgrep-venv\`, so its dependency tree never touches the Python every PP tool shares |

## Scope (v1)

`tools/security_scan.py --repo <project> [--base HEAD]`:

| capability | status |
|---|---|
| SAST: semgrep on the changed source files, findings **only on changed lines** (pre-existing findings in untouched lines are not repeated) | PLANNED |
| SCA: osv-scanner over every lockfile in the project; each vulnerable package marked `introduced` when its lockfile changed since `--base` | PLANNED |
| per-scanner outcome `CLEAN` / `FINDINGS` / `UNCHECKED` (+ reason), never merged | PLANNED |
| wired into a blocking done-gate | ABSENT (not v1, see below) |
| SBOM, licence scanning, threat modelling | ABSENT (not v1) |

## Behaviour contract

1. **Read-only.** Scanners read the project in place; neither writes to it. The changed files are
   hashed before and after; a mismatch makes the run `UNMEASURABLE`.
2. **Unchecked is never clean.** A missing binary, a timeout, a network failure fetching rules or
   the vulnerability database, or unparseable scanner output yields `UNCHECKED` for that scanner
   with the reason. A run where every scanner is `UNCHECKED` exits 2.
3. **Changed lines only, for SAST.** A finding is reported when its line range intersects a line
   changed since `--base` (untracked files count as all-changed). The rest are counted as
   `pre_existing`, so silence about them is never mistaken for their absence.
4. **SCA is whole-project.** A vulnerable dependency is a risk wherever it came from; `introduced`
   only says whether this change brought it in.
5. **Bounded.** Each scanner has its own timeout (default 300 s).
6. **Exit codes:** 0 = measured (findings or not), 2 = nothing could be checked or the project
   moved. Findings are information for the agent, not a build break.

## Why not the done-gate in v1

The done-gate (`zero-issue-gate.js`) is a blocking Stop hook. A scan that downloads rules and a
vulnerability database, and takes minutes on a starved host, inside a blocking hook is the shape
that hangs sessions; the gate's newest fix (6f897bf, "never starve the host") exists to stop
exactly that. Gate integration waits until v1 has run on real projects and its cost is measured.

## Wiring

`commands/security-scan.md` (`/security-scan [--base <rev>]`): run the tool, fix or justify each
changed-line SAST finding, and upgrade or justify each `introduced` vulnerable dependency.

## Acceptance

`python tools/test_security_scan.py` exit 0 (V-SEC-* gates) on a fixture git project:

- a changed line with a known-bad pattern (e.g. `subprocess` with `shell=True` on input,
  `yaml.load` without a safe loader) is reported, with rule id and line;
- the same pattern on an **unchanged** line is not reported but is counted `pre_existing`;
- a clean changed file reports no SAST finding (control);
- a lockfile pinning a package version with a published OSV advisory is reported, `introduced`
  when that lockfile is part of the change; a lockfile with a patched version reports nothing;
- a missing scanner binary gives `UNCHECKED` with a reason, never `CLEAN`;
- the project's files are byte-identical after the run.

Mutation drill: with the changed-line filter removed, `UNCHECKED` collapsed into `CLEAN`, or the
`introduced` mark inverted, the suite goes red.

## Evidence (2026-10-01)

- Installs: osv-scanner v2.6.0, SHA-256 `e0ed7644...` equal to the release's `SHA256SUMS`;
  semgrep 1.178.0 in `Apps\semgrep-venv` (runs natively on Windows; `p/default` scan of one file
  27 s, metrics off).
- Probes: osv-scanner exit 1 + 4 advisories on PyYAML 5.3, exit 0 on 6.0.2; it lists one
  requirement twice (`5.3` and `5.3.0`), hence the dedup.
- `python tools/test_security_scan.py`: 12/12 (452 s, network) - changed-line SAST, pre_existing
  count, introduced vs existing, dedup, clean and patched controls, UNCHECKED for each missing
  binary, exit 2 when nothing could run, project untouched.
- Mutation drill on isolated copies: **1 of 4 run, KILLED** (changed-line filter removed ->
  V-SEC-SAST-CHANGED-LINE red, 9/12). The other three (binary-not-found read as CLEAN,
  `introduced` inverted, dedup removed) were **not run**: Claude Code stopped the drill for host
  memory pressure. Rows below stay PLANNED until they are.
- Real-project scan: not yet run.

## Rollback

Delete the tool, its test and the command file; remove `Apps\osv-scanner` and
`Apps\semgrep-venv`. No state is persisted.
