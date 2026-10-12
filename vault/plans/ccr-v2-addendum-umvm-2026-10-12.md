---
covers: [ccr, umvm, multimodal-carry, pixel-rent, image-carry]
goal: ccr
status: ACTIVE
authority: existing goal ccr (cap 36,880,000; RESUMPTION next actions 1-2 already name image carry). No new Owner capital.
---
# CCR v2 addendum 2: Multimodal Context Rent (UMVM under UCVM), 2026-10-12

## Problem
Measured on Madzia worker d6343597 (26 calls, 1,192,066 tok, `evidence/carry_decompose.py`): Read images are
55 % of model-facing carry, but the per-image ~3K token figure is INFERRED (made to reconcile), not measured.
An image read once is re-sent by every later call of the epoch. S4 falsified system-prompt/tool-guidance text as
the dominant rent (negative knowledge, do not reopen without new evidence).

## Host facts (Claude Code 2.1.296 mod API, `claude-code.d.ts`)
- `session.append` (L10574-10646): every row, with `door`, `origin.tool`, `uuid`, `agentId`; media blocks
  "may be dropped or moved, not changed or added". So: an image can be withheld AT APPEND (never enters), not
  rewritten.
- `session.compact` (L10803-10864): a hook on trigger `plugin` may answer `{ messages }`; a message "without
  handle is read as built". Candidate LIVE pixel GC (rebuild the transcript minus dead image blocks).
  UNTESTED: the M1 probe never recorded a compact row. Until proven, epoch rotation is the only proven GC.
- `turn.complete` carries per-call `usage` (already receipted as `ev:usage`).

## Measured 2026-10-12 (M1 + M2 sealed; supersedes the 55 % figure above)
- Cost model: tokens = ceil(w*h/750) of the block AS SENT, no megapixel cap on Opus 5.5 (Read already caps the
  long edge at 2000 px). Calibrated from next-call usage minus known text rows: 1033x917 est 1,264 / meas ~1,318;
  2000x1278 est 3,408 / meas ~3,420 (`evidence/image_carry.py` header).
- Madzia d6343597 (26 calls, 1,192,066 tok): image carry **200,546 = 16.8 %** (13 unique images, 15,985 tok
  once); hard floor 14,401 x 26 = **31.4 %**; text transcript growth ~**52 %** (`evidence/image_carry_d6343597.json`).
  The 55 % came from a char share with an inferred 3K/image: CARRY_ATTRIBUTION_INFERRED_NOT_MEASURED, confirmed.
- Live proof (sid ea47d9c4): mod per-call ctx == provider usage 4/4; a re-read of the same bytes is billed again
  in full (+3,408); rotate advice fired at call 4 (carry 20,416 >= floor 12,086; image 6,816, text 13,600).
- Consequence: pixels are NOT the dominant rent. Image-only GC (D, C) caps at ~14 % of an epoch; epoch rotation
  (B) sheds text and pixels together, model-predicted 36-45 % for 2-3 epochs of a 26-call boundary. B leads; C
  fails Proof of Agent Necessity on these numbers (subagent floor >= the carry of a late image pair).

## Arm D measured 2026-10-12 (fixture, `evidence/umvm_armD/`)
- `$.session.compact()` is refused headless: "not available in a headless (-p / SDK) session yet: compaction here
  runs inside a turn (a /compact prompt)" (HOST_LIMITATION). A driver sends a `/compact` turn instead; the mod's
  `session.compact` hook answers trigger `manual` with a rebuilt kept-set: **zero model calls**.
- Full rebuild (no handles): next call 97,955 vs ~102.8K expected (image 3,408 + attachment rows gone); text recall
  intact. Without a tombstone the model read the empty result as "the image read failed" (false belief); with the
  CCR tombstone it says the image left the context and does not invent colours.
- Mixed kept-set (last messages kept by handle): installed as a NO-OP (next call cache-read the old prefix byte
  for byte). So the hybrid "keep the current pair resident" arm is not expressible in place on 2.1.296.
- Price: GC rewrites the prefix (cw 80,256 on the next call). Ledger tokens: saves ~4.8K per later call. Price
  weighted (cache read = 0.1): the rewrite costs ~92K read-equivalents, repaid only after ~190 calls. Same shape
  for epoch rotation. Ledger-token wins can be price losses: decide per metric, report both.
- Madzia workers p4p2a2/a3: image share 9.3 % / 10.5 %; a3 ran 53 calls, 4,015,727 tok, ctx 20.4K -> 113K.
  Reviewers 45-52 % image but 43-60K total (correct pixel consumers). Text carry is the dominant rent.
- Madzia driver stopped at `OWNER_STRATEGY` (phase 2: 3 hypotheses rejected): no canary until the Owner decides.

## Liveness model (maps to UCVM AVAILABLE -> LINKED -> RESIDENT -> MATERIALIZED)
| State | Meaning | Where it lives |
|---|---|---|
| COLD_ARTIFACT | file on disk, no live dependency | L0 disk, L1 receipt row (hash, dims) |
| WARM_REFERENCE | linked by the current unit, not in the transcript | path + hash in ContextImage |
| SEMANTICIZED | a Visual Semantic Delta (verdict JSON) exists for some boundaries | receipt/verdict file |
| HOT_PIXEL | base64 block in the live transcript, re-sent every call | provider context |
Raw artifacts are never deleted by GC; GC means leaving HOT_PIXEL only.

## Units (execution mode, micro-commits)
1. **M1 carry receipt (observe)**: `session.append` row receipt in the CCR mod: door, tool, text bytes, per image
   {fnv hash, media type, w x h from the PNG/JPEG header, base64 bytes, est tokens = ceil(w*h/750) after the
   provider's 1568-px long-edge downscale}. Plus existing per-call usage. Analyzer turns receipts into a
   per-call carry curve by modality (image / tool-result text / hook / assistant) with zero transcript parsing.
2. **M2 image-cost truth**: calibrate est tokens against the usage delta of the call after an image append in a
   controlled `claude -p` fixture (same prompt with / without one image). Image share becomes MEASURED or BOUNDED.
3. **Experiments** (fixture first, Madzia only at a driver boundary):
   - A resident (baseline: d6343597 data, no re-run).
   - B rotate after visual verdict (driver-side; needs KSR boundary.py change -> driver boundary only).
   - C visual specialist subagent returns verdict JSON (needs Proof of Agent Necessity: startup tax measured).
   - D live pixel GC via plugin compaction (mod-only; only if the host honours a rebuilt kept-set).
   Winner = lowest total tokens per accepted transition at reviewer parity (Madzia reviewer verdict). Stop-loss:
   any reviewer regression kills the arm.
4. **Epoch compiler input**: `rotate` advice file written by the mod when projected image carry of the next call
   exceeds a threshold (advice only; the driver decides).
5. **Knowledge**: negative knowledge (S4), failure classes confirmed by data only.

## Done-gates for this addendum
M1 receipts present on a real run; image tokens measured or bounded with the method named; at least the arms that
the host supports measured; no quality regression; RESUMPTION_FILE updated after each sealed unit.
