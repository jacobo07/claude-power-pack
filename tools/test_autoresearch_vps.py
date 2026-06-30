#!/usr/bin/env python3
"""test_autoresearch_vps.py -- Block C done-gate (V-gates, hermetic x3).

Verifies the CONTRACT, not the live VPS (per the plan: "el test verifica
contrato, no requiere el VPS para correr en CI"). Five gates:

  V-VPS-NO-LOCAL-INTERRUPT  -- the local Stop hook returns silently (no
                               systemMessage) so AutoResearch never interrupts
                               the Owner's session. Host-tolerant: passes if the
                               live hook is absent (e.g. CI / another machine).
  V-PULL-MECHANISM          -- session_start_hub.js defines AND wires the digest
                               read + detached VPS pull.
  V-AGENT-REACH-ENRICH      -- enricher module exists; VTT parsing, the top-N
                               cap, and the disabled no-op all behave.
  V-CREDENTIALS-NOT-IN-REPO -- no credential literals under modules/autoresearch.
  V-BASELINE-INTACT         -- signal_scorer.score_signal is deterministic
                               (discovery/scoring not regressed by Block C).

Run: python tools/test_autoresearch_vps.py   (exit 0 iff 5/5 on all 3 runs)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
AR_DIR = PP_ROOT / "modules" / "autoresearch"
HUB = PP_ROOT / "hooks" / "session_start_hub.js"
LIVE_HOOK = Path.home() / ".claude" / "hooks" / "kobiiclaw-autoresearch.js"
sys.path.insert(0, str(AR_DIR))

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate} -- {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate} -- {ev}")


def gate_no_local_interrupt() -> None:
    if not LIVE_HOOK.exists():
        _ok("V-VPS-NO-LOCAL-INTERRUPT",
            "live Stop hook absent on this host (nothing to interrupt)")
        return
    src = LIVE_HOOK.read_text(encoding="utf-8")
    # The object KEY `systemMessage:` must be gone; the word may survive in the
    # V4 comment, which is fine.
    if "systemMessage:" not in src and "return { continue: true };" in src:
        _ok("V-VPS-NO-LOCAL-INTERRUPT",
            "Stop hook returns { continue: true } with no systemMessage")
    else:
        _fail("V-VPS-NO-LOCAL-INTERRUPT", "hook still emits a systemMessage")


def gate_pull_mechanism() -> None:
    if not HUB.exists():
        _fail("V-PULL-MECHANISM", "session_start_hub.js not found")
        return
    hub = HUB.read_text(encoding="utf-8")
    defined = all(t in hub for t in (
        "function hookAutoResearchDigest", "function hookAutoResearchPull",
        "VPS_DIGEST_CACHE"))
    wired = "hookAutoResearchPull();" in hub and "hookAutoResearchDigest()" in hub
    if defined and wired:
        _ok("V-PULL-MECHANISM",
            "hub defines + wires inline digest read & detached pull")
    else:
        _fail("V-PULL-MECHANISM", f"defined={defined} wired={wired}")


def gate_enrich() -> None:
    try:
        import enricher
    except Exception as exc:
        _fail("V-AGENT-REACH-ENRICH", f"import failed: {exc}")
        return
    for fn in ("jina_fetch", "ytdlp_transcript", "enrich_signals", "_parse_vtt"):
        if not hasattr(enricher, fn):
            _fail("V-AGENT-REACH-ENRICH", f"missing {fn}")
            return
    # VTT parse: strips header/timestamps, dedups consecutive duplicate cues.
    vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n"
           "00:00:03.000 --> 00:00:05.000\nHello world\nSecond line\n")
    parsed = enricher._parse_vtt(vtt)
    if ("Hello world" not in parsed or parsed.count("Hello world") != 1
            or "Second line" not in parsed):
        _fail("V-AGENT-REACH-ENRICH", f"vtt parse wrong: {parsed!r}")
        return
    orig = enricher.jina_fetch
    try:
        calls = {"n": 0}

        def fake_jina(url, *a, **k):
            calls["n"] += 1
            return "ENR"
        enricher.jina_fetch = fake_jina
        # Top-N cap: 20 signals, budget 3 -> exactly 3 enriched.
        sigs = [{"type": "rss", "link": f"http://x/{i}", "score": i / 100.0}
                for i in range(20)]
        n = enricher.enrich_signals(
            sigs, {"enrichment": {"enabled": True, "max_signals": 3,
                                  "ytdlp_enabled": False}})
        n_marked = sum(1 for s in sigs if s.get("enriched") == "ENR")
        if n != 3 or n_marked != 3:
            _fail("V-AGENT-REACH-ENRICH", f"cap not honored: n={n} marked={n_marked}")
            return
        # Disabled -> no-op.
        sigs2 = [{"type": "rss", "link": "http://x", "score": 1.0}]
        enricher.enrich_signals(sigs2, {"enrichment": {"enabled": False}})
        if any("enriched" in s for s in sigs2):
            _fail("V-AGENT-REACH-ENRICH", "disabled still enriched")
            return
    finally:
        enricher.jina_fetch = orig  # restore for hermetic re-runs
    _ok("V-AGENT-REACH-ENRICH",
        "module + vtt-parse + top-N cap + disabled-noop verified")


def gate_credentials() -> None:
    pat = re.compile(
        r"(?i)(cookie\s*[:=]|bearer\s+[a-z0-9]|password\s*[:=]|"
        r"sk-[a-z0-9]{20}|ghp_[A-Za-z0-9]{20}|auth_token\s*[:=]|"
        r"access_token\s*[:=])")
    hits: list[str] = []
    for p in AR_DIR.rglob("*"):
        if p.suffix not in (".py", ".json") or "__pycache__" in str(p):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for m in pat.finditer(txt):
            hits.append(f"{p.name}:{m.group(0)[:24]}")
    if not hits:
        _ok("V-CREDENTIALS-NOT-IN-REPO",
            "no credential literals under modules/autoresearch")
    else:
        _fail("V-CREDENTIALS-NOT-IN-REPO", f"{hits[:3]}")


def gate_baseline() -> None:
    try:
        import signal_scorer
    except Exception as exc:
        _fail("V-BASELINE-INTACT", f"import failed: {exc}")
        return
    sig = {"authority": 1.0, "keywords": [], "title": "x", "summary": "y",
           "published_epoch": None, "entry_count": 1}
    sc = signal_scorer.score_signal(sig, {"universal_keywords": []})
    # 0.35*1 + 0.35*1(no kw) + 0.20*0.5(no ts) + 0.10*0.2(count1) = 0.82
    if abs(sc - 0.82) < 0.01:
        _ok("V-BASELINE-INTACT", f"score_signal deterministic = {sc}")
    else:
        _fail("V-BASELINE-INTACT", f"unexpected score {sc}")


def run_suite() -> None:
    gate_no_local_interrupt()
    gate_pull_mechanism()
    gate_enrich()
    gate_credentials()
    gate_baseline()


def main() -> int:
    global _passes, _fails
    results: list[tuple[int, int]] = []
    for i in range(3):
        _passes = 0
        _fails = 0
        print(f"--- hermetic run {i + 1}/3 ---")
        run_suite()
        results.append((_passes, _fails))
    last_p, last_f = results[-1]
    consistent = len(set(results)) == 1
    ok = all(f == 0 for _, f in results) and consistent
    print(f"AUTORESEARCH_VPS_PASS={last_p}/{last_p + last_f}  "
          f"runs={results}  consistent={consistent}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
