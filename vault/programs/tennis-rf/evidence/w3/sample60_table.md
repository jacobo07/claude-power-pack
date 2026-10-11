# W3 step 3 -- 60-function Tennis m2c sample (no compile)

Producer: m2c_producer.py (pinned m2c 708d2d2), ppc-mwcc-c, over SportsPackEP DTK asm. unresolved_types = `?` type tokens in the m2c C; unk_fields = `unk[0-9A-F]+` field tokens. Resort-shape = step0 shape hash vs Resort split (exact/loose/none). fan-in/out = distinct bl callers/callees over the whole DOL asm.

| fn | unit | insns | shape | status | unresolved_types | unk_fields | fan-in | fan-out |
|---|---|---|---|---|---|---|---|---|
| fn_80203E40 | 80202950 | 3 | exact | L1 | 0 | 1 | 0 | 0 |
| fn_80203E4C | 80202950 | 4 | exact | M2C_FAILED | 0 | 0 | 1 | 0 |
| fn_80230BF8 | 80202950 | 14 | exact | L1 | 2 | 2 | 2 | 2 |
| fn_801BD47C | 801BC5B8 | 16 | exact | L1 | 1 | 0 | 0 | 1 |
| fn_8022E61C | 80202950 | 16 | exact | L1 | 1 | 0 | 0 | 1 |
| fn_80257978 | 8023FE44 | 16 | exact | L1 | 1 | 0 | 0 | 1 |
| fn_803315A0 | 8032BC4C | 16 | exact | L1 | 1 | 0 | 0 | 1 |
| fn_80230FE4 | 80202950 | 17 | exact | L1 | 0 | 1 | 1 | 0 |
| fn_801BC6B4 | 801BC5B8 | 22 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_8024B7C8 | 8023FE44 | 22 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_8025C600 | 80257B08 | 22 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_8022621C | 80202950 | 23 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_80278FEC | 80278300 | 23 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_8027DBA8 | 80278300 | 23 | exact | L1 | 2 | 0 | 0 | 2 |
| fn_8024C0F0 | 8023FE44 | 30 | exact | L1 | 12 | 0 | 0 | 3 |
| fn_801BD194 | 801BC5B8 | 3 | loose | L1 | 1 | 0 | 1 | 0 |
| fn_8022F90C | 80202950 | 3 | loose | L1 | 0 | 1 | 1 | 0 |
| fn_8032CF78 | 8032BC4C | 3 | loose | L1 | 0 | 1 | 3 | 0 |
| fn_802047D8 | 80202950 | 4 | loose | L1 | 0 | 1 | 0 | 0 |
| fn_80230ABC | 80202950 | 4 | loose | L1 | 0 | 1 | 5 | 0 |
| fn_8020711C | 80202950 | 5 | loose | L1 | 0 | 1 | 4 | 0 |
| fn_80220A54 | 80202950 | 5 | loose | L1 | 0 | 3 | 5 | 0 |
| fn_80230F90 | 80202950 | 5 | loose | M2C_FAILED | 0 | 0 | 1 | 0 |
| fn_8027A154 | 80278300 | 5 | loose | L1 | 0 | 2 | 1 | 0 |
| fn_80233A68 | 80202950 | 6 | loose | M2C_FAILED | 0 | 0 | 1 | 0 |
| fn_8020CC14 | 80202950 | 13 | loose | L1 | 0 | 3 | 1 | 0 |
| fn_80252AD8 | 8023FE44 | 14 | loose | L1 | 3 | 0 | 0 | 1 |
| fn_80279E44 | 80278300 | 17 | loose | L1 | 2 | 2 | 1 | 1 |
| fn_8021F3E4 | 80202950 | 24 | loose | L1 | 1 | 4 | 1 | 2 |
| fn_80254440 | 8023FE44 | 27 | loose | L1 | 1 | 7 | 1 | 1 |
| fn_80203FEC | 80202950 | 3 | none | L1 | 0 | 0 | 1 | 0 |
| fn_8021EAA8 | 80202950 | 6 | none | L1 | 0 | 1 | 1 | 0 |
| fn_802128D4 | 80202950 | 8 | none | L1 | 0 | 2 | 2 | 0 |
| fn_80253E30 | 8023FE44 | 9 | none | M2C_FAILED | 0 | 0 | 1 | 0 |
| fn_8020A354 | 80202950 | 12 | none | M2C_FAILED | 0 | 0 | 0 | 0 |
| fn_8020380C | 80202950 | 15 | none | M2C_FAILED | 0 | 0 | 0 | 0 |
| fn_80241018 | 8023FE44 | 17 | none | L1 | 0 | 3 | 1 | 0 |
| fn_8022FFA8 | 80202950 | 21 | none | M2C_ERROR | 1 | 4 | 4 | 1 |
| fn_8022E7A0 | 80202950 | 24 | none | L1 | 1 | 2 | 0 | 3 |
| fn_80252F34 | 8023FE44 | 27 | none | L1 | 2 | 5 | 1 | 0 |
| fn_8024FB7C | 8023FE44 | 30 | none | M2C_ERROR | 0 | 1 | 0 | 1 |
| fn_8021F8BC | 80202950 | 34 | none | L1 | 0 | 2 | 1 | 2 |
| fn_801BCBCC | 801BC5B8 | 39 | none | L1 | 2 | 6 | 1 | 0 |
| fn_802500E0 | 8023FE44 | 43 | none | M2C_FAILED | 0 | 0 | 1 | 0 |
| fn_8021FEE0 | 80202950 | 48 | none | L1 | 2 | 15 | 0 | 2 |
| fn_80216640 | 80202950 | 53 | none | L1 | 3 | 4 | 1 | 2 |
| fn_80253348 | 8023FE44 | 57 | none | L1 | 1 | 17 | 1 | 1 |
| fn_8020384C | 80202950 | 63 | none | L1 | 0 | 16 | 0 | 5 |
| fn_8021F080 | 80202950 | 69 | none | L1 | 6 | 19 | 1 | 4 |
| fn_802797E4 | 80278300 | 74 | none | L1 | 6 | 14 | 1 | 7 |
| fn_8032EB78 | 8032BC4C | 80 | none | M2C_ERROR | 0 | 8 | 0 | 1 |
| fn_8025C6D0 | 80257B08 | 91 | none | M2C_ERROR | 18 | 18 | 1 | 7 |
| fn_8027D360 | 80278300 | 104 | none | L1 | 4 | 24 | 0 | 8 |
| fn_8022C2A0 | 80202950 | 119 | none | L1 | 4 | 25 | 1 | 4 |
| fn_80257424 | 8023FE44 | 130 | none | L1 | 8 | 15 | 0 | 3 |
| fn_8025B6D4 | 80257B08 | 149 | none | L1 | 3 | 31 | 1 | 6 |
| fn_8025342C | 8023FE44 | 171 | none | L1 | 4 | 61 | 1 | 5 |
| fn_80251A60 | 8023FE44 | 213 | none | M2C_ERROR | 0 | 13 | 1 | 5 |
| fn_8022D46C | 80202950 | 305 | none | L1 | 14 | 67 | 1 | 12 |
| fn_80247530 | 8023FE44 | 1310 | none | L1 | 25 | 360 | 1 | 32 |

Totals: L1 48 / fail 12; unresolved_types sum 142; unk_fields sum 763.
