# Estimator fit (WU-S3)
cost_i = f + g*i per assistant message (input+cache_read+cache_creation), OLS. Source: owner transcripts of the four slim-t2 missions.

| mission | calls | total | first call | g |
|---|---|---|---|---|
| m-93c9624fb4cc | 19 | 909,247 | 18,332 | 2,488 |
| m-6ffa7ac2513b | 19 | 742,614 | 18,236 | 2,430 |
| m-1cb7a01e969b | 22 | 680,606 | 18,514 | 1,165 |
| m-c60ceb4c354c | 17 | 442,155 | 18,585 | 815 |

Pooled g = mean = 1,725 (growth_n = 4).

Open point: WU-1H4 (448,589 over 7 calls, ~64K/call) cannot be reproduced by f~18K + g~1.7K; it would need g~9.4K. These four epochs do not support the packet's 1H4 figure, so the 1H4 shortfall is not covered by this fit. Quadratic test uses the fitted missions; the three-miss DEGRADED rule is the backstop.
