# Cognitive PGO report (CDC C8)

Window 14 d; read 2993/2993 transcripts (complete); 43,727,349,487 processed tokens.

## Dominant tax by role
| role | calls | tokens | share |
|---|---|---|---|
| unattributed | 52649 | 14,126,956,933 | 32.3% |
| READ | 46769 | 11,214,960,727 | 25.6% |
| IMPLEMENT | 16738 | 4,983,901,064 | 11.4% |
| NOVELTY | 12576 | 3,610,560,667 | 8.3% |
| CONTROL | 9046 | 2,163,074,113 | 4.9% |
| PROOF | 7889 | 2,065,437,307 | 4.7% |
| PLAN | 6999 | 1,701,671,231 | 3.9% |
| REREAD | 5209 | 1,259,166,231 | 2.9% |
| CONTEXT_FAULT | 5792 | 891,131,957 | 2.0% |
| REPAIR | 2920 | 873,563,413 | 2.0% |
| RECOVERY | 2045 | 551,142,874 | 1.3% |
| RESEARCH | 749 | 161,735,429 | 0.4% |
| STATUS | 461 | 124,047,541 | 0.3% |

## By project (top)
- C--Users-User--claude-skills-claude-power-pack: 7,500,045,762
- C--Users-User-Desktop-Cursor-Projects-TUA-X: 5,263,588,653
- C--Users-User-Desktop-Cursor-Projects-InfinityOps: 4,562,724,299
- C--Users-User-Desktop-Cursor-Projects-GEO-audit: 4,252,350,767
- C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files: 3,334,901,017
- C--Users-User-Desktop-Cursor-Projects-Vibe-Coding-Projects-Orca-X: 2,437,990,769
- C--Users-User-Apps-orca-dws-wt: 1,804,198,266
- C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects: 1,795,042,731
- C--Users-User-Desktop-Cursor-Projects-InfinityOps-17-Businesses-QuickLease: 1,666,921,936
- C--Users-User-Apps-recon-work-wt-keosdtk-home: 1,633,747,447
- C--Users-User-Desktop-Cursor-Projects-Jacobo: 1,036,543,049
- C--Users-User-Apps-orca-backlog-wt: 1,008,856,930
- C--Users-User-Desktop-Cursor-Projects-TUA-X--claude-worktrees-brand001-clock-a: 841,813,695
- C--Users-User-Desktop-Cursor-Projects-CostaLuz-Lawyers: 771,941,495
- C--Users-User-Apps-io-ucg: 717,766,495

## By work class
- BUILD: 43,031,177,164
- INVESTIGATE: 696,172,323

## Motifs (tool n-grams, rank = tokens x sessions)
| motif | occ | sessions | tokens |
|---|---|---|---|
| PowerShell:other > PowerShell:other | 16459 | 1194 | 8,657,181,856 |
| Read > Read | 16915 | 2049 | 3,450,062,744 |
| Read > Edit | 9913 | 1199 | 5,236,085,265 |
| Grep > Read | 10308 | 1678 | 3,732,465,666 |
| PowerShell:other > PowerShell:other > PowerShell:other | 8060 | 911 | 6,377,613,870 |
| Edit > Edit | 10369 | 1150 | 4,154,430,923 |
| Read > Grep | 8725 | 1738 | 2,603,995,533 |
| Grep > Grep | 9937 | 1500 | 2,994,652,164 |
| Edit > Read > Edit | 4812 | 931 | 3,678,632,091 |
| Read > Read > Read | 8133 | 1622 | 1,945,924,837 |
| PowerShell:other > PowerShell:other > PowerShell:other > PowerShell:other | 4367 | 669 | 4,551,377,215 |
| Edit > Read | 6007 | 1025 | 2,965,607,519 |
| PowerShell:other > Read | 6076 | 1085 | 2,771,656,267 |
| Write > PowerShell:other | 5816 | 898 | 3,114,344,793 |
| Read > Edit > Edit | 3711 | 883 | 2,638,903,714 |

