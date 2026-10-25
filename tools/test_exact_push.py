"""V-XPUSH-* -- exact_push binds a push to the SHA that was scanned.

Root cause (2026-10-25): scan of origin/B..B at tip f4db3d41, then `git push origin B:B` re-resolved the
moving ref and published 0b4aa4ce unscanned. Everything runs against a temp local bare repo, never a real remote.
Credential-shaped values are assembled at run time so this file carries none.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import exact_push as xp  # noqa: E402

GIT = xp.GIT
passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, why: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {why}")


def g(cwd, *a, check=True) -> str:
    r = subprocess.run([GIT, "-C", str(cwd), *a], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError(f"git {a}: {r.stderr}")
    return r.stdout.strip()


def commit(repo: Path, name: str, text: str) -> str:
    (repo / name).write_text(text, encoding="utf-8")
    g(repo, "add", name)
    g(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", f"add {name}")
    return g(repo, "rev-parse", "HEAD")


def remote_ref(bare: Path, ref: str) -> str:
    return g(bare, "rev-parse", "--verify", "-q", f"refs/heads/{ref}", check=False)


def fresh(tmp: Path):
    tmp.mkdir(parents=True, exist_ok=True)
    bare = tmp / "remote.git"
    repo = tmp / "work"
    g(tmp, "init", "-q", "--bare", str(bare))
    g(tmp, "init", "-q", "-b", "feat", str(repo))
    base = commit(repo, "a.txt", "one\n")
    g(repo, "push", "-q", str(bare), "feat:refs/heads/feat")
    return bare, repo, base


def run(repo: Path, *argv) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(HERE / "exact_push.py"), *argv, "--repo", str(repo)],
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="xpush-"))
    try:
        bare, repo, base = fresh(tmp / "one")
        a = commit(repo, "b.txt", "clean change\n")
        ra_p = tmp / "ra.json"
        rc, out = run(repo, "scan", "--remote", str(bare), "--ref", "feat", "--out", str(ra_p))
        ra = load(ra_p).get("receipt", {})
        if rc == 0 and ra.get("sha") == a and ra.get("base_sha") == base and ra.get("result") == "PASS":
            _ok("V-XPUSH-SCAN", f"receipt binds sha {a[:8]} over base {base[:8]}")
        else:
            _fail("V-XPUSH-SCAN", f"rc={rc} out={out[:200]}")

        # a concurrent commit moves the tip to B; A's receipt must not publish it
        b = commit(repo, "c.txt", "moved after the scan\n")
        rc, out = run(repo, "push", "--receipt", str(ra_p))
        if rc != 0 and remote_ref(bare, "feat") == base:
            _ok("V-XPUSH-TIP-MOVED", "tip B with A's receipt refused; remote untouched")
        else:
            _fail("V-XPUSH-TIP-MOVED", f"rc={rc} remote={remote_ref(bare, 'feat')[:8]} out={out[:200]}")

        rc, out = run(repo, "push", "--receipt", str(ra_p), "--sha", a)
        if rc == 0 and remote_ref(bare, "feat") == a:
            _ok("V-XPUSH-EXACT-SHA", f"remote ref == A {a[:8]}, B {b[:8]} unpublished")
        else:
            _fail("V-XPUSH-EXACT-SHA", f"rc={rc} remote={remote_ref(bare, 'feat')[:8]} out={out[:200]}")

        rb_p = tmp / "rb.json"
        rc, out = run(repo, "scan", "--remote", str(bare), "--ref", "feat", "--out", str(rb_p))
        rc2, out2 = run(repo, "push", "--receipt", str(rb_p))
        if rc == 0 and rc2 == 0 and remote_ref(bare, "feat") == b:
            _ok("V-XPUSH-RESCAN-B", "rescan B then push B: remote == B")
        else:
            _fail("V-XPUSH-RESCAN-B", f"rc={rc}/{rc2} remote={remote_ref(bare, 'feat')[:8]} out={out2[:200]}")

        # receipt re-sealed after tampering with remote URL / ref / policy hash: only the binding check can catch it
        bare2, repo2, base2 = fresh(tmp / "two")
        commit(repo2, "d.txt", "x\n")
        r2_p = tmp / "r2.json"
        run(repo2, "scan", "--remote", str(bare2), "--ref", "feat", "--out", str(r2_p))
        r2 = load(r2_p)
        for gate, field, val in (("V-XPUSH-REMOTE-DIFF", "remote_url", str(tmp / "elsewhere.git")),
                                 ("V-XPUSH-REF-DIFF", "ref", "other"),
                                 ("V-XPUSH-POLICY-DIFF", "policy_hash", "0" * 64)):
            t = json.loads(json.dumps(r2))
            t["receipt"][field] = val
            t["sha256"] = xp.digest(t["receipt"])
            p = tmp / f"{gate}.json"
            p.write_text(json.dumps(t), encoding="utf-8")
            rc, out = run(repo2, "push", "--receipt", str(p))
            if rc != 0 and remote_ref(bare2, "feat") == base2:
                _ok(gate, f"{field} differs -> refused")
            else:
                _fail(gate, f"rc={rc} remote={remote_ref(bare2, 'feat')[:8]} out={out[:160]}")

        # a planted credential in the range, mid-range so a tip-only scan would miss it
        cred = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
        bare3, repo3, base3 = fresh(tmp / "three")
        commit(repo3, "s.txt", f"k = {cred}\n")
        commit(repo3, "t.txt", "later clean commit\n")
        r3_p = tmp / "r3.json"
        rc, out = run(repo3, "scan", "--remote", str(bare3), "--ref", "feat", "--out", str(r3_p))
        r3 = load(r3_p).get("receipt", {})
        rc2, out2 = run(repo3, "push", "--receipt", str(r3_p))
        if (rc != 0 and r3.get("result") == "BLOCK" and rc2 != 0 and remote_ref(bare3, "feat") == base3
                and cred not in out + out2 + json.dumps(r3)):
            _ok("V-XPUSH-SECRET", "credential in a mid-range commit -> BLOCK, push refused, value not echoed")
        else:
            _fail("V-XPUSH-SECRET", f"rc={rc}/{rc2} result={r3.get('result')} out={out[:160]}")

        # control: a non-credential line (generic assignment, MEDIUM) is admitted under the secrets-only policy
        bare4, repo4, base4 = fresh(tmp / "four")
        line = "pass" + "word = 'x" + "y" * 20 + "'\n"
        s4 = commit(repo4, "n.txt", line)
        r4_p = tmp / "r4.json"
        rc, out = run(repo4, "scan", "--remote", str(bare4), "--ref", "feat", "--out", str(r4_p))
        rc2, out2 = run(repo4, "push", "--receipt", str(r4_p))
        if rc == 0 and rc2 == 0 and remote_ref(bare4, "feat") == s4:
            _ok("V-XPUSH-CONTROL-ADMIT", "non-credential pattern admitted: the gate does not refuse everything")
        else:
            _fail("V-XPUSH-CONTROL-ADMIT", f"rc={rc}/{rc2} out={out[:160]} {out2[:160]}")

        pol = xp.policy()
        if pol.get("name") == "secrets-only" and xp.digest(pol) != xp.digest(dict(pol, name="everything")):
            _ok("V-XPUSH-POLICY-HASH", "policy names secrets-only and its hash changes with it")
        else:
            _fail("V-XPUSH-POLICY-HASH", str(pol)[:120])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"XPUSH_PASS={passes}/{passes + fails}  threshold=10/10")
    return 0 if fails == 0 and passes == 10 else 1


if __name__ == "__main__":
    sys.exit(main())
