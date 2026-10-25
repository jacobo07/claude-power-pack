# ctx-rent-a2 closure

**Class: DELIVERED_WITH_TRANSFERRED_OBLIGATIONS.** Written 2026-10-25 on plane GEX44 (clone `mission/ctx-rent-obs`).
Receipt of ownership: `vault/programs/ctx-rent-a2/TAKEOVER.json` (12 rows, slices A-L), sha256 `8a19463321ff20d31328db4b3574382b7b85c08c86981d71ff56de1f0c5b0588`.

## Authority lineage (plan `vault/plans/context-rent-observatory-2026-10-25.md` section 1)
| seq | when (local) | value | source |
|---|---|---|---|
| 1 | 10-11 10:27 | cap 14,000,000 | plan 6f5840a3, Owner "y go p95" |
| 33 | 10-11 14:02 | programme 30,000,000 | capital packet `owner-capital-ctx-rent-2026-10-11.json`, approval e2a5f2c6 |
| 44/45 | 10-23 15:29 | programme 60,000,000; lease L2 cap 30M | Owner typed `subelo 30M ctx-rent-a2`, owner-econ-raise |

No AUTHORITY_PROVENANCE_FAILURE. Weakness: the 60M row had no approving entry uuid; `tools/econ_plane.py` now takes
`--approval-uuid` and writes it into the programme row source (V-ECON-RAISE-APPROVAL-UUID).

## What was delivered
- A (4de21ba8) census method; B (c6657844) boot deflation, still N=1 on the provider call (B1 re-types it).
- Residual R1-R6 sealed (aa97ebf8; R6 as a separate file a06e4dc8).
- Slices C-L: ownership moved, see TAKEOVER.json. Each row carries who owns the implementation, who owns the evidence, and the
  file:line or commit that proves the transfer.
- UNVERIFIED on this plane: the econ-succession commits af7ec647 and 44396331 are not objects in this clone (rows I and J).

## Ledger moves: pending, done on the laptop plane
Plane GEX44 holds no ctx-rent-a2 ledger (`goal-status` here reads programme null, settled 0), so no pane booking and no
programme lowering was done here. Released amount: not recorded here (UNKNOWN until the laptop lowers the programme).
See `vault/programs/ctx-rent-obs/STATUS.md` section LEDGER_TODO for the two exact actions.
