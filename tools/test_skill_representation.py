#!/usr/bin/env python
"""test_skill_representation.py -- pillar F gate (skill-capability, SC-F, decision D-01): sweep + operations.

    python3 tools/test_skill_representation.py                     # check (default mode)
    python3 tools/test_skill_representation.py --recording PATH    # recording-scoped clauses on one file (red entrance)
    python3 tools/test_skill_representation.py --operations PATH   # V-FO-FILE + V-FO-ENTRIES on one file (red entrance)
    python3 tools/test_skill_representation.py --write-evidence    # render evidence/F-representation.md
    python3 tools/test_skill_representation.py --json              # recordings summary + groups + listing effect

What it judges:
1. the dedup content-hash sweep of `tools/skill_dedup_sweep.py` (D-01 item 1, V-FD-*);
2. the applied-operations ledger `vault/programs/skill-capability/f-operations.json` (D-01 item 2, V-FO-*), schema
   `skill-capability/f-operations/1` = {schema, rule (the frozen F rule verbatim), note, operations: [entry]}.
   An entry carries references, never figures:
       {op: disclosure|fission|fusion|inline|dedup, skill,
        before: {denominator: "D-LISTING", probe_label, session_id, command}, after: {same keys},
        recall: {before: {window, command}, after: {window, command}}}
   plus, for op dedup only, {sweep, group}. `window` and `sweep` are repo paths under
   `vault/programs/skill-capability/evidence/` ending `.json`, no `..`. The gate derives startup tokens and listing
   chars from the ONE probe row matching label AND session id, and recall num / n from the committed window docs;
3. the rendered prg evidence `evidence/F-representation.md` (D-03, V-FR-EVIDENCE-CURRENT).

The default mode reads only committed repo files and git blobs: every recording discovered by
`evidence/F-sweep-*.json`, the committed blobs at each recording's repo_commit, the committed operations file, probe
rows and lessons file, and nothing under any home directory, so the CE verifier can re-run it on another host at
`--final`. An uncommitted input is INCONCLUSIVE, never judged.

Output lines: `  ok   <ID> <evidence>` / `  FAIL <ID> <diagnostic>` / `  INCONCLUSIVE <ID> <reason>`, last line
`SR_PASS=<passed>/<total>`. Exit codes: 0 every clause ok, 1 any FAIL or INCONCLUSIVE, 2 could not run.
INCONCLUSIVE is never a pass.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import datetime
import fnmatch
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
REPO = _THIS_DIR.parent
for _p in (str(_THIS_DIR), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import skill_dedup_sweep as sweep  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402
import test_listing_floor_verdict as lfv  # noqa: E402

EVIDENCE_DIR = "vault/programs/skill-capability/evidence/"
SWEEP_GLOB = "F-sweep-*.json"
REQUIRED_KEYS = ("schema", "host", "node", "repo_commit", "live_root", "command", "method", "planes", "groups",
                 "drift_excluded", "member_files")
HEX = set("0123456789abcdef")


class Clause(Exception):
    """Raised by a clause body: status is FAIL or INCONCLUSIVE."""

    def __init__(self, status, msg):
        super().__init__(msg)
        self.status = status


def fail(msg):
    raise Clause("FAIL", msg)


def inconclusive(msg):
    raise Clause("INCONCLUSIVE", msg)


def run_clause(fn, *args):
    """(status, text). A clause returns its evidence string on ok; any unexpected exception is a FAIL line, never a
    traceback (a malformed recording must read red)."""
    try:
        return "ok", fn(*args)
    except Clause as c:
        return c.status, str(c)
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as e:
        return "FAIL", f"malformed recording: {type(e).__name__}: {e}"


# --------------------------------------------------------------------------- discovery

GIT_ROW = "(git ls-tree HEAD)"
GIT_UNAVAILABLE = "INCONCLUSIVE: git cannot list the tracked paths at HEAD"


def discover(repo=REPO):
    """[(filename, recording or None, reason or None)] for every F-sweep-*.json tracked at HEAD or present in the
    working tree, sorted. Each is read as its COMMITTED blob at HEAD (`smd.committed_bytes`): a recording that exists
    only in the working tree, or differs from HEAD, is refused as uncommitted (INCONCLUSIVE), never judged."""
    tracked, why = smd.tracked_paths(repo, "HEAD")
    if tracked is None:
        # Committed cannot be told from uncommitted: one INCONCLUSIVE row carrying git's reason, never a per-file
        # "exists only in the working tree" diagnosis, and never "nothing discovered" (05-REVIEW IN-04).
        return [(GIT_ROW, None, f"{GIT_UNAVAILABLE}: {why}")]
    names = {p.name for p in (Path(repo) / EVIDENCE_DIR).glob(SWEEP_GLOB)}
    names |= {t[len(EVIDENCE_DIR):] for t in tracked if t.startswith(EVIDENCE_DIR)
              and fnmatch.fnmatch(t[len(EVIDENCE_DIR):], SWEEP_GLOB)}
    out = []
    for n in sorted(names):
        if EVIDENCE_DIR + n not in tracked:
            out.append((n, None, f"uncommitted: {EVIDENCE_DIR}{n} exists only in the working tree (commit it)"))
            continue
        raw, why = smd.committed_bytes(repo, EVIDENCE_DIR + n)
        if raw is None:
            out.append((n, None, why))
            continue
        try:
            out.append((n, json.loads(smd.lf_bytes(raw).decode("utf-8")), None))
        except ValueError as e:
            out.append((n, None, f"{n} is not JSON: {e}"))
    return out


# --------------------------------------------------------------------------- clauses (pure: take the recording)

def c_recordings(name, rec, suffix_rule=True):
    """`suffix_rule` is the naming rule of the evidence directory (host == filename suffix); `--recording` on a path
    outside that directory reports it as not applied rather than failing a scratch copy for its name."""
    if rec is None:
        fail(f"{name}: unreadable")
    if not isinstance(rec, dict):
        fail(f"{name}: not a JSON object")
    missing = [k for k in REQUIRED_KEYS if k not in rec]
    if missing:
        fail(f"{name}: missing keys {missing}")
    if rec["schema"] != sweep.SCHEMA:
        fail(f"{name}: schema {rec['schema']!r} != {sweep.SCHEMA!r}")
    if not (isinstance(rec["host"], str) and sweep.HOST_RE.fullmatch(rec["host"])):
        fail(f"{name}: host {rec['host']!r} is not ^[a-z0-9-]+$")
    if not sweep.host_ok(rec["host"]):
        fail(f"{name}: host {rec['host']!r} collides with the {sweep.REPO_LABEL!r} plane label")
    if suffix_rule and name != f"F-sweep-{rec['host']}.json":
        fail(f"{name}: host {rec['host']!r} does not match the filename suffix")
    rc = rec["repo_commit"]
    if not (isinstance(rc, str) and len(rc) == 40 and set(rc) <= HEX):
        fail(f"{name}: repo_commit {rc!r} is not 40-hex")
    if set(rec["planes"]) != {"repo", rec["host"]}:
        fail(f"{name}: planes {sorted(rec['planes'])} != ['repo', {rec['host']!r}]")
    return f"{name} host={rec['host']} repo_commit={rc[:8]}" + ("" if suffix_rule else
                                                                 " (filename suffix rule not applied: outside "
                                                                 f"{EVIDENCE_DIR})")


def _strip_subset(grps):
    return [{k: v for k, v in g.items() if k != "subset"} for g in grps]


def c_groups_reproduce(name, rec):
    grps, drift = sweep.groups(rec["planes"])
    recorded = _strip_subset(rec["groups"])
    if len(grps) != len(recorded):
        fail(f"{name}: re-derived {len(grps)} groups, recorded {len(recorded)}")
    for i, (a, b) in enumerate(zip(grps, recorded)):
        if a != b:
            keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            fail(f"{name}: group {i} {a.get('names')} differs from the recorded one in {keys}")
    uncovered = [f"{m['plane']}/{m['name']}" for g in grps for m in g["members"]
                 if f"{m['plane']}/{m['name']}" not in rec["member_files"]]
    if uncovered:
        fail(f"{name}: re-derived group member(s) {uncovered} carry no member_files list")
    if drift != rec["drift_excluded"]:
        fail(f"{name}: drift_excluded re-derived {len(drift)} names, recorded {len(rec['drift_excluded'])}")
    names = "; ".join(f"{'+'.join(g['names'])} fm_name_collision={g['fm_name_collision']}" for g in grps)
    return f"{name} groups={len(grps)} [{names}] drift_excluded={len(drift)}"


REPO_FLOOR = 24  # repo-plane skills measured at plan time (05-01); fewer is a FAIL, zero is UNMEASURED
COUNT_KEYS = ("entries", "skills")
GEX44_NAME = "F-sweep-gex44.json"


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def c_pop_floor(name, rec):
    parts = []
    for label in sorted(rec["planes"]):
        p = rec["planes"][label]
        for k in COUNT_KEYS:
            if not _int(p.get(k)):
                inconclusive(f"{name}: {label}.{k} is {p.get(k)!r}, not an int (UNMEASURED, never 'no duplicates')")
            if p[k] <= 0:
                inconclusive(f"{name}: {label}.{k} is {p[k]} (UNMEASURED: a zero population is no measurement)")
        for k in ("no_skill_md", "non_dir", "names"):
            if not isinstance(p.get(k), list):
                inconclusive(f"{name}: {label}.{k} is not a list")
        if p["entries"] != p["skills"] + len(p["no_skill_md"]) + len(p["non_dir"]):
            fail(f"{name}: {label} entries {p['entries']} != skills {p['skills']} + no_skill_md "
                 f"{len(p['no_skill_md'])} + non_dir {len(p['non_dir'])}")
        if len(p["records"]) != p["skills"] or sorted(p["records"]) != p["names"]:
            fail(f"{name}: {label} records ({len(p['records'])}) do not match skills {p['skills']} / names")
        if label == "repo" and p["skills"] < REPO_FLOOR:
            fail(f"{name}: repo plane holds {p['skills']} skills < floor {REPO_FLOOR}")
        parts.append(f"{label}={p['skills']}/{p['entries']} (no_skill_md={len(p['no_skill_md'])} "
                     f"non_dir={len(p['non_dir'])})")
    return f"{name} " + " ".join(parts) + f" repo_floor={REPO_FLOOR}"


@functools.lru_cache(maxsize=8)
def _repo_plane_at(commit):
    return sweep.repo_plane(REPO, commit)


def c_repo_reproduces(name, rec):
    # The live plane cannot be re-read on another host, so its hashes are recorded facts and only what is derived
    # from them is re-checked (V-FD-GROUPS-REPRODUCE, V-FD-MEMBER-FILES). The repo plane is re-read from blobs.
    now = _repo_plane_at(rec["repo_commit"])
    if now["status"] != "MEASURED":
        inconclusive(f"{name}: repo plane at {rec['repo_commit'][:8]} not re-derivable: {now['reason']}")
    old, new = rec["planes"]["repo"], sweep.public(now)
    for k in sorted(set(old) | set(new)):
        if k == "records":
            continue
        if old.get(k) != new.get(k):
            fail(f"{name}: repo.{k} differs from the blobs at {rec['repo_commit'][:8]}")
    ro, rn = old.get("records", {}), new["records"]
    for n in sorted(set(ro) | set(rn)):
        if ro.get(n) != rn.get(n):
            keys = sorted(k for k in sweep.RECORD_KEYS if (ro.get(n) or {}).get(k) != (rn.get(n) or {}).get(k))
            fail(f"{name}: repo record {n} differs from the blobs at {rec['repo_commit'][:8]} in {keys}")
    return f"{name} repo plane re-derived from blobs at {rec['repo_commit'][:8]}: {len(rn)} records equal"


def c_member_files(name, rec):
    mf = rec["member_files"]
    for mid in sorted(mf):
        label, _, skill = mid.partition("/")
        recd = rec["planes"][label]["records"].get(skill)
        if recd is None:
            fail(f"{name}: member_files {mid} names no recorded skill")
        files = {r: s for r, s in mf[mid]}
        if smd.dir_digest(files) != recd["dir_digest"]:
            fail(f"{name}: member_files {mid} re-digests to a value != its recorded dir_digest")
        if files.get("SKILL.md") != recd["skill_md_sha"]:
            fail(f"{name}: member_files {mid} SKILL.md line != recorded skill_md_sha")
        if len(files) != recd["files"]:
            fail(f"{name}: member_files {mid} lists {len(files)} files, record says {recd['files']}")
    for g in rec["groups"]:
        if sweep.subset_pairs(g, mf) != g.get("subset"):
            fail(f"{name}: group {g.get('names')} subset re-derived {sweep.subset_pairs(g, mf)} != {g.get('subset')}")
    return f"{name} {len(mf)} member file lists re-digest; subset pairs " + \
        "; ".join(str(g.get("subset")) for g in rec["groups"])


def c_planes_apart(name, rec):
    drift = set(rec["drift_excluded"])
    for g in rec["groups"]:
        names = {m["name"] for m in g["members"]}
        if len(names) < 2 or g.get("distinct_names", 0) < 2:
            fail(f"{name}: group {sorted(names)} carries fewer than 2 distinct names (same-name copies are drift, "
                 f"pillar H)")
        # (The former "drift name as the only name of a group" branch could not fire: fewer than 2 names already
        # fails above, 05-REVIEW IN-01.) The group's three name counts must agree with each other.
        if not g.get("distinct_names") == len(names) == len(g.get("names", ())) == len(set(g.get("names", ()))):
            fail(f"{name}: group {sorted(names)} distinct_names {g.get('distinct_names')!r} != its {len(names)} member "
                 f"names / names list {g.get('names')}")
    return f"{name} {len(rec['groups'])} groups each >= 2 distinct names; drift_excluded={len(drift)} kept apart"


def c_real_group(name, rec):
    if rec["host"] != "gex44":
        return f"{name} n/a (positive control is pinned to the gex44 plane)"
    grps, _ = sweep.groups(rec["planes"])
    if not grps:
        fail(f"{name}: the gex44 plane re-derives 0 groups (positive control on real data is empty)")
    return f"{name} gex44 re-derives {len(grps)} group(s): " + "; ".join("+".join(g["names"]) for g in grps)


RECORDING_CLAUSES = (
    ("V-FD-POP-FLOOR", c_pop_floor),
    ("V-FD-REPO-REPRODUCES", c_repo_reproduces),
    ("V-FD-GROUPS-REPRODUCE", c_groups_reproduce),
    ("V-FD-MEMBER-FILES", c_member_files),
    ("V-FD-PLANES-APART", c_planes_apart),
    ("V-FD-REAL-GROUP", c_real_group),
)
CLAUSE_IDS = ("V-FD-RECORDINGS",) + tuple(c for c, _ in RECORDING_CLAUSES)


# --------------------------------------------------------------------------- hash poles (synthetic, temp dirs)

FM_A = "---\nname: alpha\ndescription: first\n---\n"
FM_B = "---\nname: beta\ndescription: second, longer\n---\n"
BODY = "# Body\n\nSame words.\n"


def _skill(root: Path, name: str, text: str, newline: str = "\n"):
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(text.replace("\n", newline).encode("utf-8"))


def _plane(root, label="live"):
    p = sweep.live_plane(root, label)
    if p["status"] != "MEASURED":
        raise AssertionError(f"pole plane {label} not measured: {p['reason']}")
    return p


def pole_same_body(tmp):
    r = Path(tmp) / "same"
    _skill(r, "alpha", FM_A + BODY)
    _skill(r, "beta", FM_B + BODY)
    p = _plane(r)
    a, b = p["records"]["alpha"], p["records"]["beta"]
    g, _ = sweep.groups({"live": p})
    ok = a["body_sha"] == b["body_sha"] and a["skill_md_sha"] != b["skill_md_sha"] and len(g) == 1
    return ok, f"body equal={a['body_sha'] == b['body_sha']} skill_md differ={a['skill_md_sha'] != b['skill_md_sha']} groups={len(g)}"


def pole_crlf(tmp):
    r = Path(tmp) / "crlf"
    _skill(r, "lf", FM_A + BODY)
    _skill(r, "crlf", FM_A + BODY, "\r\n")
    p = _plane(r)
    ok = p["records"]["lf"]["body_sha"] == p["records"]["crlf"]["body_sha"]
    return ok, f"CRLF body equal={ok}"


def pole_one_byte(tmp):
    r = Path(tmp) / "onebyte"
    _skill(r, "alpha", FM_A + BODY)
    _skill(r, "beta", FM_A + BODY.replace("Same", "Samf"))
    p = _plane(r)
    g, _ = sweep.groups({"live": p})
    ok = p["records"]["alpha"]["body_sha"] != p["records"]["beta"]["body_sha"] and not g
    return ok, f"one-byte body differ={ok} groups={len(g)}"


def pole_no_frontmatter(tmp):
    r = Path(tmp) / "nofm"
    _skill(r, "plain", BODY)
    rec = _plane(r)["records"]["plain"]
    whole = hashlib.sha256(BODY.encode("utf-8")).hexdigest()
    ok = rec["has_frontmatter"] is False and rec["body_sha"] == whole and rec["fm_name"] is None
    return ok, f"has_frontmatter={rec['has_frontmatter']} body=whole file:{rec['body_sha'] == whole}"


def pole_same_name_cross_plane(tmp):
    r1, r2 = Path(tmp) / "x1", Path(tmp) / "x2"
    _skill(r1, "foo", FM_A + BODY)
    _skill(r2, "foo", FM_A + BODY)
    g, drift = sweep.groups({"repo": _plane(r1, "repo"), "live": _plane(r2, "live")})
    ok = not g and drift == ["foo"]
    return ok, f"groups={len(g)} drift_excluded={drift}"


def pole_cross_plane_renamed(tmp):
    r1, r2 = Path(tmp) / "y1", Path(tmp) / "y2"
    _skill(r1, "foo", FM_A + BODY)
    _skill(r2, "bar", FM_B + BODY)
    g, drift = sweep.groups({"repo": _plane(r1, "repo"), "live": _plane(r2, "live")})
    labels = [(m["plane"], m["name"]) for m in g[0]["members"]] if g else []
    ok = len(g) == 1 and labels == [("live", "bar"), ("repo", "foo")] and not drift
    return ok, f"groups={len(g)} members={labels}"


def pole_discovery(tmp):
    r = Path(tmp) / "disc"
    _skill(r, "real", FM_A + BODY)
    (r / "nodoc").mkdir()
    (r / "nodoc" / "README.md").write_bytes(b"not a skill\n")
    (r / "loose.txt").write_bytes(b"a plain file\n")
    p = _plane(r)
    ok = (p["no_skill_md"] == ["nodoc"] and p["non_dir"] == ["loose.txt"] and p["names"] == ["real"]
          and p["entries"] == 3 and p["skills"] == 1)
    return ok, f"skills={p['names']} no_skill_md={p['no_skill_md']} non_dir={p['non_dir']} entries={p['entries']}"


def pole_empty_body(tmp):
    # Frontmatter-only skills (and frontmatter + blank lines, which _FM_RE's closing `---\s*\n` also eats) all hash
    # to sha256(b""): unrelated skills must not become one dedup group on that (05-REVIEW WR-04).
    r = Path(tmp) / "empty"
    _skill(r, "pdf-tools", "---\nname: pdf-tools\ndescription: Extract tables from PDF files\n---\n")
    _skill(r, "slack-notify", "---\nname: slack-notify\ndescription: Post a message to a Slack channel\n---\n")
    _skill(r, "x", "---\nname: x\ndescription: x\n---\n\n\n")
    p = _plane(r)
    sizes = sorted({rec["body_bytes"] for rec in p["records"].values()})
    g, _ = sweep.groups({"live": p})
    ok = sizes == [0] and not g
    return ok, f"body_bytes={sizes} groups={len(g)}"


def pole_listing_line_bound(tmp):
    # listing_chars_upper_bound must bound the characters a removal frees from the listing text the probe parses
    # (`- <name>: <desc>` lines, `described (N)` = len(desc.strip())), not the description characters alone
    # (05-REVIEW WR-05). Built in memory; `tmp` is unused.
    descs = {"aa": "d" * 100, "bbb": "e" * 100}
    listing = "".join(f"- {n}: {d}\n" for n, d in descs.items())
    watch = {n: f"described ({len(d)})" for n, d in descs.items()}
    rows = [{"session_id": sid, "watch": watch} for sid in sweep.K4_SESSIONS.values()]
    g = {"names": sorted(descs), "distinct_names": len(descs)}
    bound = sweep.listing_effect(g, rows)["listing_chars_upper_bound"]
    freed = [len(listing) - len(listing.replace(f"- {n}: {d}\n", "")) for n, d in descs.items()]
    ok = isinstance(bound, int) and bound >= max(freed) and bound == max(freed)
    return ok, f"listing_chars_upper_bound={bound} chars freed per removal={freed}"


def pole_host_repo_refused(tmp):
    # `repo` is the repo plane's label: as a host it collapses {"repo": rp, host: lp} to the live plane alone, which
    # V-FD-RECORDINGS admitted because {"repo", "repo"} == {"repo"} (05-REVIEW WR-06). Refused at all three doors.
    live, out = Path(tmp) / "live", Path(tmp) / "F-sweep-repo.json"
    _skill(live, "real", FM_A + BODY)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = sweep.main(["--measure-live", "--host", "repo", "--out", str(out), "--live-root", str(live)])
    rec_b, why_b = sweep.build_recording(REPO, "HEAD", live, "repo")
    p = sweep.public(_plane(live, "repo"))
    rec = {"schema": sweep.SCHEMA, "host": "repo", "node": "n", "repo_commit": "0" * 40, "live_root": str(live),
           "command": "", "method": sweep.METHOD, "planes": {"repo": p}, "groups": [], "drift_excluded": [],
           "member_files": {}}
    st, text = run_clause(c_recordings, out.name, rec)
    ok = rc == 2 and not out.exists() and rec_b is None and st == "FAIL"
    return ok, (f"--measure-live --host repo rc={rc} wrote={out.exists()}; build_recording "
                f"{'refused' if rec_b is None else 'built'}; V-FD-RECORDINGS {st}")


def pole_unreadable_inconclusive(tmp):
    # An unreadable live skill directory, or a tracked skills/ path that is not UTF-8, must read INCONCLUSIVE, never a
    # traceback (05-REVIEW IN-02).
    parts, ok = [], True
    live = Path(tmp) / "live"
    _skill(live, "real", FM_A + BODY)
    _skill(live, "locked", FM_B + BODY)
    locked = live / "locked"
    os.chmod(locked, 0)
    try:
        if os.access(locked / "SKILL.md", os.R_OK):
            parts.append("live: n/a (mode 000 does not deny this user, e.g. root)")
        else:
            try:
                st = sweep.live_plane(live)["status"]
            except Exception as e:  # noqa: BLE001 -- the defect under test is that this raises
                st = f"RAISED {type(e).__name__}"
            ok &= st == "INCONCLUSIVE"
            parts.append(f"live mode-000 skill: {st}")
    finally:
        os.chmod(locked, 0o755)
    if os.name != "posix":
        return ok, "; ".join(parts + ["repo: n/a (non-UTF-8 file names need POSIX)"])
    repo = Path(tmp) / "repo"
    bad = os.path.join(os.fsencode(repo), b"skills", b"bad\xff")
    os.makedirs(bad)
    with open(os.path.join(bad, b"SKILL.md"), "wb") as fh:
        fh.write((FM_A + BODY).encode("utf-8"))
    for n in range(REPO_FLOOR):
        _skill(repo / "skills", f"s{n}", FM_A + BODY + str(n))
    git = ["git", "-C", str(repo), "-c", "user.name=pole", "-c", "user.email=pole@example.invalid",
           "-c", "commit.gpgsign=false"]
    try:
        for argv in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "pole"]):
            subprocess.run(git + argv, check=True, capture_output=True, timeout=SUBPROCESS_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as e:
        return False, "; ".join(parts + [f"repo: could not build the git fixture: {type(e).__name__}"])
    try:
        st = sweep.repo_plane(repo, "HEAD")["status"]
    except Exception as e:  # noqa: BLE001 -- the defect under test is that this raises
        st = f"RAISED {type(e).__name__}"
    ok &= st == "INCONCLUSIVE"
    parts.append(f"repo non-UTF-8 tracked path: {st}")
    return ok, "; ".join(parts)


def pole_git_unavailable(tmp):
    # When git cannot list HEAD, discovery cannot tell committed from uncommitted: every recording is INCONCLUSIVE
    # with git's own reason, never "exists only in the working tree", and an empty evidence directory is not a FAIL
    # "no recording discovered" (05-REVIEW IN-04). Driven on the real repo and on an empty temp tree.
    real = smd.tracked_paths
    smd.tracked_paths = lambda repo, ref: (None, "git ls-tree timed out (pole)")
    try:
        parts, ok = [], True
        for label, repo in (("repo", REPO), ("empty", Path(tmp))):
            res, _ = recordings_results(discover(repo))
            st, text = res.get("V-FD-RECORDINGS", ("absent", ""))
            worst = max((RANK.get(v[0], 2) for v in res.values()), default=2)
            good = st == "INCONCLUSIVE" and "timed out (pole)" in text and "uncommitted" not in text and worst == 1
            ok &= good
            parts.append(f"{label}: V-FD-RECORDINGS {st} ({'git reason' if 'timed out' in text else text[:60]}), "
                         f"worst {[k for k, v in RANK.items() if v == worst]}")
    finally:
        smd.tracked_paths = real
    return ok, "; ".join(parts)


def pole_discovery_links(tmp):
    # The symlinked list, the dangling link that goes to non_dir, and the non-UTF-8 refusal of live_plane, each of
    # which a mutant could break with every other pole green (05-REVIEW IN-06). POSIX only: named n/a elsewhere.
    if os.name != "posix":
        return True, "n/a (directory symlinks and non-UTF-8 names need POSIX)"
    r = Path(tmp) / "links"
    _skill(r, "real", FM_A + BODY)
    os.symlink(r / "real", r / "link", target_is_directory=True)
    os.symlink(r / "nowhere", r / "dangling")
    p = _plane(r)
    links_ok = (p["names"] == ["link", "real"] and p["symlinked"] == ["link"] and p["non_dir"] == ["dangling"]
                and p["no_skill_md"] == [] and p["entries"] == 3)
    bad_root = os.path.join(os.fsencode(Path(tmp) / "nonutf8"), b"bad\xff")
    os.makedirs(bad_root)
    with open(os.path.join(bad_root, b"SKILL.md"), "wb") as fh:
        fh.write((FM_A + BODY).encode("utf-8"))
    q = sweep.live_plane(Path(tmp) / "nonutf8")
    utf8_ok = q["status"] == "INCONCLUSIVE" and "not UTF-8" in q.get("reason", "")
    return links_ok and utf8_ok, (f"names={p['names']} symlinked={p['symlinked']} non_dir={p['non_dir']} "
                                  f"no_skill_md={p['no_skill_md']}; non-UTF-8 entry: {q['status']}")


POLES = (("SAME-BODY", pole_same_body), ("CRLF", pole_crlf), ("ONE-BYTE", pole_one_byte),
         ("NO-FRONTMATTER", pole_no_frontmatter), ("SAME-NAME-CROSS-PLANE", pole_same_name_cross_plane),
         ("CROSS-PLANE-RENAMED", pole_cross_plane_renamed), ("DISCOVERY", pole_discovery),
         ("EMPTY-BODY", pole_empty_body), ("LISTING-LINE-BOUND", pole_listing_line_bound),
         ("HOST-REPO-REFUSED", pole_host_repo_refused), ("UNREADABLE-INCONCLUSIVE", pole_unreadable_inconclusive),
         ("GIT-UNAVAILABLE", pole_git_unavailable), ("DISCOVERY-LINKS", pole_discovery_links))


def _whole_file_hasher(skill_md_bytes):
    text = smd.lf_bytes(skill_md_bytes)
    m = sweep.skill_index._FM_RE.match(text.decode("utf-8", "surrogateescape"))
    return (m.group(1) if m else None), hashlib.sha256(text).hexdigest(), len(text)


def c_hash_poles():
    lines, all_ok = [], True
    with tempfile.TemporaryDirectory() as tmp:
        for pid, fn in POLES:
            sub = Path(tmp) / pid
            sub.mkdir()
            try:
                ok, ev = fn(sub)
            except (AssertionError, OSError, KeyError, IndexError) as e:
                ok, ev = False, f"{type(e).__name__}: {e}"
            all_ok &= ok
            lines.append(f"{'ok  ' if ok else 'FAIL'} V-FD-POLE-{pid} {ev}")
        real = sweep.body_hash
        sub = Path(tmp) / "MUTANT"
        sub.mkdir()
        try:
            sweep.body_hash = _whole_file_hasher
            mut_ok, ev = pole_same_body(sub)
        finally:
            sweep.body_hash = real
        killed = not mut_ok
        all_ok &= killed
        lines.append(f"{'ok  ' if killed else 'FAIL'} V-FD-MUTANT-WHOLE-FILE-HASHER "
                     f"{'killed by SAME-BODY' if killed else 'SURVIVED SAME-BODY'} ({ev})")
        real_g = sweep.groupable
        sub = Path(tmp) / "MUTANT-EMPTY"
        sub.mkdir()
        try:
            sweep.groupable = lambda rec: True
            mut_ok, ev = pole_empty_body(sub)
        finally:
            sweep.groupable = real_g
        killed = not mut_ok
        all_ok &= killed
        lines.append(f"{'ok  ' if killed else 'FAIL'} V-FD-MUTANT-EMPTY-BODY-GROUPED "
                     f"{'killed by EMPTY-BODY' if killed else 'SURVIVED EMPTY-BODY'} ({ev})")
    head = f"{len(POLES)} poles + 2 mutants"
    if not all_ok:
        fail(head + "\n" + "\n".join(lines))
    return head + "\n" + "\n".join(lines)


# --------------------------------------------------------------------------- tamper drills

def _non_member(rec, label):
    members = {(m["plane"], m["name"]) for g in rec["groups"] for m in g["members"]}
    drift = set(rec["drift_excluded"])
    for n in rec["planes"][label]["names"]:
        if (label, n) not in members and n not in drift:
            return n
    return None


def d_repo_body(rec):
    n = _non_member(rec, "repo")
    rec["planes"]["repo"]["records"][n]["body_sha"] = "0" * 64
    return n


def d_gex44_body(rec):
    # A non-member takes the group's body hash: a hidden duplicate. (A non-member changed to a hash that collides
    # with nothing derives nothing different, so it is a recorded fact only --compare on the measuring host sees.)
    n = _non_member(rec, rec["host"])
    rec["planes"][rec["host"]]["records"][n]["body_sha"] = rec["groups"][0]["body_sha"]
    return n


def d_groups_emptied(rec):
    rec["groups"] = []
    return "groups"


def d_pop_zero(rec):
    rec["planes"][rec["host"]]["skills"] = 0
    return rec["host"]


def d_same_name_inject(rec):
    n = rec["drift_excluded"][0]
    r = rec["planes"]["repo"]["records"][n]
    members = [sweep._member(lb, n, rec["planes"][lb]["records"][n]) for lb in sorted(rec["planes"])]
    rec["groups"].append({"body_sha": r["body_sha"], "body_bytes": r["body_bytes"], "members": members,
                          "names": [n], "distinct_names": 1, "fm_name_collision": False,
                          "skill_md_identical": True, "subset": []})
    return n


def d_distinct_names(rec):
    # The recorded count disagrees with the group's own names: a group whose shape no longer says what it holds.
    g = rec["groups"][0]
    g["distinct_names"] = len(g["names"]) + 1
    return f"group {'+'.join(g['names'])} distinct_names"


def d_member_sha(rec):
    mid = sorted(rec["member_files"])[0]
    lines = rec["member_files"][mid]
    i = next((k for k, (r, _) in enumerate(lines) if r != "SKILL.md"), 0)
    lines[i][1] = "f" * 64
    return f"{mid}:{lines[i][0]}"


DRILLS = (("REPO-BODY", d_repo_body, {"V-FD-REPO-REPRODUCES"}),
          ("GEX44-BODY", d_gex44_body, {"V-FD-GROUPS-REPRODUCE"}),
          ("GROUPS-EMPTIED", d_groups_emptied, {"V-FD-GROUPS-REPRODUCE"}),
          ("POP-ZERO", d_pop_zero, {"V-FD-POP-FLOOR"}),
          ("SAME-NAME-INJECT", d_same_name_inject, {"V-FD-PLANES-APART", "V-FD-GROUPS-REPRODUCE"}),
          ("MEMBER-SHA", d_member_sha, {"V-FD-MEMBER-FILES"}),
          ("DISTINCT-NAMES", d_distinct_names, {"V-FD-PLANES-APART", "V-FD-GROUPS-REPRODUCE"}))


def tamper_drill_rows(name, rec):
    """[(drill id, what was tampered, expected red set, observed red set or None when it could not be built)]."""
    out = []
    for did, fn, expect in DRILLS:
        t = copy.deepcopy(rec)
        try:
            what = fn(t)
        except (KeyError, TypeError, IndexError) as e:
            out.append((did, f"could not be built: {type(e).__name__}: {e}", expect, None))
            continue
        out.append((did, what, expect, {c for c, (st, _) in judge_recording(name, t).items() if st != "ok"}))
    return out


def c_tamper_drills(name, rec):
    lines, all_ok = [], True
    clean = judge_recording(name, copy.deepcopy(rec))
    bad = sorted(c for c, (st, _) in clean.items() if st != "ok")
    if bad:
        inconclusive(f"{name}: clean control does not pass ({bad}); drills cannot be judged")
    lines.append(f"ok   V-FD-DRILL-CLEAN untampered copy passes all {len(clean)} V-FD recording clauses")
    for did, what, expect, got in tamper_drill_rows(name, rec):
        if got is None:
            all_ok = False
            lines.append(f"FAIL V-FD-DRILL-{did} {what}")
            continue
        ok = got == expect
        all_ok &= ok
        lines.append(f"{'ok  ' if ok else 'FAIL'} V-FD-DRILL-{did} ({what}) "
                     + (f"killed by {', '.join(sorted(got))}" if ok else
                        f"expected {sorted(expect)}, red clauses {sorted(got)}"))
    head = f"{name} {len(DRILLS)} drills + clean control"
    if not all_ok:
        fail(head + "\n" + "\n".join(lines))
    return head + "\n" + "\n".join(lines)


# --------------------------------------------------------------------------- operations ledger (D-01 item 2)

OPS_REL = "vault/programs/skill-capability/f-operations.json"
OPS_SCHEMA = "skill-capability/f-operations/1"
WINDOW_SCHEMA = "skill-delivery-window/1"
OPS = ("disclosure", "fission", "fusion", "inline", "dedup")
LISTING_DENOM = "D-LISTING"
LISTING_HOSTS = ("laptop",)          # the D-LISTING plane: recall windows must be measured where the listing is
LISTING_PLANES = ("repo", "laptop")  # sweep planes whose members the laptop listing can describe
SIDES = ("before", "after")
ENTRY_CLAUSES = ("V-FO-OP", "V-FO-BEFORE", "V-FO-AFTER", "V-FO-PAIR", "V-FO-RECALL", "V-FO-HELPED",
                 "V-FO-RECALL-HELD", "V-FO-DEDUP-SWEEP", "V-FO-PLANE")
GOOD = ("ok", "n/a")


def _evidence_json_path(p) -> bool:
    """A repo path under the evidence directory ending .json, with no `..` and no backslash."""
    return (isinstance(p, str) and p.startswith(EVIDENCE_DIR) and p.endswith(".json") and "\\" not in p
            and ".." not in Path(p).parts and len(p) > len(EVIDENCE_DIR) + len(".json"))


def _nonempty(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _side(entry, key, rows, denoms):
    """(status, text, (row index, startup_tokens, listing_chars) or None) for entry[key] = before / after."""
    s = entry.get(key)
    if not isinstance(s, dict):
        return "FAIL", f"UNMEASURED: {key} is {type(s).__name__}, not a D-LISTING row reference", None
    d = s.get("denominator")
    if d != LISTING_DENOM:
        return "FAIL", f"{key}.denominator {d!r} is not {LISTING_DENOM} (the frozen rule names D-LISTING)", None
    if d not in denoms:
        return "FAIL", f"{key}.denominator {d!r} is not a frozen denominator of the ledger", None
    if not _nonempty(s.get("command")):
        return "FAIL", f"UNMEASURED: {key}.command is absent (a measurement records its command)", None
    label, sid = s.get("probe_label"), s.get("session_id")
    if not (_nonempty(label) and _nonempty(sid)):
        return "FAIL", f"UNMEASURED: {key} names no probe_label AND session_id", None
    hits = [i for i, r in enumerate(rows) if isinstance(r, dict) and r.get("label") == label
            and r.get("session_id") == sid]
    if len(hits) != 1:
        return "FAIL", (f"UNMEASURED: {len(hits)} probe rows carry label {label!r} and session {sid!r} "
                        "(need exactly 1)"), None
    i = hits[0]
    r = rows[i]
    if not (lfv._is_int(r.get("rc")) and r["rc"] == 0 and r.get("result") == "OK"):
        return "FAIL", f"UNMEASURED: {key} row #{i} rc={r.get('rc')!r} result={str(r.get('result'))[:60]!r}", None
    # A row appended from another host resolves by label and session id just as well; only a row derived to the
    # D-LISTING plane measures the listing the frozen rule names (05-REVIEW WR-03).
    plane = _row_plane(r)
    if plane not in LISTING_HOSTS:
        return "FAIL", (f"UNMEASURED: {key} row #{i} plane {plane} is not the D-LISTING plane {list(LISTING_HOSTS)} "
                        "(cwd or settings_file under the laptop profile)"), None
    tok = r.get("startup_tokens")
    listing = r.get("listing")
    chars = listing.get("chars") if isinstance(listing, dict) else None
    for what, v in (("startup_tokens", tok), ("listing.chars", chars)):
        if not lfv._is_int(v) or v <= 0:
            return "FAIL", (f"UNMEASURED: {key} row #{i} {what}={v!r} (absent, zero or non-int is no "
                            "measurement)"), None
    return "ok", (f"{key} {label} session {sid[:8]} row #{i}: startup_tokens={tok}, listing_chars={chars}"), \
        (i, tok, chars)


def check_entry(entry, rows, docs, sweeps, noise, denoms):
    """[(clause, status, text)] for one applied operation, in ENTRY_CLAUSES order. Pure. status is ok / FAIL /
    INCONCLUSIVE / n/a / skipped; skipped = an upstream clause of this entry is not ok (the entry already fails), and
    is never counted as ok. Every figure comes from `rows` / `docs` / `sweeps`, never from the entry."""
    out = {}
    if not isinstance(entry, dict):
        return [(c, "FAIL", f"entry is {type(entry).__name__}, not an object") for c in ENTRY_CLAUSES]
    op, skill = entry.get("op"), entry.get("skill")
    if op not in OPS:
        out["V-FO-OP"] = ("FAIL", f"op {op!r} not in {list(OPS)}")
    elif not _nonempty(skill):
        out["V-FO-OP"] = ("FAIL", f"skill {skill!r} is not a non-empty string")
    else:
        out["V-FO-OP"] = ("ok", f"op {op} on skill {skill}")
    side = {}
    for key, cid in (("before", "V-FO-BEFORE"), ("after", "V-FO-AFTER")):
        st, text, data = _side(entry, key, rows, denoms)
        out[cid] = (st, text)
        side[key] = data
    both = out["V-FO-BEFORE"][0] == "ok" and out["V-FO-AFTER"][0] == "ok"
    if not both:
        out["V-FO-PAIR"] = ("skipped", "before or after not ok")
    else:
        bi, ai = side["before"][0], side["after"][0]
        if bi == ai:
            out["V-FO-PAIR"] = ("FAIL", f"before and after resolve to the same row #{bi}")
        elif bi > ai:
            out["V-FO-PAIR"] = ("FAIL", f"before row #{bi} comes after the after row #{ai} in the append-only rows")
        else:
            out["V-FO-PAIR"] = ("ok", f"before row #{bi} precedes after row #{ai}")
    st, text, rec = _recall(entry, docs)
    out["V-FO-RECALL"] = (st, text)
    if not both:
        out["V-FO-HELPED"] = ("skipped", "before or after not ok")
    elif not isinstance(noise, dict) or not lfv._is_int(noise.get("tokens")) or noise["tokens"] <= 0:
        out["V-FO-HELPED"] = ("INCONCLUSIVE", "noise not sourced: whether the op helped cannot be judged")
    else:
        b, a, nz = side["before"][1], side["after"][1], noise["tokens"]
        verdict = "ok" if a + nz < b else "FAIL"
        out["V-FO-HELPED"] = (verdict, (f"after startup_tokens {a} + noise {nz} {'<' if verdict == 'ok' else '>='} "
                                        f"before {b} (noise: {noise.get('source', 'sourced')} line "
                                        f"{noise.get('line')})" + ("" if verdict == "ok" else
                                                                   ": not measured to help")))
    if st != "ok":
        out["V-FO-RECALL-HELD"] = ("skipped", "recall not ok")
    else:
        (bn, bd), (an, ad) = rec["before"], rec["after"]
        held = an * bd >= bn * ad
        out["V-FO-RECALL-HELD"] = ("ok" if held else "FAIL",
                                   f"recall after {an}/{ad} {'>=' if held else '<'} before {bn}/{bd}"
                                   + ("" if held else ": recall dropped"))
    if op != "dedup":
        out["V-FO-DEDUP-SWEEP"] = ("n/a", f"op {op!r} is not dedup")
        out["V-FO-PLANE"] = ("n/a", f"op {op!r} is not dedup")
    else:
        st, text, grp = _dedup_sweep(entry, sweeps)
        out["V-FO-DEDUP-SWEEP"] = (st, text)
        if st != "ok":
            out["V-FO-PLANE"] = ("skipped", "dedup sweep not ok")
        else:
            planes = sorted({m["plane"] for m in grp["members"] if m["name"] == skill})
            off = [p for p in planes if p not in LISTING_PLANES]
            out["V-FO-PLANE"] = (("FAIL", f"member on plane {off[0]}: D-LISTING measures the laptop listing")
                                 if off else ("ok", f"{skill} sits on plane(s) {planes}, all in {list(LISTING_PLANES)}"))
    return [(c,) + out[c] for c in ENTRY_CLAUSES]


def _utc_epoch(v):
    """Seconds since the epoch for an ISO-8601 timestamp that carries a timezone (`Z` accepted), else None."""
    if not isinstance(v, str) or not v.strip():
        return None
    try:
        t = datetime.datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.timestamp() if t.tzinfo is not None else None


class Unjudged:
    """A window the entry names that exists in the working tree but is not committed (as committed): never judged,
    so the recall clause reads INCONCLUSIVE, not FAIL (05-REVIEW IN-05)."""

    def __init__(self, why):
        self.why = why


def _recall(entry, docs):
    """(status, text, {side: (num, n)} or None). Figures come from the committed window documents only."""
    rc = entry.get("recall")
    if not isinstance(rc, dict):
        return "FAIL", "UNMEASURED: recall is absent (the frozen rule requires a recall check)", None
    paths = {}
    for k in SIDES:
        s = rc.get(k)
        if not isinstance(s, dict):
            return "FAIL", f"UNMEASURED: recall.{k} is absent", None
        if not _evidence_json_path(s.get("window")):
            return "FAIL", f"recall.{k}.window {s.get('window')!r} is not a .json path under {EVIDENCE_DIR}", None
        if not _nonempty(s.get("command")):
            return "FAIL", f"UNMEASURED: recall.{k}.command is absent", None
        paths[k] = s["window"]
    if paths["before"] == paths["after"]:
        return "FAIL", f"recall before and after name the same window {paths['before']}", None
    got, hosts, spans = {}, set(), {}
    for k in SIDES:
        w = paths[k]
        doc = docs.get(w)
        if isinstance(doc, Unjudged):
            return "INCONCLUSIVE", f"recall.{k} window {w}: {doc.why} (an uncommitted input is never judged)", None
        if not isinstance(doc, dict):
            return "FAIL", f"UNMEASURED: recall.{k} window {w} is not a committed window document", None
        if doc.get("schema") != WINDOW_SCHEMA:
            return "FAIL", f"{w} schema {doc.get('schema')!r} != {WINDOW_SCHEMA!r}", None
        if doc.get("capability") != entry.get("skill"):
            return "FAIL", f"{w} capability {doc.get('capability')!r} != skill {entry.get('skill')!r}", None
        r = doc.get("recall")
        if not isinstance(r, dict):
            return "FAIL", f"UNMEASURED: {w} recall is {r!r}", None
        num, n = r.get("num"), r.get("n")
        if not (lfv._is_int(num) and lfv._is_int(n)) or n <= 0 or not 0 <= num <= n:
            return "FAIL", f"UNMEASURED: {w} recall num={num!r} n={n!r} (n > 0 and 0 <= num <= n required)", None
        start, end = _utc_epoch(doc.get("start")), _utc_epoch(doc.get("end"))
        if start is None or end is None or not start < end:
            return "FAIL", (f"UNMEASURED: {w} start={doc.get('start')!r} end={doc.get('end')!r} (two timezone-bearing "
                            "timestamps with start < end required)"), None
        spans[k] = (start, end)
        got[k] = (num, n)
        hosts.add(doc.get("host"))
    # Two filenames for one measurement, or an "after" measured before the "before", would satisfy the recall check
    # without any post-operation measurement (05-REVIEW WR-02).
    if not spans["before"][1] <= spans["after"][0]:
        return "FAIL", (f"recall before window {paths['before']} (end {docs[paths['before']].get('end')}) does not end "
                        f"by the start of the after window {paths['after']} ({docs[paths['after']].get('start')}): "
                        "no post-operation measurement"), None
    if len(hosts) != 1:
        return "FAIL", f"recall windows come from different hosts {sorted(map(str, hosts))}", None
    host = hosts.pop()
    if host not in LISTING_HOSTS:
        return "FAIL", (f"recall windows host {host!r} is not the D-LISTING plane {list(LISTING_HOSTS)}: recall must "
                        "be measured where the listing is"), None
    return "ok", (f"recall before {got['before'][0]}/{got['before'][1]} ({paths['before']}), after "
                  f"{got['after'][0]}/{got['after'][1]} ({paths['after']}), host {host}; n is reported per rate"), got


def _dedup_sweep(entry, sweeps):
    """(status, text, re-derived group or None). Only a group re-derived from an admitted recording counts."""
    ref, grp_sha, skill = entry.get("sweep"), entry.get("group"), entry.get("skill")
    if not isinstance(ref, str) or ref not in sweeps:
        return "FAIL", (f"sweep {ref!r} is not a committed recording that passed every V-FD clause "
                        f"(admitted: {sorted(sweeps)})"), None
    if not (isinstance(grp_sha, str) and len(grp_sha) == 64 and set(grp_sha) <= HEX):
        return "FAIL", f"group {grp_sha!r} is not 64-hex", None
    grps, _ = sweep.groups(sweeps[ref]["planes"])
    g = next((x for x in grps if x["body_sha"] == grp_sha), None)
    if g is None:
        return "FAIL", f"group {grp_sha[:12]} is not re-derived from {ref} ({len(grps)} groups there)", None
    names = sorted({m["name"] for m in g["members"]})
    if skill not in names:
        return "FAIL", f"skill {skill!r} is not a member of group {grp_sha[:12]} {names}", None
    return "ok", f"group {grp_sha[:12]} re-derived from {ref}: members {names}", g


def parse_ops(raw: bytes, rule):
    """The operations document from bytes, or raises Clause. `rule` = the frozen F rule (None skips that check)."""
    try:
        doc = json.loads(smd.lf_bytes(raw).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        fail(f"not JSON: {e}")
    if not isinstance(doc, dict):
        fail("not a JSON object")
    if doc.get("schema") != OPS_SCHEMA:
        fail(f"schema {doc.get('schema')!r} != {OPS_SCHEMA!r}")
    if rule is not None and doc.get("rule") != rule:
        fail("rule is not the frozen F rule of the ledger, verbatim")
    if not _nonempty(doc.get("note")):
        fail("note is absent")
    ops = doc.get("operations")
    if not isinstance(ops, list) or not all(isinstance(e, dict) for e in ops):
        fail("operations is not a list of objects")
    return doc


def frozen_f():
    """(frozen F rule text, set of frozen denominator keys, frozen denominators) from the ledger. Read only."""
    fr = lfv.frozen()
    rule = next((p.get("rule") for p in fr.get("pillars", []) if p.get("id") == "F"), None)
    return rule, set(fr.get("denominators", {})), fr.get("denominators", {})


def read_ops(path=None, rule=None):
    """(doc, None) or raises Clause. Default: the COMMITTED file at HEAD (05-01 posture: an uncommitted copy is
    INCONCLUSIVE, never judged). `path`: that file as it is on disk (the red entrance)."""
    p = Path(path) if path else REPO / OPS_REL
    if not p.is_file():
        fail(f"{path or OPS_REL} absent: absent is not zero operations")
    if path:
        raw = p.read_bytes()
    else:
        raw, why = smd.committed_bytes(REPO, OPS_REL)
        if raw is None:
            inconclusive(why)
    return parse_ops(raw, rule)


def c_fo_file(path=None, rule=None):
    doc = read_ops(path, rule)
    return (f"{path or OPS_REL} schema {OPS_SCHEMA}, rule = frozen F rule, {len(doc['operations'])} entries"
            + ("" if path else " (committed blob at HEAD)")), doc


def committed_json(rel):
    """(doc, None) or (None, reason) for a committed JSON file at HEAD."""
    raw, why = smd.committed_bytes(REPO, rel)
    if raw is None:
        return None, why
    try:
        return json.loads(smd.lf_bytes(raw).decode("utf-8")), None
    except (ValueError, UnicodeDecodeError) as e:
        return None, f"{rel} is not JSON: {e}"


def probe_rows():
    """(rows, None) or (None, reason). The rows are the committed probe results (append-only)."""
    raw, why = smd.committed_bytes(REPO, lfv.JSONL_REL)
    if raw is None:
        return None, why
    try:
        return lfv.load_rows(REPO / lfv.JSONL_REL), None
    except (OSError, ValueError) as e:
        return None, f"{lfv.JSONL_REL} unreadable: {e}"


def window_docs(ops):
    """{rel: committed window doc, or Unjudged(reason) for one present but not committed as is} for every window path
    the entries name that passes the path rule."""
    docs = {}
    for e in ops:
        rc = e.get("recall") if isinstance(e, dict) else None
        for k in SIDES:
            w = (rc.get(k) or {}).get("window") if isinstance(rc, dict) and isinstance(rc.get(k), dict) else None
            if _evidence_json_path(w) and w not in docs:
                doc, why = committed_json(w)
                if doc is not None:
                    docs[w] = doc
                elif str(why).startswith("uncommitted") or (REPO / w).is_file():
                    docs[w] = Unjudged(why)  # present but not committed as is; an absent window stays FAIL
    return docs


def c_fo_entries(doc, inputs):
    ops = doc["operations"]
    if not ops:
        host = " host gex44 per f-operations.json note" if "gex44" in doc.get("note", "") else ""
        return f"0 operations applied (n=0,{host})".replace(",)", ")")
    if inputs.get("rows") is None:
        inconclusive(f"{len(ops)} entries, probe rows unreadable: {inputs.get('rows_why')}")
    bad, statuses = [], set()
    for i, e in enumerate(ops):
        res = check_entry(e, inputs["rows"], inputs["docs"], inputs["sweeps"], inputs["noise"], inputs["denoms"])
        red = [f"{c} {st}: {t}" for c, st, t in res if st not in GOOD]
        statuses |= {st for _, st, _ in res if st not in GOOD + ("skipped",)}
        if red:
            bad.append(f"entry #{i} ({e.get('op')!r}, {e.get('skill')!r}): " + "; ".join(red))
    if bad and statuses == {"INCONCLUSIVE"}:
        # Every refusal is "could not judge" (an uncommitted window, unsourced noise): the entry is not malformed.
        inconclusive(f"{len(bad)} of {len(ops)} entries not judged\n" + "\n".join(bad))
    if bad:
        fail(f"{len(bad)} of {len(ops)} entries refused\n" + "\n".join(bad))
    return f"{len(ops)} operations applied, every clause ok or n/a"


def sourced_noise():
    """({tokens, line, source}, None) or (None, reason): the K4 noise of the committed lessons file, through the
    parser phase 2 already sources (`lfv.bounds_parse`)."""
    raw, why = smd.committed_bytes(REPO, lfv.LESSONS_REL)
    if raw is None:
        return None, why
    noise = lfv.bounds_parse(None, smd.lf_bytes(raw).decode("utf-8"))[1]
    if not noise or not lfv._is_int(noise.get("tokens")) or noise["tokens"] <= 0:
        return None, f"{lfv.LESSONS_REL} carries no `noise +-<k>k` figure"
    return dict(noise, source=lfv.LESSONS_REL), None


def c_fo_noise_sourced():
    noise, why = sourced_noise()
    if noise is None:
        inconclusive(f"{why}: V-FO-HELPED could not be evaluated for any future entry")
    return f"noise {noise['tokens']} tokens from {noise['source']} line {noise['line']}"


def operations_inputs(ops, sweeps):
    rows, rows_why = probe_rows()
    return {"rows": rows, "rows_why": rows_why, "docs": window_docs(ops), "sweeps": sweeps,
            "noise": sourced_noise()[0], "denoms": frozen_f()[1]}


# --------------------------------------------------------------------------- V-FO drills (fixtures + real data)

DRILL_SKILL = "drill-skill"
DRILL_W = {"before": EVIDENCE_DIR + "C-window-DRILL-before.json", "after": EVIDENCE_DIR + "C-window-DRILL-after.json"}
DRILL_SWEEP = EVIDENCE_DIR + "F-sweep-laptop.json"
DRILL_NOISE = {"tokens": 1500, "line": 0, "source": "drill fixture"}
DRILL_SIDS = {"before": "00000000-0000-4000-8000-0000000000b0", "after": "00000000-0000-4000-8000-0000000000a0"}
_DRILL_BODY = hashlib.sha256(b"drill body").hexdigest()
_DRILL_OTHER = hashlib.sha256(b"drill other").hexdigest()


def _drill_row(label, sid, tokens, chars):
    return {"label": label, "session_id": sid, "rc": 0, "result": "OK", "startup_tokens": tokens,
            "listing": {"chars": chars}, "cwd": LAPTOP_PROFILE + "drill"}


DRILL_SPANS = {"before": ("2026-09-01T00:00:00Z", "2026-09-08T00:00:00Z"),
               "after": ("2026-09-10T00:00:00Z", "2026-09-17T00:00:00Z")}


def _drill_window(num, n, cap=DRILL_SKILL, host="laptop", span=DRILL_SPANS["before"]):
    return {"schema": WINDOW_SCHEMA, "capability": cap, "host": host, "recall": {"num": num, "n": n},
            "start": span[0], "end": span[1]}


def _drill_record(body_sha, fm):
    return {"body_bytes": 10, "body_sha": body_sha, "dir_digest": body_sha, "files": 1, "fm_name": fm,
            "has_frontmatter": True, "skill_md_sha": body_sha}


def _side_ref(label, sid):
    return {"denominator": LISTING_DENOM, "probe_label": label, "session_id": sid,
            "command": "python wiki/tools/listing_floor_probe.py --label " + label}


def base_fixture(denoms):
    """A fully formed fabricated disclosure entry and the committed-looking inputs it references."""
    entry = {"op": "disclosure", "skill": DRILL_SKILL,
             "before": _side_ref("drill-before", DRILL_SIDS["before"]),
             "after": _side_ref("drill-after", DRILL_SIDS["after"]),
             "recall": {k: {"window": DRILL_W[k], "command": "python3 tools/test_skill_delivery.py --measure-live"}
                        for k in SIDES}}
    rows = [_drill_row("unrelated", "00000000-0000-4000-8000-000000000000", 70000, 25000),
            _drill_row("drill-before", DRILL_SIDS["before"], 90000, 30000),
            _drill_row("drill-after", DRILL_SIDS["after"], 80000, 29000)]
    docs = {DRILL_W["before"]: _drill_window(4, 5, span=DRILL_SPANS["before"]),
            DRILL_W["after"]: _drill_window(5, 5, span=DRILL_SPANS["after"])}
    rec = {"planes": {"repo": {"records": {}},
                      "laptop": {"records": {DRILL_SKILL: _drill_record(_DRILL_BODY, DRILL_SKILL),
                                             DRILL_SKILL + "-copy": _drill_record(_DRILL_BODY, DRILL_SKILL),
                                             "drill-other": _drill_record(_DRILL_OTHER, "drill-other")}}}}
    return {"entry": entry, "rows": rows, "docs": docs, "sweeps": {DRILL_SWEEP: rec}, "noise": dict(DRILL_NOISE),
            "denoms": set(denoms)}


def _as_dedup(fx):
    fx["entry"].update(op="dedup", sweep=DRILL_SWEEP, group=_DRILL_BODY)


def _m_dedup_control(fx):
    _as_dedup(fx)


def _m_op_outside(fx):
    fx["entry"]["op"] = "rename"


def _m_missing_after(fx):
    del fx["entry"]["after"]


def _m_wrong_denom(fx):
    fx["entry"]["before"]["denominator"] = "D-CARD"


def _m_zero_tokens(fx):
    fx["rows"][1]["startup_tokens"] = 0


def _m_session_mismatch(fx):
    fx["entry"]["after"]["session_id"] = DRILL_SIDS["before"]


def _m_row_plane(fx):
    fx["rows"][2]["cwd"] = "/home/x"  # an after row appended from another host: not a D-LISTING measurement


def _m_ambiguous(fx):
    fx["rows"].append(copy.deepcopy(fx["rows"][1]))


def _m_order(fx):
    fx["rows"][1], fx["rows"][2] = fx["rows"][2], fx["rows"][1]


def _m_missing_recall(fx):
    del fx["entry"]["recall"]


def _m_recall_null(fx):
    fx["docs"][DRILL_W["after"]]["recall"] = None  # the C-window-G shape


def _m_recall_n0(fx):
    fx["docs"][DRILL_W["before"]]["recall"] = {"num": 0, "n": 0}


def _m_recall_wrong_cap(fx):
    fx["docs"][DRILL_W["after"]]["capability"] = "some-other-skill"


def _m_recall_wrong_host(fx):
    for k in SIDES:
        fx["docs"][DRILL_W[k]]["host"] = "gex44"


def _m_recall_duplicate(fx):
    fx["docs"][DRILL_W["after"]] = copy.deepcopy(fx["docs"][DRILL_W["before"]])  # one measurement, two filenames


def _m_recall_order(fx):
    fx["docs"][DRILL_W["before"]]["start"], fx["docs"][DRILL_W["before"]]["end"] = DRILL_SPANS["after"]
    fx["docs"][DRILL_W["after"]]["start"], fx["docs"][DRILL_W["after"]]["end"] = DRILL_SPANS["before"]


def _m_recall_untimed(fx):
    del fx["docs"][DRILL_W["after"]]["start"]


def _m_not_helped(fx):
    fx["rows"][2]["startup_tokens"] = fx["rows"][1]["startup_tokens"] - fx["noise"]["tokens"]  # the boundary


def _m_noise_absent(fx):
    fx["noise"] = None


def _m_recall_drop(fx):
    fx["docs"][DRILL_W["after"]]["recall"] = {"num": 3, "n": 5}


def _m_dedup_not_in_sweep(fx):
    _as_dedup(fx)
    fx["entry"]["group"] = "0" * 64


def _m_dedup_not_member(fx):
    _as_dedup(fx)
    recs = fx["sweeps"][DRILL_SWEEP]["planes"]["laptop"]["records"]
    recs[DRILL_SKILL + "-alt"] = recs.pop(DRILL_SKILL)


def _m_dedup_gex44_real(fx, real):
    """The committed gex44 recording and its real sleepy group, recast as a dedup of sleepy-skills."""
    rec = real["sweeps"].get(EVIDENCE_DIR + GEX44_NAME)
    if rec is None:
        raise KeyError(f"{GEX44_NAME} is not an admitted recording")
    g = next((x for x in sweep.groups(rec["planes"])[0] if "sleepy-skills" in x["names"]), None)
    if g is None:
        raise KeyError("the gex44 recording re-derives no group holding sleepy-skills")
    fx["entry"].update(op="dedup", skill="sleepy-skills", sweep=EVIDENCE_DIR + GEX44_NAME, group=g["body_sha"])
    fx["sweeps"] = {EVIDENCE_DIR + GEX44_NAME: rec}
    for k in SIDES:
        fx["docs"][DRILL_W[k]]["capability"] = "sleepy-skills"


def _m_k4_real(fx, real):
    """The committed K4 rows pinned by session id, recast as a disclosure op, with the sourced noise."""
    if real["rows"] is None:
        raise KeyError("committed probe rows unreadable")
    fx["rows"] = real["rows"]
    fx["noise"] = real["noise"]
    fx["entry"]["before"] = _side_ref("champion-startup", sweep.K4_SESSIONS["champion"])
    fx["entry"]["after"] = _side_ref("challenger-startup", sweep.K4_SESSIONS["challenger"])


FO_DRILLS = (
    ("POSITIVE-CONTROL", None, set()),
    ("POSITIVE-CONTROL-DEDUP", _m_dedup_control, set()),
    ("OP-OUTSIDE", _m_op_outside, {"V-FO-OP"}),
    ("MISSING-AFTER", _m_missing_after, {"V-FO-AFTER"}),
    ("WRONG-DENOM", _m_wrong_denom, {"V-FO-BEFORE"}),
    ("ZERO-TOKENS", _m_zero_tokens, {"V-FO-BEFORE"}),
    ("SESSION-MISMATCH", _m_session_mismatch, {"V-FO-AFTER"}),
    ("AMBIGUOUS-LABEL", _m_ambiguous, {"V-FO-BEFORE"}),
    ("ROW-PLANE", _m_row_plane, {"V-FO-AFTER"}),
    ("ORDER", _m_order, {"V-FO-PAIR"}),
    ("MISSING-RECALL", _m_missing_recall, {"V-FO-RECALL"}),
    ("RECALL-NULL", _m_recall_null, {"V-FO-RECALL"}),
    ("RECALL-N0", _m_recall_n0, {"V-FO-RECALL"}),
    ("RECALL-WRONG-CAP", _m_recall_wrong_cap, {"V-FO-RECALL"}),
    ("RECALL-WRONG-HOST", _m_recall_wrong_host, {"V-FO-RECALL"}),
    ("RECALL-DUPLICATE", _m_recall_duplicate, {"V-FO-RECALL"}),
    ("RECALL-ORDER", _m_recall_order, {"V-FO-RECALL"}),
    ("RECALL-UNTIMED", _m_recall_untimed, {"V-FO-RECALL"}),
    ("NOT-HELPED", _m_not_helped, {"V-FO-HELPED"}),
    ("NOISE-ABSENT", _m_noise_absent, {"V-FO-HELPED"}),
    ("RECALL-DROP", _m_recall_drop, {"V-FO-RECALL-HELD"}),
    ("DEDUP-NOT-IN-SWEEP", _m_dedup_not_in_sweep, {"V-FO-DEDUP-SWEEP"}),
    ("DEDUP-NOT-MEMBER", _m_dedup_not_member, {"V-FO-DEDUP-SWEEP"}),
    ("DEDUP-GEX44-REAL", _m_dedup_gex44_real, {"V-FO-PLANE"}),
    ("K4-REAL", _m_k4_real, {"V-FO-HELPED"}),
)
_REAL_DRILLS = {"DEDUP-GEX44-REAL", "K4-REAL"}


def fo_drill_rows(real):
    """[(name, expected red set, observed red set or None, text)]. `real` = {rows, noise, sweeps, denoms} from the
    committed inputs. A mutant passes when its FAIL/INCONCLUSIVE set is EXACTLY the expected one (skipped and n/a
    are excluded); a positive control passes when that set is empty."""
    out = []
    for name, mutate, expect in FO_DRILLS:
        fx = base_fixture(real["denoms"])
        try:
            if mutate is not None:
                mutate(fx, real) if name in _REAL_DRILLS else mutate(fx)
        except (KeyError, TypeError, IndexError) as e:
            out.append((name, expect, None, f"could not be built: {type(e).__name__}: {e}"))
            continue
        res = check_entry(fx["entry"], fx["rows"], fx["docs"], fx["sweeps"], fx["noise"], fx["denoms"])
        red = {c for c, st, _ in res if st in ("FAIL", "INCONCLUSIVE")}
        text = "; ".join(t for c, st, t in res if c in red) if red else ""
        out.append((name, expect, red, text))
    return out


def fo_entries_status_rows(real):
    """[(name, expected V-FO-ENTRIES status, observed status, text)]: the entry-level status, driven through
    window_docs + c_fo_entries (05-REVIEW IN-05). An uncommitted window, or unsourced noise, is INCONCLUSIVE (an
    uncommitted input is never judged); a real refusal next to it stays FAIL."""
    global committed_json
    out = []
    real_cj = committed_json
    for name, expect in (("UNCOMMITTED-WINDOW", "INCONCLUSIVE"), ("NOISE-UNSOURCED", "INCONCLUSIVE"),
                         ("UNCOMMITTED-AND-DROP", "FAIL")):
        fx = base_fixture(real["denoms"])
        if name == "NOISE-UNSOURCED":
            fx["noise"] = None
            docs = fx["docs"]
        else:
            committed_json = lambda rel: (None, f"uncommitted: working-tree {rel} differs from HEAD (pole)")
            try:
                docs = window_docs([fx["entry"]])
            finally:
                committed_json = real_cj
            if name == "UNCOMMITTED-AND-DROP":
                fx["rows"][2]["startup_tokens"] = fx["rows"][1]["startup_tokens"]  # also not measured to help
        inputs = {"rows": fx["rows"], "docs": docs, "sweeps": fx["sweeps"], "noise": fx["noise"],
                  "denoms": fx["denoms"]}
        st, text = run_clause(c_fo_entries, {"operations": [fx["entry"]], "note": "pole"}, inputs)
        out.append((name, expect, st, str(text).split("\n")[-1][:160]))
    return out


def c_fo_drills(real):
    lines, all_ok = [], True
    for name, expect, got, text in fo_entries_status_rows(real):
        ok = got == expect
        all_ok &= ok
        lines.append(f"{'ok  ' if ok else 'FAIL'} V-FO-ENTRIES-STATUS-{name} expected {expect}, got {got} ({text})")
    for name, expect, got, text in fo_drill_rows(real):
        ok = got is not None and got == expect
        all_ok &= ok
        if got is None:
            lines.append(f"FAIL V-FO-DRILL-{name} {text}")
        elif not expect:
            lines.append(f"{'ok  ' if ok else 'FAIL'} V-FO-DRILL-{name} "
                         + ("passes all clauses" if ok else f"red clauses {sorted(got)}: {text}"))
        else:
            lines.append(f"{'ok  ' if ok else 'FAIL'} V-FO-DRILL-{name} "
                         + (f"killed by {', '.join(sorted(got))} ({text})" if ok else
                            f"expected {sorted(expect)}, red clauses {sorted(got)}: {text}"))
    head = f"{len(FO_DRILLS)} drills ({sum(1 for _, _, e in FO_DRILLS if not e)} positive controls)"
    if not all_ok:
        fail(head + "\n" + "\n".join(lines))
    return head + "\n" + "\n".join(lines)


SELF = Path(__file__).resolve()
SUBPROCESS_TIMEOUT_S = 120
RECALL_ABSENT_RE = re.compile(r"(^|; |: )V-FO-RECALL FAIL: UNMEASURED: recall is absent", re.M)


def c_fo_subprocess_poles(real):
    """The --operations entrance across a real process boundary: red on a fabricated entry without a recall check,
    green on the committed file. --operations never runs drills or subprocesses (no recursion)."""
    if real["rows"] is None:
        inconclusive("committed probe rows unreadable: the red pole cannot reference real rows")
    rule = frozen_f()[0]
    fx = base_fixture(real["denoms"])
    _m_k4_real(fx, real)
    del fx["entry"]["recall"]
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "f-operations-no-recall.json"
        bad.write_bytes((json.dumps({"schema": OPS_SCHEMA, "rule": rule, "note": "subprocess pole (fabricated)",
                                     "operations": [fx["entry"]]}, indent=1) + "\n").encode("utf-8"))
        runs = []
        for path in (str(bad), OPS_REL):
            try:
                r = subprocess.run([sys.executable, str(SELF), "--operations", path], cwd=str(REPO),
                                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   timeout=SUBPROCESS_TIMEOUT_S)
            except (OSError, subprocess.TimeoutExpired) as e:
                inconclusive(f"--operations {path} did not complete: {type(e).__name__}: {e}")
            runs.append((r.returncode, r.stdout))
    (rc_bad, out_bad), (rc_ok, out_ok) = runs
    # The recall clause must be the named reason, token-exact: a bare "V-FO-RECALL" substring is also matched by
    # "V-FO-RECALL-HELD skipped: recall not ok", which a mutant that waves an absent recall through still prints
    # (05-REVIEW WR-01). The K4 rows are refused by V-FO-HELPED too, so rc 1 alone proves nothing about recall.
    red_ok = (rc_bad == 1 and "FAIL V-FO-ENTRIES" in out_bad
              and RECALL_ABSENT_RE.search(out_bad) is not None)
    green_ok = rc_ok == 0 and "ok   V-FO-ENTRIES" in out_ok
    text = (f"red pole (K4 rows, recall deleted) rc={rc_bad} {'names' if red_ok else 'lacks'} FAIL V-FO-ENTRIES + "
            f"V-FO-RECALL; green pole ({OPS_REL}) rc={rc_ok}")
    if not (red_ok and green_ok):
        fail(text + "\n" + out_bad[-800:] + "\n" + out_ok[-800:])
    return text


# --------------------------------------------------------------------------- rendered prg evidence (D-03)

FR_EVIDENCE_REL = EVIDENCE_DIR + "F-representation.md"
# D-01: this phase runs no fresh session (a statement about this phase, not a measurement).
FRESH_SESSIONS_THIS_PHASE = 0
LAPTOP_PROFILE = "C:\\Users\\User\\"
# Render sources read from the working tree; a dirty one makes V-FR-EVIDENCE-CURRENT INCONCLUSIVE rather than judging
# the committed evidence against an uncommitted world (phase 4 posture). The ledger is read for its frozen section
# only, which the CE verifier pins, so it is not listed.
RENDER_SOURCES = (OPS_REL, lfv.JSONL_REL, lfv.LESSONS_REL, EVIDENCE_DIR + SWEEP_GLOB)

ENTRY_SCHEMA_LINES = (
    "`op`: one of disclosure, fission, fusion, inline, dedup; `skill`: the skill name.",
    "`before` / `after`: {`denominator`: \"D-LISTING\", `probe_label`, `session_id`, `command`}: a reference to ONE "
    "row of the D-LISTING probe results, resolved by label AND session id. No figure is typed: startup_tokens and "
    "listing chars are read from that row.",
    "`recall`: {`before`: {`window`, `command`}, `after`: {`window`, `command`}}: committed skill-delivery windows "
    "(`skill-delivery-window/1`) under the evidence directory; num and n are read from them, and their `start` / "
    "`end` order them (the before window ends by the after window's start).",
    "dedup only: `sweep` (a committed `F-sweep-*.json` recording) and `group` (the 64-hex body_sha of a group "
    "re-derived from it).",
)

FO_CLAUSE_DOC = (
    ("V-FO-FILE", "an absent, malformed or other-schema operations file, or one whose rule is not the frozen F rule "
                  "verbatim (absent is never zero operations)"),
    ("V-FO-ENTRIES", "any entry with a clause that is not ok or n/a (INCONCLUSIVE when every such clause is "
                     "INCONCLUSIVE)"),
    ("V-FO-OP", "an op outside {disclosure, fission, fusion, inline, dedup}, or no skill"),
    ("V-FO-BEFORE", "a before side that is missing, not D-LISTING or without its command, or that resolves to zero "
                    "or several probe rows by label AND session id, or to a row with rc != 0, result != OK, a row "
                    "not derived to the laptop plane (cwd or settings_file under the laptop profile), or a "
                    "zero / non-int figure (UNMEASURED)"),
    ("V-FO-AFTER", "an after side with any defect V-FO-BEFORE refuses"),
    ("V-FO-PAIR", "before and after resolving to one row, or the after row preceding the before row in the "
                  "append-only rows"),
    ("V-FO-RECALL", "a missing recall check; a window outside the evidence directory, absent, of another schema "
                    "or capability (one present but uncommitted is INCONCLUSIVE, never judged); a null recall, n = 0, num outside [0, n]; a window without timezone-bearing start < end, or a "
                    "before window that does not end by the after window's start (one window twice, or reversed); "
                    "windows from two hosts, or from a host that is not the D-LISTING plane (laptop)"),
    ("V-FO-HELPED", "after startup_tokens + sourced noise >= before startup_tokens (not measured to help); unsourced "
                    "noise is INCONCLUSIVE"),
    ("V-FO-RECALL-HELD", "after recall below before recall (integer cross-multiplication)"),
    ("V-FO-DEDUP-SWEEP", "a dedup whose sweep is not a committed recording that passed every V-FD clause, whose "
                         "group is not re-derived from it, or whose skill is not a member"),
    ("V-FO-PLANE", "a dedup of a member on a plane D-LISTING does not measure (only repo and laptop are)"),
    ("V-FO-NOISE-SOURCED", "the K4 noise figure absent from the committed lessons file"),
    ("V-FO-DRILLS", "a drill whose red set is not exactly its expected clause, or a positive control that is not "
                    "green"),
    ("V-FO-SUBPROCESS-POLES", "the --operations entrance not exiting 1 on a fabricated entry without a recall check, "
                              "or not exiting 0 on the committed file, across a real process"),
    ("V-FR-EVIDENCE-CURRENT", "this file differing from a fresh render of committed inputs, or not committed"),
)

D01_REASONS = (
    "Both halves of the frozen rule are implemented and checkable now. Dedup can only cite a group re-derived from a "
    "committed content-hash sweep that is measured on real planes and holds a real group (05-01). An applied "
    "operation can only be recorded with D-LISTING rows and recall windows, and the gate derives every figure from "
    "those committed instrument outputs.",
    "The ROADMAP goal is \"apply ... only where measured to help\". On gex44 nothing can be measured against "
    "D-LISTING, and the one listing lever with evidence was falsified twice (C6, K4). Applying zero operations is "
    "the goal's own answer on this plane. The frozen rule does not require that any operation be applied.",
    "The gate is not one that cannot fire. Every clause has a fabricated red drill, both green poles are fully formed "
    "entries, two drills use real committed data (the K4 rows, the gex44 group), and the entrance is driven red "
    "across a real process boundary.",
    "AUTHORIZATION_BOUND is rejected. It would state that the pillar waits on the Owner, but the pillar's rule is "
    "satisfied without an Owner act. The L6 `falsification` file it needs (a pre-registered IMPLEMENT ending "
    "otherwise) would assert a falsification that never happened: nothing pre-registered for F was falsified.",
)


def _row_plane(row):
    """`laptop` when the row's cwd or settings_file sits under the laptop profile (the derivation of B), else
    UNKNOWN. Never a host read."""
    if not isinstance(row, dict):
        return "UNKNOWN"
    for k in ("cwd", "settings_file"):
        v = row.get(k)
        if isinstance(v, str) and v.startswith(LAPTOP_PROFILE):
            return "laptop"
    return "UNKNOWN"


def evidence_state(found, real):
    """Everything the render reads, from committed inputs (the operations file from disk, guarded by the dirty-source
    check of V-FR-EVIDENCE-CURRENT)."""
    rule, _, denoms = frozen_f()
    try:
        ops, ops_why = parse_ops((REPO / OPS_REL).read_bytes(), rule), None
    except (OSError, Clause) as e:
        ops, ops_why = None, str(e)
    recs = [(n, r) for n, r, _ in found if r is not None and EVIDENCE_DIR + n in real["sweeps"]]
    return {"rule": rule, "sessions": denoms.get("D-SESSIONS", {}), "listing": denoms.get("D-LISTING", {}),
            "recordings": recs, "tamper": {n: tamper_drill_rows(n, r) for n, r in recs},
            "ops": ops, "ops_why": ops_why, "rows": real["rows"],
            "k4": sweep.k4_rows(real["rows"]) if real["rows"] is not None else {},
            "noise": real["noise"], "fo_drills": fo_drill_rows(real)}


def _red_text(s):
    return ", ".join(sorted(s)) if s else "(none)"


def render_evidence(state) -> str:
    """Pure. No timestamp, no absolute host path, no interpreter version, no host read."""
    L = ["# Pillar F -- representation operations (skill-capability)", "",
         "Frozen pillar F rule (ledger, quoted):", "", f"> {state['rule']}", "",
         "Rendered by `tools/test_skill_representation.py --write-evidence` from committed inputs only: the sweep "
         "recordings `" + EVIDENCE_DIR + SWEEP_GLOB + "`, `" + OPS_REL + "`, the D-LISTING probe rows of `"
         + lfv.JSONL_REL + "` (the two K4 rows pinned by session id), the noise line of `" + lfv.LESSONS_REL
         + "` and the drill outcomes. No host is read and no timestamp is written, so a re-run on another host "
         "renders the same bytes.", "", "## Planes", ""]
    for n, r in state["recordings"]:
        L.append(f"- host: {r['host']} -- sweep recording `{n}`, node `{r['node']}`, repo_commit `{r['repo_commit']}`,"
                 f" live root `{r['live_root']}`")
    for arm in ("champion", "challenger"):
        row = state["k4"].get(arm)
        if row is None:
            L.append(f"- host: UNKNOWN -- D-LISTING K4 {arm} row: UNMEASURED (not found by session id)")
            continue
        L.append(f"- host: {_row_plane(row)} -- D-LISTING probe row `{row.get('label')}`, session "
                 f"`{row.get('session_id')}`, ts {row.get('ts')} (derived: cwd or settings_file under the laptop "
                 "profile, the derivation of B-listing-floor.md)")
    L += ["", "The two planes are kept apart: the sweep describes the gex44 install, the D-LISTING rows describe the "
          "laptop listing.", "", "## Commands", ""]
    for n, r in state["recordings"]:
        L.append(f"command: {r['command']}")
        L.append(f"command: python3 tools/skill_dedup_sweep.py --compare {EVIDENCE_DIR}{n}")
        L.append(f"note: on node `{r['node']}` this --compare exits 1 (`MOVED <plane>/<skill> ['dir_digest', 'files'] "
                 "(groups and drift_excluded unchanged)`) once a live skill's own hooks append to its directory; "
                 "groups and drift_excluded unchanged is the expected reading. On any other node it is INCONCLUSIVE "
                 "(host-bound).")
    L += ["command: python3 tools/test_skill_representation.py",
          "command: python3 tools/test_skill_representation.py --write-evidence", "",
          "## Population (per plane, per recording, never summed)", "",
          "| recording | plane | entries | skills | no_skill_md | non_dir |", "|---|---|---|---|---|---|"]
    for n, r in state["recordings"]:
        for label in sorted(r["planes"]):
            p = r["planes"][label]
            nd = ", ".join(p["non_dir"]) if p["non_dir"] else "-"
            L.append(f"| {n} | {label} | {p['entries']} | {p['skills']} | {len(p['no_skill_md'])} | "
                     f"{len(p['non_dir'])} ({nd}) |")
    L += ["", "## Dedup candidate groups", ""]
    for n, r in state["recordings"]:
        if not r["groups"]:
            L.append(f"- `{n}`: 0 groups")
        for g in r["groups"]:
            L.append(f"### `{n}` group {g['body_sha'][:12]}")
            L.append("")
            L.append(f"- body_sha `{g['body_sha'][:12]}`, body_bytes {g['body_bytes']}")
            L.append("- members: " + "; ".join(f"{m['plane']}/{m['name']} (fm_name {m['fm_name']}, files "
                                               f"{m['files']})" for m in g["members"]))
            L.append("- subset pairs: " + ("; ".join(f"{a} is a subset of {b}" for a, b in g.get("subset") or [])
                                           or "none"))
            L.append(f"- fm_name_collision: {g['fm_name_collision']}")
            if state["rows"] is None:
                L.append("- laptop listing status: UNMEASURED (probe rows unreadable)")
                continue
            eff = sweep.listing_effect(g, state["rows"])
            for name in g["names"]:
                st = eff["status"][name]
                L.append(f"- laptop listing status of `{name}` per K4 row: champion {st.get('champion')}, "
                         f"challenger {st.get('challenger')}")
            L.append(f"- entries_upper_bound {eff['entries_upper_bound']}; listing_chars_upper_bound "
                     f"{eff['listing_chars_upper_bound']}")
            L.append(f"- cap note: {eff['cap_note']}")
            L.append("- This is an upper bound, never a realized saving.")
            L.append("")
    ops = state["ops"]
    L += ["## Operations applied", ""]
    if ops is None:
        L.append(f"- operations applied: UNREADABLE ({state['ops_why']})")
    else:
        note = ops.get("note", "")
        words = note.split()
        host = next((w for a, w in zip(words, words[1:]) if a.lower() == "host"), "UNSTATED")
        L.append(f"- operations applied: {len(ops['operations'])} (`{OPS_REL}`; host: {host}, per its note)")
        L.append(f"- note, quoted: \"{note}\"")
    ses, lst, nz = state["sessions"], state["listing"], state["noise"]
    L.append("- Why none were applied (D-01): a before/after measurement against D-LISTING needs fresh laptop "
             f"sessions. D-SESSIONS: listing family {ses.get('listing_family_remaining')} of "
             f"{ses.get('listing_family_total')} left; this phase consumed {FRESH_SESSIONS_THIS_PHASE} fresh sessions. "
             "Listing hiding was falsified twice against D-LISTING (C6, K4: pillar B).")
    L.append(f"- Frozen D-LISTING at K4: startup_tokens {lst.get('startup_tokens_before_K4')} -> "
             f"{lst.get('startup_tokens_after_K4')}, listing chars cap {lst.get('listing_chars_cap')}, after "
             f"{lst.get('listing_chars_after_K4')}; noise "
             + (f"{nz['tokens']} tokens ({nz['source']} line {nz['line']})." if nz else "UNMEASURED (not sourced)."))
    L.append("- Laptop applications go to the owner bundle as `[F]` lines with upper bounds, never as savings.")
    L += ["", "## Entry schema", ""] + [f"- {x}" for x in ENTRY_SCHEMA_LINES]
    L += ["", "## What each clause refuses", ""] + [f"- {c}: refuses {t}." for c, t in FO_CLAUSE_DOC]
    L += ["", "## Operation drills (fabricated unless named REAL)", "", "| drill | expected | observed |",
          "|---|---|---|"]
    for name, expect, got, text in state["fo_drills"]:
        if got is None:
            obs = f"NOT BUILT: {text}"
        elif got == expect:
            obs = "passes all clauses" if not expect else f"killed by {_red_text(got)}"
        else:
            obs = f"WRONG: red clauses {_red_text(got)}"
        L.append(f"| {name} | {_red_text(expect)} | {obs} |")
    for n, rows in state["tamper"].items():
        L += ["", f"## V-FD tamper drills (`{n}`)", "", "| drill | tampered | expected | observed |",
              "|---|---|---|---|"]
        for did, what, expect, got in rows:
            obs = ("NOT BUILT" if got is None else
                   f"killed by {_red_text(got)}" if got == expect else f"WRONG: red clauses {_red_text(got)}")
            L.append(f"| {did} | {what} | {_red_text(expect)} | {obs} |")
    L += ["", "## Decision D-01: IMPLEMENTED_AND_VERIFIED (not AUTHORIZATION_BOUND)", ""]
    L += [f"{i}. {t}" for i, t in enumerate(D01_REASONS, 1)]
    return "\n".join(L) + "\n"


def dirty_sources():
    """(paths, None) or (None, reason): render sources that differ from HEAD (untracked included)."""
    out, why = smd.git_run(REPO, "status", "--porcelain", "-z", "--", *RENDER_SOURCES)
    if out is None:
        return None, why
    return sorted({e[3:].decode("utf-8", "surrogateescape") for e in out.split(b"\0") if len(e) > 3}), None


def c_fr_evidence_current(rendered):
    try:
        disk = (REPO / FR_EVIDENCE_REL).read_bytes()
    except OSError:
        fail(f"{FR_EVIDENCE_REL} is absent: run --write-evidence and commit it")
    dirty, why = dirty_sources()
    if dirty is None:
        inconclusive(f"cannot check the render's sources against HEAD: {why}")
    if dirty:
        inconclusive(f"render sources differ from HEAD: {dirty[:5]}")
    if smd.lf_bytes(disk) != rendered.encode("utf-8"):
        fail(f"{FR_EVIDENCE_REL} differs from a fresh render: re-render with --write-evidence")
    raw, why = smd.committed_bytes(REPO, FR_EVIDENCE_REL)
    if raw is None:
        inconclusive(why)
    return f"{FR_EVIDENCE_REL} (committed) equals the render of committed inputs (line endings normalized)"


def admitted_sweeps(found):
    """{rel: recording} for every discovered recording that passed every V-FD recording clause."""
    out = {}
    for name, rec, _ in found:
        if rec is not None and all(st == "ok" for st, _ in judge_recording(name, rec).values()):
            out[EVIDENCE_DIR + name] = rec
    return out


def operations_run(path=None, found=None):
    """{V-FO-FILE, V-FO-ENTRIES} on the committed file (default) or on `path` (the red entrance)."""
    rule = frozen_f()[0]
    results = {}
    st, val = run_clause(c_fo_file, path, rule)
    if st != "ok":
        results["V-FO-FILE"] = (st, val)
        results["V-FO-ENTRIES"] = ("INCONCLUSIVE", "operations file not admitted by V-FO-FILE")
        return results, None
    text, doc = val
    results["V-FO-FILE"] = ("ok", text)
    ops = doc["operations"]
    needs_sweeps = any(isinstance(e, dict) and e.get("op") == "dedup" for e in ops)
    sweeps = admitted_sweeps(found if found is not None else discover()) if needs_sweeps else {}
    inputs = operations_inputs(ops, sweeps)
    results["V-FO-ENTRIES"] = run_clause(c_fo_entries, doc, inputs)
    return results, doc


# --------------------------------------------------------------------------- runner

def judge_recording(name, rec, clauses=RECORDING_CLAUSES, suffix_rule=True):
    """{clause id: (status, text)} for one recording. V-FD-RECORDINGS gates the rest: a recording it does not admit
    makes every other clause INCONCLUSIVE (never ok). The verdict of a recording is the conjunction of all."""
    out = {"V-FD-RECORDINGS": run_clause(c_recordings, name, rec, suffix_rule)}
    for cid, fn in clauses:
        if out["V-FD-RECORDINGS"][0] != "ok":
            out[cid] = ("INCONCLUSIVE", f"{name}: recording not admitted by V-FD-RECORDINGS")
        else:
            out[cid] = run_clause(fn, name, rec)
    return out


RANK = {"ok": 0, "INCONCLUSIVE": 1, "FAIL": 2}


def merge(results, per_rec):
    """Fold one recording's results into the clause table: a clause is ok only when ok on every recording."""
    for cid, (st, text) in per_rec.items():
        if cid not in results:
            results[cid] = (st, text)
            continue
        old_st, old_text = results[cid]
        results[cid] = (st if RANK[st] > RANK[old_st] else old_st, f"{old_text} | {text}")


