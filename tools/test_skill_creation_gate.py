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
  V-SCG-ROUTER-DESCRIPTION  inserting the declaration leaves skill_index._read_frontmatter's (name, description)
                        unchanged on block-scalar, plain, reordered and CRLF frontmatter and on every repo skill; the
                        old append-at-end placement is the positive control that changes it
  V-SCG-REASON-YAML-SCALARS  the reason grammar refuses YAML null / bool / number / date literals and admits text,
                        including every generated reason (cross-checked with PyYAML when it is importable)
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
from modules.skill_router import skill_index as si  # noqa: E402  (scg put the repo root on sys.path)

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

    def m_duplicate_reason(fx, repo):
        line = f"  {scg.REASON_KEY}: {s_reason}\n"
        t = read_md(repo, s)
        if t.count(line) != 1:
            return f"precondition: {line!r} occurs {t.count(line)} times"
        _replace_md(fx, repo, s, t.replace(line, line + line, 1), "S duplicate reason line")

    def m_dotslash(fx, repo):
        t = read_md(repo, cw)
        _replace_md(fx, repo, cw, t.replace(f"{scg.DETECTOR_KEY}: {p}\n", f"{scg.DETECTOR_KEY}: ./{p}\n", 1),
                    "CWST ./ path")

    def path_edit(new, msg):
        def m(fx, repo):
            t = read_md(repo, cw)
            line = f"{scg.DETECTOR_KEY}: {p}\n"
            if t.count(line) != 1:
                return f"precondition: {line!r} occurs {t.count(line)} times"
            _replace_md(fx, repo, cw, t.replace(line, f"{scg.DETECTOR_KEY}: {new}\n", 1), msg)
        return m

    def m_toplevel(fx, repo):
        lines = [f"{scg.DETECTOR_KEY}: none", f"{scg.REASON_KEY}: {s_reason}"]
        _replace_md(fx, repo, s, scg.insert_declaration(originals[s], lines), "S top-level keys")

    def m_no_reason(fx, repo):
        t = read_md(repo, s)
        out = "".join(ln for ln in t.splitlines(True) if scg.REASON_KEY not in ln)
        if out == t:
            return "precondition: no reason line to remove"
        _replace_md(fx, repo, s, out, "S none without reason")

    def m_reason_null(fx, repo):
        t = read_md(repo, s)
        if s_reason not in t:
            return "precondition: S reason not found"
        _replace_md(fx, repo, s, t.replace(s_reason, "null", 1), "S reason is the YAML null literal")

    def m_reason_toplevel(fx, repo):
        lines = ["metadata:", f"  {scg.DETECTOR_KEY}: none", f"{scg.REASON_KEY}: {s_reason}"]
        _replace_md(fx, repo, s, scg.insert_declaration(originals[s], lines), "S reason outside metadata")

    def reason_edit(text, msg):
        def m(fx, repo):
            t = read_md(repo, s)
            if s_reason not in t:
                return "precondition: S reason not found"
            _replace_md(fx, repo, s, t.replace(s_reason, text, 1), msg)
        return m

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
        ("DUPLICATE-REASON-S", m_duplicate_reason, {f"{s}:DECLARED": F}, True),
        ("DOTSLASH-CWST", m_dotslash, {f"{cw}:FORM": F}, True),
        ("TOPLEVEL-S", m_toplevel, {f"{s}:FORM": F}, True),
        ("DOT-SEGMENT-CWST", path_edit(p.replace("/", "/./", 1), "CWST a/./b path"), {f"{cw}:FORM": F}, True),
        ("TRAILING-SLASH-CWST", path_edit(p + "/", "CWST trailing slash"), {f"{cw}:FORM": F}, True),
        ("NONE-NO-REASON-S", m_no_reason, {f"{s}:TARGET": F}, True),
        ("REASON-NULL-S", m_reason_null, {f"{s}:FORM": F}, True),
        ("REASON-TOPLEVEL-S", m_reason_toplevel, {f"{s}:FORM": F}, True),
        ("REASON-COLON-S", reason_edit("coverage class none: no card hook", "S reason with a colon"), {f"{s}:FORM": F},
         True),
        ("REASON-HASH-S", reason_edit("coverage class none # no card hook", "S reason with a hash"), {f"{s}:FORM": F},
         True),
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


# Plain scalars a YAML 1.1 / core-schema reader resolves to null, bool, int, float or date (refused as a reason), and
# texts it reads as strings (admitted). PyYAML, when importable, cross-checks the literals it resolves itself.
YAML_REFUSED = ("null", "Null", "NULL", "no", "No", "off", "OFF", "false", "True", "yes", "on", "y", "n", "0", "12",
                "-1", "1_000", "0x1F", "0o17", "0b101", "1.5", ".5", "0.", "1e3", "2026-10-04")
YAML_ADMITTED = ("none of these", "nothing", "2 hooks", "yesterday", "node 18", "v1.2", "no card hook names it")


