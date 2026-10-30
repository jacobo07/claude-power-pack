---
title: UKDL / baseline candidates -- education-first short video production (QuickLease, 2026-10-30)
date: 2026-10-30
status: PARTLY PROMOTED. PROC-019 is committed on a local branch of InfinityOps (feat/edu-checklist-guide, b72b14d1, NOT merged, NOT pushed): it has no operative effect until that branch is merged. Everything else here is a CANDIDATE. This file and tools/video_audio_audit.py are NEW untracked files in a PP tree that held ~1,200 uncommitted entries on feature/knowledge-acquisition, so they were not committed (a commit there would take other sessions' work under this message).
evidence: ql-motion repo (local, C:\Users\User\Apps\ql-motion) EVIDENCE-qlc-edu-v1.md, EVIDENCE-qle-v1.md, EVIDENCE-audio-audit-v1.md, DECISION-PACK-education-first-2026-10-30.md
---

# 1. Ownership sweep
Not re-drafted: `PR-VISUAL-01` (validate against the primary source), `documented-capability-must-be-executable`, the Reality Contract, `instrument-before-claim` (every candidate below is an instance of it). Motion patterns for the web (VP-016 etc.) live in `UKDL_CANDIDATES_MOTION_GRAMMAR.md`; this file is the VIDEO side.

# 2. Promoted (has a tool a future agent can run)
## PROMOTED-1 -- acoustic audit of a finished video, with an honest verdict ceiling
`tools/video_audio_audit.py <video> [--lines <vo-lines.json> --key <id>]` (copy of ql-motion `scripts/audio-audit.py`): audio vs picture duration, loudness, true peak, silent gaps, ASR transcript with word times, script match, speaking rate. The verdict string is fixed at `TRANSCRIBED + ACOUSTIC-MEASURED`; `AUDIO VERIFIED` needs a listener. It caught two real defects no frame review could (12.9 s and 7.7 s of no voice). Prerequisite: ffmpeg/ffprobe on PATH and `faster-whisper`.
Limit proved by use: the voice/bed balance of a finished mix is INCONCLUSIVE when the bed is sidechain-ducked; measure stems instead.

# 3. Candidates (not yet demonstrated beyond one project)
## CAND-VIDEO-1 -- every on-screen text has a ledger entry and the gate must not read your provenance field as text
A ledger + checker (ql-motion `scripts/claims-check.mjs`, 9/9 tests) where text keys are scanned from the timeline JSON. Lesson: a provenance field named like a field the checker treats as content (`status` inside `rows[]`) fails the gate; use a name outside the scanned set (`origin`). Fix the data, never loosen the checker.
## CAND-VIDEO-2 -- one data-driven scene, many pieces
One composition (headline + N rows + closing + CTA + brand) driven by timeline JSON (`QLEduScenes.tsx`) gave three different pieces; the row meaning (who decides / process steps / questions) is data. Distinct awareness, belief, AHA, CTA and function per piece, recorded in the timeline's `learning` block.
## CAND-VIDEO-3 -- long renders run detached, polled with a bound
An interactive ssh dropped mid-render. Launch the job with `nohup ... &` behind `ssh -n`, poll the log with a hard deadline, reap your own hung client by pid after checking its command line (another pane's ssh looks identical).
## CAND-VIDEO-4 -- a CTA names what the page IS
"Read the checklist" pointed at a page that is a guide; the destination check is a live fetch plus a label match, not "the URL exists" (see PROC-019).
## CAND-VIDEO-5 -- reconciling a claim means reading the deployed surface
A stale local checkout produced a contradiction that did not exist (PROC-019, promoted on a local branch).
## CAND-VIDEO-6 -- text-edit tools can silently normalise line endings
An Edit on a file with 40 LF-only lines among CRLF lines rewrote all 40 and made an 11-line change look like 51 insertions and 40 deletions; the concurrent-writers hook caught it. Rebuild from `git show HEAD:path` bytes plus the intended block and confirm `git diff --stat` before committing.

# 4. What would make a candidate real
Each needs a second project to use it (or a mutant test that fails when it is removed). PROMOTED-1 needs a command or skill that names it, otherwise future agents will not find it; PROC-019 needs the InfinityOps branch merged.
