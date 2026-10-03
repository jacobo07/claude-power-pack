#!/usr/bin/env python
"""test_skill_drift.py -- pillar H gate (skill-capability, SC-H, decision D-02).

    python3 tools/test_skill_drift.py                          # check (default mode)
    python3 tools/test_skill_drift.py --recording PATH         # V-SKD-RECORD-REPRODUCES on one recording only
    python3 tools/test_skill_drift.py --write-evidence         # render evidence/H-drift.md

Default mode builds its own poles in temporary git repos (committed skill + identical, mutated, truncated,
extended or absent live copy) and reads the committed recordings `evidence/H-live-*.json`; it NEVER reads the
host's live skills tree, so the cognitive-economy verifier can re-run it on a host whose live tree differs.
The host's real red pole is `python3 tools/skill_mirror_drift.py --live` (exit 1 on DRIFT).

Output lines: `  ok   V-SKD-X <evidence>` / `  FAIL V-SKD-X <diagnostic>` / `  INCONCLUSIVE V-SKD-X <why>`,
last line `SKD_PASS=<passed>/<total>`. Exit codes: 0 all ok, 1 FAIL or INCONCLUSIVE, 2 could not run.
INCONCLUSIVE is never a pass: a gate that could not read its source must not look green.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent))
import skill_mirror_drift as smd  # noqa: E402

REPO = _THIS.parents[1]
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/H-drift.md"
RECORDING_GLOB = "vault/programs/skill-capability/evidence/H-live-*.json"
OK, FAIL, INCONC = "ok", "FAIL", "INCONCLUSIVE"

SKILL_MD = "---\nname: a\n---\nbody line one\nbody line two\n"
X_PY = "def x():\n    return 1\n"


# --------------------------------------------------------------------------- temp poles

@contextlib.contextmanager
def temp_repo(files=None):
    """A temp git repo holding committed `skills/a/...`; yields (repo Path, commit sha, live-root Path)."""
    files = files or {"SKILL.md": SKILL_MD, "core/x.py": X_PY}
    with tempfile.TemporaryDirectory() as td:
        repo, live = Path(td) / "repo", Path(td) / "live"
        repo.mkdir()
        live.mkdir()
        exe = smd.vgm._git_exe()

        def git(*a):
            subprocess.run([exe, "-C", str(repo), "-c", "user.name=gate", "-c", "user.email=gate@invalid",
                            "-c", "core.autocrlf=false", *a], check=True, capture_output=True, timeout=30)
        git("init", "-q")
        for rel, text in files.items():
            p = repo / "skills" / "a" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(text.encode("utf-8"))
        git("add", "-A")
        git("commit", "-q", "-m", "pole")
        sha, why = smd.resolve_commit(repo)
        if sha is None:
            raise RuntimeError(why)
        yield repo, sha, live


def put_live(live: Path, files: dict, crlf=False):
    for rel, text in files.items():
        p = live / "a" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        p.write_bytes(data.replace(b"\n", b"\r\n") if crlf else data)


def row_of(rep, name="a"):
    return next((r for r in rep.get("rows", []) if r["skill"] == name), None)


def _need_git():
    try:
        smd.vgm._git_exe()
    except FileNotFoundError as e:
        return str(e)
    return None


# --------------------------------------------------------------------------- clauses: poles

def c_pole_identical():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-POLE-IDENTICAL", f"git unavailable: {no}")]
    with temp_repo() as (repo, sha, live):
        put_live(live, {"SKILL.md": SKILL_MD, "core/x.py": X_PY}, crlf=True)
        r = row_of(smd.live_report(repo, live))
    if r and r["status"] == "IDENTICAL" and r["eol_only"] is True:
        return [(OK, "V-SKD-POLE-IDENTICAL", "committed skill vs CRLF live copy: IDENTICAL, eol_only True")]
    return [(FAIL, "V-SKD-POLE-IDENTICAL", f"expected IDENTICAL eol_only, got {r and (r['status'], r['eol_only'])}")]


def c_pole_drift():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-POLE-DRIFT", f"git unavailable: {no}")]
    cases = []
    with temp_repo() as (repo, sha, live):
        base = {"SKILL.md": SKILL_MD, "core/x.py": X_PY}
        mutants = [
            ("changed byte", {**base, "SKILL.md": SKILL_MD.replace("one", "onf")}, ([], [], ["SKILL.md"])),
            ("truncated", {**base, "core/x.py": X_PY[:5]}, ([], [], ["core/x.py"])),
            ("deleted file", {"SKILL.md": SKILL_MD}, (["core/x.py"], [], [])),
            ("extra file", {**base, "core/y.py": "y\n"}, ([], ["core/y.py"], [])),
        ]
        out = []
        for label, files, (miss, extra, chg) in mutants:
            sub = live / label.replace(" ", "_")
            sub.mkdir()
            put_live(sub, files)
            r = row_of(smd.live_report(repo, sub))
            good = (r and r["status"] == "DRIFT" and r["missing_live"] == miss
                    and r["extra_live"] == extra and r["changed"] == chg)
            cases.append(good)
            out.append(f"{label}: {r and (r['status'], r['missing_live'], r['extra_live'], r['changed'])}"
                       f"{'' if good else ' (expected ' + str((miss, extra, chg)) + ')'}")
        # Review WR-03: a symlinked directory inside the live skill is never descended, and must still be an entry
        # (hashed by its link text, like a symlinked file), or extra live content reads IDENTICAL.
        sub = live / "symlinked_dir"
        sub.mkdir()
        put_live(sub, base)
        target = live.parent / "outside"
        target.mkdir()
        (target / "evil.py").write_bytes(b"x = 1\n")
        (sub / "a" / "extra").symlink_to(target, target_is_directory=True)
        r = row_of(smd.live_report(repo, sub))
        good = r and r["status"] == "DRIFT" and r["extra_live"] == ["extra"] and not r["missing_live"]
        cases.append(good)
        out.append(f"extra symlinked dir: {r and (r['status'], r['missing_live'], r['extra_live'], r['changed'])}"
                   f"{'' if good else ' (expected DRIFT extra_live [extra])'}")
    verdict = OK if all(cases) else FAIL
    return [(verdict, "V-SKD-POLE-DRIFT", "; ".join(out))]


def c_pole_absent():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-POLE-ABSENT", f"git unavailable: {no}")]
    with temp_repo() as (repo, sha, live):
        r = row_of(smd.live_report(repo, live))
    if r and r["status"] == "ABSENT_LIVE" and r["live_digest"] is None:
        return [(OK, "V-SKD-POLE-ABSENT", "no live directory: ABSENT_LIVE, live_digest None")]
    return [(FAIL, "V-SKD-POLE-ABSENT", f"expected ABSENT_LIVE, got {r and r['status']}")]


def _cli(argv):
    """(rc, stdout) of smd.main(argv), stdout captured."""
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = smd.main(argv)
    return rc, buf.getvalue()


def c_no_live_root():
    """CR-01: an absent live root, or one holding none of the repo skills, compared nothing. `--live` and `--json`
    must not exit 0 on it; the identical-copy control must."""
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-NO-LIVE-ROOT", f"git unavailable: {no}")]
    with temp_repo() as (repo, sha, live):
        put_live(live, {"SKILL.md": SKILL_MD, "core/x.py": X_PY})
        empty = live.parent / "empty-live"
        empty.mkdir()
        absent = live.parent / "no-such-root"
        got = {}
        for label, root in (("absent", absent), ("empty", empty), ("control", live)):
            for mode in ("--live", "--json"):
                got[(label, mode)] = _cli([mode, "--repo", str(repo), "--live-root", str(root)])
    bad = [f"{k[0]} {k[1]} rc={rc}" for k, (rc, _) in got.items() if (rc == 0) != (k[0] == "control")]
    unlabelled = [f"{k[0]} {k[1]}" for k, (rc, out) in got.items()
                  if k[0] != "control" and k[1] == "--live"
                  and not any(ln.startswith(("UNMEASURED ", "INCONCLUSIVE ")) for ln in out.splitlines())]
    if not bad and not unlabelled:
        return [(OK, "V-SKD-NO-LIVE-ROOT", "absent and empty live roots: --live and --json exit 1 (UNMEASURED / "
                                           "INCONCLUSIVE), identical-copy control exits 0")]
    return [(FAIL, "V-SKD-NO-LIVE-ROOT", f"wrong exit: {bad}; no UNMEASURED/INCONCLUSIVE label: {unlabelled}")]


# --------------------------------------------------------------------------- evidence

def load_recording(raw: bytes):
    """Recording dict from committed bytes, CRLF->LF first (laptop checkout)."""
    return json.loads(smd.lf_bytes(raw).decode("utf-8"))


def recordings(repo=REPO):
    """[(path, dict | None, reason | None)] for every committed H-live-*.json, sorted by name."""
    out = []
    for p in sorted(Path(repo).glob(RECORDING_GLOB)):
        try:
            out.append((p, load_recording(p.read_bytes()), None))
        except (OSError, ValueError) as e:
            out.append((p, None, f"unreadable: {e}"))
    return out


def raw_skill_md_figures(rec):
    """(identical, differ, absent) of SKILL.md raw bytes, from the recording's raw shas."""
    same = diff = absent = 0
    for r in rec["rows"]:
        lr = r.get("live_raw")
        if lr is None or "SKILL.md" not in lr:
            absent += 1
        elif lr["SKILL.md"] == (r.get("repo_raw") or {}).get("SKILL.md"):
            same += 1
        else:
            diff += 1
    return same, diff, absent


