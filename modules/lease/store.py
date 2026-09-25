"""A fenced lease store for one authority home.

A lease keeps a holder live; a FENCE keeps the world safe. Holding a lease is a
belief about the past, and any holder can be paused past its TTL and wake up
still believing it. So every grant, expiry, release and consume moves the fence
of each resource class it touches, and the only question a resource may ask is
`check(class, fence)`: is this fence the current one, held by a live lease?
A resource that does not ask has no mutual exclusion, whatever the lease says.

Clean-room reconstruction; concepts only, no upstream code (UWCP assimilation R2,
vault/specs/uwcp-assimilation.md §14):
  - etcd lessor (v3.7.2 server/lease/lessor.go): the authority owns the clock;
    revoke clears guarded state atomically; a minimum TTL exists.
  - etcd #9888 / #21372: a clock restarted by its owner's restart makes leases
    immortal -> deadlines here are ABSOLUTE and persisted; a reload never extends.
  - etcd #11456 + Jepsen etcd-3.4.3: a lock is a liveness hint; fencing is safety.
  - etcd #14370: ack precedes durability -> every op returns only after fsync.
  - Temporal range_id (service/history/shard): the generation moves on every
    ownership change and is compared by the store, not by the holder.
  - Temporal ScheduleToStart vs StartToClose: a queued reservation has a
    queue-wait deadline; the TTL starts at DISPATCH, not at the grant.
  - Temporal #2683: fencing is only as good as the store's CAS -> the store
    refuses to run on a network/overlay filesystem, where flock is not a lock.

Authority: an append-only JSONL journal, one record per transition, each with a
contiguous `seq`; state is a fold of the journal. The journal is also the input
the history checker (modules/history_check) reads, so the lease has one record,
not a record and a log that can disagree.

Clock: `clock()` on THIS host only. Deadlines written here are judged only here.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

JOURNAL = "lease.journal.jsonl"
LOCKFILE = "lease.lock"

# lease states
RESERVED = "RESERVED"                  # granted, queued, TTL not running
ACTIVE = "ACTIVE"                      # dispatched, TTL running
RELEASED = "RELEASED"
EXPIRED = "EXPIRED"
QUEUE_WAIT_EXCEEDED = "QUEUE_WAIT_EXCEEDED"
CONSUMED = "CONSUMED"
LIVE_STATES = frozenset({RESERVED, ACTIVE})

# refusal reasons -- each needs a different fix, so each has its own name
HELD = "held"
TTL_BELOW_FLOOR = "ttl_below_floor"
UNKNOWN_LEASE = "unknown_lease"
NOT_HOLDER = "not_holder"
STALE_FENCE = "stale_fence"
NOT_LIVE = "not_live"
BAD_STATE = "bad_state"
BAD_REQUEST = "bad_request"

REFUSED_FS = frozenset({"nfs", "nfs4", "cifs", "smb", "smbfs", "smb2", "smb3", "overlay",
                        "overlayfs", "9p", "sshfs", "davfs", "afs", "glusterfs", "ceph"})


class LeaseStoreError(Exception):
    """The store itself cannot be trusted (corrupt journal, unsupported filesystem)."""


class UnsupportedFilesystem(LeaseStoreError):
    pass


class JournalCorrupt(LeaseStoreError):
    pass


@dataclass(frozen=True)
class Result:
    ok: bool
    reason: str = ""                   # empty when ok
    lease_id: str = ""
    fences: dict = field(default_factory=dict)
    state: str = ""
    deadline: float | None = None


@dataclass
class Lease:
    lease_id: str
    holder: str
    classes: tuple
    ttl_s: float
    state: str
    fences: dict
    queue_deadline: float | None
    deadline: float | None


# --- filesystem guard ------------------------------------------------------

def filesystem_type(path: Path) -> str:
    """Name of the filesystem holding `path`, or "" when it cannot be established."""
    path = Path(path).resolve()
    if sys.platform.startswith("linux"):
        best, fstype = "", ""
        try:
            with open("/proc/mounts", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    mnt = parts[1].replace("\\040", " ")
                    if (str(path) == mnt or str(path).startswith(mnt.rstrip("/") + "/")) \
                            and len(mnt) > len(best):
                        best, fstype = mnt, parts[2]
        except OSError:
            return ""
        return fstype.lower()
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        drive = os.path.splitdrive(str(path))[0] + "\\"
        if drive.startswith("\\\\"):
            return "smb"                                   # UNC share
        k32 = ctypes.windll.kernel32
        if k32.GetDriveTypeW(ctypes.c_wchar_p(drive)) == 4:  # DRIVE_REMOTE
            return "smb"
        name = ctypes.create_unicode_buffer(64)
        flags = wintypes.DWORD()
        ok = k32.GetVolumeInformationW(ctypes.c_wchar_p(drive), None, 0, None, None,
                                       ctypes.byref(flags), name, 64)
        return name.value.lower() if ok else ""
    return ""


def fs_refusal(fstype: str) -> str:
    """Why this filesystem cannot hold a lease store, or "" if it can."""
    if not fstype:
        return "filesystem type could not be established"
    if fstype in REFUSED_FS or fstype.startswith("fuse"):
        return f"filesystem {fstype!r}: flock there is not a lock"
    return ""


# --- the exclusive section -------------------------------------------------

class _Exclusive:
    """Host-local exclusive lock around one store directory."""

    def __init__(self, path: Path, timeout_s: float):
        self.path, self.timeout_s, self.fh = path, timeout_s, None

    def __enter__(self):
        self.fh = open(self.path, "a+b")
        deadline = time.monotonic() + self.timeout_s
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
                    return self
                except OSError:
                    if time.monotonic() > deadline:
                        self.fh.close()
                        raise TimeoutError(f"lease store lock busy: {self.path}")
                    time.sleep(0.01)
        import fcntl
        while True:
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.monotonic() > deadline:
                    self.fh.close()
                    raise TimeoutError(f"lease store lock busy: {self.path}")
                time.sleep(0.01)

    def __exit__(self, *exc):
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        finally:
            self.fh.close()


def _fsync_dir(path: Path) -> None:
    if os.name == "nt":
        return                          # NTFS journals the directory entry itself
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


# --- the store ---------------------------------------------------------------

class LeaseStore:
    """Every public method takes the exclusive section, applies due expiries,
    decides, appends one journal record (fsync), and only then returns."""

    def __init__(self, root, *, min_ttl_s: float, clock=time.time, host: str | None = None,
                 lock_timeout_s: float = 10.0):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        why = fs_refusal(filesystem_type(self.root))
        if why:
            raise UnsupportedFilesystem(f"{self.root}: {why}")
        if not (isinstance(min_ttl_s, (int, float)) and min_ttl_s > 0):
            raise LeaseStoreError("min_ttl_s must be positive: it is the floor below which a "
                                  "healthy holder expires between renewals")
        self.min_ttl_s = float(min_ttl_s)
        self.clock = clock
        self.host = host or socket.gethostname()
        self.journal = self.root / JOURNAL
        self._lock = _Exclusive(self.root / LOCKFILE, lock_timeout_s)
        self.torn_records = 0

    # -- journal --------------------------------------------------------------

    def _read(self) -> list[dict]:
        if not self.journal.exists():
            return []
        raw = self.journal.read_bytes()
        records, torn = [], 0
        for line in raw.split(b"\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                torn += 1               # a write that never completed was never acked
                continue
            want = len(records) + 1
            if rec.get("seq") != want:
                raise JournalCorrupt(f"{self.journal}: expected seq {want}, found {rec.get('seq')}")
            records.append(rec)
        self.torn_records = torn
        return records

    def _append(self, records: list[dict], rec: dict) -> dict:
        rec = {"seq": len(records) + 1, "ts": self.clock(), "host": self.host, **rec}
        line = json.dumps(rec, sort_keys=True, separators=(",", ":")).encode("utf-8")
        prefix = b""
        if self.journal.exists() and self.journal.stat().st_size > 0:
            with open(self.journal, "rb") as rh:
                rh.seek(-1, os.SEEK_END)
                if rh.read(1) != b"\n":
                    prefix = b"\n"          # isolate a torn tail so it can never merge
        with open(self.journal, "ab") as fh:
            fh.write(prefix + line + b"\n")
            fh.flush()
            os.fsync(fh.fileno())
        _fsync_dir(self.root)
        records.append(rec)
        return rec

    # -- fold -------------------------------------------------------------------

    @staticmethod
    def _fold(records: list[dict]) -> tuple[dict, dict, dict]:
        leases: dict[str, Lease] = {}
        gen: dict[str, int] = {}
        owner: dict[str, str | None] = {}
        for r in records:
            op = r["op"]
            if op == "grant":
                fences = {}
                for c in r["classes"]:
                    gen[c] = gen.get(c, 0) + 1
                    owner[c] = r["lease_id"]
                    fences[c] = gen[c]
                leases[r["lease_id"]] = Lease(r["lease_id"], r["holder"], tuple(r["classes"]),
                                              r["ttl_s"], RESERVED, fences,
                                              r.get("queue_deadline"), None)
                continue
            lease = leases[r["lease_id"]]
            if op in ("dispatch", "renew"):
                lease.state, lease.deadline = ACTIVE, r["deadline"]
            elif op in ("release", "expire", "queue_expire", "consume"):
                lease.state = {"release": RELEASED, "expire": EXPIRED,
                               "queue_expire": QUEUE_WAIT_EXCEEDED, "consume": CONSUMED}[op]
                for c in lease.classes:
                    # ownership changed: the fence moves even with no new holder yet,
                    # so a paused holder's fence is stale from this record on.
                    gen[c] = gen.get(c, 0) + 1
                    if owner.get(c) == lease.lease_id:
                        owner[c] = None
            else:
                raise JournalCorrupt(f"unknown op {op!r} at seq {r['seq']}")
        return leases, gen, owner

    def _expire_due(self, records: list[dict]) -> tuple[dict, dict, dict]:
        now = self.clock()
        leases, gen, owner = self._fold(records)
        for lease in list(leases.values()):
            if lease.state == RESERVED and lease.queue_deadline is not None \
                    and now >= lease.queue_deadline:
                self._append(records, {"op": "queue_expire", "lease_id": lease.lease_id})
            elif lease.state == ACTIVE and lease.deadline is not None and now >= lease.deadline:
                self._append(records, {"op": "expire", "lease_id": lease.lease_id})
        return self._fold(records)

    def _holder_guard(self, leases, lease_id, holder, fences) -> Result | None:
        lease = leases.get(lease_id)
        if lease is None:
            return Result(False, UNKNOWN_LEASE, lease_id)
        if lease.holder != holder:
            return Result(False, NOT_HOLDER, lease_id, state=lease.state)
        if lease.state not in LIVE_STATES:
            return Result(False, NOT_LIVE, lease_id, state=lease.state)
        if dict(fences) != lease.fences:
            return Result(False, STALE_FENCE, lease_id, lease.fences, lease.state)
        return None

    # -- public -------------------------------------------------------------------

    def acquire(self, classes, holder: str, ttl_s: float, lease_id: str,
                queue_wait_s: float | None = None) -> Result:
        """Reserve every class or none. The TTL does not run until dispatch()."""
        classes = tuple(sorted(set(classes)))
        if not classes or not holder or not lease_id:
            return Result(False, BAD_REQUEST, lease_id)
        if not (isinstance(ttl_s, (int, float)) and ttl_s >= self.min_ttl_s):
            return Result(False, TTL_BELOW_FLOOR, lease_id)
        if queue_wait_s is not None and not (isinstance(queue_wait_s, (int, float))
                                             and queue_wait_s > 0):
            return Result(False, BAD_REQUEST, lease_id)
        with self._lock:
            records = self._read()
            leases, gen, owner = self._expire_due(records)
            if lease_id in leases:
                prev = leases[lease_id]
                # the same request replayed after a lost response returns what it got,
                # but only for the same holder and classes
                if prev.holder == holder and prev.classes == classes and prev.state in LIVE_STATES:
                    return Result(True, "", lease_id, prev.fences, prev.state, prev.deadline)
                return Result(False, BAD_REQUEST, lease_id, state=prev.state)
            busy = [c for c in classes if owner.get(c)]
            if busy:
                return Result(False, HELD, lease_id, state=",".join(busy))
            qd = self.clock() + queue_wait_s if queue_wait_s is not None else None
            self._append(records, {"op": "grant", "lease_id": lease_id, "holder": holder,
                                   "classes": list(classes), "ttl_s": float(ttl_s),
                                   "queue_deadline": qd})
            lease = self._fold(records)[0][lease_id]
            return Result(True, "", lease_id, lease.fences, lease.state)

    def dispatch(self, lease_id: str, holder: str, fences: dict) -> Result:
        """The job left the queue: the TTL starts now."""
        with self._lock:
            records = self._read()
            leases, _, _ = self._expire_due(records)
            bad = self._holder_guard(leases, lease_id, holder, fences)
            if bad:
                return bad
            lease = leases[lease_id]
            if lease.state != RESERVED:
                return Result(False, BAD_STATE, lease_id, lease.fences, lease.state)
            rec = self._append(records, {"op": "dispatch", "lease_id": lease_id,
                                         "deadline": self.clock() + lease.ttl_s})
            return Result(True, "", lease_id, lease.fences, ACTIVE, rec["deadline"])

    def renew(self, lease_id: str, holder: str, fences: dict) -> Result:
        with self._lock:
            records = self._read()
            leases, _, _ = self._expire_due(records)
            bad = self._holder_guard(leases, lease_id, holder, fences)
            if bad:
                return bad
            lease = leases[lease_id]
            if lease.state != ACTIVE:
                return Result(False, BAD_STATE, lease_id, lease.fences, lease.state)
            rec = self._append(records, {"op": "renew", "lease_id": lease_id,
                                         "deadline": self.clock() + lease.ttl_s})
            return Result(True, "", lease_id, lease.fences, ACTIVE, rec["deadline"])

    def _end(self, op: str, state: str, lease_id: str, holder: str, fences: dict) -> Result:
        with self._lock:
            records = self._read()
            leases, _, _ = self._expire_due(records)
            bad = self._holder_guard(leases, lease_id, holder, fences)
            if bad:
                return bad
            if op == "consume" and leases[lease_id].state != ACTIVE:
                return Result(False, BAD_STATE, lease_id, leases[lease_id].fences,
                              leases[lease_id].state)
            self._append(records, {"op": op, "lease_id": lease_id})
            return Result(True, "", lease_id, leases[lease_id].fences, state)

    def release(self, lease_id: str, holder: str, fences: dict) -> Result:
        return self._end("release", RELEASED, lease_id, holder, fences)

    def consume(self, lease_id: str, holder: str, fences: dict) -> Result:
        """Mark the reserved work as spent. Absorbing: a consumed lease never lives again."""
        return self._end("consume", CONSUMED, lease_id, holder, fences)

    def check(self, cls: str, fence: int) -> Result:
        """The resource-side question. True only for the CURRENT fence of `cls`,
        held by a lease that is ACTIVE and inside its deadline."""
        with self._lock:
            records = self._read()
            leases, gen, owner = self._expire_due(records)
            lid = owner.get(cls)
            if not lid:
                return Result(False, NOT_LIVE)
            lease = leases[lid]
            if gen.get(cls) != fence or lease.fences.get(cls) != fence:
                return Result(False, STALE_FENCE, lid, lease.fences, lease.state)
            if lease.state != ACTIVE:
                return Result(False, BAD_STATE, lid, lease.fences, lease.state)
            return Result(True, "", lid, lease.fences, ACTIVE, lease.deadline)

    def snapshot(self) -> dict:
        """Read-only projection for status views. Never authorizes anything."""
        with self._lock:
            records = self._read()
            leases, gen, owner = self._fold(records)
        return {"leases": {k: vars(v) for k, v in leases.items()}, "fence": dict(gen),
                "owner": dict(owner), "records": len(records), "torn_records": self.torn_records}

    def records(self) -> list[dict]:
        """The journal, for independent history checking."""
        with self._lock:
            return list(self._read())
