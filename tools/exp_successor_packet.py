"""Experiment exp-successor-packet-001: does a fresh successor do better with a SOURCE PACKET
REFERENCE on its card than with the card alone? (T8 item 31; decides item 12's consumer.)

Two parts, both recorded under vault/experiments/exp-successor-packet-001/:

  dryrun   Placement arithmetic over every REAL mission card on this host: card bytes today,
           card bytes with a packet reference, the packet's own bytes, and what inlining the
           packet into the remaining headroom would LOSE. No model call.
  prepare  Builds the cases from this repo's real source, persists each case's packet whole,
           renders the two prompts (baseline = the successor card as gsd_mission renders it;
           candidate = the same card + the packet reference), hashes everything and
           PREREGISTERS. Must be committed before `run`.
  run      One real headless `claude -p` successor per (case, variant), read-only tools only.
           The source must still hash to the registered bytes or the run is refused.
  grade    Deterministic substring rubric derived from the source at prepare time. The grader
           never receives the variant name (blinded) and is not the worker (independent).
  analyze  The vendored analysis, verbatim.

    python tools/exp_successor_packet.py dryrun|prepare|run|grade|analyze
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gsd_mission as gm  # noqa: E402
import paired_experiment as pe  # noqa: E402
import source_packet as sp  # noqa: E402

# 001 was registered with whole-file packets and WITHDRAWN before any run: inspection showed
# neither candidate packet held its answer (verified_reuse.py cut at the excerpt budget,
# gsd_mission.py blocked whole by the vendor's credential-line filter). See its WITHDRAWN.md.
EXP_ID = "exp-successor-packet-002"
WORKER = {"route": "claude-code-headless", "requestedModel": "default", "config": {"mode": "print", "tools": "read-only"}}
RUN_TIMEOUT_S = 420


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


# ---------------------------------------------------------------- cases (real source, this repo)
# The candidate packet is the REGION the work is about (an anchor with surrounding context), the
# shape a predecessor's handoff can name; it is not the answer line alone.
# Case files must be ones the vendor's credential-line filter does not block whole: measured
# 2026-09-28, it blocks 441 of 1,091 Python files here (322 only for "pass" before ":" or "="),
# routing_metrics.py and gsd_mission.py among them. That limit is recorded, not worked around.
def _cases() -> list[dict]:
    pg_src = (ROOT / "tools" / "plan_graph_check.py").read_text(encoding="utf-8")
    hash_fn = re.search(r'p = f"\[repo-\{hashlib\.(\w+)\(', pg_src).group(1)
    return [
        {"id": "reuse-refusal", "split": "training", "paths": ["tools/verified_reuse.py"],
         "selectors": [{"path": "tools/verified_reuse.py", "anchor": 'if v.get("accepted") is not False',
                        "beforeLines": 30, "afterLines": 5}],
         "question": ("In tools/verified_reuse.py, lookup() can refuse a hit that the vendored module "
                      "returned. Quote the exact condition it checks and name the constant it returns."),
         "rubric": ["needsFreshReview", "REFUSED"]},
        {"id": "foreign-repo-key", "split": "holdout", "paths": ["tools/plan_graph_check.py"],
         "selectors": [{"path": "tools/plan_graph_check.py", "anchor": 'p = f"[repo-', "beforeLines": 30, "afterLines": 3}],
         "question": ("In tools/plan_graph_check.py, _owns() gives a file that lives in ANOTHER repository its own "
                      "namespace. Quote the exact line that builds that namespaced key and name the hash function."),
         "rubric": ["[repo-", hash_fn]},
    ]


def _card(note: str) -> str:
    rec = {"epoch": 2, "mission_id": "m-experiment01", "cwd": str(ROOT), "resume_command": "/gsd-autonomous",
           "workstream": None, "directives": [], "note": note, "work_dir": None}
    return gm.render_card(rec, {"head": "(experiment)", "dirty": 0, "recent": []}, "")


def _prompt(case: dict, ref: dict | None) -> str:
    note = f"Next step for this epoch: answer one question about the code. {case['question']}"
    card = _card(note)
    if ref is not None:
        card = card + "\n\n" + sp.card_reference(ref)
    return (card + "\n\nTASK: " + case["question"] + "\nAnswer in one short paragraph, quoting code exactly. "
            "Do not edit, create or delete any file. Stop after answering.")


# ---------------------------------------------------------------- dry run over real cards
def dryrun() -> dict:
    rows = []
    for f in sorted(glob.glob(os.path.expanduser("~/.claude/state/gsd-mission-m-*.json"))):
        try:
            rec = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        card = rec.get("card")
        cwd = rec.get("work_dir") or rec.get("cwd")
        if not card or not cwd or not Path(cwd).is_dir():
            continue
        g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
        r = subprocess.run([g, "-C", cwd, "log", "-1", "--name-only", "--format="], capture_output=True, text=True, timeout=20)
        files = [p for p in (r.stdout or "").splitlines() if p.strip() and (Path(cwd) / p).is_file()][:8]
        if not files:
            continue
        pk = sp.build(cwd, files)
        packet_bytes = len(pk.prompt.encode("utf-8"))
        card_bytes = len(card.encode("utf-8"))
        ref_block = sp.card_reference({"verdict": pk.verdict, "files": len(files), "bytes": packet_bytes,
                                       "sha256": "0" * 64, "path": str(Path.home() / ".claude" / "state" /
                                                                       "source-packets" / ("0" * 64 + ".txt")),
                                       "gaps": pk.gaps})
        headroom = gm.CARD_MAX_BYTES - card_bytes
        rows.append({"mission": rec["mission_id"], "files": len(files), "card_bytes": card_bytes,
                     "packet_bytes": packet_bytes, "packet_verdict": pk.verdict,
                     "reference_card_bytes": card_bytes + 2 + len(ref_block.encode("utf-8")),
                     "headroom": headroom, "inline_lost_bytes": max(0, packet_bytes - headroom)})
    lost = [r for r in rows if r["inline_lost_bytes"] > 0]
    summary = {"cases": len(rows), "card_cap": gm.CARD_MAX_BYTES,
               "reference_card_max": max((r["reference_card_bytes"] for r in rows), default=None),
               "reference_fits_all": all(r["reference_card_bytes"] <= gm.CARD_MAX_BYTES for r in rows),
               "inline_would_truncate": len(lost),
               "inline_lost_bytes_total": sum(r["inline_lost_bytes"] for r in lost),
               "packet_bytes_total": sum(r["packet_bytes"] for r in rows), "rows": rows}
    pe.save(EXP_ID, "dryrun.json", summary)
    return summary


# ---------------------------------------------------------------- preregistration
def prepare() -> dict:
    cases, spec_cases, material = _cases(), [], {}
    for c in cases:
        ref = sp.persist(str(ROOT), c["paths"], selectors=c.get("selectors"))
        if ref.get("verdict") != sp.COMPLETE:
            # A candidate packet that does not hold its region would measure a broken packet, not
            # the placement -- the defect that voided 001. Refuse to register rather than run it.
            raise pe.ExperimentError(f"{c['id']}: candidate packet is {ref.get('verdict')}: {ref.get('gaps')}")
        if ref.get("verdict") == sp.UNJUDGED:
            raise pe.ExperimentError(f"{c['id']}: packet could not be built: {ref.get('gaps')}")
        prompts = {"baseline": _prompt(c, None), "candidate": _prompt(c, ref)}
        source = b"".join((ROOT / p).read_bytes() for p in c["paths"])
        rubric = {"required": c["rubric"]}
        contract = {"question": c["question"], "paths": c["paths"], "readOnly": True}
        spec_cases.append({"id": c["id"], "split": c["split"], "contractSha256": _sha(json.dumps(contract, sort_keys=True)),
                           "sourceSha256": _sha(source), "rubricSha256": _sha(json.dumps(rubric, sort_keys=True)),
                           "promptSha256": {k: _sha(v) for k, v in prompts.items()}, "maxScore": len(c["rubric"])})
        material[c["id"]] = {"prompts": prompts, "rubric": rubric, "packet": ref, "paths": c["paths"]}
    spec = {"schema": "genesis-paired-experiment-v1", "id": EXP_ID, "createdAt": pe.js_now(), "worker": WORKER,
            "scope": "diagnostic", "qualityMetric": "normalized-score", "cases": spec_cases, "maxAttemptsPerRun": 1,
            "targets": {"qualityMultiplier": 1, "tokenReduction": 0.05}}
    reg = pe.preregister(spec)
    pe.save(EXP_ID, "material.json", material)
    return reg


# ---------------------------------------------------------------- runs
def _run_one(prompt: str) -> dict:
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    t0 = time.time()
    try:
        # Identical flags for both arms. The packet dir is readable (as it is for a real worker) and
        # the one command the reference names may run; every write tool is refused, and any other
        # shell command needs a permission nobody is there to grant, so it is denied.
        p = subprocess.run([exe, "-p", "--output-format", "json", "--no-session-persistence",
                            "--add-dir", str(sp.packets_dir()),
                            "--allowedTools", "Bash(python tools/source_packet.py --verify:*)",
                            "--disallowedTools", "Edit", "Write", "NotebookEdit",
                            # the Owner's settings may default to a bypass mode; pin the one in
                            # which the denials above actually hold
                            "--permission-mode", "default"],
                           input=prompt, capture_output=True, text=True, encoding="utf-8",
                           cwd=str(ROOT), timeout=RUN_TIMEOUT_S)
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired:
        return {"status": "failed", "elapsedMs": round((time.time() - t0) * 1000), "reason": "timeout"}
    elapsed = round((time.time() - t0) * 1000)
    try:
        j = json.loads(out)
    except ValueError:
        return {"status": "failed", "elapsedMs": elapsed, "reason": f"rc={rc} unparseable output: {out[:200]!r}"}
    u = j.get("usage") or {}
    inp = int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
    models = list((j.get("modelUsage") or {}).keys())
    text = j.get("result") or ""
    ok = rc == 0 and not j.get("is_error") and bool(text.strip())
    return {"status": "passed" if ok else "failed", "elapsedMs": elapsed, "text": text,
            "usage": {"input_tokens": inp, "cached_input_tokens": int(u.get("cache_read_input_tokens") or 0),
                      "output_tokens": int(u.get("output_tokens") or 0)} if u else None,
            "actualModel": models[0] if len(models) == 1 else None, "num_turns": j.get("num_turns"),
            "reason": None if ok else f"rc={rc} is_error={j.get('is_error')} {str(j.get('result'))[:160]}"}


def run() -> list:
    reg = pe.load(EXP_ID, "registration.json")
    material = pe.load(EXP_ID, "material.json")
    if reg is None or material is None:
        raise pe.ExperimentError("prepare first (and commit the registration)")
    runs = pe.load(EXP_ID, "runs.json", default=[])
    outputs = pe.load(EXP_ID, "outputs.json", default={})
    done = {(r["caseId"], r["variant"]) for r in runs}
    for case in reg["spec"]["cases"]:
        m = material[case["id"]]
        source = b"".join((ROOT / p).read_bytes() for p in m["paths"])
        if _sha(source) != case["sourceSha256"]:
            raise pe.ExperimentError(f"{case['id']}: source moved since registration; this experiment is void")
        for variant in ("baseline", "candidate"):
            if (case["id"], variant) in done:
                continue
            started = pe.js_now()
            res = _run_one(m["prompts"][variant])
            text = res.pop("text", "") or ""
            attempt = {"sequence": 1, "status": res["status"], "actualModel": res.get("actualModel"),
                       "usage": res.get("usage"), "elapsedMs": res["elapsedMs"]}
            if res["status"] == "passed":
                attempt["outputSha256"] = _sha(text)
            runs.append({"caseId": case["id"], "variant": variant, "registrationSha256": reg["sha256"],
                         "promptSha256": case["promptSha256"][variant], "sourceSha256": case["sourceSha256"],
                         "worker": WORKER, "startedAt": started, "attempts": [attempt], "historyComplete": True})
            outputs[f"{case['id']}:{variant}"] = {"text": text, "reason": res.get("reason"), "num_turns": res.get("num_turns")}
            pe.save(EXP_ID, "runs.json", runs)
            pe.save(EXP_ID, "outputs.json", outputs)
            print(f"{case['id']}:{variant} {res['status']} {res['elapsedMs']} ms usage={res.get('usage')} "
                  f"turns={res.get('num_turns')} {res.get('reason') or ''}")
    return runs


# ---------------------------------------------------------------- blinded deterministic grading
def _score(text: str, required: list[str]) -> int:
    """Blinded by construction: it is given the output and the rubric, never the variant."""
    return sum(1 for s in required if s in text)


def grade() -> list:
    reg = pe.load(EXP_ID, "registration.json")
    material = pe.load(EXP_ID, "material.json")
    runs = pe.load(EXP_ID, "runs.json", default=[])
    outputs = pe.load(EXP_ID, "outputs.json", default={})
    grades = []
    for r in runs:
        last = r["attempts"][-1]
        if last["status"] != "passed":
            continue
        text = outputs[f"{r['caseId']}:{r['variant']}"]["text"]
        required = material[r["caseId"]]["rubric"]["required"]
        score = _score(text, required)
        evidence = {"required": required, "found": [s for s in required if s in text], "outputSha256": _sha(text)}
        case = next(c for c in reg["spec"]["cases"] if c["id"] == r["caseId"])
        grades.append({"caseId": r["caseId"], "variant": r["variant"], "registrationSha256": reg["sha256"],
                       "rubricSha256": case["rubricSha256"], "independent": True, "blinded": True,
                       "reviewerId": "deterministic-substring-grader", "evidenceSha256": _sha(json.dumps(evidence, sort_keys=True)),
                       "score": score, "outputSha256": last["outputSha256"]})
    pe.save(EXP_ID, "grades.json", grades)
    return grades


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else ""
    if cmd == "dryrun":
        s = dryrun()
        print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1))
    elif cmd == "prepare":
        r = prepare()
        print(f"REGISTERED {EXP_ID} sha256={r['sha256']} createdAt={r['spec']['createdAt']}")
    elif cmd == "run":
        run()
    elif cmd == "grade":
        for g in grade():
            print(f"{g['caseId']}:{g['variant']} score={g['score']}")
    elif cmd == "analyze":
        a = pe.analyze(EXP_ID)
        print(json.dumps({k: a[k] for k in ("complete", "quality", "workerTokens", "workerTokenReduction",
                                             "regressions", "targets", "warnings")}, indent=1))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
