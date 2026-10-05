---
phase: 01-judgement-task-bank-for-11-rules
plan: 02
status: complete
completed: 2026-10-05
---
# 01-02 Summary: hfee, dcme, vpdt judgement tasks

Built: `task_hfee_outbox.py` (human-facing-external-effects), `task_dcme_doc_status.py`
(documented-capability-must-be-executable), `task_vpdt_verified_level.py` (validation-planes-do-not-transfer).
Written by a subagent in /tmp (harness refused its writes under the shared checkout path), placed in bank-draft
by the orchestrator.

Review (pp-code-reviewer, WARNING 4 HIGH / 2 MEDIUM / 1 LOW): F1-F6 fixed by a follow-up agent and re-verified by
the orchestrator; each mutant that scored full marks before now fails a judgement check:
- hfee: resend key must equal the first key (approved at NOW, resent at NOW+700); key-window probes at 25 h and
  72 h may not send; past the window only a raise or "needs_operator" passes (hfee_nowkey 1/3, hfee_silent_sent 1/3).
- dcme: a failing / unstartable documented command passes only on BROKEN or a raise (dcme_unverified 1/3);
  a not-CI-runnable command only on UNVERIFIED or a raise (dcme_ci_broken 2/3).
- vpdt: new judgement check `preview_from_other_build` (vpdt_prod_only 2/3).
- F7 (LOW, dcme stub hint "UNVERIFIED" for CI-unrunnable commands) not changed: the stub does not state the
  answer; recorded as a known weak-discrimination limit.

Verify: selftests SELFTEST OK; `validate --only J-hfee_outbox,J-dcme_doc_status,J-vpdt_verified_level` ->
VALIDATE-E1 3/3 base=78ba9e7414 pins=13/13.