def render_plane(rec) -> list:
    L = [f"### Plane {rec['host']}", ""]
    L.append(f"- host `{rec['host']}`, node `{rec.get('node')}`, measured_at {rec.get('measured_at')}, "
             f"live root `{rec.get('live_root')}`")
    L.append(f"- repo_commit `{rec['repo_commit']}` (repo side = committed blobs at that commit)")
    L.append(f"- command: {rec.get('command')}")
    c = rec["counts"]
    L.append(f"- counts: IDENTICAL {c['IDENTICAL']} (of which eol_only {c['eol_only']}), DRIFT {c['DRIFT']}, "
             f"ABSENT_LIVE {c['ABSENT_LIVE']}, INCONCLUSIVE {c['INCONCLUSIVE']}; {len(rec['rows'])} repo skills")
    L.append("")
    L.append("| skill | status | eol_only | missing_live / extra_live / changed |")
    L.append("|---|---|---|---|")
    for r in rec["rows"]:
        detail = ""
        if r["status"] == "DRIFT":
            detail = (f"missing_live {', '.join(r['missing_live']) or '-'}; extra_live "
                      f"{', '.join(r['extra_live']) or '-'}; changed {', '.join(r['changed']) or '-'}")
        L.append(f"| {r['skill']} | {r['status']} | {'yes' if r['eol_only'] else 'no'} | {detail} |")
    L.append("")
    same, diff, absent = raw_skill_md_figures(rec)
    L.append("#### Reconciliation with CONTEXT")
    L.append("")
    L.append(f"04-CONTEXT D-02 records \"4 identical, 10 differ, 10 absent\" for this plane. That is a raw-byte "
             f"comparison of SKILL.md alone; recomputed here from the recording's raw shas it gives {same} identical, "
             f"{diff} differ, {absent} absent. This gate compares the whole directory after LF normalization (the "
             f"method named under Method), which gives IDENTICAL {c['IDENTICAL']} (eol_only {c['eol_only']}), DRIFT "
             f"{c['DRIFT']}, ABSENT_LIVE {c['ABSENT_LIVE']}: the 10 raw-byte \"differ\" are CRLF-versus-LF files whose "
             f"content is equal, and the one real DRIFT is a missing set of files that a SKILL.md-only compare cannot see. "
             f"Both are measurements of the same tree; they answer different questions.")
    L.append("")
    L.append("Drift found on this host is reported and never fixed here (no write under the home directory). "
             "Running `python3 tools/skill_mirror_drift.py --live` on the laptop plane is an Owner-bundle `[H]` item.")
    L.append("")
    return L


