#!/usr/bin/env python
"""test_card_lineage.py -- pillar G gate (skill-capability, SC-G, decision D-03).

    python3 tools/test_card_lineage.py                     # check (default mode)
    python3 tools/test_card_lineage.py --write-evidence    # render evidence/G-lineage.md (no currency check)

The frozen G rule: a compiled-out card names the skill and commit it was compiled from, and a gate fails when the
source skill changes without the card being re-derived. tools/card_lineage.py is that gate; this file drives it from
both poles and proves that every one of its 10 clauses can change the verdict.

What each V-CLG clause proves:
  V-CLG-LIVE-CLEAN          the live checkout at HEAD judges PASS with an empty fail set
  V-CLG-POSITIVE-CONTROL    the two known cards are population members (population >= 2) and each trailer names
                            the skill skill_coverage.discover_cards finds for that hook in the committed blobs. The
                            two hook paths appear only here and in the drill fixture: a control, not discovery
  V-CLG-DRILL-<id>          one row of the drill table below: the observed (verdict, fail set) equals the declared
                            row EXACTLY (not a subset), so a clause that silently stops evaluating turns a row red
  V-CLG-SUBPROCESS-RED      the CLI exits 1 and names the failing card and clause on a red fixture, exits 0 on a
                            clean one
  V-CLG-GIT-FAILURE         git unavailable (vgm._git_exe raising) is INCONCLUSIVE with no exception escaping, and
                            the judge returns PASS again after restoration
  V-CLG-GIT-FAILURE-MIDJUDGE  one git subcommand failing inside a clause (merge-base, log, cat-file; timeout,
                            rc and OS-error forms) is INCONCLUSIVE with every non-PASS clause git-tagged, never FAIL;
                            the same failure on a red fixture still reads FAIL
  V-CLG-EVERY-CLAUSE        the declared fail sets cover all 10 clauses; forcing each clause PASS flips its
                            singleton drill to PASS (and restoring it flips it back); TRAILER, which has no
                            singleton, is shown load-bearing by a marker-only population on UNLINEAGED-CARD
  V-CLG-EVIDENCE-CURRENT    the COMMITTED blob of evidence/G-lineage.md (CRLF->LF) equals the render of this run
  V-CLG-EVIDENCE-DRILL      the render is accepted, its CRLF copy is accepted, a one-character change is refused

Fixture (DG-07). One base temp git repo is built per run from the HEAD blobs of this checkout (`git show HEAD:`,
committed files only, never the working tree) and copied per drill:
  R  the dispatcher and the two cards, each card with its three lineage lines removed
  A  the two source SKILL.md blobs
  B  each card with its lineage lines appended again, trailer = card_lineage.trailer_for(fixture, skill)
  C  skill_mirror_drift.record_cards(fixture), committed
Fixture git runs with a fixed identity, core.autocrlf=false, commit.gpgsign=false and an empty core.hooksPath (also
written to the repo-local config), so no global hook or signing runs inside a drill.

Drill-table notation (DG-08): a per-card clause is "<card rel>:<CLAUSE>", a gate clause is bare. CW is
hooks/doctrine_cards.js (skill concurrent-writers-shared-tree), DS is hooks/destructive_doctrine_card.js (skill
destructive-state-authorization), ALL7(X) is the seven per-card clauses of card X. "re-recorded" means
record_cards in the copy, then a commit; "refused" means the drill asserts record_cards returned (None, reason)
as its precondition.

This gate writes only under its own temporary directory, plus evidence/G-lineage.md with --write-evidence. It never
edits a skill or hook file of this checkout.

Output lines: `ok   V-CLG-X <evidence>` / `FAIL V-CLG-X <diagnostic>` / `INCONC V-CLG-X <why>`, last line
`CLG_PASS=<passed>/<total>  threshold=<total>/<total>`. Exit 0 only when every clause is ok.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent))
import card_lineage as cl  # noqa: E402
import skill_coverage as sc  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402

REPO = smd.REPO
EVIDENCE_REL = "vault/programs/skill-capability/evidence/G-lineage.md"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
OK, FAIL, INCONC = "ok", "FAIL", "INCONC"
PASS = cl.PASS

CW = "hooks/doctrine_cards.js"
DS = "hooks/destructive_doctrine_card.js"
LINEAGE_COMMENT = "// LINEAGE (skill-capability pillar G)"
GIT_TIMEOUT = 60


def ALL7(card):
    return {f"{card}:{c}" for c in cl.CARD_CLAUSES}


# --------------------------------------------------------------------------- fixture

class FixtureError(Exception):
    """The fixture could not be built. `git` True when the cause is a git failure (every clause INCONC)."""

    def __init__(self, msg, git=False):
        super().__init__(msg)
        self.git = git


def _seed_blob(rel) -> bytes:
    out, why = smd.git_run(REPO, "show", f"HEAD:{rel}")
    if out is None:
        raise FixtureError(f"seed {rel}: {why}", git=True)
    return out


def _strip_lineage(rel, data: bytes):
    """(base text without the three lineage lines, [the two comment lines]) or FixtureError."""
    text = sc.lf(data.decode("utf-8"))
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if len(lines) < 3 or not lines[-3].startswith(LINEAGE_COMMENT) or not lines[-1].startswith(cl.LINEAGE_MARKER):
        raise FixtureError(f"{rel}: last three lines are not the lineage block")
    return "\n".join(lines[:-3]) + "\n", lines[-3:-1]


class Fixture:
    def __init__(self, root: Path):
        self.root = root
        self.hooks_dir = root / "empty-hooks"
        self.hooks_dir.mkdir()
        try:
            self.exe = smd.vgm._git_exe()
        except FileNotFoundError as e:
            raise FixtureError(f"git not found: {e}", git=True) from e
        self.base = root / "base"
        self.info = {}
        self._build()

    # ---- git and files
    def git(self, repo, *a) -> str:
        cmd = [self.exe, "-C", str(repo), "-c", "user.name=clg", "-c", "user.email=clg@invalid",
               "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
               "-c", f"core.hooksPath={self.hooks_dir}", *a]
        p = subprocess.run(cmd, capture_output=True, timeout=GIT_TIMEOUT)
        if p.returncode != 0:
            err = p.stderr.decode("utf-8", "replace").strip().splitlines()
            raise FixtureError(f"git {a[0]} rc={p.returncode}: {err[-1] if err else 'no stderr'}")
        return p.stdout.decode("utf-8", "replace")

    def head(self, repo) -> str:
        return self.git(repo, "rev-parse", "HEAD").strip()

    def commit(self, repo, msg) -> str:
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", msg)
        return self.head(repo)

    @staticmethod
    def read(repo, rel) -> str:
        return (Path(repo) / rel).read_bytes().decode("utf-8")

    @staticmethod
    def write(repo, rel, text, raw=None):
        p = Path(repo) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw if raw is not None else text.encode("utf-8"))

    def rerecord(self, repo):
        """smd.record_cards in the copy (the H re-derivation act); commit when it recorded. (record, reason)."""
        rec, why = smd.record_cards(repo)
        if rec is not None:
            self.commit(repo, "re-record H")
        return rec, why

    # ---- base fixture (DG-07)
    def _build(self):
        disp = _seed_blob(sc.DISPATCHER_REL)
        cards = {}
        for rel in (CW, DS):
            base, comments = _strip_lineage(rel, _seed_blob(rel))
            t, why = cl.parse_trailer(sc.lf(_seed_blob(rel).decode("utf-8")))
            if t is None:
                raise FixtureError(f"{rel}: HEAD trailer {why}")
            cards[rel] = {"base": base, "comments": comments, "skill": t["skill"],
                          "source": f"skills/{t['skill']}/SKILL.md"}
        for rel in (CW, DS):
            cards[rel]["source_bytes"] = _seed_blob(cards[rel]["source"])
        b = self.base
        b.mkdir()
        self.git(b, "init", "-q")
        for k, v in (("user.name", "clg"), ("user.email", "clg@invalid"), ("core.autocrlf", "false"),
                     ("commit.gpgsign", "false"), ("core.hooksPath", str(self.hooks_dir))):
            self.git(b, "config", k, v)
        self.write(b, sc.DISPATCHER_REL, None, raw=disp)
        for rel in (CW, DS):
            self.write(b, rel, cards[rel]["base"])
        R = self.commit(b, "R: dispatcher + cards without lineage")
        for rel in (CW, DS):
            self.write(b, cards[rel]["source"], None, raw=cards[rel]["source_bytes"])
        A = self.commit(b, "A: source skills")
        for rel in (CW, DS):
            line, why = cl.trailer_for(b, cards[rel]["skill"])
            if line is None:
                raise FixtureError(f"trailer_for {cards[rel]['skill']}: {why}")
            cards[rel]["trailer_line"] = line
            self.write(b, rel, cards[rel]["base"] + "\n".join(cards[rel]["comments"] + [line]) + "\n")
        B = self.commit(b, "B: cards with lineage trailers")
        rec, why = smd.record_cards(b)
        if rec is None:
            raise FixtureError(f"record_cards on the base fixture refused: {why}")
        C = self.commit(b, "C: H record")
        self.info = {"R": R, "A": A, "B": B, "C": C, "cards": cards}

    def fresh(self, name) -> Path:
        dst = self.root / "drills" / name
        shutil.copytree(self.base, dst, symlinks=True)
        return dst

    # ---- card helpers
    def skill(self, card):
        return self.info["cards"][card]["skill"]

    def source(self, card):
        return self.info["cards"][card]["source"]

    def marker_lines(self, repo, card):
        return [ln for ln in sc.lf(self.read(repo, card)).split("\n") if ln.startswith(cl.LINEAGE_MARKER)]

    def replace_marker(self, repo, card, new_lines):
        """Replace the single marker line of `card` by `new_lines` (a list; [] deletes it)."""
        text = sc.lf(self.read(repo, card))
        lines = text.split("\n")
        idx = [i for i, ln in enumerate(lines) if ln.startswith(cl.LINEAGE_MARKER)]
        if len(idx) != 1:
            raise FixtureError(f"{card}: expected one marker line, found {len(idx)}")
        lines[idx[0]:idx[0] + 1] = new_lines
        self.write(repo, card, "\n".join(lines))

    def set_trailer(self, repo, card, **fields):
        (line,) = self.marker_lines(repo, card)
        t, why = cl.parse_trailer(line)
        if t is None:
            raise FixtureError(f"{card}: trailer {why}")
        t.update(fields)
        self.replace_marker(repo, card, [f"{cl.LINEAGE_MARKER} skill={t['skill']} source={t['source']} "
                                         f"sha256={t['sha256']} commit={t['commit']}"])

    def trailer(self, repo, card):
        (line,) = self.marker_lines(repo, card)
        return cl.parse_trailer(line)[0]

    def change_source_first_byte(self, repo, card) -> bytes:
        p = Path(repo) / self.source(card)
        data = p.read_bytes()
        new = (b"X" if data[:1] != b"X" else b"Y") + data[1:]
        p.write_bytes(new)
        return new


def observed(repo):
    r = cl.judge(repo)
    return r["verdict"], cl.fail_set(r), r


def _reasons(result) -> str:
    out = [f"{cid}: {c['reason']}" for cid, c in result.get("gate", {}).items() if c.get("outcome") != PASS]
    for card in result.get("cards", []):
        out += [f"{card['card']}:{cid}: {c['reason']}" for cid, c in card["clauses"].items()
                if c.get("outcome") != PASS]
    if result.get("verdict") == "INCONCLUSIVE":
        out.append(f"reason: {result.get('reason')}")
    return "; ".join(out)


# --------------------------------------------------------------------------- drills (mutations)
# Each mutation takes (fx, repo) and returns None, or a precondition failure string.

def m_clean(fx, repo):
    return None


def m_source_changed_rerecorded(fx, repo):
    fx.change_source_first_byte(repo, CW)
    fx.commit(repo, "source v2")
    rec, why = fx.rerecord(repo)
    return None if rec is not None else f"re-record refused: {why}"


def m_source_changed_raw(fx, repo):
    fx.change_source_first_byte(repo, CW)
    fx.commit(repo, "source v2")
    return None


def m_rederived(fx, repo):
    m_source_changed_raw(fx, repo)
    line, why = cl.trailer_for(repo, fx.skill(CW))
    if line is None:
        return f"trailer_for refused: {why}"
    fx.replace_marker(repo, CW, [line])
    fx.commit(repo, "re-derive CW trailer")
    rec, why = fx.rerecord(repo)
    return None if rec is not None else f"re-record refused: {why}"


def _rerecorded(fx, repo, msg):
    fx.commit(repo, msg)
    rec, why = fx.rerecord(repo)
    return None if rec is not None else f"re-record refused: {why}"


def m_trailer_sha_digit(fx, repo):
    sha = fx.trailer(repo, CW)["sha256"]
    fx.set_trailer(repo, CW, sha256=("0" if sha[0] != "0" else "1") + sha[1:])
    return _rerecorded(fx, repo, "CW trailer sha digit")


def m_trailer_absent(fx, repo):
    fx.replace_marker(repo, DS, [])
    return _rerecorded(fx, repo, "DS trailer deleted")


def m_trailer_duplicate(fx, repo):
    (line,) = fx.marker_lines(repo, DS)
    fx.replace_marker(repo, DS, [line, line])
    return _rerecorded(fx, repo, "DS trailer duplicated")


def m_trailer_unparseable(fx, repo):
    sha = fx.trailer(repo, DS)["sha256"]
    fx.set_trailer(repo, DS, sha256=sha[:63])
    return _rerecorded(fx, repo, "DS trailer sha 63 hex")


def m_skill_mismatch(fx, repo):
    line, why = cl.trailer_for(repo, fx.skill(DS))
    if line is None:
        return f"trailer_for refused: {why}"
    fx.replace_marker(repo, CW, [line])
    return _rerecorded(fx, repo, "CW trailer names DS skill")


def m_source_path(fx, repo):
    ds = fx.trailer(repo, DS)
    fx.set_trailer(repo, CW, skill=fx.skill(CW), source=fx.source(DS), sha256=ds["sha256"], commit=fx.info["A"])
    return _rerecorded(fx, repo, "CW trailer source path of DS")


def m_ghost_skill(fx, repo):
    text = fx.read(repo, CW)
    pat = re.compile(r"`" + re.escape(fx.skill(CW)) + r"`(\s+skill\b)")
    new, n = pat.subn(r"`ghost-skill`\1", text, count=1)
    if n != 1:
        return f"CARD_TOKEN occurrence of {fx.skill(CW)} not found"
    fx.write(repo, CW, new)
    fx.set_trailer(repo, CW, skill="ghost-skill", source="skills/ghost-skill/SKILL.md")
    fx.commit(repo, "CW renamed to ghost-skill")
    rec, why = smd.record_cards(repo)
    return None if rec is None else "re-record was expected to be refused, but it recorded"


def m_commit_unknown(fx, repo):
    fx.set_trailer(repo, CW, commit="deadbeef" * 5)
    return _rerecorded(fx, repo, "CW trailer commit unknown")


def m_commit_not_ancestor(fx, repo):
    src = fx.source(CW)
    data = (Path(repo) / src).read_bytes()
    fx.git(repo, "checkout", "-q", "-b", "side", fx.info["R"])
    fx.write(repo, src, None, raw=data)
    S = fx.commit(repo, "S: source on a side branch")
    fx.git(repo, "checkout", "-q", "-")
    fx.set_trailer(repo, CW, commit=S)
    return _rerecorded(fx, repo, "CW trailer commit on a side branch")


def m_commit_not_touching(fx, repo):
    fx.set_trailer(repo, CW, commit=fx.info["C"])
    return _rerecorded(fx, repo, "CW trailer commit = record commit")


def m_commit_wrong_digest(fx, repo):
    new = fx.change_source_first_byte(repo, CW)
    fx.commit(repo, "V: source changed")
    fx.set_trailer(repo, CW, sha256=smd.vgm._norm_sha(new), commit=fx.info["A"])
    return _rerecorded(fx, repo, "CW trailer new digest, commit A")


def m_floor_one(fx, repo):
    (Path(repo) / DS).unlink()
    fx.commit(repo, "DS removed")
    rec, why = fx.rerecord(repo)
    if rec is None:
        return f"re-record refused: {why}"
    return None if len(rec["pairs"]) == 1 else f"re-record holds {len(rec['pairs'])} pairs, not 1"


def m_floor_zero(fx, repo):
    (Path(repo) / DS).unlink()
    (Path(repo) / CW).unlink()
    fx.commit(repo, "both cards removed")
    rec, why = smd.record_cards(repo)
    return None if rec is None else "re-record was expected to be refused, but it recorded"


NEW_CARD = "hooks/new_card.js"
DEEP_CARD = "hooks/tests/deep_card.js"
SUB_CARD = "hooks/_shared/sub_card.js"
DOT_CARD = "hooks/tests/fixtures/dot_card.js"


def m_unlineaged_card(fx, repo):
    fx.write(repo, NEW_CARD, f"// read the `{fx.skill(CW)}` skill before committing (unlineaged drill card)\n")
    fx.commit(repo, "unlineaged card")
    return None


def m_dispatcher_uncovered(fx, repo):
    fx.write(repo, DEEP_CARD, fx.read(repo, CW))
    text = fx.read(repo, sc.DISPATCHER_REL)
    lines = text.split("\n")
    idx = [i for i, ln in enumerate(lines) if f"{CW}'" in ln]
    if len(idx) != 1:
        return f"dispatcher lines registering {CW}: {len(idx)}, expected 1"
    lines.insert(idx[0] + 1, lines[idx[0]].replace(CW, DEEP_CARD))
    fx.write(repo, sc.DISPATCHER_REL, "\n".join(lines))
    fx.commit(repo, "deep card registered")
    rec, why = fx.rerecord(repo)
    if rec is None:
        return f"re-record refused: {why}"
    return None if len(rec["pairs"]) == 3 else f"re-record holds {len(rec['pairs'])} pairs, not 3"


def _register_dotslash(fx, repo, card, text):
    """Write `card` and register it next to CW with the dispatcher's own-directory shape `./<rel>` (no re-record:
    pillar H's parser reads only the `../skills/claude-power-pack/` shape, so its record does not move)."""
    fx.write(repo, card, text)
    lines = fx.read(repo, sc.DISPATCHER_REL).split("\n")
    idx = [i for i, ln in enumerate(lines) if f"{CW}'" in ln]
    if len(idx) != 1:
        return f"dispatcher lines registering {CW}: {len(idx)}, expected 1"
    rel = card[len("hooks/"):]
    lines.insert(idx[0] + 1, f"    {{ exe: NODE_EXE, script: './{rel}', timeoutMs: 5000 }},")
    fx.write(repo, sc.DISPATCHER_REL, "\n".join(lines))
    fx.commit(repo, f"{card} registered as ./{rel}")
    regs = sc.registered_hooks(fx.read(repo, sc.DISPATCHER_REL), dotslash=True)
    return None if card in regs else f"{card} not parsed as a registration"