def emit(results) -> int:
    passed = 0
    for cid, (st, text) in results.items():
        tag = {"ok": "ok  ", "FAIL": "FAIL", "INCONCLUSIVE": "INCONCLUSIVE"}[st]
        head, *rest = str(text).split("\n")
        print(f"  {tag} {cid} {head}")
        for ln in rest:
            print(f"      {ln}")
        passed += st == "ok"
    print(f"SR_PASS={passed}/{len(results)}")
    return 0 if results and passed == len(results) else 1


def recordings_results(found):
    """(clause table of the V-FD recording clauses over `found`, the admitted gex44 recording or None)."""
    results = {}
    if not found:
        results["V-FD-RECORDINGS"] = ("FAIL", f"no {EVIDENCE_DIR}{SWEEP_GLOB} discovered")
    gex44 = None
    for name, rec, why in found:
        if rec is None:
            unjudged = "uncommitted" in str(why) or name == GIT_ROW
            merge(results, {cid: ("INCONCLUSIVE" if cid != "V-FD-RECORDINGS" else
                                  ("INCONCLUSIVE" if unjudged else "FAIL"),
                                  f"{name}: {why}") for cid in CLAUSE_IDS})
            continue
        merge(results, judge_recording(name, rec))
        if name == GEX44_NAME:
            gex44 = rec
    if gex44 is None and not ({GEX44_NAME, GIT_ROW} & {n for n, _, _ in found}):
        merge(results, {"V-FD-REAL-GROUP": ("FAIL", f"{GEX44_NAME} not discovered (or unreadable): the positive "
                                                    "control on real data is missing")})
    return results, gex44


