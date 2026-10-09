#!/usr/bin/env python3
"""U-DOCTRINE gate: the enforcer the 41 doctrine rows point to.

Each cluster has (a) a rule section in vault/specs/gsdx-factory/doctrine/ENFORCEMENT.md that names its member row ids
and the rule text, and (b) a LIVE check over this tree's artifacts that exits non-zero when the doctrine is violated.
  gsdx_doctrine_gate.py --cluster <name> [--doc path]    -> exit 0 only if the section is intact AND the live check holds
  gsdx_doctrine_gate.py --selftest                       -> mutates a COPY of the doc / packets; every mutation must fail
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "vault" / "specs" / "gsdx-factory" / "doctrine" / "ENFORCEMENT.md"
PACKETS = ROOT / "vault" / "specs" / "packets"
PLAN = ROOT / "vault" / "plans" / "gsdx-factory-master-plan.md"
GIT = r"C:\Program Files\Git\cmd\git.exe"
MAX_FILES_PER_COMMIT = 80
RECENT_COMMITS = 40

CLUSTERS = {
    "commit": ["micro-commit-law", "micro-commits-3"],
    "authority": ["owner-approval-contract", "owner-authority-contract", "scope-boundary", "hard-stop-law-2",
                  "first-response-contract-3", "mission-execution-mode", "one-mission-law", "mission-continuity-law"],
    "delegation": ["agent-teams", "agent-teams-mode-4", "delegation-principle-4", "opportunity-delegation-must-become-software",
                   "opportunity-delegation-principle-4", "self-prompting-continuation-loop", "known-work-novel-work-law"],
    "economics": ["ultimate-economic-law", "constitutional-economic-law", "asymptotic-law", "cognitive-economic-kernel",
                  "vmax-null-error", "kernel-vmax-null-error-3", "conservation-law-of-cognitive-work",
                  "call-accounting-invariant", "economic-contracts-for-mature-capabilities",
                  "cognitive-economics-completion-contract", "cognitive-jit", "constitutive-baseline-pruner",
                  "baseline-retirement", "baseline-completion-law"],
    "knowledge": ["context-first-reality-first-law", "the-three-mutually-reinforcing-outputs", "source-ownership-levels",
                  "bug-failure-knowledge-contract", "reconstruction-factory-law", "reconstruction-law",
                  "dataset-completeness-contract", "a-g1-residual-law", "video-image-contract-2",
                  "active-reality-contract-3"],
}


def all_ids():
    return ["S-" + i for ids in CLUSTERS.values() for i in ids]


def section(doc_text: str, cluster: str):
    m = re.search(rf"^## CLUSTER {cluster}\n(.*?)(?=^## CLUSTER |\Z)", doc_text, re.M | re.S)
    return m.group(1) if m else None


def check_doc(cluster: str, doc: Path):
    errs = []
    sec = section(doc.read_text(encoding="utf-8", errors="replace"), cluster) if doc.exists() else None
    if sec is None:
        return [f"no '## CLUSTER {cluster}' section in {doc}"]
    if not re.search(r"^RULE: \S.{20,}", sec, re.M):
        errs.append("section has no RULE: line")
    if "ENFORCER: tools/gsdx_doctrine_gate.py" not in sec:
        errs.append("section does not name its enforcer")
    for i in CLUSTERS[cluster]:
        if f"- S-{i}" not in sec.splitlines():
            errs.append(f"member row S-{i} not listed")
    return errs


def packets(root: Path):
    return sorted(root.glob("WU-*.md"))


def live(cluster: str, packets_dir: Path):
    errs = []
    if cluster == "commit":
        p = subprocess.run([GIT, "-C", str(ROOT), "log", f"-{RECENT_COMMITS}", "--format=@%h", "--shortstat"],
                           capture_output=True, text=True, errors="replace", timeout=120)
        cur = None
        for ln in p.stdout.splitlines():
            if ln.startswith("@"):
                cur = ln[1:]
            m = re.search(r"(\d+) files? changed", ln)
            if m and int(m.group(1)) > MAX_FILES_PER_COMMIT:
                errs.append(f"commit {cur} touches {m.group(1)} files (> {MAX_FILES_PER_COMMIT}): not a micro-commit")
        if p.returncode != 0:
            errs.append(f"git log rc={p.returncode}")
    elif cluster == "authority":
        plan = PLAN.read_text(encoding="utf-8", errors="replace") if PLAN.exists() else ""
        if "hard ceiling of 55M" not in plan:
            errs.append("master plan lost the approved hard ceiling")
        for f in packets(packets_dir):
            t = f.read_text(encoding="utf-8", errors="replace")
            if "Budget and closeout" in t and "HANDOFF NOTE" not in t:
                errs.append(f"{f.name}: closeout section without HANDOFF NOTE")
    elif cluster == "delegation":
        for f in packets(packets_dir):
            t = f.read_text(encoding="utf-8", errors="replace")
            if "Plan (binding" not in t:  # pre-chain packets (G1, G2) are outside compiled-unit doctrine
                continue
            for h in ("done_gate:", "work_tree:"):
                if not re.search(rf"^{h}", t, re.M):
                    errs.append(f"{f.name}: missing header {h}")
    elif cluster == "economics":
        for f in packets(packets_dir):
            t = f.read_text(encoding="utf-8", errors="replace")
            if "Budget and closeout" in t and not re.search(r"\d+\s*tool calls", t):
                errs.append(f"{f.name}: closeout section without a numeric tool-call budget")
    elif cluster == "knowledge":
        for rel in ("vault/knowledge_base/ukdl-universal.md", "vault/knowledge_base/clae/CLAE_PROCESS_RULES.md",
                    "vault/specs/gsdx-factory/l1/sections.json"):
            if not (ROOT / rel).exists():
                errs.append(f"missing knowledge surface {rel}")
    return errs


def run(cluster: str, doc: Path, packets_dir: Path):
    return check_doc(cluster, doc) + live(cluster, packets_dir)


def selftest() -> int:
    bad = []
    for c in CLUSTERS:
        if run(c, DOC, PACKETS):
            bad.append(f"baseline {c} not green: {run(c, DOC, PACKETS)[:2]}")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        txt = DOC.read_text(encoding="utf-8")
        for c in CLUSTERS:  # mutation 1: drop a member row
            first = CLUSTERS[c][0]
            (t / "d.md").write_text(txt.replace(f"- S-{first}", "- removed", 1), encoding="utf-8")
            if not check_doc(c, t / "d.md"):
                bad.append(f"mutant (member dropped) survived in {c}")
            (t / "d.md").write_text(re.sub(r"^RULE:.*$", "", txt, flags=re.M), encoding="utf-8")
            if not check_doc(c, t / "d.md"):
                bad.append(f"mutant (rule removed) survived in {c}")
        pk = t / "p"
        pk.mkdir()
        for f in packets(PACKETS):
            (pk / f.name).write_text(f.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        victim = next((f for f in packets(pk) if "Budget and closeout" in f.read_text(encoding="utf-8")), None)
        if victim:
            v = victim.read_text(encoding="utf-8")
            victim.write_text(v.replace("HANDOFF NOTE", "x").replace("tool calls", "calls"), encoding="utf-8")
            for c in ("authority", "economics"):
                if not live(c, pk):
                    bad.append(f"mutant (packet closeout stripped) survived in {c}")
            victim.write_text(re.sub(r"^done_gate:.*$", "", v, flags=re.M), encoding="utf-8")
            if not live("delegation", pk):
                bad.append("mutant (done_gate stripped) survived in delegation")
    for b in bad:
        print("SELFTEST FAIL", b)
    print("DOCTRINE-GATE SELFTEST", "FAIL" if bad else "OK")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", choices=sorted(CLUSTERS))
    ap.add_argument("--doc", default=str(DOC))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.cluster:
        ap.error("--cluster or --selftest required")
    errs = run(a.cluster, Path(a.doc), PACKETS)
    for e in errs:
        print("VIOLATION", e)
    print("DOCTRINE-GATE", "FAIL" if errs else "OK", a.cluster)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
