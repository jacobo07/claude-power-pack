#!/usr/bin/env python3
"""test_alert_escalation.py -- gates for the repeat-alert escalation policy.

Both poles are tested: a repeat that must escalate, and a finding that
resolves normally and must NEVER escalate. The load-bearing gate replays the
real 333-handoff corpus that motivated the policy and asserts the escalator
would have fired at the third notice.

Hermetic: every write goes to a fresh temp dir. The replay gate reads the real
corpus read-only and SKIPs (explained) when it is absent.

Run: python tools/test_alert_escalation.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.alert_escalation import policy as esc  # noqa: E402

HANDOFFS = PP_ROOT / "vault" / "handoffs"
DAY = 86400

_passes: list[str] = []
_fails: list[str] = []
_skips: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  [OK] {gate} -- {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  [X ] {gate} -- {diagnostic}")


def _skip(gate: str, why: str) -> None:
    _skips.append(gate)
    print(f"  [..] {gate} -- SKIP: {why}")


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="esc-"))


def _policy(after: int = 3, days: int = 7) -> esc.Policy:
    return esc.Policy(escalate_after=after, re_escalate_after_days=days,
                      source="test")


# --------------------------------------------------------------- V-ESC-THRESHOLD

def gate_threshold() -> None:
    d = _tmp()
    try:
        pol = _policy(after=3)
        routes = [esc.observe(d, pol, "mirror-drift", "k", now=1000.0 + i).route
                  for i in range(3)]
        if routes == [esc.ROUTINE, esc.ROUTINE, esc.ESCALATE]:
            _ok("V-ESC-THRESHOLD",
                f"routes={routes} -- promotion lands exactly at occurrence 3")
        else:
            _fail("V-ESC-THRESHOLD", f"expected ROUTINE,ROUTINE,ESCALATE got {routes}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- V-ESC-SUPPRESS

def gate_suppress() -> None:
    d = _tmp()
    try:
        pol = _policy(after=3, days=7)
        base = 1000.0
        for i in range(3):
            esc.observe(d, pol, "mirror-drift", "k", now=base + i)
        later = [esc.observe(d, pol, "mirror-drift", "k",
                             now=base + 100 + i * 3600).route for i in range(20)]
        if set(later) == {esc.SUPPRESS}:
            _ok("V-ESC-SUPPRESS",
                f"{len(later)}/{len(later)} post-escalation occurrences suppressed "
                f"within the {pol.re_escalate_after_days}-day window")
        else:
            _fail("V-ESC-SUPPRESS", f"expected all SUPPRESS, got {set(later)}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# -------------------------------------------------------- V-ESC-RESOLVE-RESETS

def gate_resolve_resets() -> None:
    """A finding that gets resolved normally must never escalate."""
    d = _tmp()
    try:
        pol = _policy(after=3)
        t = 1000.0
        routes = []
        for _cycle in range(6):
            routes.append(esc.observe(d, pol, "mirror-drift", "k", now=t).route)
            t += 60
            routes.append(esc.observe(d, pol, "mirror-drift", "k", now=t).route)
            t += 60
            esc.note_resolved(d, "k", now=t)  # the fix landed
            t += 60
        if esc.ESCALATE in routes:
            _fail("V-ESC-RESOLVE-RESETS",
                  f"escalated despite resolution between every pair: {routes}")
            return
        ledger = esc.load_ledger(d)
        standing = esc.open_escalations(ledger)
        if standing:
            _fail("V-ESC-RESOLVE-RESETS", f"stale standing rows: {standing}")
            return
        _ok("V-ESC-RESOLVE-RESETS",
            f"{len(routes)} occurrences over 6 resolve cycles, 0 escalations, "
            f"0 standing rows -- resolution is a real transition")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def gate_resolve_clears_standing() -> None:
    d = _tmp()
    try:
        pol = _policy(after=2)
        esc.observe(d, pol, "mirror-drift", "k", now=1000.0)
        esc.observe(d, pol, "mirror-drift", "k", now=1060.0)
        before = len(esc.open_escalations(esc.load_ledger(d)))
        esc.note_resolved(d, "k", now=1120.0)
        after = len(esc.open_escalations(esc.load_ledger(d)))
        body = (d / esc.STANDING_NAME).read_text(encoding="utf-8")
        if before == 1 and after == 0 and "No finding is currently escalated" in body:
            _ok("V-ESC-RESOLVE-CLEARS-STANDING",
                "standing rows 1 -> 0 and the report says so in words")
        else:
            _fail("V-ESC-RESOLVE-CLEARS-STANDING",
                  f"before={before} after={after} report={body[:80]!r}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------ V-ESC-CONFIG

def gate_config() -> None:
    """The threshold is configurable, not hardcoded -- file and env."""
    repo = _tmp()
    try:
        cfg = repo / "vault" / "config"
        cfg.mkdir(parents=True)
        (cfg / "alert_escalation.json").write_text(
            json.dumps({"escalate_after": 5, "re_escalate_after_days": 2}),
            encoding="utf-8")
        from_file = esc.load_policy(repo)

        prior = os.environ.get(esc.ENV_THRESHOLD)
        os.environ[esc.ENV_THRESHOLD] = "9"
        try:
            from_env = esc.load_policy(repo)
        finally:
            if prior is None:
                os.environ.pop(esc.ENV_THRESHOLD, None)
            else:
                os.environ[esc.ENV_THRESHOLD] = prior

        os.environ[esc.ENV_THRESHOLD] = "1"
        try:
            clamped = esc.load_policy(repo)
        finally:
            os.environ.pop(esc.ENV_THRESHOLD, None)

        shipped = esc.load_policy(PP_ROOT)
        checks = [
            (from_file.escalate_after == 5, f"file threshold {from_file.escalate_after}"),
            (from_file.re_escalate_after_days == 2,
             f"file re-escalate {from_file.re_escalate_after_days}"),
            (from_env.escalate_after == 9, f"env threshold {from_env.escalate_after}"),
            (clamped.escalate_after == esc.MIN_ESCALATE_AFTER,
             f"floor clamp {clamped.escalate_after}"),
            (shipped.source.endswith("alert_escalation.json"),
             f"shipped config read from {shipped.source}"),
        ]
        bad = [msg for ok, msg in checks if not ok]
        if bad:
            _fail("V-ESC-CONFIG", "; ".join(bad))
        else:
            _ok("V-ESC-CONFIG",
                f"file=5 env=9 clamp={esc.MIN_ESCALATE_AFTER} "
                f"shipped={shipped.escalate_after} from {Path(shipped.source).name}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


# --------------------------------------------------------------- V-ESC-BOOTSTRAP

def gate_bootstrap() -> None:
    """History already on disk counts. A ledger created today must not make a
    two-month-old repeat look like a first sighting."""
    d = _tmp()
    try:
        key = esc.finding_key("mirror-drift", "a.md", "b.md")
        for i in range(4):
            (d / f"mirror-drift-2026-05-2{i}T10-00-00Z.md").write_text(
                f"# Mirror Drift Detected\n\n- **Finding key**: `{key}`\n",
                encoding="utf-8")
        counted = esc.count_prior_occurrences(d, "mirror-drift", key)
        route = esc.observe(d, _policy(after=3), "mirror-drift", key,
                            now=time.time()).route
        if counted == 4 and route == esc.ESCALATE:
            _ok("V-ESC-BOOTSTRAP",
                f"{counted} prior handoffs adopted -> first run escalates immediately")
        else:
            _fail("V-ESC-BOOTSTRAP", f"counted={counted} route={route}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def gate_legacy_match() -> None:
    """Pre-policy handoffs carry no key line; they are matched by content."""
    d = _tmp()
    try:
        legacy = r"C:\some\path\apex_baseline_doctrine.md"
        for i in range(5):
            (d / f"mirror-drift-2026-06-0{i}T10-00-00Z.md").write_text(
                f"# Mirror Drift Detected\n\n- **PP path**: `{legacy}`\n",
                encoding="utf-8")
        hit = esc.count_prior_occurrences(d, "mirror-drift", "new-key",
                                          legacy_match=legacy)
        miss = esc.count_prior_occurrences(d, "mirror-drift", "new-key",
                                          legacy_match=r"C:\other\file.md")
        if hit == 5 and miss == 0:
            _ok("V-ESC-LEGACY-MATCH",
                "5 keyless handoffs matched by content; a different path matches 0")
        else:
            _fail("V-ESC-LEGACY-MATCH", f"hit={hit} miss={miss}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------- V-ESC-STANDING-ONE-FILE

def gate_standing_one_file() -> None:
    d = _tmp()
    try:
        pol = _policy(after=2)
        for k in ("k1", "k2", "k3"):
            esc.observe(d, pol, "mirror-drift", k, detail=f"detail {k}", now=1000.0)
            esc.observe(d, pol, "mirror-drift", k, detail=f"detail {k}", now=1060.0)
        reports = list(d.glob("ESCALATED*.md"))
        body = (d / esc.STANDING_NAME).read_text(encoding="utf-8")
        named = sum(1 for k in ("k1", "k2", "k3") if f"`{k}`" in body)
        if len(reports) == 1 and named == 3:
            _ok("V-ESC-STANDING-ONE-FILE",
                "3 escalations -> 1 file, 3 rows (rewritten in place, never appended)")
        else:
            _fail("V-ESC-STANDING-ONE-FILE",
                  f"files={len(reports)} rows_named={named}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --------------------------------------------------------------- V-ESC-REPLAY-333

def gate_replay_real_corpus() -> None:
    """The case that motivated the policy, replayed at its real cadence."""
    if not HANDOFFS.is_dir():
        _skip("V-ESC-REPLAY-333", f"corpus absent: {HANDOFFS}")
        return
    real = sorted(HANDOFFS.glob("mirror-drift-*.md"))
    if len(real) < 10:
        _skip("V-ESC-REPLAY-333", f"only {len(real)} handoffs on disk")
        return
    stamps = [esc.handoff_timestamp(p) for p in real]
    d = _tmp()
    try:
        pol = esc.load_policy(PP_ROOT)
        routes = [esc.observe(d, pol, "mirror-drift", "replay", now=ts).route
                  for ts in stamps]
        first_esc = routes.index(esc.ESCALATE) + 1 if esc.ESCALATE in routes else 0
        writes = sum(1 for r in routes if r != esc.SUPPRESS)
        span_days = (stamps[-1] - stamps[0]) / DAY
        if first_esc != pol.escalate_after:
            _fail("V-ESC-REPLAY-333",
                  f"first escalation at occurrence {first_esc}, "
                  f"expected {pol.escalate_after}")
            return
        if writes >= len(real):
            _fail("V-ESC-REPLAY-333",
                  f"no reduction: {writes} writes for {len(real)} occurrences")
            return
        _ok("V-ESC-REPLAY-333",
            f"{len(real)} real handoffs over {span_days:.0f} days -> escalates at "
            f"occurrence {first_esc}; {writes} files would have been written "
            f"instead of {len(real)} ({len(real) - writes} suppressed)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------ verifier integration

def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "bvr_under_test", PP_ROOT / "tools" / "background_verifier_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_verifier_wired() -> None:
    mod = _load_verifier()
    cwd = _tmp()
    try:
        a, b = cwd / "global.md", cwd / "mirror.md"
        a.write_text("one\ntwo\nthree\n", encoding="utf-8")
        b.write_text("one\ntwo\n", encoding="utf-8")
        mod.MIRROR_PAIRS = [(a, b)]
        handoffs = cwd / "vault" / "handoffs"

        pol = esc.load_policy(PP_ROOT)
        for _ in range(pol.escalate_after):
            mod.check_mirror_parity(cwd)
            for p in handoffs.glob("mirror-drift-*.md"):  # defeat the 10-min dedupe
                os.utime(p, (0, 0))
        files = sorted(handoffs.glob("mirror-drift-*.md"))
        bodies = [p.read_text(encoding="utf-8") for p in files]
        urgent = [t for t in bodies if "**Severity**: URGENT" in t]
        keyed = [t for t in bodies if "**Finding key**:" in t]
        standing = handoffs / esc.STANDING_NAME
        # Handoff filenames carry a whole-second stamp, so a same-second rerun
        # overwrites rather than accumulating. The ledger, not the file count,
        # records how many detections actually happened.
        seen = max((e.occurrences for e in esc.load_ledger(handoffs).values()),
                   default=0)

        if not (seen == pol.escalate_after and len(urgent) == 1
                and len(keyed) == len(bodies) and standing.is_file()):
            _fail("V-ESC-VERIFIER-WIRED",
                  f"observed={seen} files={len(files)} urgent={len(urgent)} "
                  f"keyed={len(keyed)} standing={standing.is_file()}")
            return

        # Now resolve it: identical content must clear the standing row.
        b.write_text("one\ntwo\nthree\n", encoding="utf-8")
        mod.check_mirror_parity(cwd)
        rows = esc.open_escalations(esc.load_ledger(handoffs))
        if rows:
            _fail("V-ESC-VERIFIER-WIRED",
                  f"standing row survived a resolved condition: {rows}")
            return
        _ok("V-ESC-VERIFIER-WIRED",
            f"{seen} detections through the real check, exactly 1 URGENT at the "
            f"threshold, every handoff keyed; parity restored -> standing 1 -> 0")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)


def gate_failopen() -> None:
    """No escalation module -> detection still happens, in routine mode."""
    mod = _load_verifier()
    cwd = _tmp()
    try:
        a, b = cwd / "global.md", cwd / "mirror.md"
        a.write_text("alpha\n", encoding="utf-8")
        b.write_text("beta\n", encoding="utf-8")
        mod.MIRROR_PAIRS = [(a, b)]
        mod.escalation = None
        mod.check_mirror_parity(cwd)
        files = list((cwd / "vault" / "handoffs").glob("mirror-drift-*.md"))
        if len(files) == 1 and "**Severity**: ROUTINE" in files[0].read_text(
                encoding="utf-8"):
            _ok("V-ESC-FAILOPEN",
                "escalation module absent -> handoff still written, ROUTINE severity")
        else:
            _fail("V-ESC-FAILOPEN", f"{len(files)} handoff(s) written")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)


def gate_no_drift_no_handoff() -> None:
    mod = _load_verifier()
    cwd = _tmp()
    try:
        a, b = cwd / "global.md", cwd / "mirror.md"
        # Bytes, not write_text: in text mode Windows turns "\r\n" into
        # "\r\r\n", which is a real difference and would test nothing.
        a.write_bytes(b"same\nlines\n")
        b.write_bytes(b"same\r\nlines\r\n")
        mod.MIRROR_PAIRS = [(a, b)]
        mod.check_mirror_parity(cwd)
        files = list((cwd / "vault" / "handoffs").glob("mirror-drift-*.md"))
        if not files:
            _ok("V-ESC-NO-FALSE-DRIFT",
                "identical content differing only in line endings raises nothing")
        else:
            _fail("V-ESC-NO-FALSE-DRIFT",
                  "line-ending difference reported as drift")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)


def gate_pair_corrected() -> None:
    """Regression guard for the defect itself: the watched pair must be two
    copies of one document, not two different documents."""
    mod = _load_verifier()
    pairs = mod.MIRROR_PAIRS
    if len(pairs) != 1:
        _fail("V-ESC-PAIR-CORRECTED", f"expected 1 pair, found {len(pairs)}")
        return
    g, p = pairs[0]
    if "apex_baseline_doctrine" in str(p):
        _fail("V-ESC-PAIR-CORRECTED",
              "still paired against apex_baseline_doctrine.md, which is a "
              "different document (mirrors a CLAUDE.md section)")
        return
    if g.name != p.name:
        _fail("V-ESC-PAIR-CORRECTED", f"pair names differ: {g.name} vs {p.name}")
        return
    if not g.is_file() or not p.is_file():
        _skip("V-ESC-PAIR-CORRECTED", "one side absent on this host")
        return
    _ok("V-ESC-PAIR-CORRECTED",
        f"both sides are `{g.name}`; PP side is the repo mirror of the same "
        f"document")


def main() -> int:
    print("Alert Escalation Gates (Option A -- unresolved-repeat promotion)")
    print("")
    gate_threshold()
    gate_suppress()
    gate_resolve_resets()
    gate_resolve_clears_standing()
    gate_config()
    gate_bootstrap()
    gate_legacy_match()
    gate_standing_one_file()
    gate_replay_real_corpus()
    gate_verifier_wired()
    gate_failopen()
    gate_no_drift_no_handoff()
    gate_pair_corrected()
    total = len(_passes) + len(_fails)
    print("")
    print(f"ESCALATION_PASS={len(_passes)}/{total}  skipped={len(_skips)}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
