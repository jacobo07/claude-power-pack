# Overlay: Live-Ops

- **Discord:** discord.py or JDA. Slash commands only (no prefix). Rate limit aware. Graceful reconnection.
- **Monitoring:** Health checks every 60s. Alert on: downtime, error rate spike, resource exhaustion.
- **Broadcast:** Queue-based message delivery. Retry with exponential backoff. Dedup by message ID.
- **Server Management:** Infrastructure as code (Terraform/Pulumi). Never manual config on production.
- **Incident Response:** Runbook per service. Rollback plan documented before every deploy.
- **Logging:** Structured JSON logs. Correlation IDs across services. Retention: 30d hot, 90d cold.
- **Scaling:** Horizontal by default. Stateless services. Session affinity only when required.
- **Deployments:** Blue-green or canary. Never direct-to-production without staging verification.
- **Backups:** Automated daily. Tested restore monthly. Point-in-time recovery for databases.
- **Communication:** Status page for users. Internal incident channel. Post-mortems within 48h.
