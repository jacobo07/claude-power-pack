#!/usr/bin/env python
"""test_listing_floor_verdict.py -- pillar B verdict gate (skill-capability, SC-B, decision D-04).

    python3 tools/test_listing_floor_verdict.py                  # check (default mode)
    python3 tools/test_listing_floor_verdict.py --jsonl PATH     # verdict clauses on one jsonl only
    python3 tools/test_listing_floor_verdict.py --json           # derived figures as one JSON object
    python3 tools/test_listing_floor_verdict.py --write-evidence # render the D-LISTING measurement file

What it reads: wiki/tools/listing_floor_probe.results.jsonl (rows selected BY LABEL, never by
position or count; the probe appends, so the file grows) and the frozen D-LISTING denominator in
vault/programs/skill-capability/ledger.json (read only, never written). Nothing is typed in: the K4
verdict is recomputed from the rows `champion-startup` / `challenger-startup`.

Verdict (K4 falsification of "hide listing entries behind a gateway"):
  V-LF-TOKENS  challenger startup_tokens >= champion startup_tokens (model-visible, primary).
  V-LF-CAP     challenger listing chars >= cap - band. cap = D-LISTING.listing_chars_cap and
               band = floor(cap * CAP_BIND_FRACTION), CAP_BIND_FRACTION = 0.01. Claude's discretion
               per CONTEXT: within 1% of its cap a listing is still cap-bound; V-LF-TOKENS carries
               the falsification on its own.

Output lines: `  ok   V-LF-X <evidence>` / `  FAIL V-LF-X <diagnostic>` / `  INCONCLUSIVE V-LF-X <why>`,
last line `LF_PASS=<passed>/<total>`. Exit codes: 0 pass, 1 fail or inconclusive, 2 could not run.
INCONCLUSIVE is never a pass: a gate that could not read its source must not look green.

The planes: the rows are laptop fresh-session readings (derived from their Windows cwd); this
script's derivation is host-independent and consumes no session. GEX44 is a different install, so
nothing here is a GEX44 listing measurement.
"""
from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSONL_REL = "wiki/tools/listing_floor_probe.results.jsonl"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/B-listing-floor.md"
SELF_REL = "tools/test_listing_floor_verdict.py"

C6_REL = "vault/plans/skill-residency-program-2026-10-03.md"
KSLICE_REL = "vault/plans/skill-virtualization-k-slice-2026-10-03.md"
LESSONS_REL = "vault/lessons/2026-10-03-capped-listing-and-card-aperture.md"
PROBE_REL = "wiki/tools/listing_floor_probe.py"
# Figures that no data row yields: cited with their source, never used by the verdict.
NON_DERIVABLE = (("22 -> 50", "described plugin entries"),
                 ("87 -> 103", "described entries"),
                 ("179 -> 32", "name-only lines"))
# D-02: this plan runs no fresh session (a statement about this phase, not a measurement).
FRESH_SESSIONS_THIS_PHASE = 0

K4_LABELS = ("R2R1", "R3", "champion-startup", "challenger-startup")
CAP_BIND_FRACTION = 0.01


# --------------------------------------------------------------------------- sources