def m_subdir_card_dotslash(fx, repo):
    text = fx.read(repo, CW).replace(cl.LINEAGE_MARKER, "// was-COMPILED-FROM:")
    return _register_dotslash(fx, repo, SUB_CARD, text)


def m_dispatcher_uncovered_dotslash(fx, repo):
    return _register_dotslash(fx, repo, DOT_CARD, fx.read(repo, CW))


def m_card_edit_unrecorded(fx, repo):
    fx.write(repo, CW, fx.read(repo, CW) + "// appended after the trailer (drill)\n")
    fx.commit(repo, "CW edited after the trailer")
    return None


def m_record_unparseable(fx, repo):
    fx.write(repo, smd.CARD_RECORD_REL, "{")
    fx.commit(repo, "record unparseable")
    return None


def m_crlf(fx, repo):
    for rel in (fx.source(CW), CW, DS, sc.DISPATCHER_REL, smd.CARD_RECORD_REL):
        p = Path(repo) / rel
        p.write_bytes(smd.lf_bytes(p.read_bytes()).replace(b"\n", b"\r\n"))
    fx.commit(repo, "CRLF")
    blob, why = smd.git_run(repo, "cat-file", "blob", f"HEAD:{fx.source(CW)}")
    if blob is None:
        return f"committed source unreadable: {why}"
    return None if b"\r\n" in blob else "committed CW SKILL.md blob carries no CR LF"


