---
phase: 09-red-team-gap-closure-claims-8-and-12
plan: 01
status: complete
---
# 09-01 summary

- Code: 111f7ac8 (worker of mission m-088f20232c3c, which then hit its 8M authority mid-verification).
  - tools/gsd_mission.py: `_counts_as_work` allow-list in progress_fingerprint and _planning_artifacts;
    RESUMPTION_FILE.md is bookkeeping anywhere; CPP_PROGRESS_BOOKKEEPING=count still restores the old reading.
  - tools/flow_replay.py: open missions end at their last row; `open_hours_bounded_at_last_row` and
    `unobserved_tail_hours` beside `hours`.
  - tools/redteam_s9.py: attack_8 adds 6 real-work cases (blind => BREACH); attack_12 judges flow_replay's own
    block against the independent recomputation, with pin-ended windows as the guard-removed control.
- Verification and report regeneration were finished by coordinator af0b2bb1 on GEX44 (see 09-VERIFICATION.md).
- Not done: bare `git`/`node` in s9 tools (LOW, laptop PATH) stays open.
- Known limit: a change only to a file whose extension is outside the allow-list (e.g. `.txt`, extensionless
  scripts) does not count as progress; the kill switch restores the old reading.
