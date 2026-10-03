#!/usr/bin/env python3
"""V-SPEC-* gates for modules/capability_runtime/agent_spec.py (virtualization S1).

Each failure path asserts its TYPED code, so a loader that returned an empty
spec, or raised a generic error, fails here. Every gate has a pole the opposite
implementation gets wrong.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_spec as A  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def code_of(fn):
    try:
        fn()
        return "NO_ERROR"
    except A.AgentSpecError as e:
        return e.code


def main() -> int:
    spec = A.load("oneshot-architect-auditor")
    src = (ROOT / "agents" / "oneshot-architect-auditor.md").read_text(encoding="utf-8")
    check("V-SPEC-RECONSTRUCT", spec.project() == src, "projection == monolithic source, byte for byte")

    virtual = spec.compile("Audit the plan.", "virtual")
    mono = spec.compile("Audit the plan.", "monolithic")
    crip = spec.compile("Audit the plan.", "crippled")
    deep = [p for p in spec.pages if p["load"] == "on_demand"]
    deep_paths = [(spec.dir / p["path"]).as_posix() for p in deep]
    check("V-SPEC-VIRTUAL-LISTS-DEEP", all(d in virtual for d in deep_paths) and len(deep) >= 1,
          f"{len(deep)} deep pages listed by path")
    check("V-SPEC-VIRTUAL-OMITS-DEEP-TEXT",
          all(spec.page_text(p)[:200] not in virtual for p in deep), "deep page text absent from virtual prompt")
    check("V-SPEC-MONOLITHIC-HAS-ALL", all(spec.page_text(p) in mono for p in spec.pages), "every page inline")
    check("V-SPEC-CRIPPLED-NO-PATHS", not any(d in crip for d in deep_paths) and "Deep pages" not in crip,
          "positive-control arm carries no page access")
    check("V-SPEC-SMALLER", len(virtual) < len(mono) * 0.6, f"virtual={len(virtual)} monolithic={len(mono)}")
    check("V-SPEC-HEADER", virtual.startswith(A.HEADER) and f"spec={spec.spec_hash()}" in virtual, virtual[:90])
    d = spec.dispatch("Audit the plan.")
    check("V-SPEC-DISPATCH-CARRIER", d["subagent_type"] == "cpp-carrier-verifier" and d["model"] == "opus", d["subagent_type"])
    check("V-SPEC-EMPTY-MISSION", code_of(lambda: spec.compile("  ")) == "EMPTY_MISSION", "typed")

    # carriers: the runtime-enforced tool line must equal the class allowlist exactly
    for cls, tools in A.CLASS_TOOLS.items():
        f = A.CARRIERS_DIR / f"{A.carrier_name(cls)}.md"
        line = re.search(r"^tools:\s*(.+)$", f.read_text(encoding="utf-8"), re.M) if f.is_file() else None
        got = [t.strip() for t in line.group(1).split(",")] if line else None
        check(f"V-SPEC-CARRIER-{cls.upper()}-TOOLS", got == tools, f"{got} == {tools}")

    # typed failures on a scratch copy of the real spec
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        base = root / "base"
        shutil.copytree(spec.dir, base)
        raw = json.loads((base / "spec.json").read_text(encoding="utf-8"))

        def variant(name, mutate):
            d2 = root / name
            shutil.copytree(base, d2)
            r = copy.deepcopy(raw)
            mutate(r, d2)
            (d2 / "spec.json").write_text(json.dumps(r), encoding="utf-8")
            return lambda: A.load(name, root)

        esc = variant("escalate", lambda r, d: r["contract"].update(
            write_surfaces=["repo"], rollback="git revert", kill_switch="off"))
        check("V-SPEC-ESCALATION-REFUSED", code_of(esc) == "CLASS_BELOW_WRITE_SURFACE",
              "write surface under a non-writer class is refused")
        ok_writer = variant("writer_ok", lambda r, d: (r["contract"].update(
            write_surfaces=["repo"], rollback="git revert", kill_switch="off"),
            r["agent"].update(permission_class="writer")))
        check("V-SPEC-WRITER-CONTROL", code_of(ok_writer) == "NO_ERROR", "same surface under writer loads")
        check("V-SPEC-UNKNOWN-CLASS", code_of(variant("badclass", lambda r, d: r["agent"].update(
            permission_class="root"))) == "UNKNOWN_CLASS", "typed")
        check("V-SPEC-MISSING-PAGE", code_of(lambda: variant("nopage", lambda r, d: (
            d / r["agent"]["pages"][0]["path"]).unlink())().compile("m")) == "MISSING_PAGE", "typed")
        check("V-SPEC-PAGE-TAMPER", code_of(lambda: variant("tamper", lambda r, d: (
            d / r["agent"]["pages"][1]["path"]).write_text("changed", encoding="utf-8"))().compile("m"))
              == "PAGE_HASH_MISMATCH", "typed")
        crlf = variant("crlf", lambda r, d: [
            (d / p["path"]).write_bytes((d / p["path"]).read_bytes().replace(b"\n", b"\r\n")) for p in r["agent"]["pages"]])
        check("V-SPEC-CRLF-CHECKOUT", code_of(lambda: crlf().compile("m")) == "NO_ERROR"
              and crlf().spec_hash() == spec.spec_hash(), "an autocrlf checkout keeps the same identity")
        check("V-SPEC-NO-INLINE", code_of(variant("noinline", lambda r, d: [
            p.update(load="on_demand") for p in r["agent"]["pages"]])) == "NO_INLINE_PAGE", "typed")
        check("V-SPEC-UNKNOWN-SPEC", code_of(lambda: A.load("does-not-exist", root)) == "UNKNOWN_SPEC", "typed")
        (root / "broken").mkdir()
        (root / "broken" / "spec.json").write_text("{not json", encoding="utf-8")
        ok, bad = A.catalog(root)
        check("V-SPEC-CATALOG-TYPED-BROKEN", any(b["spec"] == "broken" and b["code"] == "UNREADABLE_SPEC" for b in bad)
              and any(s.id == "oneshot-architect-auditor" for s in ok), f"ok={len(ok)} bad={[b['code'] for b in bad]}")

        # ACV C4: every unreadable shape is a typed record, never an exception out of catalog().
        # Measured 2026-10-03: only JSONDecodeError was caught, so these escaped resolve() untyped.
        good = raw
        shapes = {"non-utf8": b"\xff\xfe{ not text", "json-array": b"[1, 2]",
                  "contract-string": json.dumps({**good, "contract": "x"}).encode(),
                  "class-list": json.dumps({**good, "agent": {**good["agent"], "permission_class": ["w"]}}).encode()}
        for name, data in shapes.items():
            (root / name).mkdir()
            (root / name / "spec.json").write_bytes(data)
        try:
            ok, bad = A.catalog(root)
            got = {b["spec"]: b["code"] for b in bad}
            err = None
        except Exception as e:  # noqa: BLE001 -- the gate's subject is exactly an escaping exception
            got, err = {}, f"{type(e).__name__}: {e}"
        want = {"non-utf8": "UNREADABLE_SPEC", "json-array": "UNREADABLE_SPEC",
                "contract-string": "INVALID_CONTRACT", "class-list": "UNKNOWN_CLASS"}
        check("V-SPEC-CATALOG-UNREADABLE-SHAPES", err is None and all(got.get(k) == v for k, v in want.items())
              and any(s.id == "oneshot-architect-auditor" for s in ok), err or got)

        # A directory with no spec.json is not a spec: resolver.fingerprint() never sees it, so
        # counting it as broken made a cached answer and a fresh one disagree (C4 audit gap 4).
        (root / "scratch-notes").mkdir()
        ok, bad = A.catalog(root)
        check("V-SPEC-CATALOG-SKIPS-NON-SPEC-DIR", not any(b["spec"] == "scratch-notes" for b in bad),
              [b["spec"] for b in bad])

    # state version: a real sha from this repo (the bare-`git` PATH gap returned 'none')
    sv = A.current_state_version(ROOT)
    check("V-SPEC-STATE-VERSION", bool(re.fullmatch(r"[0-9a-f]{40}", sv)), sv[:12])

    # pointer delivery: the parent carries a header + path, the carrier Reads the image,
    # and the live agent-solo-guard accepts the dispatch for a no-write carrier.
    import subprocess
    with tempfile.TemporaryDirectory() as t:
        for sid in ("silent-failure-hunter", "oneshot-architect-auditor"):
            sp = A.load(sid)
            d = sp.dispatch("Review x for problems.", images_dir=Path(t))
            img = Path(d["image"])
            ok_img = img.is_file() and img.read_text(encoding="utf-8") == sp.compile("Review x for problems.")
            check(f"V-SPEC-POINTER-{sid}", ok_img and len(d["prompt"]) < 600 and img.as_posix() in d["prompt"],
                  f"prompt={len(d['prompt'])} chars, image={img.stat().st_size if img.is_file() else 0} B")
            guard = Path.home() / ".claude" / "hooks" / "agent-solo-guard.js"
            payload = json.dumps({"tool_name": "Agent", "cwd": str(ROOT),
                                  "tool_input": {"prompt": d["prompt"], "subagent_type": d["subagent_type"]}})
            tracker = Path.home() / ".claude" / "state" / "agent-solo-tracker.json"
            if tracker.exists():
                tracker.unlink()
            g = subprocess.run(["node", str(guard)], input=payload, capture_output=True, text=True, timeout=30)
            check(f"V-SPEC-GUARD-ACCEPTS-{sid}", g.returncode == 0, f"exit={g.returncode} {g.stderr[:80]}")
            if tracker.exists():
                tracker.unlink()

    print(f"AGENT_SPEC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