def load_rows(path) -> list:
    """Parse one JSON object per line. Raises OSError / ValueError; callers turn that into INCONCLUSIVE."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{n} is not JSON ({exc})")
    return rows


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def k4_arms(rows):
    """Select the two startup arms by label. Returns (arms, refusal); exactly one is None."""
    arms = {}
    for key, label in (("champion", "champion-startup"), ("challenger", "challenger-startup")):
        hits = [r for r in rows if isinstance(r, dict) and r.get("label") == label]
        if len(hits) != 1:
            return None, f"label {label} appears {len(hits)} times (need exactly 1)"
        row = hits[0]
        listing = row.get("listing")
        if not isinstance(listing, dict):
            return None, f"{label}: listing is not an object ({str(listing)[:60]!r})"
        if not _is_int(listing.get("chars")):
            return None, f"{label}: listing.chars is not an int"
        if not _is_int(row.get("startup_tokens")):
            return None, f"{label}: startup_tokens is not an int"
        arms[key] = row
    return arms, None


def frozen() -> dict:
    """The frozen object of the ledger. Read only."""
    return json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))["frozen"]


def band_of(cap: int) -> int:
    return int(math.floor(cap * CAP_BIND_FRACTION))


# --------------------------------------------------------------------------- provenance (git + plan texts)


def _git(*args):
    """(rc, stdout). rc 127 when git is missing. Argv list only, never a shell."""
    git = shutil.which("git")
    if not git:
        return 127, ""
    r = subprocess.run([git, "-C", str(REPO), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout


def _read_rel(rel):
    try:
        return (REPO / rel).read_text(encoding="utf-8")
    except OSError:
        return None


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _lf_sha(data: str) -> str:
    return hashlib.sha256(data.replace("\r\n", "\n").encode("utf-8")).hexdigest()


C6_RE = re.compile(r"C6 DONE: (\d+) name-only overrides.*?initial listing before \((\w+)\) vs after "
                   r"\(fresh (\w+)\): ([\d,]+) -> ([\d,]+) chars")
BOUND_RE = re.compile(r"~listing\s+size\s+\(~(\d+)k\s+tokens\),\s+minus\s+gateway\s+reads\s+"
                      r"\(~(\d+)k\s+tokens\s+each\)")
NOISE_RE = re.compile(r"noise\s+\+-(\d+(?:\.\d+)?)k")


def c6_parse(text):
    """Figures of the C6 bullet from the whitespace-collapsed plan text, or None."""
    if not text:
        return None
    m = C6_RE.search(_collapse(text))
    if not m:
        return None
    return {"overrides": int(m.group(1)), "before_session": m.group(2), "after_session": m.group(3),
            "before": int(m.group(4).replace(",", "")), "after": int(m.group(5).replace(",", "")),
            "span": f"{m.group(4)} -> {m.group(5)}"}


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def bounds_parse(ktext, ltext):
    """(bound, noise): each a dict with its value(s) and 1-based line, or None when the text is missing."""
    bound = noise = None
    if ktext:
        m = BOUND_RE.search(ktext)
        if m:
            bound = {"listing_tokens": int(m.group(1)) * 1000, "gateway_read_tokens": int(m.group(2)) * 1000,
                     "line": _line_of(ktext, m.start())}
    if ltext:
        m = NOISE_RE.search(ltext)
        if m:
            noise = {"tokens": int(round(float(m.group(1)) * 1000)), "line": _line_of(ltext, m.start())}
    return bound, noise


def _last_line(out: str):
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return lines[-1].strip() if lines else None


def aperture_probe(k4):
    """Run the probe AS COMMITTED at K4 on two synthetic listings. Returns a dict or {'error': ...}."""
    rc, src = _git("show", f"{k4}:{PROBE_REL}")
    if rc != 0:
        return {"error": f"git show {k4}:{PROBE_REL} failed (rc {rc})"}
    with tempfile.TemporaryDirectory() as td:
        pp = Path(td) / "lf_probe_k4.py"
        pp.write_text(src, encoding="utf-8")
        try:
            spec = importlib.util.spec_from_file_location("_lf_probe_k4", pp)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            def run(listing: str) -> int:
                tr = Path(td) / "t.jsonl"
                tr.write_text(json.dumps({"attachment": {"type": "skill_listing", "isInitial": True,
                                                         "content": listing}}) + "\n", encoding="utf-8")
                return mod.analyse(str(tr), [])["listing"]["entries"]
            ns = "- plug:a: d1\n- plug:b: d2\n- solo: d3\n- bare"
            ctl = "- x: d1\n- y: d2\n- z"
            return {"ns_lines": ns.count("\n- ") + 1, "ns_entries": run(ns),
                    "ctl_lines": ctl.count("\n- ") + 1, "ctl_entries": run(ctl)}
        except Exception as exc:  # the instrument failed to run: report, never guess
            return {"error": f"probe at {k4} did not run: {type(exc).__name__}: {exc}"}


@functools.lru_cache(maxsize=1)
def static() -> dict:
    """Everything the render and the provenance clauses read from git and the plan files. Immutable
    sources (K4 blob, K4 probe) plus the live plan texts; computed once per process."""
    st = {}
    rc, out = _git("log", "--diff-filter=A", "--format=%H", "--", JSONL_REL)
    st["k4_commit"] = _last_line(out) if rc == 0 else None
    k4 = st["k4_commit"]
    st["k4_blob_rows"] = st["k4_blob_sha"] = st["k4_msg"] = None
    st["aperture"] = {"error": "no K4 commit"}
    if k4:
        rc, blob = _git("show", f"{k4}:{JSONL_REL}")
        if rc == 0:
            try:
                rows = [json.loads(ln) for ln in blob.splitlines() if ln.strip()]
                st["k4_blob_rows"], st["k4_blob_sha"] = rows, _lf_sha(blob)
            except ValueError:
                pass
        rc, msg = _git("log", "-1", "--format=%B", k4)
        st["k4_msg"] = _collapse(msg) if rc == 0 else None
        st["aperture"] = aperture_probe(k4)
    st["c6_text"] = _read_rel(C6_REL)
    st["c6"] = c6_parse(st["c6_text"])
    st["c6_commit"] = None
    if st["c6"]:
        rc, out = _git("log", "-S" + st["c6"]["span"], "--format=%H", "--", C6_REL)
        st["c6_commit"] = _last_line(out) if rc == 0 else None
    st["ktext"], st["ltext"] = _read_rel(KSLICE_REL), _read_rel(LESSONS_REL)
    st["bound"], st["noise"] = bounds_parse(st["ktext"], st["ltext"])
    return st


def cited_figures(st, denoms):
    """[(figure, what, in_commit_message, lessons_line_or_None, frozen_or_None)]"""
    out = []
    lessons = (st.get("ltext") or "").splitlines()
    frozen_pr = denoms["D-LISTING"].get("plugin_refill_entries")
    for fig, what in NON_DERIVABLE:
        in_msg = bool(st.get("k4_msg")) and fig in st["k4_msg"]
        line = next((i for i, ln in enumerate(lessons, 1) if fig in ln), None)
        out.append((fig, what, in_msg, line, frozen_pr if frozen_pr == fig else None))
    return out


# --------------------------------------------------------------------------- provenance clauses


def clause_c6(c6, c6_commit, cap):
    if c6 is None:
        return "INCONCLUSIVE", f"the C6 bullet is absent or unparseable in {C6_REL}"
    if not c6_commit:
        return "INCONCLUSIVE", "the commit that introduced the C6 figures could not be derived from git"
    band = band_of(cap)
    text = (f"C6 {c6['overrides']} name-only overrides, listing {c6['before']} ({c6['before_session']}) -> "
            f"{c6['after']} ({c6['after_session']}) chars, commit {c6_commit[:8]}")
    if c6["after"] >= c6["before"] - band:
        return "ok", text + ": listing did not drop, cap still binds"
    return "FAIL", text + f": listing fell by more than the band {band}"


def clause_rows_at_k4(rows, blob_rows):
    if blob_rows is None:
        return "INCONCLUSIVE", "the jsonl blob at the K4 commit could not be read from git"
    bad = []
    for label in K4_LABELS:
        a = [r for r in rows if isinstance(r, dict) and r.get("label") == label]
        b = [r for r in blob_rows if isinstance(r, dict) and r.get("label") == label]
        if len(a) != 1 or len(b) != 1:
            bad.append(f"{label} (working {len(a)} rows, K4 blob {len(b)} rows)")
        elif a[0] != b[0]:
            bad.append(f"{label} differs from the K4 blob")
    if bad:
        return "FAIL", "K4 rows edited or missing: " + "; ".join(bad)
    return "ok", f"the {len(K4_LABELS)} K4 rows equal the jsonl blob at the K4 commit"


def clause_aperture(ap):
    if ap is None or "error" in ap:
        return "INCONCLUSIVE", (ap or {}).get("error", "no aperture result")
    text = (f"probe at K4: {ap['ns_lines']} lines (two namespaced) -> entries {ap['ns_entries']}; "
            f"non-namespaced control {ap['ctl_lines']} lines -> entries {ap['ctl_entries']}")
    if ap["ns_entries"] == ap["ns_lines"] - 1 and ap["ctl_entries"] == ap["ctl_lines"]:
        return "ok", text + ": entries/described are first-':' key counts"
    return "FAIL", text + ": the aperture does not behave as the first-':' key count"


def clause_bounds(bound, noise):
    if bound is None:
        return "INCONCLUSIVE", f"the next-hypothesis bound is absent in {KSLICE_REL}"
    if noise is None:
        return "INCONCLUSIVE", f"the stated noise is absent in {LESSONS_REL}"
    return "ok", (f"bound {bound['listing_tokens']} minus {bound['gateway_read_tokens']} per gateway read "
                  f"({KSLICE_REL} line {bound['line']}); noise +-{noise['tokens']} ({LESSONS_REL} line {noise['line']})")


def clause_cited(cited):
    miss = [f"{fig} ({'commit message' if not m else 'lessons line'})" for fig, _, m, ln, _ in cited
            if not m or ln is None]
    if miss:
        return "INCONCLUSIVE", "figure source not found: " + "; ".join(miss)
    return "ok", f"{len(cited)} non-derivable figures located in the K4 commit message and the lessons file"


# --------------------------------------------------------------------------- clauses
# every clause returns (status, text); status in ok | FAIL | INCONCLUSIVE


def clause_tokens(arms):
    champ, chall = arms["champion"]["startup_tokens"], arms["challenger"]["startup_tokens"]
    delta = chall - champ
    text = f"challenger startup_tokens {chall} vs champion {champ} (delta {delta:+d})"
    if delta >= 0:
        return "ok", text + ": not below champion"
    return "FAIL", text + ": challenger is below champion, the floor fell"


def clause_cap(arms, denoms):
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    band = band_of(cap)
    chars = arms["challenger"]["listing"]["chars"]
    gap = cap - chars
    text = f"challenger listing chars {chars}, cap {cap}, gap {gap} chars ({gap / cap * 100:.2f}% of cap), band {band}"
    if chars >= cap - band:
        return "ok", text + ": still cap-bound"
    return "FAIL", text + ": listing is meaningfully below the cap"


def clause_denom_match(arms, denoms):
    d = denoms["D-LISTING"]
    want = (("challenger chars", arms["challenger"]["listing"]["chars"], d["listing_chars_after_K4"]),
            ("champion startup_tokens", arms["champion"]["startup_tokens"], d["startup_tokens_before_K4"]),
            ("challenger startup_tokens", arms["challenger"]["startup_tokens"], d["startup_tokens_after_K4"]))
    bad = [f"{n} row {got} != frozen {exp}" for n, got, exp in want if got != exp]
    if bad:
        return "FAIL", "rows no longer equal frozen D-LISTING: " + "; ".join(bad)
    return "ok", "rows equal frozen D-LISTING (" + ", ".join(f"{n} {got}" for n, got, _ in want) + ")"


def clause_evidence_current(text, rendered):
    """text = the committed evidence file (None when absent); rendered = a fresh render()."""
    if text is None:
        return "FAIL", f"{EVIDENCE_REL} is absent: re-render with --write-evidence"
    if text.replace("\r\n", "\n") != rendered:
        return "FAIL", f"{EVIDENCE_REL} differs from a fresh render: re-render with --write-evidence"
    return "ok", f"{EVIDENCE_REL} is byte-equal to a fresh render"


def evaluate_core(rows, denoms):
    """V-LF-SOURCES, V-LF-TOKENS, V-LF-CAP. Returns (results, arms)."""
    arms, refusal = k4_arms(rows)
    if refusal:
        return [("V-LF-SOURCES", "INCONCLUSIVE", refusal),
                ("V-LF-TOKENS", "INCONCLUSIVE", "no arms"),
                ("V-LF-CAP", "INCONCLUSIVE", "no arms"),
                ("V-LF-DENOM-MATCH", "INCONCLUSIVE", "no arms")], None
    res = [("V-LF-SOURCES", "ok", "champion-startup and challenger-startup resolved, one row each")]
    res.append(("V-LF-TOKENS",) + clause_tokens(arms))
    res.append(("V-LF-CAP",) + clause_cap(arms, denoms))
    res.append(("V-LF-DENOM-MATCH",) + clause_denom_match(arms, denoms))
    return res, arms


def verdict_of(results) -> str:
    st = {n: s for n, s, _ in results}
    if "FAIL" in (st.get("V-LF-TOKENS"), st.get("V-LF-CAP")):
        return "NOT_FALSIFIED"
    if st.get("V-LF-TOKENS") == "ok" and st.get("V-LF-CAP") == "ok":
        return "FALSIFIED"
    return "INCONCLUSIVE"


# --------------------------------------------------------------------------- render


def sessions_host(arms) -> str:
    cwds = [arms[k].get("cwd") or "" for k in ("champion", "challenger")]
    return "laptop" if all(c.startswith("C:\\Users\\User\\") for c in cwds) else "host unknown"


def row_by_label(rows, label):
    hits = [r for r in rows if isinstance(r, dict) and r.get("label") == label]
    return hits[0] if len(hits) == 1 else None


def command_for(row) -> str:
    cmd = f"python wiki/tools/listing_floor_probe.py --label {row['label']}"
    if row.get("settings_file"):
        cmd += f" --settings-file {row['settings_file']}"
    if row.get("cwd"):
        cmd += f" --cwd {row['cwd']}"
    return cmd + " --prompt <not recorded in the row>"


def delta_wording(delta: int, noise: int) -> str:
    if delta < 0:
        return f"startup tokens fell by {-delta} (n=1 per arm, not a saving without a repeat)"
    if delta <= noise:
        return "no saving shown (delta inside noise)"
    return f"startup tokens rose by {delta}, above the stated noise (+-{noise}) by {delta - noise}"


def render(rows, denoms, fro, st=None) -> str:
    """Pure and deterministic: no timestamps, no host, no HEAD sha, nothing that depends on the
    total row count of the live (append-only) jsonl. The reading of the plans and lessons is live:
    editing a cited line makes V-LF-EVIDENCE-CURRENT red, re-render and re-pin state.B's sha256."""
    st = st if st is not None else static()
    results, arms = evaluate_core(rows, denoms)
    if arms is None:
        raise ValueError(results[0][2])
    need = [n for n, v in (("K4 commit", st["k4_commit"]), ("K4 blob", st["k4_blob_rows"]), ("C6 figures", st["c6"]),
                           ("C6 commit", st["c6_commit"]), ("bound", st["bound"]), ("noise", st["noise"])) if not v]
    if need:
        raise ValueError("missing provenance: " + ", ".join(need))
    d, cap = denoms["D-LISTING"], denoms["D-LISTING"]["listing_chars_cap"]
    rule = next(p["rule"] for p in fro["pillars"] if p["id"] == "B")
    k4, c6, bound, noise = st["k4_commit"][:8], st["c6"], st["bound"], st["noise"]
    ch, cl = arms["champion"], arms["challenger"]
    delta = cl["startup_tokens"] - ch["startup_tokens"]
    L = []
    L.append("# [B] listing floor -- D-LISTING measurement")
    L.append("")
    L.append(f"Planes: sessions host `{sessions_host(arms)}` (derived: both arms' `cwd` start with "
             "`C:\\Users\\User\\`); derivation host-independent (this file is rendered from committed rows by "
             f"`{SELF_REL}`, nothing typed in). Fresh sessions consumed in this phase: {FRESH_SESSIONS_THIS_PHASE}.")
    L.append("")
    L.append(f"Sources: `{JSONL_REL}` rows selected by label ({', '.join(K4_LABELS)}), pinned to the jsonl blob at "
             f"K4 commit {k4} (LF sha256 {st['k4_blob_sha']}, {len(st['k4_blob_rows'])} K4 rows); "
             f"`{C6_REL}` at commit {st['c6_commit'][:8]}; `{KSLICE_REL}`; `{LESSONS_REL}`; frozen D-LISTING "
             f"in `{LEDGER_REL}`. Frozen caveat: {d['caveat']}.")
    L.append("")
    L.append("Frozen pillar B rule (ledger, quoted):")
    L.append("")
    L.append(f"> {rule}")
    L.append("")
    L.append("## Arms (fresh-session first-call figures, one session each)")
    L.append("")
    L.append("| label | session_id | ts | cwd | settings_file | listing chars | startup_tokens |")
    L.append("|---|---|---|---|---|---|---|")
    for k in ("champion", "challenger"):
        r = arms[k]
        L.append(f"| {r['label']} | {r.get('session_id')} | {r.get('ts')} | {r.get('cwd')} | "
                 f"{r.get('settings_file')} | {r['listing']['chars']} | {r['startup_tokens']} |")
    L.append("")
    L.append("## Verdict (recomputed from the rows)")
    L.append("")
    for n, s_, t in results:
        L.append(f"- {s_} {n}: {t}")
    L.append(f"- verdict: {verdict_of(results)} (frozen cap {cap}, band {band_of(cap)})")
    L.append("")
    L.append("## Row counts and their aperture")
    L.append("")
    L.append(f"- {ch['label']}: entries {ch['listing'].get('entries')}, described {ch['listing'].get('described')}; "
             f"{cl['label']}: entries {cl['listing'].get('entries')}, described {cl['listing'].get('described')}. "
             "These are first-':' key counts of the probe, not skill counts: every `plugin:skill` line collapses "
             "into one key.")
    s_, t = clause_aperture(st["aperture"])
    L.append(f"- {s_} V-LF-ENTRIES-APERTURE: {t}")
    L.append("")
    L.append("## Figures not derivable from any data row")
    L.append("")
    for fig, what, in_msg, line, fz in cited_figures(st, denoms):
        src = f"commit {k4} message" if in_msg else f"commit {k4} message (figure not found)"
        les = f"{LESSONS_REL} line {line}" if line else f"{LESSONS_REL} (figure not found)"
        frz = f"; frozen D-LISTING.plugin_refill_entries = \"{fz}\"" if fz else ""
        L.append(f"- {what} {fig}: source {src}; {les}{frz}; not used by the verdict")
    L.append("")
    L.append("## C6 (name-only skillOverrides, laptop)")
    L.append("")
    s_, t = clause_c6(c6, st["c6_commit"], cap)
    L.append(f"- {s_} V-LF-C6: {t}")
    L.append(f"- source: `{C6_REL}` bullet `C6 DONE`, introduced by commit {st['c6_commit'][:8]}; "
             "no startup-token reading recorded for C6.")
    L.append("")
    L.append("## Economics")
    L.append("")
    L.append("- realized saving: none.")
    L.append(f"- C6 moved the initial listing {c6['after'] - c6['before']:+d} chars ({c6['before']} -> {c6['after']}).")
    L.append(f"- K4 moved startup tokens {delta:+d} ({ch['startup_tokens']} -> {cl['startup_tokens']}) against the "
             f"stated noise +-{noise['tokens']} ({LESSONS_REL} line {noise['line']}): "
             f"{delta_wording(delta, noise['tokens'])}. {d['caveat']}.")
    L.append(f"- recorded next hypothesis (`{KSLICE_REL}` line {bound['line']}, needs Owner): an UPPER BOUND of "
             f"~{bound['listing_tokens']} startup tokens per session minus ~{bound['gateway_read_tokens']} per "
             "gateway read; displacement unknown; denominator D-LISTING; never a realized saving.")
    L.append("")
    L.append("## Sessions (D-SESSIONS)")
    L.append("")
    sess = denoms["D-SESSIONS"]
    L.append(f"- K4 rows in the K4 blob: {len(st['k4_blob_rows'])}; fresh sessions consumed in this phase: "
             f"{FRESH_SESSIONS_THIS_PHASE} (D-02); listing family remaining {sess['listing_family_remaining']} of "
             f"{sess['listing_family_total']}.")
    L.append("")
    L.append("## Commands (reconstructed from row fields; prompts not recorded in the rows)")
    L.append("")
    for label in K4_LABELS:
        row = row_by_label(rows, label)
        L.append(f"command: {command_for(row)}" if row else f"- row {label} absent")
    L.append("command: python3 tools/test_listing_floor_verdict.py   (check; `python` on the laptop)")
    L.append("command: python3 tools/test_listing_floor_verdict.py --write-evidence   (render this file)")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- drills
