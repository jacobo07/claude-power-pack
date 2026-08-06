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

REPAIRED 2026-08-06. Those files no longer ERROR. They were never one fault: two were an
"import file mismatch" between identically-named V-blocks in hyphenated directories that
cannot form a dotted module name (fixed by `--import-mode=importlib` in pytest.ini), and
the rest were flat sibling names meaning different things in one process -- `detectors`
in deployment/ and auto-testing/, `runners` in deployment/, rollback/ AND backup/ -- where
the first importer wins the global sys.modules slot whatever a later file prepends to
sys.path (fixed at each source by importing via package path).

They were kept visible here rather than ignored, and that is why they were repairable: the
errors stayed in `collection_errors`, SQI kept folding them into silent loss, and the
queue could be worked. Suppressing them would have made this file's own contract a lie
and left the faults permanent. The repair queue is now empty; the restraint is not.

Note the repair did NOT raise reach: those five files carry a main() driver rather than
test_* functions, so they still contribute 0 collected tests. Collection went 4 errors ->
0 with the count unchanged at 340. Making pytest actually RUN their cases is a separate
change, and one that WOULD move reach -- honestly, by reaching authored surface that has
always been there.
"""

collect_ignore_glob = [
    "_logs/*",              # scratch milestone scripts; body runs at import, ends in sys.exit
    "_quarantine/*",        # quarantined by construction
    "backups/*",            # point-in-time copies, not a test surface
    "vendor/*",             # third-party
    "kpp-distiller-kernel/*",   # vendored kernel
]
