"""Derivation store (CDC C6): equivalent demand reuses a completed or in-flight derivation.

key = sha256(normalized question \\0 scope \\0 sorted dependency fingerprints). A dependency is a file path (its
content sha), an http(s) URL or an evidence id (the string itself). Record: answer pointer (a file), provenance,
created, ttl, invalidators. API: get (fresh + deps unchanged) / begin (O_EXCL lock) / complete / abandon.
A lock older than LOCK_STALE_S (30 min) is stale and begin() recovers it.
Twin of hooks/research_reuse.js (same key, same layout). Layout under <state>/derivation-store/:
  <key>.json record, <key>.lock in-flight lock, answers/<key>.txt answer text.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

LOCK_STALE_S = 30 * 60
DEFAULT_TTL_S = 24 * 3600


def state_dir() -> Path:
    return Path(os.environ.get("GSD_LONG_RUN_STATE_DIR") or Path.home() / ".claude" / "state")


def store_dir() -> Path:
    return state_dir() / "derivation-store"


def normalize(q: str) -> str:
    return " ".join(str(q or "").split()).lower()


def dep_fp(dep: str) -> str:
    """File path -> path + content sha; anything else (URL, evidence id) -> the string. Missing file -> MISSING."""
    if re.match(r"^[a-z][a-z0-9+.-]*://", dep, re.I) or not (os.sep in dep or "/" in dep or "\\" in dep):
        return dep
    try:
        return dep + "@" + hashlib.sha256(Path(dep).read_bytes()).hexdigest()
    except OSError:
        return dep + "@MISSING"


def make_key(question: str, scope: str = "", deps=()) -> str:
    fps = sorted(dep_fp(d) for d in deps)
    return hashlib.sha256("\0".join([normalize(question), str(scope), *fps]).encode("utf-8")).hexdigest()


def _rec(key: str):
    try:
        return json.loads((store_dir() / f"{key}.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def get(question: str, scope: str = "", deps=(), now: float | None = None):
    """Fresh record whose deps are unchanged, else None. A dep change alters the key, so a stale dep is a miss;
    the stored invalidators are re-checked for the case where the caller passes a subset of deps."""
    now = time.time() if now is None else now
    key = make_key(question, scope, deps)
    r = _rec(key)
    if not r or r.get("status") != "complete":
        return None
    if now - float(r.get("created", 0)) > float(r.get("ttl_s", DEFAULT_TTL_S)):
        return None
    for dep, fp in (r.get("invalidators") or {}).items():
        if dep_fp(dep) != fp:
            return None
    if not Path(r.get("answer", "")).exists():
        return None
    return r


def lock_path(key: str) -> Path:
    return store_dir() / f"{key}.lock"


def inflight(question: str, scope: str = "", deps=(), now: float | None = None):
    """Live (non-stale) lock owner dict, else None."""
    now = time.time() if now is None else now
    p = lock_path(make_key(question, scope, deps))
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return d if now - float(d.get("ts", 0)) <= LOCK_STALE_S else None


def begin(question: str, scope: str = "", deps=(), owner: str = "", now: float | None = None):
    """-> ('owner', key) when the lock is taken, ('subscribe', lock_dict) when another live owner holds it."""
    now = time.time() if now is None else now
    key = make_key(question, scope, deps)
    store_dir().mkdir(parents=True, exist_ok=True)
    p = lock_path(key)
    body = json.dumps({"owner": owner, "ts": now, "key": key, "lock": str(p)}).encode()
    for _ in range(2):
        try:
            fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            cur = inflight(question, scope, deps, now)
            if cur is not None:
                return "subscribe", cur
            try:
                p.unlink()  # stale / unreadable lock: recover it
            except OSError:
                pass
            continue
        try:
            os.write(fd, body)
        finally:
            os.close(fd)
        return "owner", key
    return "subscribe", {"owner": "?", "lock": str(p)}


def complete(question: str, scope: str, deps, answer_text: str, provenance: str = "",
             ttl_s: int = DEFAULT_TTL_S, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    key = make_key(question, scope, deps)
    d = store_dir()
    (d / "answers").mkdir(parents=True, exist_ok=True)
    ans = d / "answers" / f"{key}.txt"
    ans.write_text(answer_text, encoding="utf-8")
    rec = {"key": key, "status": "complete", "question": normalize(question), "scope": scope,
           "answer": str(ans), "provenance": provenance, "created": now, "ttl_s": ttl_s,
           "invalidators": {x: dep_fp(x) for x in deps}}
    tmp = d / f"{key}.json.tmp{os.getpid()}"
    tmp.write_text(json.dumps(rec), encoding="utf-8")
    os.replace(tmp, d / f"{key}.json")
    abandon(question, scope, deps)
    return rec


def abandon(question: str, scope: str = "", deps=()) -> None:
    try:
        lock_path(make_key(question, scope, deps)).unlink()
    except OSError:
        pass


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "key":
        print(make_key(a[1], a[2] if len(a) > 2 else "", a[3:]))
    else:
        print("usage: derivation_store.py key <question> [scope] [dep...]")
