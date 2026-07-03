# Conversation Quality Audit — Detector Design Report (PASO -1)

**Date:** 2026-07-03
**Tool to build:** `tools/conversation_quality_audit.py`
**Reuses:** `tools/token_corpus_audit.py::iter_transcripts` (no re-implementation
of the `.jsonl` reader).
**Complement of:** `token_corpus_audit.py` (volume) — this measures *behavior*.

## Shared infrastructure

A new `parse_conversation(fp)` builds the **ordered** message list per session:
each entry = `{role, text, out_tokens, tools[], write_paths[], ts, idx}`.
`out_tokens` is the REAL `message.usage.output_tokens` (assistant turns) — every
"tokens spent" figure below is measured, not estimated. Cost of a pattern
instance = the offending assistant turn's real `output_tokens` (or a pair sum).

Corpus caveat inherited from the prior audit: sessions can double-count across
working-dir-encoded project dirs. Reported per-session, so a dupe inflates a
count by ≤1 per physical file; noted in output.

## The 5 detectors + false-positive mitigations

### P1 — Agent self-correction (consecutive assistant turns)
- **Signal:** assistant turn T follows assistant turn T-1 (same role, no user
  between) AND T's first ~240 chars match a *strong* correction cue.
- **Cues (strong only):** `I made an error`, `my mistake`, `that was incorrect`,
  `let me fix that`, `correction:`, `I was wrong`, `me equivoqué`, `error mío`,
  `me equivoco`, `corrijo`, `en realidad me`. Bare `actually` is **excluded**
  (too common in normal prose).
- **Cost:** `out_tokens(T-1) + out_tokens(T)` (the wasted original + the redo).
- **FP mitigation:** require consecutive-assistant adjacency (a correction after
  the Owner pointed out the error is NOT self-correction — that's normal); cue
  must be in the turn HEAD, not buried; skip if inside a ``` code fence.

### P2 — Owner repeats instruction
- **Signal:** two Owner messages A, B (A before B, non-adjacent) with Jaccard
  content-word overlap > 0.7, both ≥ 5 significant words, AND the assistant
  turn(s) between A and B contain NO `tool_use` (agent didn't act).
- **Cost:** sum of `out_tokens` of the between-turns (talk without action).
- **FP mitigation:** min 5 significant words kills "ok"/"sí"/"continua" matches;
  stopword-filtered token sets; the "no tool_use between" clause is what
  separates *repeat because ignored* from *natural topic recurrence*.

### P3 — Duplicate Reality Scan (cross-session, same repo)
- **Signal:** a session's first assistant turn text contains a scan cue
  (`Reality Scan`, `FASE -1`, `PREFLIGHT`, `leer antes de`, `read before`,
  `corpus scan`) AND another session in the **same project dir** within **7
  days** has a first-assistant-turn with > 0.6 text overlap.
- **Cost:** `out_tokens` of the *later* (duplicate) scan turn.
- **FP mitigation:** high text-similarity (>0.6) requirement — a genuinely fresh
  scan of changed code reads differently; identical ritual boilerplate is what
  trips it. Only the later of each pair is counted (no double-count).

### P4 — Plan→execution divergence (LOWEST confidence — flagged as such)
- **Signal:** assistant turn generates a plan listing file paths (≥2 paths in a
  bulleted/numbered block) → next Owner msg is a short approval (<20 tokens:
  sí/ok/adelante/go/aprobado/dale) → next assistant turn's `write_paths`
  overlap the planned paths < 0.4.
- **Cost:** `out_tokens` of the divergent execution turn.
- **FP mitigation:** requires explicit path list in the plan (illustrative prose
  won't match); requires the short-approval gate; <0.4 overlap threshold.
  **Reported as low-confidence** — divergence can be a legitimate superset. Any
  fire is surfaced with evidence for human judgement, never auto-fixed.

### P5 — Question already answered (same session)
- **Signal:** assistant turn contains a question (sentence ending `?`, ≥ 6
  words) whose keyword set overlaps > 0.7 with an EARLIER assistant question in
  the same session that had an Owner reply between them.
- **Cost:** `out_tokens` of the repeated-question turn.
- **FP mitigation:** min 6 words; requires an intervening Owner answer (proves
  it was already resolved); stopword-filtered overlap.

## Reporting contract

- Per pattern: total frequency, total token cost, top-3 examples with ≤3-line
  evidence snippets (truncated, redacted of long content).
- Rank patterns by total token cost.
- **Frequency < 5 in whole corpus → "not found significantly", NO fix proposed.**
- **Frequency ≥ 5 → concrete fix** tied to the real examples.
- Sessions with highest pattern density listed.

## Known limitations (honest)
- P4 is heuristic and low-confidence by construction.
- Semantic overlap is keyword-Jaccard, not embeddings — catches lexical repeats,
  misses paraphrase. Under-counts, never over-claims.
- No git-history join for P3 (uses text-similarity as the change proxy).
