"""Artifact Done-Gate (P2) -- done is an artifact on disk, not an exit code.

Generalises AKOS Checks 12/13, which were paid for in blood: two of four
V1 features shipped as DELIVERED while one had produced zero bytes and
the other had never once completed. Both passed their tests. Both
returned exit 0. Neither produced its artifact.

The contract inverts the burden of proof. A command does not get to say
"I succeeded"; it must NAME the artifact it produces and its SHAPE, and
the gate goes and looks:

    contract = ArtifactContract(
        name="embeddings",
        path="vault/embeddings/index.jsonl",
        kind=Kind.JSONL,
        min_count=1000,
        required_keys=("id", "vector"),
    )
    verdict = verify(contract)   # reads the real disk, not the log

Three things this refuses, by construction:

  * a tolerated exit code            -- the gate never looks at one
  * a fixture-scale passing test     -- min_count is production scale
  * a correctly-handled error        -- a graceful-failure path proves
                                        the failure branch works and
                                        says NOTHING about the success
                                        branch (see gate(), which will
                                        not let one substitute for the
                                        other)

MISSING is reported as NEVER_OBSERVED_TO_WORK. That is a defect status.
It is not a pass, it is not a warning, and it does not get deferred.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from glob import glob
from pathlib import Path


class Kind(str, Enum):
    FILE = "file"
    DIR = "dir"
    JSON = "json"
    JSONL = "jsonl"
    SQLITE = "sqlite"


class Status(str, Enum):
    PASS = "PASS"
    # The artifact was never produced. The command may have exited 0,
    # its tests may be green -- it has never been observed to work.
    NEVER_OBSERVED_TO_WORK = "NEVER_OBSERVED_TO_WORK"
    EMPTY = "EMPTY"                # exists, zero bytes / zero records
    TOO_FEW = "TOO_FEW"            # produced, but below production scale
    MALFORMED = "MALFORMED"        # unparseable, or missing required keys
    WRONG_KIND = "WRONG_KIND"      # file where a dir was promised, etc.


PASSING = frozenset({Status.PASS})


@dataclass(frozen=True)
class ArtifactContract:
    """What a command promises to leave on disk."""
    name: str
    path: str                       # may be a glob
    kind: Kind = Kind.FILE
    min_bytes: int = 1              # zero-byte output is never success
    min_count: int = 1              # records / rows / files
    required_keys: tuple[str, ...] = ()
    table: str = ""                 # for Kind.SQLITE
    # A failure-branch check proves the error path works. It can never
    # stand in for the success branch -- gate() enforces that.
    is_failure_branch: bool = False


@dataclass
class Verdict:
    contract: ArtifactContract
    status: Status
    count: int = 0
    size_bytes: int = 0
    resolved_path: str = ""
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status in PASSING

    def as_dict(self) -> dict:
        return {
            "artifact": self.contract.name,
            "declared_path": self.contract.path,
            "resolved_path": self.resolved_path,
            "status": self.status.value,
            "count": self.count,
            "size_bytes": self.size_bytes,
            "detail": self.detail,
        }


@dataclass
class GateResult:
    verdicts: list[Verdict] = field(default_factory=list)
    detail: str = ""

    @property
    def passed(self) -> bool:
        success = [v for v in self.verdicts if not v.contract.is_failure_branch]
        # No success-branch contract at all: a suite of graceful-failure
        # checks is not evidence the feature works. This is the AKOS
        # trap, stated as code.
        if not success:
            return False
        return all(v.passed for v in success)

    @property
    def failures(self) -> list[Verdict]:
        return [v for v in self.verdicts if not v.passed]

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "detail": self.detail,
            "verdicts": [v.as_dict() for v in self.verdicts],
        }


def _resolve(pattern: str) -> list[Path]:
    hits = sorted(glob(pattern, recursive=True))
    return [Path(h) for h in hits]


def _check_json(p: Path, c: ArtifactContract) -> tuple[Status, int, str]:
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return Status.MALFORMED, 0, f"unparseable JSON: {exc}"
    if isinstance(data, list):
        records, count = data, len(data)
    elif isinstance(data, dict):
        records, count = [data], len(data)
    else:
        return Status.MALFORMED, 0, f"JSON root is {type(data).__name__}"
    if c.required_keys and records:
        first = records[0]
        if isinstance(first, dict):
            missing = [k for k in c.required_keys if k not in first]
            if missing:
                return (Status.MALFORMED, count,
                        f"record missing required keys: {missing}")
    return Status.PASS, count, ""


def _check_jsonl(p: Path, c: ArtifactContract) -> tuple[Status, int, str]:
    count = 0
    first: dict | None = None
    with p.open("r", encoding="utf-8-sig") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                return (Status.MALFORMED, count,
                        f"line {lineno} is not JSON: {exc}")
            if first is None and isinstance(rec, dict):
                first = rec
            count += 1
    if c.required_keys and first is not None:
        missing = [k for k in c.required_keys if k not in first]
        if missing:
            return (Status.MALFORMED, count,
                    f"record missing required keys: {missing}")
    return Status.PASS, count, ""


def _check_sqlite(p: Path, c: ArtifactContract) -> tuple[Status, int, str]:
    if not c.table:
        return Status.MALFORMED, 0, "Kind.SQLITE contract declares no table"
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            cur = con.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type IN ('table','view') AND name=?", (c.table,))
            if not cur.fetchone()[0]:
                return Status.MALFORMED, 0, f"no such table: {c.table}"
            count = con.execute(
                f'SELECT count(*) FROM "{c.table}"').fetchone()[0]
        finally:
            con.close()
    except sqlite3.Error as exc:
        return Status.MALFORMED, 0, f"sqlite error: {exc}"
    return Status.PASS, int(count), ""


def verify(contract: ArtifactContract) -> Verdict:
    """Look at the disk. Never at an exit code, a log line, or a test."""
    hits = _resolve(contract.path)
    if not hits:
        return Verdict(
            contract, Status.NEVER_OBSERVED_TO_WORK,
            detail=(f"no artifact at '{contract.path}'. The command may "
                    "have exited 0 and its tests may pass -- it has "
                    "never been observed to produce its output."),
        )

    if contract.kind is Kind.DIR:
        dirs = [h for h in hits if h.is_dir()]
        if not dirs:
            return Verdict(contract, Status.WRONG_KIND,
                           resolved_path=str(hits[0]),
                           detail="a directory was promised; found a file")
        target = dirs[0]
        children = [c for c in target.rglob("*") if c.is_file()]
        size = sum(c.stat().st_size for c in children)
        v = Verdict(contract, Status.PASS, len(children), size, str(target))
        if not children:
            v.status, v.detail = Status.EMPTY, "directory contains no files"
        elif len(children) < contract.min_count:
            v.status = Status.TOO_FEW
            v.detail = (f"{len(children)} files, contract requires "
                        f"{contract.min_count}")
        return v

    files = [h for h in hits if h.is_file()]
    if not files:
        return Verdict(contract, Status.WRONG_KIND, resolved_path=str(hits[0]),
                       detail="a file was promised; found a directory")
    target = files[0]
    size = target.stat().st_size

    if size == 0:
        return Verdict(
            contract, Status.EMPTY, 0, 0, str(target),
            "the artifact exists and is zero bytes -- the command "
            "produced nothing",
        )
    if size < contract.min_bytes:
        return Verdict(contract, Status.TOO_FEW, 0, size, str(target),
                       f"{size} bytes, contract requires "
                       f"{contract.min_bytes}")

    if contract.kind is Kind.JSON:
        status, count, detail = _check_json(target, contract)
    elif contract.kind is Kind.JSONL:
        status, count, detail = _check_jsonl(target, contract)
    elif contract.kind is Kind.SQLITE:
        status, count, detail = _check_sqlite(target, contract)
    else:
        status, count, detail = Status.PASS, 1, ""

    v = Verdict(contract, status, count, size, str(target), detail)
    if status is Status.PASS:
        if count == 0:
            v.status = Status.EMPTY
            v.detail = "parses, but holds zero records"
        elif count < contract.min_count:
            v.status = Status.TOO_FEW
            v.detail = (f"{count} records, contract requires "
                        f"{contract.min_count} -- a fixture-scale result "
                        "is not a production-scale result")
    return v


def gate(contracts: list[ArtifactContract]) -> GateResult:
    """Every success-branch contract must PASS. A failure-branch check
    may pass or fail; it can never substitute for the success branch."""
    res = GateResult([verify(c) for c in contracts])
    success = [v for v in res.verdicts if not v.contract.is_failure_branch]
    if not success:
        res.detail = (
            "no success-branch artifact was declared. A graceful-failure "
            "path proves the error branch works and says nothing about "
            "whether the feature does. NOT DONE."
        )
    elif res.passed:
        res.detail = (f"{len(success)} artifact(s) observed on disk with "
                      "the declared shape.")
    else:
        res.detail = (f"{len(res.failures)} artifact contract(s) unmet -- "
                      "the feature is not done.")
    return res


def is_done(contracts: list[ArtifactContract]) -> tuple[bool, GateResult]:
    res = gate(contracts)
    return res.passed, res


def write_receipt(res: GateResult, ledger: Path, command: str = "") -> Path:
    """A PASS is worth recording; it is the evidence a later 'done' claim
    rests on. Append-only, atomic."""
    import os
    ledger.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        **res.as_dict(),
    }
    old = ledger.read_text(encoding="utf-8") if ledger.exists() else ""
    tmp = ledger.with_suffix(ledger.suffix + ".tmp")
    tmp.write_text(old + json.dumps(entry, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, ledger)
    return ledger
