# Cognitive OS — CO-07 — Session Hibernation & Dedup

> A session that is idle, expensive, or waiting should not hold live context. **CO-07 lets a
> session freeze — serialize, compress, store, and destroy its active context — then restore
> on demand, byte-faithful.** Hibernation is how the kernel keeps the *number of hot sessions*
> low (the lever CO-08 enforces) without losing any session's work.
>
> EXTEND, not NEW: `modules/session_resilience/snapshot_versioning.py` already stores an
> incremental baseline+delta chain with integrity-validated reconstruction; `restore_guard.js`
> already dedups session restore on cold start. CO-07 adds the two missing pieces — *compression/
> archive* (snapshots are uncompressed JSON today) and *on-demand destroy-and-restore as a
> deliberate economy move* (today's snapshots are for crash recovery, not voluntary hibernation).

---

## Part I — The Hibernation Lifecycle

### I.1 Freeze → serialize → compress → store → destroy → restore

Hibernation is a six-step transition that takes a session from hot to cold and back:

- **Freeze.** The session's working set (CO-04 HOT) and resumable state (cwd, transcript sid,
  task, pending changes) are captured at a clean boundary — the same capture `work_state_saver`
  (M2) and `snapshot_versioning` (G3) already perform, here invoked *voluntarily* rather than only
  under pressure.
- **Serialize.** The frozen state is written to a durable form. G3's incremental baseline+delta
  chain is the serialization substrate; CO-07 reuses it.
- **Compress.** The genuinely new step. Today's snapshots live as uncompressed JSON lines; a
  hibernated session — which may sit cold for hours or days — is compressed for storage, reducing
  the COLD footprint (CO-04 External/Cold tier). Compression is lossless and integrity-anchored (a
  hash over the pre-compression state, checked on restore) so a corrupted archive is detected, never
  silently restored wrong (the G3 hash-mismatch-raises discipline).
- **Store.** The compressed, anchored archive is written to the COLD tier, indexed so the session can
  be found and restored.
- **Destroy active context.** The hot session's live context is released — this is the *point* of
  hibernation: the session stops counting against the global hot-session envelope (CO-08) and the
  60% ceiling. Crucially, destroy happens *only after* store is verified (store-then-destroy
  ordering), so there is never a window where the session exists in neither hot nor stored form.
- **Restore on demand.** When the session is needed, the archive is decompressed, integrity-checked,
  reconstructed (G3's exact reconstruction), and resumed via the existing `--resume <sid>` path. The
  Reality Contract: a restore is only "complete" when the G4 Recovery Acceptance Framework returns
  RECOVERED (HR-SESSION-RESILIENCE-001) — CO-07 inherits that gate; a restore that scores PARTIAL/
  FAILED holds the claim and enumerates what is missing.

### I.2 When to hibernate (the economy decision)

Hibernation is a *cost* move, decided by the economy (CO-01/CO-02) and the ceiling (CO-00):

- **Idle.** A session untouched for a threshold window while another session needs the hot-session
  budget → hibernate the idle one, free the envelope.
- **Expensive-and-waiting.** A session holding a large context while blocked (waiting on a long
  background task, a deploy, an Owner decision) → hibernate; its context is dead weight while it
  waits, and the freeze/restore cost is far below the cost of holding it hot.
- **Envelope pressure.** CO-08 needs to admit a new hot session but the cap is reached → the
  scheduler hibernates the lowest-priority hot session to make room, rather than refusing the new one
  or blowing the cap.

The decision is always cost-justified: hibernate when the cost of holding a session hot (context
against the ceiling + envelope occupancy) exceeds the freeze+restore cost. CO-01 prices both sides.

### I.3 The store-then-destroy invariant (durability)

The cardinal safety rule, inherited from the Session Safety Contract and the deploy doctrine (HR-005
backup-before-write): **never destroy live context before the hibernation archive is stored and
verified.** The ordering is freeze → serialize → compress → store → *verify store* → destroy. If any
step before verify fails, the session stays hot (fail-open toward keeping the session alive). This
guarantees hibernation can never lose a session — the worst case is a session that should have
hibernated stays hot (a missed economy, not a lost session). A `.jsonl` transcript is never part of
what destroy touches; the live conversation record is sacred (CO-06 III.2 lineage).

---

## Part II — Session Dedup

### II.1 The dedup problem and the existing coverage

Multiple restorers, reloads, and manual opens can spawn duplicate or overlapping sessions for the
same cwd — wasted hot-session budget and confusing state. The PP already covers part of this:
`restore_guard.js` dedups by session id and only cold-start-restores when zero live terminals exist
(preventing the reload-doubling that the persistent-sessions/tasks conflict caused), and
`build_pane_map.ps1` filters sub-sessions. The Reality Scan rated Session Dedup **EXISTS** — so CO-07
*reuses* it rather than rebuilding, and integrates it with hibernation.

### II.2 Dedup integrated with hibernation

CO-07's contribution is to make dedup *economy-aware*: a duplicate session is a candidate for
immediate hibernation or merge, not just suppression. When the kernel detects two sessions converging
on the same cwd/task, it keeps the one with the richer live state hot and hibernates (or declines to
restore) the other, recording the decision. Dedup and hibernation share the same identity anchor —
the transcript sid on disk (the SCS C28 dedup anchor that W2/W4 already use) — so there is one source
of truth for "is this session already alive" across restore, coordinate, and hibernate. The honest
limit (from the Reality Scan): the system cannot prevent the Owner from *manually* opening a second
terminal on the same repo — dedup covers the automated restore paths, and CO-08's scheduler + CO-10's
honest classification handle the manual case as a flagged, not silently-absorbed, event.

### II.3 Hibernation as the dedup resolution

The cleanest resolution to a detected duplicate is hibernation: rather than killing a session (which
risks losing work) or leaving both hot (which wastes budget), the kernel hibernates the redundant one
— its work is preserved in a verified archive, the hot-session budget is freed, and it can be restored
if it turns out to be genuinely needed. This makes dedup *non-destructive*: duplicates are folded into
cold storage, never discarded, consistent with the Session Safety Contract's durability invariant.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Corrupt archive on restore.** Compression or serialization corrupted the state. Detection: the
  integrity anchor (hash) mismatches on restore → G3 raises, the restore is refused, and the session
  falls back to the last-good archive or a fresh-with-checkpoint resume. Never a silently-wrong
  restore.
- **Destroy-before-store race.** A crash between destroy and store would lose the session. Prevention:
  the store-then-destroy ordering with verify makes this structurally impossible — destroy is gated on
  verified store.
- **Restore scores PARTIAL.** Some dimension (an editor pane, a host-unrestorable surface) cannot be
  reconstructed. Per G4, this is reported as PARTIAL with the missing dimensions enumerated, never
  upgraded to a false RECOVERED.
- **Hibernation thrash.** A session hibernated and restored repeatedly (mis-judged idle). Detection:
  freeze/restore churn on one session → raise its idle threshold / pin it hot; the freeze+restore cost
  is real (CO-01) and churn shows as wasted compute.
- **Stale hibernated session.** An archive whose cwd/branch moved under it. Detection: on restore, a
  premise check (the cwd exists, the branch matches) — a moved session restores into a flagged,
  verify-first state rather than blindly.

### III.2 Rollback protocol

CO-07 extends a crash-recovery system into voluntary hibernation; rollback returns it to crash-only:
(1) disable voluntary hibernation — snapshots revert to G3's pressure/crash-only capture (today's
baseline), the kernel loses the economy move but keeps recovery; (2) disable compression — archives
revert to uncompressed JSON (more COLD footprint, but no compression-corruption surface); (3) dedup
reverts to `restore_guard.js`'s standalone behavior. The fail-safe direction: keep sessions hot and
stored uncompressed — never a path that could lose a session. The store-then-destroy invariant holds
even during rollback.

