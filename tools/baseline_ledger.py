#!/usr/bin/env python3
"""
Global Baseline Ledger — per-project, multi-axis engineering baseline tracker.

Axes (independent dimensions):
    - k_qa                 — K-QA vN prompt-protocol version (e.g. "v310.0", "v600.0")
    - k_router             — K-Router vN version (e.g. "v1.0", "v2.0")
    - engineering_baseline — internal engineering-rigor tier ("Baseline 41.0" → "v41.0")
    - highest_dna          — highest DNA-NNNN doctrine code referenced (stored as "DNA-1400")

Each project carries a value per axis (or null). global_max is computed per axis.
The Translator Hook matches the prompt's axis and elevates against THAT axis only.

Ledger path: ~/.claude/vault/global_baseline_ledger.json
Obsidian mirror: ~/.claude/knowledge_vault/governance/global_baseline_ledger.md

CLI:
    python baseline_ledger.py --show
    python baseline_ledger.py --max [--axis <axis>]
    python baseline_ledger.py --seed
    python baseline_ledger.py --register <project> --axis <axis> --baseline <v>
    python baseline_ledger.py --elevate  <project> --axis <axis> --baseline <v>
    python baseline_ledger.py --validate
    python baseline_ledger.py --sync-obsidian
"""

import argparse
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HOME = Path.home()
LEDGER_PATH = HOME / ".claude" / "vault" / "global_baseline_ledger.json"
OBSIDIAN_MIRROR = HOME / ".claude" / "knowledge_vault" / "governance" / "global_baseline_ledger.md"

AXES = ("k_qa", "k_router", "engineering_baseline", "highest_dna")
V_RE = re.compile(r"^v(\d+)(?:\.(\d+))?$", re.IGNORECASE)
DNA_RE = re.compile(r"^DNA-(\d+)$", re.IGNORECASE)

