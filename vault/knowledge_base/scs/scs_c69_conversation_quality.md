# SCS C69 — Conversation-Quality-Audit-by-default

**Sealed:** 2026-07-03
**Type:** process doctrine + tooling (behavioral axis)
**Slot check:** C67 = Hibernation, C68 = Token-Corpus-Doctrine (both taken) → this is C69.
**Sibling:** `[[scs_c68_token_corpus_doctrine]]` — that axis measures VOLUME; this measures BEHAVIOR.

---

## Doctrine

`tools/conversation_quality_audit.py` detects 5 qualitative inefficiency patterns
in the real `.jsonl` content (complement of `token_corpus_audit.py`, which
measures volume). Run it after **major PP changes** to verify the patterns do not
worsen. Only patterns with **frequency ≥ 5** earn a fix; below that → "not found
significantly", no fix (reality contract).

## Audit result 2026-07-03 (646 sessions)

| Pattern | Freq | Cost (real out-tokens) | Confidence | UKDL |
|---|---|---|---|---|
| P1 agent self-correction | 71 | 370,081 | normal | T-AGENT-SELF-CORRECTION-001 |
| P4 plan→exec divergence | 44 | 249,170 | **LOW (upper bound)** | T-PLAN-EXECUTION-DIVERGENCE-001 |
| P5 question already answered | 33 | 90,349 | normal | T-REPEATED-QUESTION-001 |
| P2 owner repeats instruction | 19 | 74,530 | normal | T-OWNER-REPEAT-INSTRUCTION-001 |
| P3 duplicate reality scan | 0 | 0 | — | NOT FOUND (no fix) |

Total measured behavioral cost of the 4 significant patterns: **~784k output
tokens** across the corpus lifetime.

## FP-hardening (the tool is only as good as its precision)

First run had false positives; hardened before sealing (RCA HALT→TRACE→HEAL→FIX):
- **P2** excludes harness `<local-command-caveat>` / `<system-reminder>` wrappers
  (not Owner instructions; they overlapped only on shared boilerplate).
- **P5** extracts the interrogative CLAUSE (single sentence, cue-bearing), not
  any turn merely containing a `?` (killed preflight/table FPs).
- **P4** requires a plan-intent cue + dedupes identical (planned,exec) pairs;
  still LOW-confidence because "planned" includes read-context files.

## Tooling + verification

```
python tools/conversation_quality_audit.py --report <out>
```
Hermetic test: `tools/test_conversation_quality_audit.py` — 6 V-gates including
`V-FP-HARNESS-EXCLUDED` and `V-FP-NONQUESTION-EXCLUDED`, ×3 stable.

## Cross-references
- Design report: `vault/plans/conversation-quality-audit-2026-07-03.md`
- Findings report: `vault/plans/conversation-quality-report-2026-07-03.md`
- UKDL entries: `vault/knowledge_base/ukdl-universal.md` (T-AGENT-SELF-CORRECTION-001 et al.)
- Volume sibling: `[[scs_c68_token_corpus_doctrine]]`
