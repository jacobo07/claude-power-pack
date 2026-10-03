# [B] listing floor -- D-LISTING measurement

Planes: sessions host `laptop` (derived: both arms' `cwd` start with `C:\Users\User\`); derivation host-independent (this file is rendered from committed rows by `tools/test_listing_floor_verdict.py`, nothing typed in). Fresh sessions consumed in this phase: 0.

Sources: `wiki/tools/listing_floor_probe.results.jsonl` rows selected by label (R2R1, R3, champion-startup, challenger-startup), pinned to the jsonl blob at K4 commit 4d1cfb83 (LF sha256 74c5514c6049b3e74de9a679d37972762862f0c37964b8f4b0f57875318a7635, 4 K4 rows); `vault/plans/skill-residency-program-2026-10-03.md` at commit d9072185; `vault/plans/skill-virtualization-k-slice-2026-10-03.md`; `vault/lessons/2026-10-03-capped-listing-and-card-aperture.md`; frozen D-LISTING in `vault/programs/skill-capability/ledger.json`. Frozen caveat: fresh-session first-call figures; one session each, n=1 per arm.

Frozen pillar B rule (ledger, quoted):

> listing hiding was falsified twice (C6, K4) against D-LISTING; a third hypothesis closes this pillar only with its own measurement against D-LISTING recording the command; a lower floor claimed without a fresh-session measurement is refused

## Arms (fresh-session first-call figures, one session each)

| label | session_id | ts | cwd | settings_file | listing chars | startup_tokens |
|---|---|---|---|---|---|---|
| champion-startup | 8f983bc6-d760-4440-938d-aeed86a548ae | 2026-10-03T15:35:11 | C:\Users\User\Apps\listing-probe\champion | None | 30000 | 87739 |
| challenger-startup | b568fafb-782d-48ab-9014-d9ae2b13c882 | 2026-10-03T15:35:50 | C:\Users\User\Apps\listing-probe\challenger | C:\Users\User\Apps\listing-probe\challenger-settings.json | 29795 | 89844 |

## Verdict (recomputed from the rows)

- ok V-LF-SOURCES: champion-startup and challenger-startup resolved, one row each
- ok V-LF-TOKENS: challenger startup_tokens 89844 vs champion 87739 (delta +2105): not below champion
- ok V-LF-CAP: challenger listing chars 29795, cap 30000, gap 205 chars (0.68% of cap), band 300: still cap-bound
- ok V-LF-DENOM-MATCH: rows equal frozen D-LISTING (challenger chars 29795, champion startup_tokens 87739, challenger startup_tokens 89844)
- verdict: FALSIFIED (frozen cap 30000, band 300)

## Row counts and their aperture

- champion-startup: entries 216, described 73; challenger-startup: entries 88, described 62. These are first-':' key counts of the probe, not skill counts: every `plugin:skill` line collapses into one key.
- ok V-LF-ENTRIES-APERTURE: probe at K4: 4 lines (two namespaced) -> entries 3; non-namespaced control 3 lines -> entries 3: entries/described are first-':' key counts

## Figures not derivable from any data row

- described plugin entries 22 -> 50: source commit 4d1cfb83 message; vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 13; frozen D-LISTING.plugin_refill_entries = "22 -> 50"; not used by the verdict
- described entries 87 -> 103: source commit 4d1cfb83 message; vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 13; not used by the verdict
- name-only lines 179 -> 32: source commit 4d1cfb83 message; vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 13; not used by the verdict

## C6 (name-only skillOverrides, laptop)

- ok V-LF-C6: C6 134 name-only overrides, listing 29991 (bfe97833) -> 30002 (a5df8940) chars, commit d9072185: listing did not drop, cap still binds
- source: `vault/plans/skill-residency-program-2026-10-03.md` bullet `C6 DONE`, introduced by commit d9072185; no startup-token reading recorded for C6.

## Economics

- realized saving: none.
- C6 moved the initial listing +11 chars (29991 -> 30002).
- K4 moved startup tokens +2105 (87739 -> 89844) against the stated noise +-1500 (vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 12): startup tokens rose by 2105, above the stated noise (+-1500) by 605. fresh-session first-call figures; one session each, n=1 per arm.
- recorded next hypothesis (`vault/plans/skill-virtualization-k-slice-2026-10-03.md` line 110, needs Owner): an UPPER BOUND of ~9000 startup tokens per session minus ~4000 per gateway read; displacement unknown; denominator D-LISTING; never a realized saving.

## Sessions (D-SESSIONS)

- K4 rows in the K4 blob: 4; fresh sessions consumed in this phase: 0 (D-02); listing family remaining 8 of 12.

## Commands (reconstructed from row fields; prompts not recorded in the rows)

command: python wiki/tools/listing_floor_probe.py --label R2R1 --settings-file C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\bfe97833-3312-4e50-a61c-efb6de71e846\scratchpad\r2.json --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label R3 --settings-file C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\bfe97833-3312-4e50-a61c-efb6de71e846\scratchpad\r2.json --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label champion-startup --cwd C:\Users\User\Apps\listing-probe\champion --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label challenger-startup --settings-file C:\Users\User\Apps\listing-probe\challenger-settings.json --cwd C:\Users\User\Apps\listing-probe\challenger --prompt <not recorded in the row>
command: python3 tools/test_listing_floor_verdict.py   (check; `python` on the laptop)
command: python3 tools/test_listing_floor_verdict.py --write-evidence   (render this file)
