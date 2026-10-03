#!/usr/bin/env python
"""skill_dedup_sweep.py -- the D-01 item 1 dedup content-hash sweep (skill-capability, pillar F).

    python3 tools/skill_dedup_sweep.py --measure-live --host gex44 --out PATH   # record repo + live planes
    python3 tools/skill_dedup_sweep.py --compare PATH                         # re-measure; exit 1 on any move
    python3 tools/skill_dedup_sweep.py --json PATH                            # groups + listing effect

What it decides: dedup CANDIDATES only. It applies nothing, deletes nothing and never writes under the live tree.

The two planes, both DISCOVERED, never listed:
  repo  every `skills/<name>/SKILL.md` tracked at a named commit, read from committed blobs (never the working tree,
        so a concurrent writer's uncommitted edit cannot stand in for the repo population);
  live  every top-level entry of a host's skills root (default `~/.claude/skills`). A directory (a symlinked one that
        resolves included, listed in `symlinked`) with a top-level SKILL.md file is a skill; a directory without one is
        named in `no_skill_md`; anything else (a file, a dangling symlink) is named in `non_dir`. Nothing is dropped
        from the denominator: entries == skills + len(no_skill_md) + len(non_dir), on both planes.

Why same-name copies are excluded: `foo` in the repo and `foo` on a live plane with one body is the mirror of one
skill, i.e. drift or its absence, which pillar H (`tools/skill_mirror_drift.py`) owns. Such names are counted in
`drift_excluded` and never form a dedup group on their own.

Reuse (D-02): `modules/skill_router/skill_index._FM_RE` is the owner's frontmatter grammar, so it is the one place
the body is split from the frontmatter; its walk `build_index` is not reused because it reads only 4000 head bytes,
reads only the live root and writes a cache under the home directory. Phase 4's `tools/skill_mirror_drift.py` owns
the committed-blob reader and the directory digest, so `repo_skills`, `repo_side`, `live_side`, `dir_digest` and
`lf_bytes` are imported, never re-implemented: there is one comparator. `tools/skill_invocations.installed_names()`
is not this population (it unions command files with directories and counts SKILL.md-less directories as skills).

Hash scheme:
  body_sha    sha256 of the LF-normalized SKILL.md with the frontmatter stripped by `_FM_RE` (whole text when there
              is no frontmatter): what the listing loads, independent of how a copy names itself;
  dir_digest  `smd.dir_digest` over `<relpath>\\0<lf_sha256>` of every file: what a deletion would remove;
  group       one body_sha shared by >= 2 DISTINCT names (any planes). Rank: distinct names descending, then
              body_bytes descending, then body_sha (Claude's discretion, D-01).

The recording holds names, hashes and counts only: no file content and no description text.

Exit codes: 0 ok, 1 differs / refused / INCONCLUSIVE, 2 could not run (bad arguments).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO = _THIS_DIR.parent
for _p in (str(_THIS_DIR), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import skill_mirror_drift as smd  # noqa: E402
import test_listing_floor_verdict as lfv  # noqa: E402
import verify_global_mirrors as vgm  # noqa: E402
from modules.skill_router import skill_index  # noqa: E402

REPO = _REPO
SCHEMA = "skill-dedup-sweep/1"
DEFAULT_LIVE_ROOT = "~/.claude/skills"
HOST_RE = re.compile(r"[a-z0-9-]+")
# The two K4 D-LISTING probe rows (wiki/tools/listing_floor_probe.results.jsonl), pinned by session id so that a row
# appended later can never be read in their place.
K4_SESSIONS = {"champion": "8f983bc6-d760-4440-938d-aeed86a548ae",
               "challenger": "b568fafb-782d-48ab-9014-d9ae2b13c882"}
UNWATCHED = "UNMEASURED (not in watch set)"
LISTING_LABEL = "laptop listing, D-LISTING probe rows: describes the laptop install, not this member's plane"
CAP_NOTE = ("upper bound only: the 30,000-char listing cap binds and refills (C6, K4: B FALSIFIED), so a realized "
            "listing saving may be 0")
DESCRIBED_RE = re.compile(r"described \((\d+)\)")
METHOD = {
    "body": "sha256 of the LF-normalized SKILL.md after skill_index._FM_RE strips the frontmatter",
    "dir": "skill_mirror_drift.dir_digest over sorted <relpath>\\0<lf_sha256> lines of every file in the directory",
    "group": "one body_sha shared by >= 2 distinct skill names; same-name cross-plane copies are drift_excluded",
}
RECORD_KEYS = ("body_bytes", "body_sha", "dir_digest", "files", "fm_name", "has_frontmatter", "skill_md_sha")


# --------------------------------------------------------------------------- pure hashing

def split_frontmatter(text: str):
    """(fm_text or None, body). The owner's grammar, `skill_index._FM_RE`, is the only splitter."""
    m = skill_index._FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def fm_name(fm_text):
    """The `name:` line of the frontmatter, stripped, or None. Same regex as `skill_index._read_frontmatter`, which is
    not called because it takes a path and reads only `_FM_HEAD_BYTES` (4000) head bytes."""
    if fm_text is None:
        return None
    m = re.search(r"^name:\s*(.+)$", fm_text, re.M)
    return m.group(1).strip() if m else None


