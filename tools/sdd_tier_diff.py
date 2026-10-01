#!/usr/bin/env python3
"""Tier-diff gate: what changes, by name, when `spec_gate.classify_tier` changes.

Loads the classifier at a base revision from git (`git show <rev>:modules/spec_gate/gate.py`)
next to the working-tree one, and runs both over two prompt sets:

  corpus   fixtures/sdd_os/replay_corpus.json tier cases -- LABELLED, so every change is judged:
             correction   old out of the labelled range, new inside it
             REGRESSION   old inside, new outside  (the gate fails on any)
             in-range     both inside (allowed; reported)
             still-wrong  both outside
  history  real prompts from ~/.claude/history.jsonl, read at run time and never written
           anywhere -- UNLABELLED, so changes are listed for review (hash + redacted snippet),
           never judged.

Consumer impact is measured by running each consumer's REAL entry point twice, with the
attribute `modules.spec_gate.gate.classify_tier` (and prd_generator's module-level import)
patched to the old and then the new classifier. Two consumers are derived instead of called,
and say so: cost_gate's Haiku tip (tier <= 1, cost_gate.py) reads session transcripts, and
cognitive_os.router's model floor is a table lookup on the tier.

    python tools/sdd_tier_diff.py [--base f6518c6] [--history N] [--show]
exit 0 = no corpus regression and every consumer probe ran; 1 = corpus regression;
2 = a probe could not run (UNJUDGED: nothing about consumers was measured).
"""
from __future__ import annotations

import hashlib
import inspect
import json
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GIT = r"C:\Program Files\Git\cmd\git.exe"
CORPUS = ROOT / "fixtures" / "sdd_os" / "replay_corpus.json"
HISTORY = Path.home() / ".claude" / "history.jsonl"
MIN_PROMPT_CHARS = 40          # the live activation route ignores shorter prompts
HISTORY_UNTIL_MS = 1790812800000   # 2026-10-01T00:00:00Z: prompts after this never enter the sample
SNIPPET = 70
_REDACT = re.compile(r"[A-Za-z]:\\[^\s\"']+|/[\w.-]+(?:/[\w.-]+)+|https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+"
                     r"|\b(?:\d{1,3}\.){3}\d{1,3}\b")

import modules.spec_gate.gate as gate_mod  # noqa: E402


