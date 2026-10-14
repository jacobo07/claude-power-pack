#!/usr/bin/env python3
"""Phase 5.2 / 05-2-03: canonical environment (N17, audit A4) and platform vs portability (N19).

The A4 defect: `proof.environment_fingerprint` hashed tool NAMES, so a tool upgraded from 1.0 to 2.0 left the
premise `equal` and a certificate was inherited across it. The canonical body resolves each declared
dependency to what is INSTALLED (`pkg:` version, `tool:` version, `lock:` file bytes, `runtime:python`);
a bare name resolves to nothing and the premise is unknown. The resolver is the boundary the drift gate
mocks; everything else (the certificate, the ledger, the judge's inheritance plan) is real.

Summary line: GSDX_TRUST_ENV_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import test_gsd_x_goal_trust_forgery as tf                 # noqa: E402  (FG fixture, hermetic HOME)
import test_gsd_x_goal_judge_validate as jv                 # noqa: E402
from modules.gsd_x.goal import convergence as cv           # noqa: E402
from modules.gsd_x.goal import inherit as ih                # noqa: E402
from modules.gsd_x.goal import proof as pf                  # noqa: E402
from modules.gsd_x.goal import trust                        # noqa: E402

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a raise is a FAIL line, never an escape
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


class Patched:
    """Swap the resolver boundary for the length of a block."""

    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = getattr(trust, k)
            setattr(trust, k, v)

    def __exit__(self, *_a):
        for k, v in self.old.items():
            setattr(trust, k, v)


def fake_pkg(versions):
    return lambda name: versions.get(name)


# --- drift through the real inheritance plan ---------------------------------------------

def plan_action(drift: bool):
    fg = tf.FG("fg-env")
    try:
        fg.cert("ob-one")
        fg.settle()
        st = jv._st(fg.w.log)
        with Patched(runtime_info=(lambda: {"impl": "CPython", "version": "9.9.9"}) if drift else trust.runtime_info):
            items = ih.plan(st, fg.w.repo, fg.w.tree(), time.time())
        row = next(i for i in items if i["obligation"] == "ob-one")
        return row["action"], row["reason"]
    finally:
        fg.close()


def gate_drift():
    act, why = plan_action(True)
    ctl, cwhy = plan_action(False)
    return act == ih.INVALIDATE and "environment" in why and ctl == ih.INHERIT, \
        f"drift -> {act} ({why}); control -> {ctl} ({cwhy})"


# --- canonical body ----------------------------------------------------------------------

def gate_versions():
    with Patched(resolve_pkg=fake_pkg({"foo": "1.0"})):
        a = trust.environment_canonical(["pkg:foo"])
    with Patched(resolve_pkg=fake_pkg({"foo": "2.0"})):
        b = trust.environment_canonical(["pkg:foo"])
        c = trust.environment_canonical(["pkg:foo"])
    legacy_a, legacy_b = pf.environment_fingerprint(["pkg:foo"]), pf.environment_fingerprint(["pkg:foo"])
    return a != b and b == c and a.startswith("env2:") and legacy_a == legacy_b, \
        f"v1.0={a[:14]} v2.0={b[:14]} (legacy names-only hash is version-blind: {legacy_a == legacy_b})"


def gate_lock(tmp):
    lk = tmp / "x.lock"
    lk.write_bytes(b"a==1\n")
    h1 = trust.environment_canonical([f"lock:{lk}"])
    lk.write_bytes(b"a==2\n")
    h2 = trust.environment_canonical([f"lock:{lk}"])
    lk.write_bytes(b"a==1\n")
    h3 = trust.environment_canonical([f"lock:{lk}"])
    gone = trust.environment_canonical([f"lock:{tmp / 'absent.lock'}"])
    return h1 != h2 and h1 == h3 and gone.startswith(pf.UNKNOWN_PREFIX), \
        f"bytes change -> {h1 != h2}, restore -> {h1 == h3}, missing file -> unknown {gone.startswith(pf.UNKNOWN_PREFIX)}"


def gate_runtime():
    body = trust.canonical_env_body([])
    rt = body.get("runtime", {})
    full = re.fullmatch(r"\d+\.\d+\.\d+.*", str(rt.get("version", ""))) is not None
    with Patched(runtime_info=lambda: {"impl": "PyPy", "version": rt.get("version")}):
        other = trust.environment_canonical([])
    return bool(rt.get("impl")) and full and other != trust.environment_canonical([]), \
        f"runtime={rt.get('impl')} {rt.get('version')}; implementation change alters the hash: {other != trust.environment_canonical([])}"


def gate_bare():
    h = trust.environment_canonical(["pytest"])
    prem = pf.observe_premises(
        {"environment": h, "freshness_class": "DETERMINISTIC", "env_deps": ["pytest"], "ts": 1.0},
        {"environment": h}, 2.0)
    return h.startswith(pf.UNKNOWN_PREFIX) and prem["environment"] == pf.UNKNOWN_OBS, \
        f"bare name -> {h[:24]}; premise {prem['environment']}"


def gate_stable():
    with Patched(resolve_pkg=fake_pkg({"a": "1", "b": "2"})):
        x = trust.environment_canonical(["pkg:a", "pkg:b"])
        y = trust.environment_canonical(["pkg:b", "pkg:a", "pkg:a"])
    with Patched(runtime_info=lambda: {"impl": "CPython", "version": "3.12.0"},
                 platform_info=lambda: {"system": "Plane", "machine": "m0"}, resolve_pkg=fake_pkg({"a": "1"})):
        vec = trust.environment_canonical(["pkg:a", "runtime:python"])
        pinned = vec == trust.environment_canonical(["runtime:python", "pkg:a", "pkg:a"])
    return x == y and pinned and re.fullmatch(r"env2:[0-9a-f]{64}", vec) is not None, \
        f"order/duplicates stable={x == y}; fixed vector {vec}"


def gate_no_legacy_caller():
    hits = []
    for p in (ROOT / "modules").rglob("*.py"):
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "environment_fingerprint(" in line and not line.lstrip().startswith(("def ", "#")):
                hits.append(f"{p.relative_to(ROOT).as_posix()}:{n}")
    return not hits, f"callers of the legacy fingerprint under modules/: {hits or 'none'}"


def gate_migration():
    """An `env1:` certificate meets an `env2:` observation: changed, so STALE once -- never equal, never unknown."""
    old = pf.environment_fingerprint([])
    new = trust.environment_canonical([])
    prem = {"environment": old, "freshness_class": "DETERMINISTIC", "env_deps": [], "ts": 1.0}
    o = pf.observe_premises(prem, {"environment": new}, 2.0)["environment"]
    o2 = pf.observe_premises(dict(prem, environment=new), {"environment": new}, 2.0)["environment"]
    return o == pf.CHANGED and o2 == pf.EQUAL, f"env1 vs env2 -> {o}; env2 vs env2 -> {o2}"


# --- N19 plane ---------------------------------------------------------------------------

def gate_plane_field():
    fg = tf.FG("fg-plane")
    try:
        fg.cert("ob-one")
        st = jv._st(fg.w.log)
        d = next(e["data"] for e in pf.project_proofs(st).produced if e["data"]["claim_id"] == fg.cids["ob-one"])
        pl = d.get("plane") or {}
        ok_shape = (pl.get("claim") == "PLATFORM" and isinstance(pl.get("planes"), list) and len(pl["planes"]) == 1
                    and bool(pl.get("modules_tree")))
        return ok_shape and trust.plane_ok(pl)[0], f"plane={pl}"
    finally:
        fg.close()


def gate_needs_two():
    one = trust.portability_plane({"windows": "t1"})
    two = trust.portability_plane({"windows": "t1", "linux": "t1"})
    return one is None and two is not None and trust.plane_ok(two)[0], f"one plane -> {one}; two same tree -> {two}"


def gate_same_tree():
    bad = trust.portability_plane({"windows": "t1", "linux": "t2"})
    forced = {"claim": "PORTABILITY", "planes": ["windows", "linux"], "modules_tree": {"windows": "t1", "linux": "t2"}}
    ctl = trust.portability_plane({"windows": "t1", "linux": "t1"})
    return bad is None and not trust.plane_ok(forced)[0] and ctl is not None, \
        f"different trees -> {bad}; hand-forced stamp ok={trust.plane_ok(forced)[0]}; control -> {ctl is not None}"


def gate_unknown_tree():
    bad = trust.portability_plane({"windows": "t1", "linux": "unknown:dirty"})
    dirty = trust.portability_plane({"windows": "t1-dirty", "linux": "t1-dirty"})
    ctl = trust.portability_plane({"windows": "t1", "linux": "t1"})
    return bad is None and dirty is None and ctl is not None, f"unknown -> {bad}; dirty -> {dirty}; control ok"


def gate_platform_not_portability():
    fg = tf.FG("fg-plat")
    try:
        fg.cert("ob-one")
        st = jv._st(fg.w.log)
        d = next(e["data"] for e in pf.project_proofs(st).produced if e["data"]["claim_id"] == fg.cids["ob-one"])
        relabeled = dict(d["plane"], claim="PORTABILITY")
        return d["plane"]["claim"] == "PLATFORM" and not trust.plane_ok(relabeled)[0], \
            f"stamped {d['plane']['claim']}; relabelled to PORTABILITY ok={trust.plane_ok(relabeled)[0]}"
    finally:
        fg.close()


def main() -> int:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="gsdx-env-"))
    run_gate("V-TRUST-ENV-HERMETIC-HOME", lambda: (jv.Path.home().resolve() == jv._TMP_HOME.resolve(), "tmp home"))
    run_gate("V-TRUST-ENV-DRIFT-INVALIDATES", gate_drift)
    run_gate("V-TRUST-ENV-VERSIONS-COUNT", gate_versions)
    run_gate("V-TRUST-ENV-LOCK-STATE", lambda: gate_lock(tmp))
    run_gate("V-TRUST-ENV-RUNTIME", gate_runtime)
    run_gate("V-TRUST-ENV-BARE-NAME-UNKNOWN", gate_bare)
    run_gate("V-TRUST-ENV-CANONICAL-STABLE", gate_stable)
    run_gate("V-TRUST-ENV-NO-LEGACY-CALLER", gate_no_legacy_caller)
    run_gate("V-TRUST-ENV-MIGRATION-ONCE", gate_migration)
    run_gate("V-TRUST-PLANE-FIELD", gate_plane_field)
    run_gate("V-TRUST-PORTABILITY-NEEDS-TWO-PLANES", gate_needs_two)
    run_gate("V-TRUST-PORTABILITY-SAME-TREE", gate_same_tree)
    run_gate("V-TRUST-PORTABILITY-UNKNOWN-TREE", gate_unknown_tree)
    run_gate("V-TRUST-PLATFORM-NOT-PORTABILITY", gate_platform_not_portability)
    total = passes + fails
    print(f"GSDX_TRUST_ENV_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
