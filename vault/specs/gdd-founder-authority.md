---
covers: [gdd-founder-authority, goal-founder-signature, goal-adopt, record-gates-signature, F2, F3-licence]
status: APPROVED-BY-PLAN (kseip-p8-gdd-resident-20260924, audit fix F2)
owner: LANE GDD (PP worktree factory/gdd)
---

# GDD slice 1 — Founder authority is a signature, not a label

## Problem (measured 2026-09-24)
`contract.declare/revise` default `actor="founder"`; `set_authority`, `set_budget` and
`sweep.set_autonomous` accept any actor string; the autonomy licence (`autonomy_gates.json`) is a
plain file in the state dir. The log's hash chain is keyless, so any principal that can write the
goal directory can append a "founder" event, rewrite history wholesale, or forge the licence.
A resident process that writes the store could therefore grant itself autonomy and authority.

## Decision
Founder-class events carry an Ed25519 signature by a key the resident cannot read, checked on
projection (not only on append — the file can be written without the API). Stdlib has no asymmetric
signatures; `cryptography` is present on both hosts (Win 49.0.0, GEX44 system python 41.0.7). If it
is missing, authority mode is UNVERIFIABLE and the resident must refuse — never a silent pass.

## Contract
1. FOUNDER_CLASS event types: goal.declared, goal.revised, goal.budget_set, goal.authority_set,
   goal.autonomous, goal.paused, goal.resumed, goal.tier_set, goal.decision_answered, goal.adopted.
2. Trust anchor: a public-key file named by env `GSDX_FOUNDER_KEYS` (JSON: key_id → {role, public
   key}). Roles: `founder`, `judge`. Modes:
   - ABSENT — no file: legacy behaviour, reported as "founder authority unverified".
   - UNPROTECTED — file present but writable by the current process (POSIX `os.access W_OK`, or any
     Windows file): signatures checked, but the anchor is not a boundary; reported as such.
   - ENFORCED — present and not writable by the reader.
   - UNVERIFIABLE — present but the crypto library is missing or the file is unreadable/malformed.
3. Signing: the signed message is the canonical JSON of {repo, goal, seq, type, data-without-_founder,
   prev_digest}; the signature and key_id live in `data["_founder"]`. The private key path comes from
   env `GSDX_FOUNDER_SIGNING_KEY` (PEM). Appending a founder-class event in any mode other than ABSENT
   without a usable signing key raises (named error) and writes nothing.
4. Verification on projection (modes UNPROTECTED/ENFORCED): after a goal's FIRST validly signed
   founder event, every later founder-class event must carry a valid `founder`-role signature, else
   projection raises GoalLogCorrupt with reason FOUNDER_SIGNATURE_INVALID and the seq. Events before
   the first signed one are legacy, attested by the chain (the signed event binds prev_digest).
   A signature by an unknown key_id or a `judge`-role key on a founder event is invalid.
5. Adoption: `goal.adopted` (founder-class, signed) is how an existing unsigned goal becomes governed.
   `is_governed(state)` = at least one validly signed founder event. The sweep/resident must refuse an
   ungoverned goal whenever the mode is not ABSENT, with a reason naming `adopt`.
6. Licence: `record_gates` signs its payload with the `judge`-role key (env
   `GSDX_JUDGE_SIGNING_KEY`); `autonomy_verdict` in modes UNPROTECTED/ENFORCED requires a valid judge
   signature over the record, else refuses ("the licence is not signed by the judge"). ABSENT keeps
   today's behaviour.
7. CLI: `founder-keygen --out PATH --role founder|judge` (private PEM 0600 + prints the public line to
   add to the anchor), `adopt --goal G`. (Other verbs are slice 2.)
8. No secret material is ever printed or logged; key_ids are short hashes of the PUBLIC key.

## Proof (tools/test_gsd_x_goal_authority.py, V-AUTH-*; both poles each)
- signed founder event accepted; unsigned founder event after adoption refused on projection;
  forged signature / wrong key / judge-role key on a founder event refused; control: a non-founder
  event (e.g. obligation) needs no signature.
- append of a founder-class event without a signing key raises and writes nothing (mode ENFORCED).
- history rewrite before a signed event → chain/signature failure (not silent).
- ungoverned goal → sweep refuses naming `adopt`; after adopt → admitted.
- licence: unsigned record refused under ENFORCED; judge-signed record accepted; founder-signed
  record refused (wrong role).
- modes: ABSENT/UNPROTECTED/ENFORCED/UNVERIFIABLE each reported; ENFORCED needs a real POSIX
  permission drill → runs on GEX44 (on Windows that case reports UNJUDGED, never PASS).
- existing suites unchanged in ABSENT mode (regression).
- goal mutation drill gains entries: signature check skipped; adoption rule skipped; licence
  signature skipped — each must be caught by its named gate.

## Rollback
Unset `GSDX_FOUNDER_KEYS` → ABSENT mode = today's behaviour. No stored data is rewritten.
