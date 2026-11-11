# S26C plan: first legitimate certification on the recovered KSR stage (PROPOSED 2026-11-11T15:45Z)

Status: AWAITING OWNER APPROVAL. Nothing below is executed. Coordinator pane ddf4990e (laptop).
Brief: the Owner's pasted message in ddf4990e (decisions 1 SI / 2 NO / 3 SI-fallback), replying to the S25 status.
Named S26C because pane d957c937 already used S26 (type lifting, CHECKPOINT_COMPLETE) and S26B (running).

## 1. Reality scan (GEX44, 15:40-15:41Z)
| fact | state |
|---|---|
| m-97b5a3985b92 (S25) | COMPLETED, closed by pane d957c937 at ~14:43Z. Its ~21M remainder is not live authority. |
| m-077596a9935d | RUNNING, authority 31.5M, spend 15.09M (16.4M left). S26 done (14.41M; nothing certified). S26B retargeted 15:40:05Z (Owner "y a todo" 15:37Z in d957c937), caps <= 9M, fresh 0. Worker 8ed0079c. |
| Canonical KSR certifier | `modules/recon_fabric/ksr_lane.py` `cmd_certify` + `certify.decide`. Hard-wired STAGE_ID ksrmb-20261001-101754, GEN ksr-v5r, CERT_DIR evidence/cert1-ksr, per-object arm (FLAGS_SPLIT certifies nothing). |
| Recovered stage | /home/kobii/ksr_stage/ksrmb-s25-20261111-140212, manifest sha 396511350197. G-NT1: 2,837 TARGET_PRESENT, 1,690 COMPILES, 582 exact canonical arm, 699 any arm, 21 still NO_TARGET. |
| Protected | receipts 02c80ae3/8687, pinned tree eb0c92b4, ksr-frontier, cert1*, Tennis certificates. |

## 2. Identity design (decision 1, items 2 and 5)
- **Stage identity:** the stage dir plus its manifest sha.
- **Context identity:** the prelude sha, the m2c results sha and the arm flags. These are the same as the historical profile and are verified, not assumed.
- **Profile identity:** a new GEN `ksr-v5r-s25stage`.
- `ksr_lane.py` gets an explicit `PROFILES` table. The historical profile stays the default and is byte-identical in behavior. The new profile carries:
  - the Owner turn that authorized it;
  - its own lane, cert and frontier dirs (`evidence/ksr-lane/ksr-v5r-s25stage`, `evidence/cert1-ksr-s25stage`, `evidence/ksr-frontier-s25stage`);
  - its own counters.
- An unknown profile name is refused.
- Same `certify.decide`, same controls, same A2 negatives, same per-object arm rule. No second certification system.
- **R2 is not opened.** The new receipts count under their own profile. Merging them into the 8,687 KSR headline is an Owner act.

## 3. Phases (processed caps; fresh 0, all deterministic compile/compare; USD 0)

| Phase | Content | Cap |
|---|---|---|
| C0 | Reconcile 2,858 vs 2,837: name the 21 and their real disposition. Commit the identity spec. | 1.5M |
| C1 | Independent target oracle. For every target symbol, the function bytes in the stage object must equal the original DOL bytes at `main:<ADDR>`. Relocation fields are masked from the DOL's own relocation data, never from the candidate source. Controls: a known pinned-stage function (positive) and a shifted-address mutant (negative). **A failure here stops S26C with nothing certified.** | 2.5M |
| C2 | Minimal profile extension in `ksr_lane.py` (see §2). Gates: positive/negative controls, mutants (unknown profile, wrong manifest sha, historical dir write, counter merge), rollback (revert = historical byte-identical), and every prior gate (S21–S26B, FRONTIER_CHECK, KSR_FRONTIER_CHECK, receipts sha). | 3.5M |
| C3 | Frozen pilot of 25 canonical-arm exact candidates. The seed is drawn after the freeze commit. Full `cmd_certify` path under the new profile: bytes, relocations, toolchain identity, structural consistency. The coordinator re-runs it independently. **Pilot = 0 certified, or any control violation → stop before expansion.** | 1.5M |
| C4 | Expansion toward the 582 in batches (100 / 200 / rest), with controls and regression re-run between batches. Any violation halts. The 699 any-arm population is evaluated separately: only the object-chosen arm counts, never per-function, and it is never summed as a disjoint population. | 3M |
| C5 | `?` repair as fallback only: it applies only when the normal compile fails. Dependency check on the material units, and a byte check that 0 of the 178 already-certified functions change. The 87 stay candidates unless they pass the full profile path. | 2.5M |
| C6 | FLAGS_SPLIT: read-only investigation of whether per-function flags can be authentic under CodeWarrior's real units. Proposal only. | 1M |
| C7 | Checkpoint. Separate counts: object recovered / compiles / experimental exact / structurally valid / canonically certified (new profile) / cost per new certification / regressions. Defects and patterns go to UKDL candidates. | 1M |
| Reserve | Closeout | 1.5M |
| **Total** | | **18M processed, 0 fresh** (under the ~21M ceiling) |

## 4. Stop rules
- Hitting a phase cap or the total ends the phase or S26C.
- C1 not proven → stop.
- C2 controls not clean → stop.
- Pilot failure → stop.
- Any regression in the historical counters, receipts or frontiers → immediate hold.
- The same lever failing twice → retire it.
- Wall: the earlier of 2026-11-12T14:48Z (record) and 2026-11-12T16:40Z.

## 5. Not authorized
- Changing `certify.decide` truth conditions.
- Writing to historical receipts, frontiers or pinned stage.
- Opening R2.
- Merging counters.
- Per-function FLAGS_SPLIT.
- A global `?` rewrite.
- Push, paid use, a live CPP deploy, or budget beyond what is approved.

## 6. Owner decision (budget and sequencing)
The ~21M the brief refers to belonged to the closed S25 record. The live record has 16.4M left, and S26B claims up to 9M of it, so S26C (18M) does not fit without one of these:
- **(a) Recommended:** pause S26B (hold) and run S26C on m-077596a9935d within its 16.4M. That covers C0–C5 plus C7 (15.5M, 0.9M reserve); C6 is deferred. S26B resumes only if budget remains. This needs no new authority. Pane d957c937 must be told.
- **(b)** Let S26B finish, then arm S26C as a new record with authority 18M (≤21M). This is a new authority act.
- **(c)** Let S26B finish, then run S26C in whatever remains (≥7.4M): C0–C3 only (pilot), with expansion at a later gate.