def body_hash(skill_md_bytes: bytes):
    """(fm_text, body_sha, body_bytes) of one SKILL.md."""
    text = smd.lf_bytes(skill_md_bytes).decode("utf-8", "surrogateescape")
    fm, body = split_frontmatter(text)
    raw = body.encode("utf-8", "surrogateescape")
    return fm, hashlib.sha256(raw).hexdigest(), len(raw)


def skill_record(skill_md_bytes: bytes, side: dict) -> dict:
    """One skill's record. `side` is the dict `smd.repo_side` / `smd.live_side` returns for that skill."""
    fm, sha, n = body_hash(skill_md_bytes)
    return {"fm_name": fm_name(fm), "has_frontmatter": fm is not None, "body_sha": sha, "body_bytes": n,
            "skill_md_sha": side["files"]["SKILL.md"], "dir_digest": side["digest"], "files": len(side["files"])}


# --------------------------------------------------------------------------- planes

def _plane(label, root, skills, no_skill_md, non_dir, records, files, symlinked=()):
    return {"status": "MEASURED", "plane": label, "root": root,
            "entries": len(skills) + len(no_skill_md) + len(non_dir), "skills": len(skills),
            "names": sorted(skills), "no_skill_md": sorted(no_skill_md), "non_dir": sorted(non_dir),
            "symlinked": sorted(symlinked), "records": {n: records[n] for n in sorted(records)},
            "_files": files}


def public(plane: dict) -> dict:
    """The recordable part of a plane (drops the transient per-file lists)."""
    return {k: v for k, v in plane.items() if not k.startswith("_")}


def repo_plane(repo, ref="HEAD") -> dict:
    """The repo plane from committed blobs at `ref`, or {status: INCONCLUSIVE, reason}. Never raises and never returns
    an empty population."""
    sha, why = smd.resolve_commit(repo, ref)
    if sha is None:
        return {"status": "INCONCLUSIVE", "reason": f"cannot resolve {ref}: {why}"}
    tracked, why = smd.tracked_paths(repo, sha)
    if not tracked:
        return {"status": "INCONCLUSIVE", "reason": why or f"nothing tracked at {sha[:8]}"}
    skills, why = smd.repo_skills(repo, sha)
    if skills is None:
        return {"status": "INCONCLUSIVE", "reason": why}
    if not skills:
        return {"status": "INCONCLUSIVE", "reason": f"no tracked skills/<name>/SKILL.md at {sha[:8]} (UNMEASURED)"}
    under = [p[len("skills/"):] for p in tracked if p.startswith("skills/")]
    dirs = {p.split("/")[0] for p in under if "/" in p}
    non_dir = sorted(p for p in under if "/" not in p)
    no_skill_md = sorted(dirs - set(skills))
    blobs = vgm.batch_blobs(str(repo), sha, [f"skills/{n}/SKILL.md" for n in skills])
    sides = smd.repo_side(repo, sha, skills)
    records, files = {}, {}
    for n in sorted(skills):
        data, w = blobs.get(f"skills/{n}/SKILL.md", (None, "not returned"))
        if data is None and w == "git-batch-empty":
            data, w = b"", None
        if data is None:
            return {"status": "INCONCLUSIVE", "reason": f"skills/{n}/SKILL.md at {sha[:8]}: {w}"}
        side = sides.get(n) or {"error": "no side"}
        if "error" in side:
            return {"status": "INCONCLUSIVE", "reason": f"skills/{n}: {side['error']}"}
        records[n] = skill_record(data, side)
        files[n] = side["files"]
    out = _plane("repo", f"skills/ @ {sha}", skills, no_skill_md, non_dir, records, files)
    out["commit"] = sha
    return out


