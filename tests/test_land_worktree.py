"""land_worktree: green path + every red branch + mutation drill (guard removed => test fails)."""
import importlib.util
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("land_worktree", os.path.join(HERE, "..", "tools", "land_worktree.py"))
lw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lw)

PASS = 'python -c "import sys; sys.exit(0)"'
FAIL = 'python -c "import sys; sys.exit(3)"'


def g(repo, *a):
    p = subprocess.run([lw.GIT, "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def commit(repo, name, text, msg="c"):
    (repo / name).write_text(text)
    g(repo, "add", name)
    g(repo, "commit", "-m", msg)


@pytest.fixture
def env(tmp_path):
    live = tmp_path / "live"
    live.mkdir()
    g(live, "init", "-b", "main")
    commit(live, "base.txt", "base\n")
    wt = tmp_path / "wt"
    g(live, "worktree", "add", "-b", "feat", str(wt))
    return live, wt


def test_lands_after_rebase_and_receipt(env):
    live, wt = env
    commit(live, "other.txt", "x\n")          # live moved on
    commit(wt, "new.txt", "n\n")
    (live / "dirty_unrelated.txt").write_text("d")  # unrelated dirt is fine
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["status"] == "LANDED", r
    assert (live / "new.txt").exists() and (live / "dirty_unrelated.txt").exists()
    assert g(live, "rev-parse", "HEAD") == r["live_head_after"] == r["branch_rebased"]


def test_overlap_refuses_and_lands_nothing(env):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    (live / "new.txt").write_text("someone else is editing")
    head = g(live, "rev-parse", "HEAD")
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["reason"] == "OVERLAP_LIVE_DIRTY" and r["overlap"] == ["new.txt"]
    assert g(live, "rev-parse", "HEAD") == head


def test_conflict_refuses_and_restores_branch(env):
    live, wt = env
    commit(live, "base.txt", "live\n")
    commit(wt, "base.txt", "wt\n")
    before = g(wt, "rev-parse", "feat")
    head = g(live, "rev-parse", "HEAD")
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["reason"] == "REBASE_CONFLICT"
    assert g(wt, "rev-parse", "feat") == before and g(live, "rev-parse", "HEAD") == head
    assert g(wt, "status", "--porcelain", "--untracked-files=no") == ""


def test_red_test_refuses_nothing_landed(env):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    head = g(live, "rev-parse", "HEAD")
    r = lw.land(str(wt), str(live), "feat", [PASS, FAIL])
    assert r["reason"] == "TESTS_RED_BEFORE"
    assert g(live, "rev-parse", "HEAD") == head and not (live / "new.txt").exists()


def test_missing_test_exe_is_red_not_green(env):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    r = lw.land(str(wt), str(live), "feat", ["no_such_exe_xyz --a"])
    assert r["reason"] == "TESTS_RED_BEFORE"


def test_no_tests_declared_refuses(env):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    assert lw.land(str(wt), str(live), "feat", [])["reason"] == "NO_TESTS_DECLARED"


def test_dirty_worktree_refuses(env):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    (wt / "base.txt").write_text("edited")
    assert lw.land(str(wt), str(live), "feat", [PASS])["reason"] == "WORKTREE_DIRTY"


def test_live_moved_during_land_refuses(env, monkeypatch):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    orig = lw.run_tests

    def moving(cwd, tests):
        if cwd == str(wt):
            commit(live, "race.txt", "r\n")   # live advances while tests run
        return orig(cwd, tests)

    monkeypatch.setattr(lw, "run_tests", moving)
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["reason"] == "LIVE_MOVED_DURING_LAND" and not (live / "new.txt").exists()


def test_post_landing_red_is_recorded(env, monkeypatch):
    live, wt = env
    commit(wt, "new.txt", "n\n")
    orig = lw.run_tests
    monkeypatch.setattr(lw, "run_tests",
                        lambda cwd, t: orig(cwd, t if cwd == str(wt) else [FAIL]))
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["status"] == "LANDED_POST_RED" and r["landed"]


def test_mutation_drill_overlap_guard_is_load_bearing(env, monkeypatch):
    """Remove the overlap guard: the refusal scenario must flip (else the red test proves nothing)."""
    live, wt = env
    commit(live, "x.txt", "1\n")
    commit(wt, "new.txt", "n\n")
    (live / "new.txt").write_text("dirty")
    monkeypatch.setattr(lw, "overlap", lambda a, b: [])
    r = lw.land(str(wt), str(live), "feat", [PASS])
    assert r["reason"] != "OVERLAP_LIVE_DIRTY"   # guard gone => scenario no longer refused by overlap
