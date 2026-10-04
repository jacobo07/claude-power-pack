# Handoff [R] -- CBR review -> the tower family-baseline owner

Pillar: [R] institutionalization / UKDL. Terminal: IMPLEMENTED_AND_VERIFIED for the UKDL half. This file hands
the CBR half to its owner. The plan of record names "CBR tower" (plan line 60). Per
`vault/specs/agent-capability-virtualization.md:233`, CBR = `modules/tower` + `vault/tower/families/`.

Owner of the CBR half: `modules/tower` (baselines, families, ratchet, select, checks, donegate) and its families
`vault/tower/families/{web_surface,kobiicraft_mode,wii_homebrew,persistent_state}.json`.

Pillar [R]'s frozen owners are `vault/knowledge_base/ukdl-universal.md` and `~/.claude/commands/cpp-compound.md`.
They keep the UKDL half, and UC-04 now lives in the first. The frozen list does not name `modules/tower`, so this
handoff is how the CBR half reaches its owner.

## Guarantees this campaign gives

- Every finding is recorded at CBR maturity **EXPERIMENTAL**, and nothing was raised above it (plan line 78). The
  `cbr:` line of each block in `vault/programs/cognitive-economy/ukdl-candidates.md` (UC-01..UC-12) is the whole
  CBR review. All twelve read EXPERIMENTAL. No finding was re-observed in an independent run or project, which is
  the bar for CANDIDATE.
- The format is checked: `gates/gate_ukdl_candidates.py` accepts only the four maturity values, and on every run
  it proves five mutants of the real file red. Observed 2026-10-04: `GATE_UKDL_CANDIDATES=PASS candidates=12
  failures=0`.
- **No family file was written.** No generation `B<n>` was added and no `ratchet` operation ran. The campaign
  wrote CBR nothing.

## Evidence

- `ukdl-candidates.md`: 12 candidates. 1 promote: UC-04, written into `ukdl-universal.md` on Owner decision 6
  (2026-10-04) as T-A-WHOLE-TREE-PROGRESS-FINGERPRINT-CANNOT-SEE-A-STALL-IN-A-SHARED-CHECKOUT-001. 2 reject: UC-02
  and UC-03, already owned. 9 keep-candidate.
- `evidence/R-prg.md`: the 2026-10-03 PRG of the UKDL half.

## Applicability (which family each candidate could enter, if earned)

| candidate | nearest family | why |
|---|---|---|
| UC-04 shared-checkout progress fingerprint | none fits | supervisor behaviour, not a project family; a mission/agent family does not exist yet (spec :233) |
| UC-07 case-variant duplicate JSON keys | `persistent_state` | a state-file shape that breaks a reader |
| UC-09 gate precondition on transient live residue | `persistent_state` | a check bound to a file another process deletes |
| UC-12 live code from an uncommitted shared tree | none fits | repo-hygiene of a shared checkout |
| UC-01, 05, 06, 08, 10, 11 | none fits | measurement / status discipline, owned by doctrine skills, not by a family |

"Could enter" is not a recommendation to write it. Entry needs CANDIDATE maturity first, and the debt below says
an entry would currently be judged nowhere.

## Limits

- Twelve findings come from one campaign in one repo on one host. EXPERIMENTAL is the honest ceiling. Every
  "seen once" in the candidates file is a real limit, not modesty.
- The applicability table is a reading of the four family file names only. Neither their contents nor their
  entries were evaluated against these candidates.

## CBR debt found (recorded, not ours to fix)

1. **`modules/tower/donegate.py` `judge` has no live caller.** Its only importer is `tools/test_tower_donegate.py`.
   `modules/gsd_x/cli.py:104` names it in a docstring only. The family done-gate therefore runs only under its
   own suite, and a family entry, however mature, is judged by nothing at runtime. The module is report-only by
   design (docstring: "nothing here can refuse anything"), but nothing produces the report either. `tower` has no
   entry in `vault/liveness/reachability_registry.json`, so this is undeclared, not declared-LIBRARY.
2. **`modules/tower/ratchet.py` `promote` has no caller.** `tools/family_baseline.py` uses only `verify_chain` and
   `revert`. This matches the spec's warning (`agent-capability-virtualization.md:267-268`: "no admission control
   and no caller -- do not rely on it"). A finding cannot move from EXPERIMENTAL into a family through any path
   that runs today.

Together these mean CBR maturity is currently a label that nothing reads back. Raising one is the owner's call:
wire `judge` into a done surface (or declare it LIBRARY with a consumer named), and give `promote` admission
control before anything calls it.

## What the owner keeps

`modules/tower`, every family file, the maturity ladder, and the decision whether and where any candidate enters
a family. The campaign edited none of them.
