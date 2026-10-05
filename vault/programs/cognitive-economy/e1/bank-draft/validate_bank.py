"""POSIX validator for the E1 judgement bank. No model call, stdlib only.

    python3 validate_bank.py validate [--only ID[,ID...]] [--log PATH]
    python3 validate_bank.py pins
    python3 validate_bank.py index (--stdout | --write | --check)

`validate`: for every task (contract order: rule bytes descending) run its selftest, then in a fresh
detached worktree at BASE outside the repo list the tree for any bank file, scrub every copy of a packet
rule, write the stub, grade it (must be red), and remove the worktree.

The functions are top-level so the Phase 2 runner can reuse them (fresh_tree, drop_tree, jprepare, jgrade).
Nothing under ~/.claude is ever opened for writing.
"""
import sys

sys.dont_write_bytecode = True

import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _e1_common import JPROMPT  # noqa: E402

REPO = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE, capture_output=True,
                           text=True, check=True).stdout.strip())
RUNS = Path("/home/kobii/e1-runs")
PY = sys.executable
PACKET = REPO / "vault/programs/cognitive-economy/post-reset-packet.json"
EXCLUDED_BY_R2 = ["rules/technical-failure-to-product-state.md", "rules/scoped-side-effect-authority.md"]

E1_PREFIX = "vault/programs/cognitive-economy/e1/"
E1_ADDENDUM = E1_PREFIX + "ADDENDUM-E1.md"
PLAN_PREFIX = ".planning/workstreams/cognitive-economy-e1/phases/"
BANK_FILE_NAMES = ("_e1_common.py", "validate_bank.py", "test_validate_bank.py")


def child_env():
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def git(*args, cwd=REPO, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=child_env())
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)} -> {r.returncode}: {r.stderr.strip()}")
    return r.stdout.strip()


def _git_bytes(*args, cwd=REPO, input=None):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, input=input, env=child_env())
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} -> {r.returncode}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


# ---- packet and pins ---------------------------------------------------------------------------------

def packet_rules():
    """The 13 candidates as {rule (relative to ~/.claude), bytes, sha256_lf}, in packet order."""
    p = json.loads(PACKET.read_text(encoding="utf-8"))
    out = []
    for c in p["experiments"][0]["candidates"]:
        rel = c["rule"]
        if rel.startswith("~/.claude/"):
            rel = rel[len("~/.claude/"):]
        out.append({"rule": rel, "bytes": c["bytes"], "sha256_lf": c["sha256_lf"]})
    return out


def e1_rules():
    """The rules this experiment decides: the 13 minus the two R2 decided, rule bytes descending."""
    return sorted((r for r in packet_rules() if r["rule"] not in EXCLUDED_BY_R2),
                  key=lambda r: -r["bytes"])


RULE_PATHS = [r["rule"] for r in packet_rules()]


def _lf_sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def pins():
    """Read the 13 rule files read-only and compare their LF sha256 to the packet -> (ok_count, mismatches)."""
    ok, bad = 0, []
    for r in packet_rules():
        f = Path.home() / ".claude" / r["rule"]
        try:
            h = _lf_sha(f.read_bytes())
        except OSError as e:
            bad.append(f"{r['rule']}: unreadable ({e.__class__.__name__})")
            continue
        if h == r["sha256_lf"]:
            ok += 1
        else:
            bad.append(f"{r['rule']}: sha256 {h[:12]} != pinned {r['sha256_lf'][:12]}")
    return ok, bad


# ---- task discovery ----------------------------------------------------------------------------------

