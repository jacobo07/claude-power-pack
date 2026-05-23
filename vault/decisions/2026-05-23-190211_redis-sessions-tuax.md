# ADR-20260523-190211: redis-sessions-tuax

Date: 2026-05-23
Status: Proposed
Verdict from arch_check: CLEAR

## Context

TUA-X needs persistent server-side session storage. The choice is
between Redis (in-memory KV, fast, ephemeral by default) and Postgres
(relational, durable, slower for raw KV access). The current TUA-X
stack already includes Postgres, so adding Redis introduces an
additional managed dependency. Sessions are short-lived (24h default
TTL) and read/write volume is high — one read + one write per
authenticated request.

The arch_check verdict was CLEAR: the vault contains no prior
Redis-vs-Postgres-vs-X session-storage decision. This ADR is the
first explicit decision on this axis to be sealed.

## Decision

Use Redis for TUA-X session storage (hot path) with Postgres as the
durable audit log. Redis handles per-request get/set; the audit
trail (session_id, started_at, last_activity, user_id_hash) is
written to Postgres asynchronously when sessions expire or on
explicit logout.

The Status of this ADR is Proposed pending Owner sign-off; if
accepted, the implementation lands behind a feature flag with
Postgres-only fallback for one release cycle.

## Consequences

### Positive
- Sub-millisecond p99 session reads on the hot path.
- Postgres `sessions_audit` table stays small (only completed sessions).
- Horizontal scale: Redis read-replicas + cluster mode trivially supported.

### Negative
- One additional managed dependency (Redis cluster + monitoring +
  backup story).
- Race condition window: if a node shuts down between Redis
  TTL-expiry and the Postgres audit write, the audit row may
  be missing. Mitigation: explicit `SessionExpired` event written
  to Postgres BEFORE Redis key deletion.
- Operational complexity: now operating two state stores.

### Neutral
- Either choice meets the 24h session TTL contract.
- Either choice satisfies GDPR right-to-delete (key deletion +
  audit-row-anonymisation).

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Postgres only | Hot-path session reads add 5-20 ms p99 per request; over the daily request count, exceeds the latency budget. |
| In-memory only (no Redis) | No cross-node session sharing; breaks horizontal scale to >1 web tier replica. |
| KeyDB instead of Redis | Less ecosystem maturity; same architectural trade-offs as Redis without the maturity tail. |
| Memcached | No native persistence; session loss on cache restart is unacceptable. |
| Cookie-based stateless (JWT) | Larger request size; revocation requires a deny-list anyway. |

## Vault-conflicts

None surfaced by arch_check.

The verdict was CLEAR. The arch_check entity match for "redis" did
not produce a high-relevance hit because no prior memory or sealed
Standard explicitly forbids or recommends Redis for sessions in this
ecosystem.

## Lessons cited

None cited.

The closest tangential lesson is `apex-completion-standard.md`
"Session Safety Axis (sealed 2026-05-22)" but that governs Claude
`.jsonl` session files at the IDE layer, not application-level
HTTP session storage. The semantic overlap is the word "session"
only; the architectural domains are disjoint.
