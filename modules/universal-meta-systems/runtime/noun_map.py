"""Noun Map Registry -- the single point of domain variability.

A meta-system's machinery is domain-blind; only the mapping of its abstract
nouns onto a domain changes (the corpus's own domain-substitution test). This
module loads that mapping for a repo, applies it to corpus text, and -- when no
mapping is declared -- PROPOSES candidate nouns without ever guessing meaning.

Contract (approved 2026-07-10):
  - Declared map lives in `<repo>/.pp_meta_systems.json`.
  - No file, or a malformed one -> fail-open to the GENERIC map (identity, no
    substitution) with a visible warning. Never crash; never silently guess.
  - Auto-derivation from CLAUDE.md is PROPOSE-only: it surfaces candidate local
    terms (frequency-ranked) for the Owner to map; it never invents a mapping.

`.pp_meta_systems.json` schema (all keys optional except noun_map):
  {
    "noun_map": { "artifact": "checkpoint", "transform": "training job", ... },
    "enabled":  ["MS-0", "MS-6"]      // subset of meta-systems; default = all 7
  }
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = ".pp_meta_systems.json"
DEFAULT_PROPOSE_TOP_N = 15
_MIN_TOKEN_LEN = 4          # ignore short function words when proposing candidates

# Small, domain-neutral stoplist: common English + doc/markdown scaffolding.
_STOPWORDS = frozenset("""
a an the and or but if then else for while of to in on at by with from into over
under this that these those it its is are was were be been being as not no do does
did done have has had will would shall should can could may might must each any all
every some such than when where which who whom whose why how what your you our we they
their them his her out up down off only also more most less least via per e g i.e
never always must-not rules rule output process path type skill claude code file files
project projects session sessions must use used using per pack power module modules
""".split())


@dataclass
class NounMap:
    mapping: dict[str, str] = field(default_factory=dict)
    source: str = "generic"          # "file" | "generic"
    enabled: tuple[str, ...] | None = None   # None => all meta-systems
    warnings: list[str] = field(default_factory=list)

    @property
    def is_generic(self) -> bool:
        return self.source == "generic" or not self.mapping


def _compile_substituter(mapping: dict[str, str]):
    """Single-pass, whole-word, case-insensitive substituter (longest key first).

    One combined alternation so a replacement's text can never itself be
    re-substituted (avoids chained double-mapping).
    """
    if not mapping:
        return None
    keys = sorted(mapping, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b",
                         re.IGNORECASE)
    lower = {k.lower(): v for k, v in mapping.items()}

    def _sub(text: str) -> str:
        if not text:
            return text
        return pattern.sub(lambda m: lower[m.group(0).lower()], text)

    return _sub


def load_noun_map(repo_root: str | Path) -> NounMap:
    """Load the repo's noun-map. Fail-open to generic; never raise."""
    root = Path(repo_root)
    cfg = root / CONFIG_FILENAME
    if not cfg.is_file():
        return NounMap(source="generic", warnings=[
            f"no {CONFIG_FILENAME} in {root}; using GENERIC noun-map "
            f"(no substitution). Declare one, or run 'propose' for candidates."])
    try:
        data = json.loads(cfg.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as e:
        return NounMap(source="generic", warnings=[
            f"{CONFIG_FILENAME} unreadable ({e.__class__.__name__}); "
            f"failing open to GENERIC noun-map."])

    raw = data.get("noun_map", {})
    if not isinstance(raw, dict):
        return NounMap(source="generic", warnings=[
            f"{CONFIG_FILENAME}: 'noun_map' is not an object; "
            f"failing open to GENERIC noun-map."])

    mapping = {str(k): str(v) for k, v in raw.items()
               if isinstance(k, str) and isinstance(v, (str, int, float))}
    enabled = data.get("enabled")
    enabled_t = None
    if isinstance(enabled, list):
        enabled_t = tuple(str(x).upper() for x in enabled
                          if re.fullmatch(r"MS-[0-6]", str(x).upper()))
    warnings: list[str] = []
    if not mapping:
        warnings.append(f"{CONFIG_FILENAME}: 'noun_map' is empty; "
                        f"behaving as GENERIC (no substitution).")
        return NounMap(source="generic", enabled=enabled_t, warnings=warnings)
    return NounMap(mapping=mapping, source="file", enabled=enabled_t, warnings=warnings)


def apply_noun_map(text: str, nm: NounMap) -> str:
    """Substitute a repo's local nouns for the corpus's abstract nouns."""
    sub = _compile_substituter(nm.mapping)
    return sub(text) if sub else text


def propose_candidates(repo_root: str | Path, top_n: int = DEFAULT_PROPOSE_TOP_N) -> list[str]:
    """PROPOSE candidate local domain nouns from the repo's CLAUDE.md.

    Deterministic, frequency-ranked, no semantics. The Owner maps a universal
    noun onto one of these; this function never produces the mapping itself.
    Returns [] when there is no CLAUDE.md to read.
    """
    root = Path(repo_root)
    src = root / "CLAUDE.md"
    if not src.is_file():
        return []
    try:
        text = src.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    counts: dict[str, int] = {}
    for tok in re.findall(r"[A-Za-z][A-Za-z_-]{%d,}" % (_MIN_TOKEN_LEN - 1), text):
        low = tok.lower()
        if low in _STOPWORDS:
            continue
        counts[low] = counts.get(low, 0) + 1
    # deterministic: highest frequency first, ties broken alphabetically
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [term for term, _ in ranked[:top_n]]