def reason_yaml_scalars(seed):
    gate_bad = [v for v in YAML_REFUSED if scg.reason_form_ok(v)] + [v for v in YAML_ADMITTED if not scg.reason_form_ok(v)]
    generated = [scg.declaration_lines(n, r["class"], r["evidence"])[2].split(": ", 1)[1]
                 for n, r in seed.rows.items() if r["class"] in ("card", "none") and r["tracked"]]
    gate_bad += [v for v in generated if not scg.reason_form_ok(v)]
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        cross = "pyyaml absent, not cross-checked"
        yaml_bad = []
    else:
        def kind(v):
            return type(yaml.safe_load(f"k: {v}")["k"]).__name__
        resolved = [v for v in YAML_REFUSED if kind(v) != "str"]
        yaml_bad = [v for v in YAML_ADMITTED + tuple(generated) if kind(v) != "str"]
        cross = f"pyyaml resolves {len(resolved)}/{len(YAML_REFUSED)} refused literals to non-str"
        if len(resolved) < 15:  # positive control: the refused list really is YAML non-strings
            yaml_bad.append(f"only {len(resolved)} refused literals resolve to non-str")
    report(not gate_bad and not yaml_bad and bool(generated), "V-SCG-REASON-YAML-SCALARS",
           f"refused {len(YAML_REFUSED)}, admitted {len(YAML_ADMITTED)} + {len(generated)} generated reasons; "
           f"gate misjudged {gate_bad}; {cross}; yaml disagrees {yaml_bad}")


# Frontmatter shapes the declaration must not change the router's (name, description) for (review WR-06).
_DESC = "Use when reviewing frontend react components."
FM_SHAPES = {
    "folded": f"---\nname: demo-skill\ndescription: >\n  {_DESC}\n---\n# body\n",
    "literal-chomp": "---\nname: demo-skill\ndescription: |-\n  Use when reviewing\n  frontend react components.\n---\nb\n",
    "folded-then-key": f"---\nname: demo-skill\ndescription: >-\n  {_DESC}\nlicense: MIT\n---\nb\n",
    "plain": f"---\nname: demo-skill\ndescription: {_DESC}\n---\nb\n",
    "description-first": f"---\ndescription: >\n  {_DESC}\nname: demo-skill\n---\nb\n",
    "no-description": "---\nname: demo-skill\n---\nb\n",
    "crlf-folded": f"---\r\nname: demo-skill\r\ndescription: >\r\n  {_DESC}\r\n---\r\nb\r\n",
}


def router_view(text: str, tmp: Path, tag: str):
    """(name, description) as the skill router's own reader returns them for `text`."""
    p = tmp / tag / "demo-skill" / scg.SKILL_MD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))
    return si._read_frontmatter(p)


def router_description(seed):
    """insert_declaration never changes skill_index._read_frontmatter's (name, description): on every shape, both
    declaration kinds, and every repo skill at HEAD (undeclared vs declared, and vs the committed text). Positive
    control: appending the block at the end of a folded description DOES change it, so the comparison can see it."""
    kinds = {"none": scg.declaration_lines("demo-skill", "none", []),
             "path": ["metadata:", f"  {scg.DETECTOR_KEY}: {seed.cwst_path}"]}
    bad, n = [], 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for shape, src in FM_SHAPES.items():
            for kind, lines in kinds.items():
                out = scg.insert_declaration(src, lines)
                d = scg.parse_declaration(out)
                n += 1
                if router_view(src, tmp, f"{shape}-{kind}-a") != router_view(out, tmp, f"{shape}-{kind}-b"):
                    bad.append(f"{shape}/{kind}: router description changed")
                if d["count"] != 1 or not all(x["metadata_child"] for x in d["detector"] + d["reason"]):
                    bad.append(f"{shape}/{kind}: declaration not one metadata child set")
        for skill, row in sorted(seed.rows.items()):
            if not row["tracked"]:
                continue
            head = head_blob(md_rel(skill)).decode("utf-8")
            plain = undeclared(head)
            views = {router_view(t, tmp, f"repo-{skill}-{i}") for i, t in enumerate((plain, seed.declared(skill, plain),
                                                                                       head))}
            n += 1
            if len(views) != 1:
                bad.append(f"{skill}: router description differs across undeclared / inserted / committed")
        src = FM_SHAPES["folded"]
        m = scg._FM_RE.match(src)
        end = m.start(1) + len(m.group(1))
        appended = src[:end] + "".join(f"{ln}\n" for ln in kinds["none"]) + src[end:]
        control = router_view(src, tmp, "ctl-a") != router_view(appended, tmp, "ctl-b")
    report(not bad and control, "V-SCG-ROUTER-DESCRIPTION",
           f"{n} insertions compared, changed {bad[:4]}; control (append after a folded description) "
           f"{'changes' if control else 'DOES NOT change'} the description")


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
            reason_yaml_scalars(seed)
            router_description(seed)
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