def render_cards() -> list:
    L = ["## Card vs source", ""]
    record, why = smd.load_card_record(REPO)
    L.append("Pairs are discovered: each deny card registered in `hooks/hook-dispatcher.js` names its skill, and the "
             "source is `skills/<skill>/SKILL.md`. The record pins the LF sha256 of both, read from committed blobs.")
    L.append("")
    if record is None:
        L.append(f"Record unreadable ({why}).")
        L.append("")
        return L
    L.append(f"- rule: {record.get('rule')}")
    L.append(f"- recorded_at_commit `{record.get('recorded_at_commit')}`")
    L.append("")
    L.append("| skill | card | status at HEAD |")
    L.append("|---|---|---|")
    try:
        rows = card_state_rows(REPO, record)
    except Exception as e:  # noqa: BLE001 -- a render must not traceback
        rows = [{"skill": "?", "card": "?", "status": f"INCONCLUSIVE ({type(e).__name__})"}]
    for r in rows:
        L.append(f"| {r['skill']} | {r['card']} | {r['status']} |")
    L.append("")
    L.append("Lineage fields inside a card (which source line each rule came from) belong to pillar G and are not "
             "recorded here; this record only makes a source change visible to a gate.")
    L.append("")
    return L


def render() -> str:
    """Deterministic, LF, no timestamp / hostname / HEAD of this run."""
    try:
        ledger = json.loads(smd.lf_bytes((REPO / LEDGER_REL).read_bytes()))
        rule = next(p["rule"] for p in ledger["frozen"]["pillars"] if p["id"] == "H")
    except (OSError, ValueError, KeyError, StopIteration, TypeError):
        rule = "(frozen rule unreadable)"
    L = []
    L.append("# [H] freshness / drift -- evidence")
    L.append("")
    L.append("Frozen pillar H rule (ledger, quoted):")
    L.append("")
    L.append(f"> {rule}")
    L.append("")
    L.append("This file covers the live-vs-mirror half (decision D-02): repo-mirrored skills against their live copy. "
             "The card-vs-source half is rendered under 'Card vs source'.")
    L.append("")
    L.append("## Method")
    L.append("")
    L.append("- Repo side: COMMITTED blobs at a named commit (`git cat-file --batch` through the primitives of "
             "`tools/verify_global_mirrors.py`), never the working tree.")
    L.append("- Unit: the whole skill directory `skills/<name>/`, reduced to a sha256 over the sorted lines "
             "`<relpath>\\0<lf_sha256>\\n`. Files are LF-normalized before hashing (the laptop clone runs "
             "core.autocrlf=true).")
    L.append("- Live side: `<live-root>/<name>/` walked without following symlinked directories; a symlinked file or "
             "directory is an entry hashed by its link text (never descended, never omitted); `__pycache__/` and "
             "`*.pyc` are excluded and counted.")
    L.append("- Statuses: IDENTICAL (`eol_only` when only line endings differ), DRIFT (with `missing_live`, "
             "`extra_live`, `changed`), ABSENT_LIVE, INCONCLUSIVE.")
    L.append("- ABSENT_LIVE is reported and is not drift: not every repo skill is meant to be installed on every host.")
    L.append("")
    L.append("## Why a skills pass")
    L.append("")
    L.append("`modules/mirror_discovery/discovery.py` files the whole `skills` domain under OTHER_OWNER, so no parity "
             "check covers repo-mirrored skills. Pairing `skills` there would also pull in the ~160 live skills no repo "
             "directory owns (gsd-*, plugins), change `domain_counts` for every estate, and add to the `verify_spp.py` "
             "mirror-parity row's 15 s budget. The new pass pairs only repo `skills/<name>` that hold a SKILL.md and "
             "reuses the comparator's primitives, so there is still one comparator.")
    L.append("")
    L.append("## Planes")
    L.append("")
    recs = recordings()
    if not recs:
        L.append("No plane recorded.")
        L.append("")
    for _, rec, why in recs:
        if rec is None:
            L.append(f"Recording unreadable ({why}).")
            L.append("")
        else:
            L.extend(render_plane(rec))
    L.extend(render_cards())
    L.append("## Commands")
    L.append("")
    L.append("command: python3 tools/skill_mirror_drift.py --cards")
    L.append("command: python3 tools/skill_mirror_drift.py --record-cards")
    L.append("command: python3 tools/test_skill_drift.py")
    L.append("command: python3 tools/test_skill_drift.py --write-evidence")
    L.append("command: python3 tools/skill_mirror_drift.py --live")
    L.append("command: python3 tools/skill_mirror_drift.py --measure-live --host gex44")
    L.append("")
    return "\n".join(L)


