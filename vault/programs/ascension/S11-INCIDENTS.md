# S10-S11H Knowledge Vault incidents: truth contract, held-out law, pivot autonomy

Record for the K unit of Generation S11 / S11H (Owner go 2026-11-03). Format and status words follow
`S9-INCIDENTS.md`:
- **FIXED**: code and a regression gate exist.
- **SMOKE**: the fix is also proven on the real host.
- **OPEN**: named, not repaired.
- **CLOSED**: not a product defect, with the reason.

Code anchors:
- Laptop PP: `c138604e` (A1), `0206a1e8` (A2), `a6a0a032` (A3), `a1186b4c` (D2/D3), `f66e9e96` (D1), `23691d01` (P1-P5).
- GEX44 live PP clone: `ce2414c1` (Gen2).
- t1: `ae3da98d` (H2 cache), `2091cdad` (R4 certs), `6fbf44f7` (H2x).

## Incidents

| # | Symptom | Root cause | Repair | Regression | Status |
|---|---|---|---|---|---|
| S11-1 | A certification-contract question ("Decide whether cert-cxx may admit an sd8 variant", S10 m-e6e0340e743d) was answered RESOLVE_BY_DEFAULT by the sweep's decision recovery | `mission_policy` had no owner class for changes to what counts as certified, exact or held-out. Such a change was read as a HOW question | A1: TRUTH_CONTRACT owner class (change verb + contract noun; relaxing verb + exact/certified) | V-MPOL-GATE-TRUTH-*; red 47/49 -> green 49/49 | FIXED, SMOKE (live on GEX44 since 41773cc3) |
| S11-2 | "Waive fn_80222480 for OM-PR1" (m-f0b595fd509f epoch 12, 2026-11-02 23:31Z) was answered RESOLVE_BY_DEFAULT after A1 | The control and gate nouns (positive/negative control, kill gate, OM-PR<n>, release conditions) were not truth-contract nouns, and drop/skip/bypass were not change verbs | D3 `a1186b4c` | V-MPOL-GATE-TRUTH-CONTROL-WAIVER | FIXED |
| S11-3 | Same mission, 05:33Z: "Owner to waive fn_80222480, or supply a donor ..." was still RESOLVE_BY_DEFAULT after D3 | No control noun in the sentence; the waiver verb was aimed at a function | P5 in `23691d01`: "waive fn_X" is TRUTH_CONTRACT | same gate, last sample | FIXED |
| S11-4 | The checkpoint reason "in-scope routes falsified" read as PRODUCT_SCOPE, which would have parked an engineering pivot for the Owner | An in/out-of-scope adjective in front of an engineering noun describes work, but it matched the scope class | D2 `a1186b4c`: the descriptive adjective is removed before the PRODUCT_SCOPE check only | V-MPOL-GATE-SCOPE-DESCRIPTIVE (both poles) | FIXED |
| S11-5 | A checkpoint sat ~6 h without its pivot (m-f0b595fd509f, 23:31Z declaration) | The host kept listing the exited worker as bare `state:"blocked"` (no waitingFor). owner_idle never held, liveness was not DEAD, and checkpoint_gate returned before pivot_gate | D1 `f66e9e96`: a bare block on the job that declared the checkpoint is released after 600 s, its `needs` ledgered first | PIVOT 17/17 (5 new), drills D4-D7 | FIXED |
| S11-6 | A decision recovery was spent on a job record that read `stopped` (GEX44 2026-11-03 09:54:41Z) | A lifecycle word was read as a model question | P5 in `23691d01`: a lifecycle word is a dead owner, relayed normally | V-MPOL-BLOCKED-LIFECYCLE-NOT-QUESTION | FIXED |
| S11-7 | K6 first attempt refused 3/3 known CXX (S10b) | Coordinator instrument error: the raw fixture was fed to the certifier without `make_unit` | Re-run through `make_unit`: 3/3, identical unit/object sha | none (method) | CLOSED: instrument, not lane. Rule: drive a certifier only through the path production uses |
| S11-8 | The frozen S10b method c631de1e failed its positive control (OFF_SHAPE on the 3 known CXX) after it was frozen | The worker froze the method without running the positive control first. Nothing refused a freeze with an unrun control | A3 `a6a0a032`: `heldout_release.py` refuses release unless positive AND negative controls pass; H2 stays sealed | HOLDOUT 10/10, drills 3/3 | FIXED (release side). OPEN: the freeze itself is not gated |
| S11-9 | A mission stayed RUNNING after its closeout commit (S10/S10b); the sweep never acted on the worker's declared checkpoint | Not traced to a line. The closeout was written as evidence, and the record changed only when the coordinator ran `checkpoint` | Coordinator set the checkpoint by hand | none | OPEN (a closeout without a checkpoint verb is not detected) |
| S11-10 | Every R4 candidate, non-members included, was REFUSED H2_MANIFEST_UNREADABLE | The OM harness audit hook (`om_skeleton.guard()`) forbids reading the sealed manifest, including the certifier's own membership check. The certify tool also dropped the receipt's contract | t1 `ae3da98d`: `h2_members()` caches per path in memory, warmed before the hook; cold still fails closed | V-H2CACHE red 1/3 -> green 3/3 | FIXED (R4: +5 CERTIFIED_CXX, t1 `2091cdad`) |
| S11-11 | The H2x static scan (vptr/this-call presence over the whole corpus) included 2 of the 20 sealed H2 members | Corpus-wide scans have no structural H2 exclusion. The worker did not know the members | Owner 2026-11-03: KEEP 20 (only a raw static feature was observed; no method output, exactness or certification) | none | OPEN: corpus scans must exclude H2 by construction |
| S11-12 | m-f0b595fd509f HALTED on max-cycles 24 mid-programme; its successor m-fc7047a29f01 had to be armed by hand | A renewal path exists (`renew_mission`; a cycle-cap halt is a budget halt). The sweep REFUSED it: "not renewed: GSD answered NO_PHASES, not work-remains" (`gsd-long-run-sweep.log` 2026-11-03T11:48:40Z): gen3-pp had no GSD milestone | Owned by spec `gsd-x-universal-mission.md` (PP `37b2abaf`, `0f80c09a`: arm refuses NO_PHASES and scaffolds the milestone). gen3-pp and recon-general now hold a ROADMAP | V-PRE-GSDX-* (that spec) | FIXED on the laptop. Not on GEX44 (live clone `ce2414c1`) |
| S11-13 | A live generation's launch prompt could not be changed | No verb rewrote a PREPARED/parked mission's command. The only route was re-arming | `retarget_mission` + `gsd_mission.py retarget` (spec `mission-retarget.md`): PREPARED, or held with the owner proven gone; refuses terminal, live owner (held or not), wu_packet, route-class and workstream change; CAS on seq; the retarget row gets sha256 only. pp-code-reviewer WARNING (1 HIGH, 2 MEDIUM, 1 LOW) all fixed | V-RETARGET 14/14, drills 6/6; MC 242/242 | FIXED on the laptop. Not on GEX44 |
| S11-14 | `recon_public_gate.py --range` with an empty base read CLEAN on 0 commits (coordinator, 2026-11-03) | An empty range scans nothing and reports no violations | Re-run with base 70c2fde4: 16 commits, VIOLATIONS {TITLE: 1} | none | OPEN (an empty range must exit 2 UNMEASURED) |
| S11-15 | The recon worker withheld private-target module names from PARITY output but left them in `tools/rf_parity.py` source (`6e723398`) and declared CHECKPOINT_COMPLETE "ready for public gate" without running the gate's `--range` mode | The worker's check was on output, not on source; nothing made the checkpoint wait for the range gate | Coordinator: names -> `TARGET_COUNT = 21`, commit amended before any push (`429b0126`); range CLEAN on 16 commits and per commit; PR #12 | factory suite 33/33 | FIXED. OPEN: `--range` judges files at the tip only; a name added then removed mid-range would pass (checked per commit here by hand) |

