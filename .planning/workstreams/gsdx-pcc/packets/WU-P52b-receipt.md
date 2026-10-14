# WU-P52b receipt (mission m-53847a002b65)
Status: DONE
Packet sha256 fe9624849e48 (residual); branch gsdx/pcc; worktree C:\Users\User\Apps\pp-gsdx-pcc; plane Windows laptop

Commits: d23e7f44 (05-2-02, 31/31); RED 05-2-03 suite (1/14) then the 05-2-03 implementation + SUMMARY commit (see `git log`).
Gate lines (verbatim, Windows laptop): GSDX_TRUST_ENV_PASS=14/14  threshold=14/14; GSDX_TRUST_FORGERY_PASS=31/31  threshold=31/31; GSDX_TRUST_PASS=7/7  threshold=7/7; GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11; GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48; GSDX_INVALIDATION_PASS=26/26  threshold=26/26; GSDX_CERTIFICATE_PASS=7/7  threshold=7/7; liveness exit 0.
DENOMINATOR rows moved: N16 (forgery), N17 (canonical env: versions, lock, runtime, bare name unknown), N19 (plane stamped on every certificate; PORTABILITY only from >=2 planes on one clean tree).
NOT run: Linux/GEX44 leg (coordinator: `tools/gsdx_env_equiv.py --vector|--live|--compare`); `tool:` resolver has no gate (spawns `<tool> --version`).
Deviation: drift gate drifts the runtime resolver through the real inherit.plan (see 05-2-03-SUMMARY).
Open points: none needing the Owner.
HANDOFF NOTE: WU-P52b done -- next WU-P52c.
