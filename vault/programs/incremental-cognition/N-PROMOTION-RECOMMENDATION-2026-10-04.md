# Incremental Cognition -- recommendation for the [N] promotion decisions (row 31)

Prepared for the Owner on 2026-10-04. A recommendation, not a decision: no candidate is promoted until the Owner approves,
and each approved promotion is written and then recorded under `## Promotions recorded` of the matching review on the
mission branch, with its commit, before `python3 tools/test_ic_closeout.py` runs.

Read in full: `ukdl-candidates.md` (16 candidates), `reviews/ukdl.md`, `reviews/cbr.md` at branch tip `d7bd4b16`
(files unchanged since 21:25). Spot-checked against the laptop tree: `T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001`
(`ukdl-universal.md:9581`) and `PR-VERIFY-HANDOFF-PREMISES-001` (`:3601`) exist and say what the review says they say; the
global rule `~/.claude/rules/state-lifetime-and-incarnation.md:31-32` already owns "run the same suite with and without the
change and diff the failure lists", which the mission's sweep did not search for.

## Recommendation

| candidate | mission verdict | recommendation | why |
|---|---|---|---|
| IC-U-01 refusal classified by its writer | PROMOTE-PROPOSED | **PROMOTE** to `ukdl-universal.md` | red-first, drilled (V-PFP-FALLBACK-QUOTED-NOT-PARKED, 137-relaunch shape); no owner found; same family as the 2026-10-04 quota-relogin fix (identity, not words or timestamps) |
| IC-U-02 install, not repository, decides | REJECT (duplicate) | **AGREE: append as an instance** to `T-COMMIT-IS-NOT-INSTALL-...-001` | the existing entry owns the rule; a7 at 01199995 adds the launch-time commit-floor refusal (`pp_install_stale`) as its mechanised form |
| IC-U-03 name the plane before blaming the change | HOLD | **DO NOT PROMOTE** (owned) | plane half: global `validation-planes-do-not-transfer` / `develop-here-prove-there`; with/without half: global `state-lifetime-and-incarnation:31-32`. Nothing left for a repository entry |
| IC-U-04 replay a handed-over list at the target base | PROMOTE-PROPOSED | **PROMOTE** as sister of `PR-VERIFY-HANDOFF-PREMISES-001` | that entry is the receiving side; this is the sending side, measured twice in this run (frozen_source 0 at 18e928af; [K] suite 66/67) |
| IC-U-05 reference and checks same session kind | HOLD | **HOLD** | one session pair, one 4,383-char part |
| IC-U-06 per-item check runs every clause of the full gate | PROMOTE-PROPOSED | **PROMOTE** | measured false PASS (ICP_PILLAR_J=PASS on a misquoted terminal), red-first fix plus a clause-removing mutant; no owner found |
| IC-D-01 frozen denominator reproduces only in its window | PROMOTE-PROPOSED | **PROMOTE** to `ukdl-cognitive-resource-os.md` | exact reproduction when windowed (13 / 1,322) against 14 / 1,679 unwindowed; domain-scoped |
| IC-D-02 missing channel is UNMEASURED | HOLD | **HOLD** (owned by global `real-context-reachability`) | one instance; no new rule |
| IC-D-03 rollover saves only growth above the floor | HOLD | **HOLD until the KME-L run** (rows 4-10), then re-review | performance claim; frozen transfer rule needs a second independent workload; KME-L is that workload and is now authorized |
| IC-D-04 retry identity is the command text | HOLD | **HOLD until the KME-L L ranking** (row 10) | rests on a probe its own evidence labels "not a measurement" |
| IC-D-05 lapsed access + live refresh is READY | HOLD | **HOLD** | scratch credentials only; reopen when a real environment is observed lapsed-but-refreshable |
| IC-D-06 verification share driven by verifier subagents | HOLD | **HOLD until the KME-L run**, then re-review | same transfer rule as IC-D-03 |
| IC-P-01..03 | HOLD | **KEEP project-level** | this program's own gate conventions |
| IC-P-04 gate trusts self-asserted front matter | HOLD | **KEEP as named debt; fix before trusting D-I terminals** | the D-I runs authorized in rows 4-10 produce exactly the files R3 judges; a hand-editable front matter passing R3 is the debt that matters next |
| CBR (all 16) | 14 REJECT, 2 HOLD, family none | **AGREE: nothing into CBR** | the four families are products (Minecraft mode, persistent state, web surface, Wii); no product instance is incomplete without these; IC-D-03 / D-06 also fail the transfer rule |

Net if approved: 4 new UKDL entries (IC-U-01, IC-U-04, IC-U-06 universal; IC-D-01 domain), 1 instance appended (IC-U-02),
0 CBR generations, 11 held or kept, of which IC-D-03, IC-D-04, IC-D-06 re-open automatically after the KME-L runs.
