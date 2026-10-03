# Pre-commit review — store identity, one producer (2026-10-03)

Reviewer: pp-code-reviewer (read-only; report persisted by the parent session).
Scope: tools/tis_observed.py (store_identity), tools/usage_index.py (consumer; local
_store_dirs/_is_link deleted), tools/test_store_identity_consumers.py,
tools/test_usage_index_identity.py.

**Verdict: APPROVE** — CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 1.

Checks: no plain dir misclassified on the live configuration (normcase both sides; broken
junction skipped by is_dir before realpath, as before); old resolve(strict) fallback not
lost; iteration order only affects which files miss a PARTIAL deadline; gates drive both
poles (exact alias-map equality, out-of-store resolved-present AND link-absent, totals on
aliased vs clean incl. id-less keys).

L1 LOW (DEFERRED, trigger named): a relative `--proj` or a base that is itself a link
makes every dir an alias. Outcome is one verified bulk rewrite to the resolved spelling
(consistent end state), then ~8 unindexed substr probes per alias on every refresh,
before the deadline check. NOT fixed by comparing against real_base/name: that would leave
legacy rows under the unresolved spelling while reads move to the resolved one, i.e. an
id-less double count. Unreachable with the default absolute base (live: realpath spelling
exact for 298/298). Trigger to reopen: any caller passing a relative or linked base.

Note (FIXED in the same commit): V-SIC-UX-ONE-PRODUCER caught only the deleted copy's own
tokens; widened to readlink / is_junction / is_symlink / iterdir(.
