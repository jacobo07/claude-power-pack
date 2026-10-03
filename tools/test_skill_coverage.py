#!/usr/bin/env python
"""test_skill_coverage.py -- pillar D gate (skill-capability, SC-D, decision D-01).

    python3 tools/test_skill_coverage.py                       # check (default mode)
    python3 tools/test_skill_coverage.py --write-evidence      # render D-coverage.md, then check
    python3 tools/test_skill_coverage.py --dispatcher PATH     # evaluate with that dispatcher text (red entrance)
    python3 tools/test_skill_coverage.py --recording PATH      # evaluate with that live recording (red entrance)

Default mode reads only repo files and the committed live recordings (evidence/D-live-*.json): no home-directory
read, no git, no network. So the CE verifier can re-run it at `--final` on another host. The skill population of
every plane is discovered (tools/skill_coverage.py); a coverage class is derived from the dispatcher registrations
and the adapter source, a criticality class from plane-labelled evidence. Nothing is typed per skill except the two
positive controls below, which exist to prove the derivation can find a known answer.

Output lines: `  ok   V-SKC-X <evidence>` / `  FAIL V-SKC-X <diag>` / `  INCONCLUSIVE V-SKC-X <why>`, last line
`SKC_PASS=<passed>/<total>`. Exit codes: 0 all ok, 1 FAIL or INCONCLUSIVE, 2 could not run. A plane whose population
could not be read is INCONCLUSIVE and is never classified as all `none`: UNMEASURED is not a pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_coverage as sc  # noqa: E402

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
REC_KEYS = ("schema", "host", "node", "measured_at", "command", "skills", "counts", "evidence")


# ------------------------------------------------------------------ recordings


def load_recording(path: Path):
    """(record, None) or (None, reason). Bytes go through the same CRLF normalization before json.loads."""
    try:
        d = json.loads(sc.read_lf(Path(path)))
    except (OSError, ValueError) as exc:
        return None, f"{Path(path).name}: unreadable ({exc})"
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
    return [load_recording(p) + (p.name,) for p in sorted((repo / sc.EVIDENCE_DIR_REL).glob("D-live-*.json"))]


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
    return ("FAIL", "; ".join(bad)) if bad else ("ok", "every skill on every plane has one coverage and one criticality class")


def c_evidence_current(planes):
    path = REPO / EVIDENCE_REL
    if not path.is_file():
        return "FAIL", f"{EVIDENCE_REL} missing (run --write-evidence)"
    if not evidence_current(path.read_bytes(), render(planes)):
        return "FAIL", f"{EVIDENCE_REL} is not the current render (run --write-evidence)"
    return "ok", f"{EVIDENCE_REL} equals the render (line endings normalized)"


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
           ("V-SKC-CRLF-CONTROLS", c_crlf_controls(disp_text))]
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
