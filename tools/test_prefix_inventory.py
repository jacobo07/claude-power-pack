#!/usr/bin/env python3
"""V-PREFIXINV gates for modules/token-optimizer/prefix_inventory.py."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "prefix_inventory", HERE.parent / "modules" / "token-optimizer" / "prefix_inventory.py")
PI = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PI)

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        home = root / ".claude"                       # home_claude is itself an ancestor of cwd
        cwd = home / "skills" / "proj"
        (home / "rules").mkdir(parents=True)
        (home / "skills" / "s1").mkdir(parents=True)
        (home / "agents").mkdir()
        cwd.mkdir(parents=True, exist_ok=True)
        (home / "CLAUDE.md").write_text("G" * 1000, encoding="utf-8")
        (cwd / "CLAUDE.md").write_text("P" * 500, encoding="utf-8")
        (home / "rules" / "orca.md").write_text("Orca X Orca X rule " + "x" * 200, encoding="utf-8")
        (home / "rules" / "scoped.md").write_text(
            "---\npaths:\n  - src/**/*.ts\n---\n" + "y" * 5000, encoding="utf-8")
        (home / "skills" / "s1" / "SKILL.md").write_text(
            "---\nname: s1\ndescription: does a thing\n  across lines\n---\n" + "BODY" * 5000,
            encoding="utf-8")
        (home / "agents" / "a1.md").write_text("---\nname: a1\ndescription: agent\n---\nbody",
                                               encoding="utf-8")
        mem = root / "MEMORY.md"
        mem.write_text("m" * 300, encoding="utf-8")

        # stop_at=root: an unbounded walk from a temp dir reaches the real ~/CLAUDE.md.
        inv = PI.inventory(cwd, home_claude=home, memory_file=mem, stop_at=root)
        leak = PI.claude_md_chain(cwd, home_claude=home)
        check("V-PREFIXINV-UNBOUNDED-WALKS-TO-ROOT",
              len(leak) >= len(PI.claude_md_chain(cwd, home_claude=home, stop_at=root)),
              f"unbounded chain={len(leak)} files (production walks every ancestor)")
        k = inv["by_kind"]
        check("V-PREFIXINV-CHAIN-DEDUPE", k["claude_md"]["files"] == 2
              and k["claude_md"]["bytes"] == 1500,
              f"global counted once though it is also an ancestor: {k['claude_md']}")
        check("V-PREFIXINV-SCOPED-APART", k["rule_scoped"]["files"] == 1 and k["rule"]["files"] == 1,
              f"rule={k['rule']['files']} rule_scoped={k['rule_scoped']['files']}")
        check("V-PREFIXINV-UNCONDITIONAL-EXCLUDES-SCOPED",
              inv["unconditional_bytes"] == sum(v["bytes"] for kk, v in k.items() if kk != "rule_scoped")
              and inv["unconditional_bytes"] < k["rule_scoped"]["bytes"] + 3000,
              f"unconditional={inv['unconditional_bytes']} scoped={k['rule_scoped']['bytes']}")
        listed = "s1 does a thing across lines"
        check("V-PREFIXINV-LISTING-NOT-BODY",
              k["skill_listing"]["bytes"] == len(listed.encode()),
              f"skill listing bytes={k['skill_listing']['bytes']} (body is 20000)")
        orca = next(r for r in inv["rows"] if r["path"].endswith("orca.md"))
        check("V-PREFIXINV-MENTIONS", orca["mentions"] == {"Orca X": 2},
              f"{orca['mentions']}")
        check("V-PREFIXINV-MEMORY", k["memory_index"]["bytes"] == 300, f"{k['memory_index']}")
        check("V-PREFIXINV-APERTURE-DECLARED",
              "tool schemas incl. MCP" in inv["not_counted"] and inv["tokens"].startswith("ESTIMATE"),
              f"not_counted={inv['not_counted']}")

        bare = PI.inventory(root / "nowhere", home_claude=root / "absent", stop_at=root)
        check("V-PREFIXINV-MISSING-DIRS", bare["by_kind"] == {} and bare["unconditional_bytes"] == 0,
              "absent dirs -> empty inventory, no crash")

    print(f"PREFIXINV_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
