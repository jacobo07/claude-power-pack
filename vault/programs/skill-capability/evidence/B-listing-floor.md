# [B] listing floor -- D-LISTING measurement

Planes: sessions host `laptop` (derived: both arms' `cwd` start with `C:\Users\User\`); derivation host-independent (this file is rendered from committed rows by `tools/test_listing_floor_verdict.py`, nothing typed in).

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
- verdict: FALSIFIED (frozen cap 30000, band 300)

## Commands

command: python wiki/tools/listing_floor_probe.py --label R2R1 --settings-file C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\bfe97833-3312-4e50-a61c-efb6de71e846\scratchpad\r2.json --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label R3 --settings-file C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\bfe97833-3312-4e50-a61c-efb6de71e846\scratchpad\r2.json --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label champion-startup --cwd C:\Users\User\Apps\listing-probe\champion --prompt <not recorded in the row>
command: python wiki/tools/listing_floor_probe.py --label challenger-startup --settings-file C:\Users\User\Apps\listing-probe\challenger-settings.json --cwd C:\Users\User\Apps\listing-probe\challenger --prompt <not recorded in the row>
command: python3 tools/test_listing_floor_verdict.py   (check; `python` on the laptop)
command: python3 tools/test_listing_floor_verdict.py --write-evidence   (render this file)
