"""V-AGENT-FM: every agent definition's frontmatter must parse as YAML.

An agent whose frontmatter fails to parse is not reported anywhere: the harness
just leaves it out of the dispatchable list. On 2026-11-17 seven agents were
invisible this way (cdio-reviewer, cdio-core, steve-jobs, woz and the three
graphify agents). The usual cause is an unquoted ": " inside a one-line
description, e.g. "the verdict gate (PR-...): APPROVE requires", which YAML reads
as a nested mapping. The CDIO hook told every UI session to run cdio-reviewer,
and that agent could never be launched.

Run: python tools/test_agent_frontmatter.py   (exit 0 = every agent loads)
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

PP_ROOT = Path(__file__).resolve().parent.parent
AGENT_ROOTS = ("agents", "vault/agents", "vendor/rtk/agents")
REQUIRED_KEYS = ("name", "description")


def frontmatter_error(path: Path) -> str | None:
    """Return why this agent file would not load, or None if it would."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "no frontmatter block"
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        return "frontmatter is never closed"
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        return f"YAML does not parse: {str(exc).splitlines()[0]}"
    if not isinstance(data, dict):
        return "frontmatter is not a mapping"
    missing = [k for k in REQUIRED_KEYS if not data.get(k)]
    if missing:
        return f"missing {', '.join(missing)}"
    if data["name"] != path.stem:
        return f"name {data['name']!r} does not match the file name"
    return None


def agent_files() -> list[Path]:
    files: list[Path] = []
    for rel in AGENT_ROOTS:
        root = PP_ROOT / rel
        if root.is_dir():
            files.extend(p for p in sorted(root.glob("*.md"))
                         if p.name.upper() not in ("README.MD", "INDEX.MD"))
    return files


def self_test() -> bool:
    """The check must be able to fail: the exact shape that hid cdio-reviewer."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "x.md"
        bad.write_text("---\nname: x\ndescription: gate (HR-1): APPROVE needs 80\n---\n",
                       encoding="utf-8")
        good = Path(tmp) / "y.md"
        good.write_text('---\nname: y\ndescription: "gate (HR-1): APPROVE needs 80"\n---\n',
                        encoding="utf-8")
        return frontmatter_error(bad) is not None and frontmatter_error(good) is None


def main() -> int:
    passes = fails = 0
    if self_test():
        passes += 1
        print("  [PASS] V-AGENT-FM-SELFTEST: unquoted ': ' is caught, quoted form loads")
    else:
        fails += 1
        print("  [FAIL] V-AGENT-FM-SELFTEST: the check cannot tell a broken agent from a good one")
    files = agent_files()
    for path in files:
        err = frontmatter_error(path)
        if err:
            fails += 1
            print(f"  [FAIL] V-AGENT-FM {path.relative_to(PP_ROOT).as_posix()}: {err}")
        else:
            passes += 1
    print(f"V-AGENT-FM checked {len(files)} agent files")
    print(f"AGENT_FM_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 and files else 1


if __name__ == "__main__":
    raise SystemExit(main())
