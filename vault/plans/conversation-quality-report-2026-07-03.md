# Conversation Quality Audit -- Behavioral Report

**Generated:** 2026-07-03 15:32  
**Sessions analyzed:** 646  
**Source:** `~/.claude/projects/*/*.jsonl` content (real turns).  
**Cost = real `message.usage.output_tokens` of the offending turn.**  
**FP-hardened:** harness wrappers excluded (P2), interrogative-clause gating (P5), plan-intent cue + dedupe (P4).

## Ranking by total token cost

| Pattern | Freq | Total tokens | Confidence | Fix? |
|---|---|---|---|---|
| agent self-correction | 71 | 370,081 | normal | yes |
| plan->execution divergence | 44 | 249,170 | LOW | yes |
| question already answered | 33 | 90,349 | normal | yes |
| owner repeats instruction | 19 | 74,530 | normal | yes |
| duplicate reality scan (cross-session) | 0 | 0 | normal | no (<5) |

## P1 -- agent self-correction

- Frequency: **71**, total cost **370,081** tokens, confidence: normal
- Top examples (cost / project / sid / evidence <=3 lines):
  - `21,436` `C--Users-User-Desktop-Curs` `c39f6153` -- Reescribo `NicheDemo` (locale-aware, NICHES es/en + chrome; corrijo `saveAmt` para parsear dígitos con cualqui
  - `18,832` `C--Users-User-Desktop-Curs` `68a5c938` -- **R6 — your exact ask:** *"just do a byte-level calco, y usa playwright para asegurarte de que esten iguales,  / **What I understand you want (and where I was wrong):** stop "re-presenting/adapting" the design — instead rep
  - `15,422` `C--Users-User-Desktop-Curs` `d58eaa25` -- Hallazgo grande y **contradice la premisa**. Pero la desensamblación dio 0 instrucciones (bug de modo capstone
- **Fix:** Verify before emitting (superpowers:verification-before-completion). A self-correction pair = the first turn shipped an unverified claim. Gate: observe evidence before the DONE/assert turn.

## P2 -- owner repeats instruction

- Frequency: **19**, total cost **74,530** tokens, confidence: normal
- Top examples (cost / project / sid / evidence <=3 lines):
  - `26,826` `C--Users-User-Desktop-Curs` `77f2c804` -- "Acceso bloqueado: claude-router no ha completado el proceso de verificación de Google / marialuisa@costaluzlawyers.es / claude-router no ha completado el proceso de verificación de Google. En estos momentos, la app se está proband
  - `26,826` `C--Users-User-Desktop-Curs` `77f2c804` -- Acceso bloqueado: claude-router no ha completado el proceso de verificación de Google / marialuisa@costaluzlawyers.es / claude-router no ha completado el proceso de verificación de Google. En estos momentos, la app se está proband
  - `12,652` `C--Users-User-Desktop-Curs` `77f2c804` -- "Acceso bloqueado: claude-router no ha completado el proceso de verificación de Google / marialuisa@costaluzlawyers.es / claude-router no ha completado el proceso de verificación de Google. En estos momentos, la app se está proband
- **Fix:** The agent talked without acting between two identical Owner asks. On any imperative, the next turn must contain the tool_use that executes it, or an explicit blocker -- never prose-only acknowledgement. NOTE: hits concentrate in error-retry sessions (Owner re-pastes the same unresolved blocker); same failure family, real signal.

## P3 -- duplicate reality scan (cross-session)

Frequency **0** (< 5). Not found with significant frequency -- **no fix proposed.**

## P4 -- plan->execution divergence

- Frequency: **44**, total cost **249,170** tokens, confidence: LOW
- Top examples (cost / project / sid / evidence <=3 lines):
  - `51,750` `C--Users-User-Desktop-Curs` `43773144` -- planned=['GOLD_STANDARD_SERVERS.md', 'OWNER_DECISIONS_PENDING.md', 'apex-completion-standard.md'] exec=['KobiMapEngine_Dataset_Estado_Actual.md']
  - `13,128` `C--Users-User-Desktop-Curs` `c4d65b5c` -- planned=['MEMORY.md', 'wii_runtime_program_generator.md'] exec=['kobii_heap_audit.h']
  - `10,745` `C--Users-User-Desktop-Curs` `5f9028b0` -- planned=['credentials.json', 'oauth_client_secret.json', 'router.py'] exec=['_r47_patch_router.py']
- **Fix:** Bind execution to the approved plan's file list (HR-ONESHOT-002 fidelity lock). If executed files diverge >40% from plan, pause and re-confirm rather than silently redoing. CAVEAT (LOW conf): 'planned' = all paths in the plan block, INCLUDING read-context files, so this count is an UPPER BOUND; each hit needs manual review, not auto-fix.

## P5 -- question already answered

- Frequency: **33**, total cost **90,349** tokens, confidence: normal
- Top examples (cost / project / sid / evidence <=3 lines):
  - `6,714` `C--Users-User-Desktop-Curs` `23b23351` -- ¿Apruebas el plan para ejecutar A→B→C autónomo
  - `5,334` `C--Users-User--claude-skil` `3f8d60d4` -- ### a) ¿JIT detecta prompts vagos y añade contexto
  - `5,334` `C--Users-User--claude-skil` `3f8d60d4` -- ### a) ¿JIT detecta prompts vagos y añade contexto
- **Fix:** Consult the Findings Bus (PM-03) before asking. RedundancyTax.reason_or_reuse covers already-answered questions in the same session.

---
*tools/conversation_quality_audit.py -- behavioral axis.*