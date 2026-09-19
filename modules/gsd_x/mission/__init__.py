"""GSD X Mission Intelligence -- the joins, and nothing more.

GSD owns the lifecycle: phase, plan, task, execution, verification, transition.
Power Pack owns evidence, gates and Production Reality. This package owns the
seams between them that nobody owned:

    contract    a Mission Contract PROJECTED from existing owners, storing only
                the human's verbatim intent and the derived obligations
    obligation  requirements that follow from intent + project reality, with
                provenance, a named consequence, and a disposition
    store       one mission, one file -- not a database, not the claims ledger
    closure     a projection that distinguishes explicit from derived, and can
                refuse to close

Nothing here schedules, plans, executes or verifies. It supplies work and proof
requirements to the owners that already do.
"""
