# [H] freshness / drift -- evidence

Frozen pillar H rule (ledger, quoted):

> drift between a skill's live copy and its repo mirror, and between a card and its source, is detected by a gate driven from both poles

This file covers the live-vs-mirror half (decision D-02): repo-mirrored skills against their live copy. Card-vs-source drift is rendered further down when the card half is recorded.

## Method

- Repo side: COMMITTED blobs at a named commit (`git cat-file --batch` through the primitives of `tools/verify_global_mirrors.py`), never the working tree.
- Unit: the whole skill directory `skills/<name>/`, reduced to a sha256 over the sorted lines `<relpath>\0<lf_sha256>\n`. Files are LF-normalized before hashing (the laptop clone runs core.autocrlf=true).
- Live side: `<live-root>/<name>/` walked without following symlinked directories; `__pycache__/` and `*.pyc` are excluded and counted.
- Statuses: IDENTICAL (`eol_only` when only line endings differ), DRIFT (with `missing_live`, `extra_live`, `changed`), ABSENT_LIVE, INCONCLUSIVE.
- ABSENT_LIVE is reported and is not drift: not every repo skill is meant to be installed on every host.

## Why a skills pass

`modules/mirror_discovery/discovery.py` files the whole `skills` domain under OTHER_OWNER, so no parity check covers repo-mirrored skills. Pairing `skills` there would also pull in the ~160 live skills no repo directory owns (gsd-*, plugins), change `domain_counts` for every estate, and add to the `verify_spp.py` mirror-parity row's 15 s budget. The new pass pairs only repo `skills/<name>` that hold a SKILL.md and reuses the comparator's primitives, so there is still one comparator.

## Planes

No plane recorded yet.

## Commands

command: python3 tools/test_skill_drift.py
command: python3 tools/test_skill_drift.py --write-evidence
command: python3 tools/skill_mirror_drift.py --live
