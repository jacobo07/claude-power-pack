# Incident: plan premises that were not in the code (2026-10-25, phase 7)

**Class:** PLAN PREMISE NOT IN CODE -> A PLAN NAMES A SWITCH, EVENT OR FIELD THAT DOES NOT EXIST.
The phase 7 plans asserted facts about the repository that the repository did not hold. Each was caught
by reading the code during the build, none by the plan check, and each changed a verdict the report could
otherwise have printed. This is the HR-PREMISE-001 class (verify file and function premises before acting
on a plan).

## Symptom

STATE.md lines 72 to 77 list six corrections made while building S7:

- Switch names: the plan named switches that do not exist. The real S1 to S6 switches are
  CPP_ROTATION_INVARIANT, CPP_ARM_PREFLIGHT, CPP_GSD_HOLD_BACKOFF, CPP_ECON_LEASE,
  CPP_TERMINAL_RECONCILE and CPP_BLOCKER_COMPILE. The admission, renew and bounded-renewal switches
  pre-date the mission and are a held group, equal in both arms.
- The idle-gap seam (`plan_next`) answers the same under either arm, so a challenger idle figure for a gap
  no seam recomputed is the champion figure.
- Event names and receipts: the plan's event names did not match the ledger, and the ledger holds zero
  halts without a receipt.
- S3 and S5: the S3 digest needs a normalisation that no switch controls, and the S5 reconcile champion arm
  cannot be measured (annotation only), so those verdicts are UNMEASURED or UNCHANGED by construction.
- The ledger does not carry every `plan_next` field: the owner of an idle gap is a host-backgrounded worker
  and the gap start is inferred because no worker-end row exists.
- Pin size: the plan text said 6333 rows; the pinned prefix holds 6339 (1740294 bytes). This phase
  recomputed it: the first 1740294 bytes of the host ledger hash to b47ff018fb44... and the pin file says
  6339 rows.

## Timeline (local time)

| when | what | instrument |
|---|---|---|
| 2026-10-25 (07-01 build) | tracer reads the env names in the six slice modules; real switches differ from the plan (6ba88a90) | reading `os.environ` names in the modules |
| 2026-10-25 (07-01 build) | full replay: failure-kind table computed from the ledger, coverage not from a hand list (7062fa76) | V-S7-DISCOVER-COVERAGE in the suite |
| 2026-10-25 (07-02) | corrections recorded in STATE.md (25dca5f5) | git log -S on the correction text |
| 2026-10-25 this phase | pin re-verified: sha256 of the first 1740294 bytes of the host ledger equals the pin | `head -c 1740294 ledger | sha256sum` gave b47ff018fb44... |
| 2026-10-25 this phase | the three suites rerun, S7 164 of 164 | /tmp/s9-evidence/test_s7_replay.out |

## Root cause

The plan was written from the spec's wording and from memory of the modules, not from the modules. The
plan check validated structure and coverage of requirements; it did not open the code to confirm a named
switch, event or count exists.

## Why the existing rule did not prevent it

HR-PREMISE-001 exists and says to verify a plan's named files and functions. It was not applied to
environment variable names, ledger event names or counts, which are premises of the same kind.

## Earliest discoverable point

Reading the env names in the six slice modules before writing the plan. Each premise was one grep away.

## Repair

The harness takes its switch set from the code and asserts it: the HELD and SWITCHES sets are disjoint
(V-S7-HELD-EQUAL), unknown `CPP_` names are refused (V-S7-NO-NEW-STATE), coverage is computed from a
discovered event census (V-S7-DISCOVER-COVERAGE), the carried-unchanged idle figure is labelled and never
printed as a gain (V-S7-IDLE-BEFORE-AFTER), and the pin is verified on every read
(V-S7-TRACER-PIN-COMMITTED-VERIFIES). The measured pin wins over the plan text.

## Test

- commit: 6ba88a90
- commit: 7062fa76
- commit: 25dca5f5
- gate: V-S7-HELD-EQUAL in tools/test_s7_replay.py
- gate: V-S7-NO-NEW-STATE in tools/test_s7_replay.py
- gate: V-S7-DISCOVER-COVERAGE in tools/test_s7_replay.py
- gate: V-S7-IDLE-BEFORE-AFTER in tools/test_s7_replay.py
- gate: V-S7-TRACER-PIN-COMMITTED-VERIFIES in tools/test_s7_replay.py

## Pattern

Every name, count and event a plan asserts is read from the code or the data before the plan is executed
(HR-PREMISE-001, extended from files and functions to switch names, ledger events and counts).

## Open debt

- The plan check does not open the code. A premise audit step for environment names and event names is
  not built; this mission records the class and does not add a tool (no policy change).
