# CCP §15: verification-harness validity + s14 close-out (pane claude-power-pack-da)

Status: PROPOSED 2026-10-03, awaiting one Owner approval. Extends `ccp-s14-identity-horizon-displacement-2026-10-02.md`.
It overrides nothing in it.

## Reality (measured 2026-10-03 ~07:10 local)
- HEAD `9b28175c` on `feature/knowledge-acquisition`, origin plus 1 (9b28175c itself), no commit since. 749 dirty paths, almost all
  belonging to other panes. Exactly ONE deletion in the whole tree: `vault/audits/ccp-s14-s3-audit.md`.
- Panes: §13 lane = session db8ae5cd (now `claude-power-pack-57`), live. It is planning the c10 remainder and the `_store_dirs`
  consolidation, and will message before touching `tis_observed.py`. c10 stays theirs.
- Backup `state/usage_index/index.identity-1790970811.bak`: 111,706,112 B, sha256 `167f16fe…bfb2` (match). RETAINED;
  deletion unauthorised. It is a sleeping human-authority obligation and blocks nothing else.

## Findings
- F1 Audit "deletion" PROVENANCE: nobody deleted it. `6b61e29a` (this pane) published the file from the predecessor's
  scratchpad `s3_audit.md` through a private index. Scratch blob = HEAD blob `673ff92c`. The working tree never held the file.
  Hazard: any peer `commit -a` / `add -A` would commit the deletion of a sealed audit.
- F2 `mutation_drill.py` (owner: this pane, confirmed by 2a's message): (a) `copy_dirs` exists (430b5de9) but `--help` does
  not document it; (b) there is no control run, so a gate that already fails on the clean copy reads KILLED (false kill);
  (c) default layout plus a test outside the subject dir means the LIVE test runs against the LIVE module and the mutant reads
  SURVIVED (false survive). (c) is known from code reading only and is proven red-first in C1. Duplicate harness born from
  it: `vault/audits/ccp-c9/c9_replica_drill.py` (2a's frozen audit record; stays).
- F3 The resumption focus is not ownership: the /kresume focus was 2a's action 1 typed into da's resume.

## Commits (EXECUTION after approval and the phase-4 audit)
- C0 Materialise the audit from HEAD blob `673ff92c` (create only; refuse if the path exists; verify blob after). No commit
  needed: the tree then matches HEAD.
- C1 `mutation_drill`: control run first (named gate must PASS and the summary must be present, else CONTROL_INVALID, exit 4);
  repo-layout copy whenever the test is outside the subject dir; default copy set tools + modules + vault/pricing +
  vault/config; `copy_dirs` documented. Red-first tests in `test_mutation_drill.py` for (b) and (c), plus a positive control.
- C2 Re-run the 8 S3 drills through the STANDARD harness (no scratch replica). Expected 8/8 KILLED; record per-mutant.
- C3 Knowledge: UKDL hunk-staged (live CEPS tail), three traps: private-index publish leaves the tree without the file;
  a drill verdict without a control run; a resumption focus executed without reconciling capsule ownership. One process
  rule: control -> mutate -> named discriminator -> explicit verdict.
- C4 Record results here. s14 closes except obligation 1 (Owner consent).

## Not now
- Rollover-timing shadow / fresh-epoch economics: owners exist (`vault/specs/economic-rollover-trigger.md`,
  `parent-context-epoch-rotation.md`, `context-watchdog.py`, `session_autopsy.py`). D2A first, in a later PLAN.
- Singleflight observer, re-derivation detector, C4.1: listed NEXT in 2a's resumption; not claimed here.
- CBR: nothing ratcheted. Candidates stay EXPERIMENTAL until a second incident or an enforcing test exists.