# Evidence-based seed (see conversation 2026-04-18 research findings)
SEED = {
    "kobiicraft": {
        "axes": {
            "k_qa": None,
            "k_router": "v2.0",
            "engineering_baseline": "v41.0",
            "highest_dna": "DNA-1600",
        },
        "evidence": {
            "k_router": "KobiiCraft Core Files/CLAUDE.md:1",
            "engineering_baseline": "KobiiCraft Core Files/CLAUDE.md:1",
            "highest_dna": "KobiiCraft Core Files/CLAUDE.md (DNA-1600 SCNS)",
        },
        "notes": "Paper 1.21.x plugin ecosystem",
    },
    "tua-x": {
        "axes": {
            "k_qa": None,
            "k_router": "v1.0",
            "engineering_baseline": "v43.0",
            "highest_dna": "DNA-3000",
        },
        "evidence": {
            "k_router": "TUAX_UGC_SYSTEM/CLAUDE.md:1",
            "engineering_baseline": "docs/baseline/SPRINT_LEDGER.md:26 (Sprint Ψ)",
            "highest_dna": "CLAUDE.md:20 Token Shield DNA-3000",
        },
        "notes": "UGC + content intelligence",
    },
    "kobiisports": {
        "axes": {
            "k_qa": "v310.0",
            "k_router": None,
            "engineering_baseline": None,
            "highest_dna": "DNA-15000",
        },
        "evidence": {
            "k_qa": "memory/sessions/session_2026-04-18_1140.md:11",
            "highest_dna": "CLAUDE.md:34 Token Shield DNA-15000",
        },
        "notes": "Wii homebrew (GRRLIB/libogc)",
    },
    "nexumops": {
        "axes": {"k_qa": None, "k_router": None, "engineering_baseline": None, "highest_dna": None},
        "evidence": {},
        "notes": "No baseline markers found — uses prompt-governance (GOV-Vxxx) only",
    },
    "moneymaker": {
        "axes": {"k_qa": None, "k_router": None, "engineering_baseline": None, "highest_dna": None},
        "evidence": {},
        "notes": "Skill project — no governance markers found",
    },
    "claude-power-pack": {
        "axes": {"k_qa": None, "k_router": None, "engineering_baseline": None, "highest_dna": None},
        "evidence": {},
        "notes": "Infrastructure host for the Ledger itself — no own baseline axis",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_version(v):
    """Normalize a version on ANY axis to a comparable tuple.
    Returns (major, minor) for vN/vN.M. Returns (n, 0) for DNA-n. (0, 0) on failure."""
    if not isinstance(v, str):
        return (0, 0)
    s = v.strip()
    m = V_RE.match(s)
    if m:
        return (int(m.group(1)), int(m.group(2) or 0))
    m = DNA_RE.match(s)
    if m:
        return (int(m.group(1)), 0)
    return (0, 0)


def version_gt(a, b):
    if a is None:
        return False
    if b is None:
        return True
    return parse_version(a) > parse_version(b)


def normalize_version(v, axis):
    """Validate a version string against axis rules. Returns normalized form or raises."""
    if v is None:
        return None
    s = v.strip()
    if axis == "highest_dna":
        if not DNA_RE.match(s):
            raise ValueError(f"axis 'highest_dna' requires format DNA-N, got: {s}")
        return s.upper()
    # All other axes use vN or vN.M (accept bare "41.0" by prefixing "v")
    if re.match(r"^\d+(?:\.\d+)?$", s):
        s = "v" + s
    if not V_RE.match(s):
        raise ValueError(f"axis '{axis}' requires format vN or vN.M, got: {v}")
    return s.lower().replace("v", "v")  # normalize case


def load_ledger():
    if not LEDGER_PATH.exists():
        return empty_ledger()
    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Auto-migrate v1.0 (single-axis) → v2.0 (multi-axis) if needed
    if data.get("version") == "1.0" and "projects" in data:
        data = migrate_v1_to_v2(data)
    return data


def empty_ledger():
    return {
        "version": "2.0",
        "schema": "multi-axis",
        "axes": list(AXES),
        "global_max": {a: None for a in AXES},
        "last_updated": now_iso(),
        "projects": {},
    }


def migrate_v1_to_v2(old):
    new = empty_ledger()
    new["last_updated"] = now_iso()
    for proj, entry in old.get("projects", {}).items():
        new["projects"][proj] = {
            "axes": {a: None for a in AXES},
            "evidence": {},
            "notes": f"[migrated from v1.0 single-axis value: {entry.get('current')}] {entry.get('notes','')}".strip(),
            "updated": entry.get("updated", now_iso()),
        }
    recompute_global_max(new)
    return new


def save_ledger(data):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def recompute_global_max(data):
    gmax = {a: None for a in AXES}
    for entry in data.get("projects", {}).values():
        for axis in AXES:
            v = (entry.get("axes") or {}).get(axis)
            if v and version_gt(v, gmax[axis]):
                gmax[axis] = v
    data["global_max"] = gmax
    data["last_updated"] = now_iso()


def ensure_project(data, project):
    if project not in data["projects"]:
        data["projects"][project] = {
            "axes": {a: None for a in AXES},
            "evidence": {},
            "notes": "",
            "updated": now_iso(),
        }
    else:
        # Ensure all axes present even on older entries
        for a in AXES:
            data["projects"][project].setdefault("axes", {}).setdefault(a, None)
        data["projects"][project].setdefault("evidence", {})


def cmd_show(_args):
    print(json.dumps(load_ledger(), indent=2, ensure_ascii=False))
    return 0


def cmd_max(args):
    data = load_ledger()
    if args.axis:
        if args.axis not in AXES:
            print(f"ERROR: unknown axis '{args.axis}'. Valid: {AXES}", file=sys.stderr)
            return 1
        print(data["global_max"].get(args.axis) or "null")
        return 0
    for a in AXES:
        print(f"{a}: {data['global_max'].get(a) or 'null'}")
    return 0


def cmd_seed(_args):
    data = load_ledger()
    if data["projects"]:
        print(f"NO-OP: ledger already has {len(data['projects'])} projects. Delete the file or use --register to add more.")
        return 0
    ts = now_iso()
    for proj, seed in SEED.items():
        data["projects"][proj] = {
            "axes": dict(seed["axes"]),
            "evidence": dict(seed["evidence"]),
            "notes": seed["notes"],
            "updated": ts,
        }
    recompute_global_max(data)
    save_ledger(data)
    sync_obsidian_mirror(data)
    print(f"OK: seeded {len(SEED)} projects with evidence-based axis values.")
    for a in AXES:
        print(f"  global_max[{a}] = {data['global_max'][a] or 'null'}")
    return 0


def _set_axis(data, project, axis, baseline, source, force):
    if axis not in AXES:
        raise ValueError(f"unknown axis '{axis}'. Valid: {AXES}")
    norm = normalize_version(baseline, axis)
    ensure_project(data, project)
    entry = data["projects"][project]
    current = entry["axes"].get(axis)
    if not force and current is not None and not version_gt(norm, current):
        return False, current
    entry["axes"][axis] = norm
    if source:
        entry["evidence"][axis] = source
    entry["updated"] = now_iso()
    recompute_global_max(data)
    return True, norm


def cmd_register(args):
    data = load_ledger()
    try:
        changed, result = _set_axis(data, args.project.strip().lower(), args.axis, args.baseline, args.source, force=True)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    save_ledger(data)
    sync_obsidian_mirror(data)
    print(f"OK: {args.project} [{args.axis}] = {result}  (global_max[{args.axis}]={data['global_max'][args.axis]})")
    return 0


def cmd_elevate(args):
    data = load_ledger()
    project = args.project.strip().lower()
    if project not in data["projects"]:
        print(f"ERROR: project '{project}' not registered. Use --register first.", file=sys.stderr)
        return 1
    try:
        changed, result = _set_axis(data, project, args.axis, args.baseline, args.source, force=False)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if not changed:
        print(f"NO-OP: {project} [{args.axis}] already at {result} >= {args.baseline}")
        return 0
    save_ledger(data)
    sync_obsidian_mirror(data)
    print(f"OK: elevated {project} [{args.axis}] → {result}  (global_max[{args.axis}]={data['global_max'][args.axis]})")
    return 0


def cmd_validate(_args):
    errors = []
    if not LEDGER_PATH.exists():
        print(f"ERROR: ledger missing at {LEDGER_PATH}", file=sys.stderr)
        return 1
    raw = LEDGER_PATH.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM detected (violates CD#10)")
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        errors.append(f"invalid JSON: {e}")
        for e in errors: print(f"FAIL: {e}", file=sys.stderr)
        return 1
    for key in ("version", "schema", "axes", "global_max", "projects"):
        if key not in data:
            errors.append(f"missing top-level key: {key}")
    for a in AXES:
        if a not in data.get("global_max", {}):
            errors.append(f"global_max missing axis: {a}")
    for proj, entry in data.get("projects", {}).items():
        if "axes" not in entry:
            errors.append(f"project '{proj}' missing 'axes'")
            continue
        for a in AXES:
            v = entry["axes"].get(a)
            if v is None:
                continue
            try:
                normalize_version(v, a)
            except ValueError as e:
                errors.append(f"project '{proj}' axis '{a}': {e}")
    if errors:
        for e in errors: print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"OK: ledger valid. {len(data['projects'])} projects, axes={AXES}")
    for a in AXES:
        print(f"  global_max[{a}] = {data['global_max'][a] or 'null'}")
    return 0


def sync_obsidian_mirror(data):
    OBSIDIAN_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("---")
    lines.append("title: Global Baseline Ledger (multi-axis)")
    lines.append("tags: [governance, flywheel, baseline]")
    lines.append("tier: governance")
    lines.append("see_also:")
    lines.append('  - "[[governance/dna-flywheel]]"')
    lines.append('  - "[[governance/supremacy-mode]]"')
    lines.append("---")
    lines.append("")
    lines.append("# Global Baseline Ledger (multi-axis)")
    lines.append("")
    lines.append(f"**Schema:** `{data.get('schema','multi-axis')}` v{data.get('version','2.0')}")
    lines.append(f"**Last updated:** {data.get('last_updated','')}")
    lines.append("")
    lines.append("## Global Max per Axis")
    lines.append("")
    lines.append("| Axis | Value | Meaning |")
    lines.append("|------|-------|---------|")
    descriptions = {
        "k_qa": "K-QA vN prompt-protocol version (Owner-typed prompts)",
        "k_router": "K-Router vN framework version",
        "engineering_baseline": "Internal engineering-rigor tier (Baseline N.0)",
        "highest_dna": "Highest DNA-NNNN doctrine code referenced",
    }
    for a in AXES:
        v = data["global_max"].get(a) or "—"
        lines.append(f"| `{a}` | `{v}` | {descriptions[a]} |")
    lines.append("")
    lines.append("## Per-Project Axis Values")
    lines.append("")
    lines.append("| Project | k_qa | k_router | engineering_baseline | highest_dna | Notes |")
    lines.append("|---------|------|----------|----------------------|-------------|-------|")
    for proj in sorted(data.get("projects", {}).keys()):
        e = data["projects"][proj]
        ax = e.get("axes", {})
        cell = lambda v: f"`{v}`" if v else "—"
        notes = (e.get("notes") or "").replace("|", "\\|")
        lines.append(f"| {proj} | {cell(ax.get('k_qa'))} | {cell(ax.get('k_router'))} | {cell(ax.get('engineering_baseline'))} | {cell(ax.get('highest_dna'))} | {notes} |")
    lines.append("")
    lines.append("## Evidence Paths")
    lines.append("")
    for proj in sorted(data.get("projects", {}).keys()):
        e = data["projects"][proj]
        ev = e.get("evidence", {})
        if not ev:
            continue
        lines.append(f"### {proj}")
        for axis, path in ev.items():
            lines.append(f"- `{axis}` ← `{path}`")
        lines.append("")
    lines.append("## Flywheel")
    lines.append("")
    lines.append("The Translator Hook (`~/.claude/hooks/baseline-translator.js`) detects the axis in each UserPromptSubmit and elevates against THAT axis only. Cross-axis comparisons are prevented — K-QA v310.0 does NOT beat Engineering Baseline v43.0; they live on independent dimensions.")
    lines.append("")
    OBSIDIAN_MIRROR.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def cmd_sync_obsidian(_args):
    data = load_ledger()
    sync_obsidian_mirror(data)
    print(f"OK: synced → {OBSIDIAN_MIRROR}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Global Baseline Ledger (multi-axis) CLI")
    p.add_argument("--show", action="store_true")
    p.add_argument("--max", action="store_true")
    p.add_argument("--seed", action="store_true")
    p.add_argument("--validate", action="store_true")
    p.add_argument("--sync-obsidian", action="store_true", dest="sync_obsidian")
    p.add_argument("--register", metavar="PROJECT", default=None)
    p.add_argument("--elevate", metavar="PROJECT", default=None)
    p.add_argument("--axis", default=None, choices=list(AXES) + [None])
    p.add_argument("--baseline", default=None)
    p.add_argument("--source", default=None)

    args = p.parse_args()
    if args.show: return cmd_show(args)
    if args.max: return cmd_max(args)
    if args.seed: return cmd_seed(args)
    if args.validate: return cmd_validate(args)
    if args.sync_obsidian: return cmd_sync_obsidian(args)
    if args.register:
        if not args.axis or not args.baseline:
            print("ERROR: --register requires --axis AND --baseline", file=sys.stderr); return 1
        ns = argparse.Namespace(project=args.register, axis=args.axis, baseline=args.baseline, source=args.source)
        return cmd_register(ns)
    if args.elevate:
        if not args.axis or not args.baseline:
            print("ERROR: --elevate requires --axis AND --baseline", file=sys.stderr); return 1
        ns = argparse.Namespace(project=args.elevate, axis=args.axis, baseline=args.baseline, source=args.source)
        return cmd_elevate(ns)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
