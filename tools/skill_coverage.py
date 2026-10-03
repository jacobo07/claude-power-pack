#!/usr/bin/env python
"""skill_coverage.py -- coverage class + criticality class for every installed skill (pillar D, D-01).

The population is DISCOVERED, never listed:
  repo plane  every skills/*/SKILL.md directory of this checkout
  live plane  the directories of one host's ~/.claude/skills that hold a SKILL.md (the repo plane's definition),
              recorded on that host by --measure-live into vault/programs/skill-capability/evidence/D-live-<host>.json;
              a directory without SKILL.md is reported in `non_skill_dirs`, never classified
Planes are reported separately; no figure sums across them, and one live plane's evidence never applies to another.

Coverage class (derived from code at gate time, never typed per skill):
  card                a PreToolUse hook registered in a `*-chain` of hooks/hook-dispatcher.js CHAIN_MAP whose source
                      emits a deny (`permissionDecision` and `deny`) and names the skill as a backticked token followed
                      by the word skill
  opportunity_detector  card AND a tools/*.py adapter that assigns KIND = "capability_opportunity" and
                      CAPABILITY = "<skill>"
  none                otherwise
The class is a property of THIS checkout's dispatcher. Whether a host runs that dispatcher is the pillar A live-sync
item, not measured here. vault/skills_heat_map.json membership is reported as a column and is never a class (a keyword
suggestion is neither a need-time opportunity judgement nor a deny card).

Criticality class (CRITICALITY_RULE below) from plane-labelled evidence, each item carrying file:line.

This module never assigns a class by skill name. It reads only repo files on its default paths; only --measure-live
reads the current user's home directory.

    python tools/skill_coverage.py --json                       # repo plane rows
    python tools/skill_coverage.py --measure-live --host gex44  # record the live plane as raw facts
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

DISPATCHER_REL = "hooks/hook-dispatcher.js"
HEAT_REL = "vault/skills_heat_map.json"
HARD_RULES_REL = "vault/hard_rules/HARD_RULES.md"
CLAUDE_MD_REL = "CLAUDE.md"
EVIDENCE_DIR_REL = "vault/programs/skill-capability/evidence"
LIVE_SCHEMA = "skill-coverage-live/1"
COVERAGE_CLASSES = ("opportunity_detector", "card", "none")
CRIT_CLASSES = ("high", "medium", "low")
HOST_RE = re.compile(r"^[a-z0-9-]+$")

CRITICALITY_RULE = (
    "high = a moved-out global rule stub (a top-level rules/*.md that says \"moved to a skill\" and names the skill, "
    "live recording only) or a HARD RULES source (a `## ... HARD RULES ...` section of a CLAUDE.md, or anywhere in "
    "vault/hard_rules/HARD_RULES.md) names it; medium = a `## ... Activation Criteria ...` section of a CLAUDE.md "
    "names it and nothing high does; low = neither. A token is the skill name in backticks, or skills/<name> followed "
    "by a non-name character. The repo plane uses repo evidence only; a live plane uses repo evidence plus its own "
    "recorded evidence."
)

CHAIN_KEY = re.compile(r"""^\s*['"]([A-Za-z0-9_-]+-chain)['"]\s*:\s*\[""")
SCRIPT = re.compile(r"""\bscript:\s*['"]\.\./skills/claude-power-pack/([^'"]+)['"]""")
CARD_TOKEN = re.compile(r"`([A-Za-z0-9_-]+)`\s+skill\b")
SKILL_TOKENS = (re.compile(r"`([A-Za-z0-9_-]+)`"), re.compile(r"skills/([A-Za-z0-9_-]+)"))
KIND_LINE = re.compile(r"""^KIND\s*=\s*['"]capability_opportunity['"]""", re.M)
CAP_LINE = re.compile(r"""^CAPABILITY\s*=\s*['"]([^'"]+)['"]""", re.M)