def default_run():
    """The full clause table over every discovered recording, plus poles and drills."""
    found = discover()
    results, gex44 = recordings_results(found)
    results["V-FD-HASH-POLES"] = run_clause(c_hash_poles)
    if gex44 is None:
        results["V-FD-TAMPER-DRILLS"] = ("INCONCLUSIVE", f"{GEX44_NAME} not admitted: no recording to tamper")
    else:
        results["V-FD-TAMPER-DRILLS"] = run_clause(c_tamper_drills, GEX44_NAME, gex44)
    ops_results, _ = operations_run(found=found)
    results.update(ops_results)
    real = real_inputs(found)
    results["V-FO-NOISE-SOURCED"] = run_clause(c_fo_noise_sourced)
    results["V-FO-DRILLS"] = run_clause(c_fo_drills, real)
    results["V-FO-SUBPROCESS-POLES"] = run_clause(c_fo_subprocess_poles, real)
    try:
        rendered = render_evidence(evidence_state(found, real))
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as e:
        results["V-FR-EVIDENCE-CURRENT"] = ("INCONCLUSIVE", f"cannot render: {type(e).__name__}: {e}")
    else:
        results["V-FR-EVIDENCE-CURRENT"] = run_clause(c_fr_evidence_current, rendered)
    return results, found


