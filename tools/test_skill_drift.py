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


# --------------------------------------------------------------------------- evidence

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
             "Card-vs-source drift is rendered further down when the card half is recorded.")
    L.append("")
    L.append("## Method")
    L.append("")
    L.append("- Repo side: COMMITTED blobs at a named commit (`git cat-file --batch` through the primitives of "
             "`tools/verify_global_mirrors.py`), never the working tree.")
    L.append("- Unit: the whole skill directory `skills/<name>/`, reduced to a sha256 over the sorted lines "
             "`<relpath>\\0<lf_sha256>\\n`. Files are LF-normalized before hashing (the laptop clone runs "
             "core.autocrlf=true).")
    L.append("- Live side: `<live-root>/<name>/` walked without following symlinked directories; `__pycache__/` and "
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
    L.append("No plane recorded yet.")
    L.append("")
    L.append("## Commands")
    L.append("")
    L.append("command: python3 tools/test_skill_drift.py")
    L.append("command: python3 tools/test_skill_drift.py --write-evidence")
    L.append("command: python3 tools/skill_mirror_drift.py --live")
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


# --------------------------------------------------------------------------- driver

CLAUSES = [c_pole_identical, c_pole_drift, c_pole_absent, c_evidence_current, c_evidence_drill]


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
    return run(CLAUSES)


if __name__ == "__main__":
    sys.exit(main())
