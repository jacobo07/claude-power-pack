"""Tests for the single-instance profile lock.

Origin: a detached child process survived the script that was meant to abort
it and was still driving the browser when a second runner started against the
same Chromium profile. The ledger was fine -- claim_next is transactional --
but a persistent-context profile cannot be opened twice.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from modules.knowledge_acquisition.runlock import (
    LockBusy,
    ProfileLock,
    profile_lock,
)


@pytest.fixture()
def profile(tmp_path):
    d = tmp_path / "session" / "eva" / "profile"
    d.mkdir(parents=True)
    return d


def test_acquire_creates_the_lock(profile):
    lock = ProfileLock(profile)
    lock.acquire()
    try:
        assert lock.path.exists()
        assert lock.holder() is not None
    finally:
        lock.release()


def test_release_frees_it(profile):
    lock = ProfileLock(profile)
    lock.acquire()
    lock.release()

    assert not lock.path.exists()
    assert ProfileLock(profile).holder() is None


def test_second_runner_is_refused_while_first_is_live(profile):
    # Arrange
    first = ProfileLock(profile)
    first.acquire()

    # Act / Assert — the second must refuse, not queue and not proceed
    try:
        with pytest.raises(LockBusy, match="another runner"):
            ProfileLock(profile).acquire()
    finally:
        first.release()


def test_stale_lock_is_stolen(profile, capsys):
    # Arrange — a holder that died without releasing, heartbeat long past
    dead = ProfileLock(profile)
    dead.acquire()
    stale = json.loads(dead.path.read_text(encoding="utf-8"))
    stale["heartbeat"] = (
        datetime.now(timezone.utc) - timedelta(seconds=10_000)
    ).isoformat()
    dead.path.write_text(json.dumps(stale), encoding="utf-8")

    # Act — a crash cannot release anything, so the lease must expire
    fresh = ProfileLock(profile)
    fresh.acquire()
    try:
        # Assert — stolen, and the theft is reported rather than silent
        assert fresh.holder() is not None
        assert "stealing stale profile lock" in capsys.readouterr().out
    finally:
        fresh.release()


def test_refresh_extends_the_lease(profile):
    # Arrange
    lock = ProfileLock(profile)
    lock.acquire()
    try:
        before = json.loads(lock.path.read_text(encoding="utf-8"))["heartbeat"]

        # Act
        lock.refresh()

        # Assert
        after = json.loads(lock.path.read_text(encoding="utf-8"))["heartbeat"]
        assert after >= before
        assert lock.holder() is not None
    finally:
        lock.release()


def test_corrupt_lock_file_is_treated_as_stale(profile):
    # Arrange — a truncated write from a crash mid-flush
    lock = ProfileLock(profile)
    lock.path.parent.mkdir(parents=True, exist_ok=True)
    lock.path.write_text("{not json", encoding="utf-8")

    # Act / Assert — unreadable must not mean permanently locked out
    fresh = ProfileLock(profile)
    fresh.acquire()
    try:
        assert fresh.holder() is not None
    finally:
        fresh.release()


def test_context_manager_releases_on_exception(profile):
    # Arrange / Act
    with pytest.raises(RuntimeError):
        with profile_lock(profile):
            raise RuntimeError("boom")

    # Assert — a failed run must not leave the profile locked for 15 minutes
    assert ProfileLock(profile).holder() is None
