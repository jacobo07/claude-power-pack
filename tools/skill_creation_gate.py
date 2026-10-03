#!/usr/bin/env python
"""skill_creation_gate.py -- the creation-governance gate (skill-capability, pillar J, decision D-02).

    python3 tools/skill_creation_gate.py              # judge HEAD; exit 0 only on PASS
    python3 tools/skill_creation_gate.py --json       # the full result as one JSON object
    python3 tools/skill_creation_gate.py --ref <c>    # judge another commit of this checkout
    python3 tools/skill_creation_gate.py --render     # print the evidence render to stdout (writes nothing)
    python3 tools/skill_creation_gate.py --suggest    # print the declaration lines each undeclared skill needs

The frozen J rule: a new skill must declare its opportunity detector or why it has none; a gate refuses a skill
directory without the declaration.

Declaration grammar (DJ-01, DJ-02). Inside the SKILL.md frontmatter (the block `skill_index._FM_RE` matches), under a
top-level `metadata:` key with an empty value, as two-space-indented children:

    metadata:
      opportunity_detector: <repo-relative path of a committed detector file>

or

    metadata:
      opportunity_detector: none
      opportunity_detector_reason: <text>

The keys live under `metadata:` because the official skill-creator validator whitelists top-level keys (name,
description, license, allowed-tools, metadata, compatibility) and excludes keys nested under metadata; a top-level
`opportunity_detector:` would add a new refusal there, so this gate refuses it (FORM). The reason text matches
REASON_RE: no colon and no `#`, so it is always a valid YAML plain scalar and can never carry a `name:` or
`description:` substring that a first-match frontmatter regex could pick up. It must also not match YAML_NON_STRING
(null, booleans, numbers, dates), so a YAML reader always reads it as a string.

Population, DISCOVERED (never listed): every distinct `<name>` among the paths `skills/<name>/...` tracked at the
judged commit. A directory with no tracked SKILL.md is a member and fails DECLARED. Floor 2.

Clauses (all 7 must be PASS for a PASS verdict; outcomes PASS, FAIL or UNMEASURED):
  per skill  DECLARED         a tracked SKILL.md whose frontmatter holds exactly one opportunity_detector line
             FORM             every opportunity_detector and opportunity_detector_reason line is a metadata child;
                              every detector value is `none` or a plain relative path (PATH_RE, no `//`, no `..`
                              segment); every reason matches REASON_RE and is not a YAML non-string scalar
             TARGET           a path value (normalized) is tracked at the judged commit; `none` has a non-blank reason
             COVERAGE-AGREES  checked against pillar D's coverage class, computed from the committed dispatcher, hooks
                              and tools/*.py through skill_coverage: class opportunity_detector agrees only with a path
                              that is one of the files of its coverage evidence; classes card and none agree only with
                              `none` (a card without a CO-12 adapter is not an opportunity detector in D's taxonomy)
             With zero opportunity_detector lines FORM, TARGET and COVERAGE-AGREES are UNMEASURED ("no declaration");
             otherwise each judges every value, independently of DECLARED.
  gate       FLOOR            population size >= 2 (0 is UNMEASURED, 1 is FAIL)
             POSITIVE-CONTROL at least one population member has coverage class opportunity_detector, proof that the
                              agreement check can see the detector branch, whatever that member declares (0 members:
                              UNMEASURED)
             EVIDENCE-CURRENT the committed vault/programs/skill-capability/evidence/J-creation-gate.md equals
                              render() of this result after LF normalization (not committed: UNMEASURED)

Committed-blob rule: every byte judged (SKILL.md files, the dispatcher, its registered hooks, every top-level tools/*.py,
the evidence file) is a git blob at the resolved commit; no working-tree file is read, so a peer's uncommitted edit
never stands in for a declaration and a CRLF clone judges the same as an LF one. Git access, blob reads and failure
classification are skill_mirror_drift's (one implementation); coverage is skill_coverage's (no second classifier).

A git failure (ref unresolvable, git missing, nothing tracked, a blob read that skill_mirror_drift.is_git_failure
classifies as a failure, a tracked path the batch read could not return) is INCONCLUSIVE, never PASS and never a
traceback. Any exception inside the judge is INCONCLUSIVE naming the exception class.

render() holds no commit sha and no time; it holds `skills_tree=<tree id of skills/>`, so the evidence goes stale
exactly when a skill changes and can be committed without staling itself.

Exit codes: 0 PASS, 1 FAIL or INCONCLUSIVE, 2 bad arguments. This tool never writes a file.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.append(str(_THIS_DIR.parent))  # appended, so the repo root never shadows an installed module

import skill_coverage as sc  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402
from modules.skill_router.skill_index import _FM_RE  # noqa: E402  (the frontmatter grammar the skill index uses)

RULE = ("a new skill must declare its opportunity detector or why it has none; a gate refuses a skill directory "
        "without the declaration")
EVIDENCE_REL = "vault/programs/skill-capability/evidence/J-creation-gate.md"
SKILL_MD = "SKILL.md"
POPULATION_FLOOR = 2
SKILL_CLAUSES = ("DECLARED", "FORM", "TARGET", "COVERAGE-AGREES")
GATE_CLAUSES = ("FLOOR", "POSITIVE-CONTROL", "EVIDENCE-CURRENT")
PASS, FAIL, UNMEASURED, INCONCLUSIVE = "PASS", "FAIL", "UNMEASURED", "INCONCLUSIVE"
NONE_VALUE = "none"
DETECTOR_KEY = "opportunity_detector"
REASON_KEY = "opportunity_detector_reason"

DETECTOR_LINE = re.compile(r"^\s*opportunity_detector:\s*(.*)$")
REASON_LINE = re.compile(r"^\s*opportunity_detector_reason:\s*(.*)$")
METADATA_LINE = re.compile(r"^metadata:\s*$")
METADATA_CHILD = re.compile(r"^  \S")
PATH_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")
REASON_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ,.;()/_'-]{0,299}$")
# A plain scalar that a YAML reader resolves to something other than a string (core schema and YAML 1.1, which
# PyYAML and the official skill-creator validator use): null, a boolean, an int (with `_`, 0x / 0o / 0b forms), a
# float, a date or timestamp. REASON_RE admits several of them (`null`, `no`, `off`, `0`, `2026-10-04`), and a
# reason a YAML reader takes as absent or as a number must never read as present (review WR-04).
YAML_NON_STRING = re.compile(
    r"(?i)^(?:null|~|true|false|yes|no|on|off|y|n)$"
    r"|^[-+]?(?:0b[01_]+|0o?[0-7_]+|0x[0-9a-f_]+|[0-9][0-9_]*(?:\.[0-9_]*)?(?:e[-+]?[0-9]+)?|\.[0-9_]+(?:e[-+]?[0-9]+)?)$"
    r"|^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$")
MISSING = "git-batch-missing"
EMPTY = "git-batch-empty"


def _out(outcome, reason=""):
    return {"outcome": outcome, "reason": reason}


# --------------------------------------------------------------------------- declaration grammar

def parse_declaration(text: str) -> dict:
    """{frontmatter, detector [{value, line, metadata_child}], reason [...], count} of one SKILL.md text.

    Lines are numbered within the frontmatter body. A child of `metadata:` is a line with exactly two spaces of
    indent after a top-level `metadata:` line with an empty value, before the next top-level line."""
    text = sc.lf(text or "")
    m = _FM_RE.match(text)
    if m is None:
        return {"frontmatter": False, "detector": [], "reason": [], "count": 0}
    detector, reason = [], []
    in_meta = False
    for n, line in enumerate(m.group(1).split("\n"), 1):
        if line and not line[0].isspace():
            in_meta = bool(METADATA_LINE.match(line))
            child = False
        else:
            child = in_meta and bool(METADATA_CHILD.match(line))
        d = DETECTOR_LINE.match(line)
        if d:
            detector.append({"value": d.group(1).strip(), "line": n, "metadata_child": child})
            continue
        r = REASON_LINE.match(line)
        if r:
            reason.append({"value": r.group(1).strip(), "line": n, "metadata_child": child})
    return {"frontmatter": True, "detector": detector, "reason": reason, "count": len(detector)}


def reason_form_ok(value: str) -> bool:
    """The DJ-02 reason grammar: REASON_RE, and never a YAML non-string scalar."""
    return bool(REASON_RE.match(value)) and not YAML_NON_STRING.match(value)


def _value_form_ok(value: str) -> bool:
    if value == NONE_VALUE:
        return True
    if not PATH_RE.match(value) or "//" in value:
        return False
    return ".." not in value.split("/")


def evidence_files(evidence) -> set:
    """The file part (before the first `:`) of each skill_coverage evidence string, normalized."""
    return {posixpath.normpath(str(e).split(":", 1)[0]) for e in evidence or []}


def declaration_lines(skill: str, klass: str, evidence) -> list:
    """The frontmatter lines that declare `skill` consistently with its coverage class (one implementation, used by
    the drills and by the 08-02 insertion). Raises ValueError when no valid declaration can be produced."""
    if klass == "opportunity_detector":
        files = [str(e).split(":", 1)[0] for e in evidence or []]
        if not files:
            raise ValueError(f"{skill}: class opportunity_detector without evidence")
        path = posixpath.normpath(files[0])
        if path == NONE_VALUE or not _value_form_ok(path):
            raise ValueError(f"{skill}: detector path {path!r} is not a plain relative path")
        return ["metadata:", f"  {DETECTOR_KEY}: {path}"]
    if klass == "card":
        hooks = sorted(evidence_files(evidence))
        if not hooks:
            raise ValueError(f"{skill}: class card without evidence")
        text = (f"coverage class card; deny card {', '.join(hooks)} names this skill and no CO-12 adapter "
                f"declares it, so it is not an opportunity detector")
    elif klass == "none":
        text = "coverage class none; no registered card hook and no CO-12 adapter names this skill"
    else:
        raise ValueError(f"{skill}: unknown coverage class {klass!r}")
    if not reason_form_ok(text):
        raise ValueError(f"{skill}: generated reason violates the reason grammar: {text!r}")
    return ["metadata:", f"  {DETECTOR_KEY}: {NONE_VALUE}", f"  {REASON_KEY}: {text}"]


def insert_declaration(text: str, lines) -> str:
    """`text` with `lines` appended at the end of its frontmatter. Keeps CRLF when the text uses it. Refuses (ValueError)
    a text without frontmatter, one that already has a top-level `metadata:` key, or one that already declares."""
    crlf = "\r\n" in text
    body = sc.lf(text)
    m = _FM_RE.match(body)
    if m is None:
        raise ValueError("no frontmatter")
    fm = m.group(1)
    if any(METADATA_LINE.match(ln) or ln.startswith("metadata:") for ln in fm.split("\n")):
        raise ValueError("frontmatter already has a metadata key; merge by hand")
    if parse_declaration(body)["count"] or parse_declaration(body)["reason"]:
        raise ValueError("frontmatter already declares an opportunity detector")
    end = m.start(1) + len(fm)
    out = body[:end] + "".join(f"{ln}\n" for ln in lines) + body[end:]
    return out.replace("\n", "\r\n") if crlf else out


# --------------------------------------------------------------------------- clauses

def c_declared(ctx, member):
    if not member["tracked"]:
        return _out(FAIL, f"{SKILL_MD} not tracked")
    decl = member["decl"]
    if not decl["frontmatter"]:
        return _out(FAIL, "no frontmatter")
    n = decl["count"]
    if n == 1:
        return _out(PASS)
    if n == 0:
        return _out(FAIL, f"no {DETECTOR_KEY} line")
    return _out(FAIL, f"{n} {DETECTOR_KEY} lines")


def c_form(ctx, member):
    decl = member["decl"]
    if not decl["count"]:
        return _out(UNMEASURED, "no declaration")
    bad = []
    for d in decl["detector"]:
        if not d["metadata_child"]:
            bad.append(f"line {d['line']}: {DETECTOR_KEY} is not a metadata child")
        if not _value_form_ok(d["value"]):
            bad.append(f"line {d['line']}: value {d['value']!r} is neither none nor a plain relative path")
    for r in decl["reason"]:
        if not r["metadata_child"]:
            bad.append(f"line {r['line']}: {REASON_KEY} is not a metadata child")
        if not REASON_RE.match(r["value"]):
            bad.append(f"line {r['line']}: reason violates the reason grammar")
        elif YAML_NON_STRING.match(r["value"]):
            bad.append(f"line {r['line']}: reason {r['value']!r} is a YAML null, boolean, number or date, not text")
    return _out(FAIL, "; ".join(bad)) if bad else _out(PASS)


def c_target(ctx, member):
    decl = member["decl"]
    if not decl["count"]:
        return _out(UNMEASURED, "no declaration")
    bad = []
    for d in decl["detector"]:
        v = d["value"]
        if v == NONE_VALUE:
            if not any(r["value"].strip() for r in decl["reason"]):
                bad.append(f"none without a non-blank {REASON_KEY}")
        elif not v or posixpath.normpath(v) not in ctx["tracked"]:
            bad.append(f"{v!r} is not tracked at {ctx['sha'][:8]}")
    return _out(FAIL, "; ".join(bad)) if bad else _out(PASS)


def c_coverage_agrees(ctx, member):
    decl = member["decl"]
    if not decl["count"]:
        return _out(UNMEASURED, "no declaration")
    klass = member["class"]
    files = evidence_files(member["evidence"])
    bad = []
    for d in decl["detector"]:
        v = d["value"]
        if klass == "opportunity_detector":
            if v == NONE_VALUE or not v or posixpath.normpath(v) not in files:
                bad.append(f"declares {v!r}; coverage class opportunity_detector with evidence {sorted(files)}")
        elif v != NONE_VALUE:
            bad.append(f"declares {v!r}; coverage class {klass} agrees only with none")
    return _out(FAIL, "; ".join(bad)) if bad else _out(PASS)


def c_floor(ctx, member=None):
    n = len(ctx["members"])
    if n == 0:
        return _out(UNMEASURED, "empty population")
    if n >= POPULATION_FLOOR:
        return _out(PASS, f"population={n}")
    return _out(FAIL, f"population={n} < {POPULATION_FLOOR}")


def c_positive_control(ctx, member=None):
    if not ctx["members"]:
        return _out(UNMEASURED, "empty population")
    hits = [m["skill"] for m in ctx["members"] if m["class"] == "opportunity_detector"]
    if hits:
        return _out(PASS, f"class opportunity_detector seen for {', '.join(hits)}")
    return _out(FAIL, "no population member has coverage class opportunity_detector")


def c_evidence_current(ctx, member=None):
    blob, why = ctx["evidence"]
    if blob is None and why == MISSING:
        return _out(UNMEASURED, "evidence not committed")
    if blob is None:
        return _out(FAIL, f"evidence unreadable: {why}")
    committed = sc.lf(blob.decode("utf-8", "replace"))
    if committed == render(ctx["result"]):
        return _out(PASS)
    return _out(FAIL, f"{EVIDENCE_REL} differs from the render of this commit (re-render and commit it)")


CLAUSES = {
    "DECLARED": c_declared,
    "FORM": c_form,
    "TARGET": c_target,
    "COVERAGE-AGREES": c_coverage_agrees,
    "FLOOR": c_floor,
    "POSITIVE-CONTROL": c_positive_control,
    "EVIDENCE-CURRENT": c_evidence_current,
}


# --------------------------------------------------------------------------- judge

def _inconclusive(result, reason):
    result.update({"verdict": INCONCLUSIVE, "reason": reason})
    return result


def population(tracked) -> list:
    return sorted({p.split("/")[1] for p in tracked if p.startswith("skills/") and p.count("/") >= 2})


def _blobs(repo, sha, rels):
    """({rel: bytes|None}, None) or (None, reason). A tracked rel that comes back as anything but an empty blob is
    a failure: git said the path is in the commit, then did not return it."""
    got = smd.vgm.batch_blobs(str(repo), sha, list(rels))
    out = {}
    for rel in rels:
        data, why = got.get(rel, (None, "not returned"))
        if data is not None:
            out[rel] = data
        elif why == EMPTY:
            out[rel] = b""
        else:
            kind = "git failure" if smd.is_git_failure(why) else "unreadable tracked blob"
            return None, f"{kind}: {rel}: {why}"
    return out, None


def judge(repo=smd.REPO, ref="HEAD") -> dict:
    """{verdict PASS|FAIL|INCONCLUSIVE, head, reason, skills_tree, population, skills [...], gate {...}}."""
    result = {"verdict": None, "head": None, "reason": "", "skills_tree": None, "population": [], "skills": [],
              "gate": {}}
    try:
        sha, why = smd.resolve_commit(repo, ref)
        if sha is None:
            return _inconclusive(result, f"{ref} not resolvable: {why}")
        result["head"] = sha
        tracked, why = smd.tracked_paths(repo, sha)
        if tracked is None:
            return _inconclusive(result, f"ls-tree: {why}")
        if not tracked:
            return _inconclusive(result, "nothing tracked")
        names = population(tracked)
        result["population"] = names
        if names:
            out, why = smd.git_run(repo, "rev-parse", f"{sha}:skills")
            if out is None:
                return _inconclusive(result, f"skills tree: {why}")
            result["skills_tree"] = out.decode("utf-8", "replace").strip()
        else:
            result["skills_tree"] = NONE_VALUE

        disp_text = ""
        if sc.DISPATCHER_REL in tracked:
            got, why = _blobs(repo, sha, [sc.DISPATCHER_REL])
            if got is None:
                return _inconclusive(result, why)
            disp_text = sc.lf(got[sc.DISPATCHER_REL].decode("utf-8", "replace"))
        hook_rels = sorted(r for r in sc.registered_hooks(disp_text) if r in tracked)
        tool_rels = sorted(p for p in tracked if re.fullmatch(r"tools/[^/]+\.py", p))
        md_rels = [f"skills/{n}/{SKILL_MD}" for n in names if f"skills/{n}/{SKILL_MD}" in tracked]
        got, why = _blobs(repo, sha, sorted(set(hook_rels) | set(tool_rels) | set(md_rels)))
        if got is None:
            return _inconclusive(result, why)
        ev = smd.vgm.batch_blobs(str(repo), sha, [EVIDENCE_REL]).get(EVIDENCE_REL, (None, "not returned"))
        if ev[0] is None and ev[1] != MISSING and ev[1] != EMPTY:
            kind = "git failure" if smd.is_git_failure(ev[1]) else "unreadable evidence blob"
            return _inconclusive(result, f"{kind}: {EVIDENCE_REL}: {ev[1]}")
        if ev[0] is None and ev[1] == EMPTY:
            ev = (b"", None)

        def text(rel):
            return sc.lf(got[rel].decode("utf-8", "replace"))

        with tempfile.TemporaryDirectory() as empty:
            cards = sc.discover_cards(Path(empty), dispatcher_text=disp_text,
                                      hook_texts={r: text(r) for r in hook_rels}, read_disk=False)
        with tempfile.TemporaryDirectory() as empty:
            adapters = sc.opportunity_adapters(Path(empty), adapter_texts={r: text(r) for r in tool_rels})

        members = []
        for n in names:
            rel = f"skills/{n}/{SKILL_MD}"
            is_tracked = rel in tracked
            klass, evidence = sc.coverage(n, cards, adapters)
            members.append({"skill": n, "md": rel, "tracked": is_tracked,
                            "decl": parse_declaration(text(rel)) if is_tracked else parse_declaration(""),
                            "class": klass, "evidence": evidence})
        ctx = {"repo": repo, "sha": sha, "tracked": tracked, "members": members, "evidence": ev, "result": result}
        for m in members:
            row = {"skill": m["skill"], "tracked": m["tracked"], "declaration": m["decl"], "class": m["class"],
                   "evidence": m["evidence"], "clauses": {}}
            for cid in SKILL_CLAUSES:
                row["clauses"][cid] = CLAUSES[cid](ctx, m)
            result["skills"].append(row)
        for cid in ("FLOOR", "POSITIVE-CONTROL"):
            result["gate"][cid] = CLAUSES[cid](ctx)
        # EVIDENCE-CURRENT last: render() reads every other clause and never this one.
        result["gate"]["EVIDENCE-CURRENT"] = CLAUSES["EVIDENCE-CURRENT"](ctx)
        non_pass = sorted(fail_set(result))
        result["verdict"] = PASS if not non_pass else FAIL
        result["reason"] = "" if not non_pass else "non-PASS: " + ", ".join(non_pass)
        return result
    except Exception as e:  # noqa: BLE001 -- a judge that crashes says INCONCLUSIVE, never prints a traceback
        return _inconclusive(result, f"exception {type(e).__name__}")


def fail_set(result) -> set:
    """{"<skill>:<CLAUSE>"} for per-skill and {"<CLAUSE>"} for gate clauses whose outcome is not PASS."""
    out = {cid for cid, c in result.get("gate", {}).items() if c.get("outcome") != PASS}
    for row in result.get("skills", []):
        out |= {f"{row['skill']}:{cid}" for cid, c in row["clauses"].items() if c.get("outcome") != PASS}
    return out


# --------------------------------------------------------------------------- render and CLI

def _cell(s) -> str:
    return str(s).replace("|", "\\|")


def _declared_text(decl) -> str:
    if not decl["count"]:
        return "(undeclared)"
    parts = [d["value"] or "(blank)" for d in decl["detector"]]
    reasons = [r["value"] for r in decl["reason"]]
    return "; ".join(parts) + (f" (reason: {' / '.join(reasons)})" if reasons else "")


def render(result) -> str:
    """Deterministic evidence markdown. Excludes EVIDENCE-CURRENT, the commit sha and any time."""
    lines = [
        "# J creation gate evidence (skill-capability pillar J)",
        "",
        f"Rule: {RULE}.",
        "",
        "Rendered by `python3 tools/skill_creation_gate.py --render`; judged by `python3 tools/skill_creation_gate.py`.",
        "",
        f"skills_tree={result.get('skills_tree')}",
        f"population={len(result.get('population', []))}",
        "",
        "| skill | declaration | coverage class | coverage evidence files | " + " | ".join(SKILL_CLAUSES) + " |",
        "|" + "---|" * (4 + len(SKILL_CLAUSES)),
    ]
    for row in result.get("skills", []):
        files = ", ".join(sorted(evidence_files(row["evidence"]))) or "-"
        outs = " | ".join(row["clauses"][cid]["outcome"] for cid in SKILL_CLAUSES)
        lines.append(f"| {_cell(row['skill'])} | {_cell(_declared_text(row['declaration']))} | {row['class']} | "
                     f"{_cell(files)} | {outs} |")
    lines.append("")
    for cid in ("FLOOR", "POSITIVE-CONTROL"):
        c = result.get("gate", {}).get(cid, {"outcome": "?", "reason": ""})
        lines.append(f"{cid}={c['outcome']}" + (f" ({c['reason']})" if c.get("reason") else ""))
    return "\n".join(lines) + "\n"


def text_lines(result) -> list:
    lines = []
    for row in result.get("skills", []):
        outs = " ".join(f"{cid}={row['clauses'][cid]['outcome']}" for cid in SKILL_CLAUSES)
        why = "; ".join(f"{cid}: {row['clauses'][cid]['reason']}" for cid in SKILL_CLAUSES
                        if row["clauses"][cid]["outcome"] != PASS and row["clauses"][cid]["reason"])
        lines.append(f"{row['skill']} class={row['class']} {outs}" + (f" -- {why}" if why else ""))
    for cid in GATE_CLAUSES:
        c = result.get("gate", {}).get(cid)
        if c is not None:
            lines.append(f"{cid}={c['outcome']}" + (f" ({c['reason']})" if c["reason"] else ""))
    tail = f"SKILL_CREATION {result['verdict']} population={len(result.get('population', []))}"
    if result["verdict"] == INCONCLUSIVE:
        tail += f" reason={result['reason']}"
    lines.append(tail)
    return lines


def suggest_lines(result) -> list:
    lines = []
    for row in result.get("skills", []):
        if row["clauses"]["DECLARED"]["outcome"] == PASS:
            continue
        if not row["tracked"]:
            lines.append(f"# {row['skill']}: {SKILL_MD} not tracked, nothing to suggest")
            continue
        lines.append(f"# {row['skill']} (coverage class {row['class']})")
        try:
            lines.extend(declaration_lines(row["skill"], row["class"], row["evidence"]))
        except ValueError as e:
            lines.append(f"# refused: {e}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="skill creation-governance gate (pillar J)")
    ap.add_argument("--repo", default=str(smd.REPO))
    ap.add_argument("--ref", default="HEAD")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true")
    mode.add_argument("--render", action="store_true", help="print the evidence render; writes nothing")
    mode.add_argument("--suggest", action="store_true", help="print declaration lines; writes nothing")
    a = ap.parse_args(argv)
    result = judge(Path(a.repo), a.ref)
    if a.json:
        print(json.dumps(result, indent=1, sort_keys=True, default=str))
    elif a.render or a.suggest:
        if result["verdict"] == INCONCLUSIVE:
            print(f"SKILL_CREATION INCONCLUSIVE reason={result['reason']}", file=sys.stderr)
            return 1
        if a.render:
            sys.stdout.write(render(result))
        else:
            print("\n".join(suggest_lines(result)))
        return 0
    else:
        print("\n".join(text_lines(result)))
    return 0 if result["verdict"] == PASS else 1


if __name__ == "__main__":
    sys.exit(main())
