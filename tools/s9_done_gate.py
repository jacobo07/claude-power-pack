#!/usr/bin/env python3
"""S9 master done-gate (flow-compression Phase 8, plan 08-03).

  python3 tools/s9_done_gate.py collect --only <suite|group A|B|C|all> --out DIR
  python3 tools/s9_done_gate.py judge   --evidence DIR/evidence.json [--json PATH]
  python3 tools/s9_done_gate.py seal-check [--expect N] [--root DIR]

collect runs each suite once as a foreground subprocess, records the HEAD commit, the subject-tree hash of
tools/hooks/modules and the dirty-path set before and after, writes the raw stdout to DIR/<suite>.out and merges a
parsed record into DIR/evidence.json. judge never runs a suite: it re-judges stored evidence with code. A verdict
that is not computed here is not a verdict. INCONCLUSIVE is never PASS.

Subject tree: sha256 over the sorted `path blob` entries of HEAD:tools, HEAD:hooks and HEAD:modules, excluding this
gate's own two files (a gate cannot be bound to a tree that contains its own later edits).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
GSD_WS = "flow-compression"
SELF_FILES = ("tools/s9_done_gate.py", "tools/test_s9_done_gate.py")
SUBJECT_DIRS = ("tools", "hooks", "modules")

# name -> (tag, recorded floor, basis, group, timeout seconds)
SUITES = {
    "test_s7_replay": ("S7_PASS", 164, "07-VERIFICATION line 14", "A", 400),
    "test_s5_reconcile": ("S5_PASS", 44, "07-VERIFICATION line 14", "A", 400),
    "test_gsd_mission": ("MC_PASS", 234, "07-VERIFICATION line 14", "B", 500),
    "test_mission_continuity": ("AMCR_PASS", 38, "07-VERIFICATION line 14", "B", 300),
    "test_mission_recovery": ("AMR_PASS", 69, "STATE phase 7", "B", 300),
    "test_mission_spend": ("MSPEND_PASS", 45, "07-VERIFICATION line 14", "B", 300),
    "test_gsd_epoch": ("EPOCH_PASS", 111, "07-VERIFICATION line 14", "B", 300),
    "test_rotation_invariant": ("ROT_PASS", 17, "07-VERIFICATION line 14", "C", 200),
    "test_arm_preflight": ("PRE_PASS", 16, "07-VERIFICATION line 14", "C", 200),
    "test_s3_admission": ("S3_PASS", 11, "07-VERIFICATION line 14", "C", 200),
    "test_s4_lease": ("S4_PASS", 14, "07-VERIFICATION line 14", "C", 200),
    "test_s6_blockers": ("S6_PASS", 72, "07-VERIFICATION line 14", "C", 300),
    "test_blocked_intent": ("BI_PASS", 16, "STATE phase 6", "C", 200),
    "test_owner_boundary_delivery": ("OBD_PASS", 14, "STATE phase 6", "C", 200),
    "test_cpp_gsd_long_routing": ("ROUTE_PASS", None, "first_observed_phase_8", "C", 300),
    "test_mission_steward": ("STEWARD_PASS", None, "first_observed_phase_8", "C", 300),
    "test_gsd_mission_baseline": (None, None, "first_observed_phase_8", "C", 300),
    "test_s9_redteam": ("S9RT_PASS", None, "08-02-SUMMARY", "C", 590),
}
# Only the two reds that existed before this mission, each allowed in its own suite and nowhere else.
KNOWN_REDS = {
    "test_mission_continuity": {"V-AMCR-ONE-RESOLVER-INVENTORY"},
    "test_mission_spend": {"V-MSPEND-HOLD-PLAN-NONE"},
}
PASS_RE = re.compile(r"^PASS (\S+)")
FAIL_RE = re.compile(r"^FAIL (\S+)")
INCON_RE = re.compile(r"^INCONCLUSIVE (\S+)")
TAG_RE = re.compile(r"\b([A-Z0-9]+_PASS)=(\d+)/(\d+)")
PLAIN_RE = re.compile(r"(\d+)\s+passed,\s*(\d+)\s+failed")


def git(*args: str, cwd: Path = REPO) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()[:200]}")
    return r.stdout


def subject_tree(repo: Path = REPO, rev: str = "HEAD") -> dict:
    """The tree being judged: HEAD plus a content hash of tools/hooks/modules without the gate's own files."""
    out = {}
    for d in SUBJECT_DIRS:
        listing = git("ls-tree", "-r", rev, "--", d, cwd=repo)
        lines = []
        for ln in listing.splitlines():
            meta, _, path = ln.partition("\t")
            if path in SELF_FILES:
                continue
            lines.append(f"{path} {meta.split()[2]}")
        out[d] = hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest()
    return {"head": git("rev-parse", rev, cwd=repo).strip(), "trees": out}