# Each mutant must die by ITS clause, the other named clause must stay ok, and the clean case must be
# all ok (a drill that cannot pass the clean case proves nothing).


def _arms_of(rows):
    return (next(r for r in rows if r.get("label") == "champion-startup"),
            next(r for r in rows if r.get("label") == "challenger-startup"))


def _m_clean(rows, denoms):
    pass


def _m_tokens_lowered(rows, denoms):
    champ, chall = _arms_of(rows)
    chall["startup_tokens"] = champ["startup_tokens"] - 1


def _m_chars_lowered(rows, denoms):
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    _arms_of(rows)[1]["listing"]["chars"] = cap - band_of(cap) - 1


def _m_chars_boundary(rows, denoms):
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    _arms_of(rows)[1]["listing"]["chars"] = cap - band_of(cap)


def _m_unmeasured(rows, denoms):
    _arms_of(rows)[1]["listing"] = "UNMEASURED (no initial skill_listing in transcript)"


def _m_duplicate(rows, denoms):
    rows.append(copy.deepcopy(_arms_of(rows)[0]))


def _m_denom_changed(rows, denoms):
    _arms_of(rows)[1]["startup_tokens"] += 1


# (name, mutator, clause that must die, expected status, {other clause: expected status})
VERDICT_DRILLS = [
    ("clean", _m_clean, "V-LF-SOURCES", "ok",
     {"V-LF-TOKENS": "ok", "V-LF-CAP": "ok", "V-LF-DENOM-MATCH": "ok"}),
    ("tokens-lowered", _m_tokens_lowered, "V-LF-TOKENS", "FAIL", {"V-LF-CAP": "ok"}),
    ("chars-lowered", _m_chars_lowered, "V-LF-CAP", "FAIL", {"V-LF-TOKENS": "ok"}),
    ("chars-at-band-edge", _m_chars_boundary, "V-LF-CAP", "ok", {"V-LF-TOKENS": "ok"}),
    ("listing-unmeasured", _m_unmeasured, "V-LF-SOURCES", "INCONCLUSIVE", {}),
    ("duplicate-champion-row", _m_duplicate, "V-LF-SOURCES", "INCONCLUSIVE", {}),
    ("challenger-tokens-changed", _m_denom_changed, "V-LF-DENOM-MATCH", "FAIL", {"V-LF-TOKENS": "ok"}),
]