### III.3 Integration contract

- **CO-08** — hibernation is the scheduler's primary tool: to admit a hot session over the cap, the
  scheduler hibernates the lowest-priority hot one. CO-07 provides freeze/restore; CO-08 decides who.
- **CO-00 / CO-01 / CO-02** — hibernation frees context (ceiling) and envelope (budget); the decision
  is cost-justified by CO-01's pricing of hot-hold vs freeze+restore.
- **CO-04** — a hibernated session is a whole-session demotion to COLD/External; CO-04's tiers define
  what serializes.
- **CO-06** — old hibernation archives beyond retention are GC'd (compressed-and-cold, then pruned if
  never restored), never the live transcript.
- **`/kclear` `/compact` `/clear`** — `/kclear` writes a hibernation checkpoint first (nothing lost on
  reset); a restored session resumes via `--resume`; `/clear` is a task-boundary that may trigger
  hibernation of the finished task's session.
- **Session Resilience (G1–G6) / Cursor** — CO-07 reuses G3 (snapshot), G4 (acceptance gate), the
  restore_guard extension, and the pane map; restore surfaces through the PP Sessions panel.

### III.4 Anti-patterns (forbidden)

- **Destroy before verified store.** The one ordering that could lose a session. Structurally forbidden.
- **Claiming RECOVERED without G4.** A restore is complete only on a RECOVERED verdict (HR-SESSION-
  RESILIENCE-001).
- **Compressing without an integrity anchor.** A restore that could be silently wrong.
- **Killing a duplicate session.** Dedup resolves by hibernation (non-destructive), never by discarding
  work.
- **Hibernating the .jsonl transcript away.** The live record is sacred; hibernation archives derived
  state, never destroys primary history.

---

### CO-07 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Freezes/compresses/stores a session and frees its hot context, restorable byte-faithful | On a cost-justified hibernation decision | — |
| store-then-destroy: live context is released only after the archive is stored AND verified | Always | A session is never lost; worst case it stays hot (missed economy) |
| Restore is complete only on a G4 RECOVERED verdict; PARTIAL enumerates misses | Always | Full restore of host-unrestorable surfaces (reported PARTIAL, not faked) |
| Dedup resolves duplicates by hibernation (non-destructive), sharing the transcript-sid anchor | Automated restore paths | Coverage of a manually-opened duplicate terminal (flagged, not absorbed) |
| Rollback returns to crash-only snapshots without losing sessions | On misbehavior | — |

**Guarantee level (honest):** CO-07 is a *durability-first economy* layer — it frees hot resources by
moving sessions to verified cold storage, never risking loss (store-then-destroy). It cannot restore
host surfaces the host cannot reconstruct (G4 PARTIAL) nor dedup a manual terminal open (CO-10 flags
it). *Sealed under SCS C61.*
