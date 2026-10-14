# 05-2-03 SUMMARY -- canonical environment (N17, audit A4) and platform vs portability (N19)

Plane for every gate below: `Windows laptop` (CPython 3.12.10). The Linux leg (GEX44) is the coordinator's: run
`python tools/gsdx_env_equiv.py --vector` and `--live` there and `--compare` with the laptop's JSON. NOT RUN on Linux.

## Delivered
- `trust.canonical_env_body` / `trust.environment_canonical`: `env2:` hash over runtime (impl + full version), platform and each
  declared dependency resolved to what is installed (`pkg:` version, `tool:` `--version`, `lock:` file sha256, `runtime:python`).
  A bare name or an unresolvable dependency yields an `unknown:` fingerprint, so the premise is unknown and never inherits.
- Both production callers (`inherit.observe_current`, `proof.certificate_payload`) go through it. `proof.environment_fingerprint`
  stays (legacy, no production caller); an `env1:` certificate meets `env2:` as `changed`, i.e. STALE once (V-TRUST-ENV-MIGRATION-ONCE).
- N19: `trust.stamp` gives every certificate `plane {claim: PLATFORM, planes:[id], modules_tree}`; `trust.portability_plane` builds a
  PORTABILITY stamp only from >= 2 planes with identical clean trees, else None. `plane_ok` (05-2-02) refuses a relabelled stamp.
- `tools/gsdx_env_equiv.py` (`--vector`, `--live`, `--compare`).

## Gates (verbatim)
- RED: `GSDX_TRUST_ENV_PASS=1/14` (logs/05-2-03-red.log, commit before the code).
- `GSDX_TRUST_ENV_PASS=14/14  threshold=14/14`
- `GSDX_TRUST_FORGERY_PASS=31/31  threshold=31/31`; `GSDX_TRUST_PASS=7/7  threshold=7/7`; `GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11`
- `GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48`; `GSDX_INVALIDATION_PASS=26/26  threshold=26/26`; `GSDX_CERTIFICATE_PASS=7/7  threshold=7/7`
- `python modules/liveness/reachability.py` exit 0.

## Deviations
- The drift gate (V-TRUST-ENV-DRIFT-INVALIDATES) drifts the runtime resolver through the real `inherit.plan`, not a `pkg:` dependency:
  the fixture contract declares no env_deps and a later contract may only strengthen. `pkg:` version sensitivity is pinned directly
  by V-TRUST-ENV-VERSIONS-COUNT. The resolver is the only mocked boundary.
- `tool:` resolution spawns `<tool> --version` (10 s bound); not exercised by a gate (no stable tool on every plane). Open point, not Owner-facing.
