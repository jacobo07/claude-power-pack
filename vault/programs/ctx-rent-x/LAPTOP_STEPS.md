# LAPTOP STEPS (ctx-rent-x) — copy-pasteable, run on the laptop; never claimed from GEX44

## L1 — Rent estate by CCR generation (laptop plane)
Why: GEX44 has no CCR start receipts (`~/.claude/ccr` empty), so every session is generation UNKNOWN here.
Command (repo root, laptop): `python tools/ctx_rent.py estate --since 2026-10-25T00:00:00Z --until 2026-11-01T00:00:00Z --out estate-laptop-w0.json`
Expected: JSON with `classes.<class>.<generation>`; generations other than UNKNOWN present; `active_release` non-null.
Acceptance: >=1 non-UNKNOWN generation cell; commit the file to vault/programs/ctx-rent-x/ on mission/ctx-rent-x.

## L2 — Release records source_commit
Command: `python tools/ccr_release.py release` then `python -c "import json;print(json.load(open('<release dir>/RELEASE.json'))['source_commit'])"`
Acceptance: a 40-hex commit (null only when not in git).
