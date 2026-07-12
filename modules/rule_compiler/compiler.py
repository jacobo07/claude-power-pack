"""Compile the hard-rule corpus into three artifacts.

  A. rules_db.json   -- every rule, validated, with field-level verdicts
  B. HARD-RULES-DIGEST.md -- <=4 KB trigger index the kill switch reads
  C. rejections.md   -- every malformed rule + why, so it can be repaired

A rejected rule is NOT deleted from its archive. It is denied entry to
the ACTIVE set: it stops being something the agent is told to obey and
becomes something the Owner is told to fix. HR-002 (a ZZZ smoke fixture
sealed CRITICAL) must not be able to fire; it also must not vanish
silently.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .digest import DIGEST_MAX_BYTES, build_digest
from .parser import PP_ROOT, load_corpus
from .schema import REASON_HELP, Reason, Rule, find_boilerplate_stops, validate

HOME = Path.home()
DIGEST_PATH = (HOME / ".claude" / "knowledge_vault" / "core"
               / "HARD-RULES-DIGEST.md")
COMPILED_DIR = PP_ROOT / "vault" / "hard_rules" / "compiled"
DB_PATH = COMPILED_DIR / "rules_db.json"
REJECTIONS_PATH = COMPILED_DIR / "rejections.md"
CLI_HINT = "~/.claude/skills/claude-power-pack/tools/hardrule_compile.py"


@dataclass
class CompileResult:
    valid: list[Rule]
    rejected: list[Rule]
    digest_text: str
    digest_bytes: int
    omitted: list[str]

    @property
    def within_budget(self) -> bool:
        return self.digest_bytes <= DIGEST_MAX_BYTES


def compile_rules(rules: list[Rule] | None = None) -> CompileResult:
    corpus = load_corpus() if rules is None else rules
    boilerplate = find_boilerplate_stops(corpus)
    for r in corpus:
        validate(r, boilerplate)
    valid = [r for r in corpus if r.valid]
    rejected = [r for r in corpus if not r.valid]
    text, omitted = build_digest(valid, rejected, CLI_HINT)
    return CompileResult(
        valid=valid,
        rejected=rejected,
        digest_text=text,
        digest_bytes=len(text.encode("utf-8")),
        omitted=omitted,
    )


def _render_rejections(res: CompileResult, stamp: str) -> str:
    lines = [
        "# HARD-RULE REJECTION REPORT (compiled artifact)",
        "",
        f"Compiled {stamp}.",
        "",
        f"**{len(res.rejected)} of {len(res.valid) + len(res.rejected)} "
        "rules failed the schema gate.** A rejected rule is not deleted "
        "-- it is denied entry to the ACTIVE set. It cannot fire, and it "
        "is listed here so it can be repaired or retired.",
        "",
        "A rule earns a place in the kill switch by being able to stop "
        "the agent: an observable TRIGGER, an imperative ACTION, and a "
        "real incident as EVIDENCE.",
        "",
    ]
    by_source: dict[str, list[Rule]] = {}
    for r in res.rejected:
        by_source.setdefault(r.source, []).append(r)
    for source, rules in sorted(by_source.items()):
        lines += [f"## {source} ({len(rules)} rejected)", ""]
        for r in rules:
            lines.append(f"### {r.rule_id} -- {r.title[:90]}")
            for reason in r.rejections:
                lines.append(f"- **{reason.value}** -- {REASON_HELP[reason]}")
            if r.trigger:
                lines.append(f"  - observed TRIGGER: `{r.trigger[:120]}`")
            if r.stop:
                first = next((l for l in r.stop.splitlines() if l.strip()), "")
                lines.append(f"  - observed ACTION: `{first[:120]}`")
            if r.evidence:
                lines.append(f"  - observed EVIDENCE: `{r.evidence[:120]}`")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_artifacts(res: CompileResult) -> dict[str, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    db = {
        "compiled_at": stamp,
        "digest_bytes": res.digest_bytes,
        "digest_max_bytes": DIGEST_MAX_BYTES,
        "counts": {
            "total": len(res.valid) + len(res.rejected),
            "valid": len(res.valid),
            "rejected": len(res.rejected),
            "omitted_from_digest": len(res.omitted),
        },
        "rules": [r.as_dict() for r in res.valid + res.rejected],
    }
    _atomic_write(DB_PATH, json.dumps(db, indent=2, ensure_ascii=False) + "\n")
    _atomic_write(REJECTIONS_PATH, _render_rejections(res, stamp))
    DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(DIGEST_PATH, res.digest_text)
    return {"db": DB_PATH, "rejections": REJECTIONS_PATH, "digest": DIGEST_PATH}


def _atomic_write(path: Path, text: str) -> None:
    """Read -> compose -> tmp -> os.replace. Never `>>` (HR-4 / U-25)."""
    import os
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def show(rule_ids: list[str]) -> list[Rule]:
    corpus = load_corpus()
    boilerplate = find_boilerplate_stops(corpus)
    for r in corpus:
        validate(r, boilerplate)
    want = {i.upper() for i in rule_ids}
    return [r for r in corpus if r.rule_id.upper() in want]


def rules_in_class(class_name: str) -> list[Rule]:
    """Every BINDING rule in a trigger class -- the drill-down the
    digest points at. Rejected rules are excluded: they cannot fire."""
    from .digest import bucket
    res = compile_rules()
    return bucket(res.valid).get(class_name.upper(), [])