def load_base_classifier(rev: str):
    src = subprocess.run([GIT, "-C", str(ROOT), "show", f"{rev}:modules/spec_gate/gate.py"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    mod = types.ModuleType("spec_gate_base")
    mod.__file__ = str(ROOT / "modules" / "spec_gate" / "gate.py")
    # @dataclass resolves annotations through sys.modules[cls.__module__]; an
    # unregistered module raises AttributeError at class creation.
    sys.modules[mod.__name__] = mod
    exec(compile(src, f"{rev}:gate.py", "exec"), mod.__dict__)  # noqa: S102 -- our own file at a rev
    return mod.classify_tier


def history_prompts(n: int, until_ms: int = HISTORY_UNTIL_MS) -> list[str]:
    """A STABLE sample: prompts before a fixed timestamp, chosen by hash order.

    A seeded shuffle of the whole file is not stable -- history.jsonl grows during
    the session, so two runs of the same code compared different samples (measured
    2026-10-01: the second run's 150 prompts shared almost none with the first).
    """
    if n <= 0 or not HISTORY.exists():
        return []
    seen: set[str] = set()
    for line in HISTORY.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        p = (d.get("display") or "").strip()
        ts = d.get("timestamp")
        if (isinstance(ts, (int, float)) and ts < until_ms and len(p) >= MIN_PROMPT_CHARS
                and not p.startswith(("/", "!"))):
            seen.add(p)
    return sorted(seen, key=lambda p: hashlib.sha256(p.encode()).hexdigest())[:n]


def snippet(p: str) -> str:
    s = _REDACT.sub("<x>", " ".join(p.split()))
    return s[:SNIPPET] + ("..." if len(s) > SNIPPET else "")


def _consumers(tmp: Path) -> dict:
    from modules.cognitive_os.router import _TIER_FLOOR
    from modules.dataset_first import classifier as dfp_cls
    from modules.dataset_first.knowledge_sufficiency import evaluate as dfp_eval
    from modules.pp_agents.signals import sdd_tier
    from modules.sdd_os.pre_exec_gate import evaluate as sdd_eval
    from modules.sdd_os.prd_generator import generate_prd
    cls_kw = {"cwd": tmp} if "cwd" in inspect.signature(dfp_cls.classify).parameters else {}
    return {
        "sdd_activation.action": lambda p, t: sdd_eval(p, tmp).action,
        "sdd_tier_signal.fires": lambda p, t: sdd_tier.evaluate(p, cwd=str(tmp)) is not None,
        "dfp.verdict": lambda p, t: dfp_eval(p).verdict,
        "dfp.project_class": lambda p, t: str(dfp_cls.classify(p, **cls_kw).project_class),
        "prd_generator.sections": lambda p, t: len(generate_prd(p).sections),
        "reframing_gate.applies": lambda p, t: gate_mod.check_reframing_gate(p).applies,
        "router.floor (derived)": lambda p, t: _TIER_FLOOR.get(t, 1),
        "cost_gate.haiku_tip (derived)": lambda p, t: t <= 1,
    }


def _with(fn, call):
    import modules.sdd_os.prd_generator as prd
    saved = (gate_mod.classify_tier, prd.classify_tier)
    gate_mod.classify_tier = prd.classify_tier = fn
    try:
        return call()
    finally:
        gate_mod.classify_tier, prd.classify_tier = saved


def main(argv: list[str]) -> int:
    rev = argv[argv.index("--base") + 1] if "--base" in argv else "f6518c6"
    n_hist = int(argv[argv.index("--history") + 1]) if "--history" in argv else 400
    show = "--show" in argv
    old_fn, new_fn = load_base_classifier(rev), gate_mod.classify_tier

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))["tier_cases"]
    buckets: dict[str, list[str]] = {"correction": [], "REGRESSION": [], "in-range": [], "still-wrong": []}
    for c in corpus:
        o, n = old_fn(c["prompt"]).tier, new_fn(c["prompt"]).tier
        if o == n:
            continue
        ok = lambda t: c["tier_min"] <= t <= c["tier_max"]  # noqa: E731
        key = ("in-range" if ok(o) and ok(n) else "correction" if ok(n)
               else "REGRESSION" if ok(o) else "still-wrong")
        buckets[key].append(f"{c['id']} T{o}->T{n}")
    print(f"corpus ({len(corpus)} labelled, base {rev}):")
    for k, v in buckets.items():
        print(f"  {k:<12} {len(v):>3}  {', '.join(v)}")

    hist = history_prompts(n_hist)
    up = down = 0
    changed: list[str] = []
    for p in hist:
        o, n = old_fn(p).tier, new_fn(p).tier
        if o != n:
            up, down = up + (n > o), down + (n < o)
            r = new_fn(p)
            changed.append(f"{hashlib.sha256(p.encode()).hexdigest()[:8]} T{o}->T{n} "
                           f"[{'+'.join(r.risk_dims) or r.base_reason[:30]}] {snippet(p)}")
    print(f"history ({len(hist)} unlabelled real prompts): changed={len(changed)} up={up} down={down}")
    if show:
        for line in changed:
            print(f"  {line}")

    prompts = [c["prompt"] for c in corpus] + hist
    unjudged: list[str] = []
    with tempfile.TemporaryDirectory(prefix="tierdiff-") as d:
        for name, probe in _consumers(Path(d)).items():
            deltas, errs = [], 0
            for p in prompts:
                try:
                    a = _with(old_fn, lambda: probe(p, old_fn(p).tier))
                    b = _with(new_fn, lambda: probe(p, new_fn(p).tier))
                except Exception:  # noqa: BLE001 -- counted, never read as "no change"
                    errs += 1
                    continue
                if a != b:
                    deltas.append(f"{a}->{b}")
            # ANY error blocks OK: a consumer that raises under one classifier and not the other
            # is a behaviour change that was counted as "no change" (code review W2, F6).
            if errs:
                unjudged.append(f"{name} ({errs} errors)")
            summary: dict[str, int] = {}
            for x in deltas:
                summary[x] = summary.get(x, 0) + 1
            print(f"  consumer {name:<32} changed={len(deltas):>3}/{len(prompts) - errs}"
                  f"{f' errors={errs}' if errs else ''}  {summary}")

    if buckets["REGRESSION"]:
        print("TIERDIFF_VERDICT=REGRESSION")
        return 1
    if unjudged:
        print(f"TIERDIFF_VERDICT=UNJUDGED probes={unjudged}")
        return 2
    print("TIERDIFF_VERDICT=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
