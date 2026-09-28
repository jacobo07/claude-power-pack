#!/usr/bin/env python3
"""seal_check.py -- phase-local, read-only seal checker for Phase 5 (seal and hand back).

Reads files under the repo root and takes every git fact on stdin from a plain git
command run by the caller (git status/rev-list/show). It never runs git itself, writes
nothing, and makes no model or network call.

Usage:
  python3 seal_check.py --selftest                 # synthetic fixtures only
  python3 seal_check.py content --stage N           # N = 1..4, no stdin
  git rev-list HEAD | python3 seal_check.py hashes --stage N
  git show cd4e436:<path> | python3 seal_check.py preserve res|ukdl --stage N
  git status --porcelain=v1 --untracked-files=all --branch | python3 seal_check.py status
"""
from __future__ import annotations

import re
import string
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# .../05-seal-and-hand-back/seal_check.py -> parents[5] is the repo/worktree root:
# 0 phases/05-.../ (self.parent), 1 phases/, 2 cognitive-resource-os/, 3 workstreams/,
# 4 .planning/, 5 repo root. Mirrors by_entrypoint.py's own ROOT derivation.
ROOT = Path(__file__).resolve().parents[5]

# Populated by _ensure_importable(), never at module-import time: a bare
# `import seal_check` must not print or sys.exit (S0).
SLOP_LISTS = None
redact = None

passes = fails = 0


def _ensure_importable() -> None:
    """Idempotent. Adds ROOT to sys.path and imports SLOP_LISTS/redact into module
    globals. Called from main()/selftest() only -- never at module-import time."""
    global SLOP_LISTS, redact
    if SLOP_LISTS is not None:
        return
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from modules.output_contracts.validator import SLOP_LISTS as _SL
    from modules.secret_firewall.redactor import redact as _redact
    SLOP_LISTS = _SL
    redact = _redact


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE = "cd4e436"
RES_REL = "vault/plans/cognitive-resource-os-RESUMPTION.md"
UKDL_REL = "vault/knowledge_base/ukdl-cognitive-resource-os.md"
PH_REL = ".planning/workstreams/cognitive-resource-os/phases"
PHASE_DIRS = {
    1: "01-gate-verdict-on-the-big-host",
    2: "02-gex44-observed-baseline",
    3: "03-p3-pre-flight-p0",
    4: "04-prefix-cache-miss-a-b",
}
P5_DIR_REL = f"{PH_REL}/05-seal-and-hand-back"
EVIDENCE_FILE = f"{P5_DIR_REL}/EVIDENCE.md"
EVIDENCE_PATHS = {n: f"{PH_REL}/{PHASE_DIRS[n]}/EVIDENCE.md" for n in range(1, 5)}
VERIFICATION_PATHS = {
    1: f"{PH_REL}/{PHASE_DIRS[1]}/01-VERIFICATION.md",
    2: f"{PH_REL}/{PHASE_DIRS[2]}/02-VERIFICATION.md",
    3: f"{PH_REL}/{PHASE_DIRS[3]}/03-VERIFICATION.md",
    4: f"{PH_REL}/{PHASE_DIRS[4]}/04-VERIFICATION.md",
}
REVIEW_PATHS = {
    2: f"{PH_REL}/{PHASE_DIRS[2]}/02-REVIEW.md",
    4: f"{PH_REL}/{PHASE_DIRS[4]}/04-REVIEW.md",
}
SUMMARY_PATHS = [
    f"{PH_REL}/{PHASE_DIRS[1]}/01-01-SUMMARY.md",
    f"{PH_REL}/{PHASE_DIRS[1]}/01-02-SUMMARY.md",
    f"{PH_REL}/{PHASE_DIRS[2]}/02-01-SUMMARY.md",
    f"{PH_REL}/{PHASE_DIRS[3]}/03-01-SUMMARY.md",
    f"{PH_REL}/{PHASE_DIRS[4]}/04-01-SUMMARY.md",
]
VERDICT_KEYS = {1: "phase_verdict", 2: "phase_verdict", 3: "p0_verdict", 4: "verdict"}
EXTRA_KEYS = {1: ["gates_verdict", "suite_verdict"], 4: ["rule_fired"]}
ORIG_UKDL_IDS = [
    "HR-COST-OBSERVED-001",
    "PR-PRICING-PROVENANCE-001",
    "PR-TRANSCRIPT-DEDUPE-001",
    "PR-SPLIT-BY-ENTRYPOINT-001",
    "T-PROJECT-KEY-PARTIAL-SANITIZE-001",
    "T-ONCE-PER-SESSION-PREFIX-001",
    "T-ONE-CALL-1H-CACHE-WRITE-001",
    "T-KNOWLEDGE-CORPUS-AUTOFEED-001",
]
# gate: ALWAYS (unconditional), VERIFICATION (gate_verification), REVIEW_CR01 (gate_review_cr01)
NEW_UKDL = {
    "PR-OWNER-GATE-BEFORE-RUN-001": {
        "section": "Process Rules", "phases": [1], "extra_paths": [], "gate": "ALWAYS",
    },
    "T-BASELINE-WITHOUT-HOST-001": {
        "section": "Traps", "phases": [2], "extra_paths": [], "gate": "ALWAYS",
    },
    "T-MEASURER-IN-CORPUS-001": {
        "section": "Traps", "phases": [2, 4], "extra_paths": [], "gate": "ALWAYS",
    },
    "T-RULE-EXCLUSION-SCOPE-001": {
        "section": "Traps", "phases": [3], "extra_paths": [], "gate": "ALWAYS",
    },
    "T-BACK-TO-BACK-REUSE-001": {
        "section": "Traps", "phases": [4, 2], "extra_paths": [], "gate": "VERIFICATION",
    },
    "T-TRUTHY-PRESENCE-GUARD-001": {
        "section": "Traps", "phases": [4], "extra_paths": [REVIEW_PATHS[4]],
        "gate": "REVIEW_CR01",
    },
}
LAPTOP_LITERALS = {
    "res": [
        "97 sessions", "168,631", "13,858", "≈ 50%", "$90.06", "272 calls",
        "62 sessions", "79.9%", "1.9% sdk-cli", "16.4% cli",
        "`python tools/test_tis_observed.py` 25/25", "~630 MB",
        "renewed missions made 0 commits", "~102k", "56.8k", "21.4k", "267->216 KB",
    ],
    "ukdl": [
        "~98.5%", "381 usage lines", "17,041", "400/400", "exists on this host",
        "0.32%", "79.9%", "$72.00", "1.9% (sdk-cli)", "(cli) of its prefix", "949 KB",
    ],
}
ALLOWED_UNTRACKED = [
    ".planning/active-workstream",
    ".planning/workstreams/cognitive-resource-os/config.json",
    ".planning/workstreams/cognitive-resource-os/milestone.lock",
    ".planning/workstreams/cognitive-resource-os/state.json",
]
TRACKING = [
    ".planning/workstreams/cognitive-resource-os/ROADMAP.md",
    ".planning/workstreams/cognitive-resource-os/STATE.md",
    ".planning/workstreams/cognitive-resource-os/REQUIREMENTS.md",
]
BRANCH_HEADER = "## mission/cognitive-resource-os-gex44"
FF_COMMAND = ("git -C /home/kobii/missions/cognitive-resource-os merge --ff-only "
              "mission/cognitive-resource-os-gex44")
