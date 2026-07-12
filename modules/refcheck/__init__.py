"""Reference Integrity Linter (P4).

Every path a doc names is resolved against the filesystem. Broken refs,
stale-user paths, and credential-shaped files are surfaced. A prompt
with a dead path does not error -- it quietly does less.

    from modules.refcheck import lint, render
    rep = lint([Path("governance"), Path("vault")])
    print(render(rep))
"""
from .linter import (
    Credential,
    Origin,
    Reference,
    RefStatus,
    Report,
    check_doc,
    extract_refs,
    lint,
    render,
    scan_credentials,
)

__all__ = [
    "lint", "render", "check_doc", "extract_refs", "scan_credentials",
    "Report", "Reference", "RefStatus", "Origin", "Credential",
]
