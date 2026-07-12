"""SQI-02 Part XII — the Baseline Guardian. Protection may not be withdrawn in silence.

The reconciliation engine measures a STATE. This measures the DERIVATIVE, and the derivative is
where the estate's most dangerous events live, because the states are frequently acceptable and
the transitions between them are frequently not (12.1). A repository whose executed count was
4,368 last week and is 4,090 today, with a green build, has lost 278 tests to a mechanism nobody
chose and nobody noticed -- and the loss is invisible in every artifact the pipeline produces,
because the pipeline reports a pass rate, and the pass rate is one hundred percent of a smaller
population.

The contract is a single asymmetry (12.2): AN INCREASE REQUIRES NOTHING, AND A DECREASE FAILS
THE BUILD. The guardian has no opinion about whether the tests are good, whether the count is
high enough, or whether coverage is adequate. It cares only that protection is not withdrawn in
silence.

Three absolutes are gated, and the second exists because gating a RATIO would defeat the whole
instrument. `reach = reached / authored`. Deleting the 97 orphaned test files in this repository
raises reach from 3.0% to 100% and leaves the executed count untouched -- a guardian that gated
on the ratio alone would report a triumph while the repository lost 97 test files. That is Part
XVIII's FIRST attack, and its countermeasure is that the ABSOLUTE counts must not fall (18.2).

    A  executed cases, PER ROOT      protection withdrawn (a skip, a scope line, a relocation)
    B  authored test files           the deletion attack (15.9, 18.2)
    C  Test File Reach               drift: code growing faster than its protection (Part XIV)

Baselines are per-root, never a repository total: a total is a sum, a sum permits redistribution,
and an entire root can die while a growing sibling absorbs the difference (12.3). They carry NODE
IDENTITIES, not counts, because a delta of three is an alarm and three names are an action (12.5).
They are keyed by the ENVIRONMENT, because the same repository yields 1,606 assertions under one
toolchain and zero under a runtime one major version behind, and a comparison across differing
environment keys is not a comparison -- it is two measurements of two different systems (12.4).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Verdicts. UNKNOWN is never a PASS: a guardian whose baseline it cannot read is a guardian that
# is disarmed, and a disarmed guard reporting success is the exact artifact this corpus exists
# to discredit.
PASS = "BASELINE_PASS"
REGRESSED = "BASELINE_REGRESSION"
CREATED = "BASELINE_CREATED"
ENV_MISMATCH = "BASELINE_ENVIRONMENT_MISMATCH"
UNKNOWN = "BASELINE_UNKNOWN"

FAILING = {REGRESSED}

BASELINE_VERSION = 1

# Reach is a ratio of two integer counts, so a re-measurement of an unchanged repository can
# differ in the last bits of the float. A guardian that alarmed on that would be a guardian that
# alarms on nothing, and one that alarms on nothing is trained out of the reader within two
# iterations. This tolerance is for float representation ONLY -- it is not a tolerance on real
# loss, and it must never be widened to quiet a genuine alarm (12.8: a guardian that quietly
# widens its tolerance until the alarms stop has been defeated by the thing it was built to catch).
REACH_FLOAT_EPSILON = 1e-9


def default_baseline_path(repo: Path) -> Path:
    """Overridable for tests. A gate that writes to a global path is not hermetic, and a
    non-hermetic gate fails on its own second run."""
    env = os.environ.get("SQI_BASELINE_PATH")
    if env:
        return Path(env)
    return repo / "vault" / "audits" / "sqi_baseline.json"


@dataclass
class Regression:
    """A named loss. Not a delta -- a delta of three is an alarm, and three names are an
    action (12.5). A party investigating a bare number spends an hour reconstructing what the
    guardian could have handed them."""

    gate: str            # "executed" | "authored" | "reach"
    root: str
    baseline: Any
    observed: Any
    lost_identities: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class GuardianVerdict:
    verdict: str
    regressions: list[Regression]
    baseline_env: str | None
    observed_env: str | None
    updated: bool
    baseline_path: str
    summary: str
    error: str | None = None

    @property
    def failing(self) -> bool:
        return self.verdict in FAILING

    def to_dict(self) -> dict:
        d = asdict(self)
        d["regressions"] = [asdict(r) for r in self.regressions]
        d["failing"] = self.failing
        return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _roots_from(report) -> dict:
    """One entry per OK invocation. The invocation IS the root unit: reach is a function of two
    arguments, and quoting a figure without naming its invocation is not a weak measurement --
    it is not a measurement (SQI-02 2.8)."""
    roots: dict[str, dict] = {}
    for inv in report.invocations:
        if inv.status != "OK":
            continue
        roots[inv.command] = {
            "invocation": inv.command,
            "oracle": inv.oracle,
            "executed_cases": inv.executed_cases or 0,
            "executed_files": sorted(inv.executed_files),
        }
    return roots


def snapshot(report, env_key: str | None) -> dict:
    """The baseline records more than a count, and the additional fields are what make it
    un-gameable (12.5)."""
    return {
        "version": BASELINE_VERSION,
        "recorded": _now(),
        "commit": report.commit,
        "environment_key": env_key,
        "roots": _roots_from(report),
        "authored_count": report.authored_count,
        "authored_identities": sorted(report.authored_files),
        "test_file_reach": report.test_file_reach,
        "reason": "",
        "author": "",
        "removed_identities": [],
    }


def load_baseline(path: Path) -> tuple[dict | None, str | None]:
    """Fail-open to UNKNOWN, never to a false PASS. A corrupt baseline means the guard cannot
    substantiate any claim about the derivative, and saying so is the honest output."""
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return None, f"baseline unreadable: {exc}"
    if not isinstance(data, dict) or "roots" not in data or "authored_count" not in data:
        return None, "baseline malformed: missing required fields (roots, authored_count)"
    return data, None


def save_baseline(path: Path, data: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def check(
    report,
    env_key: str | None = None,
    *,
    repo: Path | None = None,
    baseline_path: Path | None = None,
    accept: bool = False,
    reason: str = "",
    author: str = "",
) -> GuardianVerdict:
    """Compare the current report against the recorded baseline.

    `accept=True` is the ONLY path by which a baseline may be LOWERED, and it exists to satisfy
    the firewall of 12.7: the party whose change caused the decrease may not, in the same task,
    author the baseline update that permits it. The reason is not suspicion of that party; it is
    that when a gate is the only object between an agent and completion, editing the gate is one
    write and every honest path is work, and the gradient is followed by sincere parties as
    reliably as by hostile ones. A baseline lowered calmly, in its own commit, with a stated
    reason, is governance. The same baseline lowered inside the commit that made it necessary is
    an escape.

    The guardian does not prevent deletion. It prevents deletion from being INVISIBLE.
    """
    repo = Path(repo) if repo else Path.cwd()
    path = Path(baseline_path) if baseline_path else default_baseline_path(repo)

    current = snapshot(report, env_key)
    base, err = load_baseline(path)

    if err:
        return GuardianVerdict(
            verdict=UNKNOWN, regressions=[], baseline_env=None, observed_env=env_key,
            updated=False, baseline_path=str(path), error=err,
            summary=f"{UNKNOWN}: {err}. The guard is disarmed; no claim about the derivative "
                    f"is licensed. This is NOT a pass.",
        )

    if base is None:
        save_baseline(path, current)
        return GuardianVerdict(
            verdict=CREATED, regressions=[], baseline_env=env_key, observed_env=env_key,
            updated=True, baseline_path=str(path),
            summary=f"{CREATED}: first run. Recorded "
                    f"{sum(r['executed_cases'] for r in current['roots'].values())} executed "
                    f"case(s) across {len(current['roots'])} root(s), "
                    f"{current['authored_count']} authored, env={env_key}.",
        )

    # 12.4 -- a comparison across differing environment keys is not a comparison. The same Java
    # repository yields 1,606 passing assertions under the correct toolchain and zero under a
    # runtime one major version behind. An alarm raised here would dispatch an engineer to look
    # for deleted tests that nobody deleted. The guardian says so rather than raising an alarm
    # it cannot substantiate.
    if base.get("environment_key") and env_key and base["environment_key"] != env_key:
        return GuardianVerdict(
            verdict=ENV_MISMATCH, regressions=[], baseline_env=base.get("environment_key"),
            observed_env=env_key, updated=False, baseline_path=str(path),
            summary=f"{ENV_MISMATCH}: baseline recorded under env "
                    f"{base['environment_key']}, observed {env_key}. These are two measurements "
                    f"of two different systems, not a comparison. No verdict on the derivative.",
        )

    regressions: list[Regression] = []

    # --- Gate A: executed cases, PER ROOT. A total permits redistribution (12.3). ---
    for cmd, cur_root in current["roots"].items():
        base_root = base["roots"].get(cmd)
        if base_root is None:
            continue  # a NEW root is an increase; increases are free
        lost = sorted(set(base_root.get("executed_files", [])) - set(cur_root["executed_files"]))
        if cur_root["executed_cases"] < base_root.get("executed_cases", 0):
            regressions.append(
                Regression(
                    gate="executed", root=cmd,
                    baseline=base_root.get("executed_cases", 0),
                    observed=cur_root["executed_cases"],
                    lost_identities=lost,
                    note="executed cases fell. Protection was withdrawn -- by a skip, a scope "
                         "line, an import error, or a relocation.",
                )
            )
        elif lost:
            # The count held and a file vanished from the manifest: a relocation or a same-name
            # rewrite, both invisible to any instrument that stores numbers (15.9).
            regressions.append(
                Regression(
                    gate="executed", root=cmd,
                    baseline=sorted(base_root.get("executed_files", [])),
                    observed=cur_root["executed_files"],
                    lost_identities=lost,
                    note="the executed COUNT held while identities vanished. A relocation or a "
                         "same-name rewrite. Only identities reveal this; counts cannot (15.9).",
                )
            )

    # --- Root disappearance: an entire root can die while a sibling absorbs the total (12.3). ---
    for cmd, base_root in base["roots"].items():
        if cmd not in current["roots"]:
            regressions.append(
                Regression(
                    gate="executed", root=cmd,
                    baseline=base_root.get("executed_cases", 0), observed=0,
                    lost_identities=sorted(base_root.get("executed_files", [])),
                    note="an entire suite root vanished from the invocation set. A repository "
                         "total would have concealed this behind a growing sibling.",
                )
            )

    # --- Gate B: authored count. THE DELETION ATTACK (18.2). ---
    # Without this gate, the cheapest way to drive reach to 100% is to delete the 97 orphans.
    # Every ratio improves, the repository is measurably worse, and no ratio-based rule is
    # violated. The countermeasure is that the ABSOLUTE must not fall.
    lost_authored = sorted(
        set(base.get("authored_identities", [])) - set(current["authored_identities"])
    )
    if current["authored_count"] < base.get("authored_count", 0):
        regressions.append(
            Regression(
                gate="authored", root="<repository>",
                baseline=base.get("authored_count", 0),
                observed=current["authored_count"],
                lost_identities=lost_authored,
                note="authored test files were DELETED. This is the deletion attack (18.2): "
                     "removing orphans raises every ratio while making the repository worse. "
                     "Deletion is permitted -- it is not permitted to be silent. Re-run with "
                     "--accept-baseline --reason ... --author ... to record it.",
            )
        )

    # --- Gate C: reach (drift, Part XIV). Subordinate to A and B, which is what makes it safe:
    # with B in place, reach can no longer be bought by deleting the denominator.
    b_reach, c_reach = base.get("test_file_reach"), current["test_file_reach"]
    if b_reach is not None and c_reach is not None and c_reach < b_reach - REACH_FLOAT_EPSILON:
        regressions.append(
            Regression(
                gate="reach", root="<repository>",
                baseline=round(b_reach, 4), observed=round(c_reach, 4),
                lost_identities=[],
                note="Test File Reach fell. Either protection was withdrawn (see the executed "
                     "gate) or the authored surface grew faster than the invocation reaches it "
                     "-- coverage drift (Part XIV). Code must not outgrow its protection.",
            )
        )

    if regressions:
        if not accept:
            head = "; ".join(
                f"{r.gate}@{r.root}: {r.baseline} -> {r.observed}" for r in regressions
            )
            return GuardianVerdict(
                verdict=REGRESSED, regressions=regressions,
                baseline_env=base.get("environment_key"), observed_env=env_key,
                updated=False, baseline_path=str(path),
                summary=f"{REGRESSED}: {head}",
            )
        # The firewall's sanctioned path: an explicit, attributed, reviewable act (12.6).
        accepted = dict(current)
        accepted["reason"] = reason
        accepted["author"] = author
        accepted["removed_identities"] = sorted(
            {i for r in regressions for i in r.lost_identities}
        )
        save_baseline(path, accepted)
        return GuardianVerdict(
            verdict=PASS, regressions=regressions,
            baseline_env=base.get("environment_key"), observed_env=env_key,
            updated=True, baseline_path=str(path),
            summary=f"{PASS} (baseline LOWERED by explicit acceptance) "
                    f"author={author!r} reason={reason!r}; "
                    f"{len(accepted['removed_identities'])} identity(ies) recorded as removed.",
        )

    # Nothing fell. An increase requires nothing (12.2) -- and it ratchets.
    improved = (
        current["authored_count"] > base.get("authored_count", 0)
        or (c_reach or 0) > (b_reach or 0)
        or any(
            r["executed_cases"] > base["roots"].get(c, {}).get("executed_cases", 0)
            for c, r in current["roots"].items()
        )
        or set(current["roots"]) - set(base["roots"])
    )
    updated = False
    if improved:
        # Carry the attribution forward; a ratchet is not an acceptance.
        current["reason"] = base.get("reason", "")
        current["author"] = base.get("author", "")
        current["removed_identities"] = base.get("removed_identities", [])
        updated = save_baseline(path, current)

    total_exec = sum(r["executed_cases"] for r in current["roots"].values())
    return GuardianVerdict(
        verdict=PASS, regressions=[], baseline_env=base.get("environment_key"),
        observed_env=env_key, updated=updated, baseline_path=str(path),
        summary=f"{PASS}: {total_exec} executed across {len(current['roots'])} root(s), "
                f"{current['authored_count']} authored, reach="
                f"{'UNKNOWN' if c_reach is None else f'{c_reach * 100:.1f}%'}"
                + (" (baseline ratcheted up)" if updated else " (stable)"),
    )