def live_plane(live_root, label="live") -> dict:
    """The live plane of one host's skills root, or {status: INCONCLUSIVE, reason}. Read only: files are opened in
    binary read mode; nothing is written, chmod-ed or touched under the root."""
    root = Path(os.path.expanduser(str(live_root)))
    if not root.is_dir():
        return {"status": "INCONCLUSIVE", "reason": f"live root {live_root} absent: nothing measured"}
    try:
        entries = sorted(os.listdir(root))
    except OSError as e:
        return {"status": "INCONCLUSIVE", "reason": f"live root {live_root} unreadable: {e}"}
    skills, no_skill_md, non_dir, symlinked, records, files = [], [], [], [], {}, {}
    for name in entries:
        try:
            name.encode("utf-8")
        except UnicodeEncodeError:
            return {"status": "INCONCLUSIVE", "reason": f"entry name {name!r} is not UTF-8: cannot be recorded"}
        p = root / name
        if not p.is_dir():  # a file, or a symlink whose target does not resolve to a directory
            non_dir.append(name)
            continue
        md = p / "SKILL.md"
        if not md.is_file():
            no_skill_md.append(name)
            continue
        try:
            with open(md, "rb") as fh:
                data = fh.read()
            side = smd.live_side(p)
        except OSError as e:
            return {"status": "INCONCLUSIVE", "reason": f"{name}: live read failed: {e}"}
        if side is None or "SKILL.md" not in side["files"]:
            return {"status": "INCONCLUSIVE", "reason": f"{name}: live_side did not see SKILL.md"}
        if p.is_symlink():
            symlinked.append(name)
        skills.append(name)
        records[name] = skill_record(data, side)
        files[name] = side["files"]
    if not skills:
        return {"status": "INCONCLUSIVE", "reason": f"live root {live_root} holds no skill (UNMEASURED)"}
    return _plane(label, str(live_root), skills, no_skill_md, non_dir, records, files, symlinked)


# --------------------------------------------------------------------------- groups (pure)

def _member(plane, name, rec):
    return {"plane": plane, "name": name, "fm_name": rec["fm_name"], "skill_md_sha": rec["skill_md_sha"],
            "dir_digest": rec["dir_digest"], "files": rec["files"]}


def subset_pairs(group: dict, member_files: dict) -> list:
    """[[a, b], ...] (member ids `<plane>/<name>`) where every (relpath, lf_sha) of a's files is in b's files. A member
    with no per-file list takes part in no pair (it cannot be judged)."""
    ids = [f"{m['plane']}/{m['name']}" for m in group["members"]]
    sets = {i: {tuple(x) for x in member_files[i]} for i in ids if isinstance(member_files.get(i), list)}
    return [[a, b] for a in ids for b in ids if a != b and a in sets and b in sets and sets[a] <= sets[b]]


def groups(planes: dict, member_files: dict | None = None):
    """(groups, drift_excluded) over `planes` = {label: plane with records}. Pure. Groups carry `subset` only when
    `member_files` is given (it is derived from the per-file lists, which V-FD-MEMBER-FILES owns)."""
    by_sha = {}
    for label in sorted(planes):
        for name, rec in sorted(planes[label]["records"].items()):
            by_sha.setdefault(rec["body_sha"], []).append((label, name, rec))
    out, drift = [], set()
    for sha, mem in by_sha.items():
        planes_of = {}
        for label, name, _ in mem:
            planes_of.setdefault(name, set()).add(label)
        drift |= {n for n, ps in planes_of.items() if len(ps) >= 2}
        if len(planes_of) < 2:
            continue
        mem = sorted(mem, key=lambda t: (t[0], t[1]))
        fm = {}
        for _, name, rec in mem:
            fm.setdefault(rec["fm_name"], set()).add(name)
        g = {"body_sha": sha, "body_bytes": mem[0][2]["body_bytes"],
             "members": [_member(lb, n, r) for lb, n, r in mem], "names": sorted(planes_of),
             "distinct_names": len(planes_of),
             "fm_name_collision": any(k is not None and len(v) >= 2 for k, v in fm.items()),
             "skill_md_identical": len({r["skill_md_sha"] for _, _, r in mem}) == 1}
        if member_files is not None:
            g["subset"] = subset_pairs(g, member_files)
        out.append(g)
    out.sort(key=lambda g: (-g["distinct_names"], -g["body_bytes"], g["body_sha"]))
    return out, sorted(drift)


