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

reviewed_against: vault/tower/families/kobiicraft_mode.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 3e49fb59090af7ea7fd5d4ccc01d270615e280d7150612d44889ddc6e8af338d
reviewed_against: vault/tower/families/persistent_state.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 3f4b0632c25c51430138f0c7fdd9967cda77491c5c34d6ed8f179d12de955d6f
reviewed_against: vault/tower/families/web_surface.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 0d95956e02a350df96a21bd5fb731f835dab2f6f67bf438148b3227b82cd9b10
reviewed_against: vault/tower/families/wii_homebrew.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 f772f282c86a66b7ef312da2fe8449fe5526508adbaadcaa8177b2dab0073cfc
reviewed_against: vault/tower/baselines/kobiicraft_mode/B0.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407
reviewed_against: vault/tower/baselines/persistent_state/B0.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64
reviewed_against: vault/tower/baselines/web_surface/B1.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1
reviewed_against: vault/tower/baselines/wii_homebrew/B0.json @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd

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
- Filing rule used below: a candidate is filed against a family only when a new instance of that family is incomplete without
  it. All sixteen candidates are mission-program lessons (supervising workers, measuring session corpora, gating a program),
  which none of the four product families covers, so every row reads `none`; therefore no row is PROMOTE-PROPOSED, and the
  two performance candidates (IC-D-03, IC-D-06) are HOLD under the frozen transfer rule above, never promoted on one corpus.

| candidate | family | verdict | reason |
|---|---|---|---|
| IC-U-01 | none | REJECT | a supervisor-side rule for deciding when a mission worker is refused; no product family's instance is incomplete without it (the nearest, persistent_state, is about destructive state and money, not about launching workers), so it has no CBR home and stays a UKDL proposal |
| IC-U-02 | none | REJECT | already a UKDL entry (duplicate of T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001); the install-versus-repository gap concerns the launch environment of a mission worker, not a product of any of the four families (web_surface covers the public deploy reaching HTTP 200, a different subject) |
| IC-U-03 | none | REJECT | a rule about naming the plane of a test run; it constrains how a failure is read, not what a product of a family must contain |
| IC-U-04 | none | REJECT | a hand-off procedure between machines of the program; no family product is incomplete without it |
| IC-U-05 | none | REJECT | a rule about the floor gate's baseline (tools/floor_regression_gate.py, this program's instrument); a CBR generation holds product rules, and this is the rule of an instrument that reads sessions |
| IC-U-06 | none | REJECT | a design rule for narrowed done-gates inside this program; not a product-family rule |
| IC-D-01 | none | REJECT | a rule for measuring session corpora, not for building a product of one of the four families; filing it against web_surface or persistent_state would put an instrument rule into a product baseline |
| IC-D-02 | none | REJECT | a measurement-honesty rule for a corpus instrument; no product family's instance is incomplete without it, and the unmeasured-is-not-zero stance is already a repository doctrine outside CBR |
| IC-D-03 | none | HOLD | a performance reading: the transfer rule applies and is not met, because the upper bound (8,773,728 weighted) comes from the KME-G smoke on GEX44 and the only other workload run, GEX44-B001, is the same kind of work on the same host, so no second materially independent workload exists (the KME-L laptop run, an Owner action, is the candidate); it also has no family today |
| IC-D-04 | none | REJECT | an instrument keying choice for a replay ranker (command text as the retry identity), resting on an unwindowed planning probe; not a product-family rule and not a guarantee |
| IC-D-05 | none | REJECT | the readiness reading of one preflight (a lapsed access token with a live refresh token), proven on scratch credentials only; no family's instance is incomplete without it |
| IC-D-06 | none | HOLD | a performance reading: the transfer rule applies and is not met, because KME-G and GEX44-B001 are both GEX44 workloads of the same kind of work, so the share driven by verifier subagents has no second materially independent workload; it also has no family today |
| IC-P-01 | none | REJECT | specific to this program's done-gate (R3 smoke versus primary roles); not a product-family rule and not a performance guarantee |
| IC-P-02 | none | REJECT | specific to this program's bundle and its R4 gate; not a product-family rule |
| IC-P-03 | none | REJECT | this bundle's labelling convention for laptop-plane commands; not a product-family rule |
| IC-P-04 | none | REJECT | a named debt of this program's done-gate, not a rule; nothing for a family to carry |

## Promotions recorded

none
