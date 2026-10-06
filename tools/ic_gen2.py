"""Incremental Cognition generation 2 (IC-gen2, autonomous-optimization) judge.

Reached through `python3 tools/test_incremental_cognition_program.py --generation 2 --status|--final|--selftest`.
Spec of record: vault/specs/autonomous-optimization.md. Generation 1's ledger, its `frozen` object and its
FROZEN_AT are read here only to be compared with, never written.

What it judges: vault/programs/incremental-cognition/gen2/ledger.json (pillars M reopened, O, P, Q, R). The
clauses are CE's own (tools/test_cognitive_economy_program.py L1-L9, X1-X3): they are reused, not
reimplemented (AO-01, no parallel verifier). CE reads seven module globals at call time, so every judgement
runs inside `bound()`, which snapshots those globals, points them at gen2, and restores all seven in a
`finally`. Nothing is rebound at import time, so a gen1 run of the same process is unaffected, and CE's own
selftest (which hardcodes the A-T fixtures) is never run under the gen2 binding.

On top of CE's clauses, the gen2-only rules G2-* (each killed by a mutant in `selftest`) pin what CE cannot
see: the ledger identity (G2-B1), gen1's pre-registration still equal to its pinned copy (G2-GEN1), the M
reopening quoting gen1 faithfully (G2-REOPEN), denominators and materiality equal to gen1's (G2-DENOM), the
predicted terminals and the pre-registered allowed loss of P (G2-PRED), and a READY spec (G2-SPEC).

Modes: status | final | selftest. Exit codes: 0 pass, 1 fail, 2 could not run. An unreadable or invalid
ledger is COULD_NOT_RUN, never a pass.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO))
import test_cognitive_economy_program as ce  # noqa: E402

GEN2_DIR = "vault/programs/incremental-cognition/gen2/"
LEDGER_REL = GEN2_DIR + "ledger.json"
FROZEN_AT_REL = GEN2_DIR + "FROZEN_AT"
HANDOFF_DIR = GEN2_DIR + "handoffs/"
PILLARS = ["M", "O", "P", "Q", "R"]
REQS_REL = ".planning/workstreams/autonomous-optimization/REQUIREMENTS.md"
REQ_ROW = re.compile(r"^\|\s*AOP-([MOPQR])\s*\|[^|\n]*\|([^|\n]*)\|\s*$", re.M)
SELF_REL = "tools/test_incremental_cognition_program.py"

GEN1_LEDGER_REL = "vault/programs/incremental-cognition/ledger.json"
GEN1_FROZEN_AT_REL = "vault/programs/incremental-cognition/FROZEN_AT"
PROGRAM = "incremental-cognition"
PREDICTED = "IMPLEMENTED_AND_VERIFIED"
ALLOWED_LOSS = "FALSIFIED_OR_REJECTED_BY_EVIDENCE"  # D-OQ4: P's pre-registered allowed loss

_GLOBALS = ("SELF_REL", "LEDGER_REL", "FROZEN_AT_REL", "HANDOFF_DIR", "PILLARS", "REQS_REL", "REQ_ROW")


def snapshot_bindings() -> dict:
    """The seven CE globals as they are now (REQ_ROW as its pattern string), for the restore check."""
    out = {}
    for k in _GLOBALS:
        v = getattr(ce, k)
        out[k] = v.pattern if k == "REQ_ROW" else list(v) if k == "PILLARS" else v
    return out


@contextlib.contextmanager
def bound():
    """Point the seven CE globals at generation 2 for the duration of one judgement, then restore them."""
    saved = {k: getattr(ce, k) for k in _GLOBALS}
    try:
        ce.SELF_REL, ce.LEDGER_REL, ce.FROZEN_AT_REL = SELF_REL, LEDGER_REL, FROZEN_AT_REL
        ce.HANDOFF_DIR, ce.PILLARS = HANDOFF_DIR, list(PILLARS)
        ce.REQS_REL, ce.REQ_ROW = REQS_REL, REQ_ROW
        yield
    finally:
        for k, v in saved.items():
            setattr(ce, k, v)


def load_ledger() -> dict:
    """The gen2 ledger (OSError / JSONDecodeError reach the caller)."""
    return json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))


def _frozen(led) -> dict:
    fr = led.get("frozen") if isinstance(led, dict) else None
    return fr if isinstance(fr, dict) else {}


def _canon(x) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def g2_b1(led) -> list:
    """G2-B1: the ledger is IC's, generation 2 (the ledger and its frozen object both say so)."""
    out = []
    if not isinstance(led, dict) or led.get("program") != PROGRAM:
        out.append(f"G2-B1 ledger program is {led.get('program') if isinstance(led, dict) else None!r}, not {PROGRAM!r}")
    if not isinstance(led, dict) or led.get("generation") != 2:
        out.append(f"G2-B1 ledger generation is {led.get('generation') if isinstance(led, dict) else None!r}, not 2")
    if _frozen(led).get("generation") != 2:
        out.append(f"G2-B1 frozen.generation is {_frozen(led).get('generation')!r}, not 2")
    return out


def g2_gen1(current_gen1_frozen, pinned_gen1_frozen) -> list:
    """G2-GEN1: gen1's pre-registration is byte-for-byte what it was at gen1's FROZEN_AT (this programme never edits it)."""
    if _canon(current_gen1_frozen) != _canon(pinned_gen1_frozen):
        return ["G2-GEN1 gen1 frozen differs from its copy at gen1 FROZEN_AT (the gen1 pre-registration was edited)"]
    return []


def g2_reopen(led, gen1_frozen, gen1_sha=None) -> list:
    """G2-REOPEN: reopens.M quotes gen1's M faithfully (predicted, rule, ledger path and, when known, FROZEN_AT sha)."""
    r = (_frozen(led).get("reopens") or {}).get("M") if isinstance(_frozen(led).get("reopens"), dict) else None
    if not isinstance(r, dict):
        return ["G2-REOPEN frozen.reopens.M is missing: the reopening of gen1 M is not pre-registered"]
    gm = [p for p in (gen1_frozen or {}).get("pillars", []) if p.get("id") == "M"]
    if not gm:
        return ["G2-REOPEN gen1 frozen has no pillar M to reopen"]
    out = []
    for key, want in (("gen1_predicted", gm[0].get("predicted")), ("gen1_rule", gm[0].get("rule")),
                      ("gen1_ledger", GEN1_LEDGER_REL), ("gen1_frozen_at", gen1_sha)):
        if want is None and key == "gen1_frozen_at":
            continue
        if r.get(key) != want:
            out.append(f"G2-REOPEN reopens.M.{key} does not match gen1 ({str(r.get(key))[:40]!r} vs {str(want)[:40]!r})")
    return out


