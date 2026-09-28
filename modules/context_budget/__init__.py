"""Context pressure OBSERVATION (native port of context-budget 1.0.0, MIT, vendor/context-budget).

This module measures; it never decides. The policy owner for a mission's context lifecycle is
tools/gsd_epoch.py decide_turn_end, which records a reading from here as evidence.

Deliberate divergence from upstream: upstream's probe that throws contributes 0 ("fail-open"),
so a broken meter reads as a comfortable context. Here a signal that cannot be read is
UNMEASURED, pressure is computed over measured weight only, and the reading states its
coverage, so a caller can never mistake "could not measure" for "low pressure".
"""
from .meter import (BANDS, MEASURED, PARTIAL, UNMEASURED, Budget, Meter, Signal,  # noqa: F401
                    epoch_reading, estimate_tokens, normalize)
