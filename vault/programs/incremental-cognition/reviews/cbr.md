# Incremental Cognition -- CBR review of the pillar N candidates

What was reviewed: every candidate block of `vault/programs/incremental-cognition/ukdl-candidates.md` (discovered, not listed
here), filed against one family of the Constitutive Baseline Ratchet or against none. CBR here is `modules/tower`, the family
definitions in `vault/tower/families/`, the generations in `vault/tower/baselines/<family>/B<n>.json`, and the read-mostly CLI
`tools/family_baseline.py` (`wiki/components/constitutive-baseline-ratchet.md`). Frozen rule N: "candidates go to
vault/programs/incremental-cognition/ukdl-candidates.md; promotion into ukdl-universal.md and CBR is reviewed, never silent".

reviewer: this run (mission `incremental-cognition`, GEX44 plane, branch `mission/incremental-cognition-run`, plan 06-03); a reading by the mission itself, not the Owner's decision
promotion: left to the Owner, recorded through the `[N]` item of `vault/programs/incremental-cognition/owner-bundle.md`; this review proposes and never writes a generation

transfer_rule: a performance guarantee promoted to CBR needs a second, materially independent workload

The line above is the program's frozen `materiality.transfer` rule, quoted byte for byte from
`vault/programs/incremental-cognition/ledger.json`; the closeout gate compares it with the ledger and refuses a
PROMOTE-PROPOSED performance candidate that has no `second_workload:` ref.

reviewed_against: vault/tower/families/kobiicraft_mode.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 3e49fb59090af7ea7fd5d4ccc01d270615e280d7150612d44889ddc6e8af338d
reviewed_against: vault/tower/families/persistent_state.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 3f4b0632c25c51430138f0c7fdd9967cda77491c5c34d6ed8f179d12de955d6f
reviewed_against: vault/tower/families/web_surface.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 0d95956e02a350df96a21bd5fb731f835dab2f6f67bf438148b3227b82cd9b10
reviewed_against: vault/tower/families/wii_homebrew.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 f772f282c86a66b7ef312da2fe8449fe5526508adbaadcaa8177b2dab0073cfc
reviewed_against: vault/tower/baselines/kobiicraft_mode/B0.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407
reviewed_against: vault/tower/baselines/persistent_state/B0.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64
reviewed_against: vault/tower/baselines/web_surface/B1.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1
reviewed_against: vault/tower/baselines/wii_homebrew/B0.json @ 189497a8348d799691d719b3e2954be29af367f9 sha256 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd

## CBR facts (read-only commands run at the recorded commit)

- Families discovered from `vault/tower/families/*.json`: `kobiicraft_mode` (B0, 15 entries), `persistent_state` (B0, 15),
  `web_surface` (B1, 17), `wii_homebrew` (B0, 15), read with `python3 tools/family_baseline.py show <family>`. They are
  PRODUCT families: a Minecraft mode, a product holding persistent or destructive state, a public web surface, a Wii homebrew
  build. A rule belongs in one only if a new instance of that family is incomplete without it.
- `tools/family_baseline.py` subcommands: `build-b0`, `show`, `review`, `verify`, `revert`. There is no `promote`
  subcommand. `python3 tools/family_baseline.py verify web_surface` printed `web_surface chain: OK (generations [0, 1])`.
- A promote function exists, `modules/tower/ratchet.py:164` (`def promote(family, new_entries, reason, authority, root=None)`,
  which writes B<n+1>), and its only callers are tests. The grep named in the plan, run now:
  `grep -rn "ratchet.promote\|import promote\|ratchet import" --include=*.py modules tools` printed four lines, none of them
  the tower module: `modules/intent_verified/__init__.py:29`, `tools/test_intent_verified.py:27`, `tools/test_uqf.py:185`,
  `tools/intent_verify.py:33` (a different module, `intent_verified`, and a CEPS helper). The sharper
  `grep -rn "rt\.promote\|\.promote(" --include=*.py modules tools` (CEPS lines removed) printed `tools/test_osr.py:110`
  and `:115` (an unrelated object) and `tools/test_tower_ratchet.py:71`, `:90`, `:92`, `:203`. So a CBR promotion today is a
  call to `modules.tower.ratchet.promote` by the Owner with a reason and an authority, and no CLI or hook reaches it.

| candidate | family | verdict | reason |
|---|---|---|---|
| IC-U-01 | none | REJECT | a supervisor-side rule for deciding when a mission worker is refused; no product family's instance is incomplete without it (the nearest, persistent_state, is about destructive state and money, not about launching workers), so it has no CBR home and stays a UKDL proposal |
| IC-D-01 | none | REJECT | a rule for measuring session corpora, not for building a product of one of the four families; filing it against web_surface or persistent_state would put an instrument rule into a product baseline |
| IC-P-01 | none | REJECT | specific to this program's done-gate (R3 smoke versus primary roles); not a product-family rule and not a performance guarantee |

## Promotions recorded

none
