#!/usr/bin/env python3
"""UWCP test job on GEX44, carried by the VPS dispatcher (job type `uwcp-test`).

    python3 uwcp_gex44_testjob.py <STAGE>

STAGE holds `repo.tar` (a `git archive` of the Power Pack at one commit) and this
file, both staged by the dispatcher with its md5 handshake. RULE-090: nothing
reaches GEX44 any other way. The job runs, on the validation plane:

  1. host facts (python, git, free memory, disk) -- the instrument's configuration;
  2. the Claude-provider suite three times (V-CLI-WAITS is a wall-clock gate that
     failed once on a starved laptop; three runs on an unstarved host say whether
     it is flaky or broken);
  3. the workspace-capsule suite once as the baseline, then the mutation drills.
     A drill is judged only if the baseline is green; otherwise it is INVALID.

Drills mutate the DISPOSABLE extracted copy, never a working tree, and restore by
bytes with a SHA-256 check anyway so each drill starts from the committed file.

Output: STAGE/run/results.json, STAGE/run/verdict.json and STAGE/verdict.json
(the dispatcher's completion check reads the pointer dir; its collector follows
the OUT= line), then `OUT=STAGE/run` as the last line of stdout.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

SUITE_TIMEOUT_S = 900
WS = "modules/gsd_x/goal/workspace.py"
WS_SUITE = "tools/test_uwcp_workspace.py"
CP_SUITE = "tools/test_gsd_x_goal_claude_providers.py"
CP_RUNS = 3

# (name, snippet, replacement, gate that must go red). Kept in step with
# tools/test_uwcp_workspace.py; a snippet that is not found exactly once is
# HARNESS-FAILED, never a verdict.
DRILLS = [
    ("M1-empty-index-seed", 'read-tree", base_tree, env=env)',
     'read-tree", "--empty", env=env)', "V-UWCP-WS-MODES-SEEDED"),
    ("M2-no-fsck", '"-c", "transfer.fsckObjects=true", "-c", "fetch.fsckObjects=true",\n',
     "\n", "V-UWCP-WS-FETCH-REFUSES-CREATION-CORRUPTION"),
    ("M3-no-size-first", '        if p.stat().st_size != part["size"]:',
     "        if False:", "V-UWCP-WS-TRUNCATED-SIZE-FIRST"),
    ("M4-env-always-differs",
     'env_differs = any(cap_env.get(k) != node_env.get(k) for k in ("autocrlf", "eol"))',
     "env_differs = True", "V-UWCP-WS-SAME-ENV-EOL-CHANGE-NON-EQUIVALENT"),
    ("M5-retire-first-pass", "        if cid in marked:", "        if True:",
     "V-UWCP-WS-RETENTION-TWO-PASS"),
    ("M6-baseline-foreign-ignored", "(p in baseline and p not in owned_set)", "False",
     "V-UWCP-WS-FOREIGN-EXCLUDED-REPORTED"),
    ("M7-dirty-target-allowed",
     '        if staged or unstaged:\n            raise HydrateError("target',
     '        if False:\n            raise HydrateError("target', "V-UWCP-WS-DIRTY-TARGET-REFUSED"),
    ("M8-scan-nothing-added", '    return b"\\n".join(keep)', '    return b""',
     "V-UWCP-WS-SECRET-CONTENT"),
]


def _sh(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return f"<{exc.__class__.__name__}>"


def _suite(repo: Path, rel: str) -> dict:
    t0 = time.monotonic()
    try:
        p = subprocess.run([sys.executable, rel], cwd=repo, capture_output=True, text=True,
                           timeout=SUITE_TIMEOUT_S,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        out, rc, timed_out = p.stdout + p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as exc:
        out, rc, timed_out = str(exc.stdout or ""), None, True
    fails = [ln.split()[1] for ln in out.splitlines() if ln.strip().startswith("FAIL ")
             and len(ln.split()) > 1]
    summary = [ln.strip() for ln in out.splitlines() if "_PASS=" in ln]
    return {"suite": rel, "rc": rc, "timed_out": timed_out, "seconds": round(time.monotonic() - t0),
            "fails": fails, "summary": summary[-1] if summary else "", "tail": out[-1500:]}


def main() -> int:
    stage = Path(sys.argv[1]).resolve()
    run, repo = stage / "run", stage / "repo"
    run.mkdir(parents=True, exist_ok=True)
    res: dict = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "host": {"hostname": platform.node(), "python": sys.version.split()[0],
                          "git": _sh("git", "--version"), "uname": " ".join(platform.uname()),
                          "free": _sh("free", "-m"), "df": _sh("df", "-h", str(stage))}}
    try:
        if repo.exists():
            shutil.rmtree(repo)
        with tarfile.open(stage / "repo.tar") as tar:
            for m in tar.getmembers():
                if m.name.startswith("/") or ".." in Path(m.name).parts:
                    raise RuntimeError(f"unsafe member {m.name}")
            tar.extractall(repo)
        res["repo_commit"] = (repo / "UWCP_COMMIT").read_text().strip() \
            if (repo / "UWCP_COMMIT").is_file() else ""

        res["claude_providers"] = [_suite(repo, CP_SUITE) for _ in range(CP_RUNS)]
        base = _suite(repo, WS_SUITE)
        res["workspace_baseline"] = base
        target = repo / WS
        orig = target.read_bytes()
        sha = hashlib.sha256(orig).hexdigest()
        # The archive must carry the commit's bytes. `git archive` under
        # core.autocrlf=true renders CRLF, which ran every suite on bytes no commit
        # holds and blinded the multi-line snippets (run uwc-20260925-172032).
        res["artifact_crlf"] = b"\r\n" in orig
        drills = []
        for name, old, new, gate in DRILLS:
            d = {"drill": name, "gate": gate}
            if res["artifact_crlf"]:
                d["verdict"] = "HARNESS-FAILED: artifact has CRLF -- not the commit's bytes"
            elif base["rc"] != 0:
                d["verdict"] = "INVALID: baseline suite not green"
            elif orig.count(old.encode()) != 1:
                d["verdict"] = f"HARNESS-FAILED: snippet occurs {orig.count(old.encode())} times"
            else:
                try:
                    target.write_bytes(orig.replace(old.encode(), new.encode()))
                    r = _suite(repo, WS_SUITE)
                finally:
                    target.write_bytes(orig)
                d["restored"] = hashlib.sha256(target.read_bytes()).hexdigest() == sha
                d["seconds"] = r["seconds"]
                if r["timed_out"]:
                    d["verdict"] = "INVALID: suite timed out"
                elif gate in r["fails"]:
                    d["verdict"] = "CAUGHT"
                elif r["rc"] != 0 or not r["summary"]:
                    # The suite died before judging: the mutant is detected, but not by
                    # the gate named for it -- a different claim, never SURVIVED
                    # (run uwc-20260925-172032 reported a KeyError crash as SURVIVED).
                    d["verdict"] = "DETECTED-BY-CRASH: named gate never judged"
                    d["tail"] = r["tail"][-400:]
                else:
                    d["verdict"] = "SURVIVED"
                    d["fails_seen"] = r["fails"]
            drills.append(d)
        res["drills"] = drills
        cp_rcs = [r["rc"] for r in res["claude_providers"]]
        verdict = {
            "job": "uwcp-test",
            "repo_commit": res["repo_commit"],
            "artifact_crlf": res["artifact_crlf"],
            "claude_providers_runs": [r["summary"] for r in res["claude_providers"]],
            "claude_providers_all_green": all(rc == 0 for rc in cp_rcs),
            "workspace_baseline": base["summary"],
            "drills": {d["drill"]: d["verdict"] for d in drills},
            "all_restored": all(d.get("restored", True) for d in drills),
        }
    except Exception as exc:  # noqa: BLE001 -- the job must still say what it could not do
        res["error"] = f"{exc.__class__.__name__}: {exc}"
        verdict = {"job": "uwcp-test", "harness_error": res["error"]}
    finally:
        shutil.rmtree(repo, ignore_errors=True)   # GEX44 disk is shared; keep only evidence
    res["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (run / "results.json").write_text(json.dumps(res, indent=2))
    body = json.dumps(verdict, indent=2)
    if "harness_error" not in verdict:
        (run / "verdict.json").write_text(body)
        (stage / "verdict.json").write_text(body)
    print(body)
    print(f"OUT={run}")
    return 0 if "harness_error" not in verdict else 1


if __name__ == "__main__":
    sys.exit(main())