## Proof-run motifs
- PowerShell:proof > PowerShell:other: 1558 occ, 565 sessions, 890,469,079 tok
- PowerShell:proof > PowerShell:proof: 1774 occ, 504 sessions, 917,470,615 tok
- Edit > PowerShell:proof: 1648 occ, 484 sessions, 847,769,107 tok
- PowerShell:other > PowerShell:proof: 1274 occ, 551 sessions, 688,049,393 tok
- Write > PowerShell:proof: 1282 occ, 456 sessions, 678,621,464 tok
- PowerShell:proof > Write: 875 occ, 363 sessions, 480,926,728 tok

## Debt register (interest = avoidable x recurrence; ROIC = interest / est. fix calls)
| debt | cost | avoidable | sessions | interest | ROIC | status |
|---|---|---|---|---|---|---|
| Context | 2,150,298,188 | 1,720,238,550 | 2160 | 3,715,715,268,000 | 148,628,610,720 | MEASURED (fix/avoidable ESTIMATE) |
| Coordination | 2,287,121,654 | 1,600,985,157 | 1328 | 2,126,108,288,496 | 141,740,552,566 | MEASURED (fix/avoidable ESTIMATE) |
| Proof | 2,065,437,307 | 619,631,192 | 1101 | 682,213,942,392 | 22,740,464,746 | MEASURED (fix/avoidable ESTIMATE) |
| Recovery | 1,424,706,287 | 712,353,143 | 1025 | 730,161,971,575 | 20,861,770,616 | MEASURED (fix/avoidable ESTIMATE) |
| Token | 1,216,866,688 | 1,216,866,688 | 398 | 484,312,941,824 | 12,107,823,546 | MEASURED (fix/avoidable ESTIMATE) |
| Decision | 1,701,671,231 | 170,167,123 | 1733 | 294,899,624,159 | 4,914,993,736 | MEASURED (fix/avoidable ESTIMATE) |
| Research | 161,735,429 | 48,520,628 | 113 | 5,482,830,964 | 182,761,032 | MEASURED (fix/avoidable ESTIMATE) |
| Owner | UNKNOWN | - | - | - | - | UNKNOWN |
| Constitutional | UNKNOWN | - | - | - | - | UNKNOWN |

## Irreducibility frontier
- NOVELTY (3,610,560,667 tok): reopen when a generator/template covers >=30 % of new files in a programme
- IMPLEMENT (4,983,901,064 tok): irreducible: the edit is the product; reopen only if edits repeat verbatim across sessions
- PLAN (1,701,671,231 tok): reopen when plan text repeats across sessions (cache as compiled unit)
- READ (11,214,960,727 tok): reopen when the same path set is read in >=3 sessions of one programme (precompute digest)
- Owner (UNKNOWN): UNKNOWN: transcripts do not carry Owner waits; reopen with a pane-wait ledger
- Constitutional (UNKNOWN): UNKNOWN: reopen when rule-citation events are logged per call

## Exit to determinism
- PowerShell:other > PowerShell:other: candidate: check for a pure function of the previous result
- Read > Read: deterministic: batch the reads / return a digest
- Read > Edit: deterministic: batch the reads / return a digest
- Grep > Read: candidate: check for a pure function of the previous result
- PowerShell:other > PowerShell:other > PowerShell:other: candidate: check for a pure function of the previous result
- Edit > Edit: candidate: check for a pure function of the previous result
- Read > Grep: deterministic: batch the reads / return a digest
- Grep > Grep: candidate: check for a pure function of the previous result
- Edit > Read > Edit: candidate: check for a pure function of the previous result
- Read > Read > Read: deterministic: batch the reads / return a digest

## Unproductive-call corpus: 18115 calls, 3,918,307,750 tokens
- REREAD: 5209 calls, 1,259,166,231 tok
- CONTEXT_FAULT: 5792 calls, 891,131,957 tok
- NO_PROGRESS_RUN:READ: 2705 calls, 619,092,226 tok
- RECOVERY: 2045 calls, 551,142,874 tok
- NO_PROGRESS_RUN:unattributed: 1948 calls, 500,405,133 tok
- NO_PROGRESS_RUN:CONTROL: 184 calls, 47,201,912 tok
- NO_PROGRESS_RUN:PROOF: 88 calls, 20,949,233 tok
- NO_PROGRESS_RUN:PLAN: 67 calls, 13,461,807 tok
- NO_PROGRESS_RUN:RESEARCH: 53 calls, 10,275,550 tok
- NO_PROGRESS_RUN:STATUS: 24 calls, 5,480,827 tok
