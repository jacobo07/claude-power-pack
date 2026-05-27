"""UQF Principle base class + registry.

A Principle is an executable quality check that can be applied to any
target (code path, code string, prompt dict, etc.) in any domain
(code / prompts / docs / tests / workflows). The base class enforces
a uniform check() interface; the registry collects all active
principles for the auditor to enumerate.

Source attribution: where a principle derives from ECC doctrine, the
subclass sets `source = "ECC/Affaan Mustafa MIT"`. PP-native principles
keep the default "PP-native".
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class PrincipleResult:
    """Outcome of one Principle.check() call.

    Fields are intentionally explicit. `passed` is the binary verdict;
    `score` is the 0.0-1.0 gradient (so a principle can express
    "partial credit" without breaking the binary gate); `evidence` is
    a short human-readable cite (filename:line, snippet, or count);
    `fix_hint` is the actionable next step. `source` carries the
    license attribution where applicable.
    """

    principle_name: str
    domain: str
    passed: bool
    score: float
    evidence: str
    fix_hint: str
    source: str = "PP-native"


class Principle(ABC):
    """Base class for all UQF principles.

    Subclasses MUST set class attributes `name`, `description`,
    `domains` (list of domains this principle applies to), and
    implement `check()`. They MAY override `score()` to give a
    gradient instead of binary.
    """

    name: ClassVar[str] = "unnamed"
    description: ClassVar[str] = ""
    domains: ClassVar[list[str]] = []
    source: ClassVar[str] = "PP-native"

    @abstractmethod
    def check(self, target: Any, domain: str) -> PrincipleResult:
        """Verify the principle against `target` in `domain`.

        `target` is shape-dependent on the principle: it may be a
        path string, raw code string, a parsed dict (finding,
        prompt), or a list (findings batch). Each Principle subclass
        documents the expected shape.
        """
        ...

    def score(self, target: Any, domain: str) -> float:
        """Return 0.0-1.0 gradient. Default = check().score."""
        return self.check(target, domain).score


_REGISTRY: list[Principle] = []


def register(p: Principle) -> Principle:
    """Add a principle to the active registry. Returns the instance
    so this can be used as a one-liner at module load time.

    Duplicate registrations (same `name`) replace the prior entry --
    so reloading a module during development doesn't accumulate
    stale duplicates."""
    global _REGISTRY
    _REGISTRY = [x for x in _REGISTRY if x.name != p.name]
    _REGISTRY.append(p)
    return p


def get_all(domain: str | None = None) -> list[Principle]:
    """Return all registered principles, optionally filtered by domain."""
    if domain is None:
        return list(_REGISTRY)
    return [p for p in _REGISTRY if domain in p.domains]


def clear_registry() -> None:
    """Test helper: empty the registry. NOT for production use."""
    global _REGISTRY
    _REGISTRY = []


def load_all_principles() -> int:
    """Import every principle module so it self-registers. Returns
    the count of principles active after loading. Idempotent."""
    from importlib import import_module
    for mod_name in (
        "pre_report_gate",
        "zero_findings_valid",
        "false_positives_catalog",
        "proof_triad",
        "severity_table",
        "error_never_silent",
        "tdd_workflow",
        "aaa_test_pattern",
        "prompt_defense_baseline",
    ):
        try:
            import_module(f"modules.uqf.principles.{mod_name}")
        except ImportError:
            # Modules not yet implemented are skipped silently;
            # the registry will simply not have them. Future Mx
            # implementations populate them.
            pass
    return len(_REGISTRY)


__all__ = [
    "Principle",
    "PrincipleResult",
    "register",
    "get_all",
    "clear_registry",
    "load_all_principles",
]