def member_files(planes: dict, grps: list) -> dict:
    """{"<plane>/<name>": sorted [[relpath, lf_sha], ...]} for group members only (non-members carry no list)."""
    out = {}
    for g in grps:
        for m in g["members"]:
            files = planes[m["plane"]]["_files"][m["name"]]
            out[f"{m['plane']}/{m['name']}"] = [[r, files[r]] for r in sorted(files)]
    return out


# --------------------------------------------------------------------------- listing effect (pure)

def k4_rows(rows) -> dict:
    """{arm: row or None} for the two K4 rows pinned by session id (exactly one row each, else None)."""
    out = {}
    for arm, sid in K4_SESSIONS.items():
        hits = [r for r in rows if isinstance(r, dict) and r.get("session_id") == sid]
        out[arm] = hits[0] if len(hits) == 1 else None
    return out


def listing_effect(group: dict, probe_rows) -> dict:
    """Per member name, the status it has in the `watch` map of the two K4 rows, else UNWATCHED; plus the upper
    bounds. Integer arithmetic only."""
    arms = k4_rows(probe_rows)
    status = {}
    for name in group["names"]:
        st = {}
        for arm, row in arms.items():
            if row is None:
                st[arm] = "UNMEASURED (K4 row not found by session id)"
                continue
            watch = row.get("watch") if isinstance(row.get("watch"), dict) else {}
            st[arm] = watch.get(name, UNWATCHED)
        status[name] = st
    k = group["distinct_names"] - 1
    described = []
    for name in group["names"]:
        m = DESCRIBED_RE.fullmatch(str(status[name].get("challenger", "")))
        described.append(int(m.group(1)) if m else None)
    chars = sum(sorted(described, reverse=True)[:k]) if described and None not in described else "UNMEASURED"
    return {"label": LISTING_LABEL, "status": status, "entries_upper_bound": k,
            "listing_chars_upper_bound": chars, "cap_note": CAP_NOTE}


def load_probe_rows(repo=REPO):
    """(rows, None) or (None, reason) from the committed-to-repo probe results file."""
    try:
        return lfv.load_rows(Path(repo) / lfv.JSONL_REL), None
    except (OSError, ValueError) as e:
        return None, f"{lfv.JSONL_REL} unreadable: {e}"


# --------------------------------------------------------------------------- recording

def build_recording(repo, ref, live_root, host, command=""):
    """(recording, None) or (None, reason). Refuses on any INCONCLUSIVE plane."""
    rp = repo_plane(repo, ref)
    if rp["status"] != "MEASURED":
        return None, f"repo plane: {rp['reason']}"
    lp = live_plane(live_root, host)
    if lp["status"] != "MEASURED":
        return None, f"{host} plane: {lp['reason']}"
    planes = {"repo": rp, host: lp}
    grps, drift = groups(planes)
    mf = member_files(planes, grps)
    for g in grps:
        g["subset"] = subset_pairs(g, mf)
    return {"schema": SCHEMA, "host": host, "node": platform.node(), "repo_commit": rp["commit"],
            "live_root": str(live_root), "command": command, "method": METHOD,
            "planes": {k: public(v) for k, v in planes.items()},
            "groups": grps, "drift_excluded": drift, "member_files": mf}, None


