#!/usr/bin/env python3
"""Shared-endpoint ledger for KEOS-Qwen.

    from modules.keos_qwen.ledger.ledger import decide, record

One implementation of the budget, consulted by every caller. The Elixir provider
shells out to `ledger.py` rather than reimplementing the predicate, because two
implementations of one budget are two answers to "how many calls are left" and
which one you get depends on who wrote the caller.
"""

__all__ = ()