def evidence_current(raw: bytes, rendered: str):
    """(ok, diagnostic). Compared after CRLF->LF: the laptop checkout hands the committed file back CRLF."""
    return smd.lf_bytes(raw) == rendered.encode("utf-8")


def c_evidence_current():
    try:
        raw = (REPO / EVIDENCE_REL).read_bytes()
    except OSError as e:
        return [(FAIL, "V-SKD-EVIDENCE-CURRENT", f"{EVIDENCE_REL} unreadable ({e}); run --write-evidence")]
    if evidence_current(raw, render()):
        return [(OK, "V-SKD-EVIDENCE-CURRENT", f"{EVIDENCE_REL} equals the render (after CRLF->LF)")]
    return [(FAIL, "V-SKD-EVIDENCE-CURRENT", f"{EVIDENCE_REL} differs from the render; run --write-evidence")]


def c_evidence_drill():
    r = render()
    raw = r.encode("utf-8")
    ctrl = evidence_current(raw, r)
    crlf = evidence_current(raw.replace(b"\n", b"\r\n"), r)
    mutated = r.replace("sha256", "sha257", 1) if "sha256" in r else r + "x"
    digit = evidence_current(mutated.encode("utf-8"), r)
    if ctrl and crlf and not digit:
        return [(OK, "V-SKD-EVIDENCE-DRILL", "render ok, CRLF copy ok, one-character change FAIL")]
    return [(FAIL, "V-SKD-EVIDENCE-DRILL", f"control={ctrl} crlf={crlf} mutated_accepted={digit}")]


# --------------------------------------------------------------------------- committed-not-worktree

def c_committed_not_worktree():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-COMMITTED-NOT-WORKTREE", f"git unavailable: {no}")]
    with temp_repo() as (repo, sha, live):
        edited = SKILL_MD + "uncommitted edit\n"
        (repo / "skills" / "a" / "SKILL.md").write_bytes(edited.encode("utf-8"))
        put_live(live, {"SKILL.md": edited, "core/x.py": X_PY})
        r = row_of(smd.live_report(repo, live))
        ctrl_live = live.parent / "live-ctl"
        ctrl_live.mkdir()
        put_live(ctrl_live, {"SKILL.md": SKILL_MD, "core/x.py": X_PY})
        c = row_of(smd.live_report(repo, ctrl_live))
    good = r and r["status"] == "DRIFT" and r["changed"] == ["SKILL.md"] and c and c["status"] == "IDENTICAL"
    if good:
        return [(OK, "V-SKD-COMMITTED-NOT-WORKTREE",
                 "live == uncommitted working tree -> DRIFT changed [SKILL.md]; live == committed blob -> IDENTICAL")]
    return [(FAIL, "V-SKD-COMMITTED-NOT-WORKTREE",
             f"worktree-equal live: {r and (r['status'], r['changed'])}; committed-equal live: {c and c['status']}")]


# --------------------------------------------------------------------------- recording reproduction

PARTS = ("schema", "rows", "commit", "population", "repo_files", "repo_digest", "live_digest", "status", "counts")


