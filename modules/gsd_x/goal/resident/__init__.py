"""GOAL RESIDENT: the goal engine's supervised, restartable driver.

Contract: vault/specs/gdd-resident-driver.md. The resident owns no goal truth,
no judge and no second store of goal state: it runs the engine's reconcile,
dispatches through the engine's providers and writes goal events only through
engine APIs. What it DOES own is its own operational state -- lock, heartbeat,
mission records, intents, gain, leases, census -- under GSDX_RESIDENT_STATE.
"""
