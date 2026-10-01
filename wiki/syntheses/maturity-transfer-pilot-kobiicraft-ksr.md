---
type: synthesis
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-kobiicraft-capability-harvest, 2026-10-01-ksr-maturity-profile, 2026-10-01-cbr-external-research]
---

# Maturity-transfer pilot: KobiiCraft → KobiiSports Resort

**Question (Owner, 2026-10-01):** can a mature system raise the maturity of other software, and
brainstorm features for it, beyond lessons? Pilot pair chosen by the Owner: KobiiCraft (source)
→ KobiiSports Resort (target). Concept: [[maturity-transfer]].

**Method.** Two read-only agents, blind to each other, using one shared taxonomy:
- One harvested 50 capabilities from KobiiCraft source @ `7f8f9d66`
  ([[2026-10-01-kobiicraft-capability-harvest]]).
- The other profiled KSR's traits, 41 existing capabilities and 24 self-recorded gaps @ `14f7840`
  ([[2026-10-01-ksr-maturity-profile]]).
- I spot-checked both sides in source (below), then did the trait-matched diff myself.

The diff is therefore **not** blind. The convergence figures below are interpretation, not
evidence.

## Result in one paragraph

Maturity transferred, but not where expected. It moved as **principles, not code**: almost no
KobiiCraft code is reusable, because it is Pterodactyl- and mineflayer-shaped. Its *portable forms*
mapped onto 19 of KSR's 24 self-recorded gaps.
- **Strongest single transfer:** KobiiCraft's world-persistence invariants map exactly onto a
  silent player-data loss path in KSR's save code.
- **Where the transfer landed:** most of it landed on KSR's **dev/infra plane** (GEX44 dispatcher,
  harness, toolchain), not the game. KSR is "not a live service" as a product, but its
  infrastructure is one. So traits must be judged **per plane**.
- **Feature brainstorming was the weakest result:** only 4 product-level (L5) ideas, all Owner
  decisions.
- **Transfer ran both ways:** KSR holds capabilities KobiiCraft lacks, and KobiiCraft's own CI
  breaks its own core doctrine. Maturity is not a scalar.

## Verified in source

| claim | where | verdict |
|---|---|---|
| KSR save: any failed validation (short read, bad magic, version >10) zeroes the profile with no log on that branch; the next save overwrites the file in place, no checksum, temp or backup | KSR `tools/caddie/src/main.cpp:1443-1445, 1498-1500, 1555-1565` | **confirmed** |
| KobiiCraft codifies the opposite: write temp → verify → publish atomically; quarantine, never regenerate, "indistinguishable from griefing to the player" | KC `scripts/network/world_persistence_gate.py:7-16` | **confirmed** |
| KobiiCraft CI fails when zero tests ran | KC `.github/workflows/ci.yml:49` | **confirmed** |
| KobiiCraft CI silently skips a gate whose script does not exist | KC `ci.yml:52-59` (`run.sh` absent) | **confirmed** |

## Proposals for KSR, ranked

Rank = how directly it closes a gap KSR itself recorded × cost.
- All are **proposals**. Nothing was changed in either repo.
- KSR is under an Owner STOP since 2026-10-01 (all four missions halted), so these are inputs to
  that backlog, not actions.