def reproduce(rec, repo=REPO):
    """[(part, verdict, diagnostic)] in PARTS order. Repo side re-derived from blobs at rec['repo_commit'];
    nothing in the recording is trusted. Later parts are skipped when rows are unusable or the commit unreadable."""
    f = []
    if not isinstance(rec, dict):
        return [("schema", FAIL, "recording is not an object")]
    f.append(("schema", OK, SCHEMA_OK) if rec.get("schema") == smd.SCHEMA else
             ("schema", FAIL, f"schema {rec.get('schema')!r} != {smd.SCHEMA!r}"))
    rows = rec.get("rows")
    if not isinstance(rows, list) or not rows:
        f.append(("rows", INCONC, "no rows: unmeasured"))
        return f
    f.append(("rows", OK, f"{len(rows)} rows"))
    want = str(rec.get("repo_commit"))
    sha, why = smd.resolve_commit(repo, want)
    if sha is None or sha != want:
        f.append(("commit", INCONC, f"repo_commit {want} unreadable: {why or 'resolves to ' + str(sha)}"))
        return f
    f.append(("commit", OK, sha[:8]))
    skills, why = smd.repo_skills(repo, sha)
    if skills is None:
        f.append(("population", INCONC, f"cannot discover skills at {sha[:8]}: {why}"))
        return f
    try:
        names = [r["skill"] for r in rows]
    except (KeyError, TypeError):
        f.append(("population", FAIL, "malformed row (no skill key)"))
        return f
    miss, extra = sorted(set(skills) - set(names)), sorted(set(names) - set(skills))
    dup = len(names) != len(set(names))
    if miss or extra or dup:
        f.append(("population", FAIL, f"repo skills at {sha[:8]} not in recording: {miss}; in recording but not "
                                       f"in repo: {extra}{'; duplicate rows' if dup else ''}"))
    else:
        f.append(("population", OK, f"{len(names)} skills discovered at {sha[:8]} equal the rows"))
    rs = smd.repo_side(repo, sha, skills)

    def per_row(part, check, okmsg):
        bad = []
        for r in rows:
            try:
                msg = check(r)
            except (KeyError, TypeError, AttributeError) as e:
                msg = f"malformed ({type(e).__name__}: {e})"
            if msg:
                bad.append(f"{r.get('skill') if isinstance(r, dict) else '?'}: {msg}")
        f.append((part, FAIL, "; ".join(bad[:6])) if bad else (part, OK, okmsg))

    def chk_files(r):
        e = rs.get(r["skill"])
        if e is None:
            return None  # reported by population
        if "error" in e:
            return f"repo side unreadable: {e['error']}"
        if r["repo_files"] != e["files"]:
            d = sorted(k for k in set(r["repo_files"]) | set(e["files"]) if r["repo_files"].get(k) != e["files"].get(k))
            return f"repo_files differ from blobs at {sha[:8]}: {d[:4]}"
        if r["repo_raw"] != e["raw"]:
            return "repo_raw differs from blobs"
        return None
    per_row("repo_files", chk_files, "per-file shas equal the blobs at the recorded commit")

    def chk_rd(r):
        e = rs.get(r["skill"])
        if e is None or "error" in e:
            return None
        if r["repo_digest"] != e["digest"]:
            return "repo_digest != digest recomputed from blobs"
        if r["repo_digest"] != smd.dir_digest(r["repo_files"]):
            return "repo_digest != dir_digest(repo_files)"
        return None
    per_row("repo_digest", chk_rd, "repo digests equal blobs and dir_digest(repo_files)")

    def chk_ld(r):
        if r["live_digest"] is None:
            return "live_files present on an absent row" if "live_files" in r else None
        if r["live_digest"] != smd.dir_digest(r["live_files"]):
            return "live_digest != dir_digest(live_files)"
        return None
    per_row("live_digest", chk_ld, "live digests equal dir_digest(live_files)")

    def chk_status(r):
        rep = {"files": r["repo_files"], "raw": r["repo_raw"], "digest": r["repo_digest"]}
        liv = None if r["live_digest"] is None else {"files": r["live_files"], "raw": r.get("live_raw", {}),
                                                     "digest": r["live_digest"]}
        c = smd.compare(rep, liv)
        got = (r["status"], r["eol_only"], r["missing_live"], r["extra_live"], r["changed"])
        exp = (c["status"], c["eol_only"], c["missing_live"], c["extra_live"], c["changed"])
        return None if got == exp else f"recorded {got[0]} but the comparator gives {exp[0]} (eol/lists {got[1:] == exp[1:]})"
    per_row("status", chk_status, "statuses equal the comparator over the recorded entries")

    recount = smd.count_rows(rows)
    f.append(("counts", OK, f"counts equal the recount {recount}") if rec.get("counts") == recount else
             ("counts", FAIL, f"recorded counts {rec.get('counts')} != recount {recount}"))
    return f


SCHEMA_OK = smd.SCHEMA


def first_bad(findings):
    return next(((p, v, d) for p, v, d in findings if v != OK), None)


def worst(findings):
    vs = [v for _, v, _ in findings]
    return FAIL if FAIL in vs else INCONC if INCONC in vs else OK


def _reproduce_clause(items):
    out = []
    for name, rec, why in items:
        if rec is None:
            out.append((INCONC, "V-SKD-RECORD-REPRODUCES", f"{name}: recording {why}"))
            continue
        fs = reproduce(rec)
        v = worst(fs)
        if v == OK:
            out.append((OK, "V-SKD-RECORD-REPRODUCES",
                        f"{rec.get('host')} {len(rec['rows'])} rows at {rec['repo_commit'][:8]}: "
                        + ", ".join(f"{p} ok" for p, _, _ in fs)))
        else:
            out.append((v, "V-SKD-RECORD-REPRODUCES", f"{name}: " + "; ".join(f"{p} {vv}: {d}" for p, vv, d in fs if vv != OK)))
    return out


def c_record_reproduces():
    items = [(p.name, rec, why) for p, rec, why in recordings()]
    if not items:
        return [(INCONC, "V-SKD-RECORD-REPRODUCES", f"no recording matches {RECORDING_GLOB}: unmeasured")]
    return _reproduce_clause(items)


def mutants(rec):
    """[(name, mutated copy, expected part, expected verdict, token the diagnostic must contain)]"""
    out = []
    drift = next(r["skill"] for r in rec["rows"] if r["status"] == "DRIFT")
    ident = next(r["skill"] for r in rec["rows"] if r["status"] == "IDENTICAL")

    def mut(fn):
        c = copy.deepcopy(rec)
        fn(c)
        return c

    def row(c, name):
        return next(r for r in c["rows"] if r["skill"] == name)

    def flip(h):
        return h[:-1] + ("0" if h[-1] != "0" else "1")

    def alter_repo_files(c):
        r = row(c, ident)
        k = sorted(r["repo_files"])[0]
        r["repo_files"][k] = flip(r["repo_files"][k])

    def alter_live_digest(c):
        r = row(c, ident)
        r["live_digest"] = flip(r["live_digest"])
    out.append(("schema string changed", mut(lambda c: c.__setitem__("schema", "skill-mirror-live/0")),
                "schema", FAIL, "schema"))
    out.append(("rows emptied", mut(lambda c: c.__setitem__("rows", [])), "rows", INCONC, "no rows"))
    out.append(("one skill row dropped", mut(lambda c: c["rows"].remove(row(c, ident))), "population", FAIL, ident))
    out.append(("one repo_files sha altered", mut(alter_repo_files), "repo_files", FAIL, ident))
    out.append(("one repo_digest altered", mut(lambda c: row(c, ident).__setitem__("repo_digest", flip(row(c, ident)["repo_digest"]))),
                "repo_digest", FAIL, ident))
    out.append(("one live_digest altered", mut(alter_live_digest), "live_digest", FAIL, ident))
    out.append(("DRIFT row re-typed IDENTICAL", mut(lambda c: row(c, drift).__setitem__("status", "IDENTICAL")),
                "status", FAIL, drift))
    out.append(("counts.DRIFT incremented", mut(lambda c: c["counts"].__setitem__("DRIFT", c["counts"]["DRIFT"] + 1)),
                "counts", FAIL, "DRIFT"))
    out.append(("repo_commit zeroed", mut(lambda c: c.__setitem__("repo_commit", "0" * 40)), "commit", INCONC, "0" * 40))
    return out


