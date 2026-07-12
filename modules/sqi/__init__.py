"""SQI — Sovereign Quality Intelligence, the executable layer.

The corpus (vault/knowledge_base/sqi/) states the laws. This package enforces them.
By SQI-00's Executable Governance Law, a policy without enforcement is documentation.

Three engines, in dependency order:

    repo_reality_scanner   SQI-01  what is actually on the disk
    environment_qualifier  SQI-03  may any result from this host be interpreted at all
    reconcile              SQI-02  what fraction of authored protection is reached

Every engine is fail-open: an unrecognized stack, an absent manifest, or a runner that
cannot be invoked yields UNKNOWN, never an exception and never a zero. Zero is a
measurement; UNKNOWN is the absence of one, and rounding the second to the first is the
attribution error the corpus exists to forbid.
"""

from modules.sqi.repo_reality_scanner import scan_repo, RepoRealityProfile
from modules.sqi.environment_qualifier import qualify, EnvironmentRecord
from modules.sqi.reconcile import reconcile, ReconciliationReport

__all__ = [
    "scan_repo",
    "RepoRealityProfile",
    "qualify",
    "EnvironmentRecord",
    "reconcile",
    "ReconciliationReport",
]
