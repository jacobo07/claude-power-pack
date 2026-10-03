#!/usr/bin/env python
"""test_skill_creation_gate.py -- pillar J gate drills (skill-capability, SC-J, decision D-02).

    python3 tools/test_skill_creation_gate.py

The frozen J rule: a new skill must declare its opportunity detector or why it has none; a gate refuses a skill
directory without the declaration. tools/skill_creation_gate.py is that gate; this file drives it from both poles.

What each V-SCG line proves:
  V-SCG-TRACER          one two-skill fixture from committed blobs: the undeclared skill is refused at DECLARED while
                        the declared detector skill passes all four clauses; declaring it, committing and committing the
                        render turns the verdict PASS (refuse, then admit)
  V-SCG-NO-SELF-ENROL   neither gate file enrols as a CO-12 adapter (DJ-06), with the real adapter as positive control
  V-SCG-DRILL-<id>      one drill: the observed fail set (and the outcome of each member) equals the declared row
                        EXACTLY, never a subset
  V-SCG-FLIP-<id>       for a singleton row, forcing that one clause PASS turns the verdict PASS and restoring it
                        restores the row: the clause is load-bearing
  V-SCG-EVERY-CLAUSE    the singleton rows cover all 7 clauses
  V-SCG-GIT-MISSING     the CLI under PATH=/nonexistent exits 1 with `SKILL_CREATION INCONCLUSIVE` naming `not found`
                        and no traceback; the same CLI with git on PATH says PASS on the same fixture
  V-SCG-LIVE            the gate on this checkout's HEAD; its fail set is printed (before 08-02 declares the repo
                        skills it is FAIL: every repo skill at DECLARED/FORM/TARGET/COVERAGE-AGREES plus EVIDENCE-CURRENT)

Fixtures are temp git repos built only from HEAD blobs of this checkout (never the working tree), with a fixed
identity, core.autocrlf=false, commit.gpgsign=false and an empty core.hooksPath. Drill skills are discovered by
coverage class at run time: CWST = the first member of class opportunity_detector, DSA = the first of class card,
S = the first of class none. Adapter files are copied from their committed blobs, never typed.

This file writes only under its own temporary directory. Output lines `[PASS] V-SCG-X ...` / `[FAIL] V-SCG-X ...`,
last line `SCG_PASS=<passed>/<total>`. Exit 0 only when every line is PASS.
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent))
import skill_coverage as sc  # noqa: E402
import skill_creation_gate as scg  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402

REPO = smd.REPO
GATE = _THIS.parent / "skill_creation_gate.py"
GIT_TIMEOUT = 60
X_DIR = "scg-readme-only"
UNTRACKED_PROBE = "tools/scg_untracked_probe.py"
EDITED_REASON = "a different valid reason written by the evidence drill"
RESULTS: list = []


def report(ok, gid, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {gid} {detail}".rstrip())
    RESULTS.append(bool(ok))


def fmt(s) -> str:
    return "{" + ",".join(sorted(s)) + "}"


# --------------------------------------------------------------------------- fixture plumbing

class FixtureError(Exception):
    pass


class Fx:
    def __init__(self, root: Path):
        self.root = root
        self.hooks_dir = root / "empty-hooks"
        self.hooks_dir.mkdir()
        self.exe = smd.vgm._git_exe()

    def git(self, repo, *a) -> str:
        cmd = [self.exe, "-C", str(repo), "-c", "user.name=scg", "-c", "user.email=scg@invalid",
               "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
               "-c", f"core.hooksPath={self.hooks_dir}", *a]
        p = subprocess.run(cmd, capture_output=True, timeout=GIT_TIMEOUT)
        if p.returncode != 0:
            err = p.stderr.decode("utf-8", "replace").strip().splitlines()
            raise FixtureError(f"git {a[0]} rc={p.returncode}: {err[-1] if err else 'no stderr'}")
        return p.stdout.decode("utf-8", "replace")

    def _config(self, repo):
        for k, v in (("user.name", "scg"), ("user.email", "scg@invalid"), ("core.autocrlf", "false"),
                     ("commit.gpgsign", "false"), ("core.hooksPath", str(self.hooks_dir))):
            self.git(repo, "config", k, v)

    def init(self, repo: Path):
        repo.mkdir(parents=True)
        self.git(repo, "init", "-q")
        self._config(repo)

    def clone(self, src: Path, dst: Path):
        self.git(self.root, "clone", "-q", "--local", str(src), str(dst))
        self._config(dst)

    def commit(self, repo, paths, msg, allow_empty=False):
        """Stage `paths` (none after a `git rm`, which already staged the removal) and commit."""
        if paths:
            self.git(repo, "add", "-A", "--", *paths)
        self.git(repo, "commit", "-q", "-m", msg, *(["--allow-empty"] if allow_empty else []))


def write(repo: Path, rel: str, data):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))


def head_blob(rel) -> bytes:
    out, why = smd.git_run(REPO, "cat-file", "blob", f"HEAD:{rel}")
    if out is None:
        raise FixtureError(f"HEAD:{rel}: {why}")
    return out


def undeclared(text: str) -> str:
    """`text` without the gate-grammar declaration block, so fixtures start from an undeclared skill whether or not
    HEAD already declares it (08-02 declared every repo skill). Removes a top-level `metadata:` line inside the
    frontmatter only when every child under it is an opportunity_detector / opportunity_detector_reason line;
    any other metadata shape is left alone, and insert_declaration then refuses it loudly."""
    m = scg._FM_RE.match(sc.lf(text))
    if m is None or "\r" in text:
        return text
    lines = m.group(1).split("\n")
    out, i = [], 0
    while i < len(lines):
        if scg.METADATA_LINE.match(lines[i]):
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and lines[j].strip():
                j += 1
            kids = lines[i + 1:j]
            if kids and all(scg.DETECTOR_LINE.match(k) or scg.REASON_LINE.match(k) for k in kids):
                i = j
                continue
        out.append(lines[i])
        i += 1
    stripped = text[:m.start(1)] + "\n".join(out) + text[m.end(1):]
    if scg.parse_declaration(stripped)["count"] or scg.parse_declaration(stripped)["reason"]:
        raise FixtureError("declaration left after stripping")
    return stripped


def render_evidence(fx, repo, msg="render evidence"):
    """record/render -> commit -> gate: the render of the current HEAD, committed."""
    r = scg.judge(repo)
    if r["verdict"] == scg.INCONCLUSIVE:
        raise FixtureError(f"render on INCONCLUSIVE judge: {r['reason']}")
    write(repo, scg.EVIDENCE_REL, scg.render(r))
    fx.commit(repo, [scg.EVIDENCE_REL], msg, allow_empty=True)


def md_rel(skill):
    return f"skills/{skill}/{scg.SKILL_MD}"


def read_md(repo, skill) -> str:
    return (repo / md_rel(skill)).read_bytes().decode("utf-8")


# --------------------------------------------------------------------------- what HEAD holds

class Seed:
    """Coverage classes, the dispatcher, its registered hooks and the adapter files, all from HEAD blobs."""

    def __init__(self):
        live = scg.judge(REPO)
        if live["verdict"] == scg.INCONCLUSIVE:
            raise FixtureError(f"live judge INCONCLUSIVE: {live['reason']}")
        self.live = live
        rows = {r["skill"]: r for r in live["skills"]}
        self.rows = rows
        by = {k: sorted(s for s, r in rows.items() if r["class"] == k and r["tracked"]) for k in sc.COVERAGE_CLASSES}
        if not by["opportunity_detector"] or not by["card"] or not by["none"]:
            raise FixtureError(f"need one skill per coverage class, got { {k: len(v) for k, v in by.items()} }")
        self.cwst, self.dsa, self.s = by["opportunity_detector"][0], by["card"][0], by["none"][0]
        self.cwst_path = sorted(scg.evidence_files(rows[self.cwst]["evidence"]))[0]
        self.dsa_hook = sorted(scg.evidence_files(rows[self.dsa]["evidence"]))[0]
        tracked, why = smd.tracked_paths(REPO, live["head"])
        if not tracked:
            raise FixtureError(f"ls-tree: {why}")
        disp = head_blob(sc.DISPATCHER_REL)
        self.files = {sc.DISPATCHER_REL: disp}
        for rel in sc.registered_hooks(sc.lf(disp.decode("utf-8", "replace"))):
            if rel in tracked:
                self.files[rel] = head_blob(rel)
        tool_rels = sorted(p for p in tracked if re.fullmatch(r"tools/[^/]+\.py", p))
        blobs = smd.vgm.batch_blobs(str(REPO), live["head"], tool_rels)
        texts = {r: sc.lf(b.decode("utf-8", "replace")) for r, (b, _) in blobs.items() if b}
        with tempfile.TemporaryDirectory() as empty:
            adapters = sc.opportunity_adapters(Path(empty), adapter_texts=texts)
        if not adapters:
            raise FixtureError("no CO-12 adapter at HEAD")
        self.adapter_rels = sorted({f for f, _ in adapters.values()})
        for rel in self.adapter_rels:
            self.files[rel] = blobs[rel][0]

    def declared(self, skill, text) -> str:
        r = self.rows[skill]
        return scg.insert_declaration(text, scg.declaration_lines(skill, r["class"], r["evidence"]))


# --------------------------------------------------------------------------- tracer (task 1)

def tracer(fx, seed):
    repo = fx.root / "tracer"
    fx.init(repo)
    for rel, data in seed.files.items():
        write(repo, rel, data)
    write(repo, md_rel(seed.cwst), seed.declared(seed.cwst, undeclared(head_blob(md_rel(seed.cwst)).decode("utf-8"))))
    s_text = undeclared(head_blob(md_rel(seed.s)).decode("utf-8"))
    write(repo, md_rel(seed.s), s_text)
    fx.commit(repo, ["."], "tracer: one declared, one undeclared")
    r1 = scg.judge(repo)
    rows = {r["skill"]: r for r in r1["skills"]}
    cw_ok = r1["verdict"] == scg.FAIL and all(c["outcome"] == scg.PASS for c in rows[seed.cwst]["clauses"].values())
    s_ok = rows[seed.s]["clauses"]["DECLARED"]["outcome"] == scg.FAIL
    exp1 = {f"{seed.s}:{c}" for c in scg.SKILL_CLAUSES} | {"EVIDENCE-CURRENT"}
    set1 = scg.fail_set(r1) == exp1
    write(repo, md_rel(seed.s), seed.declared(seed.s, s_text))
    fx.commit(repo, [md_rel(seed.s)], "tracer: declare the second skill")
    render_evidence(fx, repo)
    r2 = scg.judge(repo)
    ok = cw_ok and s_ok and set1 and r2["verdict"] == scg.PASS
    report(ok, "V-SCG-TRACER", f"refused={r1['verdict']} fail_set={fmt(scg.fail_set(r1))} "
                               f"admitted={r2['verdict']} fail_set={fmt(scg.fail_set(r2))}")


# --------------------------------------------------------------------------- base fixture and drills

def build_base(fx, seed) -> tuple:
    base = fx.root / "base"
    fx.init(base)
    tar, why = smd.git_run(REPO, "archive", "--format=tar", seed.live["head"], "skills")
    if tar is None:
        raise FixtureError(f"git archive: {why}")
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        tf.extractall(base, filter="data") if hasattr(tarfile, "data_filter") else tf.extractall(base)
    for md in sorted((base / "skills").glob(f"*/{scg.SKILL_MD}")):
        md.write_bytes(undeclared(md.read_bytes().decode("utf-8")).encode("utf-8"))
    for rel, data in seed.files.items():
        write(base, rel, data)
    fx.commit(base, ["."], "base: HEAD skills undeclared")
    first = scg.judge(base)
    if first["verdict"] == scg.INCONCLUSIVE:
        raise FixtureError(f"base judge: {first['reason']}")
    originals = {}
    for row in first["skills"]:
        if not row["tracked"]:
            continue
        orig = read_md(base, row["skill"])
        originals[row["skill"]] = orig
        lines = scg.declaration_lines(row["skill"], row["class"], row["evidence"])
        write(base, md_rel(row["skill"]), scg.insert_declaration(orig, lines))
    fx.commit(base, ["skills"], "base: every skill declared from its coverage class")
    render_evidence(fx, base)
    return base, originals


def _replace_md(fx, repo, skill, text, msg):
    write(repo, md_rel(skill), text)
    fx.commit(repo, [md_rel(skill)], msg)


def drill_table(seed, originals):
    cw, ds, s = seed.cwst, seed.dsa, seed.s
    p = seed.cwst_path
    s_reason = scg.declaration_lines(s, "none", [])[2].split(": ", 1)[1]

    def m_baseline(fx, repo):
        return None

    def m_undeclared_s(fx, repo):
        _replace_md(fx, repo, s, originals[s], "S undeclared")

    def m_duplicate(fx, repo):
        line = f"  {scg.DETECTOR_KEY}: {p}\n"
        t = read_md(repo, cw)
        if t.count(line) != 1:
            return f"precondition: {line!r} occurs {t.count(line)} times"
        _replace_md(fx, repo, cw, t.replace(line, line + line, 1), "CWST duplicate detector line")

    def m_dotslash(fx, repo):
        t = read_md(repo, cw)
        _replace_md(fx, repo, cw, t.replace(f"{scg.DETECTOR_KEY}: {p}\n", f"{scg.DETECTOR_KEY}: ./{p}\n", 1),
                    "CWST ./ path")

    def m_toplevel(fx, repo):
        lines = [f"{scg.DETECTOR_KEY}: none", f"{scg.REASON_KEY}: {s_reason}"]
        _replace_md(fx, repo, s, scg.insert_declaration(originals[s], lines), "S top-level keys")

    def m_no_reason(fx, repo):
        t = read_md(repo, s)
        out = "".join(ln for ln in t.splitlines(True) if scg.REASON_KEY not in ln)
        if out == t:
            return "precondition: no reason line to remove"
        _replace_md(fx, repo, s, out, "S none without reason")

    def m_untracked_path(fx, repo):
        write(repo, UNTRACKED_PROBE, "# present on disk, never committed\n")
        lines = ["metadata:", f"  {scg.DETECTOR_KEY}: {UNTRACKED_PROBE}"]
        _replace_md(fx, repo, s, scg.insert_declaration(originals[s], lines), "S declares an uncommitted path")
        st = fx.git(repo, "status", "--porcelain", "--", UNTRACKED_PROBE)
        if not st.startswith("??"):
            return f"precondition: probe is not untracked ({st.strip()!r})"

    def m_dsa_card(fx, repo):
        lines = ["metadata:", f"  {scg.DETECTOR_KEY}: {seed.dsa_hook}"]
        _replace_md(fx, repo, ds, scg.insert_declaration(originals[ds], lines), "DSA declares its card hook")

    def m_cwst_none(fx, repo):
        lines = ["metadata:", f"  {scg.DETECTOR_KEY}: none", f"  {scg.REASON_KEY}: declared none for the drill"]
        _replace_md(fx, repo, cw, scg.insert_declaration(originals[cw], lines), "CWST declares none")

    def m_readme_only(fx, repo):
        write(repo, f"skills/{X_DIR}/README.md", "# a skill directory without SKILL.md\n")
        fx.commit(repo, [f"skills/{X_DIR}"], "X README only")

    def m_all_removed(fx, repo):
        fx.git(repo, "rm", "-r", "-q", "--", "skills")
        fx.commit(repo, [], "all skills removed")

    def m_cwst_removed(fx, repo):
        fx.git(repo, "rm", "-r", "-q", "--", f"skills/{cw}")
        fx.commit(repo, [], "CWST removed")

    def m_floor_one(fx, repo):
        others = sorted(d.name for d in (repo / "skills").iterdir() if d.is_dir() and d.name != cw)
        fx.git(repo, "rm", "-r", "-q", "--", *[f"skills/{o}" for o in others])
        fx.commit(repo, [], "only CWST left")

    def m_reason_edit(fx, repo):
        t = read_md(repo, s)
        if s_reason not in t:
            return "precondition: S reason not found"
        _replace_md(fx, repo, s, t.replace(s_reason, EDITED_REASON, 1), "S reason edited, not re-rendered")

    def m_evidence_removed(fx, repo):
        fx.git(repo, "rm", "-q", "--", scg.EVIDENCE_REL)
        fx.commit(repo, [], "evidence removed")

    def m_crlf(fx, repo):
        t = read_md(repo, s)
        _replace_md(fx, repo, s, t.replace("\r\n", "\n").replace("\n", "\r\n"), "S CRLF")
        blob = fx.git(repo, "cat-file", "blob", f"HEAD:{md_rel(s)}")
        if "\r\n" not in blob:
            return "precondition: committed blob is not CRLF"

    def m_worktree_only(fx, repo):
        write(repo, md_rel(s), originals[s])
        st = fx.git(repo, "status", "--porcelain", "--", md_rel(s))
        if not st.strip():
            return "precondition: working file not modified"

    U, F = scg.UNMEASURED, scg.FAIL
    four = {f"{s}:DECLARED": F, f"{s}:FORM": U, f"{s}:TARGET": U, f"{s}:COVERAGE-AGREES": U}
    x4 = {f"{X_DIR}:DECLARED": F, f"{X_DIR}:FORM": U, f"{X_DIR}:TARGET": U, f"{X_DIR}:COVERAGE-AGREES": U}
    # (id, mutate, expected {key: outcome}, re-render after the mutation)
    return [
        ("BASELINE", m_baseline, {}, False),
        ("UNDECLARED-S", m_undeclared_s, four, True),
        ("DUPLICATE-CWST", m_duplicate, {f"{cw}:DECLARED": F}, True),
        ("DOTSLASH-CWST", m_dotslash, {f"{cw}:FORM": F}, True),
        ("TOPLEVEL-S", m_toplevel, {f"{s}:FORM": F}, True),
        ("NONE-NO-REASON-S", m_no_reason, {f"{s}:TARGET": F}, True),
        ("UNTRACKED-PATH-S", m_untracked_path, {f"{s}:TARGET": F, f"{s}:COVERAGE-AGREES": F}, True),
        ("DSA-DECLARES-CARD", m_dsa_card, {f"{ds}:COVERAGE-AGREES": F}, True),
        ("CWST-DECLARES-NONE", m_cwst_none, {f"{cw}:COVERAGE-AGREES": F}, True),
        ("README-ONLY-DIR", m_readme_only, x4, True),
        ("ALL-SKILLS-REMOVED", m_all_removed, {"FLOOR": U, "POSITIVE-CONTROL": U}, True),
        ("CWST-REMOVED", m_cwst_removed, {"POSITIVE-CONTROL": F}, True),
        ("FLOOR-ONE", m_floor_one, {"FLOOR": F}, True),
        ("REASON-EDIT-UNRENDERED", m_reason_edit, {"EVIDENCE-CURRENT": F}, False),
        ("EVIDENCE-REMOVED", m_evidence_removed, {"EVIDENCE-CURRENT": U}, False),
        ("CRLF-S", m_crlf, {}, True),
        ("WORKTREE-ONLY-S", m_worktree_only, {}, False),
    ]


def outcomes(result) -> dict:
    out = {cid: c["outcome"] for cid, c in result["gate"].items() if c["outcome"] != scg.PASS}
    for row in result["skills"]:
        out.update({f"{row['skill']}:{cid}": c["outcome"] for cid, c in row["clauses"].items()
                    if c["outcome"] != scg.PASS})
    return out


def _forced(ctx, member=None):
    return {"outcome": scg.PASS, "reason": "forced PASS by the flip drill"}


def run_drills(fx, base, seed, originals) -> set:
    flipped = set()
    for did, mutate, expected, rerender in drill_table(seed, originals):
        repo = fx.root / f"drill-{did}"
        try:
            fx.clone(base, repo)
            why = mutate(fx, repo)
            if why:
                report(False, f"V-SCG-DRILL-{did}", why)
                continue
            if rerender:
                render_evidence(fx, repo)
            r = scg.judge(repo)
        except FixtureError as e:
            report(False, f"V-SCG-DRILL-{did}", f"fixture: {e}")
            continue
        got = outcomes(r)
        want_verdict = scg.PASS if not expected else scg.FAIL
        ok = got == expected and r["verdict"] == want_verdict
        detail = (f"expected={fmt(f'{k}={v}' for k, v in expected.items())} "
                  f"observed={fmt(f'{k}={v}' for k, v in got.items())} verdict={r['verdict']}")
        report(ok, f"V-SCG-DRILL-{did}", detail)
        if len(expected) == 1 and ok:
            key = next(iter(expected))
            clause = key.split(":")[-1]
            # The render records every clause outcome except EVIDENCE-CURRENT, so forcing any other clause changes
            # what the evidence must say: the forced world gets its own render (in a copy, record/render -> commit
            # -> gate), else the flip would only prove EVIDENCE-CURRENT. EVIDENCE-CURRENT itself is flipped on the
            # drill repo as is, because re-rendering would repair the very thing the drill broke.
            frepo = fx.root / f"flip-{did}"
            saved = scg.CLAUSES[clause]
            try:
                scg.CLAUSES[clause] = _forced
                if clause == "EVIDENCE-CURRENT":
                    forced = scg.judge(repo)
                else:
                    fx.clone(repo, frepo)
                    render_evidence(fx, frepo, "render under the forced clause")
                    forced = scg.judge(frepo)
            except FixtureError as e:
                forced = {"verdict": f"fixture error {e}"}
            finally:
                scg.CLAUSES[clause] = saved
            again = scg.judge(repo)
            fok = forced["verdict"] == scg.PASS and outcomes(again) == expected
            if fok:
                flipped.add(clause)
            report(fok, f"V-SCG-FLIP-{did}", f"{clause} forced PASS -> verdict={forced['verdict']}; "
                                            f"restored -> {fmt(outcomes(again))}")
    return flipped


# --------------------------------------------------------------------------- other lines

def no_self_enrol(seed):
    texts = {f"tools/{f.name}": f.read_text(encoding="utf-8") for f in (GATE, _THIS)}
    bad = [rel for rel, t in texts.items() if sc.KIND_LINE.search(t) or sc.CAP_LINE.search(t)]
    with tempfile.TemporaryDirectory() as empty:
        mine = sc.opportunity_adapters(Path(empty), adapter_texts=texts)
        control = sc.opportunity_adapters(Path(empty), adapter_texts={
            rel: seed.files[rel].decode("utf-8", "replace") for rel in seed.adapter_rels})
    ok = not bad and not mine and bool(control)
    report(ok, "V-SCG-NO-SELF-ENROL", f"gate files enrolled={sorted(mine)} offending={bad}; "
                                      f"control enrols {sorted(control)}")


def git_missing(base):
    py = "/usr/bin/python3" if Path("/usr/bin/python3").is_file() else sys.executable
    env = {"PATH": "/nonexistent", "HOME": os.environ.get("HOME", ""), "LANG": "C.UTF-8"}
    p = subprocess.run([py, str(GATE), "--repo", str(base)], capture_output=True, timeout=120, env=env)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    last = (p.stdout.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
    ctl = subprocess.run([py, str(GATE), "--repo", str(base)], capture_output=True, timeout=120)
    ctl_last = (ctl.stdout.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
    ok = (p.returncode == 1 and last.startswith("SKILL_CREATION INCONCLUSIVE") and "not found" in last
          and "Traceback" not in out and ctl.returncode == 0 and ctl_last.startswith("SKILL_CREATION PASS"))
    report(ok, "V-SCG-GIT-MISSING", f"rc={p.returncode} last={last!r}; control rc={ctl.returncode} last={ctl_last!r}")


def live():
    r = scg.judge(REPO)
    fs = scg.fail_set(r)
    report(r["verdict"] == scg.PASS, "V-SCG-LIVE",
           f"verdict={r['verdict']} population={len(r['population'])} fail_set_size={len(fs)} fail_set={fmt(fs)}"
           + (f" reason={r['reason']}" if r["verdict"] == scg.INCONCLUSIVE else ""))


def main() -> int:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="scg-") as tmp:
        try:
            fx = Fx(Path(tmp))
            seed = Seed()
            print(f"# discovered CWST={seed.cwst} ({seed.cwst_path}) DSA={seed.dsa} ({seed.dsa_hook}) S={seed.s} "
                  f"adapters={seed.adapter_rels}")
            tracer(fx, seed)
            no_self_enrol(seed)
            base, originals = build_base(fx, seed)
            flipped = run_drills(fx, base, seed, originals)
            all7 = set(scg.SKILL_CLAUSES) | set(scg.GATE_CLAUSES)
            report(flipped == all7, "V-SCG-EVERY-CLAUSE", f"flipped={fmt(flipped)} missing={fmt(all7 - flipped)}")
            git_missing(base)
        except (FixtureError, FileNotFoundError) as e:
            report(False, "V-SCG-FIXTURE", f"{type(e).__name__}: {e}")
    live()
    print(f"# wall={time.monotonic() - t0:.1f}s")
    passed = sum(RESULTS)
    print(f"SCG_PASS={passed}/{len(RESULTS)}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