def lf(text: str) -> str:
    """CRLF, then lone CR, turned into LF before any regex or line split.

    The laptop clone runs core.autocrlf=true and none of the parsed paths (dispatcher, hooks, tools/*.py,
    CLAUDE.md, HARD_RULES.md, rules stubs, recordings) is `-text` in .gitattributes, so each can arrive CRLF there.
    An LF-only line parser would keep a `\\r` on every chain key and read the dispatcher as having no chains."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_lf(path: Path) -> str:
    return lf(Path(path).read_bytes().decode("utf-8", errors="replace"))


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ------------------------------------------------------------------ population


def repo_population(repo: Path = REPO) -> list[str]:
    sk = Path(repo) / "skills"
    if not sk.is_dir():
        return []
    return sorted(p.name for p in sk.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


# ------------------------------------------------------------------ registrations


def registered_hooks(dispatcher_text: str) -> dict:
    """{rel: [{chain, line}]} for every `script: '../skills/claude-power-pack/<rel>'` entry of CHAIN_MAP."""
    out: dict = {}
    chain = None
    inside = False
    for n, line in enumerate(lf(dispatcher_text).split("\n"), 1):
        if not inside:
            if line.startswith("const CHAIN_MAP = {"):
                inside = True
            continue
        if line.startswith("};"):
            break
        if line.lstrip().startswith("//"):
            continue
        m = CHAIN_KEY.match(line)
        if m:
            chain = m.group(1)
            continue
        m = SCRIPT.search(line)
        if m and chain:
            out.setdefault(m.group(1), []).append({"chain": chain, "line": n})
    return out


def discover_cards(repo: Path = REPO, dispatcher_text: str | None = None, *, hook_texts: dict | None = None,
                   read_disk: bool = True) -> list:
    """Card sources: registered PreToolUse hooks whose text emits a deny and names `<skill>` skill.

    hook_texts (rel -> text) overlays disk reads, for drills. read_disk=False uses the overlay alone (a caller that
    read the dispatcher and hooks from committed blobs, so discovery and hashing share one plane). Returns dicts
    sorted by (skill, hook)."""
    repo = Path(repo)
    if dispatcher_text is None:
        dispatcher_text = read_lf(repo / DISPATCHER_REL)
    overlay = {k: lf(v) for k, v in (hook_texts or {}).items()}
    cards = []
    for rel, regs in registered_hooks(dispatcher_text).items():
        pre = [r for r in regs if r["chain"].startswith("PreToolUse-")]
        if not pre:
            continue
        if rel in overlay:
            text = overlay[rel]
        elif read_disk and (repo / rel).is_file():
            text = read_lf(repo / rel)
        else:
            continue
        if "permissionDecision" not in text or "deny" not in text:
            continue
        for m in CARD_TOKEN.finditer(text):
            for r in pre:
                cards.append({"skill": m.group(1), "hook": rel, "chain": r["chain"],
                              "dispatcher_line": r["line"], "source_line": line_of(text, m.start())})
    return sorted(cards, key=lambda c: (c["skill"], c["hook"], c["chain"], c["source_line"]))


def opportunity_adapters(repo: Path = REPO, adapter_texts: dict | None = None) -> dict:
    """{skill: (file, line)} for tools/*.py declaring KIND = capability_opportunity and CAPABILITY = "<skill>"."""
    repo = Path(repo)
    texts = {}
    for p in sorted((repo / "tools").glob("*.py")):
        texts[f"tools/{p.name}"] = None
    for k, v in (adapter_texts or {}).items():
        texts[k] = lf(v)
    out: dict = {}
    for rel, text in texts.items():
        if text is None:
            text = read_lf(repo / rel)
        if not KIND_LINE.search(text):
            continue
        m = CAP_LINE.search(text)
        if m:
            out.setdefault(m.group(1), (rel, line_of(text, m.start())))
    return out


def coverage(skill: str, cards: list, adapters: dict) -> tuple:
    ev = [f"{c['hook']}:{c['source_line']} ({c['chain']} @ {DISPATCHER_REL}:{c['dispatcher_line']})"
          for c in cards if c["skill"] == skill]
    if ev and skill in adapters:
        f, ln = adapters[skill]
        return "opportunity_detector", ev + [f"{f}:{ln}"]
    return ("card", ev) if ev else ("none", [])


def heat_map_names(repo: Path = REPO):
    """(names set, generated_iso) of vault/skills_heat_map.json, or None when absent or unreadable."""
    try:
        d = json.loads(read_lf(Path(repo) / HEAT_REL))
        return set(d["skills"]), str(d.get("generated_iso", ""))
    except (OSError, ValueError, KeyError, TypeError):
        return None


# ------------------------------------------------------------------ criticality


def tokens_in(line: str) -> set:
    out = set()
    for rx in SKILL_TOKENS:
        out.update(rx.findall(line))
    return out


def section_hits(text: str, file: str, plane: str, names, whole: str | None = None) -> list:
    """Evidence items for skills named in a `## ...` section classed by its heading.

    whole = "hard_rule" treats the entire text as one hard_rule section (HARD_RULES.md)."""
    names = set(names)
    items, kind = [], whole
    for n, line in enumerate(lf(text).split("\n"), 1):
        if whole is None and line.startswith("## "):
            low = line.lower()
            kind = "hard_rule" if "hard rules" in low else "activation" if "activation criteria" in low else None
            continue
        if kind is None:
            continue
        for s in sorted(tokens_in(line) & names):
            items.append({"kind": kind, "plane": plane, "file": file, "line": n, "skill": s})
    return items


def stub_hits(text: str, file: str, plane: str, names) -> list:
    text = lf(text)
    if "moved to a skill" not in text:
        return []
    names = set(names)
    items = []
    for n, line in enumerate(text.split("\n"), 1):
        for s in sorted(set(CARD_TOKEN.findall(line)) & names):
            items.append({"kind": "rule_stub", "plane": plane, "file": file, "line": n, "skill": s})
    return items


def repo_evidence(repo: Path, names, claude_md: str | None = None, hard_rules: str | None = None) -> list:
    repo = Path(repo)
    out = []
    if claude_md is None and (repo / CLAUDE_MD_REL).is_file():
        claude_md = read_lf(repo / CLAUDE_MD_REL)
    if hard_rules is None and (repo / HARD_RULES_REL).is_file():
        hard_rules = read_lf(repo / HARD_RULES_REL)
    if claude_md is not None:
        out += section_hits(claude_md, CLAUDE_MD_REL, "repo", names)
    if hard_rules is not None:
        out += section_hits(hard_rules, HARD_RULES_REL, "repo", names, whole="hard_rule")
    return out


def criticality(name: str, evidence: list) -> tuple:
    mine = [e for e in evidence if e["skill"] == name]
    kinds = {e["kind"] for e in mine}
    cls = "high" if kinds & {"rule_stub", "hard_rule"} else "medium" if "activation" in kinds else "low"
    return cls, [f"{e['kind']}@{e['plane']} {e['file']}:{e['line']}" for e in mine]


def classify_plane(names, plane: str, cards: list, adapters: dict, crit_evidence: list, heat) -> list:
    rows = []
    for name in sorted(names):
        cov, cov_ev = coverage(name, cards, adapters)
        crit, crit_ev = criticality(name, crit_evidence)
        hm = "UNMEASURED" if heat is None else ("yes" if name in heat[0] else "no")
        rows.append({"plane": plane, "skill": name, "coverage": cov, "coverage_evidence": cov_ev,
                     "criticality": crit, "criticality_evidence": crit_ev, "heat_map": hm})
    return rows


def repo_rows(repo: Path = REPO) -> list:
    names = repo_population(repo)
    return classify_plane(names, "repo", discover_cards(repo), opportunity_adapters(repo),
                          repo_evidence(repo, names), heat_map_names(repo))


# ------------------------------------------------------------------ live recording


def measure_live(host: str, home: Path | None = None) -> dict:
    """Raw facts of the current user's ~/.claude, labelled with the host. No class is recorded."""
    import platform
    import skill_invocations as si
    home = Path(home) if home else Path.home() / ".claude"
    sk = home / "skills"
    entries = sorted(sk.iterdir()) if sk.is_dir() else []
    installed = si.installed_names(home)
    # The repo plane's definition of a skill on both planes (review WR-08): a directory holding SKILL.md. A
    # directory without one (a container such as bmad/, a parked SKILL.md.disabled, a vault) is reported by name in
    # `non_skill_dirs` and never classified, so it cannot inflate the none/low totals or meet the population floor.
    all_dirs = {p.name for p in entries if p.is_dir()}
    dirs = sorted(p.name for p in entries if p.is_dir() and (p / "SKILL.md").is_file() and p.name in installed)
    non_skill = sorted(n for n in all_dirs if n not in dirs)
    counts = {
        "entries": len(entries),
        "skill_dirs": len(dirs),
        "dangling_symlinks": sum(1 for p in entries if p.is_symlink() and not p.exists()),
        "dirs_without_skill_md": len(non_skill),
        "commands_excluded": len(installed - all_dirs),
    }
    ev = []
    rules = home / "rules"
    if rules.is_dir():
        for p in sorted(rules.glob("*.md")):
            ev += stub_hits(read_lf(p), f"~/.claude/rules/{p.name}", host, dirs)
    cm = home / "CLAUDE.md"
    if cm.is_file():
        ev += section_hits(read_lf(cm), "~/.claude/CLAUDE.md", host, dirs)
    return {
        "schema": LIVE_SCHEMA, "host": host, "node": platform.node(),
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": f"python3 tools/skill_coverage.py --measure-live --host {host}",
        "skills": dirs, "counts": counts, "evidence": ev, "non_skill_dirs": non_skill,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="print the repo-plane rows as JSON")
    ap.add_argument("--measure-live", action="store_true", help="record this host's live plane (reads the home dir)")
    ap.add_argument("--host", help="label for --measure-live ([a-z0-9-]+)")
    args = ap.parse_args(argv)
    if args.measure_live:
        if not args.host or not HOST_RE.match(args.host):
            print("--measure-live requires --host matching ^[a-z0-9-]+$")
            return 2
        rec = measure_live(args.host)
        out = REPO / EVIDENCE_DIR_REL / f"D-live-{args.host}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, indent=1, sort_keys=True) + "\n")
        print(f"wrote {out.relative_to(REPO).as_posix()}: {rec['counts']}, {len(rec['evidence'])} evidence items")
        return 0
    rows = repo_rows()
    if args.json:
        print(json.dumps(rows, indent=1, sort_keys=True))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