def _load_task(f, here):
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    spec = importlib.util.spec_from_file_location(f.stem, f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise SystemExit(f"cannot load {f.name}: {type(e).__name__}: {e}")
    for attr in ("RULE", "MODULE", "STUB", "CHECKS", "JUDGES"):
        if not hasattr(mod, attr):
            raise SystemExit(f"{f.name} defines no {attr}")
    return mod


def tasks(only=None, here=HERE):
    """Discover task_*.py by NAME in `here`. With `only` (task ids) load ONLY those files, so a sibling
    task another plan is still writing cannot break the run; without it load every task file."""
    here = Path(here)
    pk = {r["rule"]: r for r in packet_rules()}
    if only is not None:
        files = []
        for i in only:
            f = here / ("task_" + (i[2:] if i.startswith("J-") else i) + ".py")
            if not f.is_file():
                raise SystemExit(f"no task file for {i}: {f}")
            files.append(f)
    else:
        files = sorted(here.glob("task_*.py"))
    out, seen = [], {}
    for f in files:
        m = _load_task(f, here)
        if m.RULE in EXCLUDED_BY_R2:
            raise SystemExit(f"{f.name}: {m.RULE} was decided by R2 and is not re-run")
        if m.RULE not in pk:
            raise SystemExit(f"{f.name}: {m.RULE} is not a packet rule")
        if m.RULE in seen:
            raise SystemExit(f"{f.name} and {seen[m.RULE]} both test {m.RULE}")
        seen[m.RULE] = f.name
        out.append({"id": "J-" + f.stem[5:], "file": f, "module": m.MODULE, "stub": m.STUB, "rule": m.RULE,
                    "checks": [(c[0], c[1]) for c in m.CHECKS], "judges": dict(m.JUDGES)})
    out.sort(key=lambda t: -pk[t["rule"]]["bytes"])
    return out


# ---- BASE and the worktree ---------------------------------------------------------------------------

def _is_bank_path(rel):
    return (rel.startswith(E1_PREFIX) and rel != E1_ADDENDUM) or rel.startswith(PLAN_PREFIX)


def base_leaks(base, repo=REPO):
    """Paths in the BASE tree that would hand a session the bank or the plans that describe the checks."""
    listing = _git_bytes("ls-tree", "-r", "--name-only", "-z", base, cwd=repo).decode("utf-8", "replace")
    return sorted(p for p in listing.split("\0") if p and _is_bank_path(p))


def jbase():
    base = (HERE / "BASE").read_text(encoding="utf-8").strip()
    try:
        git("cat-file", "-e", base + "^{commit}")
    except RuntimeError:
        raise SystemExit(f"BASE {base} is not a commit in this repository")
    leaks = base_leaks(base)
    if leaks:
        raise SystemExit(f"BASE {base} contains the bank or its plans: {leaks[:5]}")
    return git("rev-parse", base + "^{commit}")


def _under_runs(wt):
    p = Path(wt).resolve()
    return RUNS.resolve() in p.parents


def drop_tree(wt):
    wt = Path(wt)
    if not _under_runs(wt):
        raise RuntimeError(f"refusing to drop {wt}: not strictly under {RUNS}")
    # Twice --force: git refuses a LOCKED worktree with one (measured in P3: an interrupted add left one locked).
    git("worktree", "remove", "--force", "--force", str(wt), check=False)
    listed = {ln[len("worktree "):] for ln in git("worktree", "list", "--porcelain", check=False).splitlines()
              if ln.startswith("worktree ")}
    return (not os.path.lexists(wt)) and str(wt.resolve()) not in listed and str(wt) not in listed


def fresh_tree(run_id, base):
    wt = RUNS / run_id
    if not _under_runs(wt) or REPO.resolve() in wt.resolve().parents or wt.resolve() == REPO.resolve():
        raise RuntimeError(f"refusing to create {wt}")
    RUNS.mkdir(parents=True, exist_ok=True)
    drop_tree(wt)  # a run killed mid-`worktree add` leaves it registered AND locked
    git("worktree", "prune", check=False)
    git("worktree", "add", "--detach", str(wt), base)
    return wt


# ---- scanning the run tree ---------------------------------------------------------------------------

def _walk_files(root):
    """Yield (absolute path, relative posix path) for regular files under root; `.git` at the root is
    skipped; symlinks are never followed and never yielded."""
    root = str(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if dirpath == root and ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            if dirpath == root and name == ".git":
                continue
            p = os.path.join(dirpath, name)
            try:
                if not stat.S_ISREG(os.lstat(p).st_mode):
                    continue
            except OSError:
                continue
            yield p, os.path.relpath(p, root).replace(os.sep, "/")


def _read(p):
    try:
        with open(p, "rb") as f:
            return f.read()
    except OSError:
        return b""


def leak_scan(wt, here=HERE):
    """-> (files_listed, hits). A hit is a path under the bank/plan prefixes, a bank file name, or a file whose
    bytes hold a bank marker. Names and markers come from the file NAMES in `here`, never from loading them."""
    here = Path(here)
    stems = [p.stem for p in sorted(here.glob("task_*.py"))]
    names = set(BANK_FILE_NAMES) | {p.name for p in here.glob("task_*.py")}
    markers = [m.encode() for m in ["E1J_PASS", "_e1_common", *stems]]
    listed, hits = 0, []
    for p, rel in _walk_files(wt):
        listed += 1
        if _is_bank_path(rel) or os.path.basename(rel) in names:
            hits.append(rel)
            continue
        data = _read(p)
        if any(m in data for m in markers):
            hits.append(rel)
    return listed, sorted(hits)


def rule_copies(wt):
    """Informational: files that are byte copies of a packet rule or sit at a packet rule's relative path."""
    rules = packet_rules()
    pinset = {r["sha256_lf"] for r in rules}
    rels = [r["rule"] for r in rules]
    out = []
    for p, rel in _walk_files(wt):
        if any(rel == r or rel.endswith("/" + r) for r in rels) or _lf_sha(_read(p)) in pinset:
            out.append(rel)
    return sorted(out)


def pin_matches(root, pins):
    """Relative paths of regular files under root whose LF sha256 is in `pins`."""
    pins = set(pins)
    return sorted(rel for p, rel in _walk_files(root) if _lf_sha(_read(p)) in pins)


def _safe_target(target, real_root, rel):
    """True only for a regular file reached without crossing a symlink and inside the real root."""
    if os.path.islink(target):
        return False
    try:
        if not stat.S_ISREG(os.lstat(target).st_mode):
            return False
    except OSError:
        return False
    real = os.path.realpath(target)
    expected = os.path.join(real_root, *rel.split("/"))
    return real == expected and real.startswith(real_root + os.sep)


def scrub_pin_copies(root, pins, rule_paths=RULE_PATHS):
    """Remove every regular file whose LF sha256 is a pin (content identity) and every root/<p> for p in
    rule_paths (path identity, exact relative path only). Never a directory, never a symlink, never a path
    that resolves outside the real root. Returns the sorted, de-duplicated relative paths removed."""
    root = Path(root)
    real_root = os.path.realpath(root)
    targets = set(pin_matches(root, pins))
    targets.update(p for p in rule_paths if os.path.lexists(root / p))
    removed = []
    for rel in sorted(targets):
        t = root / rel
        if not _safe_target(t, real_root, rel):
            continue
        os.remove(t)
        removed.append(rel)
    return sorted(set(removed))


# ---- prepare and grade -------------------------------------------------------------------------------

def jprepare(wt, t):
    """Scrub every packet-rule copy from the run tree (both arms), then write the stub. Returns the removed
    paths. Shared by the Phase 2 runner for every counted run."""
    wt = Path(wt)
    if not _under_runs(wt):
        raise RuntimeError(f"refusing to prepare {wt}: not strictly under {RUNS}")
    p = wt / t["module"]
    if os.path.lexists(p):
        raise RuntimeError(f"{t['module']} already exists in {wt}: collision with the BASE tree")
    removed = scrub_pin_copies(wt, [r["sha256_lf"] for r in packet_rules()], RULE_PATHS)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t["stub"], encoding="utf-8")
    return removed


def jgrade(wt, t, cleanup=True):
    wt = Path(wt)
    shutil.copyfile(HERE / "_e1_common.py", wt / "_e1_common.py")
    shutil.copyfile(t["file"], wt / "_e1j_task.py")
    try:
        r = subprocess.run([PY, "_e1j_task.py", "grade", t["module"]], cwd=str(wt), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300, env=child_env())
    except subprocess.TimeoutExpired:
        # A solution that never returns is graded as failed, never as an aborted run.
        return {"rc": 124, "passed": 0, "total": 0, "control": (0, 0), "judgement": (0, 0),
                "fails": ["grade timed out after 300 s"], "summary": "grade timeout"}
    finally:
        if cleanup:
            for f in ("_e1_common.py", "_e1j_task.py"):
                try:
                    (wt / f).unlink()
                except OSError:
                    pass
    out = r.stdout + r.stderr
    m = re.findall(r"E1J_PASS=(\d+)/(\d+) control=(\d+)/(\d+) judgement=(\d+)/(\d+)", out)
    fails = [ln[5:80] for ln in out.splitlines() if ln.startswith("FAIL ")]
    if m:
        k, n, ca, cb, ja, jb = (int(x) for x in m[-1])
        summary = f"E1J_PASS={k}/{n} control={ca}/{cb} judgement={ja}/{jb}"
        res = {"passed": k, "total": n, "control": (ca, cb), "judgement": (ja, jb)}
    else:
        summary = "no E1J line"
        res = {"passed": 0, "total": 0, "control": (0, 0), "judgement": (0, 0)}
    return {"rc": r.returncode, **res, "fails": fails, "summary": summary}


def task_ok(selftest_rc, g, files_listed, leak, module_absent, rescan, removed):
    return (selftest_rc == 0 and g["rc"] != 0 and "E1J_PASS=" in g["summary"] and files_listed > 0
            and not leak and bool(module_absent) and not rescan and bool(removed))


# ---- validate ----------------------------------------------------------------------------------------

def _header(base, pins_ok):
    lines = [f"E1 VALIDATE {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             f"host {os.uname().nodename}",
             f"python {sys.version.split()[0]}",
             f"repo-head {git('rev-parse', 'HEAD')}",
             f"BASE {base}",
             f"PINS {pins_ok}/13"]
    for f in sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "VALIDATE.log"):
        lines.append(f"SHA256 {hashlib.sha256(f.read_bytes()).hexdigest()} {f.name}")
    return lines


