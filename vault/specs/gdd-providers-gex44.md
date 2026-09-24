---
covers: [codex-budget-reader, local-llm-provider, shared-quota-dir, provider-health-states, F4, F14, plan-38, plan-38a, plan-55]
status: APPROVED-BY-PLAN (kseip-p8-gdd-resident-20260924 §38, §38a, §55; fixes F4, F14)
owner: LANE RESIDENT after GDD slice 1 lands (providers/*.py; never tools/gsd_x_goal.py)
---

# Wave G — providers that can run unattended on GEX44

## 1. Codex budget, read not probed (port of CavEX `tools/forja/codex_budget.py`, credited)
- Codex writes `rate_limits` (limit_id "codex"; primary/secondary used_percent, window_minutes,
  resets_at; credits; plan_type) into every session rollout under `~/.codex/sessions`. Reading it costs
  zero tokens; probing costs >= 14 140 tokens per call (measured by Forja, 2026-09-22).
- Verdicts kept distinct, as Forja does: OK · REFUSED (window exhausted, reset in the future) ·
  RESET_SINCE (the reading's window already reset — budget unknown-but-fresh, never read as 100 %) ·
  NO_DATA (no reading) · UNREADABLE (could not look; outranks every other verdict in a run).
- Scan bound: newest 40 rollouts. Only the minimum needed is ported (reader + verdict), not Forja's
  worker-planning.
- The rate meter is per ACCOUNT while rollouts are per UNIX USER. So each provider user publishes its
  newest reading (numbers only, no content) into the shared quota dir (§3); the admission verdict is
  taken over all published readings, freshest first.

## 2. Provider health states (plan §55)
UNKNOWN · AVAILABLE · DEGRADED · UNAVAILABLE · UNAUTHENTICATED · RATE_LIMITED · DISABLED ·
CERTIFIED(host). "Configured" is not a state. UNAUTHENTICATED is decided from the provider's own auth
status command (codex `login status`, claude `auth status`), never from the presence of a file.
CERTIFIED(host) is only ever written by a real epoch on that host.

## 3. Shared quota dir (F4)
`/var/lib/kobii-factory/quota` (root-created, group `kobii-quota` = {kobii, factory}, setgid 2770):
the codex ledger, cooldown, DISABLE flag, published readings, and leases. Both users pin it by env
`GSDX_QUOTA_DIR`; the codex provider reads the DISABLE flag there as well as its legacy `~/.hermes`
path, so the Founder's kill switch stops every user. Adding kobii to the group changes kobii's
identity only by one supplementary group; running kobii processes do not pick it up until restart,
which is the intended conservative behaviour.

## 4. Leases (F14)
One file per scarce resource (`codex-account`, `keos-llm`): holder, heartbeat ts, TTL. Expired leases
are reclaimable; admission never waits past a TTL; a lease is advisory for peers (KEOS, Ágora, Forja
are invited, not forced) and binding for the Factory.

## 5. local-llm provider (plan §38a)
Dispatches a bounded epoch to the OpenAI-compatible server `keos-llm` on 127.0.0.1:8081 (Qwen3-Coder
30B) under the `keos-llm` lease. Free in money, not in capacity. Certified only by a real bounded
epoch on GEX44 that produces a verified artifact; until then its state is UNKNOWN, never AVAILABLE.

## Proof
Unit (fixtures built from the documented rollout shape, including a reset-passed 100 % → RESET_SINCE,
an unreadable dir → UNREADABLE outranking OK, NO_DATA on empty) + GEX44 integration: codex provider
as `factory` reads its own rollouts after the Owner's login; the DISABLE flag set by kobii refuses a
`factory` dispatch (two-sided); an expired lease is reclaimed and a live one respected.
