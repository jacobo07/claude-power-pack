#!/usr/bin/env python
"""card_lineage.py -- the compile-out lineage gate (skill-capability, pillar G).

    python3 tools/card_lineage.py                          # judge HEAD; exit 0 only on PASS
    python3 tools/card_lineage.py --json                   # the full result as one JSON object
    python3 tools/card_lineage.py --ref <commit>           # judge another commit of this checkout
    python3 tools/card_lineage.py --trailer-for <skill>    # print the trailer line for a skill's committed SKILL.md

The frozen G rule: a compiled-out card names the skill and commit it was compiled from, and a gate fails when the
source skill changes without the card being re-derived. Pillar H's record (card_source_digests.json) alone does not
satisfy it, because H can be re-recorded without anybody re-reading the skill. The lineage therefore lives INSIDE the
card file, one trailer line per skill the card names, and only rewriting that line clears a source change.

Trailer grammar (one full line of the LF-normalized card text, comment-only, no backtick character). A card that names
several skills in CARD_TOKEN form (pillar H records one pair per named skill) carries one trailer per named skill, so a
change to ANY named skill's SKILL.md fails SOURCE-CURRENT until that skill's line is re-derived:

    // COMPILED-FROM: skill=<name> source=skills/<name>/SKILL.md sha256=<64 hex> commit=<40 hex>

sha256 is the LF-normalized sha256 of the committed SKILL.md (identity); commit is the commit that last changed that
SKILL.md when the card was derived (provenance). `--trailer-for` prints the line; it never writes a card, because the
gate does not generate card text: a person or agent re-reads the skill, re-derives the card and pastes the line.

Population, DISCOVERED (never listed): every `hooks/**/*.js` tracked at the judged commit, outside `hooks/tests/` and
`hooks/_tests/`, whose LF text holds a skill_coverage CARD_TOKEN match or a line starting with the marker. Discovery
does not depend on the registration shape. A member whose blob cannot be read makes the
verdict INCONCLUSIVE; it is never dropped. Floor 2.

Clauses (all 10 must be PASS for a PASS verdict; outcomes are PASS, FAIL or UNMEASURED):
  per card  TRAILER          at least one marker line, every one parses, no skill twice (absent, duplicate skill,
                             unparseable: UNMEASURED; the other six per-card clauses are then UNMEASURED "no trailer"),
                             and the marker lines are the last lines of the card (content after them: FAIL, and the
                             other six are still judged on the parsed trailers, so TRAILER alone can fail a card)
            SKILL            the trailer skills EQUAL the set of skills the card text names in CARD_TOKEN form: a
                             named skill without a trailer, or a trailer for a skill the card does not name, is FAIL
  The five clauses below SKILL are judged per trailer and folded: FAIL if any trailer FAILs, else UNMEASURED if any is
  UNMEASURED, else PASS.
            SOURCE-PATH      the trailer's source is skills/<trailer skill>/SKILL.md
            SOURCE-CURRENT   the committed source at the judged commit has the trailer's digest (an absent source,
                             i.e. a skill that does not exist, is UNMEASURED)
  SOURCE-CURRENT and the three COMMIT-* clauses judge the CANONICAL source skills/<trailer skill>/SKILL.md, never the
  trailer's source string, so a wrong path cannot make them report a foreign file as current (06 review IN-02).
            COMMIT-ANCESTOR  the trailer commit resolves and is an ancestor of the judged commit
            COMMIT-TOUCHES   the trailer commit changed the source path: last_change(commit, source) == commit, the
                             same definition trailer_for prints (a merge that resolved the source counts)
            COMMIT-DIGEST    the source blob at the trailer commit has the trailer's digest
  gate      FLOOR            population size >= 2 (0 is UNMEASURED, 1 is FAIL)
            DISPATCHER-COVERED  every card the dispatcher registers, in either CHAIN_MAP shape
                             (`../skills/claude-power-pack/<rel>` and `./<rel>`, via
                             skill_mirror_drift.committed_card_pairs(dotslash=True)), is a population member, so a
                             registered card outside the sweep (e.g. under hooks/tests/) cannot escape it
            H-RECORD-CURRENT pillar H's committed record agrees with the committed cards and sources
                             (skill_mirror_drift.card_drift + card_verdict)

Committed-blob rule (DG-03): every byte compared comes from git blobs at the resolved judged commit or at the trailer
commit. No working-tree file is read, so a peer's uncommitted edit never stands in for a source, and a CRLF working
tree (the laptop clone) judges the same as an LF one. `skill_mirror_drift.load_card_record` and `committed_bytes` are
deliberately not used: at HEAD they read the working tree to refuse an uncommitted copy. Git access, blob reads,
failure classification and the record comparison are the functions pillar H uses (one implementation).

A git failure before or during discovery (unresolvable ref, git missing, nothing tracked, a member blob read failure)
is INCONCLUSIVE, never PASS and never a traceback. After discovery, a clause whose git call did not answer (failure,
timeout, a non-absence rc, or a trailer commit beyond a shallow clone's history) is a git-tagged UNMEASURED; when every
non-PASS clause is git-tagged the verdict is INCONCLUSIVE, and any measured FAIL or non-git UNMEASURED makes it FAIL.
A trailer commit absent from a complete (non-shallow) history cannot be an ancestor: COMMIT-ANCESTOR FAIL.

Exit codes: 0 PASS, 1 FAIL or INCONCLUSIVE (or a refused --trailer-for), 2 bad arguments. This tool never writes a file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import skill_coverage as sc  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402

LINEAGE_MARKER = "// COMPILED-FROM:"
TRAILER_RE = re.compile(
    r"^// COMPILED-FROM: skill=(?P<skill>[A-Za-z0-9_-]+) source=(?P<source>\S+) "
    r"sha256=(?P<sha256>[0-9a-f]{64}) commit=(?P<commit>[0-9a-f]{40})$")
# Every tracked hooks/**/*.js except the test trees (whose texts quote card tokens as test data).
CARD_FILE_RE = re.compile(r"hooks/(?!tests/|_tests/)(?:[^/]+/)*[^/]+\.js")
SKILL_NAME_RE = re.compile(r"[A-Za-z0-9_-]+")
POPULATION_FLOOR = 2
CARD_CLAUSES = ("TRAILER", "SKILL", "SOURCE-PATH", "SOURCE-CURRENT", "COMMIT-ANCESTOR", "COMMIT-TOUCHES",
                "COMMIT-DIGEST")
GATE_CLAUSES = ("FLOOR", "DISPATCHER-COVERED", "H-RECORD-CURRENT")
PASS, FAIL, UNMEASURED = "PASS", "FAIL", "UNMEASURED"


def _out(outcome, reason="", git=False):
    """A clause outcome. git=True marks an UNMEASURED that came from git not answering (a failure, a timeout, a
    shallow history), which folds into an INCONCLUSIVE verdict instead of FAIL (06 review WR-02)."""
    o = {"outcome": outcome, "reason": reason}
    if git and outcome == UNMEASURED:
        o["git"] = True
    return o


# git_run answers that are a fact about the judged tree (a path or object that is not there), not git failing.
_GIT_ANSWERS = ("does not exist", "exists on disk, but not in", "not in '")


def _git_reason(why) -> bool:
    """True when a reason string says git did not answer: git missing, an OS error or timeout (`git <sub> failed:`),
    a batch failure (smd.BATCH_FAILURES), or a non-zero rc that is not an absence answer."""
    w = str(why or "")
    if "git not found" in w or any(f in w for f in smd.BATCH_FAILURES):
        return True
    if re.search(r"\bgit [\w-]* failed:", w):
        return True
    if re.search(r"\bgit [\w-]* rc=\d+:", w):
        return not any(a in w for a in _GIT_ANSWERS)
    return False


def _unmeasured(reason, why=None):
    return _out(UNMEASURED, reason, git=_git_reason(why if why is not None else reason))


def _source_rel(skill) -> str:
    return f"skills/{skill}/SKILL.md"


# --------------------------------------------------------------------------- trailer and population

def _marker_lines(text) -> list:
    return [line for line in sc.lf(text).split("\n") if line.startswith(LINEAGE_MARKER)]


def _not_at_end(text) -> bool:
    """True when a non-marker line follows a marker line (one trailing newline is not a line)."""
    lines = sc.lf(text).split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    idx = [i for i, line in enumerate(lines) if line.startswith(LINEAGE_MARKER)]
    return bool(idx) and idx != list(range(len(lines) - len(idx), len(lines)))


def parse_trailers(text):
    """(trailers, None) or (None, "absent" | "unparseable" | "duplicate skill <name>"), or (trailers, "not at end of
    file") when every marker line parses but other content follows the lineage block: the trailers are returned so
    the other clauses can still be judged, and TRAILER is a measured FAIL (06 review IN-01)."""
    marks = _marker_lines(text)
    if not marks:
        return None, "absent"
    out = []
    for line in marks:
        m = TRAILER_RE.match(line)
        if not m:
            return None, "unparseable"
        out.append(m.groupdict())
    seen = set()
    for t in out:
        if t["skill"] in seen:
            return None, f"duplicate skill {t['skill']}"
        seen.add(t["skill"])
    if _not_at_end(text):
        return out, "not at end of file"
    return out, None


def parse_trailer(text):
    """(the one trailer, None) or (None, reason): parse_trailers for a text that must carry exactly one."""
    ts, why = parse_trailers(text)
    if ts is None or why:
        return None, why
    if len(ts) != 1:
        return None, f"{len(ts)} trailers"
    return ts[0], None


def population(repo, sha, tracked):
    """([{card, text}] sorted by card, None) or (None, "<rel>: <reason>") when a candidate blob cannot be read.
    Candidates are the tracked hooks/**/*.js outside the test trees (CARD_FILE_RE); a member holds a CARD_TOKEN match
    or a marker line."""
    rels = sorted(t for t in tracked if CARD_FILE_RE.fullmatch(t))
    blobs = smd.vgm.batch_blobs(str(repo), sha, rels)
    members = []
    for rel in rels:
        data, why = blobs.get(rel, (None, "not returned"))
        if data is None and why == "git-batch-empty":
            data = b""
        if data is None:
            # Either a git failure (smd.is_git_failure) or git-batch-missing for a path ls-tree just listed: both
            # mean the candidate was not read, and an unread candidate is never dropped.
            kind = "git failure" if smd.is_git_failure(why) else "unreadable"
            return None, f"{rel}: {kind}: {why}"
        text = sc.lf(data.decode("utf-8", "replace"))
        if sc.CARD_TOKEN.search(text) or _marker_lines(text):
            members.append({"card": rel, "text": text})
    return members, None


def last_change(repo, rev, source):
    """(sha of the last commit up to `rev` that changed `source`, or "" when none did, None) or (None, reason).

    The ONE definition of "the commit that changed the source", used by both trailer_for (the generator) and
    COMMIT-TOUCHES (the judge), so the judge can never refuse a commit the generator printed (06 review WR-03).
    Path-limited `git log` with default history simplification: a merge counts when it differs from every parent
    (e.g. a conflict resolved inside the source), which `git diff-tree` without -m/--cc never reports."""
    log, why = smd.git_run(repo, "log", "-1", "--format=%H", rev, "--", source)
    if log is None:
        return None, f"git log for {source}: {why}"
    commit = log.decode("utf-8", "replace").strip()
    return (commit if re.fullmatch(r"[0-9a-f]{40}", commit) else ""), None


def trailer_for(repo, skill, ref="HEAD"):
    """(trailer line, None) for the committed skills/<skill>/SKILL.md at `ref`, or (None, reason). Print-only."""
    if not SKILL_NAME_RE.fullmatch(skill or ""):
        return None, f"bad skill name {skill!r}"
    sha, why = smd.resolve_commit(repo, ref)
    if sha is None:
        return None, f"{ref} not resolvable: {why}"
    source = _source_rel(skill)
    data, why = smd.vgm.batch_blobs(str(repo), sha, [source]).get(source, (None, "not returned"))
    if data is None and why == "git-batch-empty":
        data = b""
    if data is None:
        return None, f"{source} not readable at {sha[:8]}: {why}"
    commit, why = last_change(repo, sha, source)
    if commit is None:
        return None, why
    if not commit:
        return None, f"no commit changed {source} up to {sha[:8]}"
    return (f"{LINEAGE_MARKER} skill={skill} source={source} sha256={smd.vgm._norm_sha(data)} "
            f"commit={commit}"), None


# --------------------------------------------------------------------------- clauses
# Each clause takes (ctx, member=None, trailers=None) and returns {outcome, reason}; trailers is the card's parsed
# trailer list. ctx holds repo, sha, members, pairs, pairs_why, registered and registered_why. judge() looks every clause up in CLAUSES at call time.


def _fold(rows):
    """One outcome from [(skill, {outcome, reason})] judged per trailer: FAIL > UNMEASURED > PASS. The reason names the
    skill when the card carries more than one trailer."""
    if not rows:
        return _out(UNMEASURED, "no trailer")
    for want in (FAIL, UNMEASURED):
        bad = [(sk, o) for sk, o in rows if o["outcome"] == want]
        if bad:
            return _out(want, "; ".join(o["reason"] if len(rows) == 1 else f"{sk}: {o['reason']}" for sk, o in bad),
                        git=all(o.get("git") for _, o in bad))
    return _out(PASS, "; ".join(o["reason"] if len(rows) == 1 else f"{sk}: {o['reason']}" for sk, o in rows))


def _per_trailer(fn):
    """A per-card clause judged once per trailer and folded (_fold)."""
    def clause(ctx, member=None, trailers=None):
        return _fold([(t["skill"], fn(ctx, member, t)) for t in (trailers or [])])
    clause.__name__ = fn.__name__
    clause.__doc__ = fn.__doc__
    return clause

def c_floor(ctx, member=None, trailer=None):
    n = len(ctx["members"])
    if n >= POPULATION_FLOOR:
        return _out(PASS, f"population={n}")
    if n == 0:
        return _out(UNMEASURED, "zero population")
    return _out(FAIL, f"population={n} below floor {POPULATION_FLOOR}")


def c_dispatcher_covered(ctx, member=None, trailer=None):
    pairs = ctx["registered"]
    if pairs is None:
        return _unmeasured(f"dispatcher card set unreadable: {ctx['registered_why']}", ctx["registered_why"])
    covered = {p["card"] for p in pairs}
    if not covered:
        return _out(UNMEASURED, "the dispatcher registers no card")
    members = {m["card"] for m in ctx["members"]}
    uncovered = sorted(covered - members)
    if uncovered:
        return _out(FAIL, "registered card outside the population: " + ", ".join(uncovered))
    return _out(PASS, f"{len(covered)} registered card(s), all members")


def c_h_record_current(ctx, member=None, trailer=None):
    raw, why = smd.git_run(ctx["repo"], "cat-file", "blob", f"{ctx['sha']}:{smd.CARD_RECORD_REL}")
    if raw is None:
        return _unmeasured(f"{smd.CARD_RECORD_REL} not readable at {ctx['sha'][:8]}: {why}", why)
    try:
        record = json.loads(smd.lf_bytes(raw).decode("utf-8"))
    except ValueError:
        return _out(UNMEASURED, "record unparseable")
    if ctx["pairs"] is None:
        return _unmeasured(f"dispatcher card set unreadable: {ctx['pairs_why']}", ctx["pairs_why"])
    # The measured pair list is passed as-is: [] is a measured empty set, never None (None would re-discover).
    rows = smd.card_drift(record, smd.card_source_state(ctx["repo"], ctx["sha"], ctx["pairs"]))
    verdict = smd.card_verdict(rows)
    if verdict == "CURRENT":
        return _out(PASS, f"{len(rows)} pair(s) CURRENT")
    bad = "; ".join(f"{r.get('card')}<-{r.get('skill')} {r['status']}"
                    + (f" ({r['reason']})" if r.get("reason") else "")
                    for r in rows if r["status"] != "CURRENT")
    if verdict == "INCONCLUSIVE":
        return _out(UNMEASURED, bad or verdict,
                    git=bool(rows) and all(_git_reason(r.get("reason")) for r in rows if r["status"] != "CURRENT"))
    return _out(FAIL, bad or verdict)


def c_trailer(ctx, member=None, trailers=None):
    ts, why = parse_trailers(member["text"])
    if ts is None:
        return _out(UNMEASURED, f"trailer {why}")
    if why:
        return _out(FAIL, f"{len(ts)} trailer(s), {why}: the lineage block must be the last lines of the card")
    return _out(PASS, f"{len(ts)} trailer(s) ending the card")


def c_skill(ctx, member=None, trailers=None):
    names = set(sc.CARD_TOKEN.findall(member["text"]))
    have = {t["skill"] for t in (trailers or [])}
    missing, extra = sorted(names - have), sorted(have - names)
    if not missing and not extra and names:
        return _out(PASS, ", ".join(sorted(names)))
    bad = []
    if missing:
        bad.append(f"card names skill(s) with no lineage trailer: {missing}")
    if extra:
        bad.append(f"trailer skill(s) not named by the card: {extra} (names: {sorted(names)})")
    return _out(FAIL, "; ".join(bad) or "the card names no skill")


@_per_trailer
def c_source_path(ctx, member=None, trailer=None):
    want = _source_rel(trailer["skill"])
    if trailer["source"] == want:
        return _out(PASS, want)
    return _out(FAIL, f"source {trailer['source']} is not {want}")


@_per_trailer
def c_source_current(ctx, member=None, trailer=None):
    src = _source_rel(trailer["skill"])
    pair = {"card": member["card"], "skill": trailer["skill"], "source": src}
    state = smd.card_source_state(ctx["repo"], ctx["sha"], [pair])
    if state.get("status") != "MEASURED":
        return _out(UNMEASURED, f"{src}: {state.get('reason', 'unmeasured')}", git=True)
    row = state["pairs"][0]
    if row.get("status") in ("UNTRACKED", "INCONCLUSIVE"):
        return _out(UNMEASURED, f"{src} {row['status']}: {row.get('reason')}",
                    git=row.get("status") == "INCONCLUSIVE")
    if row["source_sha256"] == trailer["sha256"]:
        return _out(PASS, "source digest at the judged commit equals the trailer")
    return _out(FAIL, f"{src} at {ctx['sha'][:8]} is {row['source_sha256'][:12]}, "
                      f"trailer says {trailer['sha256'][:12]}: re-derive the card")


def _trailer_commit(ctx, trailer):
    """(full sha, None, None) or (None, reason, kind). kind "absent" = the commit does not exist in a complete
    (non-shallow) history; "git" = git did not answer, or the history is shallow so absence proves nothing."""
    commit, why = smd.resolve_commit(ctx["repo"], trailer["commit"])
    if commit is not None:
        return commit, None, None
    if not re.search(r"\bgit rev-parse rc=1: no stderr$", str(why or "")):
        return None, why, "git"
    out, w = smd.git_run(ctx["repo"], "rev-parse", "--is-shallow-repository")
    if out is None:
        return None, f"{why}; shallow check: {w}", "git"
    if out.decode("utf-8", "replace").strip() == "false":
        return None, f"{trailer['commit'][:8]} does not exist in this complete history", "absent"
    return None, f"shallow clone: {trailer['commit'][:8]} is beyond the history this checkout holds", "git"


def _commit_unreadable(why, kind):
    return _out(UNMEASURED, f"commit-not-readable: {why}", git=kind == "git")


@_per_trailer
def c_commit_ancestor(ctx, member=None, trailer=None):
    commit, why, kind = _trailer_commit(ctx, trailer)
    if commit is None:
        if kind == "absent":
            return _out(FAIL, f"{why}, so it is not an ancestor of {ctx['sha'][:8]}")
        return _commit_unreadable(why, kind)
    out, why = smd.git_run(ctx["repo"], "merge-base", "--is-ancestor", commit, ctx["sha"])
    if out is not None:
        return _out(PASS, f"{commit[:8]} is an ancestor of {ctx['sha'][:8]}")
    if " rc=1:" in (why or ""):
        return _out(FAIL, f"{commit[:8]} is not an ancestor of {ctx['sha'][:8]}")
    return _out(UNMEASURED, f"merge-base: {why}", git=True)


@_per_trailer
def c_commit_touches(ctx, member=None, trailer=None):
    commit, why, kind = _trailer_commit(ctx, trailer)
    if commit is None:
        return _commit_unreadable(why, kind)
    src = _source_rel(trailer["skill"])
    last, why = last_change(ctx["repo"], commit, src)
    if last is None:
        return _out(UNMEASURED, why, git=True)
    if last == commit:
        return _out(PASS, f"{commit[:8]} changed {src}")
    return _out(FAIL, f"{commit[:8]} did not change {src} (the last commit up to it that did: "
                      f"{last[:8] if last else 'none'})")


@_per_trailer
def c_commit_digest(ctx, member=None, trailer=None):
    commit, why, kind = _trailer_commit(ctx, trailer)
    if commit is None:
        return _commit_unreadable(why, kind)
    src = _source_rel(trailer["skill"])
    data, why = smd.vgm.batch_blobs(str(ctx["repo"]), commit, [src]).get(src, (None, "not returned"))
    if data is None and why == "git-batch-empty":
        data = b""
    if data is not None:
        got = smd.vgm._norm_sha(data)
        if got == trailer["sha256"]:
            return _out(PASS, f"{src} at {commit[:8]} carries the trailer digest")
        return _out(FAIL, f"{src} at {commit[:8]} is {got[:12]}, trailer says {trailer['sha256'][:12]}")
    if why == "git-batch-missing":
        return _out(FAIL, f"no-blob-at-commit: {src} at {commit[:8]}")
    if smd.is_git_failure(why):
        return _out(UNMEASURED, f"git failure: {why}", git=True)
    return _unmeasured(f"{src} at {commit[:8]}: {why}", why)


CLAUSES = {
    "TRAILER": c_trailer,
    "SKILL": c_skill,
    "SOURCE-PATH": c_source_path,
    "SOURCE-CURRENT": c_source_current,
    "COMMIT-ANCESTOR": c_commit_ancestor,
    "COMMIT-TOUCHES": c_commit_touches,
    "COMMIT-DIGEST": c_commit_digest,
    "FLOOR": c_floor,
    "DISPATCHER-COVERED": c_dispatcher_covered,
    "H-RECORD-CURRENT": c_h_record_current,
}


# --------------------------------------------------------------------------- judge

def _inconclusive(head, reason, result=None):
    r = result or {"population": [], "cards": [], "gate": {}}
    r.update({"verdict": "INCONCLUSIVE", "head": head, "reason": reason})
    return r


def judge(repo=smd.REPO, ref="HEAD") -> dict:
    """{verdict PASS|FAIL|INCONCLUSIVE, head, reason, population [rels], cards [{card, trailers, clauses}], gate}."""
    result = {"verdict": None, "head": None, "reason": "", "population": [], "cards": [], "gate": {}}
    try:
        sha, why = smd.resolve_commit(repo, ref)
        if sha is None:
            return _inconclusive(None, f"{ref} not resolvable: {why}", result)
        result["head"] = sha
        tracked, why = smd.tracked_paths(repo, sha)
        if tracked is None:
            return _inconclusive(sha, f"ls-tree: {why}", result)
        if not tracked:
            return _inconclusive(sha, "nothing tracked", result)
        members, why = population(repo, sha, tracked)
        if members is None:
            return _inconclusive(sha, f"population read failed: {why}", result)
        result["population"] = [m["card"] for m in members]
        # pairs: pillar H's own pair set (its record's definition, one registration shape). registered: every card
        # the dispatcher registers in either shape, for DISPATCHER-COVERED (06 review WR-01).
        pairs, pairs_why = smd.committed_card_pairs(repo, sha)
        registered, registered_why = smd.committed_card_pairs(repo, sha, dotslash=True)
        ctx = {"repo": repo, "sha": sha, "members": members, "pairs": pairs, "pairs_why": pairs_why,
               "registered": registered, "registered_why": registered_why}

        for m in members:
            trailers, _ = parse_trailers(m["text"])
            clauses = {"TRAILER": CLAUSES["TRAILER"](ctx, m, trailers)}
            # The six depend on TRAILER's OUTCOME alone (06 review WR-04): UNMEASURED (absent, duplicate, unparseable)
            # leaves them unmeasured; PASS or a measured FAIL (block not at the end) judges them on the parsed
            # trailers. A TRAILER forced PASS on a card without trailers judges an empty list: SKILL is then a measured
            # FAIL (named skill, no trailer) and the per-trailer clauses read "no trailer", never a crash.
            for cid in CARD_CLAUSES[1:]:
                if clauses["TRAILER"]["outcome"] == UNMEASURED:
                    clauses[cid] = _out(UNMEASURED, "no trailer")
                else:
                    clauses[cid] = CLAUSES[cid](ctx, m, trailers or [])
            result["cards"].append({"card": m["card"], "trailers": trailers, "clauses": clauses})
        for cid in GATE_CLAUSES:
            result["gate"][cid] = CLAUSES[cid](ctx)

        result["verdict"], result["reason"] = fold_verdict(result)
        return result
    except Exception as e:  # noqa: BLE001 -- a judge that crashes must say INCONCLUSIVE, never print a traceback
        return _inconclusive(result.get("head"), f"exception {type(e).__name__}", result)


def fold_verdict(result):
    """(verdict, reason). PASS when every clause is PASS. FAIL when any clause is a measured FAIL, or UNMEASURED for a
    reason that is not git (an absent trailer, a missing source, a zero population). INCONCLUSIVE when every non-PASS
    clause is a git-tagged UNMEASURED: git did not answer, which is not drift (06 review WR-02)."""
    named = [(cid, c) for cid, c in result["gate"].items()]
    named += [(f"{card['card']}:{cid}", c) for card in result["cards"] for cid, c in card["clauses"].items()]
    if not named:
        return FAIL, "no clause judged"
    non_pass = [(k, c) for k, c in named if c["outcome"] != PASS]
    if not non_pass:
        return PASS, ""
    if all(c["outcome"] == UNMEASURED and c.get("git") for _, c in non_pass):
        return "INCONCLUSIVE", "git did not answer in " + ", ".join(sorted(k for k, _ in non_pass))
    return FAIL, ""


def fail_set(result) -> set:
    """{"<card>:<clause>"} for per-card and {"<clause>"} for gate clauses whose outcome is not PASS."""
    out = {cid for cid, c in result.get("gate", {}).items() if c.get("outcome") != PASS}
    for card in result.get("cards", []):
        out |= {f"{card['card']}:{cid}" for cid, c in card["clauses"].items() if c.get("outcome") != PASS}
    return out


# --------------------------------------------------------------------------- CLI

def render(result) -> list:
    lines = []
    for card in result["cards"]:
        skill = ",".join(t["skill"] for t in (card["trailers"] or [])) or "?"
        cl = " ".join(f"{cid}={card['clauses'][cid]['outcome']}" for cid in CARD_CLAUSES)
        lines.append(f"{card['card']} skill={skill} {cl}")
        for cid in CARD_CLAUSES:
            c = card["clauses"][cid]
            if c["outcome"] != PASS:
                lines.append(f"  {cid}: {c['reason']}")
    for cid in GATE_CLAUSES:
        c = result["gate"].get(cid)
        if c is None:
            continue
        lines.append(f"{cid}={c['outcome']}" + (f" ({c['reason']})" if c["reason"] else ""))
    head = (result.get("head") or "none")[:8]
    tail = f"CARD_LINEAGE {result['verdict']} population={len(result['population'])} head={head}"
    if result["verdict"] == "INCONCLUSIVE":
        tail += f" reason={result['reason']}"
    lines.append(tail)
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="compile-out card lineage gate (pillar G)")
    ap.add_argument("--repo", default=str(smd.REPO))
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--trailer-for", metavar="SKILL")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    if a.trailer_for is not None:
        if not SKILL_NAME_RE.fullmatch(a.trailer_for):
            print(f"card_lineage: bad skill name {a.trailer_for!r}", file=sys.stderr)
            return 2
        line, why = trailer_for(repo, a.trailer_for, a.ref)
        if line is None:
            print(f"card_lineage: refused: {why}", file=sys.stderr)
            return 1
        print(line)
        return 0
    result = judge(repo, a.ref)
    if a.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        print("\n".join(render(result)))
    return 0 if result["verdict"] == PASS else 1


if __name__ == "__main__":
    sys.exit(main())
