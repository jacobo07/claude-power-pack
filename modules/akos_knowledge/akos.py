#!/usr/bin/env python3
"""akos.py -- AKOS brief parser + domain resolver + unit selector.

Single source of truth for turning a static AKOS_KNOWLEDGE_BRIEF.md into
domain-tagged units and selecting the subset relevant to a given repo. Both
live consumers (JIT injector, question harvester) import from here so the
brief is parsed exactly one way.

Brief format (as emitted by the AKOS engine), by example:

    # Knowledge Brief: claude-power-pack
    **Domains:** saas, sales, ai_automation, scaling, ...
    **Units matched:** 89

    ### Saas (4 insights)

    **1.** [system_prompt] _142-I Scaled a $50k month AI Product..._
    > I scaled an AI product to 50K per month without sales calls ...

    **2.** [system_prompt] _453-How To Get 1,000 Paying SaaS Customer..._
    > **Source:** `youtube\\...`

Domain headers -> ``### <Name> (<n> insights)``; units -> ``**<i>.** [<type>]
_<title>_`` followed by a ``> <snippet>`` line. The domain name is normalized
to a lowercase underscored key ("Ai Automation" -> "ai_automation").

Fail-open ABSOLUTE: any malformed input yields an empty parse, never raises.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MAP = _PP_ROOT / "vault" / "config" / "akos_domain_map.json"
_BRIEF_NAME = "AKOS_KNOWLEDGE_BRIEF.md"

# Bounds (a parser over an on-disk artifact must never run unbounded).
_MAX_BRIEF_BYTES = 2_000_000     # 2 MB — the PP brief is ~34 KB; guard anyway
_MAX_UNITS_PARSED = 2000         # hard ceiling on units returned from a brief
_BRIEF_WALK_UP = 3               # parents to check for a repo-root brief
_SNIP_LEN = 220                  # injected snippet char cap

_DOMAIN_HDR_RE = re.compile(r"^###\s+(.+?)\s+\((\d+)\s+insights?\)\s*$")
_UNIT_RE = re.compile(r"^\*\*(\d+)\.\*\*\s+\[([^\]]+)\]\s+_(.+?)_\s*$")
_QUOTE_RE = re.compile(r"^>\s?(.*)$")
# A brief line that is pure metadata inside a quote (Source/Language/etc.) is
# not a useful snippet lead — skip to the first substantive quote line.
_META_QUOTE_RE = re.compile(
    r"^\*\*(?:Source|Language|Transcribed)\b|^\s*$", re.I)


@dataclass
class AkosUnit:
    domain: str          # normalized key, e.g. "saas", "ai_automation"
    index: int           # 1-based position within its domain section
    kind: str            # brief type tag, e.g. "system_prompt" | "prompt"
    title: str           # source title (filename stem, cleaned)
    snippet: str         # first substantive quote line (bounded)

    def one_line(self) -> str:
        t = _clean_title(self.title)
        s = self.snippet.strip()
        if len(s) > _SNIP_LEN:
            s = s[:_SNIP_LEN].rstrip() + "…"
        return f"[{self.domain}] {t}" + (f' — "{s}"' if s else "")


def normalize_domain(name: str) -> str:
    """"Ai Automation" -> "ai_automation"; "Saas" -> "saas"."""
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")


def _clean_title(title: str) -> str:
    t = (title or "").strip()
    # Strip a leading numeric id + separators ("142-Foo", "054- 1 - Foo").
    t = re.sub(r"^\d+\s*-\s*(?:\d+\s*-\s*)?", "", t)
    # Drop a trailing ".md" the brief sometimes carries in the title.
    t = re.sub(r"\.md$", "", t)
    return t.strip()


def parse_brief(text: str) -> list[AkosUnit]:
    """Parse brief Markdown into domain-tagged units. Fail-open -> []."""
    try:
        if not text:
            return []
        units: list[AkosUnit] = []
        cur_domain = ""
        pending: AkosUnit | None = None
        for raw in text.split("\n"):
            line = raw.rstrip()
            hdr = _DOMAIN_HDR_RE.match(line)
            if hdr:
                cur_domain = normalize_domain(hdr.group(1))
                pending = None
                continue
            um = _UNIT_RE.match(line)
            if um and cur_domain:
                pending = AkosUnit(
                    domain=cur_domain,
                    index=int(um.group(1)),
                    kind=um.group(2).strip(),
                    title=um.group(3).strip(),
                    snippet="",
                )
                units.append(pending)
                if len(units) >= _MAX_UNITS_PARSED:
                    break
                continue
            # Attach the first substantive quote line as the snippet.
            if pending is not None and not pending.snippet:
                q = _QUOTE_RE.match(line)
                if q:
                    body = q.group(1).strip()
                    if body and not _META_QUOTE_RE.match(body):
                        pending.snippet = body
        return units
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return []


def find_brief(cwd) -> Path | None:
    """Locate the AKOS brief for a session cwd. Checks, in order:
    ``<cwd>/knowledge/BRIEF``, ``<cwd>/BRIEF``, then the same two under each
    of the nearest ``_BRIEF_WALK_UP`` parents (a session may open in a
    subdir while the brief lives at repo root). Fail-open -> None.
    """
    try:
        base = Path(cwd)
    except Exception:  # noqa: BLE001
        return None
    candidates: list[Path] = []
    chain = [base] + list(base.parents)[:_BRIEF_WALK_UP]
    for d in chain:
        candidates.append(d / "knowledge" / _BRIEF_NAME)
        candidates.append(d / _BRIEF_NAME)
    for p in candidates:
        try:
            if p.is_file() and p.stat().st_size <= _MAX_BRIEF_BYTES:
                return p
        except OSError:
            continue
    return None


def load_domain_map(path=None) -> dict:
    """Load the repo->domains map. Fail-open -> conservative empty map."""
    try:
        p = Path(path) if path else _DEFAULT_MAP
        cfg = json.loads(p.read_text(encoding="utf-8-sig"))
        if not isinstance(cfg, dict):
            return {"repos": {}, "max_units": 6, "per_domain": 3}
        cfg.setdefault("repos", {})
        cfg.setdefault("max_units", 6)
        cfg.setdefault("per_domain", 3)
        return cfg
    except Exception:  # noqa: BLE001 -- fail-open
        return {"repos": {}, "max_units": 6, "per_domain": 3}


def resolve_domains(cwd, domain_map: dict) -> list[str]:
    """Resolve target domains for a cwd by matching any lowercased path
    component against the map's repo keys (repo-root match preferred over a
    deeper subdir). Returns [] when no component matches — the conservative
    'brief-exists AND mapped' policy means an unmapped repo gets nothing.
    """
    try:
        repos = (domain_map or {}).get("repos") or {}
        if not repos:
            return []
        try:                                 # normalize relative -> absolute
            abscwd = Path(cwd).resolve()
        except Exception:                    # noqa: BLE001
            abscwd = Path(cwd)
        parts = [str(p).strip().lower() for p in abscwd.parts if str(p).strip()]
        # Root -> leaf: the first (topmost) matching component wins so a
        # nested cwd resolves to its repo root, not an incidental subdir.
        for part in parts:
            if part in repos:
                return list(repos[part])
            for key in repos:
                # startswith handles variant suffixes (infinityops-bis-capab).
                if part.startswith(key) and len(key) >= 4:
                    return list(repos[key])
        return []
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def select_units(units: list[AkosUnit], target_domains: list[str], *,
                 max_units: int = 6, per_domain: int = 3) -> list[AkosUnit]:
    """Pick units whose domain is in target_domains, up to per_domain each
    and max_units total, in target-domain order then document order.
    Deterministic (no scoring field exists in the brief). Fail-open -> [].
    """
    try:
        if not units or not target_domains:
            return []
        by_domain: dict[str, list[AkosUnit]] = {}
        for u in units:
            by_domain.setdefault(u.domain, []).append(u)
        out: list[AkosUnit] = []
        for dom in target_domains:
            key = normalize_domain(dom)
            for u in by_domain.get(key, [])[:max(0, per_domain)]:
                out.append(u)
                if len(out) >= max_units:
                    return out
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def units_for_cwd(cwd, *, domain_map_path=None):
    """End-to-end convenience for both consumers.

    Returns (brief_path, target_domains, selected_units). Any of the three
    is falsy when the policy declines injection (no brief, or unmapped repo,
    or no domain overlap). Fail-open -> (None, [], []).
    """
    try:
        cfg = load_domain_map(domain_map_path)
        domains = resolve_domains(cwd, cfg)
        if not domains:
            return (None, [], [])          # unmapped repo -> silence
        brief = find_brief(cwd)
        if brief is None:
            return (None, domains, [])     # mapped but no brief -> silence
        text = brief.read_text(encoding="utf-8-sig", errors="replace")
        units = parse_brief(text)
        selected = select_units(
            units, domains,
            max_units=int(cfg.get("max_units", 6)),
            per_domain=int(cfg.get("per_domain", 3)),
        )
        return (brief, domains, selected)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return (None, [], [])


def _cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="AKOS brief inspector")
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    brief, domains, units = units_for_cwd(args.cwd)
    if args.json:
        print(json.dumps({
            "brief": str(brief) if brief else None,
            "domains": domains,
            "units": [u.__dict__ for u in units],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"brief={brief}")
        print(f"domains={domains}")
        for u in units:
            print("  " + u.one_line())
        print(f"selected={len(units)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
