#!/usr/bin/env python3
"""KEOS-Qwen -- turning real local-model coding failures into durable evidence.

Canonical import form, and it is not decoration:

    from modules.keos_qwen.outcome import OK, Attempt, classifiable

The phase-4 audit's gap 12 is the sharpest finding in this module's history. The
plan enumerated 28 files and not one `__init__.py`, so the package would not have
imported -- while the very failure seeding its corpus was Qwen writing
`import judge` when the real module is `modules.gsd_x.goal.judge` with relative
imports. The plan reproduced, exactly, the defect it exists to catalogue.

That is not a coincidence worth smiling at. It is the measurement: the failure is
a CONTEXT failure, not an obedience failure, and it does not care whether the
author is a 30B model or the agent auditing it. Both wrote an import path from
what seemed obvious instead of from the tree. Observed 5 of 5 samples across both
arms of the doctrine A/B on 2026-09-24 -- the one failure in this corpus that
replicates perfectly, and the one that fine-tuning should probably never be used
to fix (see the estate's KNOWLEDGE VS WEIGHTS rule).

Source files in this package are deliberately ASCII-only. Gap 13: `open(path,
"w")` truncates BEFORE encoding, so a UnicodeEncodeError leaves a zero-byte file,
and this module writes evidence for a living.
"""

__all__ = ()