def g2_denom(led, gen1_frozen) -> list:
    """G2-DENOM: denominators and materiality are gen1's, not re-chosen for gen2."""
    out = []
    for key in ("denominators", "materiality"):
        if _canon(_frozen(led).get(key)) != _canon((gen1_frozen or {}).get(key)):
            out.append(f"G2-DENOM frozen.{key} differs from gen1 frozen.{key}")
    return out


def g2_pred(led) -> list:
    """G2-PRED: every pillar predicts IMPLEMENTED_AND_VERIFIED and names its roadmap phases; P's rule carries the allowed loss."""
    out = []
    for p in _frozen(led).get("pillars") or []:
        pid = p.get("id") if isinstance(p, dict) else None
        if not isinstance(p, dict):
            out.append(f"G2-PRED a pillar entry is not an object: {p!r}")
            continue
        if p.get("predicted") != PREDICTED:
            out.append(f"G2-PRED {pid}: predicted {p.get('predicted')!r}, gen2 pre-registers {PREDICTED} for every pillar (D-OQ4)")
        ph = p.get("roadmap_phases")
        if not (isinstance(ph, list) and ph and all(isinstance(x, int) for x in ph)):
            out.append(f"G2-PRED {pid}: roadmap_phases must be a non-empty list of phase numbers, got {ph!r}")
        if pid == "P" and ALLOWED_LOSS not in str(p.get("rule")):
            out.append(f"G2-PRED P: the rule does not carry the allowed loss {ALLOWED_LOSS} (D-OQ4)")
    return out


def g2_spec(led, root) -> list:
    """G2-SPEC: frozen.spec names an existing spec that is READY at tier 3."""
    spec = _frozen(led).get("spec")
    if not isinstance(spec, str) or not spec:
        return ["G2-SPEC frozen.spec is missing"]
    path = Path(root) / spec
    if not path.is_file():
        return [f"G2-SPEC frozen.spec {spec} does not exist"]
    try:
        from modules.sdd_os.readiness import READY, assess
        r = assess(path, 3)
    except Exception as exc:  # an unjudgeable spec is a refusal, never a pass
        return [f"G2-SPEC readiness of {spec} could not be judged: {type(exc).__name__}: {exc}"]
    if r.state != READY:
        return [f"G2-SPEC {spec} is {r.state} at tier 3, missing {list(r.missing)}"]
    return []


CHAMP_DIR = GEN2_DIR + "evidence/champion/"
STEP_LINE = re.compile(r"^STEP (\S+) exit=(\d+) killed=(\S+) wall_s=(\d+) peak_rss_MB=(\d+) read_GB=([0-9.]+)\s*$", re.M)
START_LINE = re.compile(r"^START (\S+) head=(\S+) root=(\S+)(?: project_filter=(.*?))?\s*$", re.M)
CHAMP_PROVENANCE = {"run5": "reconstructed", "run6": "runner-script"}  # D-OQ5: Run 5's runner text was overwritten
CHAMP_SCALARS = ("exit", "wall_s", "peak_rss_MB", "read_GB")


def _champ_steps(summary_text: str) -> dict:
    """STEP lines of a runner summary as {id: {exit, wall_s, read_GB, peak_rss_MB}}."""
    return {m[1]: {"exit": int(m[2]), "wall_s": int(m[4]), "read_GB": float(m[6]), "peak_rss_MB": int(m[5])}
            for m in STEP_LINE.finditer(summary_text)}


