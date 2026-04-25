# Anti-Fragility Hack Ledger (AFHL) — schema

**File:** `vault/anti_fragility/hacks.jsonl` (per project, opt-in)
**Consumer:** `tools/forensic_probes.py afhl_check()`
**Goal:** every "non-canonical stabilizer" (NMS reflection, native shim, monkey-patch, regex-of-rescue, Kamek slot, JVM agent) is registered with its upstream-bug context, so a delta touching it triggers re-validation.

## Why this exists

Hacks rot silently. A reflection accessor that worked against Paper 1.20 may compile-clean against 1.21 yet hit a renamed field at runtime. A regex parser written to dodge a quirk in upstream library v1.4 may over-match when v1.5 fixes the quirk. Static analysis sees "the hack code didn't change" and grades A. AFHL flips it: when the upstream changes, the hack must be re-validated even if its source is byte-identical.

## File format — JSONL, append-only (versioned)

```json
{"hack_id":"paper-nms-pose-accessor","added":"2026-03-15","file":"src/main/java/com/kobii/util/NMSPose.java","upstream":"papermc/Paper","upstream_version_range":"[1.21.0, 1.21.4)","upstream_bug_url":"https://github.com/PaperMC/Paper/issues/12345","reason":"Public API for entity pose missing; reflection into nms.Entity#aZ","validates_via":"tests/integration/PoseRegressionTest.java","last_revalidated":"2026-04-01T09:00:00Z","last_revalidated_against":"1.21.3"}
{"hack_id":"font-cache-locale-shim","added":"2026-02-20","file":"src/lib/fontCache.ts","upstream":"npm:fontkit","upstream_version_range":"[1.8.0, 2.0.0)","upstream_bug_url":"https://github.com/foliojs/fontkit/issues/567","reason":"fontkit caches glyph metrics keyed without locale variant; shim re-keys","validates_via":"tests/font-cache.test.ts","last_revalidated":"2026-04-10T14:30:00Z","last_revalidated_against":"1.9.2"}
```

## Required fields

| Field | Type | Meaning |
|-------|------|---------|
| `hack_id` | string | stable kebab-case identifier |
| `added` | string (ISO date) | when the hack first landed |
| `file` | string (relative path) | the file whose code IS the hack |
| `upstream` | string | what the hack patches around (`papermc/Paper`, `npm:fontkit`, `cargo:tokio`, `gn:libogc`, etc.) |
| `upstream_version_range` | string | semver range or version-range expression where the hack applies |
| `upstream_bug_url` | string | link to the issue/PR that motivated the hack |
| `reason` | string | one-line "why this exists" |
| `validates_via` | string (relative path) | the test/script that proves the hack still works |

## Optional fields

- `last_revalidated` — ISO timestamp of last successful run of `validates_via`
- `last_revalidated_against` — upstream version exercised
- `auto_close_at` — date by which the hack should be removed (when upstream ships fix)
- `severity` — `low`/`medium`/`high` blast-radius hint

## States

- **CONFIGURED + clean**: file exists, no entry's `file` matches a path in current delta → no cap.
- **CONFIGURED + findings[]**: delta touches one or more `file` entries OR upstream bumped past `upstream_version_range` without `last_revalidated` update → findings emitted.
- **NOT_CONFIGURED**: file does not exist → advisory; no cap.

## Verdict caps

| Finding | Cap |
|---------|-----|
| Delta modifies a registered hack file | **B** unless commit also updates `last_revalidated` AND validates_via test ran green in the same session |
| Delta touches a file in a project whose upstream just exited the registered range | **REJECT** until hack re-evaluated |
| Hack `auto_close_at` date passed | **B** until hack removed or extended |

## How a project opts in

1. Create `vault/anti_fragility/hacks.jsonl` (the directory + empty file is enough to opt in).
2. Each time you write a "this is gross but it works" piece of code, append an entry. The append happens IN THE SAME COMMIT as the hack — the hack is not registered later, it is registered as part of being introduced.
3. Run the validates_via test as part of CI when upstream version bumps.

## Schema versioning

The first line of `hacks.jsonl` may optionally be a schema record:

```json
{"_schema":"afhl-v1"}
```

Future schema bumps (`afhl-v2`) add fields without breaking older readers; readers ignore unknown fields.

## Non-goals

- AFHL does NOT auto-detect hacks — registration is intentional.
- AFHL does NOT remove hacks for you — the human owns that decision.
- AFHL does NOT replace good engineering — it makes the cost of a hack visible.
