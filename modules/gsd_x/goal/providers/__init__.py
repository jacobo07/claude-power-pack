"""Execution providers for goal epochs.

Each one implements the same contract (`..epoch.Provider`) and returns the same
receipt shape, so goal semantics never live inside a provider and a provider can
be replaced without the goal noticing.
"""
