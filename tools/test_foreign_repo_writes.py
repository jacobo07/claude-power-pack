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