def m_worktree_only(fx, repo):
    fx.change_source_first_byte(repo, CW)
    fx.replace_marker(repo, DS, [])
    st = fx.git(repo, "status", "--porcelain")
    return None if st.strip() else "working tree is clean (the edit did not land)"


THIRD = "third-skill"


def _add_third(fx, repo, trailer):
    """A second skill the CW card names in CARD_TOKEN form (a "see also" pointer above the lineage block), with its
    own trailer appended to the lineage block when `trailer`; committed and H re-recorded. None or a precondition."""
    fx.write(repo, f"skills/{THIRD}/SKILL.md", f"---\nname: {THIRD}\n---\nrule v1\n")
    fx.commit(repo, "third skill")
    lines = sc.lf(fx.read(repo, CW)).split("\n")
    i = next(k for k, ln in enumerate(lines) if ln.startswith(LINEAGE_COMMENT))
    lines.insert(i, f"// see also the `{THIRD}` skill for the companion rule (drill)")
    if trailer:
        line, why = cl.trailer_for(repo, THIRD)
        if line is None:
            return f"trailer_for {THIRD} refused: {why}"
        j = max(k for k, ln in enumerate(lines) if ln.startswith(cl.LINEAGE_MARKER))
        lines.insert(j + 1, line)
    fx.write(repo, CW, "\n".join(lines))
    fx.commit(repo, f"CW names {THIRD}" + (" with its trailer" if trailer else ""))
    rec, why = fx.rerecord(repo)
    if rec is None:
        return f"re-record refused: {why}"
    return None if len(rec["pairs"]) == 3 else f"re-record holds {len(rec['pairs'])} pairs, not 3"


def m_multi_skill_lineaged(fx, repo):
    return _add_third(fx, repo, trailer=True)


def m_multi_skill_rerecorded(fx, repo):
    pre = _add_third(fx, repo, trailer=True)
    if pre is not None:
        return pre
    v, fs, _ = observed(repo)
    if v != PASS:
        return f"before the {THIRD} change the card judges {v} {_fmt(fs)}, not PASS"
    fx.write(repo, f"skills/{THIRD}/SKILL.md", f"---\nname: {THIRD}\n---\nrule v2, changed\n")
    fx.commit(repo, f"{THIRD} changed")
    rec, why = fx.rerecord(repo)
    return None if rec is not None else f"re-record refused: {why}"


def m_multi_skill_unlineaged(fx, repo):
    return _add_third(fx, repo, trailer=False)


def m_merge_rederived(fx, repo):
    """CW's SKILL.md edited on two branches and the conflict resolved inside the merge, so the merge commit is the only
    commit carrying the merged blob; the trailer is then re-derived with trailer_for (which names the merge) and H
    re-recorded. The tool's own trailer must be accepted."""
    src = fx.source(CW)
    p = Path(repo) / src
    main = fx.git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    fx.git(repo, "checkout", "-q", "-b", "side")
    p.write_bytes(b"side\n" + p.read_bytes())
    fx.commit(repo, "side edit")
    fx.git(repo, "checkout", "-q", main)
    base = p.read_bytes()
    p.write_bytes(b"main\n" + base)
    fx.commit(repo, "main edit")
    try:
        fx.git(repo, "merge", "-q", "--no-ff", "side", "-m", "merge")
        return "the merge did not conflict"
    except FixtureError:
        pass
    p.write_bytes(b"resolved\n" + base)
    fx.git(repo, "add", src)
    fx.git(repo, "commit", "-q", "-m", "merge resolved in SKILL.md")
    merge = fx.head(repo)
    if len(fx.git(repo, "log", "-1", "--format=%P").split()) != 2:
        return "HEAD is not a merge"
    line, why = cl.trailer_for(repo, fx.skill(CW))
    if line is None:
        return f"trailer_for refused: {why}"
    if not line.endswith(f"commit={merge}"):
        return f"trailer_for did not name the merge {merge[:8]}: {line.split('commit=')[-1][:8]}"
    fx.replace_marker(repo, CW, [line])
    fx.commit(repo, "re-derive CW trailer (merge)")
    rec, why = fx.rerecord(repo)
    return None if rec is not None else f"re-record refused: {why}"


