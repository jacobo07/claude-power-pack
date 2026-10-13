# CCR v4 Stage 3 -- A1 evidence (version truth + A4 patch)

All numbers below are from the Linux plane GEX44, host 2.1.296 (`~/.local/bin/claude`), 2026-10-13. None comes from a laptop projection.

## 1. A4 patch
`git apply -v vault/programs/ccr/stage3/a4/ccr-mod-a4.patch`: applied cleanly to policy.ts, register.ts and policy.test.ts. No hand resolution was needed.

## 2. Estate gate (`python3 tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime`)
| state | verdict | sum 1x | sum 10x | bound | policy.ts sha256 |
|---|---|---:|---:|---:|---|
| before patch | FAIL (exit 1) | 6,452 | 35,927 | 8,000 | cd640ac46f8d |
| after patch | PASS (exit 0) | 6,452 | 3,646 | 8,000 | 74895721fcb5 |
| after A1 edits (final) | PASS (exit 0) | 6,452 | 3,646 | 8,000 | 5a7ddbd6a51c |

The kernel is 2,970 bytes. The inputs are 25 files and 160,848 bytes at 1x, and 250 files and 1,608,480 bytes at 10x.

## 3. Tests
- `claude plugin test mods/cpp-cognitive-runtime`: 30 pass, 0 fail after the patch. After A1 the result is **33 pass, 0 fail**, adding three new "version truth" tests: effective modes per surface, a policyGen golden value `acce69838866` computed outside the runtime, and the RELEASE.json parse.
- `claude plugin validate mods/cpp-cognitive-runtime`: **Validation passed**.
- `python3 tools/test_ccr_release.py`: **CCR_PASS=20/20**. The new gates are V-CCR-RELEASE-ID, V-CCR-ROLLBACK-ID, V-CCR-SESSIONS-STATES (CURRENT/STALE/DEV/UNKNOWN, with Linux and Windows path shapes), V-CCR-SESSIONS-NEWEST-START, V-CCR-SESSIONS-STALE-FLAG, V-CCR-SESSIONS-NO-ACTIVE and V-CCR-ALIVE-REAL.
- Not executed here: the Windows branch of `_alive` (ctypes OpenProcess/GetExitCodeProcess). The Linux run tests only Windows path *shapes*. The laptop's `status --sessions` in LAPTOP_APPLY is the first execution of that branch.
- Note: `/usr/local/bin/claude` on this host is 2.1.113, and it has no `plugin test` command and fails `validate`. Every result above comes from `~/.local/bin/claude` 2.1.296.

## 4. Start receipt from a fresh session
Probe command: `claude -p --model haiku --plugin-dir mods/cpp-cognitive-runtime --output-format json "ok"`. It was the single allowed probe. Session 59fd86cb, rc 0, haiku processed 14,600 tokens (2 in, 14,449 cache-create, 149 out). Free RAM was 55 GB available.

```
{"ts":1791924836217,"sid":"59fd86cb-2d58-4e90-aeea-e8bb994b5d2e","ev":"start","runtime":"0.1.0","version":"2.1.296","compatible":true,"modes":{"subagent":"enforce","main":"shadow","unit":"enforce"},"repoKey":"667e1ff2","interactive":false,"kernel":2970,"unit":"bounded-code-worker","release":"/home/kobii/missions/ccr-s3/mods/cpp-cognitive-runtime","releaseId":null,"policyGen":"f1524a35dc36","effective":{"main":"shadow","subagent":"enforce","unit":"enforce","project":"enforce"},"workClass":"bounded-code-worker"}
```
`releaseId` is null because this was a dev load: the mod directory has no RELEASE.json, and only `ccr_release.py build` writes one. The probe inherited `CCR_WORK_UNIT` from the launching session, so the unit class is bounded-code-worker.

## 5. `python3 tools/ccr_release.py status --sessions --receipts mods/cpp-cognitive-runtime/.state-dev/receipts` (GEX44)
```
{
  "active": null,
  "sessions": [
    {
      "pid": 1100480,
      "sid": "9dde3bfe-a3e3-4307-8de8-4139f80da267",
      "cwd": "/home/kobii/missions/ccr-s3",
      "host": "2.1.296",
      "kind": "interactive",
      "loaded": null,
      "release": null,
      "policyGen": null,
      "state": "UNKNOWN",
      "stale": false
    },
    {
      "pid": 2843330,
      "sid": "6ef58b0f-b63c-4a82-b053-fa43fa0d756c",
      "cwd": "/home/kobii/missions/incremental-cognition",
      "host": "2.1.288",
      "kind": "bg",
      "loaded": null,
      "release": null,
      "policyGen": null,
      "state": "UNKNOWN",
      "stale": false
    },
    {
      "pid": 4168684,
      "sid": "6da60f5a-cd68-46a3-a6a1-f324414099c8",
      "cwd": "/home/kobii/missions/cognitive-economy-e1",
      "host": "2.1.289",
      "kind": "bg",
      "loaded": null,
      "release": null,
      "policyGen": null,
      "state": "UNKNOWN",
      "stale": false
    }
  ],
  "counts": {
    "CURRENT": 0,
    "STALE": 0,
    "DEV": 0,
    "UNKNOWN": 3
  }
}
```
GEX44 has no `~/.claude/ccr` release root, so `active` is null. The three live sessions loaded the CCR snapshot or none, and they have no A1 start receipt in the dirs read, so all three are UNKNOWN. None was inferred.
