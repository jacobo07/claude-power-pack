#!/usr/bin/env python3
"""floor_diet.py -- ctx-rent-x Phase 2: top-level floor diet, rows 1-3 of ctx-rent-obs b3 PROPOSAL.

Rows: 1 park agent files unused/not hook-dispatched (agents/ -> agents-parked/), 2 move three always-loaded rules
into skills (rules/X.md -> skills/X/SKILL.md plus a stub) and list them in skill-rule-index.md, 3 trim each
project MEMORY.md to 200 lines (cold lines -> MEMORY_COLD.md). Row 5 (hook additionalContext cap) edits hook code and
is a separate laptop step.

Every apply backs up each touched path under <home>/.claude/backups/ctx-rent-x-<ts>/ and writes revert.sh there.
Default is a dry run; --home lets tests and GEX44 dry-runs target a scratch HOME. Never run apply against a live
HOME from a worker: it is a LAPTOP STEP.

CLI: plan|apply|revert --home DIR [--keep-agents a,b] [--used-agents FILE] [--ts TS]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

RULES_TO_SKILLS = [
    "generated-content-needs-an-evidence-gate",
    "effect-authority-across-transports",
    "durable-exit-transaction",
]
MEMORY_LIMIT = 200


def _dispatched_agents(claude: Path) -> set[str]:
    """Agent names a hook/command/script mentions as subagent_type: kept regardless of recent use."""
    names: set[str] = set()
    pat = re.compile(r"subagent_type[\"'\s:=]+([A-Za-z0-9_.:-]+)")
    for d in ("hooks", "commands"):
        for f in (claude / d).rglob("*") if (claude / d).is_dir() else []:
            if f.suffix in {".js", ".py", ".md", ".json", ".ts"} and f.is_file():
                try:
                    names.update(pat.findall(f.read_text(errors="ignore")))
                except OSError:
                    pass
    return names


def plan(home: Path, keep_agents: set[str], used_agents: set[str]) -> dict:
    claude = home / ".claude"
    keep = keep_agents | used_agents | _dispatched_agents(claude)
    agents = sorted((claude / "agents").glob("*.md")) if (claude / "agents").is_dir() else []
    park = [a.name for a in agents if a.stem not in keep]
    rules = [r for r in RULES_TO_SKILLS if (claude / "rules" / f"{r}.md").is_file()]
    mem = []
    for m in sorted((claude / "projects").glob("*/memory/MEMORY.md")) if (claude / "projects").is_dir() else []:
        n = len(m.read_text(errors="ignore").splitlines())
        if n > MEMORY_LIMIT:
            mem.append({"path": str(m.relative_to(home)), "lines": n, "cold": n - MEMORY_LIMIT})
    return {"agents_park": park, "agents_kept": sorted(a.stem for a in agents if a.stem in keep),
            "rules_to_skills": rules, "memory_trim": mem}


def _backup(home: Path, bdir: Path, rel: Path) -> None:
    src = home / rel
    if src.exists():
        dst = bdir / "files" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def apply(home: Path, p: dict, ts: str) -> Path:
    claude = home / ".claude"
    bdir = claude / "backups" / f"ctx-rent-x-{ts}"
    if bdir.exists():
        raise SystemExit(f"backup dir exists: {bdir}")
    (bdir / "files").mkdir(parents=True)
    created: list[str] = []   # paths that did not exist before: revert deletes them
    touched: list[str] = []   # paths that existed: revert restores them
    rel = lambda x: Path(".claude") / x  # noqa: E731

    parked = claude / "agents-parked"
    for a in p["agents_park"]:
        _backup(home, bdir, rel(f"agents/{a}"))
        touched.append(f".claude/agents/{a}")
        parked.mkdir(exist_ok=True)
        shutil.move(str(claude / "agents" / a), str(parked / a))
        created.append(f".claude/agents-parked/{a}")

    idx = claude / "rules" / "skill-rule-index.md"
    _backup(home, bdir, rel("rules/skill-rule-index.md"))
    lines = []
    for r in p["rules_to_skills"]:
        src = claude / "rules" / f"{r}.md"
        body = src.read_text()
        _backup(home, bdir, rel(f"rules/{r}.md"))
        touched.append(f".claude/rules/{r}.md")
        sk = claude / "skills" / r / "SKILL.md"
        if sk.exists():
            raise SystemExit(f"skill exists, refusing to overwrite: {sk}")
        sk.parent.mkdir(parents=True)
        first = next((l for l in body.splitlines() if l.strip() and not l.startswith("#")), r)
        sk.write_text(f"---\nname: {r}\ndescription: {first[:300].replace(chr(10), ' ')}\n---\n\n{body}")
        created.append(f".claude/skills/{r}/SKILL.md")
        src.unlink()
        lines.append(f"- `{r}` -> skill `{r}` (moved from always-loaded rules by ctx-rent-x floor diet)")
    if lines:
        if idx.exists():
            touched.append(".claude/rules/skill-rule-index.md")
            idx.write_text(idx.read_text().rstrip("\n") + "\n" + "\n".join(lines) + "\n")
        else:
            idx.write_text("# Skill rule index\n\n" + "\n".join(lines) + "\n")
            created.append(".claude/rules/skill-rule-index.md")

    for m in p["memory_trim"]:
        path = home / m["path"]
        _backup(home, bdir, Path(m["path"]))
        touched.append(m["path"])
        ls = path.read_text().splitlines()
        # keep the head (hooks to the newest/most-used memories are written first) and park the rest
        cold = path.with_name("MEMORY_COLD.md")
        if cold.exists():
            _backup(home, bdir, Path(m["path"]).with_name("MEMORY_COLD.md"))
            touched.append(str(Path(m["path"]).with_name("MEMORY_COLD.md")))
        else:
            created.append(str(Path(m["path"]).with_name("MEMORY_COLD.md")))
        prior = cold.read_text() if cold.exists() else ""
        cold.write_text(prior + ("\n" if prior and not prior.endswith("\n") else "") + "\n".join(ls[MEMORY_LIMIT:]) + "\n")
        path.write_text("\n".join(ls[:MEMORY_LIMIT]) + "\n")

    (bdir / "manifest.json").write_text(json.dumps({"home": str(home), "created": created, "touched": touched}, indent=1))
    return bdir


def revert(home: Path, bdir: Path) -> None:
    man = json.loads((bdir / "manifest.json").read_text())
    for c in man["created"]:
        t = home / c
        if t.is_file():
            t.unlink()
    for d in (".claude/agents-parked",):
        t = home / d
        if t.is_dir() and not any(t.iterdir()):
            t.rmdir()
    for t_rel in man["touched"]:
        src = bdir / "files" / t_rel
        if src.is_file():
            dst = home / t_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for r in RULES_TO_SKILLS:
        d = home / ".claude" / "skills" / r
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "apply", "revert"])
    ap.add_argument("--home", required=True)
    ap.add_argument("--keep-agents", default="")
    ap.add_argument("--used-agents", help="file, one agent name per line (agents used in the last 30 days)")
    ap.add_argument("--ts", default="manual")
    ap.add_argument("--backup-dir")
    a = ap.parse_args(argv)
    home = Path(a.home)
    keep = {x for x in a.keep_agents.split(",") if x}
    used = set(Path(a.used_agents).read_text().split()) if a.used_agents else set()
    if a.cmd == "revert":
        revert(home, Path(a.backup_dir)); print("reverted"); return 0
    p = plan(home, keep, used)
    if a.cmd == "plan":
        print(json.dumps(p, indent=1)); return 0
    print(apply(home, p, a.ts)); return 0


if __name__ == "__main__":
    sys.exit(main())
