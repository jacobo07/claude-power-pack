#!/usr/bin/env python
"""test_skill_representation.py -- pillar F gate (skill-capability, SC-F, decision D-01), sweep half.

    python3 tools/test_skill_representation.py                    # check (default mode)
    python3 tools/test_skill_representation.py --recording PATH   # recording-scoped clauses on one file (red entrance)
    python3 tools/test_skill_representation.py --json             # recordings summary + groups + listing effect

What it judges: the dedup content-hash sweep of `tools/skill_dedup_sweep.py` (D-01 item 1). The default mode reads
only committed repo files and git blobs: every recording discovered by `evidence/F-sweep-*.json`, the committed
blobs at each recording's repo_commit, and nothing under any home directory, so the CE verifier can re-run it on
another host at `--final`.

Output lines: `  ok   <ID> <evidence>` / `  FAIL <ID> <diagnostic>` / `  INCONCLUSIVE <ID> <reason>`, last line
`SR_PASS=<passed>/<total>`. Exit codes: 0 every clause ok, 1 any FAIL or INCONCLUSIVE, 2 could not run.
INCONCLUSIVE is never a pass.
"""
from __future__ import annotations

import argparse
import copy
import fnmatch
import functools
import hashlib
import json
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

def discover(repo=REPO):
    """[(filename, recording or None, reason or None)] for every F-sweep-*.json tracked at HEAD or present in the
    working tree, sorted. Each is read as its COMMITTED blob at HEAD (`smd.committed_bytes`): a recording that exists
    only in the working tree, or differs from HEAD, is refused as uncommitted (INCONCLUSIVE), never judged."""
    names = {p.name for p in (Path(repo) / EVIDENCE_DIR).glob(SWEEP_GLOB)}
    tracked, _ = smd.tracked_paths(repo, "HEAD")
    names |= {t[len(EVIDENCE_DIR):] for t in (tracked or ()) if t.startswith(EVIDENCE_DIR)
              and fnmatch.fnmatch(t[len(EVIDENCE_DIR):], SWEEP_GLOB)}
    tracked = tracked or set()
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
        if len(names) == 1 and names <= drift:
            fail(f"{name}: drift_excluded {sorted(names)} is the only name of a group")
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


POLES = (("SAME-BODY", pole_same_body), ("CRLF", pole_crlf), ("ONE-BYTE", pole_one_byte),
         ("NO-FRONTMATTER", pole_no_frontmatter), ("SAME-NAME-CROSS-PLANE", pole_same_name_cross_plane),
         ("CROSS-PLANE-RENAMED", pole_cross_plane_renamed), ("DISCOVERY", pole_discovery))


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
    head = f"{len(POLES)} poles + 1 mutant"
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
          ("MEMBER-SHA", d_member_sha, {"V-FD-MEMBER-FILES"}))


def c_tamper_drills(name, rec):
    lines, all_ok = [], True
    clean = judge_recording(name, copy.deepcopy(rec))
    bad = sorted(c for c, (st, _) in clean.items() if st != "ok")
    if bad:
        inconclusive(f"{name}: clean control does not pass ({bad}); drills cannot be judged")
    lines.append(f"ok   V-FD-DRILL-CLEAN untampered copy passes all {len(clean)} V-FD recording clauses")
    for did, fn, expect in DRILLS:
        t = copy.deepcopy(rec)
        try:
            what = fn(t)
        except (KeyError, TypeError, IndexError) as e:
            all_ok = False
            lines.append(f"FAIL V-FD-DRILL-{did} could not be built: {type(e).__name__}: {e}")
            continue
        got = {c for c, (st, _) in judge_recording(name, t).items() if st != "ok"}
        ok = got == expect
        all_ok &= ok
        lines.append(f"{'ok  ' if ok else 'FAIL'} V-FD-DRILL-{did} ({what}) "
                     + (f"killed by {', '.join(sorted(got))}" if ok else
                        f"expected {sorted(expect)}, red clauses {sorted(got)}"))
    head = f"{name} {len(DRILLS)} drills + clean control"
    if not all_ok:
        fail(head + "\n" + "\n".join(lines))
    return head + "\n" + "\n".join(lines)


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


def default_run():
    """The full clause table over every discovered recording, plus poles and drills."""
    results = {}
    found = discover()
    if not found:
        results["V-FD-RECORDINGS"] = ("FAIL", f"no {EVIDENCE_DIR}{SWEEP_GLOB} discovered")
    gex44 = None
    for name, rec, why in found:
        if rec is None:
            merge(results, {cid: ("INCONCLUSIVE" if cid != "V-FD-RECORDINGS" else
                                  ("INCONCLUSIVE" if "uncommitted" in str(why) else "FAIL"),
                                  f"{name}: {why}") for cid in CLAUSE_IDS})
            continue
        merge(results, judge_recording(name, rec))
        if name == GEX44_NAME:
            gex44 = rec
    if gex44 is None and GEX44_NAME not in {n for n, _, _ in found}:
        merge(results, {"V-FD-REAL-GROUP": ("FAIL", f"{GEX44_NAME} not discovered (or unreadable): the positive "
                                                    "control on real data is missing")})
    results["V-FD-HASH-POLES"] = run_clause(c_hash_poles)
    if gex44 is None:
        results["V-FD-TAMPER-DRILLS"] = ("INCONCLUSIVE", f"{GEX44_NAME} not admitted: no recording to tamper")
    else:
        results["V-FD-TAMPER-DRILLS"] = run_clause(c_tamper_drills, GEX44_NAME, gex44)
    return results, found


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
    a = ap.parse_args(argv)
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
