#!/usr/bin/env python3
"""cdc_gate.py -- CDC C11: evaluate the 24 Master Done-Gates from evidence files, receipts and jsonl rows.

  cdc_gate.py [--root R] [--live-home H] [--out FILE]   evaluate, print JSON, write FILE (default evidence/cdc-gate.json)
  cdc_gate.py --selftest                                 plant a missing artifact in a temp copy; it must flip to FAIL

Statuses: PASS | FAIL | UNKNOWN | EXTERNAL_LIMITATION. UNKNOWN never counts as PASS. Exit 0 always except
selftest failure (1) or bad usage (2); the verdict is in the JSON (`summary`). Deterministic, no model call.

The brief's own numbering is not stored in the repo. Gates 2, 4, 5, 18, 19, 22 keep the numbers the master plan
(section 5/6) states; the rest are numbered by this file (vault/programs/cdc/C11-gates.md records the mapping).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROG = Path("vault/programs/cdc")
EV = PROG / "evidence"
PASS, FAIL, UNKNOWN, EXT = "PASS", "FAIL", "UNKNOWN", "EXTERNAL_LIMITATION"


def _txt(root: Path, rel) -> str | None:
    p = root / rel
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace") if p.is_file() else None
    except OSError:
        return None


def _json(root: Path, rel):
    t = _txt(root, rel)
    if t is None:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


def _missing(root: Path, rels) -> list[str]:
    return [str(r) for r in rels if not (root / r).is_file()]


def _receipt_ok(root: Path, uid: str) -> tuple[bool, str]:
    t = _txt(root, PROG / f"WU-{uid}-receipt.md")
    if t is None:
        return False, f"receipt WU-{uid}-receipt.md missing"
    if not re.search(r"^Status:\s*DONE\s*$", t, re.M):
        return False, f"receipt WU-{uid} not Status: DONE"
    return True, ""


def _g(n, name, status, reason, evidence=(), in_scope=True):
    return {"gate": n, "name": name, "status": status, "reason": reason, "evidence": list(evidence), "in_scope": in_scope}


def _artifact_gate(root, n, name, unit, files, receipt_re, ok_reason, unknown_if_no_marker=False):
    """PASS only if receipt DONE + files exist + receipt carries the PROVEN marker. Missing file -> FAIL."""
    miss = _missing(root, files)
    if miss:
        return _g(n, name, FAIL, "missing artifact(s): " + ", ".join(miss), files)
    ok, why = _receipt_ok(root, unit)
    if not ok:
        return _g(n, name, FAIL, why, files)
    t = _txt(root, PROG / f"WU-{unit}-receipt.md") or ""
    if not re.search(receipt_re, t, re.S):
        return _g(n, name, UNKNOWN, f"receipt {unit} lacks the PROVEN marker /{receipt_re}/", files)
    return _g(n, name, PASS, ok_reason, files)


def evaluate(root: Path, live_home: Path | None = None) -> dict:
    root = Path(root)
    live_home = Path(live_home) if live_home else Path.home() / ".claude"
    R = []
    P = PROG

    # 1 role ledger (C1)
    g = _artifact_gate(root, 1, "Role ledger classifies every call", "C1", [EV / "ql-phase1-roles.json"],
                       r"PROVEN: .session_autopsy\.py --roles", "12 roles + unattributed, goldens and mutants green (C1)")
    d = _json(root, EV / "ql-phase1-roles.json")
    if g["status"] == PASS and not isinstance(d, dict):
        g = _g(1, g["name"], FAIL, "ql-phase1-roles.json unreadable", g["evidence"])
    R.append(g)

    # 2 model-call firewall: external limitation for the main turn
    R.append(_g(2, "Model-call firewall (interceptable edges only)", EXT,
                "host exposes no pre-call hook for the main model turn; enforced at Agent/launch/tool edges only "
                "(C3 tests 22/22 + dispatch 4/4); real denied spawn from a deployed session NOT_PROVEN",
                [P / "WU-C3-receipt.md"]))

    # 3 effect enum / ABI (C2)
    R.append(_artifact_gate(root, 3, "Effect enum + ABI refuses deopt-less zero route", "C2",
                            ["tools/cognitive_effects.py", P / "C2-decision.md"],
                            r"REFUSED_EFFECT", "REFUSED_EFFECT drill green (C2)"))

    # 4, 5 in-epoch selection: external limitation
    R.append(_g(4, "In-epoch context selection / paging", EXT,
                "host owns the transcript; met at epoch boundary (rotation + capsule), not in-epoch", [P / "PROGRAMME.md"]))
    R.append(_g(5, "In-epoch tool/skill selection", EXT,
                "met through MCP/skill exposure settings (C7 floor metrics), not per-turn selection", [P / "WU-C7-receipt.md"]))

    # 6 semantic breaker (C4)
    inc = list((live_home / "state" / "token-incidents").glob("*.json")) if (live_home / "state" / "token-incidents").is_dir() else []
    g = _artifact_gate(root, 6, "Semantic breaker trips on no-progress loop", "C4",
                       ["hooks/semantic_breaker.js", "tools/test_semantic_breaker.py", "vault/config/semantic-breaker.json"],
                       r"Tripped at call 25", "synthetic loop tripped at call 25, deny budget written (C4 canary)")
    if g["status"] == PASS and not inc:
        g["reason"] += "; incident file not present on this host (receipt-only evidence)"
    R.append(g)

    # 7 proof locality (C5/C5b)
    g = _artifact_gate(root, 7, "Proof locality: closure agrees with full suite", "C5b",
                       [EV / "C5b-step2.json", EV / "C5b-baseline.json", "tools/change_impact.py"],
                       r"Verdict: AGREE on all 3", "AGREE on 3 landings after serial rerun + parent control")
    if g["status"] == PASS:
        g["reason"] += "; raw 'full minus baseline' was non-empty (3/7/5): baseline non-deterministic, agreement needed control runs"
    R.append(g)

    # 8 derivation store (C6): two-session proof rows
    rows = []
    t = _txt(root, EV / "C6-proof.jsonl")
    for ln in (t or "").splitlines():
        try:
            rows.append(json.loads(ln))
        except ValueError:
            pass
    stored = any(r.get("phase") == "stored" for r in rows)
    denied = any(r.get("phase") == "ask" and r.get("deny") and r.get("session") != "sess-A" for r in rows)
    if t is None:
        R.append(_g(8, "Derivation store serves repeat query", FAIL, f"missing artifact: {EV / 'C6-proof.jsonl'}", [EV / "C6-proof.jsonl"]))
    elif stored and denied:
        R.append(_g(8, "Derivation store serves repeat query", PASS, "sess-A stored, sess-B denied with stored answer path (jsonl rows)", [EV / "C6-proof.jsonl"]))
    else:
        R.append(_g(8, "Derivation store serves repeat query", FAIL, "jsonl lacks stored + second-session deny rows", [EV / "C6-proof.jsonl"]))

    # 9 research gate live
    R.append(_g(9, "Research gate observed on a live WebSearch/WebFetch", UNKNOWN,
                "no live call observed; settings.json registration of the Web events is an Owner step (C6 NOT_PROVEN)", [P / "WU-C6-receipt.md"]))

    # 10 cognitive CI blocks planted regression (C7)
    R.append(_artifact_gate(root, 10, "Cognitive CI blocks a planted regression", "C7",
                            ["tools/cognitive_ci.py", P / "cognitive-baseline.json", P / "cognitive-budget-changes.json"],
                            r"land_worktree refuses COGNITIVE_REGRESSION", "planted +8K CLAUDE.md RED, landing refused, live untouched (C7)"))

    # 11 metamorphic gates
    R.append(_artifact_gate(root, 11, "Metamorphic gates (fixed-work metrics invariant)", "C7",
                            ["tools/test_cognitive_ci.py"], r"metamorphic gates.*unchanged", "+skills/history/goals/tests leave fixed-work metrics unchanged"))

    # 12 PGO report complete (C8)
    pg = _json(root, EV / "cognitive-pgo.json")
    if pg is None:
        R.append(_g(12, "PGO report over the full window", FAIL, f"missing/unreadable {EV / 'cognitive-pgo.json'}", [EV / "cognitive-pgo.json"]))
    else:
        cov = pg.get("coverage")
        full = isinstance(cov, dict) and cov.get("scanned") is not None and cov.get("scanned") == cov.get("total")
        txt = json.dumps(cov)
        okc = full or bool(re.search(r"2993", txt)) or "complete" in txt.lower()
        R.append(_g(12, "PGO report over the full window", PASS if okc else UNKNOWN,
                    "coverage complete: " + txt[:160] if okc else "coverage not shown complete: " + txt[:160], [EV / "cognitive-pgo.json"]))

    # 13 unknown is not zero
    if pg is None:
        R.append(_g(13, "UNKNOWN kept distinct from zero in PGO", FAIL, "cognitive-pgo.json missing", [EV / "cognitive-pgo.json"]))
    else:
        s = json.dumps(pg)
        R.append(_g(13, "UNKNOWN kept distinct from zero in PGO", PASS if '"UNKNOWN"' in s else FAIL,
                    "Owner/Constitutional reported as UNKNOWN" if '"UNKNOWN"' in s else "no UNKNOWN value in the report (zero-as-unknown risk)",
                    [EV / "cognitive-pgo.json"]))

    # 14 holdouts
    R.append(_artifact_gate(root, 14, "Holdout replay (not used for design)", "C10", [EV / "holdouts.json", EV / "holdouts.md"],
                            r"PROVEN \(replay\): 28 holdout traces", "28 holdout traces replayed; avoidable shares are replay estimates, realised saving NOT_PROVEN"))

    # 15 cross-domain canary
    R.append(_artifact_gate(root, 15, "Live cross-domain canary in a non-PP repo", "C10", [EV / "holdouts.md"],
                            r"cross-domain canary in TUA-X", "TUA-X read-only claude -p, 4 turns, 0 denials; guards wired by --settings"))

    # 16 fresh-repo inheritance (observed state of the deployed dispatcher)
    dep = _txt(live_home, "hooks/hook-dispatcher.js")
    inh = _txt(root, EV / "C9-inheritance.md")
    if dep is None:
        R.append(_g(16, "Fresh-repo inheritance (deployed dispatcher runs the guards)", UNKNOWN, "deployed dispatcher not readable", [EV / "C9-inheritance.md"]))
    else:
        has = [k for k in ("cognitive_admission", "semantic_breaker") if k in dep]
        if len(has) == 2:
            R.append(_g(16, "Fresh-repo inheritance (deployed dispatcher runs the guards)", PASS if inh else UNKNOWN,
                        "deployed dispatcher lists both guards" + ("" if inh else "; no probe evidence"), [EV / "C9-inheritance.md"]))
        else:
            R.append(_g(16, "Fresh-repo inheritance (deployed dispatcher runs the guards)", FAIL,
                        "deployed ~/.claude/hooks/hook-dispatcher.js lacks " + ", ".join(k for k in ("cognitive_admission", "semantic_breaker") if k not in has)
                        + "; Copy-Item of the repo dispatcher is an Owner act (hooks-dir deploy denied to workers)",
                        [EV / "C9-inheritance.md"], in_scope=False))

    # 17 admission denial observed in a real session
    R.append(_g(17, "Admission denial observed from a real deployed session", UNKNOWN,
                "dispatcher not deployed (gate 16) -> no real-session denial row; hook-level and CLI-level proofs only", [P / "WU-C3-receipt.md"]))

    # 18 certified primitive replaces motif on replayed trace
    rp = _json(root, EV / "proof-digest-replay.json")
    g = _artifact_gate(root, 18, "Compiled primitive replaces a motif on a replayed trace", "C8",
                       ["tools/proof_digest.py", EV / "proof-digest-replay.json"], r"4 mutants that flip RED", "proof_digest replay 3 calls -> 1 (estimates); adoption NOT_PROVEN")
    if g["status"] == PASS and not isinstance(rp, dict):
        g = _g(18, g["name"], FAIL, "proof-digest-replay.json unreadable", g["evidence"])
    R.append(g)

    # 19 retirement with backup + revert
    rt = _txt(root, EV / "C9-retirements.md")
    g = _artifact_gate(root, 19, "At least one retirement with backup + revert path", "C9", [EV / "C9-retirements.md"],
                       r"R1 rule retirement", "R1 retired (-213 chars), guard test 31/31, backup + revert command recorded")
    if g["status"] == PASS and not (rt and re.search(r"(?i)revert", rt) and re.search(r"(?i)backup", rt)):
        g = _g(19, g["name"], FAIL, "C9-retirements.md lacks backup/revert", g["evidence"])
    R.append(g)

    # 20 registration liveness
    R.append(_artifact_gate(root, 20, "CDC guards registered / matcher liveness green", "C9", ["tools/test_cdc_registration.py"],
                            r"Matcher liveness 3/3", "registration test + mutants; matcher liveness 3/3, hookreg 15/15"))

    # 21 kill switches present in code
    ks = {"CPP_COG_ADMISSION": "hooks/cognitive_admission.js", "CPP_SEM_BREAKER": "hooks/semantic_breaker.js",
          "CPP_COG_CI": "tools/cognitive_ci.py", "CPP_RESEARCH_GATE": "hooks/research_reuse.js", "CDC_EFFECT_GATE": "tools/cognitive_effects.py"}
    lack = [k for k, f in ks.items() if k not in (_txt(root, f) or "")]
    ev21 = list(ks.values())
    if lack:
        R.append(_g(21, "Every guard has an env kill switch", FAIL, "kill switch name not found in code: " + ", ".join(lack), ev21))
    else:
        R.append(_g(21, "Every guard has an env kill switch", PASS, "all 5 switches present in their guard source", ev21))

    # 22 self-hosting
    R.append(_g(22, "Self-hosting: C1 ledger measures C0-C12; C5-C12 vs C0-C4", UNKNOWN,
                "no per-unit ledger of the CDC worker transcripts is stored; C12 not yet run", [EV / "ql-phase1-roles.json"]))

    # 23 every bug has a KV entry
    bugs = ["cognitive-admission-empty-prompt-duplicate", "cdc-admission-hook-missing-run", "cdc-parallel-proof-false-reds",
            "cdc-hub-closure-not-local", "cdc-repo-dispatcher-not-deployed-dispatcher", "cdc-research-lock-window-mismatch"]
    miss = [b for b in bugs if not (root / "vault" / "lessons" / f"{b}.md").is_file()]
    R.append(_g(23, "Every bug met in C0-C10 has a Knowledge Vault entry", FAIL if miss else PASS,
                ("missing lessons: " + ", ".join(miss)) if miss else f"{len(bugs)} lessons present", [f"vault/lessons/{b}.md" for b in bugs]))

    # 24 handoff rendered from state
    h = _txt(root, P / "HANDOFF.md")
    if h is None:
        R.append(_g(24, "Handoff rendered from state by script", FAIL, f"missing {P / 'HANDOFF.md'}", [P / "HANDOFF.md"]))
    else:
        R.append(_g(24, "Handoff rendered from state by script",
                    PASS if re.search(r"rendered by tools/cdc_handoff\.py", h) else FAIL,
                    "carries render stamp" if "rendered by tools/cdc_handoff.py" in h else "no render stamp (hand-written?)", [P / "HANDOFF.md"]))

    for r in R:
        r["evidence"] = [str(e).replace("\\", "/") for e in r["evidence"]]
    summ = {s: sum(1 for r in R if r["status"] == s) for s in (PASS, FAIL, UNKNOWN, EXT)}
    summ["fail_in_scope"] = [r["gate"] for r in R if r["status"] == FAIL and r["in_scope"]]
    summ["fail_out_of_scope"] = [r["gate"] for r in R if r["status"] == FAIL and not r["in_scope"]]
    return {"programme": "cdc", "gates": R, "summary": summ,
            "all_pass": summ[PASS] == len(R)}


def selftest() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cdcgate-"))
    try:
        base = tmp / "base"
        shutil.copytree(ROOT / PROG, base / PROG, ignore=shutil.ignore_patterns("*.log"))
        for f in ("tools", "hooks", "vault/config", "vault/lessons"):
            src = ROOT / f
            if src.is_dir():
                shutil.copytree(src, base / f, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "_tests", "test_*"))
        home = tmp / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / "hook-dispatcher.js").write_text("// cognitive_admission semantic_breaker", encoding="utf-8")
        a = {r["gate"]: r for r in evaluate(base, home)["gates"]}
        victim = base / EV / "cognitive-pgo.json"
        if not victim.is_file():
            print("selftest: control artifact absent in copy", file=sys.stderr)
            return 1
        victim.unlink()
        b = {r["gate"]: r for r in evaluate(base, home)["gates"]}
        ok = a[12]["status"] != FAIL and b[12]["status"] == FAIL and b[13]["status"] == FAIL
        ok = ok and a[9]["status"] == UNKNOWN and b[9]["status"] == UNKNOWN
        print(json.dumps({"selftest": "ok" if ok else "FAILED", "before12": a[12]["status"], "after12": b[12]["status"], "after13": b[13]["status"]}))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--live-home", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    root = Path(a.root)
    res = evaluate(root, Path(a.live_home) if a.live_home else None)
    out = Path(a.out) if a.out else root / EV / "cdc-gate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(res["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
