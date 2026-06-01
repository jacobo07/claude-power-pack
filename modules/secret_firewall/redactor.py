"""Universal Redaction Bus -- substitute PATTERNS matches with [REDACTED:<name>]."""
from __future__ import annotations

from .detector import PATTERNS

# One terminal page (~2 KB) is enough to identify a redacted record while
# bounding log inflation; raise only on operator request.
DEFAULT_LOG_MAX_LEN = 2000


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    # Higher-severity patterns first so a CRITICAL match wins when
    # ranges overlap (e.g. anthropic_key inside a generic_secret line).
    for name, (pat, _sev) in sorted(
        PATTERNS.items(), key=lambda kv: -kv[1][1].value
    ):
        out = pat.sub(f"[REDACTED:{name}]", out)
    return out


def redact_for_log(text: str, *, max_len: int = DEFAULT_LOG_MAX_LEN) -> str:
    r = redact(text)
    if len(r) <= max_len:
        return r
    return r[:max_len] + f"... [truncated {len(r) - max_len} chars]"