def real_inputs(found):
    rows, _ = probe_rows()
    return {"rows": rows, "noise": sourced_noise()[0], "sweeps": admitted_sweeps(found), "denoms": frozen_f()[1]}


def json_report(found):
    rows, why = None, None
    raw, why = smd.committed_bytes(REPO, sweep.lfv.JSONL_REL)
    if raw is not None:
        rows = [json.loads(ln) for ln in smd.lf_bytes(raw).decode("utf-8").splitlines() if ln.strip()]
    out = []
    for name, rec, rwhy in found:
        if rec is None:
            out.append({"recording": name, "status": "INCONCLUSIVE", "reason": rwhy})
            continue
        out.append({"recording": name, "host": rec.get("host"), "repo_commit": rec.get("repo_commit"),
                    "planes": {k: {c: v.get(c) for c in ("entries", "skills", "no_skill_md", "non_dir")}
                               for k, v in rec.get("planes", {}).items()},
                    "drift_excluded": rec.get("drift_excluded"),
                    "groups": [{"names": g.get("names"), "body_sha": g.get("body_sha"),
                                "fm_name_collision": g.get("fm_name_collision"), "subset": g.get("subset"),
                                "listing_effect": (sweep.listing_effect(g, rows) if rows is not None else
                                                   f"UNMEASURED ({why})")}
                               for g in rec.get("groups", [])]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--recording", metavar="PATH", help="recording-scoped V-FD clauses on one file; exit 1 if any "
                    "is not ok (no drills, no discovery)")
    ap.add_argument("--json", action="store_true", help="recordings summary + groups + listing effect")
    ap.add_argument("--operations", metavar="PATH", help="V-FO-FILE + V-FO-ENTRIES on that operations file only "
                    "(read from disk; no drills, no subprocess); exit 1 if either is not ok")
    ap.add_argument("--write-evidence", action="store_true", help=f"render {FR_EVIDENCE_REL} from committed inputs "
                    "and write it (utf-8, LF)")
    a = ap.parse_args(argv)
    if a.write_evidence:
        found = discover()
        text = render_evidence(evidence_state(found, real_inputs(found)))
        with open(REPO / FR_EVIDENCE_REL, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {FR_EVIDENCE_REL} ({len(text.encode('utf-8'))} bytes)")
        return 0
    if a.operations:
        return emit(operations_run(a.operations)[0])
    if a.recording:
        p = Path(a.recording)
        rec, why = sweep.load_recording(p)
        if rec is None:
            return emit({"V-FD-RECORDINGS": ("FAIL", why)})
        inside = p.resolve().parent == (REPO / EVIDENCE_DIR).resolve()
        return emit(judge_recording(p.name, rec, suffix_rule=inside))
    if a.json:
        _, found = None, discover()
        sys.stdout.write(json.dumps(json_report(found), indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        return 0
    results, _ = default_run()
    return emit(results)


if __name__ == "__main__":
    sys.exit(main())
