"""verticals -- where domain vocabulary is allowed to live.

The parent package is the kernel and is domain-blind, enforced by
`V-SA-KERNEL-DOMAIN-BLIND`, which globs `*.py` at the kernel level only. This
subpackage is deliberately outside that glob: it is the one place a domain noun may
appear, because `universal-meta-systems/runtime/specialization.py::contaminates_kernel`
checks a derivative's vocabulary against KERNEL fields, not against the vertical that
declares it.

A vertical here is not a copy of the kernel. It is a `SpecializationSpec` whose six
components are compiled into contract-field overrides and recorded as a genealogy row,
so an improvement to the kernel still reaches it. `HR-APA-016` refuses a specialization
whose entire delta is naming.

This package carries an explicit `__init__.py` rather than relying on namespace-package
behaviour, so the import path is declared rather than inferred.
"""

__all__ = ["signup"]
