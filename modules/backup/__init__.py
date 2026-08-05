"""Backup / Snapshot skill -- state-preservation precondition for Deploy.

Spec: vault/specs/backup-skill.md.
Sister axis to Deploy. Precondition for the future Rollback Axis.

The re-exports below are load-bearing, not convenience. This package shares its
name with its own implementation module (`modules/backup/backup.py`), and the
two resolve differently depending on who imports first:

  standalone   `python modules/backup/test_v_block.py` puts this directory on
               sys.path, so the top-level name `backup` binds to backup.py.
  under pytest `modules/` has no __init__.py, so pytest's basedir walk stops
               there, inserts `modules/` on sys.path and imports the test as
               `backup.test_v_block` -- which imports THIS package first and
               caches it as sys.modules['backup']. A later `import backup`
               never consults sys.path again, so it gets the package.

With this file empty, that second path raised ImportError on a name that has
always existed (backup.py:73), and the V-block that passes 15/15 standalone
could not even be collected. Exporting the public API makes both bindings
answer the same way.
"""
from __future__ import annotations

from .backup import DEFAULT_FREE_FLOOR_BYTES, backup, main, validate_config
from .retention import apply_retention
from .verify_restore import verify_restore

__all__ = [
    "DEFAULT_FREE_FLOOR_BYTES",
    "apply_retention",
    "backup",
    "main",
    "validate_config",
    "verify_restore",
]
