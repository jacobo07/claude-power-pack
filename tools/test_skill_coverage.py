#!/usr/bin/env python
"""test_skill_coverage.py -- pillar D gate (skill-capability, SC-D, decision D-01).

    python3 tools/test_skill_coverage.py                       # check (default mode)
    python3 tools/test_skill_coverage.py --write-evidence      # render D-coverage.md, then check
    python3 tools/test_skill_coverage.py --dispatcher PATH     # evaluate with that dispatcher text (red entrance)
    python3 tools/test_skill_coverage.py --recording PATH      # evaluate with that live recording (red entrance)

Default mode reads only repo files, and the COMMITTED blobs at HEAD of the live recordings (evidence/D-live-*.json)
and of evidence/D-coverage.md (review WR-04: an uncommitted copy is INCONCLUSIVE, never read): no home-directory
read, no network; git is read-only. So the CE verifier can re-run it at `--final` on another host. The skill population of
every plane is discovered (tools/skill_coverage.py); a coverage class is derived from the dispatcher registrations
and the adapter source, a criticality class from plane-labelled evidence. Nothing is typed per skill except the two
positive controls below, which exist to prove the derivation can find a known answer.

Output lines: `  ok   V-SKC-X <evidence>` / `  FAIL V-SKC-X <diag>` / `  INCONCLUSIVE V-SKC-X <why>`, last line
`SKC_PASS=<passed>/<total>`. Exit codes: 0 all ok, 1 FAIL or INCONCLUSIVE, 2 could not run. A plane whose population
could not be read is INCONCLUSIVE and is never classified as all `none`: UNMEASURED is not a pass.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_coverage as sc  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402 -- committed-blob reads (review WR-04)

REPO = sc.REPO
SELF_REL = "tools/test_skill_coverage.py"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/D-coverage.md"
# Measured `skills/*/SKILL.md` count at plan time (2026-10-03). Raising it is allowed; lowering needs a stated reason.
REPO_FLOOR = 24
CONTROLS = {
    "concurrent-writers-shared-tree": "opportunity_detector",
    "destructive-state-authorization": "card",
}
CRIT_CONTROLS = (("repo", "motion-promo", "medium"), ("gex44", "destructive-state-authorization", "high"))
REC_KEYS = ("schema", "host", "node", "measured_at", "command", "skills", "counts", "evidence")


# ------------------------------------------------------------------ recordings


def load_recording(path: Path):
    """(record, None) or (None, reason) from a file (the --recording red entrance and the drills)."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        return None, f"{Path(path).name}: unreadable ({exc})"
    return load_recording_bytes(raw, Path(path).name)


def load_recording_bytes(raw: bytes, name: str):
    """(record, None) or (None, reason). Bytes go through the same CRLF normalization before json.loads."""
    try:
        d = json.loads(sc.lf(raw.decode("utf-8", errors="replace")))
    except ValueError as exc:
        return None, f"{name}: unreadable ({exc})"
    path = Path(name)
    if not isinstance(d, dict):
        return None, f"{Path(path).name}: not an object"
    miss = [k for k in REC_KEYS if k not in d]
    if miss:
        return None, f"{Path(path).name}: missing fields {miss}"
    if d["schema"] != sc.LIVE_SCHEMA:
        return None, f"{Path(path).name}: schema {d['schema']!r} != {sc.LIVE_SCHEMA!r}"
    if not isinstance(d["skills"], list) or not d["skills"]:
        return None, f"{Path(path).name}: empty skills list (UNMEASURED, not zero skills)"
    if not isinstance(d["counts"], dict) or not isinstance(d["evidence"], list):
        return None, f"{Path(path).name}: counts or evidence malformed"
    return d, None


def discover_recordings(repo: Path = REPO) -> list:
    """[(record | None, reason | None, name)] for every D-live-*.json, read as COMMITTED blobs at HEAD (review
    WR-04). A recording edited in the working tree, or written and never committed, is refused as uncommitted."""
    repo = Path(repo)
    glob = f"{sc.EVIDENCE_DIR_REL}/D-live-*.json"
    tracked, why = smd.tracked_paths(repo, "HEAD")
    if tracked is None:
        return [(None, f"cannot list HEAD: {why}", "D-live-*.json")]
    import fnmatch
    rels = {p for p in tracked if fnmatch.fnmatch(p, glob)} | {p.relative_to(repo).as_posix() for p in repo.glob(glob)}
    out = []
    for rel in sorted(rels):
        name = rel.rsplit("/", 1)[-1]
        if rel not in tracked:
            out.append((None, f"{name}: uncommitted recording, not in HEAD", name))
            continue
        raw, why = smd.committed_bytes(repo, rel)
        out.append(((None, f"{name}: {why}") if raw is None else load_recording_bytes(raw, name)) + (name,))
    return out


