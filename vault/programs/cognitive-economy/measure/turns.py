#!/usr/bin/env python
"""turns.py -- pillar H (turns per verified advancement) and J (non-convergence). Zero model calls.

Population: every model call the usage index holds for D-W7 (start < ts <= end, the predicate of
`usage_index.window`), read through a READ-ONLY sqlite connection. Each call is found in the
transcript the index assigned it to, by its index key `<message.id>|<requestId>`, so the population
is D-W7 by construction (control: calls classified + calls without features == D-W7 calls).

Features of a call (observable state only):
  prev_error : the user turn just before it carried a tool_result with is_error=true
  repeat     : every tool it issued was issued before in the same transcript with identical
               name + input, with no edit and no compaction in between
  cats       : one category per tool_use --
               edit_committed   Write/Edit/MultiEdit/NotebookEdit on a file a commit in the file's
                                repo touched within [call - 300 s, call + 24 h] (any branch)
               edit_uncommitted the same, in a git repo, no such commit
               edit_unknown     the same, but the repo's `git log` failed: no class claims it (UNSETTLED)
               edit_bookkeeping edit of a record file (BOOKKEEPING_PATH), in or out of a repo
               edit_outside     edit of a file outside any git repo, not a record file
               test             shell command that runs a test or gate (TEST_CMD | GATE_CMD)
               git              shell command that is git bookkeeping (GIT_CMD)
               shell            any other shell command
               coord            orchestration / conversation tools (COORD_TOOLS)
               bk               task bookkeeping tools (BK_TOOLS)
               read             Read/Grep/Glob/Web*/LSP
               other            anything else (MCP etc.)
  text_only  : the call issued no tool_use

Classes, first match wins (the rule for each is the line):
  recovery       prev_error
  repeat         repeat
  proof          any test
  bookkeeping    any edit_bookkeeping, git or bk
  advancing      any edit_committed
  non_convergent any edit_uncommitted
  coordination   any coord, or text_only
  unsettled      everything else (exploration, execution, scratch edits): its value is not
                 observable, so it is kept apart from waste (UNSETTLED is not WASTE)

J (pre-registered reading, written before any figure was computed): the frozen rule says
"non-advancing turns of interactive roots >= 3 % of D-W7 earns a detector proposal". A
non-convergence detector can only act on turns that show non-convergence, so J's decision input
is the weighted share of repeat + recovery + non_convergent turns in HUMAN-rooted trees. The
broader share (every class except advancing) is reported beside it and is not the decision input.

Modes:
  --measure [--json OUT]       full D-W7 run
  --freeze OUT                 also write a frozen feature sample (cats only, no paths or text) and
                               the sha256 of its labels, for the H gate
  --sample N --seed S OUT      a blind labelling sheet: N calls, tool names + truncated inputs,
                               no classifier label
  --score SHEET                compare a labelled sheet with the classifier (agreement + a
                               shuffled-label negative control)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
DB = Path.home() / ".claude" / "state" / "usage_index" / "index.sqlite"
W_START = datetime(2026, 9, 26, tzinfo=timezone.utc).timestamp()
W_END = datetime(2026, 10, 3, tzinfo=timezone.utc).timestamp()
DW7_CALLS = 75969
DW7_WEIGHTED = 3325101725
GRACE_S, LATER_S = 300, 24 * 3600

EDIT_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
SHELL_TOOLS = {"Bash", "PowerShell"}
COORD_TOOLS = {"Agent", "Task", "SendMessage", "Skill", "ToolSearch", "AskUserQuestion", "ScheduleWakeup",
               "EnterWorktree", "ExitWorktree", "EnterPlanMode", "ExitPlanMode", "Monitor", "TaskStop",
               "TaskOutput", "ListAgents", "CronCreate", "CronDelete", "CronList", "PushNotification",
               "Workflow", "Artifact", "RemoteTrigger", "SendFeedback"}
BK_TOOLS = {"TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TodoWrite"}
READ_TOOLS = {"Read", "Grep", "Glob", "WebFetch", "WebSearch", "LSP", "NotebookRead"}
BOOKKEEPING_PATH = re.compile(
    r"(?i)([\\/]\.planning[\\/]|[\\/]memory[\\/]|MEMORY\.md$|RESUMPTION_FILE|[\\/]STATE\.md$|ROADMAP\.md$|"
    r"SUMMARY\.md$|VERIFICATION\.md$|EVIDENCE\.md$|CHANGELOG|HANDOFF|[\\/]\.claude[\\/](state|cache|jobs)[\\/])")
GATE_CMD = re.compile(r"(?i)(gate_\w+\.py|--selftest\b|--pillar\b|--final\b|\btsc\b|\bruff\b|\bmypy\b|"
                      r"\beslint\b|\bverify\w*\.py\b|_PASS=)")
GIT_CMD = re.compile(r"(?i)(\bgit(\.exe)?['\"]?|\$g)\s+(-C\s+\S+\s+)?(commit|add|status|log|diff|show|branch|"
                     r"rev-parse|fetch|push|merge|rebase|stash|tag|worktree)\b")
CLASSES = ("recovery", "repeat", "proof", "bookkeeping", "advancing", "non_convergent", "coordination",
           "unsettled")


def classify(f: dict, order: tuple = CLASSES) -> str:
    """Pure: a feature row -> its class. `order` exists only so the gate can drive a red branch."""
    cats = set(f.get("cats") or ())
    tests = {
        "recovery": bool(f.get("prev_error")),
        "repeat": bool(f.get("repeat")),
        "proof": "test" in cats,
        "bookkeeping": bool(cats & {"edit_bookkeeping", "git", "bk"}),
        "advancing": "edit_committed" in cats,
        "non_convergent": "edit_uncommitted" in cats,
        "coordination": "coord" in cats or bool(f.get("text_only")),
        "unsettled": True,
    }
    return next(c for c in order if tests[c])


def labels_sha(rows: list[dict], order: tuple = CLASSES) -> str:
    return hashlib.sha256("\n".join(classify(r, order) for r in rows).encode()).hexdigest()


# ------------------------------------------------------------------ extraction

def ro_connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def shell_cat(cmd: str) -> str:
    import root_progress as rp
    if rp.TEST_CMD.search(cmd) or GATE_CMD.search(cmd):
        return "test"
    if GIT_CMD.search(cmd):
        return "git"
    return "shell"


def tool_cat(name: str, inp: dict):
    """(category, edit path or None). Edit categories are resolved later, after the commit join."""
    if name in EDIT_TOOLS:
        return "edit", inp.get(EDIT_TOOLS[name])
    if name in SHELL_TOOLS:
        return shell_cat(str(inp.get("command", ""))), None
    if name in COORD_TOOLS:
        return "coord", None
    if name in BK_TOOLS:
        return "bk", None
    if name in READ_TOOLS:
        return "read", None
    return "other", None


def scan_file(path: str, wanted: set) -> dict:
    """{index key: feature} for the calls of `wanted` found in this transcript."""
    out: dict = {}
    seen: set = set()
    err_pending = False
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return out
    with fh:
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            if o.get("isCompactSummary") or (o.get("type") == "system" and o.get("subtype") == "compact_boundary"):
                seen.clear()
            m = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = m.get("content") if isinstance(m.get("content"), list) else []
            if o.get("type") == "user":
                if any(isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error") for c in content):
                    err_pending = True
                continue
            if o.get("type") != "assistant" or not isinstance(m.get("usage"), dict):
                continue
            key = f"{m.get('id')}|{o.get('requestId')}"
            if key not in out:
                out[key] = {"prev_error": err_pending, "tools": [], "reps": [], "ts": o.get("timestamp"),
                            "cwd": o.get("cwd")}
                err_pending = False
            f = out[key]
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                name, inp = c.get("name"), c.get("input") if isinstance(c.get("input"), dict) else {}
                cat, epath = tool_cat(name, inp)
                if cat == "edit":
                    seen.clear()
                    f["reps"].append(False)
                else:
                    k2 = hashlib.sha1((str(name) + json.dumps(inp, sort_keys=True, default=str))
                                      .encode("utf-8", "replace")).digest()
                    f["reps"].append(k2 in seen)
                    seen.add(k2)
                if epath and o.get("cwd") and not Path(epath).is_absolute():
                    epath = str(Path(o["cwd"]) / epath)
                f["tools"].append((cat, epath))
    return {k: v for k, v in out.items() if k in wanted}


def ts_of(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


_TOP_CACHE: dict = {}


def find_top(d: str):
    """The repo top of directory `d`, found in-process: the nearest ancestor holding a `.git`
    entry (a directory, or a file for worktrees and submodules) -- what `git rev-parse
    --show-toplevel` answers for a normal tree, without one subprocess per directory. Every
    directory on the walk is cached, so siblings and children cost one dict lookup."""
    walked = []
    p = Path(d)
    top = None
    while True:
        key = str(p)
        if key in _TOP_CACHE:
            top = _TOP_CACHE[key]
            break
        walked.append(key)
        try:
            if (p / ".git").exists():
                top = p
                break
        except OSError:
            pass
        if p.parent == p:
            break
        p = p.parent
    for key in walked:
        _TOP_CACHE[key] = top
    return top


class Commits:
    """Commit join: is a path touched by a commit of its repo within [t - GRACE, t + LATER]?
    One `git log` per repo over the whole window, indexed path -> sorted commit times."""

    def __init__(self):
        import root_progress as rp
        self.rp = rp
        self.repo_commits: dict = {}   # norm(top) -> raw commit list (also fed to root_progress)
        self.repo_index: dict = {}     # norm(top) -> {norm(path): sorted [ct]}
        self.failed: dict = {}         # norm(top) -> why its log could not be read
        self.raw_by_store: dict = {}   # git common dir -> [(sha, ct, [relative paths])] or None

    @staticmethod
    def common_dir(top: Path) -> str:
        """The object store a work tree shares with its siblings: `.git` itself, or for a linked
        worktree the `commondir` of the gitdir its `.git` file names. `--all` answers the same
        commits for every worktree of one store, so the log is fetched once per store."""
        dotgit = top / ".git"
        try:
            if dotgit.is_file():
                gd = Path(dotgit.read_text(encoding="utf-8", errors="replace").split("gitdir:", 1)[1].strip())
                gd = gd if gd.is_absolute() else (top / gd)
                cd = gd / "commondir"
                if cd.is_file():
                    c = Path(cd.read_text(encoding="utf-8").strip())
                    gd = c if c.is_absolute() else gd / c
                return os.path.normcase(os.path.normpath(str(gd.resolve())))
        except (OSError, IndexError):
            pass
        return os.path.normcase(os.path.normpath(str(dotgit)))

    def git_log(self, top: Path, since: float, until: float):
        """root_progress._commits' query and parsing, with three differences that matter for a
        measurement: a 600 s timeout (`--all --name-only` on a ~10k-ref repo exceeds the original
        60 s), a non-zero exit is a FAILURE (None) rather than an empty history, and the log is
        fetched once per object store (`--no-renames`: a rename lists both paths, a superset for
        "touched")."""
        def iso(t):
            return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        store = self.common_dir(top)
        if store not in self.raw_by_store:
            t0 = datetime.now().timestamp()
            try:
                r = subprocess.run([self.rp.GIT, "-C", str(top), "log", "--all", "--no-renames",
                                    f"--since={iso(since)}", f"--until={iso(until)}", "--name-only",
                                    "--format=%x00%H %ct"], capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=600)
                rc, why = r.returncode, f"rc {r.returncode}"
            except (OSError, subprocess.SubprocessError) as exc:
                r, rc, why = None, -1, type(exc).__name__
            print(f"[git] {top} store={store} rc={rc} {datetime.now().timestamp() - t0:.0f}s",
                  file=sys.stderr, flush=True)
            raw = None
            if rc == 0:
                raw = []
                for block in r.stdout.split("\x00")[1:]:
                    lines = [x for x in block.splitlines() if x.strip()]
                    if lines:
                        sha, ct = lines[0].split()
                        raw.append((sha, float(ct), lines[1:]))
            else:
                self.failed[store] = why
            self.raw_by_store[store] = raw
        raw = self.raw_by_store[store]
        if raw is None:
            return None
        return [(sha, ct, {self.rp._norm(top / f) for f in fs}) for sha, ct, fs in raw]

    def commits(self, top: Path):
        key = self.rp._norm(top)
        if key not in self.repo_commits:
            cs = self.git_log(Path(top), W_START - GRACE_S - 7 * 86400, W_END + LATER_S)
            self.repo_commits[key] = cs
            if cs is not None:
                idx = defaultdict(list)
                for _sha, ct, ch in cs:
                    for n in ch:
                        idx[n].append(ct)
                self.repo_index[key] = {n: sorted(v) for n, v in idx.items()}
        return self.repo_commits[key]

    def status(self, path: str, t: float) -> str:
        from bisect import bisect_left
        if BOOKKEEPING_PATH.search(path or ""):
            return "edit_bookkeeping"
        top = find_top(str(Path(path).parent))
        if top is None:
            return "edit_outside"
        if self.commits(top) is None:
            return "edit_unknown"      # the repo's log could not be read: UNSETTLED, never non-convergent
        times = self.repo_index[self.rp._norm(top)].get(self.rp._norm(path))
        if not times:
            return "edit_uncommitted"
        i = bisect_left(times, t - GRACE_S)
        return "edit_committed" if i < len(times) and times[i] <= t + LATER_S else "edit_uncommitted"

    def patch_root_progress(self):
        """Hand root_progress (imported, never edited) the same in-process repo discovery and the
        already-fetched commit logs, filtered to its span; a span outside the cached range falls
        back to its own `git log`."""
        rp, orig = self.rp, self.rp._commits
        lo, hi = W_START - GRACE_S - 7 * 86400, W_END + LATER_S

        def commits(top, since, until):
            if since >= lo and until <= hi:
                cs = self.commits(Path(top))
                if cs is not None:
                    return [c for c in cs if since <= c[1] <= until]
            return orig(top, since, until)

        rp.repo_top = lambda cwd: find_top(str(cwd)) if Path(str(cwd)).is_dir() else None
        rp._commits = commits


def extract() -> tuple[list[dict], dict]:
    import fanout_ledger as fl
    con = ro_connect()
    rows = con.execute("SELECT k, file, ts, is_sub, prompt_id, inp, cw, cr, out FROM calls "
                       "WHERE ts > ? AND ts <= ?", (W_START, W_END)).fetchall()
    prompts = {r[0]: r[1:] for r in con.execute(
        "SELECT p.prompt_id, p.kind, p.source, f.title, f.entrypoint FROM prompts p "
        "LEFT JOIN files f ON f.path = p.file")}
    resolve = fl.root_resolver(con)
    by_file = defaultdict(list)
    for r in rows:
        by_file[r[1]].append(r)
    del rows
    commits = Commits()
    commits.patch_root_progress()
    feats, missing = [], 0
    t0 = datetime.now().timestamp()
    for i, (fp, rs) in enumerate(by_file.items()):
        if i % 200 == 0:
            print(f"[extract] {i}/{len(by_file)} files, {len(feats)} calls, "
                  f"{datetime.now().timestamp() - t0:.0f}s", file=sys.stderr, flush=True)
        found = scan_file(fp, {r[0] for r in rs})
        root_pid = resolve(fp) if rs[0][3] else None
        for k, _f, ts, is_sub, pid, inp, cw, cr, out in rs:
            w = inp + cr * 0.1 + cw * 2 + out * 5
            rp_id = root_pid if is_sub else pid
            pr = prompts.get(rp_id)
            root_class = fl.classify_root(pr[0], pr[1], pr[3], pr[2]) if pr else "UNKNOWN"
            g = found.get(k)
            if g is None:
                missing += 1
                feats.append({"k": k, "w": w, "is_sub": bool(is_sub), "root": rp_id, "root_class": root_class,
                              "featureless": True, "cats": [], "prev_error": False, "repeat": False,
                              "text_only": False})
                continue
            cats = []
            for cat, epath in g["tools"]:
                cats.append(commits.status(epath, ts) if cat == "edit" else cat)
            feats.append({"k": k, "w": w, "is_sub": bool(is_sub), "root": rp_id, "root_class": root_class,
                          "cats": sorted(set(cats)), "prev_error": g["prev_error"],
                          "repeat": bool(g["reps"]) and all(g["reps"]), "text_only": not g["tools"]})
    con.close()
    return feats, {"files": len(by_file), "featureless": missing, "repos": len(commits.repo_commits),
                   "repos_log_failed": commits.failed}


def aggregate(feats: list[dict]) -> dict:
    tot_w = sum(f["w"] for f in feats)
    by = defaultdict(lambda: [0, 0.0])
    inter = defaultdict(lambda: [0, 0.0])
    for f in feats:
        c = "featureless" if f.get("featureless") else classify(f)
        by[c][0] += 1
        by[c][1] += f["w"]
        if f["root_class"] == "HUMAN":
            inter[c][0] += 1
            inter[c][1] += f["w"]
    pct = lambda x: round(100 * x / DW7_WEIGHTED, 4)
    table = {c: {"calls": n, "weighted_pct_DW7": pct(w)} for c, (n, w) in sorted(by.items())}
    human = {c: {"calls": n, "weighted_pct_DW7": pct(w)} for c, (n, w) in sorted(inter.items())}
    j_input = sum(inter[c][1] for c in ("repeat", "recovery", "non_convergent"))
    broad = sum(w for c, (n, w) in inter.items() if c not in ("advancing",))
    return {"calls": len(feats), "weighted": round(tot_w), "weighted_pct_DW7": pct(tot_w),
            "classes": table, "human_rooted": human,
            "J_decision_input_pct_DW7": pct(j_input), "J_broad_non_advancing_pct_DW7": pct(broad)}


def per_root(feats: list[dict], n: int = 40) -> dict:
    """Turns per commit / per green test for the costliest roots, via tools/root_progress.py
    (imported, never edited). Coverage = their share of the window's weighted spend."""
    import root_progress as rp
    con = ro_connect()
    by_root = defaultdict(list)
    for f in feats:
        by_root[f["root"]].append(f)
    by_root.pop(None, None)
    ranked = sorted(by_root.items(), key=lambda kv: -sum(f["w"] for f in kv[1]))[:n]
    rows = []
    for pid, fs in ranked:
        p = rp.root_progress(con, pid)
        turns = len(fs)
        commits = (p.get("commits_in_span") or 0)
        greens = (p.get("tests") or {}).get("GREEN", 0)
        cls = Counter("featureless" if f.get("featureless") else classify(f) for f in fs)
        rows.append({"root": pid, "root_class": fs[0]["root_class"], "turns": turns,
                     "weighted_pct_DW7": round(100 * sum(f["w"] for f in fs) / DW7_WEIGHTED, 4),
                     "state": p.get("state"), "commits_in_span": commits, "green_tests": greens,
                     "turns_per_commit": round(turns / commits, 1) if commits else None,
                     "turns_per_green_test": round(turns / greens, 1) if greens else None,
                     "classes": dict(cls)})
    con.close()
    adv = [r for r in rows if r["state"] == "ADVANCED"]
    tpc = sorted(r["turns_per_commit"] for r in rows if r["turns_per_commit"])
    return {"roots_judged": len(rows), "roots_total": len(by_root),
            "coverage_weighted_pct_DW7": round(sum(r["weighted_pct_DW7"] for r in rows), 4),
            "states": dict(Counter(r["state"] for r in rows)),
            "median_turns_per_commit": tpc[len(tpc) // 2] if tpc else None,
            "advanced_roots": len(adv), "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--freeze")
    ap.add_argument("--sample", type=int)
    ap.add_argument("--seed", type=int, default=20261003)
    ap.add_argument("--sheet")
    ap.add_argument("--score")
    a = ap.parse_args(argv)
    if a.score:
        return score(a.score)
    feats, meta = extract()
    agg = aggregate(feats)
    control = {"population_calls": len(feats), "dw7_calls": DW7_CALLS,
               "population_equals_dw7": len(feats) == DW7_CALLS, **meta}
    if a.sample:
        return write_sheet(feats, a.sample, a.seed, a.sheet)
    res = {"window": "D-W7", "control": control, "aggregate": agg, "per_root": per_root(feats)}
    if a.freeze:
        rnd = random.Random(a.seed)
        sample = [{k: f[k] for k in ("cats", "prev_error", "repeat", "text_only")}
                  for f in rnd.sample([f for f in feats if not f.get("featureless")], 3000)]
        frozen = {"seed": a.seed, "n": len(sample), "classes_order": list(CLASSES),
                  "labels_sha256": labels_sha(sample), "rows": sample}
        Path(a.freeze).write_text(json.dumps(frozen, indent=0, sort_keys=True), encoding="utf-8", newline="\n")
        res["frozen"] = {"path": a.freeze, "labels_sha256": frozen["labels_sha256"]}
    blob = json.dumps(res, indent=1, sort_keys=True, default=str)
    if a.json:
        Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
    print("result_sha256", hashlib.sha256(blob.encode()).hexdigest())
    print("control", json.dumps(control))
    print("aggregate", json.dumps(agg))
    pr = res["per_root"]
    print("per_root", json.dumps({k: v for k, v in pr.items() if k != "rows"}))
    return 0 if control["population_equals_dw7"] else 1


# ------------------------------------------------------------------ labelling controls

def write_sheet(feats, n, seed, out) -> int:
    """A blind sheet: what each sampled call DID (tool names + short inputs), never its class."""
    rnd = random.Random(seed)
    pick = rnd.sample([f for f in feats if not f.get("featureless")], n)
    con = ro_connect()
    rows = []
    for f in pick:
        fp = con.execute("SELECT file FROM calls WHERE k=?", (f["k"],)).fetchone()[0]
        rows.append({"k": f["k"], "file": fp, "label": None, "did": describe(fp, f["k"])})
    con.close()
    Path(out).write_text(json.dumps(rows, indent=1), encoding="utf-8", newline="\n")
    print(f"sheet {out}: {len(rows)} calls, unlabelled")
    return 0


def describe(fp: str, key: str) -> dict:
    """Tool uses of one call (inputs truncated) and whether an error result preceded it."""
    tools, err, prev_err = [], None, False
    for raw in open(fp, encoding="utf-8", errors="replace"):
        try:
            o = json.loads(raw)
        except ValueError:
            continue
        m = o.get("message") if isinstance(o.get("message"), dict) else {}
        content = m.get("content") if isinstance(m.get("content"), list) else []
        if o.get("type") == "user":
            prev_err = any(isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error")
                           for c in content) or (prev_err and not content)
            continue
        if f"{m.get('id')}|{o.get('requestId')}" != key:
            if o.get("type") == "assistant" and isinstance(m.get("usage"), dict) and err is None:
                prev_err = False
            continue
        if err is None:
            err = prev_err
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                tools.append({"name": c.get("name"), "input": json.dumps(c.get("input"), default=str)[:300]})
            elif isinstance(c, dict) and c.get("type") == "text":
                tools.append({"name": "<text>", "input": c.get("text", "")[:200]})
    return {"error_before": bool(err), "uses": tools}


def score(sheet: str) -> int:
    rows = json.loads(Path(sheet).read_text(encoding="utf-8"))
    feats, _ = extract()
    by_k = {f["k"]: f for f in feats}
    pairs = [(r["label"], classify(by_k[r["k"]])) for r in rows if r.get("label") and r["k"] in by_k]
    agree = sum(h == c for h, c in pairs)
    rnd = random.Random(7)
    shuffled = [c for _, c in pairs]
    rnd.shuffle(shuffled)
    agree_shuf = sum(h == s for (h, _), s in zip(pairs, shuffled))
    conf = Counter(f"{h}->{c}" for h, c in pairs if h != c)
    out = {"labelled": len(pairs), "agreement": round(agree / len(pairs), 3) if pairs else None,
           "shuffled_agreement": round(agree_shuf / len(pairs), 3) if pairs else None,
           "disagreements": dict(conf)}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
