# Requirements: CCR v5

Source: Owner brief (pane d124ce03, 2026-10-14) and `vault/plans/ccr-v5-svm-imc-2026-10-14.md`.

- REQ-1 Context Rent Ledger attributes the lobby floor by category; project-age vs epoch-age split measured (Phase 1).
- REQ-2 X2 step 5 live; GEX44 breaker fail-closed proven by test; driver versioned (Phase 2).
- REQ-3 Shared institutional mutation: intent, lease, base revision, durable wait, sweep wakeup, validated merge with rollback on any failure; foreign bytes never touched (Phase 3).
- REQ-4 No SEALED with dirty successor-critical continuation unless a certified store owns it (Phase 4).
- REQ-5 Typed semantic pages with stable identity, version, invalidators, L0-L3 disclosure, live dependency closure, served by the CCR `page` tool (Phases 5-6).
- REQ-6 Page fault receipts, fault-storm prefetch, semantic GC at rotation, raw recall preserved (Phase 7).
- REQ-7 Epoch continuation vs rotation decided by measured economics; wall kept as breaker (Phase 8).
- REQ-8 CI: elasticity, overmaterialization, page fault, stale page, raw recall, epoch, conflict, abandoned writer, sealing (Phase 9).
- REQ-9 Lobby Phase 2.1 canary measured against old pane and fresh-session baseline (Phase 10).
- REQ-10 Knowledge Vault / FIOS / UKDL / CBR updated only from proof; A7 never certified without its canary (Phase 11).
