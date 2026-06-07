#!/usr/bin/env python3
"""absorb_ecc_skills_agents.py -- CURATED selective absorption of ECC skills+agents.

The name-diff (ecc_skill_agent_diff.py) reports ~260 skills + 63 agents as
"net-new", but that over-counts: by PURPOSE most are out-of-PP-scope domains
(healthcare/homelab/network/finance/seo/...), redundant with the rules taxonomy
absorbed 2026-06-06 (*-patterns / *-testing / *-security per language), ECC
self-management, or overlap PP's existing 88 skills / 39 agents. Mass-copying
all 323 = bloat that violates adapt-not-copy.

This mirrors ONLY a curated, PP-aligned, non-redundant gem-set: ECC's
distinctive agent-harness / eval engineering skills + the language-reviewer
agents that pair with the new rules taxonomy. Everything else is recorded in a
skip-manifest with the reason. Mirrors are PP-canonical (under skills/ + agents/
in the power-pack); global activation (copying to ~/.claude) is an Owner-side
step (HR-001). skip-if-exists keeps it idempotent + non-clobbering.

  python tools/absorb_ecc_skills_agents.py --ecc <ECC root> --diff <diff.json> [--apply]
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]

ATTRIB = (
    "<!-- Absorbed from ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License "
    "(c) 2026 Affaan Mustafa. Curated selective absorption into "
    "claude-power-pack (2026-06-06). PP-canonical copy; activate globally by "
    "copying into ~/.claude/agents or ~/.claude/skills (Owner-side, HR-001). -->"
)

# Curated gem-set -- PP-aligned + non-redundant. Reasons inline.
ALLOW_AGENTS = [
    # Language reviewers -- pair with the rules taxonomy; PP only had a GENERIC
    # pp-code-reviewer. Scoped to PP's actual stack.
    "python-reviewer", "typescript-reviewer", "rust-reviewer",
    "java-reviewer", "go-reviewer", "cpp-reviewer",
    # Unique quality lenses PP lacked as dispatchable agents.
    "silent-failure-hunter", "type-design-analyzer", "comment-analyzer",
    # Meta: PP is itself a harness.
    "harness-optimizer",
]
ALLOW_SKILLS = [
    # ECC's distinctive agent-harness / eval engineering -- PP's core domain,
    # beyond PP's current skills.
    "agent-architecture-audit", "agent-eval", "eval-harness",
    "agent-harness-construction", "autonomous-loops", "agentic-os",
    "agent-introspection-debugging", "verification-loop",
    "recursive-decision-ledger", "intent-driven-development",
]


def _mirror_md(text: str) -> str:
    """Insert attribution after YAML frontmatter (preserve it at top)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            if nl != -1:
                return f"{text[:nl + 1]}{ATTRIB}\n\n{text[nl + 1:].lstrip(chr(10))}"
    return f"{ATTRIB}\n\n{text}"


def absorb(ecc_root: Path, diff_json: Path, apply: bool) -> dict:
    added_a, added_s, skipped_exist = [], [], []

    agents_dst = PP_ROOT / "agents"
    skills_dst = PP_ROOT / "skills"

    for name in ALLOW_AGENTS:
        src = ecc_root / "agents" / f"{name}.md"
        dst = agents_dst / f"{name}.md"
        if not src.is_file():
            continue
        if dst.exists():
            skipped_exist.append(f"agent/{name}")
            continue
        added_a.append(name)
        if apply:
            agents_dst.mkdir(parents=True, exist_ok=True)
            dst.write_text(_mirror_md(src.read_text(encoding="utf-8")),
                           encoding="utf-8")

    for name in ALLOW_SKILLS:
        src = ecc_root / "skills" / name
        dst = skills_dst / name
        if not (src / "SKILL.md").is_file():
            continue
        if dst.exists():
            skipped_exist.append(f"skill/{name}")
            continue
        added_s.append(name)
        if apply:
            shutil.copytree(src, dst)
            sk = dst / "SKILL.md"
            sk.write_text(_mirror_md(sk.read_text(encoding="utf-8")),
                          encoding="utf-8")

    # Skip-manifest: every net-new item NOT in the curated allowlist.
    d = json.loads(diff_json.read_text(encoding="utf-8"))
    skip_manifest = {
        "absorbed_agents": ALLOW_AGENTS,
        "absorbed_skills": ALLOW_SKILLS,
        "skipped_agents": [a for a in d["agents"]["new"]
                           if a["name"] not in ALLOW_AGENTS],
        "skipped_skills": [s for s in d["skills"]["new"]
                           if s["name"] not in ALLOW_SKILLS],
        "skip_reason": ("Not in the curated PP-aligned gem-set: out-of-scope "
                        "domain, redundant with the absorbed rules taxonomy "
                        "(*-patterns/*-testing/*-security), ECC self-management, "
                        "or overlaps an existing PP skill/agent."),
    }
    if apply:
        out = PP_ROOT / "vault" / "audits" / "ecc_skills_agents_skip_manifest.json"
        out.write_text(json.dumps(skip_manifest, indent=2), encoding="utf-8")

    return {"added_agents": added_a, "added_skills": added_s,
            "skipped_exist": skipped_exist,
            "skipped_count": len(skip_manifest["skipped_agents"])
            + len(skip_manifest["skipped_skills"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--ecc", required=True)
    ap.add_argument("--diff", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    r = absorb(Path(args.ecc), Path(args.diff), apply=args.apply)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] curated ECC skills+agents absorption")
    print(f"  agents absorbed ({len(r['added_agents'])}): {', '.join(r['added_agents'])}")
    print(f"  skills absorbed ({len(r['added_skills'])}): {', '.join(r['added_skills'])}")
    print(f"  skipped (already present): {len(r['skipped_exist'])}")
    print(f"  skipped (not curated, in manifest): {r['skipped_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
