"""SQI — Sovereign Quality Intelligence, the executable layer.

The corpus (vault/knowledge_base/sqi/) states the laws. This package enforces them.
By SQI-00's Executable Governance Law, a policy without enforcement is documentation.

Five engines, in dependency order:

    repo_reality_scanner   SQI-01       what is actually on the disk
    environment_qualifier  SQI-03       may any result from this host be interpreted at all
    reconcile              SQI-02       what fraction of authored protection is reached
    baseline_guardian      SQI-02 XII   did protection fall -- the derivative, not the level
    weakening_detectors    SQI-02 XV    did the surviving tests stop asserting anything

The last two are the pair, and the pair is the point. The guardian gates COUNTS, so it catches
deletion, the skip, and the relocation -- every failure that lowers a number. Weakening lowers no
number at all: the file is present, the case is collected, the case passes, and the protection is
gone. A guardian without the weakening detectors is a locked door in a building with no walls.

Every engine is fail-open: an unrecognized stack, an absent manifest, or a runner that
cannot be invoked yields UNKNOWN, never an exception and never a zero. Zero is a
measurement; UNKNOWN is the absence of one, and rounding the second to the first is the
attribution error the corpus exists to forbid.
"""

from modules.sqi.repo_reality_scanner import scan_repo, RepoRealityProfile
from modules.sqi.environment_qualifier import qualify, EnvironmentRecord
from modules.sqi.reconcile import reconcile, ReconciliationReport
from modules.sqi.baseline_guardian import check, GuardianVerdict
from modules.sqi.weakening_detectors import (
    count_assertions,
    count_mocks,
    hash_test_content,
    mutation_probe,
)
from modules.sqi.weakening_baseline import check as check_weakening, WeakeningVerdict

__all__ = [
    "scan_repo",
    "RepoRealityProfile",
    "qualify",
    "EnvironmentRecord",
    "reconcile",
    "ReconciliationReport",
    "check",
    "GuardianVerdict",
    "count_assertions",
    "count_mocks",
    "hash_test_content",
    "mutation_probe",
    "check_weakening",
    "WeakeningVerdict",
]
