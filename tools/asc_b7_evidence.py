"""Builds vault/programs/ascension/bcap-1/b7/evidence.json for the web_surface B7 (Taste) promotion.

Run AFTER the recorded pair exists (tools/asc_inherit_run.py --deltas .../b7/deltas.json --out .../b7 --task saas).
The taste lint is static, so this runs on any plane once the pair's files are fetched. Every value comes from a
command that runs now; nothing is typed in by hand:

  improvement        the `taste:index.html` check over a fixture page carrying critical anti-slop findings vs the same
                     page with them removed (FAIL -> PASS);
  negative_controls  donegate.judge with the candidate B7 over pages that MUST fail: the fixture, and the treated
                     agent's own surface with an em-dash and with a window scroll listener planted;
  positive_control   the treated agent's surface as recorded;
  control_agent      the control surface's verdict, reported apart (it is NOT a negative control: a quiet control
                     that happens to pass would otherwise be read as a broken instrument);
  reuse              pointer into inheritance_run.json.

Exit 0 only when the positive control passes, every negative control fails and before != after. `discriminated`
says whether the control agent ALSO failed (the inheritance was visible in this pair); false is reported, not hidden.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "vault/programs/ascension/bcap-1/b7"
DELTAS = OUT / "deltas.json"
NEW = ["web_surface-taste-hard-bans"]

# rc 1 = the entry was judged and is not APPLIED_VERIFIED; rc 4 = the judge itself broke (an uncaught exception would
# also exit 1 and be read as a control that "really failed").
JUDGE = """
import sys, traceback
try:
    sys.path.insert(0, %r)
    from modules.tower import donegate
    r = donegate.judge("web_surface", sys.argv[2], root=sys.argv[1])
    rows = [e for e in r["entries"] if e["entry_id"] in %r]
except Exception:
    traceback.print_exc()
    sys.exit(4)
if not rows:
    print("entry not in the candidate")
    sys.exit(4)
print(rows[0].get("verdict"), rows[0].get("detail"))
sys.exit(0 if rows[0]["verdict"] == "APPLIED_VERIFIED" else 1)
"""

CLEAN = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Tidewell</title>
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body><header><h1>Action items from every meeting</h1>
<p>Upload a recording and get the decisions and owners back in a minute.</p>
<a href="#pricing">See pricing</a></header>
<section><h2>Features</h2><p>Speaker labels, owners and due dates.</p></section>
<section id="pricing"><h2>Pricing</h2><p>Team plan and Studio plan.</p></section>
</body></html>
"""
SLOP = (CLEAN.replace("<h1>Action items from every meeting</h1>", "<h1>Action items — from every meeting</h1>")
        .replace("<section><h2>Features</h2>", "<section><h2>Quietly in use at</h2><p>Acme, Jane Doe</p></section>"
                 "<section><h2>Features</h2>"))


def judge_rc(cand_root: str, repo: Path) -> tuple:
    p = subprocess.run([sys.executable, "-c", JUDGE % (str(ROOT), NEW), cand_root, str(repo)],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout.strip() or p.stderr.strip())[-300:]


def site(html: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="asc-b7-fx-")) / "site"
    d.mkdir()
    (d / "index.html").write_text(html, encoding="utf-8")
    return d


def plant(src: Path, label: str, html_edit) -> Path:
    dst = Path(tempfile.mkdtemp(prefix="asc-b7-%s-" % label)) / "site"
    shutil.copytree(src, dst)
    idx = dst / "index.html"
    idx.write_text(html_edit(idx.read_text(encoding="utf-8")), encoding="utf-8")
    return dst


def emdash(html: str) -> str:
    return re.sub(r"(<h1[^>]*>)", "\\1Plain notes — ", html, count=1)


def scroll_listener(html: str) -> str:
    return html.replace("</body>", "<script>window.addEventListener('scroll', () => {});</script></body>", 1)


def taste_verdict(page_dir: Path) -> str:
    from modules.tower import checks as ck
    return ck.evaluate({"id": NEW[0], "check": "taste:index.html"}, str(page_dir)).outcome


def main() -> int:
    import asc_inherit_run as R
    run = json.loads((OUT / "inheritance_run.json").read_text(encoding="utf-8"))
    cand = R.candidate_root(DELTAS)
    slop, clean = site(SLOP), site(CLEAN)
    before, after = taste_verdict(slop), taste_verdict(clean)
    treated, control = OUT / "inherit" / "treated", OUT / "inherit" / "control"
    controls = []
    for name, path in (("fixture with an em-dash, a 'quietly in use at' header and stand-in names judged by candidate B7", slop),
                       ("treated agent surface plus a planted em-dash judged by candidate B7", plant(treated, "dash", emdash)),
                       ("treated agent surface plus a planted window scroll listener judged by candidate B7",
                        plant(treated, "scroll", scroll_listener))):
        rc, detail = judge_rc(cand, path)
        controls.append({"name": name, "rc": rc, "detail": detail})
    prc, pdetail = judge_rc(cand, treated)
    crc, cdetail = judge_rc(cand, control)
    t, c = run["runs"]["treated"], run["runs"]["control"]
    ev = {
        "improvement": {"run": "check taste:index.html over a fixture page with vs without critical anti-slop findings",
                        "measure": "modules.tower.checks verdict", "before": before, "after": after},
        "negative_controls": controls,
        "positive_control": {"name": "treated agent surface judged by candidate B7", "rc": prc, "detail": pdetail},
        "control_agent": {"name": "control agent surface (no baseline) judged by candidate B7", "rc": crc,
                          "detail": cdetail},
        "discriminated": crc != 0 and prc == 0,
        "reuse": {"run": "fresh `claude -p` treated agent, task %r never names a taste ban (b7/inherit/treated)"
                         % run.get("task_key"),
                  "pointer": "inheritance_run.json runs.treated.files=%s vs runs.control.files=%s; candidate %s sha256 %s"
                             % (t["files"], c["files"], run["candidate_generation"], run["candidate_sha256"][:12])},
    }
    (OUT / "evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(ev, indent=1, ensure_ascii=False))
    ok = prc == 0 and all(x["rc"] == 1 for x in controls) and before != after
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
