#!/usr/bin/env python3
"""UWCP S2 -- Workspace Capsule gates (V-UWCP-WS-*).

Every fixture is a throwaway repository created, owned and deleted by this file.
Cross-host behaviour is simulated by two clones with different conversion
settings (autocrlf true vs false, fileMode/symlinks off as on NTFS): that is
LOCAL_REALITY for the object model; the Windows->GEX44 leg is REMOTE_REALITY owed
in S5.

    python tools/test_uwcp_workspace.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import workspace as ws   # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe" if os.name == "nt" else "git"
FAKE_KEY = "sk-ant-" + "A" * 50                   # HR-SECRET-005: clearly fake, real shape
passes = fails = 0


def _ok(gate, ev=""):
    global passes
    passes += 1
    print(f"  PASS {gate} {ev}")


def _fail(gate, diag=""):
    global fails
    fails += 1
    print(f"  FAIL {gate} {diag}")


def check(gate, cond, diag=""):
    (_ok if cond else _fail)(gate, diag if not cond else "")


def git(repo, *args, stdin=None, check_rc=True) -> str:
    p = subprocess.run([GIT, "-C", str(repo), *args], capture_output=True, input=stdin)
    if check_rc and p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr.decode(errors='replace')}")
    return p.stdout.decode("utf-8", "replace")


def mkrepo(path: Path, autocrlf: str = "false") -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    for k, v in (("user.name", "t"), ("user.email", "t@t"), ("core.autocrlf", autocrlf),
                 ("core.filemode", "false"), ("core.symlinks", "false"),
                 ("commit.gpgsign", "false")):
        git(path, "config", k, v)
    return path


def commit_all(repo, msg="c"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def expect_raise(fn, exc_type):
    try:
        fn()
    except exc_type as exc:
        return exc
    except Exception as exc:  # noqa: BLE001 -- report the wrong class, do not hide it
        return RuntimeError(f"wrong exception {type(exc).__name__}: {exc}")
    return None


def base_fixture(tmp: Path) -> Path:
    """autocrlf=true source: tracked text, a 100755 script and a 120000 symlink entry."""
    src = mkrepo(tmp / "src", autocrlf="true")
    (src / "app").mkdir()
    (src / "app" / "main.py").write_bytes(b"line1\r\nline2\r\nline3\r\n")
    (src / "app" / "util.py").write_bytes(b"def f():\r\n    return 1\r\n")
    (src / "other").mkdir()
    (src / "other" / "notes.txt").write_bytes(b"other team\r\n")
    (src / "run.sh").write_bytes(b"echo hi\n")
    (src / "target.txt").write_bytes(b"t\n")
    commit_all(src, "base")
    git(src, "update-index", "--chmod=+x", "run.sh")
    oid = git(src, "hash-object", "-w", "--stdin", stdin=b"target.txt").strip()
    git(src, "update-index", "--add", "--cacheinfo", f"120000,{oid},link")
    (src / "link").write_bytes(b"target.txt")           # what symlinks=false checks out
    git(src, "commit", "-q", "-m", "modes")
    return src


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="uwcp-ws-"))
    try:
        run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"UWCP_WORKSPACE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


def run(tmp: Path) -> None:
    src = base_fixture(tmp)
    # Dirty state: staged + unstaged (CRLF, as a Windows editor writes), allowlisted
    # untracked, non-allowlisted untracked, out-of-scope dirty, baseline-foreign in scope.
    (src / "app" / "main.py").write_bytes(b"line1\r\nSTAGED\r\nline3\r\n")
    git(src, "add", "app/main.py")
    (src / "app" / "main.py").write_bytes(b"line1\r\nSTAGED\r\nline3\r\nUNSTAGED\r\n")
    (src / "run.sh").write_bytes(b"echo edited on windows\n")
    (src / "app" / "util.py").write_bytes(b"def f():\r\n    return 2\r\n")
    (src / "app" / "new_data.json").write_bytes(b'{"k": 1}\n')
    (src / "app" / "scratch.log").write_bytes(b"noise\n")
    (src / "other" / "notes.txt").write_bytes(b"someone else's edit\r\n")
    status_before = git(src, "status", "--porcelain=v1")
    index_before = git(src, "ls-files", "-s")
    cap = tmp / "cap1"
    m = ws.capture(src, cap, scope_paths=["app", "run.sh", "link", "target.txt"],
                   foreign_baseline=["app/util.py"], include_untracked=["app/*.json"])
    cid = m["capsule_id"]

    # --- source untouched ------------------------------------------------------
    check("V-UWCP-WS-SOURCE-UNTOUCHED",
          git(src, "status", "--porcelain=v1") == status_before
          and git(src, "ls-files", "-s") == index_before
          and not git(src, "for-each-ref", "refs/uwcp").strip(),
          "capture changed the source's status/index or left refs/uwcp behind")

    # --- identity: modes seeded from the base survive a Windows capture ----------
    wt = {p: (mode, o) for mode, o, p in ws._ls_tree(src, m["trees"]["worktree_tree"])}
    check("V-UWCP-WS-MODES-SEEDED",
          wt.get("run.sh", ("",))[0] == "100755" and wt.get("link", ("",))[0] == "120000",
          f"run.sh={wt.get('run.sh')} link={wt.get('link')}")
    main_blob = git(src, "cat-file", "blob", wt["app/main.py"][1]).encode()
    check("V-UWCP-WS-CLEAN-FORM-EOL", b"\r" not in main_blob and b"UNSTAGED" in main_blob,
          f"worktree tree blob = {main_blob!r}")
    idx = {p: o for _m, o, p in ws._ls_tree(src, m["trees"]["index_tree"])}
    check("V-UWCP-WS-TWO-TREES",
          b"UNSTAGED" not in git(src, "cat-file", "blob", idx["app/main.py"]).encode()
          and b"STAGED" in git(src, "cat-file", "blob", idx["app/main.py"]).encode(),
          "index_tree does not hold exactly the staged version")

    # --- foreign + untracked -----------------------------------------------------
    check("V-UWCP-WS-FOREIGN-EXCLUDED-REPORTED",
          m["foreign"] == ["app/util.py", "other/notes.txt"]
          and b"return 1" in git(src, "cat-file", "blob", wt["app/util.py"][1]).encode()
          # foreign paths are not dropped from the tree: they travel at their BASE version
          and git(src, "cat-file", "blob", wt["other/notes.txt"][1]) == "other team\n",
          f"foreign={m['foreign']}")
    reasons = {e["path"]: e["reason"] for e in m["excluded"]}
    check("V-UWCP-WS-UNTRACKED-ALLOWLIST",
          [u["path"] for u in m["untracked"]] == ["app/new_data.json"]
          and "not allowlisted" in reasons.get("app/scratch.log", ""),
          f"untracked={m['untracked']} excluded={reasons}")

    # --- canonical manifest ----------------------------------------------------
    raw = (cap / ws.MANIFEST).read_bytes()
    check("V-UWCP-WS-CANONICAL-ID",
          hashlib.sha256(raw).hexdigest() == cid and ws._canonical(json.loads(raw)) == raw
          and all("size" in p and "sha256" in p for p in m["parts"]),
          "manifest bytes are not the canonical form its id names")
    bad = expect_raise(lambda: ws.load_manifest(cap, "0" * 64), ws.HydrateError)
    check("V-UWCP-WS-WRONG-ID-REFUSED", isinstance(bad, ws.HydrateError)
          and getattr(bad, "code", "") == "wrong_capsule", repr(bad))

    # --- hydrate into a node with DIFFERENT conversion settings ------------------
    node = mkrepo(tmp / "node", autocrlf="false")
    ws.hydrate(cap, node, capsule_id=cid)
    v, why = ws.verify(node, m)
    check("V-UWCP-WS-HYDRATE-EQUIVALENT", v == ws.EQUIVALENT, f"{v} {why}")
    check("V-UWCP-WS-NODE-RENDERS-OWN-EOL",
          (node / "app" / "main.py").read_bytes() == b"line1\nSTAGED\nline3\nUNSTAGED\n",
          repr((node / "app" / "main.py").read_bytes()))
    staged_node, unstaged_node, _ = ws._status(node)
    check("V-UWCP-WS-STAGING-RESTORED",
          "app/main.py" in staged_node and "app/main.py" in unstaged_node
          and "run.sh" in unstaged_node and "run.sh" not in staged_node,
          f"staged={staged_node} unstaged={unstaged_node}")
    check("V-UWCP-WS-FOREIGN-AT-BASE",
          (node / "other" / "notes.txt").read_bytes() == b"other team\n"
          and (node / "app" / "util.py").read_bytes() == b"def f():\n    return 1\n"
          and not (node / "app" / "scratch.log").exists(),
          "a foreign or non-allowlisted path travelled")

    # --- drift: eol-only under differing env is COMPATIBLE; content is not -------
    (node / "app" / "main.py").write_bytes(b"line1\r\nSTAGED\r\nline3\r\nUNSTAGED\r\n")
    v, why = ws.verify(node, m)
    check("V-UWCP-WS-EOL-DRIFT-COMPATIBLE", v == ws.COMPATIBLE, f"{v} {why}")
    (node / "app" / "main.py").write_bytes(b"line1\nSTAGED\nline3\nTAMPERED\n")
    v, why = ws.verify(node, m)
    check("V-UWCP-WS-CONTENT-NON-EQUIVALENT", v == ws.NON_EQUIVALENT
          and any("app/main.py" in r for r in why), f"{v} {why}")
    same = mkrepo(tmp / "same", autocrlf="true")
    ws.hydrate(cap, same, capsule_id=cid)
    (same / "app" / "main.py").write_bytes(b"line1\r\nSTAGED\r\nline3\r\nUNSTAGED\r\n")
    v, why = ws.verify(same, m)
    check("V-UWCP-WS-SAME-ENV-EOL-EQUIVALENT", v == ws.EQUIVALENT, f"{v} {why}")

    # Equal env: an eol-only change is a real change (the clean form moved), not drift.
    lf = mkrepo(tmp / "lf_src", autocrlf="false")
    (lf / "a.txt").write_bytes(b"one\ntwo\n")
    commit_all(lf)
    (lf / "a.txt").write_bytes(b"one\ntwo\nthree\n")
    lfm = ws.capture(lf, tmp / "c_lf", scope_paths=["."])
    lfn = mkrepo(tmp / "lf_node", autocrlf="false")
    ws.hydrate(tmp / "c_lf", lfn, capsule_id=lfm["capsule_id"])
    (lfn / "a.txt").write_bytes(b"one\r\ntwo\r\nthree\r\n")
    v, why = ws.verify(lfn, lfm)
    check("V-UWCP-WS-SAME-ENV-EOL-CHANGE-NON-EQUIVALENT", v == ws.NON_EQUIVALENT, f"{v} {why}")

    # --- dirty target refused ---------------------------------------------------
    e = expect_raise(lambda: ws.hydrate(cap, node, capsule_id=cid), ws.HydrateError)
    check("V-UWCP-WS-DIRTY-TARGET-REFUSED", isinstance(e, ws.HydrateError)
          and e.code == "dirty_target"
          and (node / "app" / "main.py").read_bytes() == b"line1\nSTAGED\nline3\nTAMPERED\n",
          repr(e))

    # --- UNKNOWN on unreadable --------------------------------------------------
    plain = tmp / "plain"
    plain.mkdir()
    v, why = ws.verify(plain, m)
    check("V-UWCP-WS-UNKNOWN-UNREADABLE", v == ws.UNKNOWN, f"{v} {why}")

    # --- part integrity: size first, digest before git, fsck at fetch -------------
    bpath = cap / ws.BUNDLE
    good = bpath.read_bytes()
    try:
        bpath.write_bytes(good[:-1])
        e = expect_raise(lambda: ws.hydrate(cap, tmp / "t_trunc", capsule_id=cid),
                         ws.HydrateError)
        check("V-UWCP-WS-TRUNCATED-SIZE-FIRST", isinstance(e, ws.HydrateError)
              and e.code == "corrupt_part" and "bytes" in str(e)
              and not (tmp / "t_trunc").exists(), repr(e))
        pack_at = good.index(b"PACK")
        flip = pack_at + (len(good) - pack_at) // 2
        flipped = good[:flip] + bytes([good[flip] ^ 0xFF]) + good[flip + 1:]
        bpath.write_bytes(flipped)
        e = expect_raise(lambda: ws.hydrate(cap, tmp / "t_flip", capsule_id=cid),
                         ws.HydrateError)
        check("V-UWCP-WS-BYTEFLIP-BEFORE-GIT", isinstance(e, ws.HydrateError)
              and e.code == "corrupt_part" and not (tmp / "t_flip").exists(), repr(e))
        # A pack corrupted AT CREATION: the digest names the corrupt bytes, so only
        # fetch+fsck can refuse it. bundle verify is recorded, not trusted.
        bv = subprocess.run([GIT, "-C", str(src), "bundle", "verify", str(bpath)],
                            capture_output=True)
        print(f"    (characterization: git bundle verify on the flipped pack -> exit "
              f"{bv.returncode})")
        forged = tmp / "cap_forged"
        shutil.copytree(cap, forged)
        body = json.loads((forged / ws.MANIFEST).read_bytes())
        for p in body["parts"]:
            if p["name"] == ws.BUNDLE:
                p["sha256"] = hashlib.sha256(flipped).hexdigest()
        fraw = ws._canonical(body)
        (forged / ws.MANIFEST).write_bytes(fraw)
        e = expect_raise(lambda: ws.hydrate(forged, tmp / "t_forged",
                                            capsule_id=hashlib.sha256(fraw).hexdigest()),
                         ws.HydrateError)
        check("V-UWCP-WS-FETCH-FSCK-CATCHES-CREATION-CORRUPTION",
              isinstance(e, ws.HydrateError) and e.code == "fetch_failed", repr(e))
    finally:
        bpath.write_bytes(good)

    # --- incremental bundle: missing prerequisite -> full re-capture --------------
    head = git(src, "rev-parse", "HEAD").strip()
    inc = ws.capture(src, tmp / "cap_inc", scope_paths=["app", "run.sh", "link", "target.txt"],
                     foreign_baseline=["app/util.py"], include_untracked=["app/*.json"],
                     base_known=head)
    e = expect_raise(lambda: ws.hydrate(tmp / "cap_inc", tmp / "t_inc",
                                        capsule_id=inc["capsule_id"]), ws.MissingPrerequisite)
    check("V-UWCP-WS-MISSING-PREREQ", isinstance(e, ws.MissingPrerequisite), repr(e))
    check("V-UWCP-WS-INCREMENTAL-SMALLER",
          inc["parts"][0]["size"] < next(p for p in m["parts"] if p["role"] == "bundle")["size"]
          and inc["trees"] == m["trees"], "incremental bundle not smaller, or trees moved")
    have = mkrepo(tmp / "have", autocrlf="false")
    git(have, "fetch", "-q", str(src), "main:refs/remotes/home/main")
    ws.hydrate(tmp / "cap_inc", have, capsule_id=inc["capsule_id"])
    v, why = ws.verify(have, inc)
    check("V-UWCP-WS-INCREMENTAL-EQUIVALENT", v == ws.EQUIVALENT, f"{v} {why}")

    # --- secrets ---------------------------------------------------------------
    s2 = mkrepo(tmp / "sec", autocrlf="false")
    (s2 / "a.txt").write_text("hello\nctx 3f786850e387550fdab836ed7e6dc881de23001b\n")
    commit_all(s2)
    (s2 / ".env").write_text("X=1\n")
    e = expect_raise(lambda: ws.capture(s2, tmp / "c_s1", scope_paths=["."],
                                        include_untracked=[".env"]), ws.CaptureRefused)
    check("V-UWCP-WS-SECRET-STRUCTURAL", isinstance(e, ws.CaptureRefused)
          and ".env" in str(e), repr(e))
    (s2 / ".env").unlink()
    (s2 / "a.txt").write_text(f"hello\nctx 3f786850e387550fdab836ed7e6dc881de23001b\n"
                              f"key={FAKE_KEY}\n")
    e = expect_raise(lambda: ws.capture(s2, tmp / "c_s2", scope_paths=["."]), ws.CaptureRefused)
    check("V-UWCP-WS-SECRET-CONTENT", isinstance(e, ws.CaptureRefused)
          and FAKE_KEY not in str(e) and "unstaged" in str(e), repr(e))
    (s2 / "a.txt").write_text("hello\nctx 3f786850e387550fdab836ed7e6dc881de23001b\n"
                              "tok=Zx9Qm2Lp7Vt4Rk8Wn3Jc6Hy1Bd5Gf0Ts2Ae9Uo\n")
    e = expect_raise(lambda: ws.capture(s2, tmp / "c_s3", scope_paths=["."]), ws.CaptureRefused)
    check("V-UWCP-WS-SECRET-ENTROPY", isinstance(e, ws.CaptureRefused)
          and "high_entropy_token" in str(e), repr(e))
    (s2 / "a.txt").write_text("hello edited\nctx 3f786850e387550fdab836ed7e6dc881de23001b\n")
    try:
        ws.capture(s2, tmp / "c_s4", scope_paths=["."])
        check("V-UWCP-WS-SECRET-CONTEXT-NOT-SCANNED", True)
    except ws.CaptureRefused as exc:
        check("V-UWCP-WS-SECRET-CONTEXT-NOT-SCANNED", False, f"control refused: {exc}")

    # --- unmerged index refused -------------------------------------------------
    um = mkrepo(tmp / "um")
    (um / "f.txt").write_text("a\n")
    commit_all(um)
    o = git(um, "hash-object", "-w", "f.txt").strip()
    info = "".join(f"{mode} {o} {st}\tf.txt\n" for mode, st in
                   (("0", "0"), ("100644", "1"), ("100644", "2"), ("100644", "3")))
    info = info.replace(f"0 {o} 0", "0 " + "0" * len(o) + " 0")
    git(um, "update-index", "--index-info", stdin=info.encode())
    e = expect_raise(lambda: ws.capture(um, tmp / "c_um", scope_paths=["."]), ws.CaptureRefused)
    check("V-UWCP-WS-UNMERGED-REFUSED", isinstance(e, ws.CaptureRefused)
          and "unmerged" in str(e), repr(e))

    # --- required filter absent refused; installed control records it -----------
    fr = mkrepo(tmp / "flt")
    (fr / ".gitattributes").write_text("*.x filter=upper\n")
    (fr / "a.x").write_text("abc\n")
    git(fr, "config", "filter.upper.clean", "cat")
    commit_all(fr)
    (fr / "a.x").write_text("abcd\n")
    good_m = ws.capture(fr, tmp / "c_f_ok", scope_paths=["."])
    git(fr, "config", "--unset", "filter.upper.clean")
    git(fr, "config", "filter.upper.required", "true")
    e = expect_raise(lambda: ws.capture(fr, tmp / "c_f_bad", scope_paths=["."]),
                     ws.CaptureRefused)
    check("V-UWCP-WS-REQUIRED-FILTER-ABSENT-REFUSED",
          isinstance(e, ws.CaptureRefused) and "upper" in str(e)
          and good_m["conversion_env"]["filters_in_scope"] == {"upper": True}, repr(e))
    fnode = mkrepo(tmp / "flt_node")
    ws.hydrate(tmp / "c_f_ok", fnode, capsule_id=good_m["capsule_id"])
    v, why = ws.verify(fnode, good_m)
    check("V-UWCP-WS-FILTER-MISSING-ON-NODE-UNKNOWN", v == ws.UNKNOWN
          and "upper" in " ".join(why), f"{v} {why}")

    # --- gitlink whose objects are absent -> NON_EQUIVALENT ------------------------
    sm = mkrepo(tmp / "sm")
    (sm / "f.txt").write_text("x\n")
    commit_all(sm)
    fake_commit = git(sm, "rev-parse", "HEAD").strip()
    git(sm, "update-index", "--add", "--cacheinfo", f"160000,{fake_commit},vendor/lib")
    git(sm, "commit", "-q", "-m", "gitlink")
    (sm / "vendor" / "lib").mkdir(parents=True)     # what a checkout leaves: an empty dir
    smm = ws.capture(sm, tmp / "c_sm", scope_paths=["."])
    smn = mkrepo(tmp / "sm_node")
    ws.hydrate(tmp / "c_sm", smn, capsule_id=smm["capsule_id"])
    v, why = ws.verify(smn, smm)
    check("V-UWCP-WS-SUBMODULE-ABSENT-NON-EQUIVALENT", v == ws.NON_EQUIVALENT
          and any("vendor/lib" in r for r in why) and smm["gitlinks"], f"{v} {why}")

    # --- case-colliding paths onto a case-insensitive host ------------------------
    cc = mkrepo(tmp / "cc")
    (cc / "seed.txt").write_text("s\n")
    commit_all(cc)
    ob = git(cc, "hash-object", "-w", "--stdin", stdin=b"same\n").strip()
    git(cc, "update-index", "--add", "--cacheinfo", f"100644,{ob},A.txt")
    git(cc, "update-index", "--add", "--cacheinfo", f"100644,{ob},a.txt")
    git(cc, "commit", "-q", "-m", "twins")
    (cc / "A.txt").write_bytes(b"same\n")
    ccm = ws.capture(cc, tmp / "c_cc", scope_paths=["."])
    ccn = mkrepo(tmp / "cc_node")
    git(ccn, "config", "core.ignorecase", "true")
    e = expect_raise(lambda: ws.hydrate(tmp / "c_cc", ccn, capsule_id=ccm["capsule_id"]),
                     ws.HydrateError)
    check("V-UWCP-WS-CASE-COLLISION-REFUSED", isinstance(e, ws.HydrateError)
          and e.code == "case_collision", repr(e))
    check("V-UWCP-WS-CASE-HELPER-CONTROL",
          ws.case_collisions(["A.txt", "a.txt", "b.txt"]) == [["A.txt", "a.txt"]]
          and ws.case_collisions(["A.txt", "b.txt"]) == [], "helper wrong")

    # --- retention: two passes, in-flight survives, RETIRED is its own outcome ------
    store = tmp / "store"
    store.mkdir()
    keep = ws.capture(src, store / "tmp_keep", scope_paths=["app"],
                      foreign_baseline=["app/util.py"])
    (store / "tmp_keep").rename(store / keep["capsule_id"])
    drop = ws.capture(sm, store / "tmp_drop", scope_paths=["."])
    (store / "tmp_drop").rename(store / drop["capsule_id"])
    inflight = store / "inflight"
    inflight.mkdir()
    (inflight / ws.BUNDLE).write_bytes(b"partial")
    r1 = ws.retain(store, {keep["capsule_id"]}, min_age_s=0)
    first_ok = (not r1["retired"] and drop["capsule_id"] in r1["marked"]
                and "inflight" in r1["in_flight"])
    r2 = ws.retain(store, {keep["capsule_id"]}, min_age_s=0)
    check("V-UWCP-WS-RETENTION-TWO-PASS",
          first_ok and r2["retired"] == [drop["capsule_id"]]
          and (inflight / ws.BUNDLE).is_file()
          and ws.capsule_status(store, keep["capsule_id"]) == ws.PRESENT,
          f"r1={r1} r2={r2}")
    e = expect_raise(lambda: ws.hydrate(store / drop["capsule_id"], tmp / "t_ret",
                                        capsule_id=drop["capsule_id"]), ws.HydrateError)
    check("V-UWCP-WS-RETIRED-DISTINCT",
          ws.capsule_status(store, drop["capsule_id"]) == ws.RETIRED
          and isinstance(e, ws.HydrateError) and e.code == ws.RETIRED, repr(e))
    ws.retain(store, set(), min_age_s=10 ** 9)
    check("V-UWCP-WS-RETENTION-AGE-MARGIN",
          ws.capsule_status(store, keep["capsule_id"]) == ws.PRESENT,
          "a young capsule was retired")


if __name__ == "__main__":
    sys.exit(main())