def m_shallow_clone(fx, repo):
    """The judged checkout is a depth-1 clone of the clean fixture: the trailer commits are real ancestors that the
    clone does not hold. Missing history is not drift."""
    full = repo.with_name(repo.name + "-full")
    shutil.move(str(repo), str(full))
    fx.git(full.parent, "clone", "-q", "--depth", "1", f"file://{full}", str(repo))
    out = fx.git(repo, "rev-parse", "--is-shallow-repository").strip()
    return None if out == "true" else f"clone is not shallow ({out})"


def _drill_table():
    return [
        ("CLEAN", m_clean, set(), "PASS"),
        ("SOURCE-CHANGED-RERECORDED", m_source_changed_rerecorded, {f"{CW}:SOURCE-CURRENT"}, "FAIL"),
        ("SOURCE-CHANGED-RAW", m_source_changed_raw, {f"{CW}:SOURCE-CURRENT", "H-RECORD-CURRENT"}, "FAIL"),
        ("REDERIVED", m_rederived, set(), "PASS"),
        ("MERGE-REDERIVED", m_merge_rederived, set(), "PASS"),
        ("MULTI-SKILL-LINEAGED", m_multi_skill_lineaged, set(), "PASS"),
        ("MULTI-SKILL-RERECORDED", m_multi_skill_rerecorded, {f"{CW}:SOURCE-CURRENT"}, "FAIL"),
        ("MULTI-SKILL-UNLINEAGED", m_multi_skill_unlineaged, {f"{CW}:SKILL"}, "FAIL"),
        ("TRAILER-SHA-DIGIT", m_trailer_sha_digit, {f"{CW}:SOURCE-CURRENT", f"{CW}:COMMIT-DIGEST"}, "FAIL"),
        ("TRAILER-ABSENT", m_trailer_absent, ALL7(DS), "FAIL"),
        ("TRAILER-DUPLICATE", m_trailer_duplicate, ALL7(DS), "FAIL"),
        ("TRAILER-UNPARSEABLE", m_trailer_unparseable, ALL7(DS), "FAIL"),
        ("SKILL-MISMATCH", m_skill_mismatch, {f"{CW}:SKILL"}, "FAIL"),
        ("SOURCE-PATH", m_source_path, {f"{CW}:SOURCE-PATH"}, "FAIL"),
        ("GHOST-SKILL", m_ghost_skill, {f"{CW}:SOURCE-CURRENT", f"{CW}:COMMIT-TOUCHES", f"{CW}:COMMIT-DIGEST",
                                        "H-RECORD-CURRENT"}, "FAIL"),
        ("COMMIT-UNKNOWN", m_commit_unknown, {f"{CW}:COMMIT-ANCESTOR", f"{CW}:COMMIT-TOUCHES",
                                              f"{CW}:COMMIT-DIGEST"}, "FAIL"),
        ("SHALLOW-CLONE", m_shallow_clone, {f"{c}:{k}" for c in (CW, DS)
                                            for k in ("COMMIT-ANCESTOR", "COMMIT-TOUCHES", "COMMIT-DIGEST")},
         "INCONCLUSIVE"),
        ("COMMIT-NOT-ANCESTOR", m_commit_not_ancestor, {f"{CW}:COMMIT-ANCESTOR"}, "FAIL"),
        ("COMMIT-NOT-TOUCHING", m_commit_not_touching, {f"{CW}:COMMIT-TOUCHES"}, "FAIL"),
        ("COMMIT-WRONG-DIGEST", m_commit_wrong_digest, {f"{CW}:COMMIT-DIGEST"}, "FAIL"),
        ("FLOOR-ONE", m_floor_one, {"FLOOR"}, "FAIL"),
        ("FLOOR-ZERO", m_floor_zero, {"FLOOR", "DISPATCHER-COVERED", "H-RECORD-CURRENT"}, "FAIL"),
        ("UNLINEAGED-CARD", m_unlineaged_card, ALL7(NEW_CARD), "FAIL"),
        ("DISPATCHER-UNCOVERED", m_dispatcher_uncovered, {"DISPATCHER-COVERED"}, "FAIL"),
        ("DISPATCHER-UNCOVERED-DOTSLASH", m_dispatcher_uncovered_dotslash, {"DISPATCHER-COVERED"}, "FAIL"),
        ("SUBDIR-CARD-DOTSLASH", m_subdir_card_dotslash, ALL7(SUB_CARD), "FAIL"),
        ("CARD-EDIT-UNRECORDED", m_card_edit_unrecorded, {"H-RECORD-CURRENT"}, "FAIL"),
        ("RECORD-UNPARSEABLE", m_record_unparseable, {"H-RECORD-CURRENT"}, "FAIL"),
        ("CRLF", m_crlf, set(), "PASS"),
        ("WORKTREE-ONLY", m_worktree_only, set(), "PASS"),
    ]


# Singleton drill per clause (V-CLG-EVERY-CLAUSE). TRAILER has none by construction: its failure leaves the other
# six per-card clauses unmeasurable, so its proof is the marker-only population on UNLINEAGED-CARD.
SINGLETON = {
    "SOURCE-CURRENT": "SOURCE-CHANGED-RERECORDED",
    "SKILL": "SKILL-MISMATCH",
    "SOURCE-PATH": "SOURCE-PATH",
    "COMMIT-ANCESTOR": "COMMIT-NOT-ANCESTOR",
    "COMMIT-TOUCHES": "COMMIT-NOT-TOUCHING",
    "COMMIT-DIGEST": "COMMIT-WRONG-DIGEST",
    "FLOOR": "FLOOR-ONE",
    "DISPATCHER-COVERED": "DISPATCHER-UNCOVERED",
    "H-RECORD-CURRENT": "CARD-EDIT-UNRECORDED",
}
TRAILER_DRILL = "UNLINEAGED-CARD"

# Clauses that must be UNMEASURED (not a measured FAIL) in a drill: an absent, duplicate or unparseable trailer, a
# zero population and empty dispatcher card set, an unreadable record, and a missing source.
UNMEASURED_EXPECT = {
    "TRAILER-ABSENT": ALL7(DS),
    "TRAILER-DUPLICATE": ALL7(DS),
    "TRAILER-UNPARSEABLE": ALL7(DS),
    "UNLINEAGED-CARD": ALL7(NEW_CARD),
    "SUBDIR-CARD-DOTSLASH": ALL7(SUB_CARD),
    "FLOOR-ZERO": {"FLOOR", "DISPATCHER-COVERED"},
    "RECORD-UNPARSEABLE": {"H-RECORD-CURRENT"},
    "GHOST-SKILL": {f"{CW}:SOURCE-CURRENT"},
    "COMMIT-UNKNOWN": {f"{CW}:COMMIT-TOUCHES", f"{CW}:COMMIT-DIGEST"},
    "SHALLOW-CLONE": {f"{c}:{k}" for c in (CW, DS) for k in ("COMMIT-ANCESTOR", "COMMIT-TOUCHES", "COMMIT-DIGEST")},
}
# Clauses that must be a MEASURED FAIL (not UNMEASURED) in a drill: a trailer commit absent from a complete history
# cannot be an ancestor (only a shallow clone makes absence unmeasurable, SHALLOW-CLONE).
FAIL_EXPECT = {
    "COMMIT-UNKNOWN": {f"{CW}:COMMIT-ANCESTOR"},
}


