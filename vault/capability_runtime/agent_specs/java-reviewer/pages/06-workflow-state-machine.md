### MEDIUM -- Workflow and State Machine (payment / event-driven code)
- **Idempotency key checked after processing**: Must be checked before any state mutation
- **Illegal state transitions**: No guard on transitions like `CANCELLED → PROCESSING`
- **Non-atomic compensation**: Rollback/compensation logic that can partially succeed
- **Missing jitter on retry**: Exponential backoff without jitter causes thundering herd
  - **[SPRING]**: Check Spring Retry configuration
  - **[QUARKUS]**: Check `@Retry` from MicroProfile Fault Tolerance
- **No dead-letter handling**: Failed async events with no fallback or alerting
  - **[SPRING]**: Spring Kafka / AMQP error handlers
  - **[QUARKUS]**: SmallRye Reactive Messaging `@Incoming` dead-letter or `nack` strategy

---

