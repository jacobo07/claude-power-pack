"""Monitoring / Alert Axis -- continuous observability node.

Sister to Deploy + Backup + Rollback: the same healthchecks that
gate those axes run in a loop here, surface state changes, write
durable receipts, and let the Owner decide on remediation.

Reuses modules/deployment/healthcheck.py verbatim -- single source
of truth for check_tcp / check_http / check_curl_grep.

Hard invariants:
  - NO automatic rollback. The monitor SUGGESTS via alerts, never
    invokes modules/rollback/. V-NO-AUTO-ROLLBACK grep-asserts this.
  - NO duplication of healthcheck logic. All check_* calls go
    through modules/deployment/healthcheck.
  - Polling + disk persistence only. Webhooks / TIS bridge / cron
    auto-install are deferred to V2 per the Q&A.

Spec: vault/plans/monitoring-alert-axis-<ISO>.md.
"""