FETCH_COMMAND = ("git fetch gex44:/home/kobii/missions/cognitive-resource-os "
                  "mission/cognitive-resource-os-gex44")
HANDBACK_LITERALS = [
    FF_COMMAND, FETCH_COMMAND, "cd4e436", ".claude/worktrees/cro-gex44",
    "mission/cognitive-resource-os-gex44",
]


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def norm_tokens(text: str) -> list:
    out = []
    for w in text.split():
        w2 = w.strip(string.punctuation).lower()
        if w2:
            out.append(w2)
    return out


def lost_tokens(orig: str, new: str) -> list:
    o = set(norm_tokens(orig))
    n = set(norm_tokens(new))
    return sorted(o - n)


def unlabelled(text: str, literals) -> list:
    problems = []
    for line in text.splitlines():
        for lit in literals:
            if lit in line and "laptop" not in line.lower():
                problems.append(line)
                break
    return problems


def figures(text: str) -> list:
    stripped = re.sub(r"`[^`]*`", "", text)
    out = []
    out += re.findall(r"\$\d[\d,]*(?:\.\d+)?", stripped)
    out += re.findall(r"\d[\d,]*(?:\.\d+)?%", stripped)
    out += re.findall(r"\b\d+/\d+\b", stripped)
    return out


def _backticked_hash_candidates(text: str) -> list:
    return re.findall(r"`([0-9a-fA-F]{7,40})`", text)


def resolve(tokens, revs) -> list:
    """Accepts a backticked hash that prefixes one of revs (case-insensitive); reports
    an unknown one; ignores a digits-only token (at least one a-f letter required)."""
    unresolved = []
    revs_l = [r.lower() for r in revs]
    for t in tokens:
        tl = t.lower()
        if not re.search(r"[a-f]", tl):
            continue
        if not any(r.startswith(tl) for r in revs_l):
            unresolved.append(t)
    return unresolved


def _heading_lines(text: str, prefix: str) -> list:
    return [i for i, l in enumerate(text.splitlines()) if l.startswith(prefix)]


def _heading_count(text: str, prefix: str) -> int:
    return len(_heading_lines(text, prefix))


def _first_heading_index(text: str, prefix: str):
    idxs = _heading_lines(text, prefix)
    return idxs[0] if idxs else None


def section(text: str, heading_prefix: str):
    """From the first line starting heading_prefix to the line before the next line
    starting with the same marker level ('## ' or '### '), or end of text."""
    level = "### " if heading_prefix.startswith("### ") else "## "
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.startswith(heading_prefix):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith(level):
            end = j
            break
    return "\n".join(lines[start:end])


def bullets(text: str) -> dict:
    """Lines starting '- Phase N (CRO-0N)' plus continuation lines up to the next
    '- ', a heading, or a blank line. Returns {phase_num: full_text}."""
    lines = text.splitlines()
    result = {}
    n = len(lines)
    i = 0
    pat = re.compile(r"^- Phase (\d) \(CRO-0(\d)\)")
    while i < n:
        m = pat.match(lines[i])
        if m and m.group(1) == m.group(2):
            phase = int(m.group(1))
            buf = [lines[i]]
            j = i + 1
            while j < n:
                l = lines[j]
                if l.startswith("- ") or l.startswith("#") or l.strip() == "":
                    break
                buf.append(l)
                j += 1
            result[phase] = "\n".join(buf)
            i = j
        else:
            i += 1
    return result


def ukdl_entries(text: str) -> dict:
    """Paragraphs starting `**\\`ID\\`**`. Returns {id: full_paragraph_text}."""
    lines = text.splitlines()
    result = {}
    n = len(lines)
    id_re = re.compile(r"^\*\*`([A-Z0-9_-]+)`\*\*")
    i = 0
    while i < n:
        m = id_re.match(lines[i])
        if m:
            eid = m.group(1)
            buf = [lines[i]]
            j = i + 1
            while j < n:
                l = lines[j]
                if l.strip() == "" or l.startswith("#") or id_re.match(l):
                    break
                buf.append(l)
                j += 1
            result[eid] = "\n".join(buf)
            i = j
        else:
            i += 1
    return result


def fm_status(path) -> str:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return "absent"
    if not text.startswith("---"):
        return "absent"
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return "absent"
    for line in lines[1:end]:
        m = re.match(r"^status:\s*(.+)$", line)
        if m:
            return m.group(1).strip()
    return "absent"


def key_line(text: str, key: str):
    pat = re.compile(r"^" + re.escape(key) + r":\s.*$", re.MULTILINE)
    m = pat.search(text)
    return m.group(0) if m else None


def privacy(text: str) -> list:
    problems = []
    if re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                 r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", text):
        problems.append("uuid-shaped string")
    if ".claude/projects/-" in text:
        problems.append(".claude/projects/- path")
    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", text):
        problems.append("email address")
    _ensure_importable()
    if redact(text) != text:
        problems.append("secret pattern (redact changed text)")
    low = text.lower()
    for tok in SLOP_LISTS.get("docs", ()):
        if tok.lower() in low:
            problems.append(f"slop token: {tok}")
    return problems


def classify_status(porcelain_text: str):
    lines = [l for l in porcelain_text.splitlines()]
    if not lines:
        return ("FAIL", "no input on stdin")
    if lines[0] != BRANCH_HEADER:
        return ("FAIL", f"unexpected branch header: {lines[0]!r}")
    dirty = []
    tracking = []
    for line in lines[1:]:
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.strip()
        if line.startswith("??"):
            if path in ALLOWED_UNTRACKED:
                continue
            dirty.append(line)
        else:
            if path in TRACKING:
                tracking.append(line)
            else:
                dirty.append(line)
    if dirty:
        return ("DIRTY", dirty)
    if tracking:
        return ("TRACKING_ONLY", tracking)
    return ("CLEAN", [])


def derive_gates(root: Path):
    v4 = fm_status(root / VERIFICATION_PATHS[4])
    gate_verification = "WRITE" if v4 in ("passed", "human_needed") else "HOLD"
    gate_review_cr01 = "HOLD"
    p = root / REVIEW_PATHS[4]
    if p.exists():
        text = p.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("### CR-01:") and "env_check" in line:
                gate_review_cr01 = "WRITE"
                break
    return gate_verification, gate_review_cr01


