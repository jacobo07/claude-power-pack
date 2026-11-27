"""record_run.py - phase-local fixture: run a command, keep its output verbatim, check the record later.

Record mode:  python3 -I record_run.py --out FILE [--expect pass|fail] [--pristine PATH ...] [--timeout S] -- CMD...
  Runs CMD (stdout and stderr merged), prints it, and writes FILE with a header (UTC date, git HEAD,
  command, and for each --pristine PATH whether `git diff --quiet HEAD -- PATH` shows it unmodified),
  the verbatim output, and a final line `# exit=N`. Returns 0 only when the command's outcome matches
  --expect (default pass) AND, for --expect fail, every --pristine PATH was unmodified (a red record
  taken on already-edited code proves nothing). A timeout is recorded as exit=TIMEOUT and never
  matches pass.
Verify mode:  python3 -I record_run.py --verify FILE --expect pass|fail [--contains STR ...] [--pristine-required]
  Re-reads FILE and checks the footer exit, every --contains string, and (with --pristine-required)
  that the header lists at least one pristine=yes entry and no pristine=NO entry.
Stdlib only, registered nowhere.
"""
import argparse
import datetime
import os
import subprocess
import sys


def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def record(a, cmd):
    pristine_lines, all_pristine = [], True
    for p in a.pristine:
        rc, _ = _git("diff", "--quiet", "HEAD", "--", p)
        ok = rc == 0
        all_pristine = all_pristine and ok
        pristine_lines.append("# pristine: %s=%s" % (p, "yes" if ok else "NO"))
    _, head = _git("rev-parse", "--short", "HEAD")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=a.timeout)
        body = (r.stdout or "") + (r.stderr or "")
        code = str(r.returncode)
        passed = r.returncode == 0
    except subprocess.TimeoutExpired as exc:
        body = ((exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes)
                else (exc.stdout or ""))
        code, passed = "TIMEOUT", False
    except OSError as exc:
        body, code, passed = "spawn failed: %s\n" % exc, "SPAWN", False
    head_lines = ["# record_run", "# date_utc: " + datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "# head: " + head, "# cmd: " + " ".join(cmd), *pristine_lines]
    text = "\n".join(head_lines) + "\n" + body + ("" if body.endswith("\n") or not body else "\n") + \
        "# exit=" + code + "\n"
    parent = os.path.dirname(a.out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    sys.stdout.write(text)
    want_pass = a.expect == "pass"
    if passed != want_pass:
        print("record_run: outcome did not match --expect %s" % a.expect)
        return 1
    if not want_pass and not code.lstrip("-").isdigit():
        # a timeout or a spawn failure is not a red run: the test never produced a verdict
        print("record_run: exit=%s is not a real failing exit code, so it is not a red record" % code)
        return 1
    if not want_pass and not all_pristine:
        print("record_run: red record taken on modified code (pristine NO)")
        return 1
    return 0


def verify(a):
    with open(a.verify, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    exits = [l for l in lines if l.startswith("# exit=")]
    if len(exits) != 1:
        print("VERIFY_FAIL: expected exactly one '# exit=' footer, found %d" % len(exits))
        return 1
    code = exits[0][len("# exit="):]
    if not code.lstrip("-").isdigit():
        print("VERIFY_FAIL: footer exit=%s is not a real exit code (timeout or spawn failure)" % code)
        return 1
    failed = code != "0"
    if (a.expect == "fail") != failed:
        print("VERIFY_FAIL: footer exit=%s does not match --expect %s" % (code, a.expect))
        return 1
    for s in a.contains:
        if s not in text:
            print("VERIFY_FAIL: record lacks required text: " + s)
            return 1
    if a.pristine_required:
        ps = [l for l in lines if l.startswith("# pristine:")]
        if not ps or any(l.endswith("=NO") for l in ps) or not any(l.endswith("=yes") for l in ps):
            print("VERIFY_FAIL: pristine entries missing or NO")
            return 1
    print("VERIFY_OK %s exit=%s" % (a.verify, code))
    return 0


def main():
    argv = sys.argv[1:]
    cmd = []
    if "--" in argv:
        i = argv.index("--")
        argv, cmd = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--verify")
    ap.add_argument("--expect", choices=("pass", "fail"), default="pass")
    ap.add_argument("--pristine", action="append", default=[])
    ap.add_argument("--contains", action="append", default=[])
    ap.add_argument("--pristine-required", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args(argv)
    if a.verify:
        return verify(a)
    if not a.out or not cmd:
        ap.error("record mode needs --out FILE and a command after --")
    return record(a, cmd)


if __name__ == "__main__":
    raise SystemExit(main())