| # | proposal | from KC | closes KSR gap | cost |
|---|---|---|---|---|
| P1 | **Save integrity.** CRC over the save (KSR already has a CRC32 in `kobii_klog.cpp:327-331`). Two-slot or write-temp-then-publish. On a failed load, keep the bad file aside (e.g. `kobii.bad`) and log the branch; never `memset` and then overwrite. | KC-27 | G17 (silent coin/rank loss) | S |
| P2 | **Boot admission gate.** One pure preflight before spending a GEX44 slot or a silicon boot: delivery identity MATCH, silicon-safety PASS, size gate, host headroom, a provenance receipt beside the WBFS. Result is APPROVED or NO_BOOT naming every failed gate. Caddie prints its build id at boot, and the harness asserts it. | KC-37, KC-33, KC-07, KC-21 | G05 stale disc 6 weeks, G06 no release manifest, G10 RAM 1121/2048 MB, G22; unifies KSR-24/26/36, which today are manual and scattered | M |
| P3 | **Status that cannot lie.** Supervised and scheduled work reports RUN status separately from MISSION status. Empty selection or an absent subject = CANNOT_EVALUATE, never PASS and never BLOCKED. One synthetic job heartbeat. Detection separate from remediation. | KC-17, KC-43/44 | G08 dispatcher RUNNING while INACTIVE, G09 executor manifest lies, G12 false BLOCKED_DELIVERY | S-M |
| P4 | **Ceiling check before archaeology.** Before a wave spends scarce slots on evidence, compute whether even a perfect answer, at both ends of its bracket, would change a critical-path decision. | KC-50 | G21 (W5-W17 spent off the critical path) | S |
| P5 | **Reproducible toolchain host.** Phased, abort-on-fail, skip-if-present provisioning including devkitPPC; host scripts versioned. | KC-49 | G01 (16 of 27 backlog rows blocked on toolchain, KSR-B-031), G07 | M |
| P6 | **CI for what runs today, plus a change→verifier registry.** Run KSR's existing tooling tests and gates in CI with a zero-tests tripwire. Map changed module areas to their required verifier (AT_CANARY, silicon, or "none" with a written reason); an unmapped change fails. | KC-19, KC-02 | G02 no CI, G04 test mode changing the unit under test | M |

Second tier, infra/dev plane: phase-reached journey reporting with positive controls (KC-15 → G03,
G19), bounded drill waits with typed endings (KC-16 → G11), restart proof by a counter that only
goes backwards (KC-22 → G16), scheduled jobs with stale-lock reclaim (KC-10 → G10 `ksr_prune.sh`
never scheduled), budgeted LLM router with probed liveness (KC-46 → G09), commit tooling plus
`.gitattributes` for multi-pane work (KC-01/06/20 → G23), drift-not-debt gates over the 222-system
gap registry (KC-24), log recurrence memory (KC-09). Secret hygiene (KC-29): KSR has Hetzner Robot
credentials, but the profile did not assess this, so it stays unknown.

## Feature brainstorm (L5): Owner decides

Grounded in what KobiiCraft built for its players. Each is a product question, not a gap.

- **Cosmetics-only coin sink.** KSR's shop is "future UI" (`main.cpp:1131-1133`); KobiiCraft sells
  only cosmetics, coins earned in play (KC-41).
- **Couch-play fairness modules.** Comeback balancer, family-play mode, sportsmanship, seasonal
  rituals for the ranked ladder (KC-41 module names; contents not read).
- **Spanish localization** with operator overlay and per-key fallback (KC-47), with a quality gate
  that refuses to guess ambiguous words (KC-26). KSR HUD strings are hard-coded English
  (`main.cpp:6090`).
- **Readable refusal at boot** for a wrong disc or region, instead of a crash (KC-12). *Hypothesis:*
  not checked whether the loader already does this.

## What did not transfer, and why

| KC | why not |
|---|---|
| KC-13 economy balancer | needs many concurrent players in one economy; KSR coins are local |
| KC-05 desired-state repair via owner API | no live config surface owned by another process |
| KC-40 chat-filter self-sanity | no moderation surface |
| KC-14 shim drift guard | no shim-collapse history |
| KC-18 praxis guard | broken at the source (CI skips it) |
| KC-23 ownership-aware rollback | no seeded data to roll back |
| KC-32 load percentiles | Dolphin timing is not hardware timing; would mislead on a constrained target |
| KC-34 publish quarantine, KC-38 launch rehearsal, KC-48 landing headers | no publishing, launch event or web surface |
| KC-39 vocabulary lint | no stated vocabulary constraint |
| KC-04 N-run repeatability | conditional: scarce boot slots make N runs expensive |
| KC-28, KC-30, KC-36, KC-08 | low value or unassessed for KSR |