def _champ_runner_argv(runner_text: str, step: str):
    """(argv, line number, problem) of the runner's `run_step <step>` line with its own $VAR assignments expanded
    and the interpreter `run_step` prepends. argv is None when the runner cannot be read this way."""
    import shlex
    env = {}
    for m in re.finditer(r"""^([A-Z][A-Z0-9_]*)=(?:'([^']*)'|"([^"]*)"|(\S+))\s*$""", runner_text, re.M):
        env[m[1]] = next(g for g in m.groups()[1:] if g is not None)
    interp = re.search(r"""^\s*(python3?)\s+"\$@"\s""", runner_text, re.M)
    if not interp:
        return None, None, "the runner has no `python3 \"$@\"` interpreter line in run_step"
    for no, line in enumerate(runner_text.splitlines(), 1):
        if re.match(rf"run_step\s+{re.escape(step)}\s", line):
            try:
                toks = shlex.split(line)[2:]
            except ValueError as exc:
                return None, no, f"the run_step {step} line does not tokenize: {exc}"
            out = []
            for t in toks:
                bad = [n for n in re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", t) if n not in env]
                if bad:
                    return None, no, f"the run_step {step} line uses {bad} that the runner never assigns"
                out.append(re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", lambda m: env[m[1]], t))
            return [interp[1]] + out, no, None
    return None, None, f"the runner has no line beginning `run_step {step}`"


def g2_champ(led, res=None) -> list:
    """G2-CHAMP: frozen.champion is re-derived from its pinned copied evidence on every run (D-OQ5). Evidence is
    read through `res` (file_text / file_sha / path_exists); a missing or unparsable file is a problem, never a skip."""
    import shlex
    res = res if res is not None else ce.Resolver()
    ch = _frozen(led).get("champion")
    if not isinstance(ch, dict):
        return ["G2-CHAMP frozen.champion is missing: the champion baseline is not pre-registered"]
    out = []
    runs = {}
    for name in ("run5", "run6"):
        r = ch.get(name)
        if not isinstance(r, dict):
            out.append(f"G2-CHAMP champion.{name} is missing")
            continue
        runs[name] = r
    for name, r in runs.items():
        cmd = r.get("command")
        if not (isinstance(cmd, str) and cmd.strip()):
            out.append(f"G2-CHAMP {name}: command is missing or empty")
        if r.get("plane") != "gex44":
            out.append(f"G2-CHAMP {name}: plane is {r.get('plane')!r}, not 'gex44'")
        if r.get("command_provenance") != CHAMP_PROVENANCE[name]:
            out.append(f"G2-CHAMP {name}: command_provenance is {r.get('command_provenance')!r}, "
                       f"must be {CHAMP_PROVENANCE[name]!r} (D-OQ5)")
        texts = {}
        ev = r.get("evidence")
        if not (isinstance(ev, list) and ev):
            out.append(f"G2-CHAMP {name}: evidence is missing")
            ev = []
        for e in ev:
            ref = e.get("ref") if isinstance(e, dict) else None
            if not (isinstance(ref, str) and ref.startswith(CHAMP_DIR)):
                out.append(f"G2-CHAMP {name}: evidence ref {ref!r} is not under {CHAMP_DIR}")
                continue
            if not res.path_exists(ref):
                out.append(f"G2-CHAMP {name}: evidence {ref} does not exist")
                continue
            got = res.file_sha(ref)
            if got != e.get("sha256"):
                out.append(f"G2-CHAMP {name}: evidence {ref} sha256 {str(got)[:12]} != pinned {str(e.get('sha256'))[:12]}")
            if e.get("source_sha256") != e.get("sha256"):
                out.append(f"G2-CHAMP {name}: evidence {ref} source_sha256 differs from sha256 (the copy is not the source)")
            texts[ref.rsplit("/", 1)[-1]] = res.file_text(ref)
        summ = next((t for k, t in texts.items() if k.endswith("summary.txt")), None)
        plog = next((t for k, t in texts.items() if k.endswith(".log")), None)
        if summ is None:
            out.append(f"G2-CHAMP {name}: no copied summary among the evidence")
        else:
            steps = _champ_steps(summ)
            row = steps.get(r.get("step"))
            if row is None:
                out.append(f"G2-CHAMP {name}: summary has no STEP line for {r.get('step')!r}")
            else:
                for k in CHAMP_SCALARS:
                    if r.get(k) != row[k]:
                        out.append(f"G2-CHAMP {name}: {k} {r.get(k)!r} != {row[k]!r} in the copied summary")
            st = START_LINE.search(summ)
            if not st:
                out.append(f"G2-CHAMP {name}: summary has no START line")
            else:
                for k, want in (("started", st[1]), ("head", st[2]), ("project_filter", st[4] if st[4] else None)):
                    if r.get(k) != want:
                        out.append(f"G2-CHAMP {name}: {k} {r.get(k)!r} != {want!r} in the copied summary START line")
                if ch.get("corpus_root") != st[3]:
                    out.append(f"G2-CHAMP corpus_root {ch.get('corpus_root')!r} != {st[3]!r} in the {name} START line")
            if name == "run6" and r.get("steps") != steps:
                out.append(f"G2-CHAMP {name}: steps {sorted(r.get('steps') or {})} differ from the copied summary's STEP lines "
                           f"{sorted(steps)} (ids or values)")
        if plog is None:
            out.append(f"G2-CHAMP {name}: no copied population log among the evidence")
        else:
            try:
                doc = json.loads(plog)
                want = {"population_match": doc["population_match"], "until_located_scans": doc["until_located"]["scans"],
                        "project_filter": doc["corpus"]["project_filter"]}
                if "population" in r:
                    want_pop = {k: doc["population"][k] for k in (r["population"] if isinstance(r["population"], dict) else {})}
                    if r["population"] != want_pop or set(r["population"]) != {"sessions_active", "calls"}:
                        out.append(f"G2-CHAMP {name}: population {r['population']!r} != {want_pop!r} in the copied log")
                for k, v in want.items():
                    if r.get(k) != v:
                        out.append(f"G2-CHAMP {name}: {k} {r.get(k)!r} != {v!r} in the copied population log")
            except (ValueError, KeyError, TypeError) as exc:
                out.append(f"G2-CHAMP {name}: the copied population log is unparsable ({type(exc).__name__}: {exc})")
        if name == "run6":
            runner = next((t for k, t in texts.items() if k.endswith(".sh")), None)
            if runner is None:
                out.append("G2-CHAMP run6: no copied runner among the evidence")
            else:
                argv, no, why = _champ_runner_argv(runner, str(r.get("step")))
                if argv is None:
                    out.append(f"G2-CHAMP run6: {why}")
                else:
                    if r.get("runner_line") != no:
                        out.append(f"G2-CHAMP run6: runner_line {r.get('runner_line')!r} != {no} in the copied runner")
                    try:
                        have = shlex.split(r.get("command") or "")
                    except ValueError:
                        have = None
                    if have != argv:
                        out.append(f"G2-CHAMP run6: command {r.get('command')!r} is not the runner's expanded argv {argv}")
    r5, r6 = runs.get("run5"), runs.get("run6")
    rd = ch.get("ratios_derived")
    if r5 and r6 and isinstance(r5.get("wall_s"), (int, float)) and isinstance(r6.get("wall_s"), (int, float)) \
            and r6["wall_s"] and r6.get("read_GB"):
        want = {"wall": round(r5["wall_s"] / r6["wall_s"], 1), "read_GB": round(r5["read_GB"] / r6["read_GB"], 1)}
        if not isinstance(rd, dict) or any(rd.get(k) != v for k, v in want.items()):
            out.append(f"G2-CHAMP ratios_derived {rd!r} != {want} recomputed from run5 / run6")
    return out


ROADMAP_REL = ".planning/workstreams/autonomous-optimization/ROADMAP.md"
FREEZE_AUDIT_REL = GEN2_DIR + "evidence/freeze-audit.md"
PLACEHOLDER = re.compile(r"(?i)\b(?:TBD|TODO|FIXME|XXX|PLACEHOLDER)\b|<[A-Za-z][^<>\n]{0,60}>")
A6_SKIP = ("materiality", "denominators", "reopens")  # copied verbatim from gen1, already pinned by G2-DENOM / G2-REOPEN
AUDIT_RECORD_LINE = re.compile(r"^ICP_GEN2_AUDIT=PASS frozen_sha256=([0-9a-f]{64})\s*$", re.M)
ROADMAP_PHASE_LINE = re.compile(r"^- \[[ xX]\] \*\*Phase (\d+):[^\n]*?\*\* - pillars? ([A-Z](?:, [A-Z])*)", re.M)


def frozen_sha256(frozen) -> str:
    """Canonical sha256 of the `frozen` object (what the freeze pins and the audit record quotes)."""
    return hashlib.sha256(json.dumps(frozen, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def expected_final_failures(frozen_at_present: bool) -> set:
    """The final-mode failure lines that are the open programme itself, no more and no fewer. The texts are CE's own
    clause strings (tools/test_cognitive_economy_program.py L2, L3, L8), not paraphrases."""
    exp = {f"L3 {pid}: no terminal disposition" for pid in PILLARS}
    if not frozen_at_present:
        exp.add("L2 not frozen: FROZEN_AT missing, the pre-registration was never committed")
    exp |= {f"L8 review {key}: missing or its file does not exist" for key in ("ukdl", "cbr")}
    exp |= {f"L8 delta {key}: empty" for key in ("product", "intelligence")}
    return exp


def roadmap_phase_map(text: str) -> dict:
    """{pillar letter: sorted phase numbers} from the ROADMAP `## Phases` checklist, phases 1..6 only."""
    out = {}
    for m in ROADMAP_PHASE_LINE.finditer(text or ""):
        n = int(m[1])
        if 1 <= n <= 6:
            for letter in re.findall(r"[A-Z]", m[2]):
                out.setdefault(letter, []).append(n)
    return {k: sorted(set(v)) for k, v in out.items()}


def _tracked_git(path: str) -> bool:
    """True when git tracks `path` (argv list, no shell)."""
    return ce._git("ls-files", "--error-unmatch", "--", path).returncode == 0


def _strings(x, path=""):
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from _strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _strings(v, f"{path}[{i}]")


def audit_rules(led, res, roadmap_text, tracked, selftest_fn) -> dict:
    """{n: (failure lines starting 'A<n> ', detail for the ok line)} for A1-A7. This is the pre-freeze gate: A3 expects
    the programme to be OPEN (no terminals yet), so it is run before FROZEN_AT, and again right after it."""
    fz = _frozen(led)
    rep = {}
    a1 = [f"A1 {x}" for x in problems(led, res, final=False)]
    rep[1] = (a1, "status problems empty (CE L1-L9/X under the gen2 binding + G2 rules)")
    rep[2] = ([] if selftest_fn() else ["A2 the gen2 selftest failed: a rule cannot be trusted to fire"],
              "gen2 selftest passes")
    with bound():
        frozen_present = res.frozen_at_commit() is not None
    actual, exp = set(problems(led, res, final=True)), expected_final_failures(frozen_present)
    a3 = [f"A3 unexpected final-mode failure: {x}" for x in sorted(actual - exp)]
    a3 += [f"A3 expected open-programme line absent from the final-mode failures: {x}" for x in sorted(exp - actual)]
    rep[3] = (a3, f"final-mode failure set equals the expected open-programme set ({len(exp)} lines, "
                  f"{'frozen' if frozen_present else 'pre-freeze'})")
    rmap = roadmap_phase_map(roadmap_text)
    a4 = []
    if not rmap:
        a4.append("A4 the ROADMAP Phases checklist yielded no pillar-to-phase map (unparsable)")
    ids = [p.get("id") for p in fz.get("pillars") or [] if isinstance(p, dict)]
    for p in fz.get("pillars") or []:
        if isinstance(p, dict) and rmap and sorted(p.get("roadmap_phases") or []) != rmap.get(p.get("id"), []):
            a4.append(f"A4 pillar {p.get('id')}: roadmap_phases {p.get('roadmap_phases')!r} != ROADMAP checklist "
                      f"{rmap.get(p.get('id'), [])}")
    a4 += [f"A4 the ROADMAP names pillar {k} in phases {v} but frozen.pillars has no {k}" for k, v in rmap.items()
           if k not in ids]
    rep[4] = (a4, "roadmap_phases equal the ROADMAP checklist: " + ", ".join(f"{k}{v}" for k, v in sorted(rmap.items())))
    owners = sorted({o for p in fz.get("pillars") or [] if isinstance(p, dict) for o in p.get("owner") or []})
    a5 = [f"A5 frozen owner {o} is not git-tracked" for o in owners if not tracked(o)]
    rep[5] = (a5, f"{len(owners)} frozen owner paths tracked")
    a6, scanned = [], 0
    for key, val in fz.items():
        if key in A6_SKIP:
            continue
        for path, s in _strings(val, key):
            scanned += 1
            m = _deferral_or_placeholder(s)
            if m:
                a6.append(f"A6 frozen.{path} carries {m!r} (a deferral word or an authoring placeholder)")
    rep[6] = (a6, f"{scanned} gen2-authored frozen strings carry no deferral word and no placeholder")
    a7, detail7 = [], "not frozen yet"
    if res.path_exists(FROZEN_AT_REL):
        detail7 = "recorded frozen_sha256 equals the live one"
        if not res.path_exists(FREEZE_AUDIT_REL):
            a7.append(f"A7 {FROZEN_AT_REL} exists but {FREEZE_AUDIT_REL} does not: the freeze has no audit record")
        else:
            recorded = set(AUDIT_RECORD_LINE.findall(res.file_text(FREEZE_AUDIT_REL)))
            live = frozen_sha256(fz)
            if len(recorded) != 1:
                a7.append(f"A7 the audit record must carry exactly one `ICP_GEN2_AUDIT=PASS frozen_sha256=<hex>` line, "
                          f"found {len(recorded)} distinct")
            elif recorded != {live}:
                a7.append(f"A7 recorded frozen_sha256 {sorted(recorded)[0][:12]} != live {live[:12]} "
                          "(frozen changed after it was audited)")
    rep[7] = (a7, detail7)
    return rep


def _deferral_or_placeholder(s: str):
    """The first deferral word or authoring placeholder in `s`, or None."""
    m = ce.DEFERRAL_PROSE.search(s) or PLACEHOLDER.search(s)
    return m.group(0) if m else None


def audit(led, res, roadmap_text, tracked=None, selftest_fn=None) -> list:
    """A1-A7 failure lines (empty = the pre-registration is cleared for the freeze). `tracked(path) -> bool` and
    `selftest_fn() -> bool` are injectable so the selftest can drive A5 without git and A2 without recursing."""
    rep = audit_rules(led, res, roadmap_text, tracked or _tracked_git,
                      selftest_fn or (lambda: selftest(verbose=False)))
    return [x for n in sorted(rep) for x in rep[n][0]]


LIFECYCLE_FORWARD = ("observed", "priced", "shadow", "canary", "certified", "promoted")
LIFECYCLE_SIDE = ("rejected", "narrowed", "superseded", "retired")
OPP_KEYS = ("id", "title", "programme", "schema_note", "plane", "scope", "workload_class", "frequency", "current_cost",
            "hypothesis", "owner_search_result", "predicted_dividend", "build_cost", "proof_cost", "carrying_cost", "risk",
            "reversibility", "champion", "challenger", "status", "lifecycle_history", "next_transition",
            "retirement_condition", "realized_dividend", "evidence")


def g2_opp(led, res=None) -> list:
    """G2-OPP: opportunity rows (top-level `opportunities`, outside `frozen`) keep the lifecycle order and never let a
    predicted dividend pass as a realized one. Evidence is re-read through `res` on every run."""
    res = res if res is not None else ce.Resolver()
    rows = led.get("opportunities") if isinstance(led, dict) else None
    if not isinstance(rows, list):
        return ["G2-OPP opportunities is missing or not a list"]
    out, seen = [], set()
    known = LIFECYCLE_FORWARD + LIFECYCLE_SIDE
    for i, o in enumerate(rows):
        if not isinstance(o, dict):
            out.append(f"G2-OPP opportunities[{i}] is not an object")
            continue
        oid = o.get("id")
        tag = f"opportunities[{i}] {oid}"
        missing = [k for k in OPP_KEYS if k not in o]
        if missing:
            out.append(f"G2-OPP {tag}: missing keys {missing}")
        if not (isinstance(oid, str) and re.fullmatch(r"OPP-\d{3}", oid)):
            out.append(f"G2-OPP {tag}: id must match OPP-NNN")
        elif oid in seen:
            out.append(f"G2-OPP {tag}: duplicate id")
        seen.add(oid)
        status, hist = o.get("status"), o.get("lifecycle_history")
        if status not in known:
            out.append(f"G2-OPP {tag}: status {status!r} is not one of {list(known)}")
        if not (isinstance(hist, list) and hist and all(isinstance(h, str) for h in hist)):
            out.append(f"G2-OPP {tag}: lifecycle_history must be a non-empty list of states")
        else:
            if hist[0] != "observed":
                out.append(f"G2-OPP {tag}: lifecycle_history starts with {hist[0]!r}, not 'observed'")
            if hist[-1] != status:
                out.append(f"G2-OPP {tag}: lifecycle_history ends with {hist[-1]!r} but status is {status!r}")
            for a, b in zip(hist, hist[1:]):
                if b not in known:
                    out.append(f"G2-OPP {tag}: lifecycle step to unknown state {b!r}")
                elif a in LIFECYCLE_SIDE and b in LIFECYCLE_FORWARD:
                    out.append(f"G2-OPP {tag}: forward step {a!r} -> {b!r} after a side state")
                elif b in LIFECYCLE_FORWARD and a in LIFECYCLE_FORWARD \
                        and LIFECYCLE_FORWARD.index(b) != LIFECYCLE_FORWARD.index(a) + 1:
                    out.append(f"G2-OPP {tag}: lifecycle step {a!r} -> {b!r} skips or repeats a state "
                               f"(order {' -> '.join(LIFECYCLE_FORWARD)})")
        real = o.get("realized_dividend")
        if real is not None:
            if status not in ("certified", "promoted", "retired"):
                out.append(f"G2-OPP {tag}: realized_dividend is set while status is {status!r} "
                           "(only certified, promoted or retired may carry one)")
            if not isinstance(real, dict):
                out.append(f"G2-OPP {tag}: realized_dividend is not an object")
            else:
                lacking = [k for k in ("value", "unit", "denominator", "measurement")
                           if real.get(k) in (None, "")]
                if lacking:
                    out.append(f"G2-OPP {tag}: realized_dividend lacks {lacking}")
                elif not res.path_exists(str(real["measurement"])):
                    out.append(f"G2-OPP {tag}: realized_dividend measurement {real['measurement']!r} does not exist")
        pred = o.get("predicted_dividend")
        if not isinstance(pred, dict) or pred.get("value") in (None, "") or pred.get("unit") in (None, ""):
            out.append(f"G2-OPP {tag}: predicted_dividend must carry value and unit")
        if re.search(r"(?i)\brealized\b", json.dumps(pred, ensure_ascii=False)):
            out.append(f"G2-OPP {tag}: predicted_dividend text says 'realized' (a prediction is never a realized dividend)")
        ev = o.get("evidence")
        if not (isinstance(ev, list) and ev):
            out.append(f"G2-OPP {tag}: evidence is missing")
            continue
        for e in ev:
            kind, ref = (e.get("kind"), e.get("ref")) if isinstance(e, dict) else (None, None)
            if kind == "file":
                if not (isinstance(ref, str) and res.path_exists(ref)):
                    out.append(f"G2-OPP {tag}: evidence file {ref!r} does not exist")
                elif res.file_sha(ref) != e.get("sha256"):
                    out.append(f"G2-OPP {tag}: evidence file {ref} sha256 {str(res.file_sha(ref))[:12]} != pinned "
                               f"{str(e.get('sha256'))[:12]}")
            elif kind == "commit":
                if not (isinstance(ref, str) and res.commit_reachable(ref)):
                    out.append(f"G2-OPP {tag}: evidence commit {ref!r} is not reachable from HEAD")
            else:
                out.append(f"G2-OPP {tag}: evidence kind {kind!r} is not 'file' or 'commit'")
    return out


def load_gen1_current():
    """Gen1's `frozen` as the working tree has it, or None when unreadable."""
    try:
        return json.loads((REPO / GEN1_LEDGER_REL).read_text(encoding="utf-8-sig"))["frozen"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def load_gen1_sha():
    try:
        return (REPO / GEN1_FROZEN_AT_REL).read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def load_gen1_pinned(sha):
    """Gen1's `frozen` as committed at its FROZEN_AT (read-only `show`), or None on any failure."""
    if not sha or not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        return None
    r = ce._git("show", f"{sha}:{GEN1_LEDGER_REL}")
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.lstrip("﻿"))["frozen"]
    except (ValueError, KeyError, TypeError):
        return None


def g2_problems(led: dict, res) -> list:
    """The gen2-only rules. Sources are read from `res` when it offers them (the selftest's fixture does)."""
    cur = getattr(res, "gen1_current", load_gen1_current)()
    sha = getattr(res, "gen1_sha", load_gen1_sha)()
    pin = getattr(res, "gen1_pinned", load_gen1_pinned)(sha)
    out = g2_b1(led)
    if cur is None:
        out.append(f"G2-GEN1 could not read gen1 frozen from {GEN1_LEDGER_REL}")
    if pin is None:
        out.append(f"G2-GEN1 could not read gen1 frozen at {sha}")
    if cur is not None and pin is not None:
        out += g2_gen1(cur, pin)
    if cur is not None:
        out += g2_reopen(led, cur, sha) + g2_denom(led, cur)
    out += g2_pred(led)
    out += g2_spec(led, getattr(res, "spec_root", REPO))
    out += g2_champ(led, res)
    out += g2_opp(led, res)
    return out


def problems(led: dict, res=None, final: bool = False) -> list:
    """CE's clauses under the gen2 binding plus the G2 rules. Empty = pass."""
    with bound():
        res = res if res is not None else ce.Resolver()
        out = ce.check_ledger(led, res, final=final, run_gates=final)
        if not final:
            out += ce.check_disposition(led, res)  # `final` already includes it
        out += g2_problems(led, res)
    return out


# ---------------------------------------------------------------- selftest
def load_text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


class Fx(ce.Resolver):
    """Fixture resolver: synthetic evidence files first, the real repo for everything else. `frozen` is what
    FROZEN_AT 'points at' (None = not frozen). The gen1 sources and the spec root are injectable. Never writes."""

    def __init__(self, frozen, files=None, gen1_cur="real", gen1_pin="real", gen1_sha="real", spec_root=REPO):
        self.frozen, self.files, self.spec_root = frozen, dict(files or {}), spec_root
        self._cur = load_gen1_current() if gen1_cur == "real" else gen1_cur
        self._pin = load_gen1_current() if gen1_pin == "real" else gen1_pin  # the pin never follows a mutated _cur
        self._sha = load_gen1_sha() if gen1_sha == "real" else gen1_sha

    # A `files` value of None HIDES that path from the real repo, so a mutant such as "FROZEN_AT without an audit
    # record" stays true after the real record has been written (found by plan 00-05: it survived once the record
    # existed on disk).
    def path_exists(self, rel):
        if rel in self.files:
            return self.files[rel] is not None
        return super().path_exists(rel)

    def file_sha(self, rel):
        return _sha(self.files[rel]) if self.files.get(rel) is not None else super().file_sha(rel)

    def file_text(self, rel):
        return self.files[rel] if self.files.get(rel) is not None else super().file_text(rel)

    def handoff_landed(self, rel):
        return True

    def frozen_at_commit(self):
        return copy.deepcopy(self.frozen)

    def gen1_current(self):
        return copy.deepcopy(self._cur)

    def gen1_sha(self):
        return self._sha

    def gen1_pinned(self, sha):
        return copy.deepcopy(self._pin)


EV_M = "ok/measurement-P.md"
EV_F = "ok/falsification-P.md"


def _p_files(names_pillar=True):
    return {EV_M: "KME-L command: python3 tools/x.py [P]\n",
            EV_F: ("falsification [P] (IC-gen2): champion vs scoped vs challenger table\n" if names_pillar
                   else "falsification of something else\n"),
            REQS_REL: "| AOP-P | KME-L challenger | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |\n"}


def _close_p(led, files, with_artifact=True, pinned=True,
             reason="the challenger did not beat the scoped path on repeated queries"):
    ev = [{"kind": "measurement", "ref": EV_M}]
    if with_artifact:
        ev.append({"kind": "falsification", "ref": EV_F})
    for e in ev:
        if pinned:
            e["sha256"] = _sha(files[e["ref"]])
    led["state"]["P"] = {"terminal": ALLOWED_LOSS, "reason": reason, "evidence": ev, "savings": []}
    return led


def _drift(frozen):
    d = copy.deepcopy(frozen)
    d["pillars"][0]["rule"] = str(d["pillars"][0].get("rule")) + " edited"
    return d


def _could_not_run_probe():
    """(exit code, printed COULD_NOT_RUN) for a ledger that is missing and for one that is not JSON."""
    global LEDGER_REL
    kept, out = LEDGER_REL, []
    try:
        for bad in (GEN2_DIR + "no-such-ledger.json", "tools/ic_gen2.py"):
            LEDGER_REL = bad
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                rc = main("final")
            out.append((rc, "COULD_NOT_RUN" in sink.getvalue()))
    finally:
        LEDGER_REL = kept
    return out


def selftest(verbose=True) -> bool:
    ok = True

    def say(good, label):
        nonlocal ok
        if not good:
            ok = False
            print(f"  FAIL {label}")
        elif verbose:
            print(f"  ok   {label}")

    real = load_ledger()

    def judge(led, frozen="own", final=False, files=None, **kw):
        fz = copy.deepcopy(led.get("frozen")) if frozen == "own" else frozen
        return problems(led, Fx(fz, files, **kw), final=final)

    def led_with(fn):
        d = copy.deepcopy(real)
        fn(d)
        return d

    def pil(d, pid):
        return [p for p in d["frozen"]["pillars"] if p["id"] == pid][0]

    clean = judge(real)
    say(not clean, f"V-IC2-CLEAN (real gen2 ledger, served as its own FROZEN_AT copy, zero problems) {clean[:2] or ''}")
    fin = judge(real, final=True)
    say(not any(x.startswith("L2") for x in fin), "V-IC2-CLEAN-FROZEN-CONTROL (final with FROZEN_AT served: no L2 line)")
    cur = load_gen1_current()
    say(cur is not None and _canon(cur) == _canon(load_gen1_pinned(load_gen1_sha())),
        "V-IC2-GEN1-LOADERS (working tree and gen1 FROZEN_AT copy read and equal)")
    say(load_gen1_pinned("0" * 40) is None and load_gen1_pinned(None) is None,
        "V-IC2-GEN1-LOADER-REFUSES (an unreadable pin is None, never a pass)")

    rows = []  # (name, expected label, problems under that mutation)

    def mut(name, label, fn, **kw):
        rows.append((name, label, judge(led_with(fn), **kw)))

    mut("program-foreign", "G2-B1", lambda d: d.update(program="skill-capability"))
    mut("generation-1", "G2-B1", lambda d: d.update(generation=1))
    mut("extra-pillar-S", "L1", lambda d: (d["frozen"]["pillars"].append(
        {"id": "S", "name": "x", "owner": [], "predicted": PREDICTED, "roadmap_phases": [1], "rule": "x"}),
        d["state"].update(S={})))
    mut("predicted-DONE", "L1", lambda d: pil(d, "M").update(predicted="DONE"))
    mut("unknown-owner", "L1", lambda d: pil(d, "M")["owner"].append("tools/does_not_exist_ic2.py"))
    mut("frozen-rule-edited", "L2", lambda d: pil(d, "O").update(rule=pil(d, "O")["rule"] + " edited"),
        frozen=copy.deepcopy(real["frozen"]))
    mut("final-without-frozen-at", "L2", lambda d: None, frozen=None, final=True)
    mut("open-pillar-final", "L3", lambda d: None, final=True)
    mut("gen1-frozen-drift", "G2-GEN1", lambda d: None, gen1_cur=_drift(cur))
    mut("gen1-frozen-unreadable", "G2-GEN1", lambda d: None, gen1_pin=None)
    mut("gen1-frozen-unreadable-now", "G2-GEN1", lambda d: None, gen1_cur=None)
    mut("reopen-misquoted", "G2-REOPEN",
        lambda d: d["frozen"]["reopens"]["M"].update(gen1_rule=d["frozen"]["reopens"]["M"]["gen1_rule"] + " x"))
    mut("reopen-predicted-misquoted", "G2-REOPEN",
        lambda d: d["frozen"]["reopens"]["M"].update(gen1_predicted=PREDICTED))
    mut("reopen-missing", "G2-REOPEN", lambda d: d["frozen"].pop("reopens"))
    mut("reopen-wrong-gen1-sha", "G2-REOPEN", lambda d: d["frozen"]["reopens"]["M"].update(gen1_frozen_at="0" * 40))
    mut("denominator-calls-changed", "G2-DENOM", lambda d: d["frozen"]["denominators"]["KME-L"].update(calls=1))
    mut("materiality-changed", "G2-DENOM", lambda d: d["frozen"]["materiality"].update(rule="a slice needs 1 %"))
    mut("Q-predicted-MERGED", "G2-PRED", lambda d: pil(d, "Q").update(predicted="MERGED_INTO_EXISTING_OWNER"))
    mut("P-rule-without-allowed-loss", "G2-PRED",
        lambda d: pil(d, "P").update(rule=pil(d, "P")["rule"].replace(ALLOWED_LOSS, "REJECTED")))
    mut("roadmap-phases-missing", "G2-PRED", lambda d: pil(d, "R").pop("roadmap_phases"))
    mut("spec-missing", "G2-SPEC", lambda d: d["frozen"].update(spec="vault/specs/does-not-exist-ic2.md"))
    mut("spec-key-absent", "G2-SPEC", lambda d: d["frozen"].pop("spec"))
    mut("spec-not-ready", "G2-SPEC", lambda d: d["frozen"].update(spec=REQS_REL))

    # G2-CHAMP: the champion numbers re-derived from the copied evidence (D-OQ5); the clean control is V-IC2-CLEAN
    def champ(d, run):
        return d["frozen"]["champion"][run]

    ref6 = CHAMP_DIR + "run6-summary.txt"
    text6 = load_text(ref6)
    mut("run5-no-command", "G2-CHAMP", lambda d: champ(d, "run5").pop("command"))
    mut("run5-provenance-verbatim", "G2-CHAMP", lambda d: champ(d, "run5").update(command_provenance="runner-script"))
    mut("run6-plane-laptop", "G2-CHAMP", lambda d: champ(d, "run6").update(plane="laptop"))
    mut("run5-read-GB-101.5", "G2-CHAMP", lambda d: champ(d, "run5").update(read_GB=101.5))
    mut("run6-step-missing", "G2-CHAMP", lambda d: champ(d, "run6")["steps"].pop("r10-l-rank"))
    mut("evidence-sha-flipped", "G2-CHAMP",
        lambda d: champ(d, "run5")["evidence"][0].update(sha256="0" * 64))
    mut("summary-text-altered", "G2-CHAMP", lambda d: None, files={ref6: text6.replace("wall_s=24 ", "wall_s=25 ", 1)})
    mut("run6-command-filter-dropped", "G2-CHAMP", lambda d: champ(d, "run6").update(
        command=champ(d, "run6")["command"].split(" --project-filter")[0]))
    mut("ratios-derived-wrong", "G2-CHAMP", lambda d: d["frozen"]["champion"]["ratios_derived"].update(wall=36.0))
    mut("champion-evidence-outside-dir", "G2-CHAMP", lambda d: champ(d, "run5")["evidence"][1].update(
        ref="vault/programs/incremental-cognition/gen2/owner-bundle.md"))
    mut("champion-missing", "G2-CHAMP", lambda d: d["frozen"].pop("champion"))

    # G2-OPP: lifecycle order and predicted-never-realized on the opportunity rows (outside `frozen`)
    def opp(d):
        return d["opportunities"][0]

    def certify(d):
        o = opp(d)
        o.update(status="certified", lifecycle_history=["observed", "priced", "shadow", "canary", "certified"],
                 realized_dividend={"value": 1, "unit": "Owner waivers avoided per default-env re-arm",
                                    "denominator": "default-env re-arms observed on the live install",
                                    "measurement": o["evidence"][0]["ref"]})

    certified = judge(led_with(certify))
    say(not certified, f"V-IC2-OPP-CERTIFIED-ACCEPTED (a row walked observed..certified with a realized dividend that "
                       f"names value, unit, denominator and measurement: no G2-OPP line) {certified[:2] or ''}")

    def with_opp(fn):
        return lambda d: fn(opp(d))

    mut("opp-realized-while-priced", "G2-OPP", with_opp(lambda o: o.update(
        realized_dividend={"value": 1, "unit": "waivers", "denominator": "re-arms", "measurement": o["evidence"][0]["ref"]})))
    mut("opp-history-skips-to-promoted", "G2-OPP", with_opp(lambda o: o.update(
        status="promoted", lifecycle_history=["observed", "promoted"])))
    mut("opp-status-done", "G2-OPP", with_opp(lambda o: o.update(status="done", lifecycle_history=["observed", "priced", "done"])))
    mut("opp-predicted-without-unit", "G2-OPP", with_opp(lambda o: o["predicted_dividend"].pop("unit")))
    mut("opp-predicted-labelled-realized", "G2-OPP", with_opp(lambda o: o["predicted_dividend"].update(
        basis="realized on the live install")))
    mut("opp-evidence-file-missing", "G2-OPP", with_opp(lambda o: o["evidence"][0].update(
        ref="vault/programs/incremental-cognition/gen2/evidence/OPP-001-does-not-exist.md")))
    mut("opp-evidence-sha-flipped", "G2-OPP", with_opp(lambda o: o["evidence"][0].update(sha256="0" * 64)))
    mut("opp-commit-unreachable", "G2-OPP", with_opp(lambda o: o["evidence"][1].update(ref="0" * 40)))
    mut("opp-duplicate-id", "G2-OPP", lambda d: d["opportunities"].append(copy.deepcopy(opp(d))))
    mut("opp-history-last-differs-from-status", "G2-OPP", with_opp(lambda o: o.update(lifecycle_history=["observed"])))
    mut("opp-history-not-starting-observed", "G2-OPP", with_opp(lambda o: o.update(lifecycle_history=["priced"])))
    mut("opp-forward-step-after-side-state", "G2-OPP", with_opp(lambda o: o.update(lifecycle_history=["observed", "rejected", "priced"])))
    mut("opp-certified-realized-missing-denominator", "G2-OPP", lambda d: (certify(d), opp(d)["realized_dividend"].pop("denominator")))
    mut("opp-key-missing", "G2-OPP", with_opp(lambda o: o.pop("retirement_condition")))

    # the bound CE clauses on a closed pillar, with the D-OQ4 allowed loss as the positive control
    f_ok = _p_files()
    allowed = judge(_close_p(copy.deepcopy(real), f_ok), files=f_ok)
    say(not allowed, f"V-IC2-ALLOWED-LOSS-ACCEPTED (P closed {ALLOWED_LOSS} with an artifact naming [P]: no "
                     f"L4/L6/L7/X line) {allowed[:2] or ''}")
    rows.append(("P-falsified-without-artifact", "L6",
                 judge(_close_p(copy.deepcopy(real), f_ok, with_artifact=False), files=f_ok)))
    f_other = _p_files(names_pillar=False)
    rows.append(("falsification-names-other-pillar", "L4", judge(_close_p(copy.deepcopy(real), f_other), files=f_other)))
    rows.append(("evidence-unpinned", "L4", judge(_close_p(copy.deepcopy(real), f_ok, pinned=False), files=f_ok)))
    rows.append(("reason-empty", "L7", judge(_close_p(copy.deepcopy(real), f_ok, reason=""), files=f_ok)))
    f_row = {**f_ok, REQS_REL: "| AOP-P | KME-L challenger | Complete -- MERGED_INTO_EXISTING_OWNER |\n"}
    rows.append(("closed-pillar-wrong-aop-row", "X2", judge(_close_p(copy.deepcopy(real), f_row), files=f_row)))
    f_norow = {**f_ok, REQS_REL: "| AOP-M | optimizer lifecycle (reopened) | Pending |\n"}
    rows.append(("closed-pillar-no-aop-row", "X2", judge(_close_p(copy.deepcopy(real), f_norow), files=f_norow)))
    # --audit A1-A7: the machine read of the pre-registration. Injected `tracked` and `selftest_fn` keep it hermetic and
    # recursion-free; the clean control and the frozen-and-matching control prove the rules do not refuse everything.
    road = load_text(ROADMAP_REL)

    def aud(led, frozen="own", files=None, roadmap=None, tracked=None, selftest_fn=None, **kw):
        fz = copy.deepcopy(led.get("frozen")) if frozen == "own" else frozen
        return audit(led, Fx(fz, files, **kw), road if roadmap is None else roadmap,
                     tracked or (lambda p: True), selftest_fn or (lambda: True))

    a_clean = aud(real)
    say(not a_clean, f"V-IC2-AUDIT-CLEAN (real ledger, injected tracked/selftest: A1-A7 empty) {a_clean[:2] or ''}")
    rec_ok = {FROZEN_AT_REL: "0" * 40 + "\n",
              FREEZE_AUDIT_REL: f"## Audit\nICP_GEN2_AUDIT=PASS frozen_sha256={frozen_sha256(real['frozen'])}\n"}
    a_frozen = aud(real, files=rec_ok)
    say(not a_frozen, f"V-IC2-AUDIT-FROZEN-RECORD-ACCEPTED (FROZEN_AT present, record sha equals live: no A line) "
                      f"{a_frozen[:2] or ''}")
    say(expected_final_failures(False) - expected_final_failures(True) ==
        {"L2 not frozen: FROZEN_AT missing, the pre-registration was never committed"}
        and len(expected_final_failures(False)) == 10,
        "V-IC2-AUDIT-EXPECTED-SET (pre-freeze set is 10 lines, post-freeze drops exactly L2)")
    rows.append(("A1-program-foreign", "A1", aud(led_with(lambda d: d.update(program="skill-capability")))))
    rows.append(("A2-selftest-red", "A2", aud(real, selftest_fn=lambda: False)))
    rows.append(("A3-closed-pillar-without-reason", "A3",
                 aud(_close_p(copy.deepcopy(real), f_ok, reason=""), files=f_ok)))
    rows.append(("A3-expected-open-line-absent", "A3",
                 aud(led_with(lambda d: d["reviews"].update(ukdl={"file": REQS_REL})))))
    rows.append(("A4-pillar-O-roadmap-phases-2", "A4", aud(led_with(lambda d: pil(d, "O").update(roadmap_phases=[2])))))
    rows.append(("A4-roadmap-unparsable", "A4", aud(real, roadmap="no checklist here")))
    rows.append(("A5-owner-not-tracked", "A5", aud(real, tracked=lambda p: p != "tools/usage_index.py")))
    rows.append(("A6-rule-contains-TBD", "A6", aud(led_with(lambda d: pil(d, "O").update(rule=pil(d, "O")["rule"] + " TBD")))))
    rows.append(("A6-rule-contains-later", "A6", aud(led_with(lambda d: pil(d, "Q").update(rule=pil(d, "Q")["rule"] + " later")))))
    rows.append(("A6-champion-note-angle-prompt", "A6", aud(led_with(
        lambda d: d["frozen"]["champion"]["run5"].update(provenance_note="see <fill in the source>")))))
    rec_bad = {FROZEN_AT_REL: "0" * 40 + "\n",
               FREEZE_AUDIT_REL: "## Audit\nICP_GEN2_AUDIT=PASS frozen_sha256=" + "0" * 64 + "\n"}
    rows.append(("A7-recorded-sha-differs", "A7", aud(real, files=rec_bad)))
    rows.append(("A7-frozen-without-record", "A7", aud(real, files={FROZEN_AT_REL: "0" * 40 + "\n", FREEZE_AUDIT_REL: None})))
    for name, label, out in rows:
        hit = [x for x in out if x.startswith(label)]
        say(bool(hit), f"V-IC2-MUT-{name} killed by {label}" if hit
            else f"V-IC2-MUT-{name} SURVIVED (expected a {label} line, got {out[:2]})")

    # the binding is restored after every route out of bound()
    before = snapshot_bindings()
    with bound():
        inside = snapshot_bindings()
    try:
        with bound():
            raise RuntimeError("probe")
    except RuntimeError:
        pass
    with contextlib.redirect_stdout(io.StringIO()):
        main("status")
    after = snapshot_bindings()
    say(inside != before and inside["LEDGER_REL"] == LEDGER_REL and after == before,
        "V-IC2-BINDING-RESTORED (seven CE globals equal their pre-run values after a status run and after an exception)")
    probe = _could_not_run_probe()
    say(probe == [(2, True), (2, True)], f"V-IC2-COULD-NOT-RUN (missing and non-JSON ledger exit 2: {probe})")
    return ok


def _main_audit() -> int:
    """`--generation 2 --audit`: one line per rule A1-A7, then ICP_GEN2_AUDIT=PASS|FAIL|COULD_NOT_RUN. Exit 0/1/2."""
    try:
        led = load_ledger()
        if not isinstance(led, dict):
            raise ValueError("ledger is not a JSON object")
        roadmap = (REPO / ROADMAP_REL).read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ICP_GEN2_AUDIT=COULD_NOT_RUN ledger or ROADMAP unreadable: {exc}")
        return 2
    rep = audit_rules(led, ce.Resolver(), roadmap, _tracked_git, lambda: selftest(verbose=False))
    n_fail = 0
    for n in sorted(rep):
        fails, detail = rep[n]
        if not fails:
            print("A7 ok (not frozen yet)" if (n == 7 and detail == "not frozen yet") else f"A{n} ok {detail}")
        for x in fails:
            n_fail += 1
            print(f"A{n} FAIL {x[len(f'A{n} '):]}")
    sha = frozen_sha256(_frozen(led))
    if n_fail:
        print(f"ICP_GEN2_AUDIT=FAIL frozen_sha256={sha} failures={n_fail}")
        return 1
    print(f"ICP_GEN2_AUDIT=PASS frozen_sha256={sha}")
    return 0


def main(mode: str) -> int:
    if mode == "selftest":
        good = selftest()
        print(f"ICP_GEN2_SELFTEST={'PASS' if good else 'FAIL'}")
        return 0 if good else 1
    if mode == "audit":
        return _main_audit()
    if mode not in ("status", "final"):
        print(f"ICP_GEN2_VERDICT=COULD_NOT_RUN unknown mode {mode!r} (status|final|selftest|audit)")
        return 2
    try:
        led = load_ledger()
        if not isinstance(led, dict):
            raise ValueError("ledger is not a JSON object")
    except (OSError, ValueError) as exc:  # JSONDecodeError is a ValueError
        print(f"ICP_GEN2_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    fails = problems(led, None, final=(mode == "final"))
    if mode == "final" and not selftest(verbose=False):
        fails.insert(0, "S0 selftest failed: the verifier cannot be trusted")
    if mode == "status":
        state = led.get("state") or {}
        open_ = [p for p in PILLARS if not (state.get(p) or {}).get("terminal")]
        print(json.dumps({"open": open_, "closed": [p for p in PILLARS if p not in open_], "violations": fails},
                         ensure_ascii=False))
        return 1 if fails else 0
    for x in fails:
        print("  FAIL", x)
    print(f"ICP_GEN2_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "final"))
