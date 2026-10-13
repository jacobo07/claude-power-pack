"""modules.prr.regions: read-only region attribution (Windows) and its summary."""
import os
import sys

import pytest

from modules.prr import regions


@pytest.mark.skipif(sys.platform != "win32", reason="VirtualQueryEx is Windows-only")
def test_scan_own_process_is_consistent():
    # Arrange
    pid = os.getpid()
    # Act
    r = regions.scan(pid)
    # Assert: resident private can never exceed committed private; a live interpreter has image pages
    assert r["pid"] == pid and r["regions"] > 0
    assert r["private_working_set_mb"] <= r["private_usage_mb"] + 1
    assert r["image_commit"] > 0 and r["private_commit"] > 0
    assert r["private_nonresident_mb"] == pytest.approx(r["private_usage_mb"] - r["private_working_set_mb"], abs=0.2)


def test_scan_refuses_off_windows(monkeypatch):
    # Arrange
    monkeypatch.setattr(regions.sys, "platform", "linux")
    # Act / Assert: never pretends to measure a plane it cannot read
    with pytest.raises(OSError, match="Windows-only"):
        regions.scan(1)


def test_summarize_counts_errors_and_takes_medians():
    # Arrange
    keys = ["private_usage_mb", "private_working_set_mb", "private_nonresident_mb", "working_set_mb",
            "private_commit", "private_reserve", "image_commit", "mapped_commit"]
    rows = [dict({k: v for k in keys}, pid=i) for i, v in enumerate((1.0, 5.0, 9.0))]
    rows.append({"pid": 99, "error": "denied"})
    # Act
    s = regions.summarize(rows)
    # Assert
    assert s["n"] == 3 and s["errors"] == 1
    assert s["median"]["private_usage_mb"] == 5.0 and s["sum"]["image_commit"] == 15.0


def test_summarize_empty_is_not_a_measurement():
    # Arrange / Act
    s = regions.summarize([{"pid": 1, "error": "denied"}])
    # Assert: zero readable processes is reported as n=0, never as a zero-byte footprint
    assert s == {"n": 0}
