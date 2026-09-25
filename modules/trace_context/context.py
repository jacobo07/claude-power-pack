"""Cross-node trace correlation without an OpenTelemetry SDK.

Clean-room reconstruction (UWCP assimilation R5, vault/specs/uwcp-assimilation.md §14);
concepts only, from the specifications, no upstream code:
  - W3C Trace Context `traceparent`: version-traceid-parentid-flags, lowercase hex,
    32/16 digits, all-zero ids invalid, version ff invalid, version 00 has exactly
    four fields (w3.org/TR/trace-context, Recommendation).
  - OTel "Environment Variables as Context Propagation Carriers": TRACEPARENT and
    TRACESTATE in a child process environment (spec status: Release Candidate).
  - OTel GenAI semantic conventions: attribute NAMES only, pinned below; their
    status is Development, so the pin is the contract, not upstream.
  - Span records are a subset of OTLP JSON span fields so a Collector's file
    receiver could ingest them later (threshold in the plan, §10).

AUTHORITY RULE: nothing that decides (routing, harvest, status, done-gate) may read
what this module writes. Ids here are correlation only; `run_token` and fences stay
the authority. Emission is best-effort: failing to write a span never alters work.
"""
from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path

ENV_TRACEPARENT = "TRACEPARENT"
ENV_TRACESTATE = "TRACESTATE"
_TP = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})(-.*)?$")

GEN_AI_ATTRIBUTES = frozenset({
    "gen_ai.operation.name", "gen_ai.provider.name", "gen_ai.request.model",
    "gen_ai.response.model", "gen_ai.response.finish_reasons", "gen_ai.usage.input_tokens",
    "gen_ai.usage.output_tokens", "gen_ai.conversation.id",
})
OTHER_ATTRIBUTES = frozenset({"error.type"})
LOCAL_PREFIX = "uwcp."


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str                        # the span that is the PARENT of anything started from here
    sampled: bool = True
    tracestate: str = ""

    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"


def _nonzero_hex(nbytes: int) -> str:
    while True:
        v = secrets.token_hex(nbytes)
        if v.strip("0"):
            return v


TRACE_ID_BYTES = 16                     # W3C: 32 lowercase hex digits
SPAN_ID_BYTES = 8                       # W3C: 16 lowercase hex digits
FINDING_EXCERPT = 80                    # how much of a bad inherited header a finding quotes


def new_trace_id() -> str:
    return _nonzero_hex(TRACE_ID_BYTES)


def new_span_id() -> str:
    return _nonzero_hex(SPAN_ID_BYTES)


def parse_traceparent(value: str | None) -> TraceContext | None:
    """A context, or None when the header is absent or invalid. Never raises."""
    if not isinstance(value, str):
        return None
    m = _TP.match(value.strip())
    if not m:
        return None
    version, trace_id, span_id, flags, rest = m.groups()
    if version == "ff" or not trace_id.strip("0") or not span_id.strip("0"):
        return None
    if version == "00" and rest:
        return None
    return TraceContext(trace_id, span_id, bool(int(flags, 16) & 1))


@dataclass(frozen=True)
class Inherited:
    context: TraceContext
    finding: str = ""                   # non-empty when an inherited value was unusable


def from_env(env: dict | None = None) -> Inherited:
    """The context this process was started under. An invalid inherited value starts
    a NEW trace and says so, rather than silently joining nothing or crashing."""
    env = os.environ if env is None else env
    raw = env.get(ENV_TRACEPARENT)
    ctx = parse_traceparent(raw)
    if ctx is not None:
        return Inherited(TraceContext(ctx.trace_id, ctx.span_id, ctx.sampled,
                                      env.get(ENV_TRACESTATE, "")))
    fresh = TraceContext(new_trace_id(), new_span_id())
    if raw is None:
        return Inherited(fresh)
    return Inherited(fresh, f"invalid inherited {ENV_TRACEPARENT} {raw[:FINDING_EXCERPT]!r}; started a new trace")


def child_env(env: dict, ctx: TraceContext, span_id: str) -> dict:
    """A copy of `env` for a child whose parent span is `span_id` in `ctx`'s trace."""
    out = dict(env)
    out[ENV_TRACEPARENT] = TraceContext(ctx.trace_id, span_id, ctx.sampled).traceparent()
    if ctx.tracestate:
        out[ENV_TRACESTATE] = ctx.tracestate
    else:
        out.pop(ENV_TRACESTATE, None)
    return out


class AttributeRejected(ValueError):
    pass


def span_record(name: str, trace_id: str, span_id: str, parent_span_id: str, start_ns: int,
                end_ns: int, host_id: str, attributes: dict | None = None) -> dict:
    attrs = dict(attributes or {})
    for k in attrs:
        if not (k in GEN_AI_ATTRIBUTES or k in OTHER_ATTRIBUTES or k.startswith(LOCAL_PREFIX)):
            raise AttributeRejected(f"attribute {k!r} is not pinned; use {LOCAL_PREFIX}* or a "
                                    "pinned gen_ai.* name")
    if parse_traceparent(f"00-{trace_id}-{span_id}-01") is None:
        raise AttributeRejected("trace_id/span_id are not valid W3C ids")
    if parent_span_id and parse_traceparent(f"00-{trace_id}-{parent_span_id}-01") is None:
        raise AttributeRejected("parent_span_id is not a valid W3C span id")
    if end_ns < start_ns:
        raise AttributeRejected("span ends before it starts")
    return {"traceId": trace_id, "spanId": span_id, "parentSpanId": parent_span_id or "",
            "name": name, "startTimeUnixNano": int(start_ns), "endTimeUnixNano": int(end_ns),
            "hostId": host_id, "attributes": attrs}


class SpanWriter:
    """Append span records to a JSONL file. Never raises into the caller."""

    def __init__(self, path):
        self.path = Path(path)
        self.emitted = 0
        self.failures = 0
        self.last_error = ""

    def emit(self, record: dict) -> bool:
        try:
            line = json.dumps(record, sort_keys=True, separators=(",", ":"))
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
            self.emitted += 1
            return True
        except Exception as exc:        # telemetry must never change the work it observes
            self.failures += 1
            self.last_error = f"{type(exc).__name__}: {exc}"
            return False
