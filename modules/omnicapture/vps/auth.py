"""
OmniCapture — Authentication & Rate Limiting.
Per-project API key validation with token bucket rate limiting.
"""

import time
import hmac
from typing import Any


class TokenBucket:
    """Simple token bucket rate limiter."""

    def __init__(self, rate_per_min: int):
        self.rate = rate_per_min / 60.0  # tokens per second
        self.capacity = rate_per_min
        self.tokens = float(rate_per_min)
        self.last_refill = time.monotonic()

    def consume(self, count: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= count:
            self.tokens -= count
            return True
        return False

    @property
    def retry_after_seconds(self) -> float:
        """Seconds until enough tokens are available."""
        if self.tokens >= 1:
            return 0.0
        return (1.0 - self.tokens) / self.rate


class AuthManager:
    """Validates API keys and enforces rate limits."""

    def __init__(self, config: dict[str, Any]):
        self._keys: dict[str, dict] = {}  # key_value -> key_config
        self._project_buckets: dict[str, TokenBucket] = {}
        self._global_bucket = TokenBucket(config.get("global_per_min", 1000))

        # Build key lookup from config
        for key_name, key_config in config.get("api_keys", {}).items():
            key_value = key_config["key"]
            self._keys[key_value] = {
                "name": key_name,
                "projects": set(key_config.get("projects", [])),
                "rate_limit": key_config.get("rate_limit_per_min", 60),
            }

    def authenticate(self, api_key: str) -> tuple[bool, str | None, set[str] | None]:
        """
        Validate an API key.
        Returns: (is_valid, key_name, allowed_projects)
        """
        key_config = self._keys.get(api_key)
        if not key_config:
            return False, None, None
        return True, key_config["name"], key_config["projects"]

    def check_rate_limit(self, api_key: str, event_count: int = 1) -> tuple[bool, float]:
        """
        Check rate limits for a request.
        Returns: (is_allowed, retry_after_seconds)
        """
        # Global rate limit
        if not self._global_bucket.consume(event_count):
            return False, self._global_bucket.retry_after_seconds

        # Per-key rate limit
        key_config = self._keys.get(api_key)
        if not key_config:
            return False, 0.0

        key_name = key_config["name"]
        if key_name not in self._project_buckets:
            self._project_buckets[key_name] = TokenBucket(key_config["rate_limit"])

        bucket = self._project_buckets[key_name]
        if not bucket.consume(event_count):
            return False, bucket.retry_after_seconds

        return True, 0.0

    def is_project_allowed(self, api_key: str, project_id: str) -> bool:
        """Check if an API key is authorized for a specific project."""
        key_config = self._keys.get(api_key)
        if not key_config:
            return False
        return project_id in key_config["projects"]
