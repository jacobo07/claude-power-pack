#!/usr/bin/env python3
"""test_foreign_repo_writes.py -- Power Pack hooks must not litter repos that are
not Power Pack projects (CDIO cross-sector benchmark B-5; Owner 2026-11-23:
"opt-in by folder").

Every benchmark case repo (a fresh git repo, nothing of PP in it) gained
vault/handoffs/ (background verifier) and .claude/cache/learnings/ (session
delta); ADS docs/ is pinned in test_ads.py (V-ADS-FOREIGN-NOT-ADOPTED). Each
writer is driven as the real subprocess, from both poles, so a foreign pole
cannot pass merely because the writer never fires:

  V-FRW-VERIFIER-FOREIGN-UNTOUCHED  git repo without vault/, with a live
                                    spec-incoherent finding -> no vault/
  V-FRW-VERIFIER-ADOPTED-WRITES     repo with vault/ + a live finding -> handoff
  V-FRW-DELTA-FOREIGN-SKIPPED       no .claude/cache/learnings -> not dispatched,
                                    nothing created
  V-FRW-DELTA-ADOPTED-DISPATCHED    the folder present -> delta.py dispatched
  V-FRW-DELTA-WORKTREE-INHERITS     a linked worktree of an adopted repo, with no
                                    folder of its own -> dispatched
  V-FRW-ADS-WORKTREE-INHERITS       the same worktree is adopted for ADS

The verifier's positive pole uses ovo-stale (an old last verdict plus a dirty
tree), because mirror-drift compares two global files this test cannot set.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = PP_ROOT / "tools" / "background_verifier_run.py"
DELTA_HOOK = PP_ROOT / "hooks" / "session_delta_stop.js"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

results: list[tuple[str, bool, str]] = []


def gate(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"  [{'OK' if ok else 'FAIL'}] {name} -- {detail}")


def _repo(root: Path) -> Path:
    root.mkdir(parents=True)
    subprocess.run([GIT, "init", "-q", str(root)], capture_output=True, timeout=30)
    (root / "index.html").write_text("<p>client page</p>", encoding="utf-8")
    return root


def _env(**extra: str) -> dict:
    env = dict(os.environ)
    for k in ("CPP_VERIFIER_ANY_REPO", "CPP_SESSION_DELTA_ANY_REPO"):
        env.pop(k, None)
    env.update(extra)
    return env


def _verifier(cwd: Path) -> int:
    return subprocess.run([sys.executable, str(VERIFIER), "--cwd", str(cwd),
                           "--session", "vfrw"], capture_output=True, text=True,
                          timeout=90, env=_env()).returncode


def _delta(cwd: Path, log: Path) -> str:
    # The observable is the hook's own log line ("dispatched" / "not adopted"),
    # written before the spawn returns. The spawned interpreter is NODE, not
    # python: node fails to parse delta.py and exits at once, so the real module
    # never runs -- with python it wrote ~/.claude/state/session_delta/vfrw.json
    # and a learnings file racing the rmtree (pp-code-reviewer, 2026-11-23). HOME
    # and USERPROFILE point into tmp as a second fence.
    home = log.parent / "home"
    subprocess.run([NODE, str(DELTA_HOOK)],
                   input=json.dumps({"cwd": str(cwd), "session_id": "vfrw"}),
                   capture_output=True, text=True, timeout=30,
                   env=_env(CPP_PYTHON_EXE=NODE, CPP_STOP_HOOK_LOG=str(log),
                            HOME=str(home), USERPROFILE=str(home)))
    try:
        return log.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="vfrw-"))
    try:
        foreign = _repo(tmp / "foreign")
        # A live finding that needs no vault/: an unresolved clarification in a
        # spec whose plan already exists. The old verifier wrote vault/handoffs/
        # here; without it this gate could pass only because nothing fired.
        feat = foreign / ".specify" / "specs" / "f1"
        feat.mkdir(parents=True)
        (feat / "spec.md").write_text("[NEEDS CLARIFICATION: who pays]\n", encoding="utf-8")
        (feat / "plan.md").write_text("plan\n", encoding="utf-8")
        rc = _verifier(foreign)
        made = (foreign / "vault").exists()
        gate("V-FRW-VERIFIER-FOREIGN-UNTOUCHED", rc == 0 and not made,
             f"rc={rc}, vault/ created={made}")

        adopted = _repo(tmp / "adopted")
        audits = adopted / "vault" / "audits"
        audits.mkdir(parents=True)
        (audits / "verdicts.jsonl").write_text(
            json.dumps({"ts": "2020-01-01T00:00:00Z", "verdict": "PASS"}) + "\n",
            encoding="utf-8")
        rc = _verifier(adopted)
        hd = adopted / "vault" / "handoffs"
        written = sorted(p.name for p in hd.glob("ovo-stale-*.md")) if hd.is_dir() else []
        gate("V-FRW-VERIFIER-ADOPTED-WRITES", rc == 0 and bool(written),
             f"rc={rc}, ovo-stale handoffs={written}")

        dforeign = _repo(tmp / "dforeign")
        out = _delta(dforeign, tmp / "d1.log")
        gate("V-FRW-DELTA-FOREIGN-SKIPPED",
             "not adopted" in out and "dispatched" not in out
             and not (dforeign / ".claude").exists(),
             f"log={out.strip()[-90:]!r}")

        dadopted = _repo(tmp / "dadopted")
        (dadopted / ".claude" / "cache" / "learnings").mkdir(parents=True)
        out = _delta(dadopted, tmp / "d2.log")
        gate("V-FRW-DELTA-ADOPTED-DISPATCHED", "dispatched" in out,
             f"log={out.strip()[-90:]!r}")

        # A linked worktree of an adopted repo is adopted: the folders are
        # untracked in the main checkout here, so the worktree has none of its own
        # (as TUA-X-qa has no docs/arch while TUA-X has).
        main = _repo(tmp / "main")
        g = ["-c", "user.email=frw@example.invalid", "-c", "user.name=frw"]
        subprocess.run([GIT, "-C", str(main), *g, "commit", "-q", "--allow-empty",
                        "-m", "root"], capture_output=True, timeout=30)
        (main / ".claude" / "cache" / "learnings").mkdir(parents=True)
        (main / "docs" / "arch").mkdir(parents=True)
        wt = tmp / "wt"
        subprocess.run([GIT, "-C", str(main), "worktree", "add", "-q", str(wt)],
                       capture_output=True, timeout=30)
        own = (wt / "docs" / "arch").exists() or (wt / ".claude").exists()
        out = _delta(wt, tmp / "d3.log")
        gate("V-FRW-DELTA-WORKTREE-INHERITS", wt.is_dir() and not own
             and "dispatched" in out, f"own folders={own}, log={out.strip()[-60:]!r}")
        sys.path.insert(0, str(PP_ROOT))
        from tools.ads_sync import main_worktree, sync
        mw = main_worktree(wt)
        s = sync(wt)
        gate("V-FRW-ADS-WORKTREE-INHERITS",
             mw is not None and mw.resolve() == main.resolve()
             and not s.get("not_adopted"),
             f"main_worktree={mw}, not_adopted={s.get('not_adopted')}")

        # first_time_project_init.py (SessionStart): it probed the GLOBAL PP install yet
        # wrote <cwd>/.pp-onboarded-prereqs into every repo with a manifest, and
        # vault/handoffs/ on a gap. USERPROFILE/HOME point at an empty folder, so every
        # check finds no Power Pack and the gap path (the handoff) is exercised for real.
        state = tmp / "ftstate"
        fakehome = tmp / "fthome"
        fakehome.mkdir()
        ftenv = _env(CPP_FIRST_TIME_STATE_DIR=str(state), HOME=str(fakehome),
                     USERPROFILE=str(fakehome))
        probe = PP_ROOT / "tools" / "first_time_project_init.py"

        def _probe(cwd: Path) -> int:
            return subprocess.run([sys.executable, str(probe), "--cwd", str(cwd), "--session", "vfrw"],
                                  capture_output=True, text=True, timeout=60, env=ftenv).returncode

        sys.path.insert(0, str(PP_ROOT / "tools"))
        from first_time_project_init import state_key
        ftf = _repo(tmp / "ftforeign")
        rc = _probe(ftf)
        key = state_key(ftf)
        in_repo = sorted(p.name for p in ftf.iterdir() if p.name not in (".git", "index.html"))
        gaps = sorted(p.name for p in state.glob(f"{key}-gaps-*.md")) if state.is_dir() else []
        gate("V-FRW-FIRSTTIME-FOREIGN-UNTOUCHED",
             rc == 0 and not in_repo and (state / f"{key}.json").is_file() and bool(gaps),
             f"rc={rc}, written in repo={in_repo}, state marker={(state / f'{key}.json').is_file()}, gaps={gaps}")

        fta = _repo(tmp / "ftadopted")
        (fta / "vault").mkdir()
        rc = _probe(fta)
        hd = fta / "vault" / "handoffs"
        written = sorted(p.name for p in hd.glob("pp-onboarding-*.md")) if hd.is_dir() else []
        gate("V-FRW-FIRSTTIME-ADOPTED-HANDOFF",
             rc == 0 and bool(written) and not (fta / ".pp-onboarded-prereqs").exists(),
             f"rc={rc}, vault handoffs={written}")

        before = sorted(p.name for p in state.iterdir())
        rc = _probe(ftf)
        after = sorted(p.name for p in state.iterdir())
        gate("V-FRW-FIRSTTIME-RUNS-ONCE", rc == 0 and before == after,
             f"new files on second run={sorted(set(after) - set(before))}")

        hook = PP_ROOT / "hooks" / "first-time-project.js"
        js = subprocess.run([NODE, "-e", "process.stdout.write(require(process.argv[1]).stateKey(process.argv[2]))",
                             str(hook), str(ftf)], capture_output=True, text=True, timeout=30)
        gate("V-FRW-FIRSTTIME-KEY-PARITY", js.returncode == 0 and js.stdout == key,
             f"js={js.stdout!r} py={key!r} err={js.stderr[-120:]!r}")
    finally:
        # git object files are read-only on Windows; plain ignore_errors left
        # every .git/objects file behind in %TEMP%.
        def _writable(func, p, _exc):
            try:
                os.chmod(p, 0o700)
                func(p)
            except OSError:
                pass
        shutil.rmtree(tmp, onerror=_writable)

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nFRW_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())