def c_record_drill():
    recs = [(p, r) for p, r, _ in recordings() if r is not None]
    if not recs:
        return [(INCONC, "V-SKD-RECORD-DRILL", "no recording to mutate: unmeasured")]
    path, rec = recs[0]
    if not any(r["status"] == "DRIFT" for r in rec["rows"]) or not any(r["status"] == "IDENTICAL" for r in rec["rows"]):
        return [(INCONC, "V-SKD-RECORD-DRILL", f"{path.name} lacks a DRIFT or an IDENTICAL row to mutate: unmeasured")]
    lines, ok = [], True
    base = reproduce(rec)
    ctl = worst(base) == OK
    # No CRLF re-encoding control here: JSON ignores CR, so it could not go red (review WR-02). The CR pole of the
    # hashed content is V-SKD-POLE-IDENTICAL (eol_only) and V-SKD-CARD-SOURCE-CRLF (CRLF blobs).
    ok = ok and ctl
    lines.append(f"control unmutated {'ok' if ctl else 'NOT ok'}")
    for name, m, part, verdict, token in mutants(rec):
        fs = reproduce(m)
        fb = first_bad(fs)
        good = bool(fb) and fb[0] == part and fb[1] == verdict and token in fb[2]
        ok = ok and good
        lines.append(f"{name}: expected {part} {verdict}, observed {fb[0] + ' ' + fb[1] if fb else 'all ok'}"
                     f"{'' if good else ' <-- WRONG (' + (fb[2] if fb else '') + ')'}")
    return [(OK if ok else FAIL, "V-SKD-RECORD-DRILL", f"{len(mutants(rec))} mutants | " + " | ".join(lines))]


def c_git_failure():
    orig = smd.vgm._git_exe

    def gone():
        raise FileNotFoundError("git executable not found (drill)")
    recs = [r for _, r, _ in recordings() if r is not None]
    smd.vgm._git_exe = gone
    try:
        fs = reproduce(recs[0]) if recs else [("commit", INCONC, "no recording")]
        rep = smd.live_report(REPO, REPO / "no-live-root")
        err = None
    except Exception as e:  # noqa: BLE001 -- the clause asserts that nothing escapes
        fs, rep, err = [], {}, f"{type(e).__name__}: {e}"
    finally:
        smd.vgm._git_exe = orig
    cm = next((x for x in fs if x[0] == "commit"), None)
    good = (err is None and cm is not None and cm[1] == INCONC and "git not found" in cm[2]
            and rep.get("status") == "INCONCLUSIVE" and "git not found" in str(rep.get("reason")))
    if good:
        return [(OK, "V-SKD-GIT-FAILURE", "git missing: reproduce commit INCONCLUSIVE and live_report INCONCLUSIVE "
                                          "('git not found'), no exception escaped")]
    return [(FAIL, "V-SKD-GIT-FAILURE", f"escaped={err}; commit={cm}; live_report={rep.get('status')}/{rep.get('reason')}")]


# --------------------------------------------------------------------------- card vs source

DISPATCHER_TMPL = ("const CHAIN_MAP = {\n  'PreToolUse-chain': [\n%s  ],\n};\n")
ENTRY_TMPL = "    { script: '../skills/claude-power-pack/hooks/%s.js' },\n"
CARD_TMPL = ("const r = { permissionDecision: 'deny', reason: 'read the `%s` skill first' };\n"
             "process.stdout.write(JSON.stringify(r));\n")


def card_state_rows(repo, record=None):
    """card_drift rows of the repo at HEAD against `record` (default: the record file in that repo)."""
    if record is None:
        record, why = smd.load_card_record(repo)
        if record is None:
            return [{"card": None, "skill": None, "status": "INCONCLUSIVE", "reason": why}]
    return smd.card_drift(record, smd.card_source_state(repo, "HEAD", smd.card_pairs(repo)))


def statuses(rows):
    return sorted(f"{r['skill']}:{r['status']}" for r in rows)


