"""Artifact Done-Gate (P2).

Done is an artifact on disk with the declared shape -- not an exit code,
not a fixture-scale passing test, not a correctly-handled error.

    from modules.done_gate import ArtifactContract, Kind, is_done
    ok, res = is_done([ArtifactContract("index", "vault/i.jsonl",
                                        Kind.JSONL, min_count=1000)])
"""
from .artifact_done_gate import (
    PASSING,
    ArtifactContract,
    GateResult,
    Kind,
    Status,
    Verdict,
    gate,
    is_done,
    verify,
    write_receipt,
)

__all__ = [
    "ArtifactContract", "Kind", "Status", "Verdict", "GateResult",
    "verify", "gate", "is_done", "write_receipt", "PASSING",
]
