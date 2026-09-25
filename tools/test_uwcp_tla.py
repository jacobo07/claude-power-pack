#!/usr/bin/env python3
"""V-TLA-* gate: model-check the UWCP concurrency core (uwcp-assimilation X2).

Four outcomes, never collapsed:
  PASS               TLC exit 0, every action exercised, a state floor met
  SUBJECT_VIOLATION  TLC exit 10-14, with the violated property named
  VERIFIER_FAILED    any other exit (parse/config/system errors, bad flags)
  UNJUDGED           no JVM or no pinned jar on this host -- never a PASS

The target config must PASS. Each other config encodes a behaviour we predicted
BEFORE running TLC and must fail on the named property; a model that failed to
find them would be refused, because a spec that cannot go red proves nothing.
Counterexample traces are written to vault/specs/tla/counterexamples/ so the UWCP
pane can replay each as a failing Python test against the code (conformance link;
the model alone proves the model, not the code).

Dev-only dependency: tla2tools.jar v1.7.4 (MIT), outside git, pinned by sha256.
GitHub published no digest for this 2024 asset, so the pin is trust-on-first-use
(size matched the release metadata: 2,274,532 bytes). Flags are those of TLC 2.19
(v1.7.4): it has neither -noGenerateSpecTE nor -dumpTrace, which master has.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TLA = ROOT / "vault" / "specs" / "tla"
CEX = TLA / "counterexamples"
JAR = Path(os.environ.get("UWCP_TLA_JAR", r"C:\Users\User\Apps\tla\tla2tools-1.7.4.jar"))
JAR_SHA256 = "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
JAVA_CANDIDATES = (os.environ.get("UWCP_JAVA", ""), r"C:\Users\User\Apps\jdk-17\bin\java.exe", "java")

MIN_DISTINCT_STATES = 200            # base config measured 417 on 2026-09-25
EXPECT = {                           # cfg -> (outcome, property that must be named)
    "UWCP.cfg": ("PASS", ""),
    "UWCP_pre_cf4d71b.cfg": ("SUBJECT_VIOLATION", "ReceiptOnlyForOpenEpoch"),
    "UWCP_current.cfg": ("SUBJECT_VIOLATION", "AtMostOneLiveExecutor"),
    "UWCP_nostopevidence.cfg": ("SUBJECT_VIOLATION", "AtMostOneLiveExecutor"),
    "UWCP_nobound.cfg": ("SUBJECT_VIOLATION", "EveryRunningEpochEndsOrBlocks"),
    "UWCP_mutant_nofence.cfg": ("SUBJECT_VIOLATION", "StaleFenceCannotAdvance"),
    "UWCP_mutant_resumeaftercancel.cfg": ("SUBJECT_VIOLATION", "CancelledNeverResumes"),
}
# The mechanism, not only the property: two cfgs violate the same invariant through
# different actions, and a trace through the wrong one would be the wrong finding.
MECHANISM = {"UWCP_current.cfg": "FalseLost", "UWCP_nostopevidence.cfg": "Expire",
             "UWCP_pre_cf4d71b.cfg": "Receipt", "UWCP_mutant_nofence.cfg": "Effect",
             "UWCP_mutant_resumeaftercancel.cfg": "Resume"}
ACTIONS = ("Begin", "Launch", "Effect", "Finish", "Crash", "NodeUnreachable", "ObserveOK",
           "ObserveExit", "Expire", "Harvest", "Bound", "Receipt", "Cancel", "Pause", "Resume", "Done")

passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def find_java() -> str:
    for c in JAVA_CANDIDATES:
        if c and (Path(c).is_file() or shutil.which(c)):
            return c
    return ""


def classify(code: int) -> str:
    if code == 0:
        return "PASS"
    if 10 <= code <= 14:
        return "SUBJECT_VIOLATION"
    return "VERIFIER_FAILED"


def violated(out: str) -> str:
    m = re.search(r"Error: (?:Invariant|Action property) (\w+) is violated", out)
    if m:
        return m.group(1)
    # TLC 2.19 does not name the violated liveness property. Attribution is by
    # construction instead: a liveness cfg lists exactly ONE property.
    if re.search(r"Error: Temporal properties were violated", out):
        return "TEMPORAL"
    return ""


def run(java: str, cfg: str, workdir: Path) -> tuple[str, str, int]:
    cmd = [java, "-XX:+UseParallelGC", "-cp", str(JAR), "tlc2.TLC", "-workers", "auto",
           "-config", str(TLA / cfg), "-coverage", "1", "-metadir", str(workdir / cfg),
           "-cleanup", str(TLA / "UWCP.tla")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=900)
    return classify(p.returncode), p.stdout + p.stderr, p.returncode


def main() -> int:
    java = find_java()
    if not java or not JAR.is_file():
        print(f"  UNJUDGED V-TLA: java={java or 'absent'} jar={'present' if JAR.is_file() else 'absent'}")
        print("TLA_UNJUDGED=1  (not a PASS: nothing was model-checked on this host)")
        return 2
    digest = hashlib.sha256(JAR.read_bytes()).hexdigest()
    if digest != JAR_SHA256:
        print(f"  VERIFIER_FAILED V-TLA-JAR-PIN: jar sha256 {digest} != pinned {JAR_SHA256}")
        return 3
    check("V-TLA-JAR-PIN", True, f"tla2tools.jar matches the pinned sha256 ({JAR})", "")

    work = Path(tempfile.mkdtemp(prefix="uwcp-tlc-"))
    CEX.mkdir(parents=True, exist_ok=True)
    for cfg, (want, prop) in EXPECT.items():
        outcome, out, code = run(java, cfg, work)
        name = violated(out)
        gate = "V-TLA-" + cfg.removesuffix(".cfg").upper().replace("_", "-")
        if want == "PASS":
            m = re.search(r"(\d+) distinct states found", out)
            distinct = int(m.group(1)) if m else 0
            cov = dict(re.findall(r"^<(\w+) line \d+, col \d+ to line \d+, col \d+ of module UWCP>: "
                                  r"\d+:(\d+)", out, re.M))
            unexercised = [a for a in ACTIONS if int(cov.get(a, 0)) == 0]
            check(gate, outcome == "PASS", f"target design holds every property (exit {code})",
                  f"outcome={outcome} exit={code} violated={name} tail={out[-600:]!r}")
            check("V-TLA-STATE-FLOOR", distinct >= MIN_DISTINCT_STATES,
                  f"{distinct} distinct states explored (floor {MIN_DISTINCT_STATES})",
                  f"only {distinct} distinct states")
            check("V-TLA-COVERAGE", not unexercised,
                  f"all {len(ACTIONS)} actions were exercised -- the green is not vacuous",
                  f"never taken: {unexercised}")
            continue
        named_ok = (name == prop) or (prop == "EveryRunningEpochEndsOrBlocks" and name == "TEMPORAL")
        check(gate, outcome == want and named_ok,
              f"predicted defect found: {prop} violated (exit {code})",
              f"outcome={outcome} exit={code} named={name!r} want {prop}; tail={out[-600:]!r}")
        trace = out[out.find("Error:"):] if "Error:" in out else out[-4000:]
        mech = MECHANISM.get(cfg)
        if mech:
            steps = re.findall(r"^State \d+: <(\w+) line", trace, re.M)
            check(gate + "-MECHANISM", mech in steps,
                  f"the counterexample goes through {mech} ({' -> '.join(steps)})",
                  f"expected {mech} in the trace, got {steps}")
        (CEX / (cfg.removesuffix(".cfg") + ".txt")).write_text(
            f"# TLC counterexample for {cfg} (predicted: {prop})\n{trace}", encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(f"TLA_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
