#!/usr/bin/env python3
"""Founder OS v0: repo-scoped evidence journal for owner-directed business rounds.

No network, LLM, customer-data ingestion, payments or side-effect execution.
The canonical repo identity is owned by modules.repo_identity, never guessed.
Usage: python tools/founder_round.py [--repo PATH] init|start|status|event|close
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import uuid

PP_ROOT = Path(__file__).resolve().parent.parent
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.founder_os import kernel  # noqa: E402
from modules.repo_identity.identity import canonical_repo  # noqa: E402

SCHEMA = 1
EVENT_KINDS = frozenset({"observation", "hypothesis", "opportunity", "decision",
                         "execution", "measurement", "learning", "rollback"})
EFFECTS = frozenset({"internal_reversible", "outward", "spend", "legal", "sensitive_data",
                     "irreversible"})
OUTCOMES = frozenset({"IMPACT_VERIFIED", "UNCERTAINTY_REDUCED", "CAPABILITY_VERIFIED",
                      "BLOCKED", "INCONCLUSIVE"})
PROVEN = OUTCOMES - {"BLOCKED", "INCONCLUSIVE"}
EVIDENCE_CLASSES = frozenset({"verified", "observed", "inferred", "simulated", "hypothesis"})
NOT_PROOF = frozenset({"inferred", "simulated", "hypothesis"})


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _require_text(row: dict, field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    if len(value) > 2000:
        raise ValueError(f"{field} exceeds 2000 characters")
    return value.strip()


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_IBAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}(?![A-Za-z0-9])")
_CARD = re.compile(r"(?<![A-Za-z0-9])(?:\d[ -]?){12,18}\d(?![A-Za-z0-9])")
_PHONE = re.compile(r"(?<![A-Za-z0-9])\+\d[\d ()-]{7,}\d")
_PAYMENT_KEY = re.compile(r"\b(?:[sr]k|pk)_(?:live|test)_[A-Za-z0-9]{16,}|\bwhsec_[A-Za-z0-9]{16,}")


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
    return total % 10 == 0


def _iban_ok(raw: str) -> bool:
    s = raw.replace(" ", "")
    if not 15 <= len(s) <= 34:
        return False
    moved = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in moved)) % 97 == 1


def _sensitive_kind(text: str) -> str | None:
    """Name the first personal or secret datum in text, else None.

    The shared Secret Firewall covers credentials only. A business journal's
    realistic leak is customer data, so this guard refuses instead of redacting:
    the journal holds metadata, and a refusal makes the author move the raw
    source out of the summary rather than ship a half-masked one.
    """
    if _PAYMENT_KEY.search(text):
        return "payment_key"
    if _EMAIL.search(text):
        return "email"
    if any(_iban_ok(m.group()) for m in _IBAN.finditer(text)):
        return "iban"
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn(digits):
            return "payment_card"
    if _PHONE.search(text):
        return "phone"
    return None


def _storage(repo: Path, state_home: Path | None = None) -> Path:
    # The existing canonical_repo handles subdirs and git worktrees. Reuse it.
    root = Path(canonical_repo(str(repo.resolve()))).resolve()
    if not root.is_dir() or not any((root / marker).exists() for marker in (".git", ".hg", ".svn")):
        raise ValueError("Founder rounds require a real version-control repository")
    key = hashlib.sha256(os.path.normcase(str(root)).encode("utf-8")).hexdigest()[:32]
    home = state_home
    if home is None:
        override = os.getenv("CPP_FOUNDER_STATE_DIR")
        home = Path(override) if override else Path.home() / ".claude" / "state" / "founder-os"
    return Path(home).expanduser() / key


def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        p.chmod(0o700)


def _write_new(p: Path, value: dict) -> None:
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    if os.name != "nt":
        p.chmod(0o600)


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        # os.kill(pid, 0) would TerminateProcess on Windows; query instead.
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return bool(ok) and code.value == 259  # STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _lock_verdict(lock: Path) -> str:
    """'stale' only on positive proof the owner is gone; anything else is 'live'."""
    try:
        pid = int(json.loads(lock.read_text(encoding="utf-8"))["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        # A crash between create and write leaves an empty lock; give a writer 60s.
        try:
            return "stale" if time.time() - lock.stat().st_mtime > 60 else "live"
        except OSError:
            return "live"
    return "live" if _pid_alive(pid) else "stale"


@contextmanager
def _locked(d: Path):
    lock = d / ".write.lock"
    if not d.is_dir():
        raise RuntimeError("uninitialized: run init from this repository first")
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as e:
        if _lock_verdict(lock) == "stale":
            raise RuntimeError("round state lock is stale (owner process is gone); "
                               "run recover to clear it") from e
        raise RuntimeError("round state locked by a live writer; retry shortly") from e
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps({"pid": os.getpid(), "time": _utc()}))
            f.flush()
            os.fsync(f.fileno())
        yield
    finally:
        lock.unlink(missing_ok=True)


def _identity(repo: Path, d: Path) -> dict:
    manifest = d / "identity.json"
    if not manifest.is_file():
        raise RuntimeError("uninitialized: run init from this repository first")
    state = json.loads(manifest.read_text(encoding="utf-8"))
    expected = str(Path(canonical_repo(str(repo.resolve()))).resolve())
    if state.get("schema") != SCHEMA or state.get("canonical_repo") != expected:
        raise RuntimeError("identity mismatch; refusing to mix business state")
    return state


def _read_events(d: Path) -> list[dict]:
    path = d / "events.jsonl"
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        # _append writes record and newline in one call, so a missing newline is a crash mid-append.
        raise RuntimeError("journal integrity failure: TORN_TAIL (last write was cut off; "
                           "run recover to quarantine it)")
    return _parse_events(raw.decode("utf-8"))


def _parse_events(text: str) -> list[dict]:
    events = []
    prev = "0" * 64
    seen = set()
    for line_number, line in enumerate(text.splitlines(), 1):
        try:
            row = json.loads(line)
            digest = row.pop("sha256")
            if row.get("prev_sha256") != prev or row.get("seq") != line_number:
                raise ValueError("sequence or previous digest mismatch")
            actual = hashlib.sha256(_json_bytes(row)).hexdigest()
            if digest != actual or row.get("event_id") in seen:
                raise ValueError("digest mismatch or repeated event_id")
            row["sha256"] = digest
            seen.add(row["event_id"])
            events.append(row)
            prev = digest
        except (ValueError, KeyError, TypeError) as e:
            raise RuntimeError(f"journal integrity failure at line {line_number}: {e}") from e
    return events


def _append(d: Path, events: list[dict], row: dict) -> dict:
    record = {"schema": SCHEMA, "seq": len(events) + 1,
              "event_id": str(uuid.uuid4()), "ts": _utc(),
              "prev_sha256": events[-1]["sha256"] if events else "0" * 64, **row}
    record["sha256"] = hashlib.sha256(_json_bytes(record)).hexdigest()
    p = d / "events.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    if os.name != "nt":
        p.chmod(0o600)
    return record


def _active(events: list[dict]) -> str | None:
    current = None
    for row in events:
        if row.get("kind") == "round_open":
            if current is not None:
                raise RuntimeError("journal contains two concurrent active rounds")
            current = row["round_id"]
        elif row.get("kind") == "round_close":
            if current != row.get("round_id"):
                raise RuntimeError("round close disagrees with active round")
            current = None
    return current


def initialize(repo: Path, state_home: Path | None = None) -> dict:
    d = _storage(repo, state_home)
    _safe_mkdir(d)
    root = str(Path(canonical_repo(str(repo.resolve()))).resolve())
    with _locked(d):
        if not (d / "identity.json").exists():
            _write_new(d / "identity.json", {"schema": SCHEMA, "canonical_repo": root,
                                              "business_name": None, "sector": None,
                                              "created_at": _utc()})
        profile = _identity(repo, d)
        _read_events(d)  # detect tampering even at init
    return {"state_dir": str(d), "profile": profile, "status": "INITIALIZED"}


def start(repo: Path, state_home: Path | None = None) -> dict:
    d = _storage(repo, state_home)
    with _locked(d):
        profile = _identity(repo, d)
        events = _read_events(d)
        if _active(events):
            raise RuntimeError("a round is active; close it or continue recording")
        round_id = str(uuid.uuid4())
        event = _append(d, events, {"kind": "round_open", "round_id": round_id})
    return {"round_id": round_id, "repository": profile["canonical_repo"],
            "business_name": profile.get("business_name"), "sector": profile.get("sector"),
            "opened_at": event["ts"], "evidence_count": len([e for e in events if e.get("kind") == "observation"]),
            "mode": "EVIDENCE_FIRST", "effects": "NONE_AUTOMATIC",
            "state_dir": str(d)}


def record(repo: Path, payload: dict, state_home: Path | None = None) -> dict:
    d = _storage(repo, state_home)
    if not isinstance(payload, dict):
        raise ValueError("event input must be a JSON object")
    kind = _require_text(payload, "kind")
    if kind not in EVENT_KINDS:
        raise ValueError(f"unsupported event kind: {kind}")
    summary = _require_text(payload, "summary")
    if payload.get("effect") not in EFFECTS:
        raise ValueError("effect must be explicitly classified")
    effect = payload["effect"]
    if effect != "internal_reversible":
        # A receipt does not confer permission; require a prior, scoped authorization reference.
        _require_text(payload, "authorization_ref")
    if kind in {"observation", "measurement", "learning"}:
        _require_text(payload, "source_ref")
        if payload.get("evidence_class") not in EVIDENCE_CLASSES:
            raise ValueError("evidence_class must be explicit; projected/simulated is not verified")
    if kind == "measurement":
        for field in ("baseline_ref", "after_ref", "metric", "window", "method"):
            _require_text(payload, field)
    if kind == "execution":
        _require_text(payload, "action_ref")
        _require_text(payload, "outcome_ref")
    if kind == "opportunity":
        _require_text(payload, "success_gate")
        _require_text(payload, "abandon_gate")
    allowed = {"kind", "summary", "effect", "authorization_ref", "source_ref", "evidence_class",
               "action_ref", "outcome_ref", "success_gate", "abandon_gate", "hypothesis_ref",
               "opportunity_ref", "estimated_cost", "estimated_value", "currency", "limitations",
               "baseline_ref", "after_ref", "metric", "window", "method",
               "subject", "value", "observed_at", "supersedes"}
    if set(payload) - allowed:
        raise ValueError(f"unsupported event fields: {sorted(set(payload) - allowed)}")
    if ("subject" in payload or "value" in payload) and kind not in kernel.SUBJECT_KINDS:
        raise ValueError("subject/value are only valid on observation, measurement or hypothesis events")
    if "subject" in payload:
        if payload["subject"] not in kernel.PROFILE_FIELDS:
            raise ValueError(f"subject must be one of {list(kernel.PROFILE_FIELDS)}")
        value = _require_text(payload, "value")
        if len(value) > 200:
            raise ValueError("value exceeds 200 characters; keep detail in the source")
    elif "value" in payload:
        raise ValueError("value requires a subject")
    if "observed_at" in payload:
        try:
            datetime.fromisoformat(payload["observed_at"])
        except (TypeError, ValueError):
            raise ValueError("observed_at must be an ISO-8601 date or datetime") from None
    for field in ("estimated_cost", "estimated_value"):
        amount = payload.get(field)
        if amount is None:
            continue
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError(f"{field} must be a number")
        if isinstance(amount, float) and not math.isfinite(amount):
            raise ValueError(f"unsupported or non-finite value for {field}; metadata scalars only")
        if amount < 0:
            raise ValueError(f"{field} must not be negative; record a cost as a positive amount")
        code = payload.get("currency")
        if not (isinstance(code, str) and re.fullmatch(r"[A-Z]{3}", code)):
            raise ValueError(f"{field} needs an ISO 4217 currency code; an amount without a currency is not recorded")
    # Secret Firewall is CPP-owned. No raw token or unbounded nested customer
    # payload may flow into this otherwise-private evidence journal.
    from modules.secret_firewall.redactor import redact_for_log
    clean = {}
    for field, value in payload.items():
        if isinstance(value, str):
            found = _sensitive_kind(value)
            if found:
                raise ValueError(f"{field} contains personal or secret data ({found}); "
                                 "reference the source instead of quoting it")
            clean[field] = redact_for_log(value, max_len=2000)
        elif value is None or isinstance(value, (bool, int)):
            clean[field] = value
        elif isinstance(value, float) and math.isfinite(value):
            clean[field] = value
        else:
            raise ValueError(f"unsupported or non-finite value for {field}; metadata scalars only")
    payload = clean
    if len(_json_bytes(payload)) > 16000:
        raise ValueError("event exceeds 16KB; store raw sources externally")
    with _locked(d):
        _identity(repo, d)
        events = _read_events(d)
        round_id = _active(events)
        if not round_id:
            raise RuntimeError("no active round; run start first")
        if kind == "execution" and any(
                e.get("round_id") == round_id and e.get("kind") == "execution"
                and e.get("payload", {}).get("action_ref") == payload["action_ref"] for e in events):
            raise ValueError(f"duplicate action_ref in this round: {payload['action_ref']}")
        target = payload.get("supersedes")
        if target is not None:
            old = next((e for e in events if e["event_id"] == target), None)
            if old is None or old.get("payload", {}).get("subject") != payload.get("subject"):
                raise ValueError("supersedes must name an earlier event with the same subject")
        row = _append(d, events, {"kind": kind, "round_id": round_id,
                                  "payload": payload})
    return {"event_id": row["event_id"], "round_id": round_id, "seq": row["seq"],
            "sha256": row["sha256"]}


def recover(repo: Path, state_home: Path | None = None) -> dict:
    """Clear a dead writer's lock and quarantine a cut-off last write.

    Acts only on positive evidence: the lock owner is gone, or the journal's last
    line lacks its newline. The journal minus that line must still verify, so
    mid-journal corruption or tampering is never repaired, only reported.
    """
    d = _storage(repo, state_home)
    if not d.is_dir():
        raise RuntimeError("uninitialized: run init from this repository first")
    lock = d / ".write.lock"
    stale_removed = False
    if lock.exists() and _lock_verdict(lock) == "stale":
        lock.unlink(missing_ok=True)
        stale_removed = True
    quarantined = 0
    with _locked(d):
        _identity(repo, d)
        path = d / "events.jsonl"
        raw = path.read_bytes() if path.exists() else b""
        if raw and not raw.endswith(b"\n"):
            keep = raw[:raw.rfind(b"\n") + 1]
            _parse_events(keep.decode("utf-8"))  # refuses unless the rest verifies
            tail = raw[len(keep):]
            (d / f"torn-tail-{int(time.time())}.bin").write_bytes(tail)
            tmp = d / "events.jsonl.recover"
            tmp.write_bytes(keep)
            os.replace(tmp, path)
            quarantined = len(tail)
        else:
            _parse_events(raw.decode("utf-8"))
    return {"stale_lock_removed": stale_removed, "quarantined_bytes": quarantined,
            "journal_integrity": "VERIFIED"}


def close(repo: Path, outcome: str, proof_ids: list[str], *,
          blocker: str | None = None, state_home: Path | None = None) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError(f"invalid outcome: {outcome}")
    d = _storage(repo, state_home)
    with _locked(d):
        _identity(repo, d)
        events = _read_events(d)
        round_id = _active(events)
        if not round_id:
            raise RuntimeError("no active round")
        own = {e["event_id"]: e for e in events if e.get("round_id") == round_id}
        if outcome in PROVEN:
            if not proof_ids or not all(p in own for p in proof_ids):
                raise ValueError("verified outcome requires this-round proof event IDs")
            proof_kinds = {own[p]["kind"] for p in proof_ids}
            if outcome == "IMPACT_VERIFIED" and not any(own[p]["kind"] == "measurement" and
                        own[p].get("payload", {}).get("evidence_class") == "verified"
                        for p in proof_ids):
                raise ValueError("incremental impact requires verified measured evidence")
            if outcome == "UNCERTAINTY_REDUCED" and not ({"observation", "measurement"} & proof_kinds):
                raise ValueError("uncertainty reduction needs observation/measurement")
            if outcome == "CAPABILITY_VERIFIED" and not any(own[p]["kind"] == "measurement" and
                        own[p].get("payload", {}).get("evidence_class") == "verified"
                        for p in proof_ids):
                raise ValueError("capability verification needs a verified test measurement")
            if any(own[p].get("payload", {}).get("evidence_class") in NOT_PROOF
                   for p in proof_ids):
                raise ValueError("simulated evidence cannot prove results")
        if outcome == "BLOCKED" and not (isinstance(blocker, str) and blocker.strip()):
            raise ValueError("BLOCKED requires an explicit blocker")
        row = _append(d, events, {"kind": "round_close", "round_id": round_id,
                                  "outcome": outcome, "proof_ids": proof_ids,
                                  "blocker": blocker})
    return {"round_id": round_id, "outcome": outcome, "seq": row["seq"]}


def status(repo: Path, state_home: Path | None = None) -> dict:
    d = _storage(repo, state_home)
    profile = _identity(repo, d)
    events = _read_events(d)
    active = _active(events)
    closes = [e for e in events if e["kind"] == "round_close"]
    return {"repository": profile["canonical_repo"], "business_name": profile.get("business_name"),
            "sector": profile.get("sector"), "active_round": active,
            "rounds_closed": len(closes), "last_outcome": closes[-1]["outcome"] if closes else None,
            "events": len(events), "state_dir": str(d), "journal_integrity": "VERIFIED"}


def kernel_view(repo: Path, state_home: Path | None = None, as_of: datetime | None = None) -> dict:
    """Business-state view and recommended plan, folded from this business's journal only."""
    d = _storage(repo, state_home)
    _identity(repo, d)
    events = _read_events(d)
    view = kernel.build_view(events, as_of=as_of)
    return {"repository": str(Path(canonical_repo(str(repo.resolve()))).resolve()),
            "fields": view, "plan": kernel.plan_round(view), "executes": "NOTHING"}