def open_findings(root: Path) -> list:
    ids = []
    for _ph, path in REVIEW_PATHS.items():
        p = root / path
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        fixed_ids = set()
        parts = text.split("---")
        if len(parts) >= 3:
            fm = parts[1]
            for m in re.finditer(r"^\s*([A-Z]+-\d+):\s*\{([^}]*)\}", fm, re.MULTILINE):
                fid, body = m.group(1), m.group(2)
                if "outcome: fixed" in body:
                    fixed_ids.add(fid)
        for m in re.finditer(r"^### (CR|BL)-(\d+):", text, re.MULTILINE):
            fid = f"{m.group(1)}-{m.group(2)}"
            if fid not in fixed_ids:
                ids.append(fid)
    return ids


def parse_summary_commits(root: Path) -> list:
    commits = []
    pat = re.compile(r"^\d+\.\s+\*\*Task \d+:.*?\*\*\s+-\s+`([0-9a-fA-F]{7,40})`",
                      re.MULTILINE)
    for f in SUMMARY_PATHS:
        p = root / f
        if p.exists():
            commits.extend(pat.findall(p.read_text(encoding="utf-8")))
    return commits


def parse_review_fix_commits(root: Path) -> list:
    commits = []
    for _ph, f in REVIEW_PATHS.items():
        p = root / f
        if p.exists():
            text = p.read_text(encoding="utf-8")
            parts = text.split("---")
            if len(parts) >= 3:
                commits.extend(re.findall(r"commit:\s*([0-9a-fA-F]{7,40})", parts[1]))
    return commits


