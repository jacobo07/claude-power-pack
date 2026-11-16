"""Builds vault/programs/ascension/bcap-1/phase5/evidence.json for the web_surface promotion.

Every number here comes from a command that runs now: the legal_surface verdict on a fixture without and with the
terms page (improvement), the exit code of a judging subprocess over the incomplete variants (negative controls), and
a pointer into the recorded fresh-agent run (reuse). Nothing is typed in by hand.
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
OUT = ROOT / "vault/programs/ascension/bcap-1/phase5"
NEW = ["web_surface-privacy-page-linked", "web_surface-terms-page-linked"]

JUDGE = """
import sys
sys.path.insert(0, %r)
from modules.tower import donegate
r = donegate.judge("web_surface", sys.argv[2], root=sys.argv[1])
bad = [e["entry_id"] for e in r["entries"] if e["entry_id"] in %r and e["verdict"] != "APPLIED_VERIFIED"]
print(bad)
sys.exit(1 if bad else 0)
"""


def judge_rc(cand_root: str, repo: Path) -> int:
    p = subprocess.run([sys.executable, "-c", JUDGE % (str(ROOT), NEW), cand_root, str(repo)],
                       capture_output=True, text=True)
    return p.returncode


def strip_terms(src: Path) -> Path:
    dst = Path(tempfile.mkdtemp(prefix="asc-incomplete-")) / "site"
    shutil.copytree(src, dst)
    idx = dst / "index.html"
    idx.write_text(re.sub(r'<a href="[^"]*terms[^"]*">[^<]*</a>', "", idx.read_text(encoding="utf-8")), encoding="utf-8")
    for f in dst.glob("terms*.html"):
        f.unlink()
    return dst


def main() -> int:
    import asc_inherit_run as R
    from modules.backlog_autopilot import webslice as W
    from modules.cdio import legal_surface as L
    cand = R.candidate_root()
    fx = Path(tempfile.mkdtemp(prefix="asc-fx-")) / "s"
    W.build_site(fx)
    before_dir = strip_terms(fx)
    before = L.check(str(before_dir), "us")["score"]["verdict"]
    after = L.check(str(fx), "us")["score"]["verdict"]
    treated = OUT / "inherit" / "treated"
    control = OUT / "inherit" / "control"
    controls = [
        {"name": "fixture without terms page judged by candidate B5", "rc": judge_rc(cand, before_dir)},
        {"name": "control agent surface (no baseline) judged by candidate B5", "rc": judge_rc(cand, control)},
        {"name": "treated agent surface minus terms page judged by candidate B5", "rc": judge_rc(cand, strip_terms(treated))},
    ]
    positive = judge_rc(cand, treated)
    run = json.loads((OUT / "inheritance_run.json").read_text(encoding="utf-8"))
    t, c = run["runs"]["treated"], run["runs"]["control"]
    ev = {
        "improvement": {"run": "legal_surface.check over the Phase 3 fixture (webslice.build_site) without vs with terms-of-use",
                        "measure": "CDIO legal_surface verdict", "before": before, "after": after},
        "negative_controls": controls,
        "positive_control": {"name": "treated agent surface judged by candidate B5", "rc": positive},
        "reuse": {"run": "fresh `claude -p` treated agent, task never mentions legal pages (inherit/treated)",
                  "pointer": "inheritance_run.json runs.treated.files=%s vs runs.control.files=%s; candidate %s sha256 %s"
                             % (t["files"], c["files"], run["candidate_generation"], run["candidate_sha256"][:12])},
    }
    (OUT / "evidence.json").write_text(json.dumps(ev, indent=1), encoding="utf-8")
    print(json.dumps(ev, indent=1))
    ok = positive == 0 and all(x["rc"] != 0 for x in controls) and before != after
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
