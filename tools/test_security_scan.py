"""V-SEC-* gates for tools/security_scan.py (spec: vault/specs/security-scan.md).

Real scanners on a throwaway git project. Needs network: semgrep fetches `p/default` and
osv-scanner queries OSV. A gate that cannot reach them is reported as such by the tool itself
(UNCHECKED), and these gates then fail rather than pass.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security_scan as ss  # noqa: E402

passes = 0
fails = 0

OLD = ("import subprocess\n\n\ndef old(user):\n"
       "    return subprocess.run(\"ls \" + user, shell=True)\n")
NEW_BAD = OLD + ("\n\ndef new(user):\n"
                 "    return subprocess.run(\"cat \" + user, shell=True)\n")
NEW_OK = OLD + "\n\ndef ok():\n    return 1\n"


def check(gate: str, cond: bool, evidence: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate}: {evidence}")


def git(repo: Path, *args: str) -> None:
    subprocess.run([ss._git(), "-C", str(repo), "-c", "user.name=sec", "-c",
                    "user.email=sec@example.invalid", *args], check=True, capture_output=True)


def write(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="sec-test-"))
    repo = tmp / "proj"
    try:
        # Arrange: committed app with one shell=True, a patched lockfile, and an unchanged
        # lockfile that already pins a vulnerable version.
        write(repo, "app.py", OLD)
        write(repo, "requirements.txt", "PyYAML==6.0.2\n")
        write(repo, "sub/requirements.txt", "jinja2==2.10\n")
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "v0")
        # The change: a second shell=True, and a downgrade to a vulnerable PyYAML.
        write(repo, "app.py", NEW_BAD)
        write(repo, "requirements.txt", "PyYAML==5.3\n")

        # Act
        before = tree_hash(repo)
        res = ss.scan(repo)
        after = tree_hash(repo)

        # Assert: SAST
        s = res["sast"]
        check("V-SEC-MEASURED", res["verdict"] == "MEASURED",
              f"{res['verdict']} sast={s['outcome']} {s.get('reason', '')} sca={res['sca']['outcome']} {res['sca'].get('reason', '')}")
        lines = sorted(f["line"] for f in s["findings"])
        # OLD is 5 lines; then two blank lines, `def new` on 8, its shell=True call on 9.
        check("V-SEC-SAST-CHANGED-LINE", s["outcome"] == "FINDINGS" and lines == [9]
              and all("shell" in f["rule"] for f in s["findings"]), f"lines={lines} rules={[f['rule'] for f in s['findings']]}")
        check("V-SEC-SAST-PRE-EXISTING-COUNTED", s["pre_existing"] == 1, f"pre_existing={s['pre_existing']}")

        # Assert: SCA
        d = res["sca"]
        by_pkg = {f["package"].lower(): f for f in d["findings"]}
        check("V-SEC-SCA-INTRODUCED", "pyyaml" in by_pkg and by_pkg["pyyaml"]["introduced"] is True
              and by_pkg["pyyaml"]["lockfile"] == "requirements.txt", str(by_pkg.get("pyyaml")))
        check("V-SEC-SCA-EXISTING", "jinja2" in by_pkg and by_pkg["jinja2"]["introduced"] is False
              and by_pkg["jinja2"]["lockfile"] == "sub/requirements.txt", str(by_pkg.get("jinja2")))
        n_yaml = sum(1 for f in d["findings"] if f["package"].lower() == "pyyaml")
        check("V-SEC-SCA-DEDUP", n_yaml == 1, f"pyyaml rows={n_yaml}")
        check("V-SEC-PROJECT-UNTOUCHED", before == after, "tree hash identical before/after")

        # Controls: a clean change reports no SAST finding; a patched lockfile no PyYAML row.
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "v1")
        write(repo, "app.py", NEW_BAD + "\n\ndef ok():\n    return 1\n")
        write(repo, "requirements.txt", "PyYAML==6.0.2\n")
        res = ss.scan(repo)
        s, d = res["sast"], res["sca"]
        check("V-SEC-SAST-CLEAN-CONTROL", s["outcome"] == "CLEAN" and s["pre_existing"] == 2,
              f"{s['outcome']} findings={s['findings']} pre_existing={s['pre_existing']}")
        pk = [f["package"].lower() for f in d["findings"]]
        check("V-SEC-SCA-PATCHED-CONTROL", "pyyaml" not in pk and "jinja2" in pk, f"packages={pk}")

        # Unchecked is never clean.
        missing = tmp / "no_such_scanner.exe"
        res = ss.scan(repo, semgrep=missing)
        check("V-SEC-SAST-UNCHECKED", res["sast"]["outcome"] == "UNCHECKED" and "not found" in res["sast"]["reason"]
              and res["verdict"] == "MEASURED", f"{res['sast']['outcome']}: {res['sast'].get('reason')}")
        res = ss.scan(repo, osv=missing)
        check("V-SEC-SCA-UNCHECKED", res["sca"]["outcome"] == "UNCHECKED", f"{res['sca']['outcome']}: {res['sca'].get('reason')}")
        cli = [sys.executable, str(Path(ss.__file__)), "--repo", str(repo), "--osv", str(missing),
               "--semgrep", str(missing)]
        r = subprocess.run(cli, capture_output=True, text=True, encoding="utf-8", errors="replace")
        check("V-SEC-ALL-UNCHECKED-EXIT-2", r.returncode == 2 and "UNMEASURABLE" in r.stdout,
              f"exit={r.returncode} {r.stdout.strip()[:120]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"SEC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