def committed_recording(name="D-live-gex44.json"):
    """(raw LF bytes, None) of a committed recording, or (None, reason)."""
    raw, why = smd.committed_bytes(REPO, f"{sc.EVIDENCE_DIR_REL}/{name}")
    return (None, why) if raw is None else (raw.replace(b"\r\n", b"\n"), None)


# ------------------------------------------------------------------ planes


def compute(repo, disp_text, recs, hook_texts=None, adapter_texts=None):
    """Planes: repo first, then one per recording. Each is {plane, names, rows} or {plane, inconclusive}."""
    cards = sc.discover_cards(repo, disp_text, hook_texts=hook_texts)
    adapters = sc.opportunity_adapters(repo, adapter_texts)
    heat = sc.heat_map_names(repo)
    names = sc.repo_population(repo)
    planes = [{"plane": "repo", "names": names, "rec": None,
               "rows": sc.classify_plane(names, "repo", cards, adapters, sc.repo_evidence(repo, names), heat)}]
    for rec, why, label in recs:
        if rec is None:
            planes.append({"plane": label, "inconclusive": why})
            continue
        evidence = sc.repo_evidence(repo, rec["skills"]) + [e for e in rec["evidence"] if e.get("plane") == rec["host"]]
        planes.append({"plane": rec["host"], "names": sorted(rec["skills"]), "rec": rec,
                       "rows": sc.classify_plane(rec["skills"], rec["host"], cards, adapters, evidence, heat)})
    return planes


def by_skill(plane):
    return {r["skill"]: r for r in plane["rows"]}


def counts(rows, key, vocab):
    c = Counter(r[key] for r in rows)
    return ", ".join(f"{v} {c.get(v, 0)}" for v in vocab)


def crosstab(rows):
    lines = ["| criticality \\ coverage | " + " | ".join(sc.COVERAGE_CLASSES) + " |",
             "|---|" + "---|" * len(sc.COVERAGE_CLASSES)]
    for crit in sc.CRIT_CLASSES:
        cells = [str(sum(1 for r in rows if r["criticality"] == crit and r["coverage"] == cv))
                 for cv in sc.COVERAGE_CLASSES]
        lines.append(f"| {crit} | " + " | ".join(cells) + " |")
    return lines


# ------------------------------------------------------------------ evidence


def evidence_current(raw: bytes, rendered: str) -> bool:
    """One definition of `current`: CRLF, then lone CR, turned into LF before the byte compare (a clone with
    core.autocrlf=true hands evidence/*.md back CRLF; it is not `-text` in .gitattributes)."""
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n") == rendered.encode("utf-8")


def frozen_rule() -> str:
    d = json.loads(sc.read_lf(REPO / LEDGER_REL))
    return next(p["rule"] for p in d["frozen"]["pillars"] if p["id"] == "D")