def statuses_for(rows, denoms) -> dict:
    results, _ = evaluate_core(rows, denoms)
    return {n: s for n, s, _ in results}


def drills(rows, denoms, fro, st=None) -> list:
    """Returns [(name, clause, observed, ok)]."""
    out = []
    for name, mut, clause, want, others in VERDICT_DRILLS:
        mrows = copy.deepcopy(rows)
        mut(mrows, denoms)
        got = statuses_for(mrows, denoms)
        good = got.get(clause) == want and all(got.get(c) == w for c, w in others.items())
        out.append((name, clause, got.get(clause), good))
    st = st if st is not None else static()
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    c6, c6c = st["c6"], st["c6_commit"]
    out.append(("c6-clean", "V-LF-C6", clause_c6(c6, c6c, cap)[0], clause_c6(c6, c6c, cap)[0] == "ok"))
    bad = dict(c6, after=20002)  # the text mutant "29,991 -> 20,002"
    o = clause_c6(bad, c6c, cap)[0]
    out.append(("c6-after-fell", "V-LF-C6", o, o == "FAIL"))
    stripped = (st["c6_text"] or "").replace("C6 DONE", "C6 PENDING")
    o = clause_c6(c6_parse(stripped), c6c, cap)[0]
    out.append(("c6-bullet-missing", "V-LF-C6", o, o == "INCONCLUSIVE"))
    o = clause_bounds(*bounds_parse((st["ktext"] or "").replace("minus gateway reads", "minus nothing"), st["ltext"]))[0]
    out.append(("bounds-text-missing", "V-LF-BOUNDS", o, o == "INCONCLUSIVE"))
    o = clause_bounds(*bounds_parse(st["ktext"], (st["ltext"] or "").replace("noise +-", "noise ")))[0]
    out.append(("noise-text-missing", "V-LF-BOUNDS", o, o == "INCONCLUSIVE"))
    o = clause_rows_at_k4(rows, st["k4_blob_rows"])[0]
    out.append(("rows-at-k4-clean", "V-LF-ROWS-AT-K4", o, o == "ok"))
    mrows = copy.deepcopy(rows)
    _arms_of(mrows)[1]["cost_usd"] = 9.99
    o = clause_rows_at_k4(mrows, st["k4_blob_rows"])[0]
    out.append(("rows-at-k4-cost-changed", "V-LF-ROWS-AT-K4", o, o == "FAIL"))
    o = clause_aperture({"ns_lines": 4, "ns_entries": 4, "ctl_lines": 3, "ctl_entries": 3})[0]
    out.append(("aperture-no-collapse", "V-LF-ENTRIES-APERTURE", o, o == "FAIL"))
    o = clause_aperture(st["aperture"])[0]
    out.append(("aperture-real-probe", "V-LF-ENTRIES-APERTURE", o, o == "ok"))
    base = render(rows, denoms, fro, st)
    arows = copy.deepcopy(rows)
    arows.append({"label": "plugin-gateway-champion", "startup_tokens": 1, "listing": {"chars": 1}})
    same = render(arows, denoms, fro, st) == base and verdict_of(evaluate_core(arows, denoms)[0]) == verdict_of(
        evaluate_core(rows, denoms)[0])
    out.append(("append-stability", "V-LF-EVIDENCE-CURRENT", "ok" if same else "FAIL", same))
    noise = st["noise"]["tokens"]
    for name, dd, must, mustnt in (("delta-inside-noise", 500, "no saving shown (delta inside noise)", "rose by"),
                                   ("delta-above-noise", noise + 605, "rose by", "no saving shown")):
        wrows = copy.deepcopy(rows)
        c, h = _arms_of(wrows)
        h["startup_tokens"] = c["startup_tokens"] + dd
        txt = render(wrows, denoms, fro, st)
        good = must in txt and mustnt not in txt.split("## Economics")[1]
        out.append((name, "V-LF-EVIDENCE-CURRENT", "ok" if good else "FAIL", good))
    rendered = base
    digit = next(i for i, c in enumerate(rendered) if c.isdigit())
    mutated = rendered[:digit] + str((int(rendered[digit]) + 1) % 10) + rendered[digit + 1:]
    clean = clause_evidence_current(rendered, rendered)[0]
    obs = clause_evidence_current(mutated, rendered)[0]
    out.append(("evidence-clean", "V-LF-EVIDENCE-CURRENT", clean, clean == "ok"))
    out.append(("evidence-digit-changed", "V-LF-EVIDENCE-CURRENT", obs, obs == "FAIL"))
    return out