**Already present in KSR:** KC-03 (silicon-safety / PAL symbol gate), KC-11 (crash handler, FZDIAG,
KLOG), KC-25 (evidence-graded frontier), KC-31 (gx mutation ledger), KC-35 (genomic_lint), KC-42
(tested job commands), and partly KC-21 (md5-shielded deploy). KC-45 (GEX44 state machine) is
probably **shared infrastructure**, not a transfer (unchecked).

Tally of the 50, by id:
- 12 feed P1-P6: KC-02, 07, 17, 19, 21, 27, 33, 37, 43, 44, 49, 50.
- 11 second tier: KC-01, 06, 09, 10, 15, 16, 20, 22, 24, 29, 46.
- 4 product questions: KC-12, 26, 41, 47.
- 7 already present or shared: KC-03, 11, 25, 31, 35, 42, 45.
- 16 non-transfers: KC-04, 05, 08, 13, 14, 18, 23, 28, 30, 32, 34, 36, 38, 39, 40, 48.

## Reverse transfer: KSR → KobiiCraft

- KSR has capabilities KobiiCraft's harvest did not show:
  - a slot ledger whose balance is derived, never stored (KSR-16);
  - an evidence-durability gate (KSR-11);
  - claim-separation lint over an evidence-graded frontier (KSR-41);
  - flags that compile to zero bytes when off (KSR-25);
  - a three-valued delivery-identity verdict (KSR-26).
- KobiiCraft's CI skips its missing praxis guard, which KSR's own lesson G12 ("gates must report
  INCONCLUSIVE when their subject is absent") would catch.
- Its Python gates are not in CI, and its backups have no restore drill.

## What the pilot says about the mechanism

1. **Traits are per plane.** Product and dev/infra planes must be profiled separately. 11 of the 23
   transfers (KC-02, 09, 10, 15, 17, 21, 22, 24, 43, 44, 49) list T-LIVE-SERVICE as an enabling
   trait, so a product-only trait match would have rejected them, because KSR the game is offline.
2. **Portable form is the unit, not code.** This matches the research: abstracted procedures
   transfer, detailed trajectories do not ([[2026-10-01-cbr-external-research]] §7f).
3. **The highest-value transfers hit L2-L4, not L5.** Grounded brainstorming answers "how should
   this be built to survive" far better than "what should it do".
4. **Maturity is a vector.** Each repo was stronger on different levels, so a CBR tower should
   carry capabilities in both directions, keyed by level × trait × plane, not one "maturity height".
5. **Converge, then verify.** 19 of 24 KSR gaps matched at least one KC capability, but I made the
   match knowing both lists. A blind judge, or the Owner's accept/reject pass, is the real test,
   and per [[cbr-gap-analysis]] it should be recorded so acceptance can be measured.

## Owner decisions (2026-10-01)

Accept/reject record, so acceptance can be measured ([[cbr-gap-analysis]]):

| proposal | decision | landed |
|---|---|---|
| P1 save integrity | accepted | KSR backlog row `KSR-B-073` (KSR `5345ca1`), blocked by the Owner STOP and KSR-B-031 |
| reverse: praxis-guard skip | accepted | KobiiCraft `post-launch-backlog.md` P1 "CI gates that cannot fire" (KC `61cd4448`) |
| reverse: Python gates in CI | accepted | same section, KC `61cd4448` |
| P2-P6, L5 ideas | no decision yet | none |

Backlog rows only. No code changed in either repo.

## Open questions

- P2-P6: take any into the KSR backlog while the Owner STOP stands?
- Is the catalogue worth building as data (level × trait × plane, per [[maturity-transfer]]), or
  is a periodic pilot like this one enough?
