---
title: A serialized Ink screen writes word gaps as cursor-forward
tier: execution
date: 2026-10-18
source: Orca repo docs/dws/live-2026-10-18-row-70-resume-evidence.md (r70r3, commit bf703ebaae; harness 55f1d7fbb6)
status: LESSON -- UKDL entry T-INK-SCREEN-SPACE-IS-CSI-C-001
---

# A serialized Ink screen writes word gaps as cursor-forward

## Evidence
- Live resume of a Claude session on GEX44 (row 70) sat on Claude's folder-trust dialog for three runs (r70r, r70r2, r70r3).
- r70r3's per-state log showed 	rust=false with a stable PTY id: the dialog was on screen, the matcher never saw it.
- Cause: the serialized Ink screen emits CSI C (cursor-forward) between words, so "trust this folder" never appeared as text.
- Fix: map CSI C to a space before stripAnsiEscapeSequences. r70r5 then passed.

## Lesson
A text match over a terminal screen that has only had escape sequences stripped can be blind to a prompt that is plainly visible. Before concluding a dialog is absent, read the raw bytes of the screen once and check what separates the words. A per-state log that names what the matcher saw is what finds it; a retry does not.