# --------------------------------------------------------------------------- driver


def derived_json(rows, denoms, fro) -> dict:
    st = static()
    results, arms = evaluate_core(rows, denoms)
    out = {"verdict": verdict_of(results), "evidence": EVIDENCE_REL,
           "clauses": {n: s_ for n, s_, _ in results}}
    if arms is None:
        return out
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    ch, cl = arms["champion"], arms["challenger"]
    delta = cl["startup_tokens"] - ch["startup_tokens"]
    noise = (st["noise"] or {}).get("tokens")
    out.update({
        "k4_arms": {k: {"label": a["label"], "session_id": a.get("session_id"), "startup_tokens": a["startup_tokens"],
                        "listing": a["listing"]} for k, a in (("champion", ch), ("challenger", cl))},
        "deltas": {"startup_tokens": delta, "challenger_gap_to_cap_chars": cap - cl["listing"]["chars"],
                   "noise_tokens": noise,
                   "wording": delta_wording(delta, noise) if noise is not None else None},
        "cap": cap, "band": band_of(cap), "c6": st["c6"],
        "commits": {"k4": st["k4_commit"], "c6": st["c6_commit"]},
        "bound": st["bound"], "noise": st["noise"],
        "sessions": {"k4_rows_in_blob": len(st["k4_blob_rows"]) if st["k4_blob_rows"] else None,
                     "fresh_consumed_this_phase": FRESH_SESSIONS_THIS_PHASE,
                     "listing_family_remaining": denoms["D-SESSIONS"]["listing_family_remaining"],
                     "listing_family_total": denoms["D-SESSIONS"]["listing_family_total"]},
        "sessions_host": sessions_host(arms),
        "k4_blob_sha256": st["k4_blob_sha"],
    })
    return out


