# CCR Stage 3 GEX44 driver (drive3.sh, v3)

`drive3.sh` is the driver that ran units A6, A7 and X2 on GEX44. It is a byte-exact copy of
`kobii@gex44:/home/kobii/missions/ccr-s3-data/drive3.sh` (ssh alias `gex44`). `MANIFEST.json` records the
host path, byte count, sha256 (local and remote), and the fetch time. The driver bytes are NOT edited
here: v3 is proven, not re-fixed.

## How it was fetched

Read-only: `ssh gex44 cat <path>` with the redirect done by `cmd` (not by PowerShell, which re-encodes),
then `ssh gex44 sha256sum <path>`. The local sha256 must equal the remote one; `MANIFEST.json` stores both.

## Why it is LF-pinned

This clone runs `core.autocrlf=true`. A checked-out `.sh` would come back with CRLF and bash would answer
`$'\r': command not found`. The `.gitattributes` in this directory pins `drive3.sh` to `text eol=lf`;
the test asserts zero CR bytes.

## How to refresh

1. Fetch again (same two commands), compute the sha256 locally.
2. Replace `drive3.sh` and update every `MANIFEST.json` field (bytes, sha256, remote_sha256, fetched_at, note).
3. Run `python -I tools/test_ccr_driver_breaker.py`; it must print `DRV_PASS=14/14`.

If the host copy changed after the proof, the manifest hash no longer matches the host: re-fetch before relying on it.

## What the test covers

`tools/test_ccr_driver_breaker.py` reads the driver as text, extracts `spent()` and `over()` only, and
sources just those into real bash (never the driver's top level). It proves the measurement fails closed:
a string-valued `message` line is measured, an empty or `ERR` measurement trips `over()`, a crashed
measurement or a failed interpreter becomes `ERR`, numeric controls (below the stop, at the stop) behave,
and three broken variants (no ERR clause, no empty clause, the A4 failure shape) make the same predicates fail.

## What the test does NOT cover

- The `pkill`/`kill` path that acts on a tripped breaker.
- The RAM hold (`MemAvailable` check) and the phase cap arithmetic.
- A live run of the driver on the host.
- Open residual (recorded, not patched): a unit whose stream file is missing or misnamed measures `0`,
  not `ERR`, so it is never over the stop. Carried to Phase 11 knowledge.
