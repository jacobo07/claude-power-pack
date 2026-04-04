"""
OmniCapture — Tiered JSONL Storage.
Hot (24h) -> Warm (7d, gzipped) -> Cold (30d, gzipped) -> Delete.
"""

import json
import gzip
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class TieredStorage:
    """Manages tiered JSONL storage for telemetry events."""

    def __init__(self, config: dict[str, Any]):
        self.base_dir = Path(config.get("base_dir", "/opt/kobiiclaw/omnicapture/data"))
        self.hot_max_age_hours = config.get("hot_max_age_hours", 24)
        self.warm_max_age_days = config.get("warm_max_age_days", 7)
        self.cold_max_age_days = config.get("cold_max_age_days", 30)
        self.max_file_size_kb = config.get("max_file_size_kb", 512)

        # Ensure directories exist
        for tier in ("hot", "warm", "cold"):
            (self.base_dir / tier).mkdir(parents=True, exist_ok=True)

    def write_event(self, event: dict[str, Any]) -> str:
        """
        Write a single event to the hot tier.
        Returns the file path written to.
        """
        project_id = event.get("project_id", "unknown")
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d-%H")

        project_dir = self.base_dir / "hot" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        filepath = project_dir / f"{hour_key}.jsonl"

        # Rotate if file exceeds max size
        if filepath.exists() and filepath.stat().st_size > self.max_file_size_kb * 1024:
            # Append sequence number
            seq = 1
            while True:
                rotated = project_dir / f"{hour_key}.{seq}.jsonl"
                if not rotated.exists() or rotated.stat().st_size <= self.max_file_size_kb * 1024:
                    filepath = rotated
                    break
                seq += 1

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return str(filepath)

    def write_batch(self, events: list[dict[str, Any]]) -> int:
        """Write multiple events to hot tier. Returns count written."""
        written = 0
        for event in events:
            self.write_event(event)
            written += 1
        return written

    def query(
        self,
        project_id: str,
        since_seconds: int = 300,
        severity: set[str] | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Query events from storage.
        Searches hot tier first, then warm if time range extends beyond 24h.
        """
        results: list[dict[str, Any]] = []
        cutoff_ts = (time.time() - since_seconds) * 1000  # epoch_ms

        # Determine which tiers to search
        tiers_to_search = ["hot"]
        if since_seconds > self.hot_max_age_hours * 3600:
            tiers_to_search.append("warm")
        if since_seconds > self.warm_max_age_days * 86400:
            tiers_to_search.append("cold")

        for tier in tiers_to_search:
            tier_dir = self.base_dir / tier / project_id
            if not tier_dir.exists():
                continue

            files = sorted(tier_dir.iterdir(), reverse=True)  # newest first
            for filepath in files:
                if len(results) >= limit:
                    break

                events = self._read_file(filepath)
                for event in events:
                    if len(results) >= limit:
                        break

                    epoch_ms = event.get("timestamp_epoch_ms", 0)
                    if epoch_ms < cutoff_ts:
                        continue

                    if severity and event.get("severity") not in severity:
                        continue

                    if category and event.get("category") != category:
                        continue

                    results.append(event)

        # Sort by timestamp descending
        results.sort(key=lambda e: e.get("timestamp_epoch_ms", 0), reverse=True)
        return results[:limit]

    def get_summary(self, project_id: str, since_seconds: int = 3600) -> dict[str, Any]:
        """Generate aggregated summary for a project."""
        events = self.query(project_id, since_seconds=since_seconds, limit=10000)

        severity_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        error_fingerprints: dict[str, dict] = {}
        latencies: list[float] = []

        for event in events:
            sev = event.get("severity", "UNKNOWN")
            cat = event.get("category", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            category_counts[cat] = category_counts.get(cat, 0) + 1

            # Track unique errors by fingerprint
            if cat == "error" and event.get("fingerprint"):
                fp = event["fingerprint"]
                if fp not in error_fingerprints:
                    error_fingerprints[fp] = {
                        "fingerprint": fp,
                        "count": 0,
                        "last_seen": event.get("timestamp_iso", ""),
                        "message": event.get("payload", {}).get("message", ""),
                        "error_type": event.get("payload", {}).get("error_type", ""),
                    }
                error_fingerprints[fp]["count"] += 1

            # Collect latencies from network events
            if cat == "network":
                lat = event.get("payload", {}).get("latency_ms")
                if lat is not None:
                    latencies.append(lat)

        # Compute p99 latency
        p99 = 0.0
        if latencies:
            latencies.sort()
            idx = int(len(latencies) * 0.99)
            p99 = latencies[min(idx, len(latencies) - 1)]

        # Top errors sorted by count
        top_errors = sorted(error_fingerprints.values(), key=lambda e: e["count"], reverse=True)[:10]

        return {
            "project_id": project_id,
            "since_seconds": since_seconds,
            "total_events": len(events),
            "error_count": severity_counts.get("ERROR", 0) + severity_counts.get("CRITICAL", 0) + severity_counts.get("FATAL", 0),
            "warning_count": severity_counts.get("WARNING", 0),
            "crash_count": category_counts.get("crash", 0),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "top_errors": top_errors,
            "p99_latency_ms": round(p99, 2),
        }

    def rotate(self) -> dict[str, int]:
        """
        Rotate storage tiers: hot->warm, warm->cold, cold->delete.
        Returns counts of files moved/deleted per tier.
        """
        stats = {"hot_to_warm": 0, "warm_to_cold": 0, "cold_deleted": 0}
        now = datetime.now(timezone.utc)

        # Hot -> Warm (files older than hot_max_age_hours)
        hot_cutoff = now - timedelta(hours=self.hot_max_age_hours)
        stats["hot_to_warm"] = self._move_tier("hot", "warm", hot_cutoff, compress=True)

        # Warm -> Cold (files older than warm_max_age_days)
        warm_cutoff = now - timedelta(days=self.warm_max_age_days)
        stats["warm_to_cold"] = self._move_tier("warm", "cold", warm_cutoff, compress=False)

        # Cold -> Delete (files older than cold_max_age_days)
        cold_cutoff = now - timedelta(days=self.cold_max_age_days)
        stats["cold_deleted"] = self._delete_old("cold", cold_cutoff)

        return stats

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage usage statistics."""
        stats = {}
        for tier in ("hot", "warm", "cold"):
            tier_dir = self.base_dir / tier
            if not tier_dir.exists():
                stats[tier] = {"files": 0, "size_mb": 0.0}
                continue

            total_size = 0
            file_count = 0
            for f in tier_dir.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size
                    file_count += 1

            stats[tier] = {
                "files": file_count,
                "size_mb": round(total_size / (1024 * 1024), 2),
            }

        return stats

    def _read_file(self, filepath: Path) -> list[dict[str, Any]]:
        """Read events from a JSONL file (supports .gz)."""
        events = []
        try:
            if filepath.suffix == ".gz":
                with gzip.open(filepath, "rt", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            events.append(json.loads(line))
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            events.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass  # Skip corrupted files
        return events

    def _move_tier(self, from_tier: str, to_tier: str, cutoff: datetime, compress: bool) -> int:
        """Move files older than cutoff from one tier to another."""
        moved = 0
        from_dir = self.base_dir / from_tier
        if not from_dir.exists():
            return 0

        for project_dir in from_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_id = project_dir.name
            to_project_dir = self.base_dir / to_tier / project_id
            to_project_dir.mkdir(parents=True, exist_ok=True)

            for filepath in list(project_dir.iterdir()):
                if not filepath.is_file():
                    continue

                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
                if file_mtime >= cutoff:
                    continue

                if compress and filepath.suffix != ".gz":
                    dest = to_project_dir / (filepath.name + ".gz")
                    with open(filepath, "rb") as f_in:
                        with gzip.open(dest, "wb") as f_out:
                            f_out.writelines(f_in)
                    filepath.unlink()
                else:
                    dest = to_project_dir / filepath.name
                    filepath.rename(dest)

                moved += 1

        return moved

    def _delete_old(self, tier: str, cutoff: datetime) -> int:
        """Delete files older than cutoff from a tier."""
        deleted = 0
        tier_dir = self.base_dir / tier
        if not tier_dir.exists():
            return 0

        for project_dir in tier_dir.iterdir():
            if not project_dir.is_dir():
                continue

            for filepath in list(project_dir.iterdir()):
                if not filepath.is_file():
                    continue

                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
                if file_mtime < cutoff:
                    filepath.unlink()
                    deleted += 1

        return deleted
