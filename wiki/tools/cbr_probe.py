"""CBR probe: drives the REAL Constitutive Baseline Ratchet (modules/tower) to reproduce the
defects cited in wiki/syntheses/cbr-gap-analysis.md.

Read-only on the repo: real families and B0 generations are only read. Every ratchet / promote /
done-gate case runs on a temp copy (`root=`), and each hole is paired with a positive control
that shows the instrument CAN return the other answer.

    python wiki/tools/cbr_probe.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from modules.tower import baselines as bl          # noqa: E402
from modules.tower import checks as ck             # noqa: E402
from modules.tower import donegate as dg           # noqa: E402
from modules.tower import families as fam          # noqa: E402
from modules.tower import ratchet as rt            # noqa: E402
from modules.tower import select as sel            # noqa: E402

FAMS = [f.id for f in fam.load_families()]


def section(t):
    print("\n## " + t)


def real_data():
    section("P1 real data (read-only)")
    for f in FAMS:
        gens = bl.generations(f)
        act = bl.active_entries(f)
        kinds = Counter(ck.parse(e.get("check") or "")[0] for e in act)
        status = Counter(e.get("status", "?") for e in act)
        s = sel.select_for_injection(act)
        print(f"{f}: generations={gens} active={len(act)} status={dict(status)} "
              f"check_kinds={dict(kinds)} injected={len(s.injected)} deferred={len(s.deferred)}")


PROMPTS = [  # (prompt, families a reader would expect)
    ("build a landing page for QuickLease", {"web_surface"}),
    ("crea una landing con formulario de contacto", {"web_surface"}),
    ("add a new game mode to the minecraft server", {"kobiicraft_mode"}),
    ("nueva modalidad skywars para kobiicraft", {"kobiicraft_mode"}),
    ("landing lobby for the new kobiicraft skywars arena", {"kobiicraft_mode"}),
    ("panel web para el servidor de minecraft", {"web_surface", "kobiicraft_mode"}),
    ("add a pricing tabla to the homepage", {"web_surface"}),
    ("SaaS dashboard with user accounts and Postgres", {"web_surface", "persistent_state"}),
    ("build a SaaS app where users save invoices", {"persistent_state"}),
    ("port the game to the Nintendo Wii", {"wii_homebrew"}),
    ("fix the typo in the README", set()),
]


def classify():
    section("P2 family classification (real families)")
    miss = 0
    for p, want in PROMPTS:
        got = {fid for fid, _ in fam.classify_prompt(p)}
        ok = got == want
        miss += not ok
        print(f"{'OK  ' if ok else 'DIFF'} {p!r}: got={sorted(got)} expected={sorted(want)}")
    print(f"classification disagreements: {miss}/{len(PROMPTS)}")


def tmp_family():
    root = tempfile.mkdtemp(prefix="cbrprobe_")
    shutil.copytree(os.path.join(bl.BASELINES_DIR, "web_surface"), os.path.join(root, "web_surface"))
    return root


def load(root, n):
    return bl.load_generation("web_surface", n, root)


def child_with(root, mutate, changes=None):
    """Write B1 from B0 after `mutate(entries)`; optional change record."""
    ents = json.loads(json.dumps(load(root, 0)["entries"]))
    mutate(ents)
    bl.write_generation("web_surface", ents, "probe", root=root,
                        extra={"changes": changes} if changes else None)


def ratchet_cases():
    section("P3 ratchet")
    first_checked = lambda es: next(e for e in es if ck.parse(e.get("check") or "")[0] != "empty")

    # Control: dropping an entry silently IS caught.
    r = tmp_family()
    child_with(r, lambda es: es.pop(0))
    rep = rt.verify_chain("web_surface", r)
    print(f"control  silent withdrawal: ok={rep.ok} regressions={[x['kind'] for x in rep.regressions]}")

    # H1: any non-empty reason/authority string licenses the same withdrawal.
    r = tmp_family()
    gone = load(r, 0)["entries"][0]["id"]
    child_with(r, lambda es: es.pop(0), {gone: {"kind": "WITHDRAWN", "reason": "x", "authority": "x"}})
    print(f"H1 withdrawal with reason='x' authority='x': ok={rt.verify_chain('web_surface', r).ok}")

    # H2: why / origin / class are outside the diff -- provenance can be rewritten silently.
    r = tmp_family()
    def launder(es):
        es[0]["why"] = "because"
        es[0]["origin"] = {"file": "nowhere.md", "line": 1}
        es[0]["class"] = "D" if es[0].get("class") == "C" else "C"
    child_with(r, launder)
    print(f"H2 why+origin+class rewritten, no record: ok={rt.verify_chain('web_surface', r).ok}")

    # H3: the NEWEST generation is unanchored -- editing it in place is invisible.
    r = tmp_family()
    child_with(r, lambda es: None)
    p = os.path.join(r, "web_surface", "B1.json")
    doc = json.load(open(p, encoding="utf-8"))
    n_before = len(doc["entries"])
    doc["entries"] = doc["entries"][3:]
    json.dump(doc, open(p, "w", encoding="utf-8"), indent=2)
    rep = rt.verify_chain("web_surface", r)
    print(f"H3 (REFUTED if ok=False) newest gen edited in place ({n_before}->{len(doc['entries'])}"
          f" entries): ok={rep.ok} -- still diffed against its parent")

    # H3b: the same three entries removed from BOTH generations, child anchor stripped. Nothing
    # differs between them, and an unanchored child does not lower `ok`.
    def hollow(strip_anchor):
        r = tmp_family()
        child_with(r, lambda es: None)
        for i in (0, 1):
            p = os.path.join(r, "web_surface", f"B{i}.json")
            d = json.load(open(p, encoding="utf-8"))
            d["entries"] = d["entries"][3:]
            if i == 1 and strip_anchor:
                d["parent_sha256"] = None
            json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
        return rt.verify_chain("web_surface", r)
    rep = hollow(True)
    print(f"H3b chain hollowed (3 entries gone from B0 and B1), anchor stripped: ok={rep.ok} "
          f"tampered={rep.tampered} unanchored={rep.unanchored}")
    rep = hollow(False)
    print(f"control  same hollowing, anchor intact: ok={rep.ok} tampered={rep.tampered}")


def promote_cases():
    section("P4 promotion admits anything well-formed")
    r = tmp_family()
    entry = {"id": "probe-trivial", "requirement": "Do the right thing.", "why": "probe",
             "origin": {"file": "C:/does/not/exist.md", "line": 9}, "class": "C",
             "check": "glob:**"}
    path = rt.promote("web_surface", [entry], reason="x", authority="x", root=r)
    print(f"promote with missing origin + check glob:** -> wrote {os.path.basename(path)}; "
          f"verify_origin={bl.verify_origin(entry)}")
    empty_repo = tempfile.mkdtemp(prefix="cbrrepo_")
    open(os.path.join(empty_repo, "x.txt"), "w").close()
    rep = dg.judge("web_surface", empty_repo, root=r)
    v = {e["entry_id"]: e["verdict"] for e in rep["entries"]}
    print(f"done-gate on a one-file repo: probe-trivial={v['probe-trivial']}")


def donegate_cases():
    section("P5 done-gate")
    r = tmp_family()
    repo = tempfile.mkdtemp(prefix="cbrrepo_")
    base = dg.judge("web_surface", repo, root=r)
    counts = Counter(e["verdict"] for e in base["entries"])
    print(f"control  real web_surface B0 vs empty repo: would_block={base['would_block']} {dict(counts)}")
    na = {e["entry_id"]: "n/a" for e in base["entries"]}
    rep = dg.judge("web_surface", repo, root=r, not_applicable=na)
    print(f"H5 every entry declared N/A with reason 'n/a': would_block={rep['would_block']} "
          f"{dict(Counter(e['verdict'] for e in rep['entries']))}")
    # DELEGATED does not block, though nothing ran the test.
    r2 = tempfile.mkdtemp(prefix="cbrprobe_")
    bl.write_generation("probe_fam", [{"id": "t1", "requirement": "tests pass", "why": "w",
                                       "origin": {"file": "f", "line": 1}, "class": "C",
                                       "check": "test:tests/test_x.py"}], "probe", root=r2)
    os.makedirs(os.path.join(repo, "tests"))
    with open(os.path.join(repo, "tests", "test_x.py"), "w") as fh:
        fh.write("def test_x():\n    assert False\n")
    rep = dg.judge("probe_fam", repo, root=r2)
    print(f"H6 test:<file> whose only test fails: verdict={rep['entries'][0]['verdict']} "
          f"would_block={rep['would_block']}")


if __name__ == "__main__":
    real_data()
    classify()
    ratchet_cases()
    promote_cases()
    donegate_cases()
