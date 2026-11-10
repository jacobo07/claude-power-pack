# Renewal silently blocked by the auto envelope (mission with Owner headroom halted 3h46m, nobody told)

Measured 2026-11-10, GEX44, m-f27c61b9e75c (Ascension S23, override path).
- 09:42:09Z HALTED "turn ended and budget: iterations 12 >= max 12", work remaining (0/9 phases ticked).
- No `mission_renewed` and no refusal row in the ledger. Re-evaluated by hand: `_renewal_why_not` =
  "lineage budget exhausted: 43,474,533 processed of 23,232,149". 23.2M is the AUTO envelope
  (`envelope_auto_assigned`, 2026-11-09 21:25Z), not the Owner's authority (160M, 1.5M reserve).
- The refusal goes only to the sweep row (`row["renewal"]`), never to the ledger or the Owner. Found by the
  coordinator 13:28Z; renewed by hand to m-3f44ac4c922c.

Fix candidates (spec first, T2):
1. When the only refusal is an auto envelope below lineage spend AND Owner authority has headroom, re-derive the
   envelope from authority (minus reserve) instead of refusing; an Owner-set envelope still refuses.
2. Every renewal refusal is ledgered (`renewal_refused`, reason) and routed through `mission_topup.notify`.
3. Renewal must not hand the successor a fresh `max_hours`: carry the remainder of the lineage wall
   (today a renewal resets the clock to created_at; the coordinator passed 51.14 h by hand).
Gate idea: V-RENEW-AUTO-ENVELOPE (auto 23M, spend 43M, authority 160M -> renews), negative with an Owner-set
envelope; V-RENEW-REFUSAL-LEDGERED; V-RENEW-WALL-REMAINDER.
