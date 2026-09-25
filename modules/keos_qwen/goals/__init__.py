"""Goal firing: the bounded, metered, unattended leg of KEOS-Qwen.

This package exists for the reason the parent's `__init__.py` records: the
original plan enumerated 28 files with no `__init__.py` anywhere, while the
very failure seeding this corpus was Qwen writing `import judge` instead of
`modules.gsd_x.goal.judge`. A package that cannot be imported by its own gate
is a package whose gate proves nothing.

ASCII only, deliberately. `open(path, "w")` truncates BEFORE encoding, so a
non-ASCII byte on a host with a latin1 default leaves a zero-byte source file --
and the measured GEX44 VM warns it runs with "native name encoding of latin1"
whenever the unit's locale is not pinned.
"""