def validate(only=None, log=None):
    out = []

    def emit(line):
        out.append(line)
        print(line, flush=True)

    ts = tasks(only)
    base = jbase()
    pins_ok, pins_bad = pins()
    for ln in _header(base, pins_ok):
        emit(ln)
    for b in pins_bad:
        emit(f"PIN-MISMATCH {b}")
    pinset = [r["sha256_lf"] for r in packet_rules()]
    bad = 0
    for t in ts:
        st = subprocess.run([PY, str(t["file"]), "selftest"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", env=child_env())
        wt = RUNS / ("validate-" + t["id"])
        try:
            fresh_tree("validate-" + t["id"], base)
            files_listed, leak = leak_scan(wt)
            copies = rule_copies(wt)
            module_absent = not os.path.lexists(wt / t["module"])
            scrubbed = jprepare(wt, t)
            rescan = sorted(set(pin_matches(wt, pinset)) | {p for p in RULE_PATHS if os.path.lexists(wt / p)})
            g = jgrade(wt, t)
        finally:
            removed = drop_tree(wt)
        ok = task_ok(st.returncode, g, files_listed, leak, module_absent, rescan, removed)
        bad += not ok
        emit(f"{'OK ' if ok else 'BAD'} {t['id']}: selftest_rc={st.returncode} stub_in_tree={g['summary']} "
             f"tree_files={files_listed} bank_in_tree={','.join(leak) or 'none'} "
             f"module_absent_at_base={module_absent} pin_copies_removed={','.join(scrubbed) or 'none'} "
             f"pin_rescan={len(rescan)} worktree_removed={removed} rule_copies={','.join(copies) or 'none'}")
    n = len(ts)
    good = n > 0 and bad == 0 and pins_ok == 13
    emit(f"VALIDATE-E1 {n - bad}/{n} base={base[:10]} pins={pins_ok}/13")
    if log:
        Path(log).write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if good else 1


# ---- index -------------------------------------------------------------------------------------------

def base_rule_copies(base, rules=None):
    """{rule: [paths in the BASE tree that are copies of that rule]} from the tree object alone: a path equal
    to / ending with the rule's relative path, or a blob whose LF sha256 equals the rule's pin."""
    rules = rules or packet_rules()
    raw = _git_bytes("ls-tree", "-r", "-l", "-z", base).decode("utf-8", "replace")
    entries = []
    for rec in raw.split("\0"):
        if not rec:
            continue
        meta, path = rec.split("\t", 1)
        parts = meta.split()
        if parts[1] == "blob":
            entries.append((path, parts[2], int(parts[3])))
    lo = min(r["bytes"] for r in rules)
    hi = 2 * max(r["bytes"] for r in rules)
    cand = [e for e in entries if lo <= e[2] <= hi]
    shas = {}
    if cand:
        data = _git_bytes("cat-file", "--batch", input=("\n".join(e[1] for e in cand) + "\n").encode())
        pos = 0
        while pos < len(data):
            nl = data.index(b"\n", pos)
            sha, _typ, size = data[pos:nl].decode().split()
            size = int(size)
            body = data[nl + 1:nl + 1 + size]
            shas[sha] = _lf_sha(body)
            pos = nl + 1 + size + 1
    out = {}
    for r in rules:
        rel = r["rule"]
        hit = {p for p, _s, _z in entries if p == rel or p.endswith("/" + rel)}
        hit |= {p for p, s, _z in cand if shas.get(s) == r["sha256_lf"]}
        out[rel] = sorted(hit)
    return out


def build_index(here=HERE):
    pk = {r["rule"]: r for r in packet_rules()}
    ts = tasks(None, here)
    base = jbase()
    copies = base_rule_copies(base)
    have = {t["rule"] for t in ts}
    items = []
    for i, t in enumerate(ts, 1):
        r = pk[t["rule"]]
        items.append({
            "order": i, "id": t["id"], "rule": t["rule"], "rule_bytes": r["bytes"], "sha256_lf": r["sha256_lf"],
            "task_file": t["file"].name, "module": t["module"],
            "control_checks": [n for n, k in t["checks"] if k == "control"],
            "judgement_checks": [{"name": n, "decision": t["judges"][n]} for n, k in t["checks"] if k == "judgement"],
            "rule_copies_at_base": copies[t["rule"]],
        })
    return {"bank": Path(here).resolve().relative_to(REPO).as_posix(), "base": base, "prompt": JPROMPT,
            "packet": "vault/programs/cognitive-economy/post-reset-packet.json",
            "excluded_rules_decided_by_r2": list(EXCLUDED_BY_R2),
            "missing": [r["rule"] for r in e1_rules() if r["rule"] not in have], "tasks": items}


def _index_text(idx):
    return json.dumps(idx, indent=1) + "\n"


# ---- CLI ---------------------------------------------------------------------------------------------

def _usage():
    print(__doc__)
    return 2


def main(argv):
    if not argv:
        return _usage()
    cmd, rest = argv[0], argv[1:]
    if cmd == "pins":
        if rest:
            return _usage()
        ok, bad = pins()
        for b in bad:
            print(f"PIN-MISMATCH {b}")
        print(f"PINS {ok}/13")
        return 0 if ok == 13 else 1
    if cmd == "validate":
        only, log, i = None, None, 0
        while i < len(rest):
            if rest[i] == "--only" and i + 1 < len(rest):
                only = [x for x in rest[i + 1].split(",") if x]
                i += 2
            elif rest[i] == "--log" and i + 1 < len(rest):
                log = rest[i + 1]
                i += 2
            else:
                return _usage()
        if only is not None and not only:
            return _usage()
        return validate(only, log)
    if cmd == "index":
        if len(rest) != 1 or rest[0] not in ("--stdout", "--write", "--check"):
            return _usage()
        idx = build_index()
        text = _index_text(idx)
        if rest[0] == "--stdout":
            print(text, end="")
            return 0
        if idx["missing"]:
            print(f"refusing: no task yet for {idx['missing']}", file=sys.stderr)
            return 1
        target = HERE / "index.json"
        if rest[0] == "--write":
            target.write_text(text, encoding="utf-8")
            print(f"wrote {target.name} ({len(idx['tasks'])} tasks)")
            return 0
        same = target.is_file() and target.read_text(encoding="utf-8") == text
        print("index.json matches" if same else "index.json is missing or differs")
        return 0 if same else 1
    return _usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
