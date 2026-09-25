"""Serving-benchmark metrics for any OpenAI-compatible endpoint (UWCP assimilation R6)."""
from .bench import RequestResult, run, run_request, summarize

__all__ = ["RequestResult", "run", "run_request", "summarize"]
