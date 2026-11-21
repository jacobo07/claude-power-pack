# CPP-RUFLO-001 ledger (BCAP-2 Phase 9) -- PARTIALLY_PROVEN

Pin: ruvnet/ruflo tag v3.78.0 = 337c8981e6196f74ea72abc990f0b76a686764d0 (MIT), fetched 2026-11-19 read-only (shallow fetch, source copy at
`/home/kobii/ruflo-sandbox-bcap2/src`, outside the repo). npm `ruflo@3.78.0` integrity `sha512-XcXKdpSPM7fLWL8rlhMAQVusBrYhsdvh4AjyO70tChPUunENUuYkgRlFeWQ39txucoKwSghm9aD072u0gxxKhw==`.

## Order followed (backlog + plan law 6)
(a) passive review -> (b) CPP-owned correction per HOLD, RED->GREEN -> (c) inert sandbox install + smoke -> (d) laptop step.
Gate: `python3 tools/test_bcap2_ruflo.py` (attack refused AND benign accepted for 27 cases, a permissive-mutant drill proving every case can
fail, real upstream manifest scan, ledger-to-gate binding). Controls: `modules/ruflo_gate/gate.py`. HOLD register: `HOLDS.json` (19 holds:
17 CPP_CORRECTED, 2 RESIDUAL).

## Observed at the pinned source (grep/read level, nothing executed)
- Upstream source ALREADY carries an allowlist for browser_open flags/URL schemes and path-containment tests; this is a source fix, not evidence
  that the published bytes or the live path carry it, and the CPP gateway does not depend on it.
- `@claude-flow/browser/package.json` postinstall runs `npm install -g agent-browser@<v>` (global install on any consumer install): the gate flags
  this real manifest. `@claude-flow/cli` has `scripts/postinstall.cjs` (153 lines; only write seen is to a package.json).
- `transfer-store.ts` (pattern marketplace, IPFS) has no digest/signature check at this commit (grep-level) -> #4750 stands; CPP pins by sha256.
- Installed tree under the sandbox: 0 risky lifecycle scripts among installed manifests (browser package is not in the ruflo dependency tree).

## Sandbox install (law 6) -- `install_sandbox.py 3.78.0 <dir>`
exact pin + registry integrity checked by `gate.install_plan_error` before npm ran; `--ignore-scripts`; scrubbed env (no secrets, HOME/XDG into the
sandbox, CLAUDE_CONFIG_DIR pointed at nothing); lockfile integrity re-checked == registry; smoke `ruflo --version` -> `ruflo v3.78.0` with a
network-blocking preload; nothing started; no process left; nothing written under the real ~/.claude (checked by find -newer).
Sandbox: `/home/kobii/ruflo-sandbox-bcap2/run` (1.2 GB, disposable, `rm -rf` to undo).

## Decision (recorded, internal, reversible)
Two holds cannot be CORRECTED by CPP (no npm provenance attestation; maintainer's "fixed in 3.71.4/3.72.0" claim unverified). Law 6 says an
uncorrectable hold keeps the install refused. I read that as refusing any install that is active or trusted: what was done is an INERT,
hash-pinned, script-disabled sandbox copy for study; nothing is wired, enabled or trusted. Activation stays refused (READY_FOR_SANDBOX only,
not READY_FOR_CANARY) until a laptop/isolated run drives the upstream advisory fixtures.

## Eight gaps -> existing CPP owners (mapping by name; not each verified executable here)
1 verification oracle -> TDD owners (test-gaps/mutation/done_gate, Phase 3) | 2 task-level A/B eval -> done_gate + CRAIF/OSR (DBG, Phase 1)
3 review-queue/batch control -> modules/backlog_autopilot ledger | 4 deploy safety -> HR-CASCADE/DEPLOY rules (existing) | 5 intent escalation
-> autonomy_gate (existing) | 6 file-ownership partition -> concurrent-writers doctrine (existing) | 7 supply-chain defense -> this gate +
dependency_sovereignty | 8 token budget -> TCO/gsd_mission budget (existing). None rebuilt.

## RESIDUALS
- no npm provenance attestation (CONFIRMED by measurement, CANARY_2026-11-20.json). `dist/` identity (campaign B, 2026-11-21, `dist_identity.py`, `DIST_IDENTITY_2026-11-21.json`): every one of 525 source .ts has a dist .js; shipped bin/ and assets/ byte-identical to source; BUT the source checkout (337c8981, grafted) and the 3.78.0 tarball DIVERGE (package.json pins @claude-flow/mcp 3.1.6 vs 3.1.8, @claude-flow/security 3.0.7 vs 3.0.8; plugins/ dist-only files). dist bytes stay UNPROVEN: rebuilding would run upstream build scripts.
- advisory fixes unverified at runtime (needs executing upstream with attack fixtures: laptop/isolated plane).
- network egress during smoke blocked only by an in-process preload (bwrap/unshare netns refused on this host); install itself needed the registry.
- fresh `npm audit` MEASURED 2026-11-20: 0 vulnerabilities (CANARY json, lockfile sha acff5e4b...), 586/586 signatures verified;  #3294 remains open upstream (CPP wraps, does not fix their code).
- 5 of the 8 GHSA classes (SSRF, loopback bridge, XFF, federation envelope, memory origin) are generic controls proven on fixtures, not yet bound
  to a running Ruflo MCP transport (nothing is running).
