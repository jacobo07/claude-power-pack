"""SQI-02 Part XV -- the weakening baseline. What the count-based guardian is blind to.

Part XII gates counts, so it catches deletion, the skip, and the relocation. This gates the
CONTENT of the surviving tests, because the ten weakenings of Part XV lower no count at all: the
file is present, the case is collected, the case passes, and the protection is gone (15.1).

    gate A   assertions FELL for a file                              WEAKENED   15.2
    gate B   mocks ROSE while assertions did NOT rise                WEAKENED   15.6
    gate C   the hash moved while the arithmetic did not             REVIEW     15.4 / 15.9
    gate D   broad-catch handlers rose                               REVIEW     15.3
    --       mocks >= 4 in a file                                    ADVISORY   estate standard

ONE store, not three, and the reason is not tidiness. 15.6 is a predicate over TWO numbers -- "a
test whose mock count rose while its assertion count did not" -- and three independent baseline
files cannot express it without one of them reaching into another's state. It would also fork the
firewall, the ratchet, and the acceptance path that `baseline_guardian` already owns, three times
over (T-SQI-PARALLEL-SYSTEM-001).

TWO GATES ARE ADVISORY ON PURPOSE, and this is the Part speaking, not a concession. 15.3 says the
broad-handler detector's output is "a candidate list for review rather than a verdict, because a
broad handler is sometimes correct." 15.4 says of the unreal fixture that "there is no counting
detector for this and it would be dishonest to claim one." An instrument that failed a build on
either would be wrong often enough to be switched off, and a switched-off gate protects nothing --
which is the entire subject of this corpus.

THIS BASELINE IS NOT KEYED BY THE ENVIRONMENT, and the departure from Part XII is deliberate. The
Part XII key exists because EXECUTION results vary by toolchain -- 1,606 assertions under the
correct runtime and zero under one a version behind -- so a comparison across keys is not a
comparison (12.4). These counts are STATIC: they are read from the syntax tree, and a file has the
same number of assertions on every host in the estate. Keying them to the environment would mean
that moving to another machine silently reset the weakening baseline, and "run it on a different
host" would become the cheapest way to erase every assertion you had removed. The environment is
RECORDED here for provenance. It is never a reason to withhold a verdict.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import weakening_detectors as D

PASS = "WEAKENING_PASS"
WEAKENED = "WEAKENED"
REVIEW = "WEAKENING_REVIEW"
CREATED = "WEAKENING_BASELINE_CREATED"
UNKNOWN = "WEAKENING_UNKNOWN"

# Only one of these fails a build. A gate that fails on a candidate list is a gate that gets
# disabled within a week, and 15.3/15.4 both produce candidate lists by construction.
FAILING = {WEAKENED}

BASELINE_VERSION = 1


def default_baseline_path(repo: Path) -> Path:
    env = os.environ.get("SQI_WEAKENING_BASELINE_PATH")
    if env:
        return Path(env)
    return Path(repo) / "vault" / "audits" / "sqi_weakening_baseline.json"


@dataclass
class Weakening:
    """A named loss of protection inside a file that still exists and still passes."""

    gate: str            # "assertions" | "mocks" | "content" | "handlers"
    path: str
    baseline: Any
    observed: Any
    severity: str        # "WEAKENED" | "REVIEW" | "ADVISORY"
    note: str = ""


@dataclass
class WeakeningVerdict:
    verdict: str
    weakenings: list[Weakening] = field(default_factory=list)
    reviews: list[Weakening] = field(default_factory=list)
    advisories: list[Weakening] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    files_tracked: int = 0
    # 15.2, stated as a list of paths. A file with no assertion and no exit-code gate executes
    # code and verifies nothing: it is not a test, it is an execution, and every runner on earth
    # reports it as passing. It is also the one population this module can never protect -- its
    # count is zero, and zero cannot fall.
    no_verification: list[str] = field(default_factory=list)
    updated: bool = False
    baseline_path: str = ""
    summary: str = ""
    error: str | None = None

    @property
    def failing(self) -> bool:
        return self.verdict in FAILING

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("weakenings", "reviews", "advisories"):
            d[k] = [asdict(w) for w in getattr(self, k)]
        d["failing"] = self.failing
        return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def snapshot(records: dict, commit: str, env_key: str | None) -> dict:
    return {
        "version": BASELINE_VERSION,
        "recorded": _now(),
        "commit": commit,
        "environment_key": env_key,   # provenance only -- never gates (see the module docstring)
        "files": records,
        "reason": "",
        "author": "",
        "accepted_losses": [],
    }


def load_baseline(path: Path) -> tuple[dict | None, str | None]:
    """Fail-open to UNKNOWN, never to a false PASS. A guard that cannot read its baseline cannot
    substantiate any claim about the derivative, and saying so is the honest output."""
    path = Path(path)
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return None, f"weakening baseline unreadable: {exc}"
    if not isinstance(data, dict) or "files" not in data or not isinstance(data["files"], dict):
        return None, "weakening baseline malformed: missing required field (files)"
    return data, None


def save_baseline(path: Path, data: dict) -> bool:
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def _gates(base_files: dict, cur_files: dict) -> tuple[list, list, list, list, list]:
    weakenings: list[Weakening] = []
    reviews: list[Weakening] = []
    advisories: list[Weakening] = []
    unknowns: list[str] = []
    no_verification: list[str] = []

    for rel, cur in sorted(cur_files.items()):
        if cur.get("verification") == "none":
            no_verification.append(rel)
        counts_known = cur.get("assertions") is not None
        if not counts_known:
            # UNKNOWN is not a finding; it is the absence of one. Coercing an unparseable file --
            # or one whose protection is an exit-code gate rather than an assertion -- to ZERO
            # would do one of two bad things: manufacture a weakening event out of a syntax error,
            # or hand the gate a number that can never fall and call the file protected. Neither
            # is honest. The file is still tracked BY HASH below, and gate C is the only gate that
            # covers it: a silent rewrite will surface as a review candidate.
            unknowns.append(f"{rel}: {cur.get('error') or 'counts unavailable'}")

        if cur.get("mocks") is not None and cur["mocks"] >= D.MOCK_SMELL_FLOOR:
            advisories.append(
                Weakening(
                    gate="mocks", path=rel, baseline=None, observed=cur["mocks"],
                    severity="ADVISORY",
                    note=f"{cur['mocks']} mocked collaborators. Past this point the unit under "
                         f"test is the only real object in the room, and the test is asserting "
                         f"that a function calls the stubs it was told to call (15.6).",
                )
            )

        base = base_files.get(rel)
        if not base:
            continue   # a new file is an increase, and increases are free.

        # --- Gate C (15.4 / 15.9): the content moved and the arithmetic did not. It runs FIRST
        # because it is the only gate that survives an inapplicable assertion count -- the
        # exit-code-gate files are covered by nothing else in this module.
        #
        # This is the signature of the unreal fixture, a payload that was realistic and is now
        # minimal, and of the same-name rewrite: a test deleted and reintroduced under the same
        # name with a weaker body has kept its identity, kept its count, and lost its content.
        # REVIEW, never a verdict: 15.4 says a counting detector for the fixture would be
        # dishonest, and this signal fires for every honest refactor too. ---
        arithmetic_still = (
            cur.get("assertions") == base.get("assertions")
            and cur.get("mocks") == base.get("mocks")
            and cur.get("cases") == base.get("cases")
        )
        if base.get("sha256") and cur.get("sha256") and cur["sha256"] != base["sha256"] \
                and arithmetic_still:
            reviews.append(
                Weakening(
                    gate="content", path=rel,
                    baseline=base["sha256"][:12], observed=cur["sha256"][:12],
                    severity="REVIEW",
                    note="the file changed and every count held. That is what an honest refactor "
                         "looks like -- and it is also the exact signature of a weakened fixture "
                         "(15.4) and of a same-name rewrite (15.9), which no count can reveal. "
                         "A change to a fixture is a change to what the test MEANS, and deserves "
                         "the attention a changed assertion would receive.",
                )
            )

        if not counts_known or base.get("assertions") is None:
            continue   # gates A, B and D each need two comparable integers.

        # --- Gate A (15.2): the removed assertion. An assertion is the only thing in a test that
        # can fail, so a test that lost one passes MORE reliably than it did before. ---
        if cur["assertions"] < base["assertions"]:
            weakenings.append(
                Weakening(
                    gate="assertions", path=rel,
                    baseline=base["assertions"], observed=cur["assertions"],
                    severity=WEAKENED,
                    note=f"assertions fell {base['assertions']} -> {cur['assertions']} while the "
                         f"file, its cases, and its green status all held. A test with zero "
                         f"assertions is not a test; it is an execution, and every runner "
                         f"reports it as passing (15.2).",
                )
            )

        # --- Gate B (15.6): over-mocking, as a DELTA on two absolutes. Never as the ratio
        # mocks/assertions: that ratio falls when assertions rise, and the cheapest way to raise
        # an assertion count is to add `assert result is not None` -- an assertion that passes for
        # every implementation including a broken one. A ratio gate would be quieted by weakening
        # 15.8, the very attack this Part exists to catch. ---
        if (
            cur["mocks"] is not None and base.get("mocks") is not None
            and cur["mocks"] > base["mocks"]
            and cur["assertions"] <= base["assertions"]
        ):
            weakenings.append(
                Weakening(
                    gate="mocks", path=rel,
                    baseline={"mocks": base["mocks"], "assertions": base["assertions"]},
                    observed={"mocks": cur["mocks"], "assertions": cur["assertions"]},
                    severity=WEAKENED,
                    note=f"mocked collaborators rose {base['mocks']} -> {cur['mocks']} while the "
                         f"assertion count did not rise. The test has moved away from reality "
                         f"without moving away from green (15.6).",
                )
            )

        # --- Gate D (15.3): the widened handler, which most often ships inside a sincere repair.
        # REVIEW by the Part's explicit instruction: a broad handler is sometimes correct. ---
        if cur.get("broad_catches") is not None and base.get("broad_catches") is not None \
                and cur["broad_catches"] > base["broad_catches"]:
            reviews.append(
                Weakening(
                    gate="handlers", path=rel,
                    baseline=base["broad_catches"], observed=cur["broad_catches"],
                    severity="REVIEW",
                    note="broad exception handlers rose. The test may now pass when the system "
                         "does the wrong thing, because the wrong thing is inside the class the "
                         "handler tolerates (15.3). Sometimes correct -- hence a candidate for "
                         "review, not a verdict.",
                )
            )

    return weakenings, reviews, advisories, unknowns, no_verification


def check(
    report,
    env_key: str | None = None,
    *,
    repo: Path | None = None,
    baseline_path: Path | None = None,
    accept: bool = False,
    reason: str = "",
    author: str = "",
    records: dict | None = None,
) -> WeakeningVerdict:
    """Compare the content of the authored suite against the recorded baseline.

    `accept=True` is the only path that may record a LOWERED assertion or a raised mock count,
    and it exists to satisfy 15.10, whose firewall is identical in shape to Part XII's: the party
    blocked by a test may not, within the same task, be the party that weakens it. Fault must be
    attributed before a repair is chosen, and a weakening whose fault attribution was never
    performed is not a repair -- it is a surrender with a passing suite.
    """
    repo = Path(repo) if repo else Path.cwd()
    path = Path(baseline_path) if baseline_path else default_baseline_path(repo)

    try:
        cur_files = records if records is not None else D.scan(repo, report.authored_files)
    except Exception as exc:  # noqa: BLE001 -- a crashed detector is UNKNOWN, never a silent pass
        return WeakeningVerdict(
            verdict=UNKNOWN, baseline_path=str(path), error=str(exc),
            summary=f"{UNKNOWN}: the detector crashed and no claim about weakening is licensed. "
                    f"This is NOT a pass.",
        )

    current = snapshot(cur_files, getattr(report, "commit", "UNKNOWN"), env_key)
    base, err = load_baseline(path)

    if err:
        return WeakeningVerdict(
            verdict=UNKNOWN, files_tracked=len(cur_files), baseline_path=str(path), error=err,
            summary=f"{UNKNOWN}: {err}. The guard is disarmed; no claim about weakening is "
                    f"licensed. This is NOT a pass.",
        )

    if base is None:
        save_baseline(path, current)
        total_a = sum(f.get("assertions") or 0 for f in cur_files.values())
        return WeakeningVerdict(
            verdict=CREATED, files_tracked=len(cur_files), updated=True, baseline_path=str(path),
            summary=f"{CREATED}: first run. Recorded {len(cur_files)} authored test file(s), "
                    f"{total_a} assertion(s), and a content hash for each. From here, a file that "
                    f"loses an assertion fails the build.",
        )

    weakenings, reviews, advisories, unknowns, no_verif = _gates(base["files"], cur_files)

    if weakenings and not accept:
        head = "; ".join(f"{w.gate}@{w.path}: {w.baseline} -> {w.observed}" for w in weakenings[:3])
        more = f" (+{len(weakenings) - 3} more)" if len(weakenings) > 3 else ""
        return WeakeningVerdict(
            verdict=WEAKENED, weakenings=weakenings, reviews=reviews, advisories=advisories,
            unknowns=unknowns, no_verification=no_verif, files_tracked=len(cur_files), updated=False,
            baseline_path=str(path),
            summary=f"{WEAKENED}: {head}{more}",
        )

    if weakenings and accept:
        accepted = dict(current)
        accepted["reason"] = reason
        accepted["author"] = author
        accepted["accepted_losses"] = [asdict(w) for w in weakenings]
        save_baseline(path, accepted)
        return WeakeningVerdict(
            verdict=PASS, weakenings=weakenings, reviews=reviews, advisories=advisories,
            unknowns=unknowns, no_verification=no_verif, files_tracked=len(cur_files), updated=True,
            baseline_path=str(path),
            summary=f"{PASS} (weakening ACCEPTED by explicit attribution) author={author!r} "
                    f"reason={reason!r}; {len(weakenings)} loss(es) recorded.",
        )

    # Nothing weakened. The baseline tracks the current content: an assertion added is an
    # increase, and increases ratchet.
    current["reason"] = base.get("reason", "")
    current["author"] = base.get("author", "")
    current["accepted_losses"] = base.get("accepted_losses", [])
    updated = save_baseline(path, current)

    total_a = sum(f.get("assertions") or 0 for f in cur_files.values())
    verdict = REVIEW if reviews else PASS
    return WeakeningVerdict(
        verdict=verdict, weakenings=[], reviews=reviews, advisories=advisories,
        unknowns=unknowns, no_verification=no_verif, files_tracked=len(cur_files),
        updated=updated, baseline_path=str(path),
        summary=f"{verdict}: {len(cur_files)} file(s) tracked, {total_a} assertion(s), "
                f"{len(reviews)} for review, {len(advisories)} advisory, "
                f"{len(unknowns)} unknown, {len(no_verif)} verifying NOTHING. "
                f"No assertion was lost.",
    )