def run_drills(fx):
    """{id: {declared, declared_verdict, verdict, fail_set, repo, pre, result, error}}"""
    out = {}
    for did, mut, declared, dverdict in _drill_table():
        row = {"declared": declared, "declared_verdict": dverdict, "verdict": None, "fail_set": None,
               "repo": None, "pre": None, "result": None, "error": None}
        try:
            repo = fx.fresh(did)
            row["repo"] = repo
            row["pre"] = mut(fx, repo)
            if row["pre"] is None:
                row["verdict"], row["fail_set"], row["result"] = observed(repo)
        except Exception as e:  # noqa: BLE001 -- a drill that cannot build is FAIL, never a traceback
            row["error"] = f"{type(e).__name__}: {e}"
        out[did] = row
    return out


def outcomes(result) -> dict:
    """{"<card>:<CLAUSE>" | "<CLAUSE>": outcome} in fail_set notation."""
    out = {cid: c.get("outcome") for cid, c in (result or {}).get("gate", {}).items()}
    for card in (result or {}).get("cards", []):
        out.update({f"{card['card']}:{cid}": c.get("outcome") for cid, c in card["clauses"].items()})
    return out


def unmeasured_mismatch(did, row) -> list:
    """Members of UNMEASURED_EXPECT[did] whose outcome is not UNMEASURED (a measured FAIL where the judge could not
    measure would be a different defect wearing the same fail set)."""
    got = outcomes(row["result"])
    return sorted([k for k in UNMEASURED_EXPECT.get(did, set()) if got.get(k) != cl.UNMEASURED]
                  + [f"{k} (expected a measured FAIL)" for k in FAIL_EXPECT.get(did, set()) if got.get(k) != cl.FAIL])


def drill_ok(row, did=None) -> bool:
    return (row["error"] is None and row["pre"] is None and row["verdict"] == row["declared_verdict"]
            and row["fail_set"] == row["declared"] and not (did and unmeasured_mismatch(did, row)))


def _fmt(s) -> str:
    return "{" + ", ".join(sorted(s)) + "}" if s is not None else "none"


# --------------------------------------------------------------------------- clauses

def c_live_clean(st):
    r = st["live"]
    fs = cl.fail_set(r)
    if r["verdict"] == PASS and not fs:
        return [(OK, "V-CLG-LIVE-CLEAN", f"HEAD judges PASS, population={len(r['population'])}, fail set empty")]
    status = INCONC if r["verdict"] == "INCONCLUSIVE" else FAIL
    return [(status, "V-CLG-LIVE-CLEAN", f"verdict={r['verdict']} fail set {_fmt(fs)}; {_reasons(r)}")]


def c_positive_control(st):
    r = st["live"]
    head = r.get("head")
    if not head:
        return [(INCONC, "V-CLG-POSITIVE-CONTROL", f"HEAD not judged: {r.get('reason')}")]
    disp, why = smd.git_run(REPO, "cat-file", "blob", f"{head}:{sc.DISPATCHER_REL}")
    if disp is None:
        return [(INCONC, "V-CLG-POSITIVE-CONTROL", f"dispatcher blob: {why}")]
    texts = {}
    for rel in (CW, DS):
        data, why = smd.git_run(REPO, "cat-file", "blob", f"{head}:{rel}")
        if data is None:
            return [(INCONC, "V-CLG-POSITIVE-CONTROL", f"{rel} blob: {why}")]
        texts[rel] = data.decode("utf-8", "replace")
    found = {}
    for c in sc.discover_cards(REPO, disp.decode("utf-8", "replace"), hook_texts=texts, read_disk=False):
        found.setdefault(c["hook"], set()).add(c["skill"])
    pop = set(r["population"])
    trailers = {c["card"]: {t["skill"] for t in (c["trailers"] or [])} for c in r["cards"]}
    bad = []
    if len(pop) < 2:
        bad.append(f"population size {len(pop)} < 2")
    for rel in (CW, DS):
        if rel not in pop:
            bad.append(f"{rel} not a population member")
        elif not found.get(rel) or found.get(rel) != trailers.get(rel):
            bad.append(f"{rel}: trailer skills {sorted(trailers.get(rel) or [])} vs discovered "
                       f"{sorted(found.get(rel, set()))}")
    if bad:
        return [(FAIL, "V-CLG-POSITIVE-CONTROL", "; ".join(bad))]
    return [(OK, "V-CLG-POSITIVE-CONTROL", f"population={len(pop)} holds both known cards; trailer skills "
                                           f"{','.join(sorted(trailers[CW]))}, {','.join(sorted(trailers[DS]))} "
                                           f"equal discover_cards")]


def c_drills(st):
    out = []
    for did, row in st["drills"].items():
        cid = f"V-CLG-DRILL-{did}"
        if row["error"] is not None:
            out.append((FAIL, cid, f"drill did not build: {row['error']}"))
        elif row["pre"] is not None:
            out.append((FAIL, cid, f"precondition: {row['pre']}"))
        elif drill_ok(row, did):
            out.append((OK, cid, f"{row['verdict']} {_fmt(row['fail_set'])}"))
        elif row["fail_set"] == row["declared"] and row["verdict"] == row["declared_verdict"]:
            out.append((FAIL, cid, f"fail set matches but not UNMEASURED: {unmeasured_mismatch(did, row)} | "
                                   f"{_reasons(row['result'])}"))
        else:
            out.append((FAIL, cid, f"declared {row['declared_verdict']} {_fmt(row['declared'])} | observed "
                                   f"{row['verdict']} {_fmt(row['fail_set'])} | {_reasons(row['result'])}"))
    return out


