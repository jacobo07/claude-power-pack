"""Rollback Axis -- third executable node of the deploy lifecycle.

Backup (safe) -> Deploy (deliver) -> Rollback (recover).

Public entry: modules.rollback.rollback.rollback(stdin_payload).
Spec: vault/specs/rollback-skill.md (Sealed 2026-05-25).
"""
