"""Root pytest configuration.

WHY THIS FILE EXISTS
--------------------
SQI's invocation oracle (`modules/sqi/reconcile.py::discover_invocations`, Part IX)
treats the ZERO-ARGUMENT DEFAULT -- bare `pytest` -- as authoritative whenever no CI
job exists, and this repository has no `.github/workflows`. So bare `pytest` is the
measured canon: it is what an agent, a hook, a done-gate, or a new engineer will run.

Bare `pytest` was aborting with INTERNALERROR and collecting NOTHING.

Cause: pytest's default `python_files` includes `*_test.py`, so it imported the nine
scratch milestone scripts under `_logs/` (`_m1_secret_firewall_test.py` and siblings).
Those are not tests -- they are standalone V-gate scripts whose entire body runs at
module scope and ends in `sys.exit(...)`. The assertion-rewriting importer executes
that body during COLLECTION, `SystemExit` propagates, and pytest aborts the whole run.

One stray scratch file in a log directory disarmed the estate's authoritative test
invocation, and the damage was silent: the only surviving OK invocation was a
DOCUMENTATION-sourced `pytest tests/` reaching 3 files, while the authored surface grew
101 -> 143. Test File Reach fell 2.97% -> 2.1% and the guardian has been reporting
BASELINE_REGRESSION unnoticed, because nothing runs `run_sqi.py` on a gate.

WHAT THIS FILE MAY AND MAY NOT DO
---------------------------------
It excludes trees that are NOT the test surface: scratch logs, quarantine, backups and
vendored code. It does NOT set `testpaths`, and it does NOT exclude `tests/`, `tools/`
or `modules/`.

That restraint is the whole contract. Part IX.1: *an engine that lets the measured party
nominate its own invocation has handed over the denominator and has ceased to measure
anything.* Narrowing collection to make a number look better is that exact move, and it
would also buy reach by shrinking a denominator -- the deletion attack the baseline
guardian's Gate B exists to refuse. Nothing here is permitted to make reach rise. Reach
rises only because collection now REACHES more of the surface that was always authored.

Note: SQI's authored-file scan is independent of pytest collection, so the ignores below
do not lower `authored_count`. The denominator is untouched by construction.

Five files under `modules/*/test_v_block.py` still ERROR on a missing `runners` package.
They are deliberately NOT ignored. They are real collection errors on real orphans
(already ORPHAN in the liveness ledger), pytest records them in `collection_errors`, and
SQI folds that into its silent-loss figure. Hiding them here would be the same handover
this file refuses. They are queued for repair, not suppressed.
"""

collect_ignore_glob = [
    "_logs/*",              # scratch milestone scripts; body runs at import, ends in sys.exit
    "_quarantine/*",        # quarantined by construction
    "backups/*",            # point-in-time copies, not a test surface
    "vendor/*",             # third-party
    "kpp-distiller-kernel/*",   # vendored kernel
]