def _cli(repo):
    p = subprocess.run([sys.executable, str(Path(cl.__file__).resolve()), "--repo", str(repo)],
                       capture_output=True, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def c_subprocess_red(st):
    red, clean = st["drills"].get("SOURCE-CHANGED-RERECORDED"), st["drills"].get("CLEAN")
    if not red or not clean or red["repo"] is None or clean["repo"] is None:
        return [(FAIL, "V-CLG-SUBPROCESS-RED", "drill repos missing")]
    rc_r, out_r = _cli(red["repo"])
    rc_c, out_c = _cli(clean["repo"])
    last_r = out_r.rstrip("\n").split("\n")[-1] if out_r.strip() else ""
    last_c = out_c.rstrip("\n").split("\n")[-1] if out_c.strip() else ""
    red_ok = rc_r == 1 and CW in out_r and "SOURCE-CURRENT=FAIL" in out_r and last_r.startswith("CARD_LINEAGE FAIL")
    clean_ok = rc_c == 0 and last_c.startswith("CARD_LINEAGE PASS")
    if red_ok and clean_ok:
        return [(OK, "V-CLG-SUBPROCESS-RED", f"red fixture rc=1 '{last_r.split(' head=')[0]}' naming {CW} "
                                             f"SOURCE-CURRENT=FAIL; clean fixture rc=0")]
    return [(FAIL, "V-CLG-SUBPROCESS-RED", f"red rc={rc_r} last={last_r!r} names_card={CW in out_r} "
                                           f"clause={'SOURCE-CURRENT=FAIL' in out_r}; clean rc={rc_c} last={last_c!r}")]


def c_git_failure(st):
    clean = st["drills"].get("CLEAN")
    if not clean or clean["repo"] is None:
        return [(FAIL, "V-CLG-GIT-FAILURE", "CLEAN drill repo missing")]
    orig = smd.vgm._git_exe

    def gone():
        raise FileNotFoundError("git executable not found (drill)")
    err, live, fixture = None, {}, {}
    smd.vgm._git_exe = gone
    try:
        live, fixture = cl.judge(REPO), cl.judge(clean["repo"])
    except Exception as e:  # noqa: BLE001 -- the clause asserts that nothing escapes
        err = f"{type(e).__name__}: {e}"
    finally:
        smd.vgm._git_exe = orig
    after = cl.judge(clean["repo"])["verdict"]
    both = [(r.get("verdict"), "git not found" in str(r.get("reason"))) for r in (live, fixture)]
    st["git_failure"] = {"live": live.get("verdict"), "fixture": fixture.get("verdict"), "restored": after}
    if err is None and both == [("INCONCLUSIVE", True)] * 2 and after == PASS:
        return [(OK, "V-CLG-GIT-FAILURE", "git missing: live and fixture judge INCONCLUSIVE ('git not found'), no "
                                          "exception escaped; restored judge PASS")]
    return [(FAIL, "V-CLG-GIT-FAILURE", f"escaped={err}; live={live.get('verdict')}/{live.get('reason')}; "
                                        f"fixture={fixture.get('verdict')}/{fixture.get('reason')}; restored={after}")]


MIDJUDGE_STUBS = (
    ("merge-base", "git merge-base failed: timed out after 30 seconds"),
    ("log", "git log rc=128: fatal: unable to read tree (drill)"),
    ("cat-file", "git cat-file failed: [Errno 5] Input/output error (drill)"),
)


def _judge_with_failing(repo, sub, why):
    """cl.judge with smd.git_run failing for one git subcommand only (after discovery, which reads via batch)."""
    orig = smd.git_run

    def flaky(r, *a, **k):
        if a and a[0] == sub:
            return None, why
        return orig(r, *a, **k)
    smd.git_run = flaky
    try:
        return cl.judge(repo)
    finally:
        smd.git_run = orig


def c_git_failure_midjudge(st):
    """A git failure inside a clause (after discovery) is INCONCLUSIVE, never FAIL: every non-PASS clause is
    git-tagged and the verdict says INCONCLUSIVE. A measured FAIL still dominates (red control)."""
    clean, red = st["drills"].get("CLEAN"), st["drills"].get("SOURCE-CHANGED-RERECORDED")
    if not clean or not red or clean["repo"] is None or red["repo"] is None:
        return [(FAIL, "V-CLG-GIT-FAILURE-MIDJUDGE", "drill repos missing")]
    bad, seen = [], []
    for sub, why in MIDJUDGE_STUBS:
        r = _judge_with_failing(clean["repo"], sub, why)
        fs = cl.fail_set(r)
        non_pass = [c for c in outcomes(r).items() if c[1] != PASS]
        tail = cl.render(r)[-1]
        seen.append(f"{sub}: {r['verdict']} {len(fs)} clause(s)")
        if r["verdict"] != "INCONCLUSIVE" or not fs or any(o == cl.FAIL for _, o in non_pass) \
                or not tail.startswith("CARD_LINEAGE INCONCLUSIVE"):
            bad.append(f"{sub}: verdict {r['verdict']} {_fmt(fs)} last={tail!r}")
    r = _judge_with_failing(red["repo"], "merge-base", MIDJUDGE_STUBS[0][1])
    if r["verdict"] != cl.FAIL or f"{CW}:SOURCE-CURRENT" not in cl.fail_set(r):
        bad.append(f"red control: merge-base failure on SOURCE-CHANGED-RERECORDED gave {r['verdict']}")
    after = cl.judge(clean["repo"])["verdict"]
    if after != PASS:
        bad.append(f"restored judge gave {after}")
    st["git_midjudge"] = seen
    if bad:
        return [(FAIL, "V-CLG-GIT-FAILURE-MIDJUDGE", "; ".join(bad))]
    return [(OK, "V-CLG-GIT-FAILURE-MIDJUDGE", "; ".join(seen) + "; a measured FAIL dominates (red control); "
                                                  "restored judge PASS")]


def _forced(ctx, member=None, trailer=None):
    return {"outcome": "PASS", "reason": "forced (drill)"}


def c_every_clause(st):
    drills = st["drills"]
    table = {did: (declared, dv) for did, _, declared, dv in _drill_table()}
    ids = set(cl.CARD_CLAUSES) | set(cl.GATE_CLAUSES)
    union = {d.split(":")[-1] for declared, _ in table.values() for d in declared}
    problems = []
    if union != ids or len(ids) != 10:
        problems.append(f"coverage: declared union {sorted(union)} vs clauses {sorted(ids)}")
    flips = []
    for cid, did in SINGLETON.items():
        row = drills.get(did)
        declared = table.get(did, (set(), None))[0]
        if {d.split(":")[-1] for d in declared} != {cid} or len(declared) != 1:
            problems.append(f"{cid}: drill {did} is not a singleton for it ({_fmt(declared)})")
            continue
        if not row or not drill_ok(row, did):
            problems.append(f"{cid}: drill {did} itself is not ok")
            continue
        orig = cl.CLAUSES[cid]
        cl.CLAUSES[cid] = _forced
        try:
            forced = cl.judge(row["repo"])["verdict"]
        finally:
            cl.CLAUSES[cid] = orig
        restored = cl.judge(row["repo"])["verdict"]
        flips.append((cid, did, forced, restored))
        if forced != PASS or restored != "FAIL":
            problems.append(f"{cid}: forced PASS gave {did}={forced}, restored gave {restored} (not load-bearing)")
    row = drills.get(TRAILER_DRILL)
    if not row or not drill_ok(row, TRAILER_DRILL):
        problems.append(f"TRAILER: drill {TRAILER_DRILL} itself is not ok")
    else:
        orig_pop = cl.population

        def marker_only(repo, sha, tracked):
            members, why = orig_pop(repo, sha, tracked)
            if members is None:
                return members, why
            return [m for m in members if cl.LINEAGE_MARKER in m["text"]], why
        cl.population = marker_only
        try:
            forced = cl.judge(row["repo"])["verdict"]
        finally:
            cl.population = orig_pop
        restored = cl.judge(row["repo"])["verdict"]
        flips.append(("TRAILER", TRAILER_DRILL, forced, restored))
        if forced != PASS or restored != "FAIL":
            problems.append(f"TRAILER: marker-only population gave {forced}, restored gave {restored}")
    st["flips"] = flips
    if problems:
        return [(FAIL, "V-CLG-EVERY-CLAUSE", "; ".join(problems))]
    return [(OK, "V-CLG-EVERY-CLAUSE", f"declared sets cover all {len(ids)} clauses; {len(flips)} forced passes "
                                       f"flipped their drill FAIL->PASS and back on restore")]


# --------------------------------------------------------------------------- evidence (G-lineage.md)

CLAUSE_TEXT = {
    "TRAILER": "at least one `// COMPILED-FROM:` line in the card, every one parses, and no skill has two; absent, "
               "a duplicate skill or an unparseable line is UNMEASURED and the other six per-card clauses are then "
               "UNMEASURED (\"no trailer\").",
    "SKILL": "the set of trailer skills EQUALS the set of skills the card text names in CARD_TOKEN form (`<name>` "
             "skill): a named skill without a trailer, or a trailer for an unnamed skill, is FAIL. The five clauses "
             "below are judged per trailer and folded (any FAIL is FAIL, else any UNMEASURED is UNMEASURED).",
    "SOURCE-PATH": "the trailer's source is `skills/<trailer skill>/SKILL.md`.",
    "SOURCE-CURRENT": "the committed source at the judged commit has the trailer's LF sha256; an absent source is "
                      "UNMEASURED. This is the clause a re-record of H alone cannot clear.",
    "COMMIT-ANCESTOR": "the trailer commit resolves and is an ancestor of the judged commit (unresolvable: "
                       "UNMEASURED, and so are the next two).",
    "COMMIT-TOUCHES": "the trailer commit changed the source path, by the definition `--trailer-for` prints: the "
                      "last commit up to it that changed the source (path-limited `git log -1`) is itself, so a merge "
                      "that resolved the source counts.",
    "COMMIT-DIGEST": "the source blob at the trailer commit has the trailer's digest.",
    "FLOOR": "population size >= 2 (0 is UNMEASURED, 1 is FAIL).",
    "DISPATCHER-COVERED": "every card the dispatcher registers, in either CHAIN_MAP shape "
                          "(`../skills/claude-power-pack/<rel>` and `./<rel>`, "
                          "skill_mirror_drift.committed_card_pairs with dotslash), is a population member, so a "
                          "registered card outside the sweep (a test directory) cannot escape it.",
    "H-RECORD-CURRENT": "pillar H's committed record agrees with the committed cards and sources "
                        "(skill_mirror_drift.card_source_state + card_drift + card_verdict).",
}

DRILL_TEXT = {
    "CLEAN": "none",
    "SOURCE-CHANGED-RERECORDED": "first byte of CW's SKILL.md changed and committed; trailer untouched; H re-recorded",
    "SOURCE-CHANGED-RAW": "the same source change, H not re-recorded",
    "REDERIVED": "SOURCE-CHANGED-RAW, then CW's trailer re-derived with trailer_for and H re-recorded",
    "MERGE-REDERIVED": "CW's SKILL.md edited on two branches, the conflict resolved inside the merge commit; trailer "
                       "re-derived with trailer_for (it names the merge) and H re-recorded",
    "MULTI-SKILL-LINEAGED": "CW also names `third-skill` (a see-also line) and carries a second trailer for it; H "
                            "re-recorded with 3 pairs",
    "MULTI-SKILL-RERECORDED": "MULTI-SKILL-LINEAGED (judged PASS first), then third-skill's SKILL.md changed and "
                              "committed, card untouched, H re-recorded",
    "MULTI-SKILL-UNLINEAGED": "CW also names `third-skill` with no trailer for it; H re-recorded with 3 pairs",
    "TRAILER-SHA-DIGIT": "one hex digit of CW's trailer sha256 changed",
    "TRAILER-ABSENT": "DS trailer line deleted (its two LINEAGE comment lines kept)",
    "TRAILER-DUPLICATE": "DS trailer line duplicated",
    "TRAILER-UNPARSEABLE": "DS trailer sha256 cut to 63 hex",
    "SKILL-MISMATCH": "CW trailer replaced by the trailer for DS's skill",
    "SOURCE-PATH": "CW trailer keeps its skill but points at DS's source, digest and commit A",
    "GHOST-SKILL": "CW's CARD_TOKEN and trailer renamed to ghost-skill (sha256 and commit kept); re-record refused",
    "COMMIT-UNKNOWN": "CW trailer commit = deadbeef x 5 (absent from a complete history: COMMIT-ANCESTOR is a "
                      "measured FAIL)",
    "SHALLOW-CLONE": "the clean fixture judged through a depth-1 clone that lacks the trailer commits (real ancestors)",
    "COMMIT-NOT-ANCESTOR": "CW trailer commit = a side-branch commit adding identical source bytes",
    "COMMIT-NOT-TOUCHING": "CW trailer commit = the H record commit (did not change the source)",
    "COMMIT-WRONG-DIGEST": "CW source changed; trailer carries the new digest but commit A",
    "FLOOR-ONE": "DS hook file removed (registration kept); H re-recorded with one pair",
    "FLOOR-ZERO": "both card files removed; re-record refused",
    "UNLINEAGED-CARD": "new top-level hooks/new_card.js naming CW's skill, no trailer, not registered",
    "DISPATCHER-UNCOVERED": "hooks/tests/deep_card.js (test directories are outside the sweep) = copy of CW, "
                            "registered next to CW; H re-recorded with 3 pairs",
    "DISPATCHER-UNCOVERED-DOTSLASH": "hooks/tests/fixtures/dot_card.js = copy of CW, registered next to CW with the "
                                     "`./tests/fixtures/dot_card.js` shape (H's parser does not read it, no re-record)",
    "SUBDIR-CARD-DOTSLASH": "hooks/_shared/sub_card.js = copy of CW with its marker defused, registered with the "
                            "`./_shared/sub_card.js` shape (no re-record)",
    "CARD-EDIT-UNRECORDED": "one comment line appended to CW after its trailer, H not re-recorded",
    "RECORD-UNPARSEABLE": "H record replaced by a lone `{`",
    "CRLF": "CW's SKILL.md, both cards, the dispatcher and the record committed with CRLF line ends",
    "WORKTREE-ONLY": "CW source byte changed and DS trailer deleted in the working tree only, not committed",
}


def _head_json(rel):
    out, why = smd.git_run(REPO, "show", f"HEAD:{rel}")
    if out is None:
        return None
    try:
        return json.loads(smd.lf_bytes(out).decode("utf-8"))
    except ValueError:
        return None


def _frozen_rule():
    led = _head_json(LEDGER_REL)
    try:
        return next(p["rule"] for p in led["frozen"]["pillars"] if p["id"] == "G")
    except (TypeError, KeyError, StopIteration):
        return None


def _cell(s) -> str:
    return str(s).replace("|", "\\|")


def render(st) -> str:
    """Deterministic LF text: no HEAD sha of this run, no host, no temp path, no timing."""
    L = ["# [G] compile-out + lineage -- evidence", "", "Frozen pillar G rule (ledger, quoted):", ""]
    rule = _frozen_rule()
    L += [f"> {rule}" if rule else "(frozen rule unreadable)", ""]
    L += ["This file is rendered by `tools/test_card_lineage.py --write-evidence` from the gate's own results, and "
          "V-CLG-EVIDENCE-CURRENT compares the committed copy with a fresh render.", ""]
    L += ["## Method", "",
          "- Trailer grammar: the last lines of each card are one comment line per skill the card names, "
          "`// COMPILED-FROM: skill=<name> source=skills/<name>/SKILL.md sha256=<64 hex> commit=<40 hex>`. "
          "A card naming two skills carries two lines, so a change to either skill's SKILL.md fails SOURCE-CURRENT "
          "until that line is re-derived (drill MULTI-SKILL-RERECORDED). "
          "sha256 is the LF-normalized digest of the committed SKILL.md; commit is the commit that last changed it "
          "when the card was derived.",
          "- Population, discovered: every `hooks/**/*.js` tracked at the judged commit outside `hooks/tests/` and "
          "`hooks/_tests/`, whose LF text holds a CARD_TOKEN match (`<name>` skill) or a line starting with "
          "`// COMPILED-FROM:`. Discovery does not depend on how (or whether) the dispatcher registers the file. "
          "Nothing is listed by hand. Floor 2.",
          "- Committed-blob rule: every byte compared comes from git blobs at the judged commit or at the trailer "
          "commit, CRLF->LF. No working-tree file is read, so an uncommitted edit never stands in for a source.",
          "- Reuse: git access, blob reads, failure classification and the H record comparison are the "
          "skill_mirror_drift functions (git_run, resolve_commit, tracked_paths, committed_card_pairs, "
          "card_source_state, card_drift, card_verdict, is_git_failure); the card token and dispatcher reading are "
          "skill_coverage's (CARD_TOKEN, registered_hooks, discover_cards). One implementation each.",
          "- Outcomes are PASS, FAIL or UNMEASURED; the verdict is PASS only when all 10 clauses are PASS for every "
          "card. A git failure before or during discovery (git missing, unresolvable ref, nothing tracked, a member "
          "blob unreadable) is INCONCLUSIVE, never PASS and never a traceback. After discovery a clause whose git "
          "call did not answer (failure, timeout, a trailer commit beyond a shallow clone's history) is a git-tagged "
          "UNMEASURED, and the verdict is INCONCLUSIVE when every non-PASS clause is one; any measured FAIL, or an "
          "UNMEASURED that is not git (no trailer, missing source), makes it FAIL.", "",
          "Clauses:", ""]
    for cid in cl.CARD_CLAUSES + cl.GATE_CLAUSES:
        L.append(f"- {cid} ({'per card' if cid in cl.CARD_CLAUSES else 'gate'}): {CLAUSE_TEXT[cid]}")
    L += ["", "## Population (live checkout, HEAD)", ""]
    live = st["live"]
    L.append(f"verdict {live['verdict']}, population {len(live['population'])}")
    L.append("")
    L.append("| card | skill | source | sha256 | commit | " + " | ".join(cl.CARD_CLAUSES) + " |")
    L.append("|" + "---|" * (5 + len(cl.CARD_CLAUSES)))
    for card in live["cards"]:
        for t in (card["trailers"] or [{}]):
            L.append(f"| {card['card']} | {t.get('skill', '-')} | {t.get('source', '-')} | {t.get('sha256', '-')} | "
                     f"{t.get('commit', '-')} | " + " | ".join(card["clauses"][c]["outcome"] for c in cl.CARD_CLAUSES)
                     + " |")
    L.append("")
    L.append("Gate clauses: " + ", ".join(f"{cid} {live['gate'].get(cid, {}).get('outcome', '-')}"
                                          for cid in cl.GATE_CLAUSES))
    rec = _head_json(smd.CARD_RECORD_REL)
    L.append(f"H record `{smd.CARD_RECORD_REL}` recorded_at_commit "
             f"`{(rec or {}).get('recorded_at_commit', '(unreadable)')}`")
    L += ["", "## Drills", "",
          "Each drill starts from a copy of a clean temporary git repo seeded from the HEAD blobs of the dispatcher, "
          "the two cards and their SKILL.md sources (commits R, A, B, C). CW is hooks/doctrine_cards.js, DS is "
          "hooks/destructive_doctrine_card.js; a per-card clause is `<card>:<CLAUSE>`. A drill is ok only when the "
          "observed verdict and fail set EQUAL the declared ones (and the clauses expected UNMEASURED are "
          "UNMEASURED).", "",
          "| id | mutation | declared | observed | result |", "|---|---|---|---|---|"]
    for did, row in st["drills"].items():
        res = "ok" if drill_ok(row, did) else "FAIL"
        obs = f"{row['verdict']} {_fmt(row['fail_set'])}" if row["fail_set"] is not None else "not observed"
        L.append(f"| {did} | {_cell(DRILL_TEXT.get(did, '-'))} | {row['declared_verdict']} "
                 f"{_fmt(row['declared'])} | {obs} | {res} |")
    L += ["", "## Load-bearing", "",
          "Each clause was forced PASS (its CLAUSES entry replaced) and its singleton drill re-judged; TRAILER has no "
          "singleton (its failure leaves the other six unmeasurable), so the population was narrowed to members "
          "carrying the marker. Each patch was restored and the drill re-judged.", "",
          "| clause | drill | patched verdict | restored verdict |", "|---|---|---|---|"]
    flips = st.get("flips")
    if flips is None:
        L.append("| (not measured) | - | - | - |")
    else:
        for cid, did, forced, restored in flips:
            L.append(f"| {cid} | {did} | {forced} | {restored} |")
    gf = st.get("git_failure")
    L += ["", "Git unavailable (`vgm._git_exe` raising): " + (
        f"live {gf['live']}, fixture {gf['fixture']}, after restoration {gf['restored']}." if gf else
        "(not measured).")]
    gm = st.get("git_midjudge")
    L += ["", "Git failing inside a clause on the clean fixture (one subcommand stubbed): " + (
        "; ".join(gm) + "." if gm else "(not measured).")]
    L += ["", "## Re-derivation", "",
          "When a source skill changes: re-read the skill, update the card text and its trailer together (the line "
          "comes from `python3 tools/card_lineage.py --trailer-for <skill>`, which prints and never writes), commit, "
          "then re-record H with `python3 tools/skill_mirror_drift.py --record-cards` and commit the record. H's "
          "re-record alone does not clear SOURCE-CURRENT (drill SOURCE-CHANGED-RERECORDED).", "",
          "## Commands", "",
          "command: python3 tools/test_card_lineage.py",
          "command: python3 tools/test_card_lineage.py --write-evidence",
          "command: python3 tools/card_lineage.py",
          "command: python3 tools/card_lineage.py --trailer-for <skill>",
          "command: python3 tools/skill_mirror_drift.py --record-cards", ""]
    return "\n".join(L)


def evidence_current(raw: bytes, rendered: str) -> bool:
    """Compared after CRLF->LF: the laptop checkout hands the committed file back CRLF."""
    return smd.lf_bytes(raw) == rendered.encode("utf-8")


def c_evidence_current(st):
    raw, why = smd.git_run(REPO, "show", f"HEAD:{EVIDENCE_REL}")
    if raw is None:
        if " rc=128:" in (why or "") and ("does not exist" in why or "not in 'HEAD'" in why):
            return [(FAIL, "V-CLG-EVIDENCE-CURRENT", f"{EVIDENCE_REL} not committed: run --write-evidence and commit")]
        return [(INCONC, "V-CLG-EVIDENCE-CURRENT", f"committed blob unreadable: {why}")]
    if evidence_current(raw, render(st)):
        return [(OK, "V-CLG-EVIDENCE-CURRENT", f"committed {EVIDENCE_REL} equals the render (after CRLF->LF)")]
    return [(FAIL, "V-CLG-EVIDENCE-CURRENT", f"committed {EVIDENCE_REL} differs from the render; run "
                                             f"--write-evidence and commit")]


def c_evidence_drill(st):
    r = render(st)
    raw = r.encode("utf-8")
    ctrl = evidence_current(raw, r)
    crlf = evidence_current(raw.replace(b"\n", b"\r\n"), r)
    mutated = r.replace("sha256", "sha257", 1) if "sha256" in r else r + "x"
    accepted = evidence_current(mutated.encode("utf-8"), r)
    if ctrl and crlf and not accepted:
        return [(OK, "V-CLG-EVIDENCE-DRILL", "render accepted, CRLF copy accepted, one-character change refused")]
    return [(FAIL, "V-CLG-EVIDENCE-DRILL", f"control={ctrl} crlf={crlf} mutated_accepted={accepted}")]


JUDGE_CLAUSES = [c_live_clean, c_positive_control, c_drills, c_subprocess_red, c_git_failure,
                 c_git_failure_midjudge, c_every_clause]
EVIDENCE_CLAUSES = [c_evidence_current, c_evidence_drill]
CLAUSES = JUDGE_CLAUSES + EVIDENCE_CLAUSES


# --------------------------------------------------------------------------- driver

def collect(tmp: Path) -> dict:
    st = {"live": cl.judge(REPO), "fixture_error": None, "drills": {}, "fx": None}
    try:
        fx = Fixture(tmp)
    except FixtureError as e:
        st["fixture_error"] = e
        return st
    st["fx"] = fx
    st["drills"] = run_drills(fx)
    return st


def run_clauses(st, clauses) -> list:
    results = []
    fe = st.get("fixture_error")
    for fn in clauses:
        cid = fn.__name__.replace("c_", "V-CLG-").upper().replace("_", "-")
        if fe is not None and fn not in (c_live_clean, c_positive_control):
            results.append((INCONC if fe.git else FAIL, cid, f"fixture not built: {fe}"))
            continue
        try:
            results.extend(fn(st))
        except Exception as e:  # noqa: BLE001 -- a clause that cannot run is INCONC, never a traceback
            results.append((INCONC, cid, f"clause raised {type(e).__name__}: {e}"))
    return results


def report(results) -> int:
    for v, cid, text in results:
        print(f"{v:<4} {cid} {text}" if v == OK else f"{v} {cid} {text}")
    passed = sum(1 for v, _, _ in results if v == OK)
    n = len(results)
    print(f"CLG_PASS={passed}/{n}  threshold={n}/{n}")
    return 0 if passed == n and n > 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write-evidence", action="store_true")
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="clg-") as td:
        st = collect(Path(td))
        if a.write_evidence:
            # The render needs the drill results, the forced-pass flips and the git-failure outcome; currency is
            # not judged here (the committed blob is what V-CLG-EVIDENCE-CURRENT reads).
            run_clauses(st, JUDGE_CLAUSES)
            dest = REPO / EVIDENCE_REL
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(render(st).encode("utf-8"))
            print(f"wrote {EVIDENCE_REL}")
            return 0
        return report(run_clauses(st, CLAUSES))


if __name__ == "__main__":
    sys.exit(main())