def _read(path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


# ---------------------------------------------------------------------------
# content mode
# ---------------------------------------------------------------------------

def _check_ukdl_entry(root: Path, eid: str, etext: str, ukdl_text: str) -> list:
    problems = []
    spec = NEW_UKDL[eid]
    cited_paths = [EVIDENCE_PATHS[p] for p in spec["phases"]] + spec["extra_paths"]
    for p in cited_paths:
        if f"`{p}`" not in etext:
            problems.append(f"{eid} missing citation `{p}`")
        if not (root / p).exists():
            problems.append(f"{eid} cited path missing on disk: {p}")
    if "GEX44" not in etext:
        problems.append(f"{eid} missing GEX44 label")
    fig_pool = set()
    for p in cited_paths:
        fp = root / p
        if fp.exists():
            fig_pool |= set(figures(_read(fp) or ""))
    bad = [f for f in figures(etext) if f not in fig_pool]
    if bad:
        problems.append(f"{eid} figures not found in cited files: {bad}")
    sec = section(ukdl_text, f"### {spec['section']}")
    if sec is None or eid not in sec:
        problems.append(f"{eid} not located under its planned section {spec['section']}")
    return problems


def _stage1_checks(root, res_text, ukdl_text, ev5_text) -> list:
    problems = []
    if _heading_count(res_text, "## 2d. Verdicts") != 1:
        problems.append("RES '## 2d. Verdicts' heading count != 1")
    idx2b = _first_heading_index(res_text, "## 2b.")
    idx2d = _first_heading_index(res_text, "## 2d. Verdicts")
    idx3 = _first_heading_index(res_text, "## 3.")
    if None in (idx2b, idx2d, idx3) or not (idx2b < idx2d < idx3):
        problems.append("RES '## 2d. Verdicts' not placed after 2b and before 3")

    res_bullets = bullets(res_text)
    b3 = res_bullets.get(3)
    if b3 is None:
        problems.append("RES missing Phase 3 bullet")
    else:
        ev3_text = _read(root / EVIDENCE_PATHS[3]) or ""
        p0_line = key_line(ev3_text, "p0_verdict")
        first_token = p0_line.split(":", 1)[1].strip().split()[0] if p0_line else None
        if not first_token or first_token not in b3:
            problems.append("phase3 bullet missing p0_verdict token")
        if "claudeMdExcludes" not in b3:
            problems.append("phase3 bullet missing claudeMdExcludes")
        if f"`{EVIDENCE_PATHS[3]}`" not in b3:
            problems.append("phase3 bullet missing backticked EV3 path")
        v3status = fm_status(root / VERIFICATION_PATHS[3])
        if f"verification: {v3status}" not in b3:
            problems.append("phase3 bullet missing verification status")
        if "GEX44" not in b3:
            problems.append("phase3 bullet missing GEX44")
        ev3_figs = set(figures(ev3_text))
        bad = [f for f in figures(b3) if f not in ev3_figs]
        if bad:
            problems.append(f"phase3 bullet figures not in EV3: {bad}")

    idx_traps = _first_heading_index(ukdl_text, "### Traps")
    entries = ukdl_entries(ukdl_text)
    if "T-RULE-EXCLUSION-SCOPE-001" not in entries:
        problems.append("UKDL missing T-RULE-EXCLUSION-SCOPE-001")
    elif idx_traps is None:
        problems.append("UKDL missing ### Traps heading")

    for eid, etext in entries.items():
        if eid in ORIG_UKDL_IDS:
            continue
        if eid not in NEW_UKDL:
            problems.append(f"unplanned UKDL id: {eid}")
            continue
        problems += _check_ukdl_entry(root, eid, etext, ukdl_text)

    if _heading_count(ev5_text, "## 0. Pre-checks") < 1:
        problems.append("EVIDENCE.md missing '## 0. Pre-checks'")
    if _heading_count(ev5_text, "## 1. Inputs") < 1:
        problems.append("EVIDENCE.md missing '## 1. Inputs'")
    hb = key_line(ev5_text, "head_before")
    if not hb or not re.match(r"^head_before:\s*[0-9a-f]{40}\s*$", hb):
        problems.append("EVIDENCE.md head_before not a 40-hex sha")
    bc = key_line(ev5_text, "base_commit")
    if bc != f"base_commit: {BASE}":
        problems.append("EVIDENCE.md base_commit wrong")
    mc = key_line(ev5_text, "model_calls")
    if mc != "model_calls: 0":
        problems.append("EVIDENCE.md model_calls not 0")

    for n in range(1, 5):
        pe = key_line(ev5_text, f"p{n}_evidence")
        if not pe or pe.split(":", 1)[1].strip() != EVIDENCE_PATHS[n]:
            problems.append(f"EVIDENCE.md p{n}_evidence mismatch")
        ev_n_text = _read(root / EVIDENCE_PATHS[n]) or ""
        actual_verdict = key_line(ev_n_text, VERDICT_KEYS[n])
        pv = key_line(ev5_text, f"p{n}_verdict_line")
        if not pv or actual_verdict is None or \
                pv.split(":", 1)[1].strip() != actual_verdict:
            problems.append(f"EVIDENCE.md p{n}_verdict_line mismatch")
        actual_status = fm_status(root / VERIFICATION_PATHS[n])
        pver = key_line(ev5_text, f"p{n}_verification")
        if not pver or pver.split(":", 1)[1].strip() != actual_status:
            problems.append(f"EVIDENCE.md p{n}_verification mismatch")
        actual_review = fm_status(root / REVIEW_PATHS[n]) if n in REVIEW_PATHS else "absent"
        prev = key_line(ev5_text, f"p{n}_review")
        if not prev or not prev.split(":", 1)[1].strip().startswith(actual_review):
            problems.append(f"EVIDENCE.md p{n}_review mismatch")

    gate_v, gate_r = derive_gates(root)
    pgv = key_line(ev5_text, "p4_gate_verification")
    if not pgv or pgv.split(":", 1)[1].strip() != gate_v:
        problems.append("EVIDENCE.md p4_gate_verification mismatch")
    pgr = key_line(ev5_text, "p4_gate_review_cr01")
    if not pgr or pgr.split(":", 1)[1].strip() != gate_r:
        problems.append("EVIDENCE.md p4_gate_review_cr01 mismatch")

    for label, text in (("RES", res_text), ("UKDL", ukdl_text), ("EVIDENCE", ev5_text)):
        priv = privacy(text)
        if priv:
            problems.append(f"{label} privacy hit: {priv}")

    return problems


def _stage2_checks(root, res_text, ukdl_text, ev5_text) -> list:
    problems = []
    order_prefixes = ["## 1.", "## 1a.", "## 2.", "## 2a.", "## 2b.", "## 2c.",
                       "## 2d.", "## 2e.", "## 3.", "## 4.", "## 4a.", "## 5."]
    idxs = {}
    for p in order_prefixes:
        found = _heading_lines(res_text, p)
        if not found:
            problems.append(f"RES missing heading {p}")
        else:
            idxs[p] = found[0]
    prev_idx, prev_p = -1, None
    for p in order_prefixes:
        if p not in idxs:
            continue
        if idxs[p] <= prev_idx:
            problems.append(f"RES heading {p} out of order (after {prev_p})")
        prev_idx, prev_p = idxs[p], p
    for p in ("## 1a.", "## 2c.", "## 2d.", "## 2e.", "## 4a."):
        c = len(_heading_lines(res_text, p))
        if c != 1:
            problems.append(f"RES heading {p} count {c} != 1")

    sec1a = section(res_text, "## 1a.") or ""
    for lit in HANDBACK_LITERALS:
        if lit not in sec1a:
            problems.append(f"RES 1a missing literal: {lit[:40]}")

    sec2 = section(res_text, "## 2.") or ""
    if "`10299f8`" not in sec2:
        problems.append("RES section 2 missing `10299f8`")

    sec2b = section(res_text, "## 2b.") or ""
    if "01-02" not in sec2b:
        problems.append("RES section 2b missing 01-02")

    res_bullets = bullets(res_text)
    for n in range(1, 5):
        bn = res_bullets.get(n)
        if bn is None:
            problems.append(f"RES missing Phase {n} bullet")
            continue
        ev_n_text = _read(root / EVIDENCE_PATHS[n]) or ""
        verdict_line = key_line(ev_n_text, VERDICT_KEYS[n])
        token = verdict_line.split(":", 1)[1].strip().split()[0] if verdict_line else None
        if not token or token not in bn:
            problems.append(f"Phase {n} bullet missing verdict token")
        for ek in EXTRA_KEYS.get(n, []):
            ekl = key_line(ev_n_text, ek)
            ekval = ekl.split(":", 1)[1].strip() if ekl else None
            if ekval and ekval.split()[0] not in bn:
                problems.append(f"Phase {n} bullet missing {ek} value")
        if f"`{EVIDENCE_PATHS[n]}`" not in bn:
            problems.append(f"Phase {n} bullet missing backticked EVIDENCE path")
        vstatus = fm_status(root / VERIFICATION_PATHS[n])
        if f"verification: {vstatus}" not in bn:
            problems.append(f"Phase {n} bullet missing verification status")
        if "GEX44" not in bn:
            problems.append(f"Phase {n} bullet missing GEX44")
        figs_ok = set(figures(ev_n_text))
        bad = [f for f in figures(bn) if f not in figs_ok]
        if bad:
            problems.append(f"Phase {n} bullet figures not in its EVIDENCE: {bad}")

    sec4 = section(res_text, "## 4.") or ""
    items = [l for l in sec4.splitlines() if re.match(r"^[123]\.\s", l)]
    if len(items) != 3:
        problems.append(f"RES section 4 has {len(items)} numbered items, expected 3")
    cite_re = re.compile(r"`" + re.escape(PH_REL) + r"/[^`]*(?:EVIDENCE|VERIFICATION)\.md`")
    if len(cite_re.findall(sec4)) < 3:
        problems.append("RES section 4 missing per-item EVIDENCE/VERIFICATION citations")

    sec4a = section(res_text, "## 4a.") or ""
    if "DEFERRED by Owner 2026-09-27" not in sec4a:
        problems.append("RES 4a missing DEFERRED literal")

    sec2e = section(res_text, "## 2e.") or ""
    for lit in ("cro-p04-ab-armA", "cro-p04-ab-armB", "MEASURED_ZERO", "10299f8"):
        if lit not in sec2e:
            problems.append(f"RES 2e missing {lit}")
    for fid in open_findings(root):
        if fid not in sec2e:
            problems.append(f"RES 2e missing open finding {fid}")

    sec5 = section(res_text, "## 5.") or ""
    if "1a" not in sec5:
        problems.append("RES section 5 missing reference to 1a")

    for heading in ("## 1a.", "## 2c.", "## 2d.", "## 2e.", "## 4."):
        sec = section(res_text, heading) or ""
        for line in sec.splitlines():
            if figures(line) and "GEX44" not in line and "laptop" not in line.lower():
                problems.append(f"unlabelled figure line under {heading}: {line[:60]}")

    if _heading_count(ev5_text, "## 2. RESUMPTION changes") < 1:
        problems.append("EVIDENCE.md missing '## 2. RESUMPTION changes'")

    return problems


def _stage3_checks(root, res_text, ukdl_text, ev5_text) -> list:
    problems = []
    idx_hr = _first_heading_index(ukdl_text, "### Hard Rules")
    lines = ukdl_text.splitlines()
    gex_para_idx = None
    for i, l in enumerate(lines):
        if l.startswith("GEX44 run"):
            gex_para_idx = i
            break
    if gex_para_idx is None or idx_hr is None or gex_para_idx >= idx_hr:
        problems.append("UKDL missing 'GEX44 run' paragraph before ### Hard Rules")
    else:
        para = "\n".join(lines[gex_para_idx:idx_hr])
        verdict_tokens = []
        for n in range(1, 5):
            ev_n_text = _read(root / EVIDENCE_PATHS[n]) or ""
            vl = key_line(ev_n_text, VERDICT_KEYS[n])
            if vl:
                verdict_tokens.append(vl.split(":", 1)[1].strip().split()[0])
        for tok in verdict_tokens:
            if tok not in para:
                problems.append(f"UKDL GEX44 paragraph missing verdict token {tok}")
        if "RESUMPTION" not in para:
            problems.append("UKDL GEX44 paragraph missing RESUMPTION pointer")

    entries = ukdl_entries(ukdl_text)
    gate_v, gate_r = derive_gates(root)
    expected = set()
    for eid, spec in NEW_UKDL.items():
        g = spec["gate"]
        write = (g == "ALWAYS" or (g == "VERIFICATION" and gate_v == "WRITE")
                 or (g == "REVIEW_CR01" and gate_r == "WRITE"))
        if write:
            expected.add(eid)
    present_new = set(entries.keys()) - set(ORIG_UKDL_IDS)
    if present_new != expected:
        problems.append(f"UKDL new id set mismatch: present={sorted(present_new)} "
                         f"expected={sorted(expected)}")

    if "T-ONE-CALL-1H-CACHE-WRITE-001" in entries and \
            "GEX44" not in entries["T-ONE-CALL-1H-CACHE-WRITE-001"]:
        problems.append("T-ONE-CALL-1H-CACHE-WRITE-001 missing GEX44 sentence")

    if _heading_count(ev5_text, "## 3. UKDL changes") < 1:
        problems.append("EVIDENCE.md missing '## 3. UKDL changes'")
    if _heading_count(ev5_text, "## 4. Hand-back") < 1:
        problems.append("EVIDENCE.md missing '## 4. Hand-back'")
    upe = key_line(ev5_text, "ukdl_phase4_entries")
    expected_upe = "WRITTEN" if gate_v == "WRITE" else "HELD"
    if not upe or expected_upe not in upe:
        problems.append("EVIDENCE.md ukdl_phase4_entries mismatch")
    fcr = key_line(ev5_text, "ff_check_rc")
    if fcr != "ff_check_rc: 0":
        problems.append("EVIDENCE.md ff_check_rc not 0")
    return problems


def _stage4_checks(root, res_text, ukdl_text, ev5_text) -> list:
    problems = []
    if _heading_count(ev5_text, "## 5. Final status") < 1:
        problems.append("EVIDENCE.md missing '## 5. Final status'")
    fs = key_line(ev5_text, "final_status")
    if not fs:
        problems.append("EVIDENCE.md missing final_status")
    cro05 = key_line(ev5_text, "cro05")
    if not cro05:
        problems.append("EVIDENCE.md missing cro05")
    else:
        val = cro05.split(":", 1)[1].strip()
        fcr = key_line(ev5_text, "ff_check_rc")
        ff_ok = fcr == "ff_check_rc: 0"
        fs_val = fs.split(":", 1)[1].strip() if fs else ""
        status_ok = fs_val.startswith("CLEAN") or fs_val.startswith("TRACKING_ONLY")
        if val.startswith("SATISFIED") and not (ff_ok and status_ok):
            problems.append("EVIDENCE.md cro05 SATISFIED but preconditions not met")
    return problems


def check_content(root: Path, stage: int) -> list:
    problems = []
    res_text = _read(root / RES_REL)
    ukdl_text = _read(root / UKDL_REL)
    ev5_text = _read(root / EVIDENCE_FILE)
    if res_text is None:
        return ["RESUMPTION.md missing"]
    if ukdl_text is None:
        return ["UKDL missing"]
    if ev5_text is None:
        return ["phase 5 EVIDENCE.md missing"]

    problems += _stage1_checks(root, res_text, ukdl_text, ev5_text)
    if stage >= 2:
        problems += _stage2_checks(root, res_text, ukdl_text, ev5_text)
    if stage >= 3:
        problems += _stage3_checks(root, res_text, ukdl_text, ev5_text)
    if stage >= 4:
        problems += _stage4_checks(root, res_text, ukdl_text, ev5_text)
    return problems


# ---------------------------------------------------------------------------
# hashes mode
# ---------------------------------------------------------------------------

def hashes_check(root: Path, stage: int, revs) -> list:
    problems = []
    res_text = _read(root / RES_REL) or ""
    ukdl_text = _read(root / UKDL_REL) or ""
    ev5_text = _read(root / EVIDENCE_FILE) or ""
    combined = res_text + "\n" + ukdl_text + "\n" + ev5_text
    candidates = _backticked_hash_candidates(combined)
    unresolved = resolve(candidates, revs)
    if unresolved:
        problems.append(f"unresolved hashes: {sorted(set(unresolved))}")

    entries = ukdl_entries(ukdl_text)
    for eid in NEW_UKDL:
        if eid in entries:
            cands = _backticked_hash_candidates(entries[eid])
            unresolved_here = set(resolve(cands, revs))
            hex_cands = [c for c in cands if re.search(r"[a-fA-F]", c)]
            if hex_cands and len(unresolved_here) == len(hex_cands):
                problems.append(f"{eid} has no resolving hash")

    if stage >= 2:
        summary_commits = parse_summary_commits(root)
        sec2c = section(res_text, "## 2c. Sealed on GEX44") or ""
        for c in summary_commits:
            if f"`{c}`" not in sec2c:
                problems.append(f"summary commit missing from RES 2c: {c}")
        review_fix_commits = parse_review_fix_commits(root)
        for c in review_fix_commits:
            if f"`{c}`" not in sec2c:
                problems.append(f"review fix commit missing from RES 2c: {c}")

    return problems


# ---------------------------------------------------------------------------
# preserve mode
# ---------------------------------------------------------------------------

def preserve_check(root: Path, which: str, stage: int, orig_text: str) -> list:
    problems = []
    path = RES_REL if which == "res" else UKDL_REL
    new_text = _read(root / path) or ""
    lost = lost_tokens(orig_text, new_text)
    if lost:
        preview = lost[:20]
        problems.append(f"lost tokens ({len(lost)}): {preview}")
    if which == "res":
        sec1 = section(orig_text, "## 1. Identity")
        if sec1:
            for line in sec1.splitlines():
                if line.strip() == "":
                    continue
                if line not in new_text:
                    problems.append(f"section 1 line missing verbatim: {line!r}")
    if stage >= 2:
        lits = LAPTOP_LITERALS["res" if which == "res" else "ukdl"]
        unl = unlabelled(new_text, lits)
        if unl:
            problems.append(f"unlabelled laptop lines ({len(unl)}): {unl[:3]}")
        if which == "ukdl":
            entries = ukdl_entries(new_text)
            missing = [i for i in ORIG_UKDL_IDS if i not in entries]
            if missing:
                problems.append(f"original UKDL ids missing: {missing}")
    return problems


# ---------------------------------------------------------------------------
# Fixture builders (selftest only)
# ---------------------------------------------------------------------------

_FIXTURE_RES = """# Fixture RESUMPTION

## 1. Identity
Line one of identity.
Line two of identity.

## 1a. GEX44 hand-back (fixture)
Hand-back: {ff_cmd}
Or fetch: {fetch_cmd}
Base cd4e436, worktree .claude/worktrees/cro-gex44, branch mission/cognitive-resource-os-gex44.

## 2. Sealed
- `deadbeef1` sealed thing GEX44
- `10299f8` (this commit) sealed thing GEX44

## 2a. Who owns what
notes here.

## 2b. Owner decisions pending
01-02 needs Owner answer.

## 2c. Sealed on GEX44 (branch mission/cognitive-resource-os-gex44)
- Phase 1: gate evidence GEX44.
- Phase 2: evidence GEX44.
- Phase 3: evidence GEX44.
- Phase 4: evidence GEX44.

## 2d. Verdicts of the GEX44 run (phases 1-4)
Lead line, GEX44.
- Phase 1 (CRO-01) -- BLOCKED gates_verdict PASS suite_verdict BLOCKED `{e1}` verification: passed GEX44 no figures here
- Phase 2 (CRO-02) -- MEASURED `{e2}` verification: passed GEX44 no figures here
- Phase 3 (CRO-03) -- PASS via claudeMdExcludes mechanism, `{e3}` verification: passed GEX44, zero model calls
- Phase 4 (CRO-04) -- UNJUDGED rule_fired R8 `{e4}` verification: passed GEX44 no figures here

## 2e. Open follow-ups from the GEX44 run
Excludes cro-p04-ab-armA and cro-p04-ab-armB. MEASURED_ZERO sessions noted. See `10299f8`.

## 3. Active decisions
stuff here.

## 4. Next three actions
1. do X, cites `{e1}`.
2. do Y, cites `{e2}`.
3. do Z, cites `{e4}`.

## 4a. Previous next actions (laptop, fixture)
DEFERRED by Owner 2026-09-27 for reasons.

## 5. Start instruction
Fetch (section 1a) then act.
"""

_FIXTURE_UKDL = """# Fixture UKDL

### Hard Rules

**`HR-COST-OBSERVED-001`** -- desc.

### Process Rules

**`PR-PRICING-PROVENANCE-001`** -- desc.
**`PR-TRANSCRIPT-DEDUPE-001`** -- desc.
**`PR-SPLIT-BY-ENTRYPOINT-001`** -- desc.

### Traps

**`T-PROJECT-KEY-PARTIAL-SANITIZE-001`** -- desc.
**`T-ONCE-PER-SESSION-PREFIX-001`** -- desc.
**`T-ONE-CALL-1H-CACHE-WRITE-001`** -- desc, not yet measured.
**`T-KNOWLEDGE-CORPUS-AUTOFEED-001`** -- desc.
**`T-RULE-EXCLUSION-SCOPE-001`** -- GEX44 finding, see `{ev3}` for detail.
"""

_FIXTURE_EV5 = """# Phase 05 EVIDENCE fixture

## 0. Pre-checks
head_before: {head_before}
base_commit: cd4e436
model_calls: 0

## 1. Inputs
p1_evidence: {e1}
p1_verdict_line: phase_verdict: BLOCKED
p1_verification: passed
p1_review: absent
p2_evidence: {e2}
p2_verdict_line: phase_verdict: MEASURED
p2_verification: passed
p2_review: absent
p3_evidence: {e3}
p3_verdict_line: p0_verdict: PASS (--settings claudeMdExcludes)
p3_verification: passed
p3_review: absent
p4_evidence: {e4}
p4_verdict_line: verdict: UNJUDGED (similar-reuse-variance-not-observed)
p4_verification: passed
p4_review: absent
p4_gate_verification: WRITE
p4_gate_review_cr01: HOLD
"""


def _build_fixture(root: Path) -> None:
    ev_texts = {
        1: "phase_verdict: BLOCKED\ngates_verdict: PASS\nsuite_verdict: BLOCKED\n",
        2: "phase_verdict: MEASURED\n",
        3: "p0_verdict: PASS (--settings claudeMdExcludes)\n",
        4: "verdict: UNJUDGED (similar-reuse-variance-not-observed)\nrule_fired: R8\n",
    }
    for n in range(1, 5):
        p = root / EVIDENCE_PATHS[n]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(ev_texts[n], encoding="utf-8")
        v = root / VERIFICATION_PATHS[n]
        v.write_text("---\nstatus: passed\n---\n# doc\n", encoding="utf-8")

    res_path = root / RES_REL
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text(
        _FIXTURE_RES.format(
            ff_cmd=FF_COMMAND, fetch_cmd=FETCH_COMMAND,
            e1=EVIDENCE_PATHS[1], e2=EVIDENCE_PATHS[2],
            e3=EVIDENCE_PATHS[3], e4=EVIDENCE_PATHS[4],
        ), encoding="utf-8")

    ukdl_path = root / UKDL_REL
    ukdl_path.parent.mkdir(parents=True, exist_ok=True)
    ukdl_path.write_text(_FIXTURE_UKDL.format(ev3=EVIDENCE_PATHS[3]), encoding="utf-8")

    ev5_path = root / EVIDENCE_FILE
    ev5_path.parent.mkdir(parents=True, exist_ok=True)
    ev5_path.write_text(
        _FIXTURE_EV5.format(
            head_before="a" * 40,
            e1=EVIDENCE_PATHS[1], e2=EVIDENCE_PATHS[2],
            e3=EVIDENCE_PATHS[3], e4=EVIDENCE_PATHS[4],
        ), encoding="utf-8")


def _build_gate_fixture(root: Path, verification4_status: str, extra_entries=()) -> None:
    _build_fixture(root)
    (root / VERIFICATION_PATHS[4]).write_text(
        f"---\nstatus: {verification4_status}\n---\n# doc\n", encoding="utf-8")
    gate_v, _gate_r = derive_gates(root)

    res_path = root / RES_REL
    res_text = res_path.read_text(encoding="utf-8")
    old_snippet = f"R8 `{EVIDENCE_PATHS[4]}` verification: passed GEX44"
    new_snippet = f"R8 `{EVIDENCE_PATHS[4]}` verification: {verification4_status} GEX44"
    res_text = res_text.replace(old_snippet, new_snippet)
    res_path.write_text(res_text, encoding="utf-8")

    if "T-TRUTHY-PRESENCE-GUARD-001" in extra_entries:
        (root / REVIEW_PATHS[4]).write_text("### CR-01: env_check bug\n", encoding="utf-8")

    lines = ["### Hard Rules", "", "**`HR-COST-OBSERVED-001`** -- desc.", "",
              "### Process Rules", ""]
    for eid in ("PR-PRICING-PROVENANCE-001", "PR-TRANSCRIPT-DEDUPE-001",
                "PR-SPLIT-BY-ENTRYPOINT-001"):
        lines.append(f"**`{eid}`** -- desc.")
    if "PR-OWNER-GATE-BEFORE-RUN-001" in NEW_UKDL:
        cited = " ".join(f"`{EVIDENCE_PATHS[p]}`"
                          for p in NEW_UKDL["PR-OWNER-GATE-BEFORE-RUN-001"]["phases"])
        lines.append(f"**`PR-OWNER-GATE-BEFORE-RUN-001`** -- GEX44 finding citing {cited}.")
    lines += ["", "### Traps", ""]
    for eid in ("T-PROJECT-KEY-PARTIAL-SANITIZE-001", "T-ONCE-PER-SESSION-PREFIX-001",
                "T-ONE-CALL-1H-CACHE-WRITE-001", "T-KNOWLEDGE-CORPUS-AUTOFEED-001"):
        if eid == "T-ONE-CALL-1H-CACHE-WRITE-001":
            lines.append(f"**`{eid}`** -- desc, not yet measured. GEX44 fixture note.")
        else:
            lines.append(f"**`{eid}`** -- desc.")
    for eid in ("T-RULE-EXCLUSION-SCOPE-001", "T-BASELINE-WITHOUT-HOST-001",
                "T-MEASURER-IN-CORPUS-001"):
        cited = " ".join(f"`{EVIDENCE_PATHS[p]}`" for p in NEW_UKDL[eid]["phases"])
        lines.append(f"**`{eid}`** -- GEX44 finding citing {cited}.")
    for eid in extra_entries:
        spec = NEW_UKDL.get(eid)
        if spec:
            cited_paths = [EVIDENCE_PATHS[p] for p in spec["phases"]] + spec["extra_paths"]
            cited = " ".join(f"`{p}`" for p in cited_paths)
        else:
            cited = f"`{EVIDENCE_PATHS[4]}`"
        lines.append(f"**`{eid}`** -- GEX44 test entry citing {cited}.")
    ukdl_body = "\n".join(lines) + "\n"

    verdict_tokens = []
    for n in range(1, 5):
        text_n = (root / EVIDENCE_PATHS[n]).read_text(encoding="utf-8")
        vl = key_line(text_n, VERDICT_KEYS[n])
        verdict_tokens.append(vl.split(":", 1)[1].strip().split()[0])
    gex_para = (f"GEX44 run 2026-09-28 (fixture): verdicts "
                f"{' '.join(verdict_tokens)}. See RESUMPTION section 2d.\n\n")
    ukdl_text = "# Fixture UKDL\n\n" + gex_para + ukdl_body
    (root / UKDL_REL).write_text(ukdl_text, encoding="utf-8")

    ev5_path = root / EVIDENCE_FILE
    ev5_text = ev5_path.read_text(encoding="utf-8")
    ev5_text = ev5_text.replace("p4_verification: passed",
                                 f"p4_verification: {verification4_status}")
    ev5_text = ev5_text.replace("p4_gate_verification: WRITE",
                                 f"p4_gate_verification: {gate_v}")
    expected_upe = "WRITTEN" if gate_v == "WRITE" else "HELD"
    ev5_text += (f"\n## 2. RESUMPTION changes\nnotes recorded here\n\n"
                 f"## 3. UKDL changes\nukdl_phase4_entries: {expected_upe}\n\n"
                 f"## 4. Hand-back\nff_check_rc: 0\n")
    ev5_path.write_text(ev5_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Selftest (S0-S8)
# ---------------------------------------------------------------------------

def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  [PASS] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  [FAIL] {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def selftest() -> int:
    global passes, fails
    passes = fails = 0
    _ensure_importable()

    # S0: import safety -- a bare `import seal_check` in a fresh subprocess must not
    # print or sys.exit.
    proc = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, {str(HERE)!r}); import seal_check"],
        capture_output=True, text=True, timeout=30)
    s0 = proc.returncode == 0 and proc.stdout == "" and proc.stderr == ""
    check("S0", s0, f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")

    # S1: lost_tokens
    orig = "alpha beta gamma\ndelta epsilon"
    new_insert = "alpha zeta beta gamma\ndelta epsilon\nomega"
    new_moved = "delta epsilon\nalpha beta gamma"
    new_deleted = "alpha gamma\ndelta epsilon"
    s1 = (lost_tokens(orig, new_insert) == []
          and lost_tokens(orig, new_moved) == []
          and lost_tokens(orig, new_deleted) == ["beta"])
    check("S1", s1, f"ins={lost_tokens(orig, new_insert)} moved={lost_tokens(orig, new_moved)} "
                     f"del={lost_tokens(orig, new_deleted)}")

    # S2: unlabelled
    lits = ["97 sessions"]
    text_bad = "GEX44 saw 97 sessions today.\nOther line."
    text_good = "GEX44 saw 97 sessions (laptop) today.\nOther line."
    unl_bad = unlabelled(text_bad, lits)
    unl_good = unlabelled(text_good, lits)
    s2 = (len(unl_bad) == 1 and unl_good == [])
    check("S2", s2, f"bad={unl_bad} good={unl_good}")

    # S3: figures
    s3_text = ("Reuse 99.96% and $17.44 were observed. See `25/25 ignored` here. "
               "The real pass line reads 25/25 today. Timestamp 2026-09-28T14:41:42Z recorded.")
    figs = figures(s3_text)
    s3 = ("99.96%" in figs and "$17.44" in figs and figs.count("25/25") == 1)
    check("S3", s3, f"{figs}")

    # S4: resolve
    revs = ["abc1234def5678900000000000000000000000",
            "1234567890abcdef1234567890abcdef12345678"]
    tokens = ["abc1234", "deadbee", "1234567"]
    unresolved = resolve(tokens, revs)
    s4 = unresolved == ["deadbee"]
    check("S4", s4, f"{unresolved}")

    # S5: check_content on fixture (positive + 3 negative mutations)
    with tempfile.TemporaryDirectory() as td0:
        root0 = Path(td0)
        _build_fixture(root0)
        clean_problems = check_content(root0, 1)
    with tempfile.TemporaryDirectory() as td1:
        root1 = Path(td1)
        _build_fixture(root1)
        res_path = root1 / RES_REL
        text = res_path.read_text(encoding="utf-8")
        text = text.replace("zero model calls", "zero model calls and 42.7% coverage")
        res_path.write_text(text, encoding="utf-8")
        figure_problems = check_content(root1, 1)
    with tempfile.TemporaryDirectory() as td2:
        root2 = Path(td2)
        _build_fixture(root2)
        ev5_path = root2 / EVIDENCE_FILE
        text = ev5_path.read_text(encoding="utf-8")
        text = text.replace(
            "p3_verdict_line: p0_verdict: PASS (--settings claudeMdExcludes)",
            "p3_verdict_line: p0_verdict: FAIL (--settings claudeMdExcludes)")
        ev5_path.write_text(text, encoding="utf-8")
        verdict_problems = check_content(root2, 1)
    with tempfile.TemporaryDirectory() as td3:
        root3 = Path(td3)
        _build_fixture(root3)
        res_path = root3 / RES_REL
        text = res_path.read_text(encoding="utf-8")
        text = text.replace(f"`{EVIDENCE_PATHS[3]}` ", "")
        res_path.write_text(text, encoding="utf-8")
        evpath_problems = check_content(root3, 1)
    s5 = (clean_problems == [] and figure_problems != [] and verdict_problems != []
          and evpath_problems != [])
    check("S5", s5, f"clean={clean_problems} fig={figure_problems} "
                     f"verdict={verdict_problems} evpath={evpath_problems}")

    # S6: UKDL gating
    with tempfile.TemporaryDirectory() as tdg1:
        rootg1 = Path(tdg1)
        _build_gate_fixture(rootg1, "gaps_found", extra_entries=["T-BACK-TO-BACK-REUSE-001"])
        present_fail = check_content(rootg1, 3)
    with tempfile.TemporaryDirectory() as tdg2:
        rootg2 = Path(tdg2)
        _build_gate_fixture(rootg2, "gaps_found", extra_entries=())
        absent_pass = check_content(rootg2, 3)
    with tempfile.TemporaryDirectory() as tdg3:
        rootg3 = Path(tdg3)
        _build_gate_fixture(rootg3, "passed", extra_entries=["T-INVENTED-001"])
        invented_fail = check_content(rootg3, 3)
    s6 = (present_fail != [] and absent_pass == [] and invented_fail != [])
    check("S6", s6, f"present_fail={present_fail} absent_pass={absent_pass} "
                     f"invented_fail={invented_fail}")

    # S7: classify_status
    base_lines = [BRANCH_HEADER] + [f"?? {p}" for p in ALLOWED_UNTRACKED]
    porcelain_clean = "\n".join(base_lines) + "\n"
    r_clean = classify_status(porcelain_clean)
    porcelain_tracking = porcelain_clean + f" M {TRACKING[1]}\n"
    r_tracking = classify_status(porcelain_tracking)
    porcelain_dirty = porcelain_clean + "?? vault/x.md\n"
    r_dirty = classify_status(porcelain_dirty)
    porcelain_upstream = ("## mission/cognitive-resource-os-gex44..."
                           "origin/mission/cognitive-resource-os-gex44\n")
    r_upstream = classify_status(porcelain_upstream)
    porcelain_noheader = "M some/file\n"
    r_noheader = classify_status(porcelain_noheader)
    s7 = (r_clean[0] == "CLEAN" and r_tracking[0] == "TRACKING_ONLY"
          and r_dirty[0] == "DIRTY" and r_upstream[0] == "FAIL" and r_noheader[0] == "FAIL")
    check("S7", s7, f"{r_clean[0]} {r_tracking[0]} {r_dirty[0]} {r_upstream[0]} {r_noheader[0]}")

    # S8: privacy
    uuid_text = "session 123e4567-e89b-12d3-a456-426614174000 found"
    path_text = "dir .claude/projects/-weird exists"
    email_text = "contact jacobo@costaluzlawyers.es for details"
    slop_text = "This feature is a placeholder for now"
    clean_text = "GEX44 measured 30.0% first-call shared share this week."
    s8 = (len(privacy(uuid_text)) > 0 and len(privacy(path_text)) > 0
          and len(privacy(email_text)) > 0 and len(privacy(slop_text)) > 0
          and privacy(clean_text) == [])
    check("S8", s8, f"uuid={bool(privacy(uuid_text))} path={bool(privacy(path_text))} "
                     f"email={bool(privacy(email_text))} slop={bool(privacy(slop_text))} "
                     f"clean={privacy(clean_text)}")

    print(f"SEALCHK_SELFTEST_PASS={passes}/{passes + fails}  "
          f"threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _stage_arg(rest) -> int:
    if "--stage" in rest:
        i = rest.index("--stage")
        try:
            return int(rest[i + 1])
        except (IndexError, ValueError):
            return 1
    return 1


def _emit(mode, problems) -> int:
    if problems:
        print(f"{mode} FAIL: " + "; ".join(problems))
        return 1
    print(f"{mode} OK")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("content FAIL: no mode given")
        return 1
    if argv[0] == "--selftest":
        return selftest()
    _ensure_importable()
    mode = argv[0]
    rest = argv[1:]

    if mode == "content":
        stage = _stage_arg(rest)
        return _emit("content", check_content(ROOT, stage))

    if mode == "hashes":
        stage = _stage_arg(rest)
        data = sys.stdin.read()
        if not data.strip():
            print("hashes FAIL: no input on stdin")
            return 1
        revs = [l.strip() for l in data.splitlines() if l.strip()]
        return _emit("hashes", hashes_check(ROOT, stage, revs))

    if mode == "preserve":
        if not rest:
            print("preserve FAIL: missing which (res|ukdl)")
            return 1
        which = rest[0]
        stage = _stage_arg(rest[1:])
        data = sys.stdin.read()
        if not data.strip():
            print("preserve FAIL: no input on stdin")
            return 1
        return _emit("preserve", preserve_check(ROOT, which, stage, data))

    if mode == "status":
        data = sys.stdin.read()
        if not data.strip():
            print("status FAIL: no input on stdin")
            return 1
        kind, payload = classify_status(data)
        if kind == "FAIL":
            print(f"status FAIL: {payload}")
            return 1
        if kind == "CLEAN":
            print("final_status: CLEAN")
            return 0
        if kind == "TRACKING_ONLY":
            print(f"final_status: TRACKING_ONLY ({'; '.join(payload)})")
            return 0
        print(f"final_status: DIRTY ({'; '.join(payload)})")
        return 1

    print(f"content FAIL: unknown mode {mode!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
