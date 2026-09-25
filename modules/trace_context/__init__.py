"""W3C trace correlation, no SDK (UWCP assimilation R5). See context.py for contract and provenance."""
from .context import (ENV_TRACEPARENT, ENV_TRACESTATE, GEN_AI_ATTRIBUTES, AttributeRejected,
                      Inherited, SpanWriter, TraceContext, child_env, from_env, new_span_id,
                      new_trace_id, parse_traceparent, span_record)

__all__ = ["ENV_TRACEPARENT", "ENV_TRACESTATE", "GEN_AI_ATTRIBUTES", "AttributeRejected",
           "Inherited", "SpanWriter", "TraceContext", "child_env", "from_env", "new_span_id",
           "new_trace_id", "parse_traceparent", "span_record"]
