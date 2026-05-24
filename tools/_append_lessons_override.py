#!/usr/bin/env python3
"""One-shot atomic append of the verify_spp override-authorization note
to vault/knowledge_base/session_lessons.md. Used once after Owner
authorized Camino 1 (override and push) on 2026-05-24. Idempotent: if
the note marker is already present, skips.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

P = Path("vault/knowledge_base/session_lessons.md")
MARKER = "verify_spp override authorization -- Prompt Lint Signal push"

NOTE = """

### verify_spp override authorization -- Prompt Lint Signal push (2026-05-24)

verify_spp.py tenia 3 FAILs preexistentes al merge del Prompt Lint
Signal. Override autorizado por Owner porque los FAILs no son
causados por el cambio de esta sesion:

- mirror-parity: 8 de 9 archivos untracked son ajenos al cambio
  (ultra.md, oneshot-architect-auditor.md, cpp-resume-sovereign.md,
  learning-sentinel.js, hook-dispatcher.js, lazarus-livesnap.js,
  zero-issue-gate.js, jobs-woz-gatekeeper.js). apex-completion-standard.md
  aparece tambien pero por ref manifest desactualizado, no por
  byte-equality (drift-report ahora PASS).
- paths+secrets: FileNotFoundError [WinError 2] -- herramienta
  preexistente rota.
- rtk-fusion: -169.2% reduction en `git log --stat -50` -- caveat
  documentado en CLAUDE.md ("command-specific by nature").

Production Branch Standard: push con FAILs preexistentes requiere
documentacion explicita del motivo. Esta nota cumple ese contrato.
Esos 3 rows deben tratarse como deuda separada -- no permitir que
su persistencia normalice el push-con-FAILs en sesiones futuras.
"""


def main() -> int:
    if not P.is_file():
        print(f"missing: {P}", file=sys.stderr)
        return 2
    body = P.read_text(encoding="utf-8")
    if MARKER in body:
        print("note already present; skip (idempotent)")
        return 0
    new = body if body.endswith("\n") else body + "\n"
    new += NOTE
    fd, tmp = tempfile.mkstemp(prefix=".lessons.", suffix=".tmp",
                               dir=P.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        os.replace(tmp, P)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print(f"appended; total {P.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
