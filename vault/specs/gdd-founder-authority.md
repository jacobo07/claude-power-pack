---
covers: [gdd-founder-authority, goal-founder-signature, goal-adopt, record-gates-signature, F2, F3-licence, founder-relay, founder-sign, founder-apply, goal-head]
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
   - UNPROTECTED — file present and valid, but something is not a boundary against the current
     process: the anchor is writable (POSIX `os.access W_OK`, or any Windows file), is itself a
     symlink, or its directory — as NAMED (unresolved) or as resolved — is writable; or the witness
     (§9) is unset, a symlink, or writable (same rule). Signatures are checked; the detail names what
     is exposed (`ANCHOR_WRITABLE`, `WITNESS_UNSET`, `WITNESS_WRITABLE`).
   - ENFORCED — anchor AND witness directory both present and out of the reader's reach.
   - UNVERIFIABLE — present but the crypto library is missing or the file is unreadable/malformed.
3. Signing: the signed message is the canonical JSON of {repo, goal, seq, type, data-without-_founder,
   prev_digest, ts, actor}; the signature and key_id live in `data["_founder"]`. `ts` and `actor` are
   fixed before signing and stored exactly as signed, so editing either breaks the signature
   (BAD_SIGNATURE). The private key path comes from env `GSDX_FOUNDER_SIGNING_KEY` (PEM). Appending a
   founder-class event in any mode other than ABSENT without a usable signing key raises (named
   error) and writes nothing.
4. Verification on projection (modes UNPROTECTED/ENFORCED): after a goal's FIRST validly signed
   founder event, every later founder-class event must carry a valid `founder`-role signature, else
   projection raises GoalLogCorrupt with reason FOUNDER_SIGNATURE_INVALID and the seq. Events before
   the first signed one are legacy, attested by the chain (the signed event binds prev_digest).
   A signature by an unknown key_id or a `judge`-role key on a founder event is invalid.
5. Adoption: `goal.adopted` (founder-class, signed) is how an existing unsigned goal becomes governed.
   `is_governed(state)` = at least one validly signed founder event. The sweep/resident must refuse an
   ungoverned goal whenever the mode is not ABSENT, with a reason naming `adopt`.
   An adoption vouches for every unsigned event before it, so it is never signed unseen: the library
   `adopt(log, actor, attest_digest, reason)` takes a REQUIRED `attest_digest` and signs only if it
   equals the log's current last-event digest (else "the history changed since review", nothing
   written). The CLI `adopt` without `--attest-digest D` prints the goal's founder-class events (seq,
   type, actor, one-line data summary), the resulting autonomy / authority / budget / paused state and
   the current last digest, and exits 2 with "review, then re-run with --attest-digest <digest>".
