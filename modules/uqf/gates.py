"""UQF Gates -- decorators + assert helpers.

Source: ECC/Affaan Mustafa MIT
       (CONTRIBUTING.md "Hook Format" semantics adapted to Python
        decorators)

Two surfaces:

  uqf_gate(domain, threshold, mode)
    Function/class decorator. Runs UQFAuditor over the calling
    module's file each time the decorated function is invoked.
    mode controls behavior on threshold violation:
      "warn"    -> print warning, continue
      "enforce" -> raise UQFViolation
      "audit"   -> log score, never warn/raise (telemetry only)

  assert_uqf(path, threshold)
    Used in test files / done-gates. Returns the AuditReport;
    raises AssertionError if score < threshold.
"""
from __future__ import annotations
import functools
import inspect
from pathlib import Path

from modules.uqf.auditor import AuditReport, UQFAuditor


class UQFViolation(Exception):
    """Raised by an enforce-mode uqf_gate when the score falls
    below the configured threshold."""


def uqf_gate(domain: str = "code",
             threshold: float = 70.0,
             mode: str = "warn"):
    """Decorator factory. See module docstring for mode semantics."""
    if mode not in ("warn", "enforce", "audit"):
        raise ValueError(f"uqf_gate mode must be warn/enforce/audit, "
                         f"got {mode!r}")

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            try:
                module_file = inspect.getfile(fn)
            except (TypeError, OSError):
                return result
            try:
                auditor = UQFAuditor()
                report = auditor.audit_file(module_file, domain=domain)
            except Exception:
                # Fail-open: a broken auditor must never break real code.
                return result
            if report.score_pct < threshold:
                msg = (
                    f"[UQF {mode.upper()}] {module_file}: "
                    f"score={report.score_pct:.1f}% "
                    f"< threshold {threshold:.1f}%"
                )
                if mode == "enforce":
                    raise UQFViolation(msg + "\n" + "\n".join(
                        f"  - {h}" for h in report.fix_hints[:5]))
                if mode == "warn":
                    print(msg)
                    for h in report.fix_hints[:3]:
                        print(f"  -> {h}")
            return result
        return wrapper

    return decorator


def assert_uqf(path: str, threshold: float = 0.0) -> AuditReport:
    """Audit `path` and assert the score meets `threshold`.

    Default threshold is 0.0 (baseline mode -- accept any score),
    used by cold-boot M0 verification. Production gates raise it
    progressively (M16 SCS C14 starts at 0% baseline, raised in
    future cycles).
    """
    auditor = UQFAuditor()
    report = auditor.audit_file(path)
    if not Path(path).is_file():
        raise AssertionError(f"UQF gate: file not found: {path}")
    if report.score_pct < threshold:
        details = "\n".join(f"  - {h}" for h in report.fix_hints[:5])
        raise AssertionError(
            f"UQF gate: {path} score={report.score_pct:.1f}% "
            f"< threshold {threshold:.1f}%\n{details}"
        )
    return report


__all__ = ["uqf_gate", "assert_uqf", "UQFViolation"]