def context_for(repo: Path, lens: str, state_home: Path | None = None,
                as_of: datetime | None = None) -> dict:
    """Lens-scoped context for THIS business: its kernel view plus the universal business_round baseline."""
    from modules.founder_os import compiler
    from modules.tower import baselines as bl
    view = kernel_view(repo, state_home, as_of)["fields"]
    gens = bl.generations("business_round")
    stamp = f"business_round/B{gens[-1]} sha256 {bl.generation_sha256('business_round', gens[-1])[:12]}" if gens else ""
    return compiler.compile_context(view, lens, bl.active_entries("business_round"), stamp)


def assess_business(repo: Path, state_home: Path | None = None, as_of: datetime | None = None) -> dict:
    """Five separate verdicts for THIS business, from its kernel view only."""
    from modules.founder_os import assessment
    return assessment.assess(kernel_view(repo, state_home, as_of)["fields"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("start")
    sub.add_parser("status")
    sub.add_parser("recover")
    sub.add_parser("kernel")
    sub.add_parser("assess")
    ctx = sub.add_parser("context")
    ctx.add_argument("--lens", required=True)
    add = sub.add_parser("event")
    add.add_argument("--file", type=Path, required=True)
    end = sub.add_parser("close")
    end.add_argument("--outcome", choices=sorted(OUTCOMES), required=True)
    end.add_argument("--proof", action="append", default=[])
    end.add_argument("--blocker", default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = initialize(args.repo)
        elif args.command == "start":
            result = start(args.repo)
        elif args.command == "event":
            result = record(args.repo, json.loads(args.file.read_text(encoding="utf-8")))
        elif args.command == "recover":
            result = recover(args.repo)
        elif args.command == "kernel":
            result = kernel_view(args.repo)
        elif args.command == "context":
            result = context_for(args.repo, args.lens)
        elif args.command == "assess":
            result = assess_business(args.repo)
        elif args.command == "close":
            result = close(args.repo, args.outcome, args.proof, blocker=args.blocker)
        else:
            result = status(args.repo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as e:
        print(json.dumps({"error": str(e), "verdict": "BLOCKED"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