def emit(results) -> int:
    passed = 0
    for name, status, text in results:
        print(f"  {status:<4} {name} {text}")
        passed += status == "ok"
    print(f"LF_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def default_results(rows, denoms, fro):
    results, arms = evaluate_core(rows, denoms)
    if arms is None:
        return results
    st = static()
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    results.append(("V-LF-C6",) + clause_c6(st["c6"], st["c6_commit"], cap))
    results.append(("V-LF-ROWS-AT-K4",) + clause_rows_at_k4(rows, st["k4_blob_rows"]))
    results.append(("V-LF-ENTRIES-APERTURE",) + clause_aperture(st["aperture"]))
    results.append(("V-LF-BOUNDS",) + clause_bounds(st["bound"], st["noise"]))
    results.append(("V-LF-CITED",) + clause_cited(cited_figures(st, denoms)))
    ev = _read_rel(EVIDENCE_REL)
    try:
        rendered = render(rows, denoms, fro, st)
    except ValueError as exc:
        results.append(("V-LF-EVIDENCE-CURRENT", "INCONCLUSIVE", f"cannot render: {exc}"))
        return results
    results.append(("V-LF-EVIDENCE-CURRENT",) + clause_evidence_current(ev, rendered))
    d = drills(rows, denoms, fro, st)
    subs = "".join(f"\n    drill {n}: {c} {o}" for n, c, o, _ in d)
    if all(g for *_, g in d):
        results.append(("V-LF-DRILLS", "ok", f"{len(d)} drills, clean case all ok, each mutant died by its own clause" + subs))
    else:
        results.append(("V-LF-DRILLS", "FAIL", "a drill did not behave as required" + subs))
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--drills", action="store_true", help="print the in-process mutant drills")
    ap.add_argument("--jsonl", help="evaluate the verdict clauses on this jsonl only")
    ap.add_argument("--json", action="store_true", help="print the derived figures as JSON")
    ap.add_argument("--write-evidence", action="store_true", help=f"render {EVIDENCE_REL}")
    args = ap.parse_args(argv)
    try:
        fro = frozen()
        denoms = fro["denominators"]
        denoms["D-LISTING"]["listing_chars_cap"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"LF_VERDICT=COULD_NOT_RUN frozen ledger unreadable: {exc}")
        return 2
    path = args.jsonl or str(REPO / JSONL_REL)
    try:
        rows = load_rows(path)
    except (OSError, ValueError) as exc:
        return emit([("V-LF-SOURCES", "INCONCLUSIVE", str(exc))])
    if args.json:
        print(json.dumps(derived_json(rows, denoms, fro), indent=1, sort_keys=True))
        return 0
    if args.drills:
        d = drills(rows, denoms, fro, static())
        for name, clause, obs, good in d:
            print(f"    drill {name}: {clause} {obs}{'' if good else ' <-- WRONG'}")
        return 0 if all(g for *_, g in d) else 1
    if args.write_evidence:
        try:
            text = render(rows, denoms, fro)
        except ValueError as exc:
            print(f"cannot render: {exc}")
            return 1
        out = REPO / EVIDENCE_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {EVIDENCE_REL} ({len(text)} chars)")
        return 0
    if args.jsonl:
        results, _ = evaluate_core(rows, denoms)
        return emit(results)
    return emit(default_results(rows, denoms, fro))


if __name__ == "__main__":
    sys.exit(main())