def porcelain(repo: Path = REPO) -> list[str]:
    return sorted(git("status", "--porcelain", "--untracked-files=all", cwd=repo).splitlines())


def parse_output(text: str) -> dict:
    passes, fails, incon = [], [], []
    tag = None
    plain = None
    for ln in text.splitlines():
        if m := PASS_RE.match(ln):
            passes.append(m.group(1))
        elif m := FAIL_RE.match(ln):
            fails.append(m.group(1))
        elif m := INCON_RE.match(ln):
            incon.append(m.group(1))
        if m := TAG_RE.search(ln):
            tag = {"name": m.group(1), "passed": int(m.group(2)), "total": int(m.group(3))}
        if m := PLAIN_RE.search(ln):
            plain = {"passed": int(m.group(1)), "failed": int(m.group(2))}
    return {"passes": passes, "fails": fails, "inconclusive": incon, "tag_line": tag, "plain": plain}


def total_of(rec: dict) -> int | None:
    if rec.get("tag_line"):
        return rec["tag_line"]["total"]
    if rec.get("plain"):
        return rec["plain"]["passed"] + rec["plain"]["failed"]
    return None


def run_suite(name: str, out_dir: Path, repo: Path = REPO) -> dict:
    tag, floor, basis, group, timeout = SUITES[name]
    before = porcelain(repo)
    st = subject_tree(repo)
    env = dict(os.environ, CPP_RESOURCE_ADMISSION="off")
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(repo / "tools" / f"{name}.py")], cwd=str(repo), env=env,
                           capture_output=True, text=True, timeout=timeout)
        code, stdout = r.returncode, r.stdout + ("\n--stderr--\n" + r.stderr if r.stderr.strip() else "")
    except subprocess.TimeoutExpired as exc:
        code, stdout = 124, ((exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
    wall = round(time.time() - t0, 1)
    after = porcelain(repo)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.out").write_text(stdout, encoding="utf-8")
    rec = parse_output(stdout)
    rec.update(name=name, tag=tag, group=group, floor=floor, basis=basis, exit=code, wall_s=wall,
               head=st["head"], trees=st["trees"], porcelain_before=before, porcelain_after=after,
               bracket_moved=before != after, command=f"python3 tools/{name}.py")
    return rec


def merge_evidence(out_dir: Path, recs: list[dict]) -> Path:
    p = out_dir / "evidence.json"
    doc = json.loads(p.read_text()) if p.is_file() else {"suites": {}}
    for r in recs:
        doc["suites"][r["name"]] = r
    p.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    return p


# ------------------------------------------------------------------------------------------------ the suite judge
def judge_suite(rec: dict, current: dict) -> dict:
    """One suite record -> {'status': PASS|FAIL|INCONCLUSIVE, 'reasons': [...]}. current = subject_tree() of the tree judged."""
    name = rec["name"]
    reasons_fail, reasons_inc = [], []
    if rec.get("trees") != current["trees"]:      # the subject trees decide; a later commit of notes or reports does not move them
        reasons_inc.append("evidence bound to a different tree than the one judged")
    if rec.get("bracket_moved"):
        reasons_inc.append("the dirty-path set moved during the run")
    allowed = KNOWN_REDS.get(name, set())
    extra = sorted(set(rec.get("fails", [])) - allowed)
    if extra:
        reasons_fail.append(f"red outside the known set: {extra}")
    if rec.get("exit") not in (0, None) and not extra:
        if not (rec.get("fails") and set(rec["fails"]) <= allowed):
            reasons_fail.append(f"non-zero exit {rec.get('exit')} not explained by a known red")
    if SUITES[name][0] and not rec.get("tag_line"):
        reasons_fail.append("tag line missing")
    elif SUITES[name][0] and rec["tag_line"]["name"] != SUITES[name][0]:
        reasons_fail.append(f"tag line {rec['tag_line']['name']} is not {SUITES[name][0]}")
    if not SUITES[name][0] and not rec.get("plain"):
        reasons_fail.append("passed/failed line missing")
    tot, floor = total_of(rec), rec.get("floor")
    if tot is None:
        reasons_fail.append("gate count unreadable")
    elif floor is not None and tot < floor:
        reasons_fail.append(f"gate count {tot} fell below the recorded {floor}")
    status = "FAIL" if reasons_fail else ("INCONCLUSIVE" if reasons_inc else "PASS")
    return {"status": status, "reasons": reasons_fail + reasons_inc, "total": tot, "known_reds_seen": sorted(set(rec.get("fails", [])) & allowed),
            "gate_inconclusive": sorted(rec.get("inconclusive", []))}


def judge_suites(evidence: dict, current: dict) -> dict:
    return {n: judge_suite(r, current) for n, r in sorted(evidence.get("suites", {}).items())}


# ------------------------------------------------------------------------------------------------ seal check
def seal_progress(root: Path, tool: str | None = None) -> dict:
    tool = tool or os.environ.get("GSD_TOOLS") or str(Path.home() / ".claude/gsd-core/bin/gsd-tools.cjs")
    r = subprocess.run(["node", tool, "query", "init.progress", "--ws", GSD_WS, "--raw", "--cwd", str(root)], cwd=str(root),
                       capture_output=True, text=True, timeout=90)
    out = r.stdout.strip()
    if out.startswith("@file:"):
        out = Path(out[len("@file:"):]).read_text(encoding="utf-8")
    doc = json.loads(out)
    phases = {str(p.get("number")): p for p in doc.get("phases") or []}
    return {"project_root": doc.get("project_root"), "completed_count": doc.get("completed_count"),
            "phase8": phases.get("08"), "phase_count": doc.get("phase_count")}


def seal_check(root: Path, expect: int | None) -> tuple[int, str]:
    try:
        p = seal_progress(root)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return 2, f"SEAL_INCONCLUSIVE init.progress did not run: {type(exc).__name__}"
    if os.path.realpath(str(p["project_root"])) != os.path.realpath(str(root)):
        return 1, f"SEAL_WRONG_ROOT project_root={p['project_root']} root={root}"
    n = p["completed_count"]
    line = f"completed_count={n} project_root={p['project_root']}"
    if expect is not None and n == expect:
        return 0, f"SEAL_OK {line}"
    ph8 = p.get("phase8") or {}
    if n == 7 and ph8.get("verification_status") != "passed":
        return 2, f"PENDING_VERIFIER {line} phase8_verification={ph8.get('verification_status')}"
    return 1, f"SEAL_MISMATCH {line} expected={expect}"


# ------------------------------------------------------------------------------------------------ plan-output consumers
PHASES = REPO / ".planning/workstreams/flow-compression/phases"
P8 = PHASES / "08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate"
P7 = PHASES / "07-s7-historical-replay-champion-challenger"
SPEC = REPO / "vault/specs/flow-compression.md"
UKDL = REPO / "vault/knowledge_base/ukdl-universal.md"
BREACH_FILE = REPO / "vault/incidents/2026-10-25-flow-compression-redteam-breaches.md"
MISSION_BASE = "7edba723"
LIVE_MISSION = "m-3d5f0a27e41d"
BASE_INCIDENTS = 8
ACCEPTANCE = ("test_gsd_mission", "test_mission_continuity", "test_mission_recovery", "test_gsd_epoch",
              "test_cpp_gsd_long_routing", "test_rotation_invariant")
SAFETY_CLAIMS = (7, 10, 11, 14)
ROW_STATUSES = ("MET", "MET_WITH_UNMEASURED", "NOT_MET", "UNMEASURED")
VERDICTS = ("DONE", "DONE_WITH_RESIDUALS", "NOT_DONE", "INCONCLUSIVE")
LAPTOP_ONLY = ("S3 DEFER autopsy", "S5 149 h disposal on the laptop ledger", "live laptop hooks and settings", "the laptop gsd-core")


def _tools_mod(name: str):
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    return __import__(name)


def _fm_check(path: Path, plan: bool) -> str | None:
    """None when the frontmatter is sound, else the reason."""
    tool = os.environ.get("GSD_TOOLS") or str(Path.home() / ".claude/gsd-core/bin/gsd-tools.cjs")
    args = ["frontmatter", "validate", str(path), "--schema", "plan", "--raw"] if plan else ["frontmatter", "get", str(path), "--raw"]
    r = subprocess.run(["node", tool, *args], capture_output=True, text=True, timeout=60, cwd=str(REPO))
    out = r.stdout.strip()
    if plan:
        return None if out.startswith("valid") else (out or r.stderr.strip())[:120] or "invalid"
    try:
        doc = json.loads(out)
    except ValueError:
        return "frontmatter did not parse"
    return None if isinstance(doc, dict) and doc.get("phase") else "frontmatter has no phase key"


LEGACY_PLANS = ("01-01-PLAN.md", "02-01-PLAN.md", "03-01-PLAN.md", "04-01-PLAN.md")   # written before the phase-seal frontmatter rule


def frontmatter_scan(repo: Path = REPO) -> dict:
    files, bad, pending, legacy = [], [], [], []
    for pat, plan in (("*-PLAN.md", True), ("*-SUMMARY.md", False), ("*-VERIFICATION.md", False)):
        for f in sorted((repo / ".planning/workstreams/flow-compression/phases").glob(f"*/{pat}")):
            files.append(f.name)
            why = _fm_check(f, plan)
            if why and f.name in LEGACY_PLANS and not f.read_text(encoding="utf-8").startswith("---"):
                legacy.append(f.name)
            elif why:
                bad.append(f"{f.name}: {why}")
    if not any(n == "08-VERIFICATION.md" for n in files):
        pending.append("08-VERIFICATION.md")
    return {"files": len(files), "bad": bad, "legacy_no_frontmatter": legacy, "pending_verifier": pending}


def live_epochs(mission: str = LIVE_MISSION) -> dict:
    r = subprocess.run([sys.executable, str(TOOLS / "gsd_epoch.py"), "epochs", "--mission", mission],
                       capture_output=True, text=True, timeout=90, cwd=str(REPO))
    try:
        rows = json.loads(r.stdout)
    except ValueError:
        return {"observed": False, "mission": mission, "total": None, "context_rotation": None}
    return {"observed": True, "mission": mission, "total": len(rows),
            "context_rotation": sum(1 for e in rows if e.get("start_cause") == "CONTEXT_ROTATION")}


def gather_context(evidence_dir: Path, repo: Path = REPO) -> dict:
    kv, rt = _tools_mod("s9_kv_check"), _tools_mod("redteam_s9")
    incs = sorted((repo / "vault/incidents").glob("2026-10-2*-flow-compression-*.md"))
    inc_findings = kv.check_incidents(incs, evidence_dir, repo)
    red_path = P8 / "08-REDTEAM.json"
    red = json.loads(red_path.read_text(encoding="utf-8"))
    rel = str(red_path.relative_to(repo))
    blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(repo), capture_output=True, timeout=60).stdout
    claims = {}
    for c in red["claims"]:
        claims[str(c["id"])] = {"verdict": c["verdict"], "reason": c.get("reason"),
                                "planes": sorted({sb.get("plane") for sb in c.get("subs", []) if sb.get("plane")}),
                                "held_controls_fired": all(sb.get("control_fired") is True for sb in c.get("subs", [])
                                                           if sb.get("verdict") == "HELD")}
    breaches = sorted(int(k) for k, v in claims.items() if v["verdict"] == "BREACH")
    sections = []
    if BREACH_FILE.is_file():
        sections = sorted(int(n) for n in re.findall(r"^### Claim (\d+)", BREACH_FILE.read_text(encoding="utf-8"), re.M))
    pred_red = next((sb["evidence"]["pinned_prefix"]["value"] for c in red["claims"] if c["id"] == 11
                     for sb in c["subs"] if sb["name"] == "predicate"), None)
    replay = json.loads((P7 / "07-REPLAY.json").read_text(encoding="utf-8"))["by_slice"]["data"] if (P7 / "07-REPLAY.json").is_file() else {}
    return {
        "incidents": {"files": [f.name for f in incs], "findings": inc_findings},
        "ukdl_findings": kv.check_ukdl(UKDL, kv.UKDL_SECTION, repo),
        "spec_findings": kv.check_spec_predicate(SPEC, P7 / "07-PIN.json"),
        "spec_predicate": kv.recount_s8(P7 / "07-PIN.json")["predicate"],
        "redteam": {"claims": claims, "n": len(red["claims"]), "blob_equals_file": blob == red_path.read_bytes(),
                    "verdicts_closed": red.get("verdicts_closed_set"), "breaches": breaches, "predicate_value": pred_red,
                    "pin_sha256": red.get("pin_sha256")},
        "breach_incident": {"exists": BREACH_FILE.is_file(), "sections": sections},
        "core_diff": rt.diff_gsd_core(MISSION_BASE, "HEAD", cwd=repo),
        "frontmatter": frontmatter_scan(repo),
        "live": live_epochs(),
        "replay": {"s1_unmeasured": (replay.get("S1") or {}).get("UNMEASURED"), "s2_moved_earlier": (replay.get("S2") or {}).get("MOVED_EARLIER"),
                   "s3_prevented": (replay.get("S3") or {}).get("PREVENTED")},
        "preamble_105k": "~105k tokens" in "".join(f.read_text(encoding="utf-8") for f in (repo / ".planning/workstreams/flow-compression/phases").glob("01*/01-EVIDENCE.md")),
    }


# ------------------------------------------------------------------------------------------------ the mission judge
def _suite_item(suites: dict, n: str) -> dict:
    st = suites.get(n, {}).get("status")
    status = {"PASS": "GREEN", "FAIL": "RED"}.get(st, "UNMEASURED")
    return {"status": status, "plane": "GEX44-clone" if st else "GEX44-clone-not-run", "detail": f"{n} {st or 'ABSENT'}"}


def _claim_item(ctx: dict, n: int) -> dict:
    c = ctx["redteam"]["claims"].get(str(n))
    if c is None:
        return {"status": "UNMEASURED", "plane": "red-team-absent", "detail": f"claim {n} not in 08-REDTEAM.json"}
    status = {"HELD": "GREEN", "BREACH": "BREACH"}.get(c["verdict"], "UNMEASURED")
    return {"status": status, "plane": "+".join(c["planes"]) or "none", "detail": f"claim {n} {c['verdict']}"}


def build_items(suites: dict, ctx: dict) -> dict:
    it = {f"suite:{n}": _suite_item(suites, n) for n in SUITES}
    it.update({f"claim:{n}": _claim_item(ctx, n) for n in range(1, 16)})
    live, rp = ctx["live"], ctx["replay"]
    it["live:rotation_epochs"] = ({"status": "GREEN" if live["context_rotation"] else "UNMEASURED", "plane": "GEX44-host-readonly",
                                   "detail": f"{live['context_rotation']} CONTEXT_ROTATION epochs of {live['total']} for {live['mission']}"}
                                  if live["observed"] else {"status": "UNMEASURED", "plane": "GEX44-host-readonly", "detail": "epochs unreadable"})
    it["replay:s1_outcomes"] = {"status": "UNMEASURED" if (rp["s1_unmeasured"] or 0) > 0 else ("GREEN" if rp["s1_unmeasured"] == 0 else "UNMEASURED"),
                                "plane": "repo-artefact", "detail": f"07-REPLAY S1 UNMEASURED {rp['s1_unmeasured']}"}
    it["evidence:preamble_105k"] = {"status": "GREEN" if ctx["preamble_105k"] else "UNMEASURED", "plane": "repo-artefact", "detail": "01-EVIDENCE epoch-2 preamble ~105k"}
    it["replay:s2_moved_earlier"] = {"status": "GREEN" if (rp["s2_moved_earlier"] or 0) >= 1 else "UNMEASURED", "plane": "repo-artefact",
                                     "detail": f"07-REPLAY S2 MOVED_EARLIER {rp['s2_moved_earlier']}"}
    it["replay:s3_prevented"] = {"status": "GREEN" if (rp["s3_prevented"] or 0) >= 1 else "UNMEASURED", "plane": "repo-artefact",
                                 "detail": f"07-REPLAY S3 PREVENTED {rp['s3_prevented']}"}
    it["laptop:s3_defer_autopsy"] = {"status": "UNMEASURED", "plane": "LAPTOP-ONLY-not-observed", "detail": LAPTOP_ONLY[0]}
    it["laptop:s5_149h"] = {"status": "UNMEASURED", "plane": "LAPTOP-ONLY-not-observed", "detail": LAPTOP_ONLY[1]}
    it["core:unchanged"] = {"status": "GREEN" if not ctx["core_diff"] else "RED", "plane": "repo-artefact", "detail": f"gsd-core paths changed since {MISSION_BASE}: {ctx['core_diff']}"}
    bi = ctx["breach_incident"]
    inc_ok = not ctx["incidents"]["findings"]
    it["incidents:cited"] = {"status": "GREEN" if inc_ok else "RED", "plane": "repo-artefact", "detail": f"{len(ctx['incidents']['files'])} incident files"}
    it["incidents:breach-iff"] = {"status": "GREEN" if bi["exists"] == bool(ctx["redteam"]["breaches"]) and bi["sections"] == ctx["redteam"]["breaches"] else "RED",
                                  "plane": "repo-artefact", "detail": f"breaches {ctx['redteam']['breaches']} sections {bi['sections']}"}
    return it


MILESTONES = {
    "S1": ("suite:test_rotation_invariant", "live:rotation_epochs", "replay:s1_outcomes", "evidence:preamble_105k", "claim:1", "claim:2"),
    "S2": ("suite:test_arm_preflight", "replay:s2_moved_earlier", "claim:3"),
    "S3": ("suite:test_s3_admission", "replay:s3_prevented", "claim:5", "claim:6", "laptop:s3_defer_autopsy"),
    "S4": ("suite:test_s4_lease", "suite:test_mission_spend", "claim:7", "claim:8"),
    "S5": ("suite:test_s5_reconcile", "suite:test_mission_recovery", "claim:10", "laptop:s5_149h"),
    "S6": ("suite:test_s6_blockers", "suite:test_blocked_intent", "suite:test_owner_boundary_delivery", "claim:9"),
    "S7": ("suite:test_s7_replay", "claim:12", "claim:13"),
}
FC_MAP = {
    "FC-01": ("suite:test_arm_preflight", "suite:test_s3_admission", "replay:s2_moved_earlier"),
    "FC-02": ("suite:test_arm_preflight", "claim:3"),
    "FC-03": ("suite:test_rotation_invariant", "live:rotation_epochs", "claim:1", "claim:2"),
    "FC-04": ("suite:test_s3_admission", "claim:5", "claim:6"),
    "FC-05": ("suite:test_mission_spend", "suite:test_s4_lease", "claim:7", "claim:8"),
    "FC-06": ("suite:test_mission_spend", "claim:7", "claim:10", "claim:14"),
    "FC-07": ("suite:test_s5_reconcile", "suite:test_mission_recovery", "claim:10"),
    "FC-08": ("suite:test_s6_blockers", "suite:test_blocked_intent", "suite:test_owner_boundary_delivery", "claim:9", "claim:11"),
    "FC-09": ("suite:test_s7_replay", "claim:12", "claim:13"),
    "FC-10": ("core:unchanged", "claim:14"),
    "FC-11": ("suite:test_s7_replay", "claim:13"),
    "FC-12": ("incidents:cited", "incidents:breach-iff"),
}


def row_status(keys, items: dict) -> str:
    sts = [items[k] for k in keys]
    if any(i["status"] == "RED" for i in sts) or any(k.startswith("claim:") and int(k.split(":")[1]) in SAFETY_CLAIMS and items[k]["status"] == "BREACH" for k in keys):
        return "NOT_MET"
    greens = [i for i in sts if i["status"] == "GREEN"]
    if not greens:
        return "UNMEASURED"
    if len(greens) == len(sts) and all("LAPTOP" not in i["plane"] for i in greens):
        return "MET"
    return "MET_WITH_UNMEASURED"


def _gate(ok: bool, detail: str) -> dict:
    return {"ok": bool(ok), "detail": detail}


def judge_all(evidence: dict, ctx: dict, current: dict) -> dict:
    suites = judge_suites(evidence, current)
    items = build_items(suites, ctx)
    rows = {m: {"status": row_status(k, items), "items": list(k)} for m, k in MILESTONES.items()}
    fc = {f: {"status": row_status(k, items), "items": list(k)} for f, k in FC_MAP.items()}
    red = ctx["redteam"]
    inc_n = len(ctx["incidents"]["files"])
    claim15 = red["claims"].get("15", {})
    bi = ctx["breach_incident"]
    fm = ctx["frontmatter"]
    gates = {
        "V-S9-SUITES": _gate(all(r["status"] == "PASS" for r in suites.values()) and len(suites) == len(SUITES),
                             f"{sum(r['status'] == 'PASS' for r in suites.values())}/{len(SUITES)} suites PASS, red {[n for n, r in suites.items() if r['status'] == 'FAIL']}, inconclusive {[n for n, r in suites.items() if r['status'] == 'INCONCLUSIVE']}"),
        "V-S9-INCIDENTS": _gate(not ctx["incidents"]["findings"] and inc_n == BASE_INCIDENTS + (1 if bi["exists"] else 0),
                                f"{inc_n} files, findings {ctx['incidents']['findings']}"),
        "V-S9-UKDL": _gate(not ctx["ukdl_findings"], f"findings {ctx['ukdl_findings']}"),
        "V-S9-SPEC-PREDICATE": _gate(not ctx["spec_findings"], f"findings {ctx['spec_findings']}"),
        "V-S9-REDTEAM": _gate(red["blob_equals_file"] and red["n"] == 15 and set(red["verdicts_closed"] or ()) == {"HELD", "BREACH", "UNMEASURED"}
                              and all(c["held_controls_fired"] for c in red["claims"].values())
                              and claim15.get("verdict") == "UNMEASURED" and "OWNER DECISION NEEDED" in (claim15.get("reason") or ""),
                              f"blob_equals_file={red['blob_equals_file']} claims={red['n']} claim15={claim15.get('verdict')}"),
        "V-S9-BREACH-INCIDENT-IFF": _gate(bi["exists"] == bool(red["breaches"]) and bi["sections"] == red["breaches"],
                                          f"breaches {red['breaches']} file {bi['exists']} sections {bi['sections']}"),
        "V-S9-PREDICATE-AGREE": _gate(red["predicate_value"] is not None and red["predicate_value"] == ctx["spec_predicate"],
                                      f"spec {ctx['spec_predicate']} red team {red['predicate_value']}"),
        "V-S9-CORE-UNCHANGED": _gate(not ctx["core_diff"], f"gsd-core paths changed since {MISSION_BASE}: {ctx['core_diff']}"),
        "V-S9-FRONTMATTER": _gate(fm["files"] > 0 and not fm["bad"], f"{fm['files']} files, bad {fm['bad']}, pending {fm['pending_verifier']}"),
        "V-S9-ACCEPTANCE": _gate(all(n in suites and suites[n]["status"] == "PASS" for n in ACCEPTANCE),
                                 f"{[n for n in ACCEPTANCE if suites.get(n, {}).get('status') != 'PASS']} not PASS"),
        "V-S9-MILESTONES": _gate(sorted(rows) == [f"S{i}" for i in range(1, 8)] and all(r["status"] in ROW_STATUSES for r in rows.values()),
                                 " ".join(f"{m}={r['status']}" for m, r in rows.items())),
        "V-S9-FC-TABLE": _gate(sorted(fc) == [f"FC-{i:02d}" for i in range(1, 13)] and all(f["items"] for f in fc.values()),
                               " ".join(f"{k}={v['status']}" for k, v in fc.items())),
    }
    causes, residuals = [], []
    inconclusive = [n for n, r in suites.items() if r["status"] == "INCONCLUSIVE"]
    for n, r in suites.items():
        if r["status"] == "FAIL":
            causes.append(f"suite {n} red: {r['reasons']}")
    for c in SAFETY_CLAIMS:
        if red["claims"].get(str(c), {}).get("verdict") == "BREACH":
            causes.append(f"safety claim {c} BREACH")
    if ctx["core_diff"]:
        causes.append(f"GSD Core paths changed: {ctx['core_diff']}")
    if ctx["incidents"]["findings"]:
        causes.append("incident citation failed")
    for g, r in gates.items():
        if not r["ok"] and g not in ("V-S9-SUITES", "V-S9-ACCEPTANCE"):
            causes.append(f"{g} red: {r['detail']}")
    for b in red["breaches"]:
        if b not in SAFETY_CLAIMS:
            residuals.append(f"claim {b} BREACH")
    residuals += [f"claim {k} UNMEASURED" for k, v in sorted(red["claims"].items(), key=lambda x: int(x[0])) if v["verdict"] == "UNMEASURED"]
    residuals += [f"milestone {m} {r['status']}" for m, r in rows.items() if r["status"] != "MET"]
    if fm["legacy_no_frontmatter"]:
        residuals.append(f"{len(fm['legacy_no_frontmatter'])} legacy PLAN files carry no frontmatter: {fm['legacy_no_frontmatter']}")
    residuals += [f"LAPTOP-ONLY: {x}" for x in LAPTOP_ONLY]
    seen = sorted({g for r in suites.values() for g in r["known_reds_seen"]})
    residuals += [f"known red {g}" for g in seen]
    if causes:
        verdict = "NOT_DONE"
    elif inconclusive:
        verdict = "INCONCLUSIVE"
        causes.append(f"evidence not bound: {inconclusive}")
    elif residuals:
        verdict = "DONE_WITH_RESIDUALS"
    else:
        verdict = "DONE"
    gates["V-S9-VERDICT"] = _gate(verdict in VERDICTS, verdict)
    return {"suites": suites, "items": items, "milestones": rows, "fc": fc, "gates": gates, "verdict": verdict,
            "causes": causes, "residuals": residuals}


def slim_evidence(evidence: dict) -> dict:
    """Parsed per-suite evidence without raw output (the .out files stay in the evidence directory)."""
    return {"suites": {n: {k: v for k, v in r.items()} for n, r in sorted(evidence["suites"].items())}}


def write_gate_doc(evidence: dict, ctx: dict, current: dict, path: Path) -> dict:
    res = judge_all(evidence, ctx, current)
    doc = {"schema": "s9-done-gate/1", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "command": "python3 tools/s9_done_gate.py judge --evidence /tmp/s9-gate/evidence.json --write-gate <path>",
           "judged_tree": current, "evidence": slim_evidence(evidence), "context": ctx, "judgement": res}
    path.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str), encoding="utf-8")
    return res