@contextlib.contextmanager
def card_repo():
    """A temp git repo with a dispatcher registering one deny-card (hooks/card_a.js -> skill a). Yields
    (repo, git, write) where write(rel, text) writes under the repo and git(*args) commits-or-runs."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        exe = smd.vgm._git_exe()

        def git(*a):
            subprocess.run([exe, "-C", str(repo), "-c", "user.name=gate", "-c", "user.email=gate@invalid",
                            "-c", "core.autocrlf=false", *a], check=True, capture_output=True, timeout=30)

        def write(rel, text):
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(text.encode("utf-8"))
        git("init", "-q")
        write("hooks/hook-dispatcher.js", DISPATCHER_TMPL % (ENTRY_TMPL % "card_a"))
        write("hooks/card_a.js", CARD_TMPL % "a")
        write("skills/a/SKILL.md", SKILL_MD)
        git("add", "-A")
        git("commit", "-q", "-m", "pole")
        yield repo, git, write


def c_card_source_current():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-CARD-SOURCE-CURRENT", f"git unavailable: {no}")]
    record, why = smd.load_card_record(REPO)
    if record is None:
        return [(INCONC, "V-SKD-CARD-SOURCE-CURRENT", why)]
    rows = card_state_rows(REPO, record)
    found = smd.card_pairs(REPO)
    desc = "; ".join(f"{r['skill']} <- {r['card']}: {r['status']}" for r in rows)
    if not record.get("pairs") or not found:
        return [(INCONC, "V-SKD-CARD-SOURCE-CURRENT", f"record holds {len(record.get('pairs') or [])} pairs, "
                                                      f"{len(found)} discovered: unmeasured")]
    if smd.card_verdict(rows) == "CURRENT" and len(rows) == len(found) == len(record["pairs"]):
        return [(OK, "V-SKD-CARD-SOURCE-CURRENT",
                 f"{len(rows)} discovered pairs equal the record at HEAD: {desc}")]
    return [(FAIL, "V-SKD-CARD-SOURCE-CURRENT",
             f"{desc}; re-derive each moved card from its source, then --record-cards")]


def c_card_source_poles():
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-CARD-SOURCE-POLES", f"git unavailable: {no}")]
    out, ok = [], True

    def expect(label, rows, want):
        nonlocal ok
        got = statuses(rows)
        good = got == sorted(want)
        ok = ok and good
        out.append(f"{label}: {got}{'' if good else ' <-- expected ' + str(sorted(want))}")
    with card_repo() as (repo, git, write):
        rec, why = smd.record_cards(repo)
        if rec is None:
            return [(INCONC, "V-SKD-CARD-SOURCE-POLES", f"temp record failed: {why}")]
        expect("unchanged", card_state_rows(repo), ["a:CURRENT"])
        write("skills/a/SKILL.md", SKILL_MD + "new rule\n")
        git("commit", "-q", "-am", "source edit")
        expect("committed source edit", card_state_rows(repo), ["a:SOURCE_CHANGED"])
        smd.record_cards(repo)
        expect("re-recorded", card_state_rows(repo), ["a:CURRENT"])
        write("hooks/card_a.js", CARD_TMPL % "a" + "// edit\n")
        git("commit", "-q", "-am", "card edit")
        expect("committed card edit", card_state_rows(repo), ["a:CARD_CHANGED"])
        smd.record_cards(repo)
        write("hooks/hook-dispatcher.js", DISPATCHER_TMPL % (ENTRY_TMPL % "card_a" + ENTRY_TMPL % "card_b"))
        write("hooks/card_b.js", CARD_TMPL % "b")
        write("skills/b/SKILL.md", SKILL_MD)
        git("add", "-A")
        git("commit", "-q", "-m", "second card")
        expect("second registered card", card_state_rows(repo), ["a:CURRENT", "b:RECORD_STALE"])
        smd.record_cards(repo)
        write("hooks/hook-dispatcher.js", DISPATCHER_TMPL % (ENTRY_TMPL % "card_b"))
        git("commit", "-q", "-am", "unregister a")
        expect("recorded pair no longer discovered", card_state_rows(repo), ["a:RECORD_STALE", "b:CURRENT"])
    return [(OK if ok else FAIL, "V-SKD-CARD-SOURCE-POLES", " | ".join(out))]


def _flip(h):
    return h[:-1] + ("0" if h[-1] != "0" else "1")


def c_card_source_crlf():
    """The CR pole sits where CR changes the result: in the hashed blobs, not in the JSON record (JSON treats CR as
    insignificant whitespace, so a CRLF re-encoded record parses the same with or without normalization; review
    WR-02). A card and source recorded LF, then committed again as CRLF bytes (autocrlf=false, so the blobs really
    carry CR), must stay CURRENT through the LF-normalized digest; the raw sha256 of the CRLF source blob must differ
    from the recorded digest (so without normalization the pair would read SOURCE_CHANGED); and a real source edit
    committed CRLF must still read SOURCE_CHANGED."""
    no = _need_git()
    if no:
        return [(INCONC, "V-SKD-CARD-SOURCE-CRLF", f"git unavailable: {no}")]
    with card_repo() as (repo, git, write):
        rec, why = smd.record_cards(repo)
        if rec is None:
            return [(INCONC, "V-SKD-CARD-SOURCE-CRLF", f"temp record failed: {why}")]
        write("hooks/card_a.js", (CARD_TMPL % "a").replace("\n", "\r\n"))
        write("skills/a/SKILL.md", SKILL_MD.replace("\n", "\r\n"))
        git("commit", "-q", "-am", "crlf re-encoding")
        crlf_rows = card_state_rows(repo)
        raw = smd.vgm.batch_blobs(str(repo), "HEAD", ["skills/a/SKILL.md"])["skills/a/SKILL.md"][0]
        carries_cr = raw is not None and b"\r\n" in raw
        raw_differs = carries_cr and hashlib.sha256(raw).hexdigest() != rec["pairs"][0]["source_sha256"]
        write("skills/a/SKILL.md", (SKILL_MD + "new rule\n").replace("\n", "\r\n"))
        git("commit", "-q", "-am", "crlf source edit")
        edit_rows = card_state_rows(repo)
    got = (statuses(crlf_rows), carries_cr, raw_differs, statuses(edit_rows))
    if got == (["a:CURRENT"], True, True, ["a:SOURCE_CHANGED"]):
        return [(OK, "V-SKD-CARD-SOURCE-CRLF", "card + source recorded LF, re-committed as CRLF blobs: CURRENT; raw "
                                               "sha256 of the CRLF blob differs from the record (normalization is "
                                               "load-bearing); CRLF source edit -> SOURCE_CHANGED")]
    return [(FAIL, "V-SKD-CARD-SOURCE-CRLF", f"(crlf rows, blob carries CR, raw sha differs, edit rows) = {got}")]


def c_card_source_git_failure():
    orig = smd.vgm._git_exe

    def gone():
        raise FileNotFoundError("git executable not found (drill)")
    record, why = smd.load_card_record(REPO)
    smd.vgm._git_exe = gone
    try:
        rows = card_state_rows(REPO, record) if record else []
        err = None
    except Exception as e:  # noqa: BLE001 -- the clause asserts that nothing escapes
        rows, err = [], f"{type(e).__name__}: {e}"
    finally:
        smd.vgm._git_exe = orig
    good = (err is None and len(rows) == 1 and rows[0]["status"] == "INCONCLUSIVE"
            and "git not found" in str(rows[0].get("reason")) and smd.card_verdict(rows) == "INCONCLUSIVE")
    # Review WR-05: rev-parse succeeds, then `cat-file --batch` fails. Every failure reason batch_blobs emits
    # (rc, error, truncated, badheader, ambiguous) is a git failure -> INCONCLUSIVE, never UNTRACKED/DRIFT; only
    # `git-batch-missing` (the path is not in the commit) is UNTRACKED.
    orig_bb = smd.vgm.batch_blobs
    batch = []
    for reason, part in (("git-batch-rc128", False), ("git-batch-error:boom", False), ("git-batch-truncated", True),
                         ("git-batch-badheader", True), ("git-batch-ambiguous", True)):
        def fake(repo, ref, rels, _r=reason, _p=part):
            real = orig_bb(repo, ref, rels)
            return {k: ((None, _r) if (not _p or i == 0) else v) for i, (k, v) in enumerate(sorted(real.items()))}
        smd.vgm.batch_blobs = fake
        try:
            v = smd.card_verdict(card_state_rows(REPO, record)) if record else "no record"
        except Exception as e:  # noqa: BLE001
            v = f"raised {type(e).__name__}"
        finally:
            smd.vgm.batch_blobs = orig_bb
        batch.append((reason, "partial" if part else "all", v))
    missing = []

    def fake_missing(repo, ref, rels):
        real = orig_bb(repo, ref, rels)
        return {k: ((None, "git-batch-missing") if i == 0 else val) for i, (k, val) in enumerate(sorted(real.items()))}
    smd.vgm.batch_blobs = fake_missing
    try:
        missing = [r["status"] for r in card_state_rows(REPO, record)] if record else []
    finally:
        smd.vgm.batch_blobs = orig_bb
    bad_batch = [b for b in batch if b[2] != "INCONCLUSIVE"]
    if good and not bad_batch and "UNTRACKED" in missing:
        return [(OK, "V-SKD-CARD-SOURCE-GIT-FAILURE", "git missing: card check INCONCLUSIVE ('git not found'), "
                                                      "no exception escaped; cat-file rc128 / error / truncated / "
                                                      "badheader / ambiguous -> INCONCLUSIVE; missing blob -> "
                                                      "UNTRACKED (control)")]
    return [(FAIL, "V-SKD-CARD-SOURCE-GIT-FAILURE", f"escaped={err}; rows={rows}; record={'ok' if record else why}; "
                                                    f"batch failures not INCONCLUSIVE: {bad_batch}; missing control "
                                                    f"{missing}")]


# --------------------------------------------------------------------------- driver

CLAUSES = [c_pole_identical, c_pole_drift, c_pole_absent, c_no_live_root, c_committed_not_worktree, c_record_reproduces,
           c_record_drill, c_git_failure, c_card_source_current, c_card_source_poles, c_card_source_crlf,
           c_card_source_git_failure, c_evidence_current, c_evidence_drill]


def run(clauses) -> int:
    results = []
    for fn in clauses:
        try:
            results.extend(fn())
        except Exception as e:  # a clause that cannot run is INCONCLUSIVE, never a traceback
            results.append((INCONC, fn.__name__.replace("c_", "V-SKD-").upper().replace("_", "-"),
                            f"clause raised {type(e).__name__}: {e}"))
    for v, cid, text in results:
        print(f"  {v:<4} {cid} {text}" if v == OK else f"  {v} {cid} {text}")
    passed = sum(1 for v, _, _ in results if v == OK)
    print(f"SKD_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write-evidence", action="store_true")
    ap.add_argument("--recording", metavar="PATH")
    a = ap.parse_args(argv)
    if a.write_evidence:
        dest = REPO / EVIDENCE_REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(render().encode("utf-8"))
        print(f"wrote {EVIDENCE_REL}")
        return 0
    if a.recording:
        try:
            rec = load_recording(Path(a.recording).read_bytes())
            items = [(Path(a.recording).name, rec, None)]
        except (OSError, ValueError) as e:
            items = [(Path(a.recording).name, None, f"unreadable: {e}")]
        res = _reproduce_clause(items)
        for v, cid, text in res:
            print(f"  {v:<4} {cid} {text}" if v == OK else f"  {v} {cid} {text}")
        n = sum(1 for v, _, _ in res if v == OK)
        print(f"SKD_PASS={n}/{len(res)}")
        return 0 if n == len(res) else 1
    return run(CLAUSES)


if __name__ == "__main__":
    sys.exit(main())