6. Licence: `record_gates` signs its payload with the `judge`-role key (env
   `GSDX_JUDGE_SIGNING_KEY`); `autonomy_verdict` in modes UNPROTECTED/ENFORCED requires a valid judge
   signature over the record, else refuses ("the licence is not signed by the judge"). In those modes
   it also refuses when either head (the record's or the tree's) is empty — an unknown head is not
   permission. The signed payload carries `licence_seq` = the witnessed value + 1 (the previous
   record's when no witness holds one), and `record_gates` writes `<witness>/licence.json` =
   {licence_seq, head} after the record. With a witness configured, a record whose licence_seq or head
   differs from the witnessed one is refused as LICENCE_STALE (an older signed licence replayed over a
   newer one), and no witnessed licence at all is LICENCE_UNWITNESSED. ABSENT keeps today's behaviour
   (no licence_seq, no head or witness checks).
7. CLI: `founder-keygen --out PATH --role founder|judge` (private PEM 0600 + prints the public line to
   add to the anchor), `adopt --goal G [--attest-digest D]`. (Other verbs are slice 2.)
8. No secret material is ever printed or logged; key_ids are short hashes of the PUBLIC key.
9. Witness (high-water mark). A signature binds its predecessor, never its successor, so deleting the
   newest event files leaves a valid chain and silently rolls back the founder's last decisions
   (re-enabled autonomy, older authority/budget, an undone pause). Env `GSDX_FOUNDER_WITNESS` names a
   directory outside the resident's write reach. Whenever a founder-class event is signed and
   published, `GoalLog.append` writes `<witness>/<repo>/<goal>.json` = {repo, goal, seq, digest}
   (atomic tmp + replace; never lowered). If that write fails after publishing, append raises naming
   the unwitnessed seq. In checking modes with a witness configured:
   - projection (`contract.project` → `authority.check_witness`) refuses with GoalLogCorrupt
     FOUNDER_ROLLBACK when the log holds no event at the witnessed seq, or holds it with another digest;
   - a GOVERNED goal with no witness file is refused as FOUNDER_WITNESS_MISSING (the resident cannot
     write the witness, so a missing mark means never witnessed, not safe); an ungoverned legacy goal
     needs none. Migration for a goal signed before the witness existed: the founder re-signs any
     decision (e.g. re-states the current budget), which writes the mark;
   - an unreadable or foreign mark is FOUNDER_WITNESS_UNREADABLE, never "no witness";
   - `append` of a founder-class event checks the mark first, so the founder cannot sign atop a
     truncated log (which would ratify the rollback).
   Residuals, stated rather than implied: (a) the mark is read-then-replaced, not compare-and-swapped,
   so two founder writers interleaving on ONE goal (A publishes N, B publishes N+1 and marks it, A's
   late write marks N) can leave the mark one event low, and that last event is unwitnessed until the
   next founder write — this fails OPEN for one event and needs two concurrent founder signers;
   (b) truncating NON-founder events after the last founder event is not detected by the witness; they
   carry no founder decision; (c) the witness directory's own subdirectories are created by the
   signer, and only the named witness directory is checked for writability.

10. Relay (GDD slice 2): a founder decision signed on one host, appended and witnessed on another.
   Production topology (measured 2026-09-24): the founder PRIVATE key lives only on the Windows
   workstation; the goal store `/var/lib/kobii-factory/goals` is owned by `factory` (the resident);
   the witness `/var/lib/kobii-factory/witness` is writable only by `factory-judge`; the anchor
   `/etc/kobii-factory/founder_keys.json` is root 0444. No single process holds the key AND can write
   the witness, so `GoalLog.append` cannot sign-and-witness a founder event anywhere. The relay splits
   it into three verbs, in this order:
   - **head** (GEX44, any reader of the store, writes nothing): `gsd_x_goal.py head --goal G
     (--repo ID | --root PATH)` prints JSON `{kind, repo, goal, seq, digest}` — the last event's seq
     and digest after `GoalLog.read()` has verified the whole chain (an empty log is `seq 0`, digest
     GENESIS). It does NOT project, so it works on a log the resident refuses; the refusal is then
     the apply's to make.
   - **founder-sign** (workstation, holds `GSDX_FOUNDER_SIGNING_KEY` and a copy of the public anchor
     in `GSDX_FOUNDER_KEYS`): `founder-sign --head FILE | (--repo --goal --seq --prev-digest)
     --type T (--data JSON | --data-file F) [--actor A] --out ENVELOPE` writes, exclusively (never
     overwrites), the envelope `{kind:"gsdx-founder-envelope/1", repo, goal, seq, prev_digest, type,
     data, ts, actor, key_id, sig}` with `seq = head seq + 1` and `prev_digest = head digest`. `data`
     excludes `_founder`; `key_id`/`sig` are exactly the block `authority.sign_event_data` makes, so
     the signature is byte-identical to what `GoalLog.append` would have stored for the same
     (repo, goal, seq, type, data, prev_digest, ts, actor) — Ed25519 is deterministic and the suite
     re-signs to prove it. Refused at sign time, nothing written: a type outside FOUNDER_CLASS
     (ENVELOPE_TYPE_NOT_FOUNDER); ABSENT or UNVERIFIABLE anchor; data that is not an object or carries
     `_founder`; seq 1 that is not `goal.declared`, or `goal.declared` at any other seq; a
     declared/revised payload whose `revision` is not `revision_of(semantic)` (a signed malformed
     declaration could never be removed). The private key is never printed.
   - **founder-apply** (GEX44, run as `factory-judge`): `founder-apply --envelope FILE`, in order:
     (1) load the anchor — ABSENT or UNVERIFIABLE is refused; (2) verify the envelope's signature
     against a FOUNDER-role anchor key over exactly (repo, goal, seq, type, data, ts, actor,
     prev_digest) — BAD_SIGNATURE / WRONG_ROLE (a judge key) / UNKNOWN_KEY, all under
     FOUNDER_SIGNATURE_INVALID; (3) the log's current last seq/digest must equal envelope seq-1 /
     prev_digest, else STALE_ENVELOPE (the Founder re-runs head and re-signs); (4) the witness mark
     (`check_witness`, rollback refused exactly as in `append`); (5) `GoalLog.append_presigned`, the
     one narrow path for a pre-signed event: it re-reads the log, repeats the seq/prev_digest and
     signature checks against what it read, and publishes through the SAME `publish` (tmp + fsync +
     `os.link` compare-and-swap) and the same witness write as `append`; (6) the mark is raised.
     Every refusal writes nothing. Replaying an applied envelope is STALE_ENVELOPE (the log has moved
     past its seq) and writes nothing.
   Concurrency: the goal log has no lock file; writers are serialised by `os.link` refusing an
   existing sequence name. The resident (`factory`) and the relay (`factory-judge`) therefore append
   safely side by side: whichever loses a sequence number gets LostRace and nothing it wrote is
   visible (the relay reports it as STALE_ENVELOPE). This holds only if BOTH users can create files in
   the goal directories — see the permission requirement below.
   **Permission requirement (not applied by this slice; the coordinator does it on GEX44):** every
   directory under `/var/lib/kobii-factory/goals` must be group `factory`, mode `2770` (group-writable,
   setgid so new files and subdirectories inherit group `factory`), and BOTH `factory` and
   `factory-judge` must run the goal tools with `umask 0007`, so a directory one of them creates (a new
   goal's dir on `goal.declared`, the `runs/` dir) stays writable by the other and every event file is
   group-readable. Without it, `founder-apply` as factory-judge fails at publish with a
   PermissionError, reported as Inconclusive (nothing published), never as success.
   What the relay does NOT protect, stated rather than implied: (a) `founder-apply`'s own checks run
   as the witness writer, whose anchor mode is UNPROTECTED by design (WITNESS_WRITABLE), so they are
   an early refusal, not the boundary — the boundary is the resident's projection, which re-verifies
   every founder event under its own ENFORCED view; (b) an envelope is a bearer decision: whoever
   holds the file can apply it (only once, and only on the head it was signed against) — it grants
   nothing the Founder did not sign, but WHEN it lands is the carrier's choice until it goes stale;
   (c) the envelope's `ts` is the workstation clock, signed as-is; nothing orders it against the
   GEX44 clock; (d) a factory-judge that is itself compromised can write the witness and the store
   (after the permission change) — it still cannot forge a founder signature, but it can truncate and
   re-witness, which the witness cannot catch because it IS the witness writer.

## Adversarial cases the review (129ac4c, 2026-09-24) added, and where each is closed
- tail truncation rolls back signed founder decisions → §9 FOUNDER_ROLLBACK.
- licence replay / empty head → §6 LICENCE_STALE, LICENCE_UNWITNESSED, "unknown head".
- adopt signs planted unsigned history unseen → §5 review + attest digest.
- signature did not cover actor/ts → §3.
- symlinked anchor in a writable dir read ENFORCED → §2 (symlink and unresolved parent).

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
- truncation after a later signed disable → FOUNDER_ROLLBACK, and the founder cannot sign atop it;
  controls: the untouched log projects (disabled), and without a witness the same truncation
  silently re-enables autonomy (the attack is real, not hypothetical).
- governed goal with no witness file → FOUNDER_WITNESS_MISSING; controls: a witnessed goal and an
  ungoverned legacy goal project.
- licence: record-gates advances licence_seq and witnesses it; an older signed licence replayed →
  LICENCE_STALE; unwitnessed → LICENCE_UNWITNESSED; empty head (record or tree) refused; controls:
  the witnessed licence / the real head are accepted.
- adopt without attest → exit 2 with the listing, nothing written; stale digest → refused, nothing
  written; correct digest → adopted. Library `adopt(..., "")` refused.
- tampered ts or actor on a signed event (re-chained) → BAD_SIGNATURE; control: untouched.
- POSIX-only (UNJUDGED on Windows or as root): ENFORCED; protected anchor with unset or writable
  witness → UNPROTECTED naming it; symlinked anchor → not ENFORCED.
- goal mutation drill gains entries: signature check skipped; adoption rule skipped; licence
  signature skipped; witness check skipped; licence_seq check skipped — each must be caught by its
  named gate.

## Proof of the relay (tools/test_gsd_x_goal_relay.py, V-RELAY-*; each red branch with a control)
- head → sign → apply appends, projects governed with the signed budget, and the stored data equals
  what `sign_event_data` makes for the same fields (byte-identical signature).
- tampered data / ts / actor / seq / prev_digest → refused, event count unchanged; wrong key (judge
  signing a founder event, a key not in the anchor) → refused; non-founder type → refused at sign time;
  stale envelope (log advanced after head) → STALE_ENVELOPE; replay → STALE_ENVELOPE, nothing written;
  apply under ABSENT / UNVERIFIABLE → refused; the witness mark rises to the applied seq; a
  pre-signed event with a bad signature is refused by `append_presigned` itself (not only by the relay).
- the CLI verbs head / founder-sign / founder-apply drive the same path end to end.
- mutation drill entries: relay skips the prev_digest check; `append_presigned` skips signature
  verification — each caught by its named gate.

## Rollback
Unset `GSDX_FOUNDER_KEYS` → ABSENT mode = today's behaviour. No stored data is rewritten.