# ------------------------------------------------------------------------------------------------ report
ROUTE_STATEMENT = ("test_cpp_gsd_long_routing is red outside the known set on this host: V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND finds no "
                   "cpp-gsd-long.md under the HOME the test builds (its own message: 'sync with Copy-Item if red'). The other 8 gates of that "
                   "suite pass. This is a host-installation check, not a repo defect; it is recorded as a cause because the known-red set is closed.")
CITE_SOURCES = (
    ("07-VERIFICATION.md", P7 / "07-VERIFICATION.md", re.compile(r"^- W[1-5]: ")),
    ("STATE.md", REPO / ".planning/workstreams/flow-compression/STATE.md", re.compile(r"^- Carried to Phase 8, (epoch_compacted|W2 and W3)")),
)


def cited_lines(repo: Path = REPO) -> list[tuple[str, str]]:
    out = []
    for label, path, rx in CITE_SOURCES:
        path = repo / path.relative_to(REPO)
        if path.is_file():
            out += [(label, ln) for ln in path.read_text(encoding="utf-8").splitlines() if rx.search(ln)]
    return out


def render_report(doc: dict, repo: Path = REPO) -> str:
    j = doc["judgement"]
    L = ["# Phase 8 master gate report (flow-compression S9)", "",
         f"Verdict: **{j['verdict']}**", "", "Rendered from 08-DONE-GATE.json by `python3 tools/s9_done_gate.py report`; never edited by hand.", "",
         "## Causes", ""]
    L += [f"- {c}" for c in j["causes"]] or ["- none"]
    L += ["", "## Statement on the one red suite", "", ROUTE_STATEMENT, "", "## Gates", ""]
    L += [f"- {'PASS' if r['ok'] else 'FAIL'} {g}: {r['detail']}" for g, r in sorted(j["gates"].items())]
    L += ["", "## Suites", ""] + [f"- {r['status']} {n} total={r['total']}" for n, r in sorted(j["suites"].items())]
    L += ["", "## Milestones S1-S7", ""] + [f"- {m}: {r['status']}" for m, r in sorted(j["milestones"].items())]
    L += ["", "## FC-01..FC-12", ""] + [f"- {k}: {v['status']}" for k, v in sorted(j["fc"].items())]
    L += ["", "## Residuals", ""] + [f"- {x}" for x in j["residuals"]]
    L += ["", "## Residuals cited verbatim", ""] + [f"> [{label}] {ln}" for label, ln in cited_lines(repo)] + [""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ cli
def _select(only: str) -> list[str]:
    if only == "all":
        return list(SUITES)
    if only in ("A", "B", "C"):
        return [n for n, v in SUITES.items() if v[3] == only]
    if only in SUITES:
        return [only]
    raise SystemExit(f"unknown suite or group: {only}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("collect")
    c.add_argument("--only", required=True)
    c.add_argument("--out", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--evidence", required=True)
    j.add_argument("--json")
    j.add_argument("--write-gate")
    s = sub.add_parser("seal-check")
    s.add_argument("--expect", type=int)
    s.add_argument("--root", default=str(REPO))
    r = sub.add_parser("report")
    r.add_argument("--write")
    args = ap.parse_args(argv)
    if args.cmd == "collect":
        out = Path(args.out)
        recs = []
        for name in _select(args.only):
            rec = run_suite(name, out)
            recs.append(rec)
            print(f"COLLECT {name} exit={rec['exit']} wall={rec['wall_s']}s total={total_of(rec)} fails={rec['fails']} bracket_moved={rec['bracket_moved']}")
            merge_evidence(out, [rec])
        return 0
    if args.cmd == "judge":
        ev_path = Path(args.evidence)
        ev = json.loads(ev_path.read_text())
        cur = subject_tree()
        ctx = gather_context(ev_path.parent)
        res = judge_all(ev, ctx, cur)
        for n, r in res["suites"].items():
            print(f"{r['status']} {n} total={r['total']} {r['reasons']}")
        for g, r in res["gates"].items():
            print(f"{'PASS' if r['ok'] else 'FAIL'} {g} {r['detail']}")
        for m, r in res["milestones"].items():
            print(f"MILESTONE {m} {r['status']}")
        print(f"VERDICT {res['verdict']} causes={res['causes']}")
        if args.json:
            Path(args.json).write_text(json.dumps(res, indent=1, sort_keys=True, default=str))
        if args.write_gate:
            write_gate_doc(ev, ctx, cur, Path(args.write_gate))
        return {"DONE": 0, "DONE_WITH_RESIDUALS": 0, "NOT_DONE": 1, "INCONCLUSIVE": 2}[res["verdict"]]
    if args.cmd == "seal-check":
        code, msg = seal_check(Path(args.root).resolve(), args.expect)
        print(msg)
        return code
    if args.cmd == "report":
        gate = P8 / "08-DONE-GATE.json"
        text = render_report(json.loads(gate.read_text(encoding="utf-8")))
        if args.write:
            Path(args.write).write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
