---
title: A test does not answer Claude's Bypass Permissions dialog
tier: execution
date: 2026-10-18
source: Orca repo docs/dws/live-2026-10-18-row-70-resume-evidence.md (r70r4), live-2026-10-18-row-59-model-turn-evidence.md (a98f54a5e3)
status: LESSON -- UKDL entry T-A-TEST-DOES-NOT-ACCEPT-BYPASS-PERMISSIONS-001
---

# A test does not answer Claude's Bypass Permissions dialog

## Evidence
- r70r4: the e2e profile's Yolo default launches Claude with --dangerously-skip-permissions, and Claude asked to accept Bypass Permissions mode on the service account.
- Accepting it persists on that account (ypassPermissionsModeAccepted); it is the Owner's consent, not a test's.
- The spec now runs with Manual permissions (gentDefaultArgs.claude = '', read back) and treats the dialog as a refusal. The row 59 turn prints HWF59M_ARGV_BYPASS_FLAG=absent and the account shows ypassPermissionsModeAccepted absent.

## Lesson
When a harness meets a consent dialog for a real account, the correct move is to change the launch so it is never asked, and to assert that it was never asked, rather than to answer it. A green run that clicked the consent proves less than a smaller run that could not.