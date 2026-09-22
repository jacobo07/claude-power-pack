"""Execution providers. Each turns an epoch into a receipt; none can satisfy an
obligation by itself -- every receipt goes through receipt.ingest and GSD X closure.

verify   -- autonomous: runs the gate an obligation names.
gsd_long -- worker: prepares an instruction a pane claims; the spine never starts it.
codex    -- autonomous, read-only: analysis only in v1.
Hermes   -- seam only (deferred): its production path is not deployed.
"""
