# [H] freshness / drift -- evidence

Frozen pillar H rule (ledger, quoted):

> drift between a skill's live copy and its repo mirror, and between a card and its source, is detected by a gate driven from both poles

This file covers the live-vs-mirror half (decision D-02): repo-mirrored skills against their live copy. The card-vs-source half is rendered under 'Card vs source'.

## Method

- Repo side: COMMITTED blobs at a named commit (`git cat-file --batch` through the primitives of `tools/verify_global_mirrors.py`), never the working tree.
- Unit: the whole skill directory `skills/<name>/`, reduced to a sha256 over the sorted lines `<relpath>\0<lf_sha256>\n`. Files are LF-normalized before hashing (the laptop clone runs core.autocrlf=true).
- Live side: `<live-root>/<name>/` walked without following symlinked directories; `__pycache__/` and `*.pyc` are excluded and counted.
- Statuses: IDENTICAL (`eol_only` when only line endings differ), DRIFT (with `missing_live`, `extra_live`, `changed`), ABSENT_LIVE, INCONCLUSIVE.
- ABSENT_LIVE is reported and is not drift: not every repo skill is meant to be installed on every host.

## Why a skills pass

`modules/mirror_discovery/discovery.py` files the whole `skills` domain under OTHER_OWNER, so no parity check covers repo-mirrored skills. Pairing `skills` there would also pull in the ~160 live skills no repo directory owns (gsd-*, plugins), change `domain_counts` for every estate, and add to the `verify_spp.py` mirror-parity row's 15 s budget. The new pass pairs only repo `skills/<name>` that hold a SKILL.md and reuses the comparator's primitives, so there is still one comparator.

## Planes

### Plane gex44

- host `gex44`, node `kobicraft-gex44`, measured_at 2026-10-03T18:28:32Z, live root `~/.claude/skills`
- repo_commit `97ded664c314857fb32f88576a41529380d060e7` (repo side = committed blobs at that commit)
- command: python3 tools/skill_mirror_drift.py --measure-live --host gex44
- counts: IDENTICAL 13 (of which eol_only 10), DRIFT 1, ABSENT_LIVE 10, INCONCLUSIVE 0; 24 repo skills

| skill | status | eol_only | missing_live / extra_live / changed |
|---|---|---|---|
| agent-architecture-audit | ABSENT_LIVE | no |  |
| agent-eval | ABSENT_LIVE | no |  |
| agent-harness-construction | ABSENT_LIVE | no |  |
| agent-introspection-debugging | ABSENT_LIVE | no |  |
| agentic-os | ABSENT_LIVE | no |  |
| android-reverse-engineering | DRIFT | no | missing_live scripts/check-deps.ps1, scripts/decompile.ps1, scripts/find-api-calls.ps1, scripts/install-dep.ps1; extra_live -; changed - |
| autonomous-loops | ABSENT_LIVE | no |  |
| concurrent-writers-shared-tree | IDENTICAL | yes |  |
| destructive-state-authorization | IDENTICAL | yes |  |
| develop-here-prove-there | IDENTICAL | yes |  |
| eval-harness | ABSENT_LIVE | no |  |
| evaluation-corpus-governance | IDENTICAL | yes |  |
| guard-event-reachability | IDENTICAL | yes |  |
| instrument-before-claim | IDENTICAL | yes |  |
| intent-driven-development | ABSENT_LIVE | no |  |
| mobile-app-ui-design | IDENTICAL | no |  |
| mobile-game-wii-port | IDENTICAL | no |  |
| monetary-quantity-integrity | IDENTICAL | yes |  |
| motion-promo | IDENTICAL | no |  |
| presence-is-not-residency | IDENTICAL | yes |  |
| real-context-reachability | IDENTICAL | yes |  |
| recurring-work-cardinality | IDENTICAL | yes |  |
| recursive-decision-ledger | ABSENT_LIVE | no |  |
| verification-loop | ABSENT_LIVE | no |  |

#### Reconciliation with CONTEXT

04-CONTEXT D-02 records "4 identical, 10 differ, 10 absent" for this plane. That is a raw-byte comparison of SKILL.md alone; recomputed here from the recording's raw shas it gives 4 identical, 10 differ, 10 absent. This gate compares the whole directory after LF normalization (the method named under Method), which gives IDENTICAL 13 (eol_only 10), DRIFT 1, ABSENT_LIVE 10: the 10 raw-byte "differ" are CRLF-versus-LF files whose content is equal, and the one real DRIFT is a missing set of files that a SKILL.md-only compare cannot see. Both are measurements of the same tree; they answer different questions.

Drift found on this host is reported and never fixed here (no write under the home directory). Running `python3 tools/skill_mirror_drift.py --live` on the laptop plane is an Owner-bundle `[H]` item.

## Card vs source

Pairs are discovered: each deny card registered in `hooks/hook-dispatcher.js` names its skill, and the source is `skills/<skill>/SKILL.md`. The record pins the LF sha256 of both, read from committed blobs.

- rule: Re-run `--record-cards` only after re-deriving each card from its current source; recording is the re-derivation act.
- recorded_at_commit `0a2ab9eaafcfcd7f915d2d0908c53b240bbde2de`

| skill | card | status at HEAD |
|---|---|---|
| concurrent-writers-shared-tree | hooks/doctrine_cards.js | CURRENT |
| destructive-state-authorization | hooks/destructive_doctrine_card.js | CURRENT |

Lineage fields inside a card (which source line each rule came from) belong to pillar G and are not recorded here; this record only makes a source change visible to a gate.

## Commands

command: python3 tools/skill_mirror_drift.py --cards
command: python3 tools/skill_mirror_drift.py --record-cards
command: python3 tools/test_skill_drift.py
command: python3 tools/test_skill_drift.py --write-evidence
command: python3 tools/skill_mirror_drift.py --live
command: python3 tools/skill_mirror_drift.py --measure-live --host gex44