## Prompt-debt registry (instruction -> mechanism -> gate -> fresh consumer)

An instruction that lives only in a prompt is debt until code carries it. A row is paid when a gate pins the
mechanism and a fresh worker that never saw the prompt obeys it.

| ID | Instruction (was prompt-only) | Mechanism | Gate | Fresh consumer | Status |
|---|---|---|---|---|---|
| PD-1 | "Pivot on method failure; do not ask the Owner" | A2 `checkpoint --residual/--gain` + `pivot-autonomy --on`; Gen2 receipts (P1-P3) | PIVOT 29/29, drills 15/15 | m-fc7047a29f01 runs with pivot Gen2 on | PAID |
| PD-2 | "Contract changes are the Owner's" | TRUTH_CONTRACT class in `mission_policy` | V-MPOL-GATE-TRUTH-* | live sweep, GEX44 `ce2414c1` | PAID |
| PD-3 | "Never read H2 before the sealed run" | `om_skeleton.guard()` audit hook + `heldout_release.py` | V-H2CACHE, HOLDOUT 10/10 | S11H worker (K5' audit clean) | PAID for reads. OPEN for scans (S11-11) |
| PD-4 | "Run the positive control before freezing a method" | none at freeze time | none | none | OPEN (S11-8) |
| PD-5 | "A closed wave declares a checkpoint" | checkpoint states (S9) | V-S9-CKPT-* | S9-S11 workers | PAID for workers. OPEN for coordinator closeouts (S11-9) |
| PD-6 | "Use `make_unit` when driving a certifier by hand" | none | none | coordinator | OPEN (process rule only) |

## Construction Return / CBR

The cases above are PP-side. The t1-side cases (R0 fn_80222480 register bijection, R1 natural experiments,
H4 negative search memory) are carried by t1 `modules/recon_fabric/cbr.py` and `search_plan`. Their CBR
births are part of the S11H mission's own units (t1 `513abb3d`, `a4a34299`, `1830a212`). This record does not
duplicate them.