def render(planes) -> str:
    L = ["# [D] coverage + criticality -- evidence", "",
         "Frozen rule (ledger pillar D): " + frozen_rule(), "",
         "## Rules", "",
         "- Coverage rule: `card` = a PreToolUse hook registered in a `*-chain` of `hooks/hook-dispatcher.js` CHAIN_MAP "
         "whose source emits a deny (`permissionDecision` and `deny`) and names the skill as a backticked token "
         "followed by the word skill. `opportunity_detector` = card AND a `tools/*.py` adapter declaring "
         "`KIND = \"capability_opportunity\"` and `CAPABILITY = \"<skill>\"`. `none` otherwise. No class is typed "
         "per skill.",
         "- Criticality rule: " + sc.CRITICALITY_RULE,
         "- Precedence: coverage and criticality are independent columns; a skill carries exactly one of each.",
         "- heat_map: membership of the skill in `vault/skills_heat_map.json` (keyword suggestion by the "
         "skill-heat-map advisor). It is reported as a column and is never a coverage class: a keyword suggestion "
         "is neither a need-time opportunity judgement nor a deny card. `UNMEASURED` = the file could not be read.",
         "- The coverage class is a property of this checkout's dispatcher. Whether a host runs that dispatcher is "
         "the pillar A live-sync item, not measured here.", "",
         "## Planes", "",
         "Planes are reported separately; no figure sums across planes.", ""]
    for p in planes:
        if "inconclusive" in p:
            L.append(f"- plane {p['plane']}: INCONCLUSIVE -- {p['inconclusive']}")
        elif p["rec"] is None:
            L.append(f"- plane repo: {len(p['rows'])} skills, discovered from `skills/*/SKILL.md`")
        else:
            r = p["rec"]
            L.append(f"- plane {r['host']}: {len(p['rows'])} skills, recorded live; node {r['node']}, "
                     f"measured_at {r['measured_at']}, command: {r['command']}")
            L.append("  counts: " + ", ".join(f"{k} {v}" for k, v in sorted(r["counts"].items())))
            if "non_skill_dirs" in r:
                L.append(f"  non_skill_dirs (no SKILL.md; reported, never classified): "
                         f"{', '.join(r['non_skill_dirs']) or '(none)'}")
    L.append("")
    for p in planes:
        if "inconclusive" in p:
            continue
        rows = p["rows"]
        L += [f"## Plane {p['plane']}", "",
              f"Coverage: {counts(rows, 'coverage', sc.COVERAGE_CLASSES)}. "
              f"Criticality: {counts(rows, 'criticality', sc.CRIT_CLASSES)}.", ""]
        L += crosstab(rows)
        hn = [r["skill"] for r in rows if r["criticality"] == "high" and r["coverage"] == "none"]
        L += ["", f"High criticality, coverage none ({len(hn)}): " + (", ".join(hn) if hn else "(none)"), "",
              "| skill | coverage | coverage evidence | criticality | criticality evidence | heat_map |",
              "|---|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {r['skill']} | {r['coverage']} | {'; '.join(r['coverage_evidence'])} | {r['criticality']} "
                     f"| {'; '.join(r['criticality_evidence'])} | {r['heat_map']} |")
        L.append("")
    L += ["## Commands", "",
          "command: python3 tools/test_skill_coverage.py   (check; `python` on the laptop)",
          "command: python3 tools/test_skill_coverage.py --write-evidence   (render this file)",
          "command: python3 tools/skill_coverage.py --measure-live --host <label>   (record a live plane; reads that "
          "host's home directory)", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ clauses


def c_population(planes):
    r = planes[0]
    names = r["names"]
    bad = []
    if not names or len(names) < REPO_FLOOR:
        bad.append(f"repo count {len(names)} < floor {REPO_FLOOR}")
    if len(set(names)) != len(names):
        bad.append("repo names not unique")
    parts, inc = [f"repo {len(names)} (floor {REPO_FLOOR})"], []
    for p in planes[1:]:
        if "inconclusive" in p:
            inc.append(f"plane {p['plane']}: {p['inconclusive']}")
            continue
        n, want = len(p["names"]), p["rec"]["counts"].get("skill_dirs")
        if n <= 0 or n < REPO_FLOOR or n != want:
            bad.append(f"plane {p['plane']} count {n}, floor {REPO_FLOOR}, counts.skill_dirs {want}")
        parts.append(f"{p['plane']} {n}")
    if bad:
        return "FAIL", "; ".join(bad)
    if inc:
        return "INCONCLUSIVE", "; ".join(inc)
    return "ok", "planes (never summed): " + ", ".join(parts)


def c_registrations(disp_text):
    regs = sc.registered_hooks(disp_text)
    pre = {rel: [r for r in v if r["chain"].startswith("PreToolUse-")] for rel, v in regs.items()}
    pre = {k: v for k, v in pre.items() if v}
    per_chain = Counter(r["chain"] for v in regs.values() for r in v)
    missing = [rel for rel in pre if not (REPO / rel).is_file()]
    if not pre:
        return "FAIL", "no registered PreToolUse script found (the parser found nothing)"
    if missing:
        return "FAIL", f"registered but absent on disk: {missing}"
    return "ok", f"{len(pre)} PreToolUse scripts exist; per chain: " + ", ".join(
        f"{k} {v}" for k, v in sorted(per_chain.items()))


def c_positive_control(planes):
    rows = by_skill(planes[0])
    bad, ok = [], []
    for name, want in CONTROLS.items():
        got = rows.get(name, {}).get("coverage")
        if got != want:
            bad.append(f"{name}: {got!r} != {want!r}")
        else:
            ok.append(f"{name} = {got} [{'; '.join(rows[name]['coverage_evidence'])}]")
    return ("FAIL", "; ".join(bad)) if bad else ("ok", " | ".join(ok))


def c_class_total(planes):
    """Review IN-01: on its own this check cannot fail (classify_plane emits one row per name from closed literals),
    so it also drives two mutants that must be caught: an invented class, and a dropped row."""
    bad = _class_total_bad(planes)
    inv = copy.deepcopy(planes[:1])
    inv[0]["rows"][0]["coverage"] = "invented"
    drop = copy.deepcopy(planes[:1])
    drop[0]["rows"].pop()
    caught = (bool(_class_total_bad(inv)), bool(_class_total_bad(drop)))
    if caught != (True, True):
        bad.append(f"mutants not caught (invented class, dropped row) = {caught}")
    return ("FAIL", "; ".join(bad)) if bad else ("ok", "every skill on every plane has one coverage and one "
                                                       "criticality class; invented-class and dropped-row mutants "
                                                       "caught")


def _class_total_bad(planes):
    bad = []
    for p in planes:
        if "inconclusive" in p:
            continue
        rows = p["rows"]
        for r in rows:
            if r["coverage"] not in sc.COVERAGE_CLASSES or r["criticality"] not in sc.CRIT_CLASSES:
                bad.append(f"{p['plane']}/{r['skill']}: {r['coverage']}/{r['criticality']}")
        if sum(Counter(r["coverage"] for r in rows).values()) != len(p["names"]) or len(rows) != len(p["names"]):
            bad.append(f"plane {p['plane']}: class counts do not sum to the population")
    return bad


def c_evidence_current(planes):
    raw, why = evidence_bytes()
    if raw is None:
        return "INCONCLUSIVE", f"{why} (run --write-evidence and commit it)"
    dirty, why = uncommitted_sources(planes)
    if dirty is None:
        return "INCONCLUSIVE", f"cannot check the render's sources against HEAD: {why}"
    if dirty:
        return "INCONCLUSIVE", f"render sources differ from HEAD: {dirty[:5]}"
    if not evidence_current(raw, render(planes)):
        return "FAIL", f"{EVIDENCE_REL} is not the current render (run --write-evidence)"
    return "ok", f"{EVIDENCE_REL} (committed) equals the render of committed sources (line endings normalized)"


def c_evidence_drill(planes):
    text = render(planes)
    crlf = text.replace("\n", "\r\n").encode("utf-8")
    pos = next((i for i, ch in enumerate(text) if ch.isdigit()), None)
    if pos is None:
        return "FAIL", "render holds no digit to mutate"
    mutated = text[:pos] + str((int(text[pos]) + 1) % 10) + text[pos + 1:]
    got = (evidence_current(text.encode("utf-8"), text), evidence_current(crlf, text),
           evidence_current(mutated.encode("utf-8"), text))
    if got == (True, True, False):
        return "ok", "control ok, CRLF copy ok, one-digit change FAIL"
    return "FAIL", f"(control, crlf, mutated) = {got}, want (True, True, False)"


def crlf(text: str) -> str:
    return text.replace("\n", "\r\n")


def c_crlf_controls(disp_text):
    cards = sc.discover_cards(REPO, disp_text)
    hooks = {c["hook"]: sc.read_lf(REPO / c["hook"]) for c in cards}
    adapters = sc.opportunity_adapters(REPO)
    atexts = {f: sc.read_lf(REPO / f) for f, _ in adapters.values()}
    d2 = crlf(disp_text)
    if "\r\n" not in d2 or any("\r\n" not in crlf(t) for t in list(hooks.values()) + list(atexts.values())):
        return "FAIL", "control: the CRLF copies do not carry CR"
    per_lf = Counter(r["chain"] for v in sc.registered_hooks(disp_text).values() for r in v)
    per_cr = Counter(r["chain"] for v in sc.registered_hooks(d2).values() for r in v)
    planes = compute(REPO, d2, [], {k: crlf(v) for k, v in hooks.items()}, {k: crlf(v) for k, v in atexts.items()})
    rows = by_skill(planes[0])
    got = {n: rows.get(n, {}).get("coverage") for n in CONTROLS}
    if per_lf != per_cr or got != CONTROLS:
        return "FAIL", f"chains {dict(per_cr)} vs {dict(per_lf)}; controls {got}"
    return "ok", f"CRLF dispatcher/hooks/adapter: {sum(per_cr.values())} registrations, controls {got}"


def drop_script_line(text: str, rel: str):
    """(text without the registration line of rel, number of lines removed)."""
    keep, n = [], 0
    for ln in sc.lf(text).split("\n"):
        if "script:" in ln and rel in ln:
            n += 1
            continue
        keep.append(ln)
    return "\n".join(keep), n


def live_plane(planes, host="gex44"):
    return next((p for p in planes if p.get("plane") == host and "rows" in p), None)


def c_criticality_rule(planes):
    out, bad = [], []
    for plane, name, want in CRIT_CONTROLS:
        p = next((q for q in planes if q["plane"] == plane and "rows" in q), None)
        if p is None:
            return "INCONCLUSIVE", f"plane {plane} not available for control {name}"
        r = by_skill(p).get(name)
        if r is None or r["criticality"] != want or not r["criticality_evidence"]:
            bad.append(f"{plane}/{name}: {r and r['criticality']!r} want {want!r}")
        else:
            out.append(f"{plane}/{name} = {want} [{'; '.join(r['criticality_evidence'])}]")
    if "rule_stub" not in " ".join(by_skill(live_plane(planes))["destructive-state-authorization"]["criticality_evidence"]):
        bad.append("gex44 destructive-state-authorization is not high via rule_stub")
    empty = next((r for r in planes[0]["rows"] if not r["criticality_evidence"]), None)
    if empty is None or empty["criticality"] != "low":
        bad.append(f"no-evidence repo skill is not low: {empty and empty['skill']}")
    else:
        out.append(f"repo/{empty['skill']} (no evidence) = low")
    return ("FAIL", "; ".join(bad)) if bad else ("ok", " | ".join(out))


def cov_of(planes, plane, name):
    return by_skill(next(p for p in planes if p["plane"] == plane))[name]["coverage"]


def c_drill_detector(disp_text, recs):
    mut, n = drop_script_line(disp_text, "hooks/doctrine_cards.js")
    name = "concurrent-writers-shared-tree"
    ctl = cov_of(compute(REPO, disp_text, []), "repo", name)
    got = cov_of(compute(REPO, mut, []), "repo", name)
    if n and ctl == "opportunity_detector" and got == "none":
        return "ok", f"{n} registration line removed: {name} {ctl} -> {got}"
    return "FAIL", f"removed {n}; control {ctl}; mutated {got} (want opportunity_detector -> none)"


def c_drill_adapter(disp_text, recs):
    name = "concurrent-writers-shared-tree"
    f, _ = sc.opportunity_adapters(REPO)[name]
    text = sc.read_lf(REPO / f)
    kept = [ln for ln in text.split("\n") if not ln.startswith("CAPABILITY")]
    removed = len(text.split("\n")) - len(kept)
    got = cov_of(compute(REPO, disp_text, [], None, {f: "\n".join(kept)}), "repo", name)
    ctl = cov_of(compute(REPO, disp_text, []), "repo", name)
    if removed and ctl == "opportunity_detector" and got == "card":
        return "ok", f"{removed} CAPABILITY line removed from {f}: {name} {ctl} -> {got}"
    return "FAIL", f"removed {removed}; control {ctl}; mutated {got} (want opportunity_detector -> card)"


def c_drill_card(disp_text, recs):
    mut, n = drop_script_line(disp_text, "hooks/destructive_doctrine_card.js")
    name = "destructive-state-authorization"
    ctl = cov_of(compute(REPO, disp_text, []), "repo", name)
    got = cov_of(compute(REPO, mut, []), "repo", name)
    if n and ctl == "card" and got == "none":
        return "ok", f"{n} registration line removed: {name} {ctl} -> {got}"
    return "FAIL", f"removed {n}; control {ctl}; mutated {got} (want card -> none)"


def c_drill_stubs(disp_text, recs):
    name = "destructive-state-authorization"
    rec = next((r for r, _, _ in recs if r and r["host"] == "gex44"), None)
    if rec is None:
        return "INCONCLUSIVE", "no gex44 recording to drop stubs from"
    mut = copy.deepcopy(rec)
    mut["evidence"] = [e for e in mut["evidence"] if e["kind"] != "rule_stub"]
    ctl = by_skill(live_plane(compute(REPO, disp_text, [(rec, None, "gex44")])))[name]["criticality"]
    got = by_skill(live_plane(compute(REPO, disp_text, [(mut, None, "gex44")])))[name]["criticality"]
    if ctl == "high" and got != "high":
        return "ok", f"rule_stub items dropped from the gex44 recording: {name} {ctl} -> {got}"
    return "FAIL", f"control {ctl}; mutated {got} (want high -> not high)"


SYN_DISP = "const CHAIN_MAP = {\n  '%s': [\n    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/x.js', timeoutMs: 1 },\n  ],\n};\n"
SYN_DENY = "emit({ permissionDecision: 'deny' }); // Full rule: the `xs` skill.\n"


def c_synthetic(disp_text, recs):
    bad, ok = [], []
    # (a) hard_rule path, both sources, each with a control
    a1 = sc.criticality("skx", sc.repo_evidence(REPO, {"skx"}, "## HARD RULES (sealed)\nuse `skx` here\n\n## Notes\n", ""))
    a1c = sc.criticality("skx", sc.repo_evidence(REPO, {"skx"}, "## HARD RULES (sealed)\n\n## Notes\nuse `skx` here\n", ""))
    a2 = sc.criticality("skx", sc.repo_evidence(REPO, {"skx"}, "", "see skills/skx/ here\n"))
    a2c = sc.criticality("skx", sc.repo_evidence(REPO, {"skx"}, "", "nothing here\n"))
    for tag, got, want, extra in (("a1", a1, "high", "hard_rule@repo"), ("a1-control", a1c, "low", ""),
                                  ("a2", a2, "high", "hard_rule@repo"), ("a2-control", a2c, "low", "")):
        if got[0] != want or (extra and not any(extra in e for e in got[1])):
            bad.append(f"{tag}: {got}")
    ok.append("a hard_rule -> high (+ Notes-section control low)")
    # (b) non-deny hook
    hooks = {"hooks/x.js": "// names the `xs` skill but never denies\n"}
    nd = sc.coverage("xs", sc.discover_cards(REPO, SYN_DISP % "PreToolUse-Bash-chain", hook_texts=hooks), {})[0]
    dn = sc.coverage("xs", sc.discover_cards(REPO, SYN_DISP % "PreToolUse-Bash-chain",
                                             hook_texts={"hooks/x.js": SYN_DENY}), {})[0]
    if (nd, dn) != ("none", "card"):
        bad.append(f"b: non-deny {nd}, deny control {dn}")
    ok.append("b non-deny hook -> none (deny control card)")
    # (c) non-PreToolUse chain
    st = sc.coverage("xs", sc.discover_cards(REPO, SYN_DISP % "Stop-chain", hook_texts={"hooks/x.js": SYN_DENY}), {})[0]
    pt = sc.coverage("xs", sc.discover_cards(REPO, SYN_DISP % "PreToolUse-Bash-chain",
                                             hook_texts={"hooks/x.js": SYN_DENY}), {})[0]
    if (st, pt) != ("none", "card"):
        bad.append(f"c: Stop-chain {st}, PreToolUse control {pt}")
    ok.append("c Stop-chain registration -> none (PreToolUse control card)")
    # (d) cross-plane
    rec1 = {"host": "p1", "skills": ["s"], "counts": {}, "evidence": [
        {"kind": "rule_stub", "plane": "p1", "file": "~/r.md", "line": 3, "skill": "s"}]}
    rec2 = {"host": "p2", "skills": ["s"], "counts": {}, "evidence": []}
    pl = compute(REPO, disp_text, [(rec1, None, "p1"), (rec2, None, "p2")])
    r1, r2 = by_skill(pl[1])["s"], by_skill(pl[2])["s"]
    if (r1["criticality"], r2["criticality"]) != ("high", "low") or r2["criticality_evidence"] \
            or not r1["criticality_evidence"]:
        bad.append(f"d: p1 {r1['criticality']} {r1['criticality_evidence']}, p2 {r2['criticality']} {r2['criticality_evidence']}")
    ok.append("d p1 stub -> high on p1, low on p2, p1 item absent from p2")
    return ("FAIL", "; ".join(bad)) if bad else ("ok", "; ".join(ok))


def with_recording_text(raw: bytes, mutate=None):
    """Load a recording from bytes through a temporary file; (record, reason)."""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "D-live-copy.json"
        f.write_bytes(raw)
        return load_recording(f)


def c_recording_crlf(disp_text, recs):
    """Parse robustness only, and it says so (review WR-02). JSON treats CR as insignificant whitespace and the
    recording holds no multi-line string, so a CRLF re-encoding parses to the same object with or without
    `read_lf`: this clause cannot prove the normalization and does not claim to. The CR-significant pole of this
    gate is a raw-bytes compare, V-SKC-EVIDENCE-DRILL (the rendered .md). The clause asserts that boundary: the raw
    CRLF bytes parsed WITHOUT normalization equal the LF parse; if a recording ever carries CR inside a value, that
    assertion goes red and normalization has become load-bearing here."""
    raw, why = committed_recording()
    if raw is None:
        return "INCONCLUSIVE", f"no committed gex44 recording: {why}"
    cr = raw.replace(b"\n", b"\r\n")
    base, w0 = with_recording_text(raw)
    crl, w1 = with_recording_text(cr)
    d = json.loads(raw)
    d["skills"][0] += "-altered"
    alt, w2 = with_recording_text(json.dumps(d).encode("utf-8"))
    if w0 or w1 or w2 or b"\r\n" not in cr:
        has_cr = b"\r\n" in cr
        return "FAIL", f"load reasons {w0} {w1} {w2}; CR present {has_cr}"
    insignificant = json.loads(cr.decode("utf-8")) == json.loads(raw.decode("utf-8"))
    rows = [live_plane(compute(REPO, disp_text, [(r, None, "gex44")]))["rows"] for r in (base, crl, alt)]
    if rows[0] == rows[1] and rows[0] != rows[2] and insignificant:
        return "ok", (f"CRLF copy loads and classifies identically ({len(rows[0])} rows; parse robustness, CR is "
                      f"insignificant to JSON, the CR pole is V-SKC-EVIDENCE-DRILL); an altered skill name changes "
                      f"the rows")
    return "FAIL", (f"crlf same {rows[0] == rows[1]}; altered differs {rows[0] != rows[2]}; CR insignificant to "
                    f"the raw parse {insignificant}")


def c_unmeasured(disp_text, recs):
    raw, why = committed_recording()
    if raw is None:
        return "INCONCLUSIVE", f"no committed gex44 recording: {why}"
    d = json.loads(raw)
    d["skills"] = []
    rec, why = with_recording_text(json.dumps(d).encode("utf-8"))
    pl = compute(REPO, disp_text, [(rec, why, "gex44")])
    p = pl[1]
    d2 = json.loads(raw)
    d2["schema"] = "other/9"
    rec2, why2 = with_recording_text(json.dumps(d2).encode("utf-8"))
    if rec is None and "inconclusive" in p and "rows" not in p and rec2 is None and why2:
        return "ok", f"empty skills -> INCONCLUSIVE ({why}); schema mismatch -> INCONCLUSIVE; no rows, never all none"
    return "FAIL", f"rec {rec is not None}, plane {sorted(p)}, schema-mismatch {rec2 is not None}"


def evidence_bytes(repo=REPO):
    """(bytes, None) or (None, reason) of the rendered evidence file as committed at HEAD (review WR-04)."""
    return smd.committed_bytes(repo, EVIDENCE_REL)


def uncommitted_sources(planes):
    """Paths the render reads from the working tree that differ from HEAD (git status). The classification sources
    stay working-tree reads; a dirty one makes EVIDENCE-CURRENT INCONCLUSIVE rather than judging the committed
    evidence against an uncommitted world. Returns (paths, None) or (None, reason)."""
    cards = sc.discover_cards(REPO)
    paths = sorted({sc.DISPATCHER_REL, sc.CLAUDE_MD_REL, sc.HARD_RULES_REL, sc.HEAT_REL, "skills"}
                   | {c["hook"] for c in cards} | {f for f, _ in sc.opportunity_adapters(REPO).values()})
    out, why = smd.git_run(REPO, "status", "--porcelain", "-z", "--", *paths)
    if out is None:
        return None, why
    return sorted({e[3:].decode("utf-8", "surrogateescape") for e in out.split(b"\0") if len(e) > 3}), None


def c_committed_records(disp_text, recs):
    """Review WR-04: the live recordings and the rendered evidence this gate judges are the COMMITTED blobs. A
    recording edited in the working tree, or written and never committed, and a re-rendered evidence file that was
    never committed, are INCONCLUSIVE ("uncommitted"), never read."""
    import subprocess
    try:
        exe = smd.vgm._git_exe()
    except FileNotFoundError as exc:
        return "INCONCLUSIVE", f"git unavailable: {exc}"
    raw, why = committed_recording()
    if raw is None:
        return "INCONCLUSIVE", f"no committed gex44 recording: {why}"
    base = json.loads(raw)
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)

        def git(*a):
            subprocess.run([exe, "-C", str(repo), "-c", "user.name=gate", "-c", "user.email=gate@invalid", *a],
                           check=True, capture_output=True, timeout=30)
        ev = repo / sc.EVIDENCE_DIR_REL
        ev.mkdir(parents=True)
        (ev / "D-live-x.json").write_text(json.dumps(base), encoding="utf-8")
        (repo / EVIDENCE_REL).write_text("# committed\n", encoding="utf-8")
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "rec")
        clean = [(lab, r is not None) for r, _, lab in discover_recordings(repo)]
        ev_clean = evidence_bytes(repo)
        edited = dict(base, host="edited")
        (ev / "D-live-x.json").write_text(json.dumps(edited), encoding="utf-8")
        (ev / "D-live-y.json").write_text(json.dumps(base), encoding="utf-8")
        (repo / EVIDENCE_REL).write_text("# re-rendered, not committed\n", encoding="utf-8")
        dirty = [(lab, r is None and "uncommitted" in str(w)) for r, w, lab in discover_recordings(repo)]
        ev_dirty = evidence_bytes(repo)
    good = (clean == [("D-live-x.json", True)] and ev_clean[0] == b"# committed\n"
            and dirty == [("D-live-x.json", True), ("D-live-y.json", True)]
            and ev_dirty[0] is None and "uncommitted" in str(ev_dirty[1]))
    if good:
        return "ok", ("clean: committed recording and evidence read; edited recording, untracked recording and "
                      "re-rendered evidence -> uncommitted, never read")
    return "FAIL", f"clean {clean} ev {ev_clean[0]!r}; dirty {dirty} ev {ev_dirty}"


