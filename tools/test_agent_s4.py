#!/usr/bin/env python3
"""V-S4-* gates: the 9 dormant repo agents migrated to AgentSpecs (virtualization S4).

Facts behind the split recipes: vault/specs/agent-capability-virtualization.RESUMPTION.md.
What each gate would catch if it broke:
  LOAD     a spec that no longer loads, or whose pages no longer reassemble the source file
  CLASS    a spec whose carrier class drops a tool the source agent had (capability loss),
           or a carrier whose frontmatter grants more than its class
  PRIM     a Prompt Defense copy that drifted back into an agent's own page
  DEEP     paging on the wrong blocks: only java data-layer, java workflow and ts react are deep
  ROUTE    a language request reaching the wrong reviewer
  HO       harness-optimizer applying instead of proposing (its surface is protected)
  CONTROL  the routing negatives are not vacuous: a bare "go" trigger turns one of them red
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime import agent_resolver as R  # noqa: E402

EXPECTED = {
    "comment-analyzer": "investigator", "type-design-analyzer": "investigator",
    "cpp-reviewer": "verifier", "go-reviewer": "verifier", "java-reviewer": "verifier",
    "python-reviewer": "verifier", "rust-reviewer": "verifier", "typescript-reviewer": "verifier",
    # Owner option b, 2026-10-01: its whole surface is protected (.claude/), so a headless
    # writer can never apply anything; it proposes a patch and the parent applies it.
    "harness-optimizer": "verifier",
}
# A source tool the class drops is a capability loss unless it is REPLACED by a named
# output contract that hands the effect to the parent. Anything else dropped is a FAIL.
REPLACED = {"harness-optimizer": {"Edit": "patch-proposal-v1"}}
DEEP = {("java-reviewer", "data-layer"), ("java-reviewer", "workflow-state-machine"),
        ("typescript-reviewer", "react-nextjs")}
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def fm_tools(text: str) -> set[str]:
    m = re.search(r"(?m)^tools:\s*(.+)$", text)
    return set(re.findall(r"[A-Za-z]+", m.group(1))) if m else set()


def ids(res, key="candidates"):
    return [c["id"] for c in res[key]]


def main() -> int:
    # --- LOAD: every spec loads and its pages reassemble the source byte for byte.
    specs = {}
    for sid, cls in EXPECTED.items():
        try:
            s = A.load(sid)
        except A.AgentSpecError as e:
            check(f"V-S4-LOAD-{sid}", False, f"{e.code}")
            continue
        specs[sid] = s
        src = (ROOT / "agents" / f"{sid}.md").read_text(encoding="utf-8")
        check(f"V-S4-LOAD-{sid}", s.permission_class == cls and s.project() == src,
              f"class={s.permission_class} round-trip={s.project() == src} spec={s.spec_hash()}")
    check("V-S4-LOAD-COUNT", len(specs) == 9, f"{len(specs)}/9 loaded")

    # --- CLASS: the class keeps every tool the source agent had; the carrier grants exactly the class.
    for sid, s in specs.items():
        src_tools = fm_tools((ROOT / "agents" / f"{sid}.md").read_text(encoding="utf-8"))
        cls_tools = set(A.CLASS_TOOLS[s.permission_class])
        rep = REPLACED.get(sid, {})
        dropped = src_tools - cls_tools
        covered = all(t in rep and s.output_contract == rep[t] for t in dropped)
        check(f"V-S4-CLASS-{sid}", bool(src_tools) and covered,
              f"source={sorted(src_tools)} class+={sorted(cls_tools - src_tools)} "
              f"replaced={ {t: rep.get(t) for t in sorted(dropped)} }")
    for cls in A.CLASS_ORDER:          # every carrier, used by a spec here or not
        carrier = ROOT / "agents" / "carriers" / f"{A.carrier_name(cls)}.md"
        got = fm_tools(carrier.read_text(encoding="utf-8")) if carrier.is_file() else set()
        check(f"V-S4-CARRIER-{cls}", got == set(A.CLASS_TOOLS[cls]), f"{carrier.name} tools={sorted(got)}")

    # --- PRIM: the Prompt Defense Baseline is the shared primitive in all 9, never an own page.
    prim = [sid for sid, s in specs.items()
            if any(p.get("primitive") == "prompt-defense-baseline" for p in s.pages)]
    own = [sid for sid, s in specs.items() for p in s.pages
           if not p.get("primitive") and "## Prompt Defense Baseline" in s.page_text(p)]
    check("V-S4-PRIM", len(prim) == 9 and not own, f"primitive={len(prim)}/9 own_copies={own}")

    # --- DEEP: exactly the three planned on-demand pages; virtual names them, monolithic inlines them.
    got_deep = {(sid, re.sub(r"^pages/\d+-|\.md$", "", p["path"]))
                for sid, s in specs.items() for p in s.pages if p["load"] == "on_demand"}
    check("V-S4-DEEP-SET", got_deep == DEEP, f"{sorted(got_deep)}")
    for sid in ("java-reviewer", "typescript-reviewer"):
        s = specs.get(sid)
        if not s:
            continue
        deep = [p for p in s.pages if p["load"] == "on_demand"]
        v = s.compile("review the diff", "virtual", state_version="none")
        mono = s.compile("review the diff", "monolithic", state_version="none")
        first_lines = [s.page_text(p).splitlines()[0] for p in deep]
        check(f"V-S4-DEEP-{sid}",
              all(s.page_path(p).as_posix() in v for p in deep)
              and not any(fl in v for fl in first_lines) and all(fl in mono for fl in first_lines),
              f"{len(deep)} deep page(s): named in virtual, absent from it, present in monolithic")

    # --- ROUTE: over the real catalog, no cache.
    def q(task, **kw):
        return R.resolve(task, use_cache=False, **kw)

    positive = [
        ("review this Go handler for goroutine leaks", "go-reviewer", "rust-reviewer"),
        ("review this golang service", "go-reviewer", "rust-reviewer"),
        ("review this Rust crate for borrow checker issues", "rust-reviewer", "go-reviewer"),
        ("review this python code for missing type hints", "python-reviewer", None),
        ("review the Spring Boot JPA repository layer", "java-reviewer", "typescript-reviewer"),
        ("review this typescript react component", "typescript-reviewer", "java-reviewer"),
        ("review the cpp smart pointer ownership in this class", "cpp-reviewer", None),
        ("check these code comments for comment rot", "comment-analyzer", None),
        ("review the type design and type invariants of this model", "type-design-analyzer", None),
    ]
    for task, want, never in positive:
        r = q(task)
        c = ids(r)
        check(f"V-S4-ROUTE-{want}", c[:1] == [want] and (never is None or never not in c),
              f"{task!r} -> {c}")

    negatives = [
        ("go ahead and summarise the release notes", "go-reviewer"),
        ("review this javascript code", "java-reviewer"),
        ("let's go through the deploy checklist", "go-reviewer"),
    ]
    for task, absent in negatives:
        c = ids(q(task))
        check(f"V-S4-NEG-{absent}", absent not in c, f"{task!r} -> {c}")

    # harness-optimizer: a verifier that proposes, never applies (Owner option b).
    hw = "optimize the agent harness configuration for reliability"
    r_default = q(hw)
    check("V-S4-HO-ROUTES-AT-VERIFIER", ids(r_default)[:1] == ["harness-optimizer"],
          f"default grant -> {ids(r_default)}")
    hs = specs.get("harness-optimizer")
    if hs:
        img = hs.compile("propose a harness fix", "virtual", state_version="none")
        check("V-S4-HO-PATCH-CONTRACT",
              hs.output_contract == "patch-proposal-v1" and not hs.contract.write_surfaces
              and "Output contract: patch proposal v1" in img and "You cannot edit files" in img
              and "{spec}" not in img and f"harness-optimizer@{hs.contract.version}" in img,
              f"contract={hs.output_contract} write_surfaces={hs.contract.write_surfaces}")
        # The carrier it lands on really has no editor: the contract is not a request, it is the surface.
        check("V-S4-HO-NO-EDITOR", not {"Edit", "Write"} & set(A.CLASS_TOOLS[hs.permission_class]),
              f"{A.carrier_name(hs.permission_class)} tools={A.CLASS_TOOLS[hs.permission_class]}")
        # HR-APA-009 still binds any future writer: write surfaces without a kill switch are refused.
        bad = json.loads(json.dumps(hs.raw))
        bad["agent"]["permission_class"] = "writer"
        bad["contract"].update(write_surfaces=["docs/"], rollback="git checkout", kill_switch="")
        try:
            A.AgentSpec(bad, hs.dir)
            refused = False
        except A.AgentSpecError as e:
            refused = e.code == "INVALID_CONTRACT"
        check("V-S4-WRITER-HR-APA-009", refused, "writer contract without kill_switch is refused")
        # And the opposite authority mismatch: write surfaces on a verifier.
        bad["agent"]["permission_class"] = "verifier"
        bad["contract"]["kill_switch"] = "x"
        try:
            A.AgentSpec(bad, hs.dir)
            refused = False
        except A.AgentSpecError as e:
            refused = e.code == "CLASS_BELOW_WRITE_SURFACE"
        check("V-S4-VERIFIER-NO-WRITE-SURFACE", refused, "write_surfaces on a verifier are refused")

    # --- CONTROL: a bare "go" trigger must turn the go-ahead negative red, or that gate is vacuous.
    with tempfile.TemporaryDirectory() as t:
        cat = Path(t)
        for sid in EXPECTED:
            shutil.copytree(A.SPECS_DIR / sid, cat / sid)
        f = cat / "go-reviewer" / "spec.json"
        raw = json.loads(f.read_text(encoding="utf-8"))
        raw["contract"]["triggers"].append("go")
        f.write_text(json.dumps(raw), encoding="utf-8")
        c = ids(R.resolve("go ahead and summarise the release notes", specs_dir=cat, use_cache=False))
        check("V-S4-CONTROL-BARE-GO", "go-reviewer" in c, f"mutant catalog -> {c}")

    total = passes + fails
    print(f"AGENT_S4_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