def dumps(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def load_recording(path):
    """(recording, None) or (None, reason); CRLF -> LF first."""
    try:
        return json.loads(smd.lf_bytes(Path(path).read_bytes()).decode("utf-8")), None
    except (OSError, ValueError) as e:
        return None, f"cannot read recording {path}: {e}"


def _first_difference(old: dict, new: dict):
    """Name of the first skill (or key) that differs between two recordings, or None."""
    for label in sorted(set(old.get("planes", {})) | set(new.get("planes", {}))):
        po, pn = old.get("planes", {}).get(label), new.get("planes", {}).get(label)
        if po is None or pn is None:
            return f"plane {label} present on one side only"
        for k in ("entries", "skills", "names", "no_skill_md", "non_dir", "symlinked"):
            if po.get(k) != pn.get(k):
                return f"{label}.{k}"
        ro, rn = po.get("records", {}), pn.get("records", {})
        for n in sorted(set(ro) | set(rn)):
            if ro.get(n) != rn.get(n):
                keys = sorted(k for k in RECORD_KEYS if (ro.get(n) or {}).get(k) != (rn.get(n) or {}).get(k))
                return f"{label}/{n} {keys}"
    for k in ("groups", "drift_excluded", "member_files"):
        if old.get(k) != new.get(k):
            return k
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--measure-live", action="store_true", help="record the repo + live planes (needs --host --out)")
    ap.add_argument("--host", help="plane label, ^[a-z0-9-]+$ (a laptop run must say laptop)")
    ap.add_argument("--out", help="recording path for --measure-live")
    ap.add_argument("--live-root", default=DEFAULT_LIVE_ROOT)
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--compare", metavar="PATH", help="re-measure at the recording's commit/root/host; exit 1 on a move")
    ap.add_argument("--json", metavar="PATH", help="print the recording's groups with their listing effect")
    ap.add_argument("--repo", default=str(REPO))
    a = ap.parse_args(argv)
    repo = Path(a.repo)

    if a.measure_live:
        if not a.host or not HOST_RE.fullmatch(a.host) or not a.out:
            print("--measure-live needs --host matching ^[a-z0-9-]+$ and --out PATH", file=sys.stderr)
            return 2
        cmd = f"python3 tools/skill_dedup_sweep.py --measure-live --host {a.host} --out {a.out}"
        if a.live_root != DEFAULT_LIVE_ROOT:
            cmd += f" --live-root {a.live_root}"
        if a.ref != "HEAD":
            cmd += f" --ref {a.ref}"
        rec, why = build_recording(repo, a.ref, a.live_root, a.host, cmd)
        if rec is None:
            print(f"INCONCLUSIVE {why}")
            return 1
        dest = Path(a.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(dumps(rec))
        p = rec["planes"]
        print(f"recorded {dest} repo_commit={rec['repo_commit'][:8]} repo={p['repo']['skills']} "
              f"{a.host}={p[a.host]['skills']}/{p[a.host]['entries']} groups={len(rec['groups'])} "
              f"drift_excluded={len(rec['drift_excluded'])}")
        return 0

    if a.compare:
        old, why = load_recording(a.compare)
        if old is None:
            print(f"INCONCLUSIVE {why}")
            return 1
        try:
            host, ref, root = old["host"], old["repo_commit"], old["live_root"]
        except (KeyError, TypeError) as e:
            print(f"INCONCLUSIVE malformed recording: {type(e).__name__}: {e}")
            return 1
        if old.get("node") != platform.node():
            print(f"INCONCLUSIVE host-bound: recorded on node {old.get('node')!r}, this is {platform.node()!r}")
            return 1
        new, why = build_recording(repo, ref, root, host, old.get("command", ""))
        if new is None:
            print(f"INCONCLUSIVE {why}")
            return 1
        diff = _first_difference(old, new)
        if diff:
            # A live skill directory can hold runtime state its own hooks append to (measured on gex44:
            # claude-power-pack/vault/ceps/fires.jsonl), so its dir_digest moves between readings while its body does
            # not. That is still a move: the recording is a snapshot, and --compare never hides one.
            same = (old.get("groups") == new.get("groups") and old.get("drift_excluded") == new.get("drift_excluded"))
            print(f"MOVED {diff}" + (" (groups and drift_excluded unchanged)" if same else ""))
            return 1
        print(f"reproduced {a.compare} at {ref[:8]}: planes, groups and member_files equal")
        return 0

    if a.json:
        rec, why = load_recording(a.json)
        if rec is None:
            print(f"INCONCLUSIVE {why}")
            return 1
        rows, why = load_probe_rows(repo)
        if rows is None:
            print(f"INCONCLUSIVE {why}")
            return 1
        out = [{"names": g["names"], "body_sha": g["body_sha"], "members": g["members"],
                "fm_name_collision": g["fm_name_collision"], "skill_md_identical": g["skill_md_identical"],
                "subset": g.get("subset"), "listing_effect": listing_effect(g, rows)}
               for g in rec.get("groups", [])]
        sys.stdout.write(json.dumps({"host": rec.get("host"), "repo_commit": rec.get("repo_commit"),
                                     "groups": out, "drift_excluded": rec.get("drift_excluded")},
                                    indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
