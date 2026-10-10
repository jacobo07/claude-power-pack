#!/usr/bin/env python3
"""A5-U3 gates: semantic stage of tools/cost_to_completion.py (hermetic; mutants run from temp dirs)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cost_to_completion as real  # noqa: E402
import route_admission as ra  # noqa: E402

FLOORS = ra.load_floors()
WF = FLOORS["profiles"][ra.TOP_LEVEL]["floor"]
res: list[tuple[str, bool, str]] = []


def check(name, cond, ev=""):
    res.append((name, bool(cond), ev))
    print(f"{'PASS' if cond else 'FAIL'} {name} {ev}")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PROFILES = {k: {"calls": c, "ctx_tokens": 200_000} for k, c in
            (("known_transform", 1), ("bounded_coding", 3), ("novel", 5))}
INV = ["file:a.py@sha1"]


def doc(obls, **kw):
    d = {"claims": [{"id": "c", "class": "novel", "obligations": obls}], "profiles": PROFILES}
    d.update(kw)
    return d


def cand(m, obls, **kw):
    return m.compile_cost(doc(obls, **kw), FLOORS)


def refused(m, obls, **kw):
    try:
        cand(m, obls, **kw)
    except m.Refused as r:
        return r.reason
    except Exception as exc:  # a mutant may crash: that is not a refusal
        return f"CRASH:{type(exc).__name__}"
    return None


def behaviours(m) -> dict:
    """Named boolean behaviours of a module; the mutants must break at least one."""
    b = {}
    ctx = 200_000
    o = cand(m, [{"id": "a", "satisfier": "STATE", "invalidators": INV}])
    b["NO_WORK"] = o["candidate"]["tokens"] == 0 and o["semantic"]["obligation_counts"] == {"NO_WORK": 1}
    o = cand(m, [{"id": "a", "satisfier": "TOOL"}, {"id": "b", "satisfier": "TRANSFORM"}])
    b["NO_COMPUTE"] = o["candidate"]["tokens"] == 0 and o["semantic"]["obligation_counts"] == {"NO_COMPUTE": 2}
    fam = [{"id": f"f{i}", "satisfier": "TRANSFORM", "family": "F", "proof": "p"} for i in range(4)]
    o = cand(m, fam)
    b["FAMILY_ONCE"] = o["candidate"]["tokens"] == (3 + 3 * 1) * ctx and o["candidate"]["calls"] == 6
    b["FAMILY_LB"] = o["semantic"]["irreducible_lower_bound"]["novel_decisions"] == 1
    o = cand(m, [{"id": "a", "satisfier": "OBSERVATION", "observation": "o1"},
                 {"id": "b", "satisfier": "OBSERVATION", "observation": "o1"},
                 {"id": "c", "satisfier": "OBSERVATION", "observation": "o2"}])
    b["SHARED_OBS"] = o["candidate"]["tokens"] == 2 * ctx and o["semantic"]["irreducible_lower_bound"]["observations"] == 2
    o = cand(m, [{"id": "a", "satisfier": "PROOF", "proof": "p1"}, {"id": "b", "satisfier": "PROOF", "proof": "p1"}])
    b["SHARED_PROOF"] = o["candidate"]["tokens"] == ctx and o["semantic"]["irreducible_lower_bound"]["assurance_judgments"] == 1
    o = cand(m, [{"id": "a", "satisfier": "STATE", "invalidators": [{"id": "h", "stale": True}]}])
    b["STALE_RECOMPUTED"] = o["candidate"]["tokens"] == ctx and o["semantic"]["stale"] == ["c/a"]
    o = cand(m, [{"id": "m", "satisfier": "MODEL", "alternatives": ["STATE", "TOOL"]},
                 {"id": "w", "satisfier": "OWNER"}], historical_calls=1000)
    s = o["semantic"]
    b["LOWER_BOUND"] = s["irreducible_lower_bound"]["total"] == 2 and o["candidate"]["tokens"] == 5 * ctx \
        and o["ceiling"]["tokens"] == 15 * ctx
    b["MULTIPLIER"] = s["overhead_multiplier_input"] == 500
    b["BUDGET_ALTS"] = s["interrupt_budget"] == {"novel": 5} and s["alternatives"][0]["alternatives"] == ["STATE", "TOOL"]
    b["REFUSE_MISSING_INV"] = refused(m, [{"id": "a", "satisfier": "STATE"}]) == "MISSING_INVALIDATOR" \
        and refused(m, [{"id": "a", "satisfier": "STATE", "invalidators": []}]) == "MISSING_INVALIDATOR"
    b["REFUSE_FAMILY_NO_PROOF"] = refused(m, [{"id": "a", "satisfier": "TRANSFORM", "family": "F"}]) == "FAMILY_NO_PROOF"
    b["REFUSE_HISTORICAL"] = refused(m, [{"id": "a", "satisfier": "TOOL"}], label="new architecture", profiles={}) == "HISTORICAL_PROFILE"
    b["PHASE_REFUSED"] = refused(m, [{"id": "a", "satisfier": "TOOL"}], phase_average_cost=1) == "PHASE_MULTIPLIER"
    return b


def mutate(old: str, new: str, tag: str):
    src = (HERE / "cost_to_completion.py").read_text(encoding="utf-8")
    assert old in src, f"mutation anchor missing: {tag}"
    d = Path(tempfile.mkdtemp(prefix=f"a5u3-mut-{tag}-"))
    (d / "cost_to_completion.py").write_text(src.replace(old, new, 1), encoding="utf-8")
    return load(d / "cost_to_completion.py", f"ctc_mut_{tag}")


def main() -> int:
    base = behaviours(real)
    for k, v in base.items():
        check(f"A5U3-{k}", v)
    # controls: the admitting side of each refusal
    check("A5U3-CONTROL-INV-ADMITS", refused(real, [{"id": "a", "satisfier": "STATE", "invalidators": INV}]) is None)
    check("A5U3-CONTROL-FAMILY-PROOF-ADMITS",
          refused(real, [{"id": "a", "satisfier": "TRANSFORM", "family": "F", "proof": "p"}]) is None)
    check("A5U3-CONTROL-HISTORICAL-ADMITS",
          refused(real, [{"id": "a", "satisfier": "TOOL"}], label="new architecture") is None
          and refused(real, [{"id": "a", "satisfier": "TOOL"}], label="forecast", profiles={}) is None)
    # historical flag
    h = real.compile_cost({"claims": [{"id": "c", "class": "novel", "obligations": [{"id": "a", "satisfier": "TOOL"}]}]}, FLOORS)
    check("A5U3-HISTORICAL-FLAG", h["HISTORICAL_PROFILE"] is True and cand(real, [{"id": "a", "satisfier": "TOOL"}])["HISTORICAL_PROFILE"] is False)
    # absent fields: output identical to the pre-semantic shape
    plain = real.compile_cost({"claims": [{"id": "x", "class": "novel"}]}, FLOORS)
    check("A5U3-ABSENT-UNCHANGED", "semantic" not in plain and "HISTORICAL_PROFILE" not in plain)
    # CLI: refusal exits 2 with reason; control exits 0
    def cli(d):
        f = Path(tempfile.mkdtemp(prefix="a5u3-cli-")) / "c.json"
        f.write_text(json.dumps(d), encoding="utf-8")
        p = subprocess.run([sys.executable, str(HERE / "cost_to_completion.py"), "--claims", str(f)],
                           capture_output=True, text=True, timeout=20)
        return p.returncode, json.loads(p.stdout.splitlines()[0] if p.returncode else p.stdout)
    rc, o = cli(doc([{"id": "a", "satisfier": "STATE"}]))
    rc2, _ = cli(doc([{"id": "a", "satisfier": "STATE", "invalidators": INV}]))
    check("A5U3-CLI-REFUSAL-AND-CONTROL", rc == 2 and o.get("reason") == "MISSING_INVALIDATOR" and rc2 == 0)
    # mutants: each must break the behaviours named
    m1 = mutate('''        if isinstance(i, dict) and (i.get("stale") or i.get("valid") is False):
            return "stale"''', '''        pass''', "stale")
    bad = [k for k, v in behaviours(m1).items() if not v]
    check("A5U3-MUTANT-STALE-ACCEPTED-RED", "STALE_RECOMPUTED" in bad, f"red={bad}")
    m2 = mutate('if o["proof"] not in st["proofs"]', 'if True', "shared-proof")
    m3 = mutate('if fam not in st["families"]:', 'if True:', "family")
    bad = [k for k, v in behaviours(m3).items() if not v]
    check("A5U3-MUTANT-FAMILY-PRICED-N-TIMES-RED", "FAMILY_ONCE" in bad, f"red={bad}")
    bad = [k for k, v in behaviours(m2).items() if not v]
    check("A5U3-MUTANT-PROOF-PRICED-N-TIMES-RED", "SHARED_PROOF" in bad, f"red={bad}")
    m4 = mutate('if o["observation"] not in st["obs"]', 'if True', "obs")
    bad = [k for k, v in behaviours(m4).items() if not v]
    check("A5U3-MUTANT-OBS-PRICED-N-TIMES-RED", "SHARED_OBS" in bad, f"red={bad}")
    m5 = mutate('if not isinstance(inv, list) or not inv or any(not i for i in inv):', 'if False:', "inv")
    check("A5U3-MUTANT-NO-INVALIDATOR-ACCEPTED-RED", not behaviours(m5)["REFUSE_MISSING_INV"])
    m6 = mutate('and historical:', 'and False:', "hist")
    check("A5U3-MUTANT-HISTORICAL-ACCEPTED-RED", not behaviours(m6)["REFUSE_HISTORICAL"])
    p = sum(1 for _, ok, _ in res if ok)
    print(f"A5_U3_PASS={p}/{len(res)}")
    return 0 if p == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
