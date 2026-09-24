"""product-demo CLI: the one entry point agents and humans use.

    python -m modules.product_demo.cli run   --spec S.json --out DIR [--viewport NAME ...] [--app-repo PATH]
    python -m modules.product_demo.cli probe --spec S.json --manifest DIR/<vp>/manifest.json [--out DIR]
    python -m modules.product_demo.cli check-spec --spec S.json

Exit codes: 0 VALID / CURRENT, 3 refused or invalid or STALE, 4 UNKNOWN or verifier failure, 2 usage.
Every heavy step (browser capture, render) runs as a bounded child whose whole
process tree dies on timeout (runner.run_bounded).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.cognitive_os.loop_budget import LoopBudget, LoopState, admit_loop, kill_check  # noqa: E402
from modules.product_demo import manifest as mf  # noqa: E402
from modules.product_demo import stage, timeline, validate  # noqa: E402
from modules.product_demo.runner import run_bounded  # noqa: E402
from modules.product_demo.spec import SpecError, load  # noqa: E402

PP_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_TIMEOUT_S = 600
RENDER_TIMEOUT_S = 1800
MAX_REVISIONS = 3
RENDER_ATTEMPTS = 2
EXIT_OK, EXIT_USAGE, EXIT_BAD, EXIT_UNKNOWN = 0, 2, 3, 4


def native_crash(rc) -> bool:
    """True when a Windows process died on an NTSTATUS error (0xC0000000..0xCFFFFFFF),
    which Python reports as a negative returncode."""
    return rc is not None and 0xC0000000 <= (rc & 0xFFFFFFFF) <= 0xCFFFFFFF


def _py() -> str:
    return sys.executable


def capture(spec_path: Path, viewport: str, out: Path, probe: bool = False):
    argv = [_py(), "-m", "modules.product_demo.capture", "--spec", str(spec_path), "--viewport", viewport,
            "--out", str(out)] + (["--probe"] if probe else [])
    res = run_bounded(argv, timeout_s=CAPTURE_TIMEOUT_S, cwd=str(PP_ROOT))
    tel_path = out / "telemetry.json"
    tel = json.loads(tel_path.read_text(encoding="utf-8")) if tel_path.is_file() else None
    return res, tel


def revise(tel: dict, output: dict) -> tuple:
    """Bounded self-correction of presentation timing only. Admitted by loop_budget;
    the cap, the oscillation check and the no-progress stop are enforced here
    because loop_budget.kill_check does not compare iterations with its cap."""
    budget = LoopBudget(max_iterations=MAX_REVISIONS, stop_gates=["no TIMING defects remain"],
                        checkpoint=True, resume_plan=True)
    verdict = admit_loop(budget)
    if verdict.verdict != "proceed":
        raise RuntimeError(f"revision loop refused by loop_budget: {verdict.reasons}")
    overrides: dict = {}
    tl = timeline.build(tel, output, overrides)
    history, seen = [], set()
    state = LoopState()
    prev_short = None
    for i in range(MAX_REVISIONS):
        timing = [d for d in tl.defects if d["class"] == "TIMING"]
        if not timing:
            break
        fingerprint = json.dumps(overrides, sort_keys=True)
        if fingerprint in seen:
            history.append({"iteration": i, "stop": "oscillation: revision repeated"})
            break
        seen.add(fingerprint)
        short = sum(d["short_ms"] for d in timing)
        if prev_short is not None and short >= prev_short:
            state.consecutive_failures += 1
        prev_short = short
        kv = kill_check(state, budget)
        if kv.kill:
            history.append({"iteration": i, "stop": f"kill_check: {kv.reasons}"})
            break
        for d in timing:
            overrides[d["step"]] = overrides.get(d["step"], 0) + d["short_ms"] + 120
        history.append({"iteration": i + 1, "lengthened": {d["step"]: d["short_ms"] + 120 for d in timing}})
        state.iterations_done = i + 1
        tl = timeline.build(tel, output, overrides)
    return tl, history


def encode_extras(mp4: Path, formats: list, poster_t: float) -> tuple:
    outs, notes = {}, []
    ff = validate.ffmpeg_exe()
    if "poster" in formats:
        poster = mp4.with_suffix(".poster.png")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{poster_t:.3f}", "-i", str(mp4),
                        "-frames:v", "1", str(poster)], capture_output=True, timeout=120)
        if poster.is_file():
            outs["poster"] = poster
        else:
            notes.append("poster extraction produced no file")
    if "webm" in formats:
        webm = mp4.with_suffix(".webm")
        r = run_bounded([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4), "-c:v", "libvpx-vp9",
                         "-b:v", "0", "-crf", "34", "-row-mt", "1", "-deadline", "good", "-an", str(webm)],
                        timeout_s=RENDER_TIMEOUT_S)
        if r.ok and webm.is_file():
            outs["webm"] = webm
        else:
            notes.append(f"webm encode {r.outcome}: {r.stderr.strip()[-300:]}")
    return outs, notes


def run_viewport(spec, spec_path: Path, vp, out_root: Path, app_repo: Path | None) -> dict:
    out = out_root / vp.name
    out.mkdir(parents=True, exist_ok=True)
    res, tel = capture(spec_path, vp.name, out)
    if tel is None:
        return {"viewport": vp.name, "outcome": "CAPTURE_FAILED", "run": res.outcome,
                "stderr": res.stderr.strip()[-800:]}
    if tel["outcome"] != "ok":
        return {"viewport": vp.name, "outcome": "REFUSED", "refusal": tel["refusal"]}
    output = vars(spec.output)
    tl, revisions = revise(tel, output)
    tld = tl.to_dict()
    (out / "timeline.json").write_text(json.dumps(tld, indent=2), encoding="utf-8")
    host = spec.base_url.split("//", 1)[-1].split("/", 1)[0]
    html = stage.compose(tld, out, stage=vp.stage, fps=spec.output.fps, title=spec.title,
                         accent=spec.brand_accent, host=host)
    mp4 = out / f"{spec.id}_{vp.name}.mp4"
    attempts = []
    for _ in range(RENDER_ATTEMPTS):
        r = run_bounded([_py(), str(PP_ROOT / "skills/motion-promo/scripts/render_film.py"), str(html),
                         "--out", str(mp4)], timeout_s=RENDER_TIMEOUT_S)
        attempts.append({"outcome": r.outcome, "rc": r.returncode, "elapsed_s": round(r.elapsed_s, 1)})
        # Retry ONLY a native process crash (NTSTATUS 0xC...: measured 0xC000070A in
        # ntdll on a memory-starved host, gone on rerun). A refusal from render_film
        # itself (rc 2) or a timeout is deterministic enough to report, not repeat.
        if r.ok or not native_crash(r.returncode):
            break
    revisions.append({"render_attempts": attempts})
    if not r.ok:
        return {"viewport": vp.name, "outcome": "RENDER_FAILED", "run": r.outcome, "rc": r.returncode,
                "elapsed_s": round(r.elapsed_s, 1), "stdout": r.stdout.strip()[-800:],
                "stderr": r.stderr.strip()[-800:]}
    payoff = tld["segments"][-1]["start_ms"] / 1000 + 0.2
    extras, notes = encode_extras(mp4, spec.output.formats, payoff)
    layout = json.loads((out / f"stage_{vp.name}.layout.json").read_text(encoding="utf-8"))
    verdict = validate.validate(mp4, layout=layout, timeline=tld, telemetry=tel, output=output,
                                canvas=stage.CANVAS[vp.stage])
    for n in notes:
        verdict.defects.append({"class": "FORMAT_UNAVAILABLE", "detail": n})
        if verdict.outcome == validate.VALID:
            verdict.outcome = validate.SUBJECT_INVALID
    manifest = mf.build(spec=spec, viewport=vp.name, capture_dir=out, telemetry=tel, timeline=tld,
                        outputs={"mp4": mp4, **extras}, verdict=verdict.to_dict(), app_repo=app_repo,
                        revisions=revisions)
    mf.write(manifest, out / "manifest.json")
    return {"viewport": vp.name, "outcome": verdict.outcome, "mp4": str(mp4),
            "defects": verdict.defects, "revisions": revisions}


def cmd_run(a) -> int:
    spec = load(a.spec)
    wanted = a.viewport or [v.name for v in spec.viewports]
    unknown = set(wanted) - {v.name for v in spec.viewports}
    if unknown:
        raise SpecError(f"unknown viewport(s) {sorted(unknown)}")
    out_root = Path(a.out)
    results = [run_viewport(spec, Path(a.spec), v, out_root, Path(a.app_repo) if a.app_repo else None)
               for v in spec.viewports if v.name in wanted]
    print(json.dumps(results, indent=2, ensure_ascii=False))
    outcomes = {r["outcome"] for r in results}
    if outcomes == {validate.VALID}:
        return EXIT_OK
    if validate.VERIFIER_FAILED in outcomes or "CAPTURE_FAILED" in outcomes or "RENDER_FAILED" in outcomes:
        return EXIT_UNKNOWN
    return EXIT_BAD


def cmd_probe(a) -> int:
    man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else Path(a.manifest).parent / "probe"
    res, tel = capture(Path(a.spec), man["viewport"], out, probe=True)
    if tel is None:
        result = {"state": "UNKNOWN", "reasons": [f"probe run {res.outcome}: {res.stderr.strip()[-300:]}"]}
    else:
        result = mf.staleness(man, tel)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return {"CURRENT": EXIT_OK, "STALE": EXIT_BAD}.get(result["state"], EXIT_UNKNOWN)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="product-demo", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--spec", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--viewport", action="append")
    r.add_argument("--app-repo")
    p = sub.add_parser("probe")
    p.add_argument("--spec", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out")
    c = sub.add_parser("check-spec")
    c.add_argument("--spec", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check-spec":
            s = load(a.spec)
            print(f"OK {s.id}: {len(s.steps)} steps, viewports {[v.name for v in s.viewports]}, sha256 {s.sha256[:12]}")
            return EXIT_OK
        return cmd_run(a) if a.cmd == "run" else cmd_probe(a)
    except SpecError as exc:
        print(f"SPEC_INVALID: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