def c_live_skill_definition(disp_text, recs):
    """Review WR-08: the live plane uses the repo plane's definition of a skill, a directory holding SKILL.md.
    A container or a parked directory (no SKILL.md) is reported in counts and `non_skill_dirs`, never classified."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / ".claude"
        for rel, text in (("skills/real/SKILL.md", "---\nname: real\n---\n"),
                          ("skills/container/inner/SKILL.md", "---\nname: inner\n---\n"),
                          ("skills/parked/SKILL.md.disabled", "x\n"),
                          ("rules/parked.md", "# Parked (moved to a skill)\nThe full rule is the `parked` skill.\n")):
            f = home / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
        rec = sc.measure_live("synthetic", home)
    c = rec["counts"]
    got = (rec["skills"], c.get("skill_dirs"), c.get("dirs_without_skill_md"), rec.get("non_skill_dirs"),
           [e["skill"] for e in rec["evidence"]])
    want = (["real"], 1, 2, ["container", "parked"], [])
    if got == want:
        return "ok", ("synthetic home: real (SKILL.md) classified; container and parked (no SKILL.md) reported as "
                      "non_skill_dirs, never classified, and a stub naming `parked` yields no evidence item")
    return "FAIL", f"(skills, skill_dirs, dirs_without_skill_md, non_skill_dirs, evidence skills) = {got}, want {want}"


# ------------------------------------------------------------------ run


def emit(results) -> int:
    for cid, (st, msg) in results:
        print(f"  {st:<4} {cid} {msg}")
    passed = sum(1 for _, (st, _) in results if st == "ok")
    print(f"SKC_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def clauses(disp_text, recs):
    planes = compute(REPO, disp_text, recs)
    res = [("V-SKC-POPULATION", c_population(planes)),
           ("V-SKC-REGISTRATIONS", c_registrations(disp_text)),
           ("V-SKC-POSITIVE-CONTROL", c_positive_control(planes)),
           ("V-SKC-CLASS-TOTAL", c_class_total(planes)),
           ("V-SKC-EVIDENCE-CURRENT", c_evidence_current(planes)),
           ("V-SKC-EVIDENCE-DRILL", c_evidence_drill(planes)),
           ("V-SKC-CRLF-CONTROLS", c_crlf_controls(disp_text)),
           ("V-SKC-CRITICALITY-RULE", c_criticality_rule(planes)),
           ("V-SKC-DRILL-DETECTOR-UNREGISTERED", c_drill_detector(disp_text, recs)),
           ("V-SKC-DRILL-ADAPTER-REMOVED", c_drill_adapter(disp_text, recs)),
           ("V-SKC-DRILL-CARD-UNREGISTERED", c_drill_card(disp_text, recs)),
           ("V-SKC-DRILL-STUBS-REMOVED", c_drill_stubs(disp_text, recs)),
           ("V-SKC-SYNTHETIC-PATHS", c_synthetic(disp_text, recs)),
           ("V-SKC-RECORDING-CRLF", c_recording_crlf(disp_text, recs)),
           ("V-SKC-UNMEASURED-NOT-NONE", c_unmeasured(disp_text, recs)),
           ("V-SKC-LIVE-SKILL-DEFINITION", c_live_skill_definition(disp_text, recs)),
           ("V-SKC-COMMITTED-RECORDS", c_committed_records(disp_text, recs))]
    return planes, res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write-evidence", action="store_true", help=f"render {EVIDENCE_REL}, then check")
    ap.add_argument("--dispatcher", help="evaluate with this dispatcher text instead of the repo's")
    ap.add_argument("--recording", help="evaluate with this live recording instead of the committed ones")
    args = ap.parse_args(argv)
    try:
        disp_text = sc.read_lf(Path(args.dispatcher) if args.dispatcher else REPO / sc.DISPATCHER_REL)
        recs = [load_recording(Path(args.recording)) + (Path(args.recording).name,)] if args.recording \
            else discover_recordings()
        planes = compute(REPO, disp_text, recs)
    except (OSError, ValueError) as exc:
        print(f"SKC_VERDICT=COULD_NOT_RUN {exc}")
        return 2
    if args.write_evidence:
        out = REPO / EVIDENCE_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        text = render(planes)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {EVIDENCE_REL} ({len(text)} chars)")
    _, res = clauses(disp_text, recs)
    return emit(res)


if __name__ == "__main__":
    sys.exit(main())
