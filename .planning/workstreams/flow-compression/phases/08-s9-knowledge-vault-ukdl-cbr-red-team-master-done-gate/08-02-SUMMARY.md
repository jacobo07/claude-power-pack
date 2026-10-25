---
phase: 08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate
plan: 02
completed: 2026-10-25
status: complete
---

# 08-02 summary: S9 red team

All 15 Owner hypotheses were attacked by `tools/redteam_s9.py` against the 07 pin (sha256 `b47ff018fb44766f`, 6339 rows).
Gates: `python3 tools/test_s9_redteam.py` prints `S9RT_PASS=112/112` (wall 341 s of the 540 s limit): instrument gates, 15 claim gates
(controls + subject), five report gates (ALL-ATTACKED, REUSE-HASHED, PIN, DETERMINISTIC, REPORT-REPRODUCES) and one drill per mapped gate
plus the no-op control. Report: `08-REDTEAM.json` / `08-REDTEAM.md` (regenerate with the command in the file). Host writes observed: 0.

## Verdicts (no PASS exists; HELD needs a fired guard-removed control)

| # | Claim | Verdict | Planes | Sub-attacks with a fired control | Reason |
|---|---|---|---|---|---|
| 1 | The context hypothesis was correlation, not cause. | **UNMEASURED** | repo-artefact, seeded | 2/2 | causal-effect:rotation and compaction were not randomised and no stratum is recorded, so no causal effect is estimable; S1 replay holds only UNMEASURED |
| 2 | Rotation increases rehydration cost more than compaction. | **UNMEASURED** | GEX44-host-readonly | 1/1 | rehydration-cost:n too small (rotation 6, compaction 0; need 3) |
| 3 | Preflight merely moves waits earlier without reducing span. | **UNMEASURED** | repo-artefact | 1/1 | span-effect:one S2 incident and its resolution is exogenous: the span effect of an earlier stop is not observable |
| 4 | Auto-normalized ROADMAP changes semantics. | **HELD** | GEX44-temp-copy, repo-artefact | 2/2 |  |
| 5 | Immutable packets become stale too quickly. | **UNMEASURED** | seeded | 1/1 | packet-staleness:supersession share 0.125 is under 0.25 but closed-phase re-targeting (Owner live evidence) is not observable in the pin |
| 6 | Admission reservation causes deadlocks or resource hoarding. | **HELD** | GEX44-host-readonly, repo-artefact, seeded | 3/3 |  |
| 7 | Auto-renew allows runaway cost. | **HELD** | GEX44-temp-copy | 1/1 |  |
| 8 | The semantic progress signal can be gamed by noisy commits or tests. | **BREACH** | GEX44-temp-copy | 1/1 |  |
| 9 | Night readiness asks too many Owner questions. | **HELD** | GEX44-host-readonly | 1/2 |  |
| 10 | The terminal reconciler creates false DONE. | **HELD** | GEX44-host-readonly, GEX44-temp-copy | 1/2 |  |
| 11 | Blocked work stealing violates dependency or workspace ownership. | **HELD** | GEX44-host-readonly, repo-artefact | 2/2 |  |
| 12 | Historical replay is biased by missing telemetry. | **BREACH** | seeded | 1/1 |  |
| 13 | The efficiency compiler optimizes aggregate mission-hours rather than the actual critical path. | **HELD** | repo-artefact, seeded | 3/3 |  |
| 14 | GSD X policy leaked into GSD Core. | **HELD** | GEX44-host-readonly, repo-artefact | 2/2 |  |
| 15 | (claim text absent from the repo) | **UNMEASURED** | repo-artefact | 1/1 | claim-text-search:claim text absent; OWNER DECISION NEEDED |

Totals: HELD 8, BREACH 2, UNMEASURED 5.

## BREACH drafts (FC-12, turned into incidents by 08-03; nothing is repaired here)

- **Claim 8 (progress signal gameable):** `resumption_file_md_only`, `tracked_junk_file` and `untracked_test_log` move the semantic fingerprint and are granted a lease renewal.
  This agrees with the live evidence the Owner quoted (no_progress blind to `.planning` work halted m-3d5f0a27e41d), from the other side: noise counts, real planning work does not.
- **Claim 12 (replay biased by missing telemetry):** summed mission-hours 27,484 h (flow_replay) / 27,528 h (independent recomputation) against a bounded 1,696 h:
  92 of 148 missions have no terminal row and are ended at the pin, not at their last row; a 15x bias against a 0.10 tolerance.
  UNMEASURED stays apart from measured (249 measured verdicts, 17 unmeasured apart; 588 of 3,400 failure rows mapped to a slice).

## Claims that cannot be HELD, and why

- **1:** wording is HELD (the one rotation-vs-compaction comparison in 01-EVIDENCE.md carries its confound caveat; removing the qualifiers makes it unqualified, so the sweep can fail), but no causal effect is estimable: no randomisation, no stratum, S1 replay is 13 UNMEASURED.
- **2:** six rotation epochs have a first-call context of about 105k tokens; the five ledgered compactions leave no observable drop in the transcripts, so the compaction side has n = 0.
- **3:** the one S2 incident (m-9d00610493fc) stops 1,127 s earlier under the challenger but the mission ended by an owner-dead timeout; the span is exogenous in both arms.
- **5:** 2 of 16 timed packets were superseded within 24 h (12.5%, under my 25% line), but the Owner's live evidence (packets re-targeting closed phases) is a staleness mode the pin cannot observe, so the claim is not held.
- **15:** the claim text is not in the repo; UNMEASURED, `OWNER DECISION NEEDED` (recorded in STATE.md).

## Deviations from the plan

- Claim 2 uses first-call context tokens per epoch and inferred compactions (a 30% fall in per-call context) because the transcripts hold no `compact_boundary` marker and no commit-bounded sums were derivable deterministically; epochs are cut at their ledger end so reruns are byte-equal.
- Claim 7 drives `mission_topup` hold-keyed idempotency (the real mechanism) rather than a `seq` key; the always-renew control patches `LEASE_MAX_RENEWALS`.
- The report reflects the tools tree at the time it was generated (file counts in the sweeps); 08-03 regenerates it once the tools tree is final.
