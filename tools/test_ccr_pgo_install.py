#!/usr/bin/env python
"""V-PGOINST-*: the X2 step 5 installer (`ccr_pgo.py install` / `verify`) and the DEFLATE hold, each gate driven from
both poles. Hermetic: every install goes to a temp directory and every verify runs as a subprocess, so no mission
state and no ~/.claude file is written (V-PGOINST-REAL-STATE-UNTOUCHED proves the second).
Run: python -I tools/test_ccr_pgo_install.py   (last line: PGOINST_PASS=<n>/<total>)"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="ccr-pgoinst-test-"))
for _k, _v in (("GSD_LONG_RUN_STATE_DIR", TMP / "st"), ("GSD_LONG_RUN_SESSIONS_DIR", TMP / "st" / "sessions"),
               ("GSD_AUTORUN_MARKER_DIR", TMP / "st"), ("CPP_CLAUDE_JOBS_DIR", TMP / "st" / "jobs"),
               ("GSD_LONG_RUN_PROJECTS_DIR", TMP / "st" / "projects")):
    os.environ[_k] = str(_v)
for _k in ("CPP_CCR_DEFLATE", "CCR_WORK_UNIT", "CPP_CCR_PGO_DIR"):
    os.environ.pop(_k, None)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import ccr_pgo as pg  # noqa: E402

TOOL = HERE / "ccr_pgo.py"
CLASSES = REPO / "vault/programs/ccr/stage3/a3/pgo-classes.json"
BE_DIR = REPO / "vault/programs/ccr/stage3/a4/pgo"
BE_NAMES = ("bounded-code-worker.breakeven.json", "read-only-reviewer.breakeven.json")
POLICY_TS = REPO / "mods/cpp-cognitive-runtime/hooks/policy.ts"
GSD_MISSION = HERE / "gsd_mission.py"
RUNBOOK = REPO / "vault/programs/ccr/PGO-INSTALL.md"
REAL_PGO = Path.home() / ".claude" / "ccr" / "state" / "pgo"
passes = fails = 0
_n = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fresh(name: str) -> Path:
    global _n
    _n += 1
    d = TMP / f"{_n:02d}-{name}"
    d.mkdir(parents=True)
    return d


def run(*args: str, env: dict | None = None) -> tuple[int, dict, str]:
    e = {k: v for k, v in os.environ.items() if k not in ("CPP_CCR_DEFLATE", "CCR_WORK_UNIT", "CPP_CCR_PGO_DIR")}
    e["PYTHONIOENCODING"] = "utf-8"
    e.update(env or {})
    p = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=e, timeout=240,
                       encoding="utf-8")
    try:
        obj = json.loads(p.stdout)
    except ValueError:
        obj = {}
    return p.returncode, obj, p.stdout + p.stderr


def snap(d: Path):
    if not d.exists():
        return None
    return sorted((str(p.relative_to(d)), sha(p) if p.is_file() else "<dir>") for p in d.rglob("*"))


def row(rows: list, probe: str) -> dict:
    return next((r for r in rows if r.get("probe") == probe), {})


def install_tracer_dest() -> Path:
    """classes only (an empty break-even dir installs no break-even file)."""
    d, empty = fresh("trace-dest"), fresh("empty-be")
    rc, out, txt = run("install", "--classes", str(CLASSES), "--breakeven", str(empty), "--dest", str(d),
                       "--receipt", str(d.parent / (d.name + "-receipt.json")))
    assert rc == 0, txt
    return d


def breakeven_ok(obj) -> bool:
    return not pg.validate_breakeven(obj, "bounded-code-worker")


def mirror_ok(ts: str) -> tuple[bool, str]:
    need = ["m?.cls === cls", "[m.capsule, m.R, m.rehyd_cost, m.first_overhead, m.r, m.g]",
            "typeof v === 'number' && Number.isFinite(v) && v >= 0", "Array.isArray(m.lengths) && m.lengths.length > 0",
            "m.lengths.every((v: unknown) => typeof v === 'number')", "'bounded-code-worker'", "'read-only-reviewer'"]
    miss = [s for s in need if s not in ts]
    m = re.search(r"\[(m\.\w+(?:,\s*m\.\w+)*)\]\s*\.every", ts)
    fields = tuple(re.findall(r"m\.(\w+)", m.group(1))) if m else ()
    if fields != pg.BREAKEVEN_NUMERIC:
        miss.append(f"numeric list {fields} != {pg.BREAKEVEN_NUMERIC}")
    return (not miss, "; ".join(miss) or "rule text present")


def dir_parity_ok(gm_text: str) -> bool:
    return ('Path.home() / ".claude" / "ccr" / "state" / "pgo"' in gm_text and "CPP_CCR_PGO_DIR" in gm_text
            and "pgo-classes.json" in gm_text)


def doc_ok(text: str, subs: set[str]) -> tuple[bool, str]:
    miss = [s for s in ("CPP_CCR_DEFLATE", "ccr_pgo.py install", "ccr_pgo.py verify", "pgo-classes.json", "Rollback")
            if s not in text]
    unknown = sorted({m for m in re.findall(r"ccr_pgo\.py\s+([a-z][a-z-]*)", text)} - subs)
    return (not miss and not unknown, f"missing={miss} unknown_subcommands={unknown}")


def main() -> int:
    real_before = snap(REAL_PGO)
    sources_ok = CLASSES.is_file() and all((BE_DIR / n).is_file() for n in BE_NAMES)
    assert sources_ok, "committed Stage 3 sources missing"

    # ---- Task 1: the tracer path, source -> install -> real contract -> real deflate -> declared unit file ----
    d = install_tracer_dest()
    receipt = json.loads((d.parent / (d.name + "-receipt.json")).read_text(encoding="utf-8"))
    rf = receipt["files"][0] if receipt.get("files") else {}
    mutated = fresh("mut") / "pgo-classes.json"
    b = bytearray(CLASSES.read_bytes())
    b[len(b) // 2] ^= 1
    mutated.write_bytes(bytes(b))
    check("V-PGOINST-COPY-VERIFIED",
          sha(d / "pgo-classes.json") == sha(CLASSES) == rf.get("destination_sha256") == rf.get("source_sha256")
          and sorted(p.name for p in d.iterdir()) == ["pgo-classes.json"] and sha(mutated) != sha(CLASSES),
          f"dest sha256 {sha(d / 'pgo-classes.json')[:16]} == source == receipt; 1 file; a flipped byte differs")

    rc, v, txt = run("verify", "--dest", str(d))
    bc, lk = row(v.get("contract", []), "bounded-code"), row(v.get("contract", []), "lookup")
    check("V-PGOINST-CONTRACT-READS-INSTALLED",
          rc == 0 and (bc.get("work_class"), bc.get("confidence")) == ("bounded-code", "MEDIUM")
          and (lk.get("work_class"), lk.get("confidence")) == ("lookup", "LOW") and bc.get("verdict") != "UNFORECAST",
          f"rc={rc} bounded-code={bc} lookup={lk}")

    on_b, on_l = row(v.get("deflate_on", []), "bounded-code"), row(v.get("deflate_on", []), "lookup")
    check("V-PGOINST-DEFLATE-ON",
          on_b.get("action") == "deflated" and on_b.get("declared_exists") is True
          and on_b.get("declared_class") == "bounded-code-worker" and on_l.get("action") == "would_deflate"
          and on_l.get("declared_exists") is False and v.get("deflate_live") == "deflated",
          f"bounded-code={on_b} lookup={on_l}")

    off = v.get("deflate_off", [])
    check("V-PGOINST-HOLD-OFF",
          len(off) == 2 and all(r.get("env") == {} and r.get("row") == {} for r in off) and on_b.get("action") == "deflated",
          f"CPP_CCR_DEFLATE=off rows={[(r.get('probe'), r.get('env'), r.get('row')) for r in off]} while on => deflated")

    empty = fresh("empty-dest")
    rc_e, ve, _ = run("verify", "--dest", str(empty))
    rc_m, vm, _ = run("verify", "--dest", str(empty / "missing"))
    check("V-PGOINST-EMPTY-DEST-UNFORECAST",
          rc_e != 0 and rc_m != 0 and all(r.get("verdict") == "UNFORECAST" for r in ve.get("contract", [{}]))
          and ve.get("ok") is False and vm.get("dest_exists") is False and rc == 0,
          f"empty rc={rc_e} verdicts={[r.get('verdict') for r in ve.get('contract', [])]}; missing dir rc={rc_m}; "
          f"installed rc={rc}")

    # ---- Task 2: break-even files, refusals, both holds, drift pin ----
    full = fresh("full-dest")
    rcf, inst, txt = run("install", "--dest", str(full))
    names = sorted(p.name for p in full.iterdir())
    rcv, vf, _ = run("verify", "--dest", str(full))
    src_of = {"pgo-classes.json": CLASSES, **{n: BE_DIR / n for n in BE_NAMES}}
    eq = all(sha(full / n) == sha(p) for n, p in src_of.items() if (full / n).is_file())
    srcs = [json.loads((BE_DIR / n).read_text(encoding="utf-8")) for n in BE_NAMES]
    check("V-PGOINST-BREAKEVEN-PARSES",
          rcf == 0 and names == sorted(src_of) and eq and rcv == 0 and vf.get("breakeven_ok") is True
          and sorted(vf.get("breakeven_files", [])) == sorted(BE_NAMES)
          and not pg.validate_breakeven(srcs[0], "bounded-code-worker")
          and not pg.validate_breakeven(srcs[1], "read-only-reviewer")
          and bool(pg.validate_breakeven(srcs[0], "read-only-reviewer")),
          f"install rc={rcf} files={names} sha256 equal={eq}; verify breakeven_ok={vf.get('breakeven_ok')}")

    ok_obj = srcs[0]

    def mut(**kw):
        o = copy.deepcopy(ok_obj)
        o.update(kw)
        return o
    nan_obj = json.loads(json.dumps(mut(capsule=float("nan"))))        # round-trips through the `NaN` literal
    variants = {"cls mismatch": (mut(cls="read-only-reviewer"), "`cls`"), "negative number": (mut(r=-1), "`r`"),
                "NaN literal": (nan_obj, "`capsule`"), "empty lengths": (mut(lengths=[]), "`lengths`"),
                "string in lengths": (mut(lengths=[1, "2"]), "`lengths`"), "bool for number": (mut(g=True), "`g`"),
                "infinity": (mut(R=float("inf")), "`R`"), "missing field": ({k: v for k, v in ok_obj.items() if k != "first_overhead"}, "`first_overhead`")}
    bad = {k: pg.validate_breakeven(o, "bounded-code-worker") for k, (o, _) in variants.items()}
    named = all(errs and want in " ".join(errs) for (k, errs), (_, want) in zip(bad.items(), variants.values()))
    check("V-PGOINST-BREAKEVEN-REJECTS-BAD", named and breakeven_ok(ok_obj),
          f"{len(variants)} variants rejected with the field named; control accepted: {breakeven_ok(ok_obj)}")

    mixed = fresh("mixed-be")
    shutil.copy(BE_DIR / BE_NAMES[0], mixed / BE_NAMES[0])
    broken = json.loads((BE_DIR / BE_NAMES[1]).read_text(encoding="utf-8"))
    broken["cls"] = "wrong-class"
    (mixed / BE_NAMES[1]).write_text(json.dumps(broken), encoding="utf-8")
    d_bad = TMP / "aon-bad"
    rc_bad, o_bad, _ = run("install", "--classes", str(CLASSES), "--breakeven", str(mixed), "--dest", str(d_bad))
    shutil.copy(BE_DIR / BE_NAMES[1], mixed / BE_NAMES[1])
    d_good = TMP / "aon-good"
    rc_good, o_good, _ = run("install", "--classes", str(CLASSES), "--breakeven", str(mixed), "--dest", str(d_good))
    check("V-PGOINST-ALL-OR-NOTHING",
          rc_bad != 0 and not d_bad.exists() and bool(o_bad.get("errors")) and rc_good == 0
          and len(list(d_good.iterdir())) == 3,
          f"one invalid break-even file: rc={rc_bad}, destination created={d_bad.exists()}; control rc={rc_good}, "
          f"files={len(list(d_good.iterdir())) if d_good.exists() else 0}")

    seed = fresh("seeded")
    (seed / "pgo-classes.json").write_bytes(b'{"hand": "tuned"}')
    seed_sha = hashlib.sha256(b'{"hand": "tuned"}').hexdigest()
    rc_r, o_r, _ = run("install", "--dest", str(seed))
    survived = (seed / "pgo-classes.json").read_bytes() == b'{"hand": "tuned"}' and sorted(
        p.name for p in seed.iterdir()) == ["pgo-classes.json"]
    same = fresh("seeded-same")
    shutil.copy(CLASSES, same / "pgo-classes.json")
    rc_s, o_s, _ = run("install", "--dest", str(same))
    forced = fresh("seeded-force")
    (forced / "pgo-classes.json").write_bytes(b'{"hand": "tuned"}')
    rc_f, o_f, _ = run("install", "--dest", str(forced), "--force")
    prev = next((f.get("previous_sha256") for f in o_f.get("files", []) if f.get("name") == "pgo-classes.json"), None)
    check("V-PGOINST-REFUSES-DIFFERING-OVERWRITE",
          rc_r != 0 and survived and rc_s == 0 and sha(same / "pgo-classes.json") == sha(CLASSES)
          and rc_f == 0 and sha(forced / "pgo-classes.json") == sha(CLASSES) and prev == seed_sha,
          f"differing: rc={rc_r}, seed survived={survived}; identical: rc={rc_s}; --force: rc={rc_f}, receipt previous "
          f"sha256 matches seed={prev == seed_sha}")

    hold = fresh("hold-dest")
    run("install", "--dest", str(hold))
    rc_h0, vh0, _ = run("verify", "--dest", str(hold))
    (hold / "pgo-classes.json").unlink()
    rc_h1, vh1, _ = run("verify", "--dest", str(hold))
    b1 = row(vh1.get("deflate_on", []), "bounded-code")
    check("V-PGOINST-HOLD-BY-REMOVAL",
          rc_h0 == 0 and row(vh0.get("deflate_on", []), "bounded-code").get("action") == "deflated" and rc_h1 != 0
          and b1.get("action") == "no_unit_class" and b1.get("declared_exists") is False
          and not any(r.get("declared_exists") for r in vh1.get("deflate_on", []))
          and all(r.get("env") == {} and r.get("row") == {} for r in vh1.get("deflate_off", [])),
          f"with file: {row(vh0.get('deflate_on', []), 'bounded-code').get('action')}; file removed: rc={rc_h1} "
          f"on={b1.get('action')} off rows empty")

    ts = POLICY_TS.read_text(encoding="utf-8")
    okm, why = mirror_ok(ts)
    ok_ctl, _ = mirror_ok(ts.replace("m.first_overhead, m.r, m.g]", "m.first_overhead, m.r]"))
    ok_ctl2, _ = mirror_ok(ts.replace("m?.cls === cls", "m?.cls == cls"))
    check("V-PGOINST-MIRROR-PINNED-TO-TS", okm and not ok_ctl and not ok_ctl2,
          f"policy.ts: {why}; dropping a field or loosening cls is detected")

    gm_text = GSD_MISSION.read_text(encoding="utf-8")
    saved = os.environ.pop("CPP_CCR_PGO_DIR", None)
    default = pg.pgo_dir()
    os.environ["CPP_CCR_PGO_DIR"] = str(TMP / "elsewhere")
    overridden = pg.pgo_dir()
    os.environ.pop("CPP_CCR_PGO_DIR")
    if saved is not None:
        os.environ["CPP_CCR_PGO_DIR"] = saved
    rc_p, vp, _ = run("verify")
    check("V-PGOINST-DIR-PARITY",
          dir_parity_ok(gm_text) and not dir_parity_ok(gm_text.replace('"ccr"', '"ccx"'))
          and default == Path.home() / ".claude" / "ccr" / "state" / "pgo" and overridden == TMP / "elsewhere"
          and Path(vp.get("dest", "")) == default,
          f"default={default}; override={overridden}; verify (no --dest) reads {vp.get('dest')}")

    # ---- Task 3: the runbook ----
    rc_h, _, helptxt = run("--help")
    subs = set(re.findall(r"[\w-]+", (re.search(r"\{([^}]*)\}", helptxt) or [None, ""])[1].replace(",", " ")))
    text = RUNBOOK.read_text(encoding="utf-8") if RUNBOOK.is_file() else ""
    okd, whyd = doc_ok(text, subs)
    okc, _ = doc_ok(text + "\nRun `python tools/ccr_pgo.py frobnicate` now.\n", subs)
    check("V-PGOINST-DOC", bool(text) and okd and not okc and {"install", "verify"} <= subs,
          f"runbook {'present' if text else 'MISSING'}; {whyd}; a nonexistent subcommand is detected={not okc}")

    # ---- the whole run must not have touched the real state directory ----
    ctl = fresh("snap-ctl")
    s0 = snap(ctl)
    (ctl / "x.json").write_text("{}", encoding="utf-8")
    detects = snap(ctl) != s0
    real_after = snap(REAL_PGO)
    check("V-PGOINST-REAL-STATE-UNTOUCHED", real_before == real_after and detects,
          f"{REAL_PGO}: {'absent' if real_before is None else str(len(real_before)) + ' entries'} before == after; "
          f"the snapshot detects a change={detects}")

    shutil.rmtree(TMP, ignore_errors=True)
    total = passes + fails
    print(f"PGOINST_PASS={passes}/{total}")
    return 0 if fails == 0 and total == 14 else 1


if __name__ == "__main__":
    sys.exit(main())
