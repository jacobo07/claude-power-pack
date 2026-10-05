#!/usr/bin/env python
"""Mission capsule adapter -- capsule-v2 for cpp-gsd-long workers (spec vault/specs/mission-capsule-rollover.md).

A THIN adapter, not a second engine (spec section 2): it translates a mission record and GSD's own
answer into a capsule, then hands that capsule to tools/rollover.py, which owns the format, the seal,
completeness, SAFE_TO_FORGET, the claim, the exam, certification and the pre-certification marker.
Nothing here re-implements any of those.

What this module owns:
- compile_mission_capsule: mission record + GSD init.manager -> a rollover-capsule-v2 dict (G1/G2).
- seal_mission: rollover.seal + completeness + the same `capsule_sealed` ledger row the interactive
  seal writes, because rollover.gate trusts only that row.
- gate_before_stop: rollover.gate, plus the outgoing transcript unchanged since the seal (I2).

State directories are resolved at CALL time and passed explicitly (G24): rollover.STATE_DIR is frozen
at import, so a test that redirects the environment after importing would otherwise write live state.

Status: IMPLEMENTED. No production caller until T6 wires tools/gsd_mission.py behind
`rollover_protocol == "capsule-v2"`; a record without that field never reaches this module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Optional

import rollover as ro

PROTOCOL = "capsule-v2"
NOTE_MAX_CHARS = 2000
# Spec 11.5: the one place the successor's script path comes from -- the precert marker (read by the
# mutation guard's deny text) and the successor card both name THIS file, never the mission's command.
TOOL = Path(__file__).resolve().as_posix()
PACKET_REF_KEYS = ("verdict", "path", "sha256", "bytes", "root", "files")


def state_dir(explicit=None) -> Path:
    """The rollover state dir, resolved NOW (never rollover.STATE_DIR, which is fixed at import)."""
    if explicit:
        return Path(explicit)
    env = os.environ.get("CPP_ROLLOVER_STATE_DIR")
    return Path(env) if env else Path.home() / ".claude" / "state" / "rollover"


def capsule_key(rec: dict) -> str:
    """The OUTGOING worker's capsule: the epoch it ran (spec 3.2)."""
    return ro.mission_key(rec["mission_id"], rec["epoch"])


def worker_name(mission_id: str, epoch) -> str:
    """The name the supervisor launches a worker under. Same expression as gsd_mission.worker_name,
    which T6 makes the caller; a test pins the two together so they cannot drift."""
    return f"{mission_id}-e{int(epoch)}"


# --------------------------------------------------------------------------- GSD -> obligations
def render_obligations(manager: Optional[dict]) -> tuple[list[str], Optional[str]]:
    """G1/G2: GSD's recommended actions as plain strings, first = next. When GSD recommends nothing
    (a phase mid-execution), the first phase not complete is the obligation: `continue phase N`."""
    if not isinstance(manager, dict):
        return [], None
    items = []
    for a in manager.get("recommended_actions") or []:
        if isinstance(a, dict) and a.get("action") and a.get("phase") not in (None, ""):
            name = str(a.get("phase_name") or "").strip()
            items.append(f"{a['action']} phase {a['phase']}" + (f": {name}" if name else ""))
    if items:
        return items, "gsd recommended_actions"
    for p in manager.get("phases") or []:
        if isinstance(p, dict) and not p.get("phase_complete") and p.get("number") not in (None, ""):
            name = str(p.get("name") or "").strip()
            return [f"continue phase {p['number']}" + (f": {name}" if name else "")], "gsd first incomplete phase"
    return [], None


def goal_pointer(manager: Optional[dict], work_dir: str) -> dict:
    """The mission's goal = GSD's STATE.md, resolved against the work tree and required to exist."""
    if not isinstance(manager, dict):
        return {"state": ro.UNKNOWN, "reason": "GSD could not be asked"}
    raw = manager.get("state_path")
    if not raw:
        return {"state": ro.UNKNOWN, "reason": "GSD names no STATE.md"}
    p = Path(raw)
    if not p.is_absolute():
        p = Path(work_dir) / p
    if not p.is_file():
        return {"state": ro.UNKNOWN, "reason": f"STATE.md not on disk: {p}"}
    return {"state": "OK", "path": str(p), "source": "gsd init.manager"}


def ask_gsd(work_dir: str, workstream: Optional[str]) -> tuple[Optional[dict], str]:
    import gsd_long_run as lr
    return lr.gsd_manager(work_dir, workstream=workstream)


# --------------------------------------------------------------------------- compile
def transcript_mark(transcript) -> Optional[dict]:
    """Size + mtime of the outgoing transcript: if either moved after the seal, the worker did
    something the capsule did not see (I2)."""
    try:
        st = Path(transcript).stat()
    except (OSError, TypeError):
        return None
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _packet_ref(ref) -> Optional[dict]:
    """A reference, never the packet: the source list stays in the packet's own .json."""
    if not isinstance(ref, dict) or not ref.get("sha256"):
        return None
    return {k: ref[k] for k in PACKET_REF_KEYS if k in ref}


def compile_mission_capsule(rec: dict, *, origin: str, note: str = "", work_dir: Optional[str] = None,
                            transcript: Optional[str] = None, packet: Optional[dict] = None,
                            manager: Optional[dict] = None, ask: Optional[Callable] = None,
                            children: Optional[dict] = None, child_reader: Optional[Callable] = None,
                            find_transcript: Optional[Callable] = None, now: Optional[float] = None) -> dict:
    """The capsule for the worker that ran `rec["epoch"]`. Facts only from durable sources (the
    record, git, GSD, the transcript's own reader); the note is the predecessor's CLAIM.

    Raises ValueError for a record that has no identity to key a capsule by: that is a caller bug,
    not a refusal. Everything else that is missing is left absent, so rollover.completeness refuses
    it by name -- the adapter never fills a gap to make a capsule look sealable."""
    if origin not in ro.MISSION_SEAL_ORIGINS:
        raise ValueError(f"seal origin {origin!r} is not one of {', '.join(ro.MISSION_SEAL_ORIGINS)}")
    mid, epoch = rec.get("mission_id"), rec.get("epoch")
    if not mid or not isinstance(epoch, int) or epoch < 1:
        raise ValueError(f"mission record has no usable identity (mission_id={mid!r}, epoch={epoch!r})")
    wd = str(work_dir or rec.get("work_dir") or rec.get("cwd") or "")
    owner = rec.get("owner") or {}
    sid = owner.get("session_id")
    gsd_why = ""
    if manager is None:
        manager, gsd_why = (ask or ask_gsd)(wd, rec.get("workstream"))
    # The worker's own record of what it wrote. Found the way the interactive seal finds it when the
    # caller passed none; a path that is not a file is NO transcript (review 2026-10-03: a wrong path
    # read as "wrote nothing", i.e. custody OK).
    tp = Path(transcript) if transcript else ((find_transcript or ro._find_transcript)(sid) if sid else None)
    if tp is not None and not tp.is_file():
        tp = None
    items, source = render_obligations(manager)
    key = capsule_key(rec)
    cap = {
        "schema": ro.SCHEMA_V2, "protocol": PROTOCOL, "kind": "mission",
        "capsule_key": key, "session_id": key, "cwd": wd, "created": ro._iso(now),
        "run": {"lineage_id": rec.get("lineage_id") or mid, "mission_id": mid, "epoch": epoch,
                "successor_epoch": epoch + 1, "worker": sid, "worker_name": worker_name(mid, epoch)},
        "seal_origin": origin, "degraded": origin != "worker_handoff",
        "repo": ro.repo_facts(wd),
        "goal": goal_pointer(manager, wd) if manager is not None else
        {"state": ro.UNKNOWN, "reason": f"GSD could not be asked: {gsd_why}"},
        "obligations": items, "obligations_source": source,
        "goal_ref": rec.get("goal_ref"),
        "resume_cmd": rec.get("resume_command"),
        "note": (note or "").strip()[:NOTE_MAX_CHARS],
        "packet": _packet_ref(packet),
        "transcript_mark": transcript_mark(tp),
    }
    if children is None:
        children = (child_reader or ro.child_state)(sid) if sid else {"verdict": ro.UNKNOWN, "reason": "no owner"}
    if origin == "recovery" and children.get("verdict") == ro.UNKNOWN and tp is None:
        # G21: the predecessor is gone and left no transcript -- nothing can be waited on. Its
        # children are named lost (a warning the successor sees), not a refusal that blocks for ever.
        children = {"verdict": "EXPIRED", "pending": [], "unconsumed": [],
                    "reason": f"predecessor dead with no transcript; any background child is lost ({children.get('reason')})"}
    cap["children"] = children
    if tp is not None:
        root = cap["repo"].get("root") if cap["repo"].get("state") == "OK" else None
        cap["foreign"] = ro.foreign_custody(ro.session_writes(tp), root)
    elif origin == "recovery":
        # G21 only: a dead predecessor with no transcript. Stated, never an empty "OK".
        cap["custody_unchecked"] = "no transcript"
    else:
        # A live handoff or a fallback with no readable transcript cannot show what the worker wrote
        # elsewhere: UNKNOWN custody, which rollover.completeness refuses by name (spec 3.5).
        cap["foreign"] = {"state": ro.UNKNOWN, "reason": "no readable transcript: the worker's own writes cannot be checked"}
    return cap


# --------------------------------------------------------------------------- seal / gate
def seal_mission(cap: dict, sd=None) -> dict:
    """Seal through rollover, and record the receipt where rollover.gate reads it. The verdict is
    UNKNOWN when that row could not be written: a seal the gate cannot see is not a seal."""
    sd = state_dir(sd)
    receipt = ro.seal(cap, sd)
    comp = ro.completeness(cap)
    stf = ro.safe_to_forget(receipt, comp)
    run = cap.get("run") or {}
    recorded = ro.ledger("capsule_sealed", sd, session_id=cap.get("session_id"), cwd=cap.get("cwd"),
                         capsule=receipt, safe_to_forget=stf["verdict"], refusals=stf["reasons"],
                         kind="mission", mission_id=run.get("mission_id"), epoch=run.get("epoch"),
                         seal_origin=cap.get("seal_origin"))
    verdict = stf["verdict"] if recorded else ro.UNKNOWN
    reasons = stf["reasons"] if recorded else stf["reasons"] + ["the seal record was not written (ledger busy)"]
    return {"verdict": verdict, "key": cap.get("session_id"), "receipt": receipt,
            "reasons": reasons, "warnings": comp["warnings"]}


def gate_before_stop(key: str, sd=None, now: Optional[float] = None,
                     max_age_s: float = ro.RESET_MAX_AGE_S) -> dict:
    """May the outgoing worker be stopped RIGHT NOW? Exactly rollover.gate on the sealed capsule:
    the bytes are those sealed, the seal is fresh, it is not already certified.

    No transcript re-check -- G3 (binding, supersedes I2) replaced it with "seal only when the host
    lists the owner idle/done" plus `outgoing_stop_authorized`, which T6 ledgers. A first version
    re-checked the transcript mark here; the review of 2026-10-03 found it both contradicted G3
    (refusing a stop for rows the host appends after the turn) and switched itself off when no path
    was passed. `transcript_mark` stays in the capsule as provenance for the chain audit (T7)."""
    return ro.gate(key, state_dir(sd), max_age_s=max_age_s, now=now)


# --------------------------------------------------------------------------- pre-certification marker
def arm_successor(rec: dict, sd=None, now: Optional[float] = None, capsule_key: Optional[str] = None) -> dict:
    """The marker for the worker about to run epoch+1, written BEFORE it is spawned (spec 3.3): from
    its first tool call it has no mutation authority until it certifies the capsule of `rec["epoch"]`.
    Created by rollover.precert_arm (G25), which replaces any earlier epoch's marker -- a merge would
    have inherited that epoch's certification.

    `capsule_key` (G6): the caller passes the record's own field. Epoch arithmetic is right only on a
    relay from the epoch that sealed; a replace after a launch that never acked runs from an epoch
    that sealed nothing, and the successor must still certify the capsule its predecessor left."""
    mid, epoch = rec["mission_id"], int(rec["epoch"])
    fields = {"worker": worker_name(mid, epoch + 1), "epoch": epoch + 1,
              "capsule_key": capsule_key or ro.mission_key(mid, epoch),
              "cwd": rec.get("cwd"), "resume_cmd": rec.get("resume_command"), "tool": TOOL}
    if now is not None:
        fields["created_at"] = now
    return ro.precert_arm(mid, fields, state_dir(sd))


def bind_successor(mission_id: str, worker: str, *, bg_id: Optional[str] = None,
                   owner_session: Optional[str] = None, sd=None) -> dict:
    """Name the armed worker as the host reported it (bg id after the spawn, session at its ack).
    An update of the existing marker, so it goes through the merging writer -- and therefore only
    onto THIS worker's uncertified marker. Binding a new bg id into an earlier epoch's certified
    marker (left behind when arming failed) would make the guard read the new worker as certified."""
    fields = {k: v for k, v in (("bg_id", bg_id), ("owner_session", owner_session)) if v}
    if not fields:
        raise ValueError("bind_successor needs a bg_id or an owner_session")
    mk = ro.precert_read(mission_id, state_dir(sd))
    if mk is None:
        raise ValueError(f"no armed marker for {mission_id}: arm before binding")
    if mk.get("worker") != worker:
        raise ValueError(f"the marker for {mission_id} names worker {mk.get('worker')!r}, not {worker!r}: arm first")
    if mk.get("certified_at"):
        raise ValueError(f"the marker for {mission_id} is already certified: it is not an armed successor's")
    return ro.precert_write(mission_id, fields, state_dir(sd))


# --------------------------------------------------------------------------- successor CLI
def _worker_of(mission_id: str, session_id: str) -> tuple[Optional[dict], str]:
    """G12: only the mission's CURRENT worker may resume or certify for it -- the acked owner, or
    while LAUNCHING the session whose id starts with the bg id the host printed for this launch."""
    import gsd_mission as gm
    rec = gm.load(mission_id)
    if rec is None:
        return None, f"no mission {mission_id}"
    owner = (rec.get("owner") or {}).get("session_id")
    bg = (rec.get("pending") or {}).get("bg_id")
    if session_id == owner or (bg and session_id.startswith(bg)):
        return rec, ""
    return None, f"session {session_id[:8]} is not the current worker of {mission_id}"


# --------------------------------------------------------------------------- chain audit (T7, spec 11.6)
def _rollover_rows(sd: Path) -> Optional[list]:
    """Every row of the rollover ledger, or None when it cannot be read (absent file = no rows)."""
    path = sd / "rollover-ledger.jsonl"
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    rows = []
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue          # a torn tail row is the ledger's own known shape, not a broken chain
        if isinstance(r, dict):
            rows.append(r)
    return rows


def _lineage(mission_id: str, load, events) -> list:
    """The lineage in order: `renewed_from` back to the root, then `mission_renewed` rows forward.
    Bounded, so a cycle in damaged records cannot hang the audit."""
    chain, cur = [], mission_id
    for _ in range(64):
        rec = load(cur)
        if rec is None or cur in chain:
            break
        chain.insert(0, cur)
        cur = rec.get("renewed_from")
        if not cur:
            break
    cur = mission_id
    for _ in range(64):
        nxt = next((e.get("successor") for e in events(cur) if e.get("event") == "mission_renewed"), None)
        if not nxt or nxt in chain or load(nxt) is None:
            break
        chain.append(nxt)
        cur = nxt
    return chain


def audit_mission(mission_id: str, sd=None, load=None, events=None) -> dict:
    """Read-only chain audit of a capsule-v2 lineage (spec 11.6): INTACT | BROKEN | UNREADABLE, every
    link checked, and the FIRST broken link by name. A step a live mission has not reached yet is OPEN,
    never broken -- the audit judges history, it does not predict it."""
    import gsd_mission as gm
    import gsd_long_run as lr
    sd = state_dir(sd)
    load = load or gm.load
    events = events or lr.ledger_events
    try:
        if load(mission_id) is None:
            return {"verdict": "UNREADABLE", "reason": f"no mission {mission_id}", "links": []}
        chain = _lineage(mission_id, load, events)
        recs = {m: load(m) or {} for m in chain}
        evs_of = {m: events(m) for m in chain}
    except Exception as exc:  # noqa: BLE001 -- a malformed record or ledger is unreadable, never "intact"
        return {"verdict": "UNREADABLE", "reason": f"{type(exc).__name__}: {exc}", "links": []}
    # Every mission ledgers at least `mission_prepared`: a v2 mission with no rows is history the audit
    # cannot see, and judging nothing must not read as INTACT.
    blind = [m for m in chain if recs[m].get("rollover_protocol") == PROTOCOL and not evs_of[m]]
    if blind:
        return {"verdict": "UNREADABLE", "reason": f"no ledger rows for v2 mission(s) {', '.join(blind)}",
                "links": []}
    rows = _rollover_rows(sd)
    if rows is None:
        return {"verdict": "UNREADABLE", "reason": "rollover ledger unreadable", "links": []}
    by_key: dict = {}
    for r in rows:
        by_key.setdefault(str(r.get("session_id") or ""), []).append(r)
    links: list = []

    def link(name, ok, mission, detail, open_=False):
        links.append({"link": name, "mission": mission, "detail": detail,
                      "state": "OK" if ok else ("OPEN" if open_ else "BROKEN")})

    for mid in chain:
        rec = recs[mid]
        live = rec.get("state") not in gm.TERMINAL
        if rec.get("rollover_protocol") != PROTOCOL:
            links.append({"link": "protocol", "mission": mid, "state": "SKIPPED",
                          "detail": "legacy record: no capsule chain to audit"})
            continue
        evs = evs_of[mid]
        names = [e.get("event") for e in evs]
        # every rotation: sealed SAFE -> authorized before the launch -> the successor's own chain
        for i, e in enumerate(evs):
            if e.get("event") != "outgoing_stop_authorized":
                continue
            # transition() ledgers only epoch/state/seq, never the record's capsule_key; the
            # authorization does not move the epoch, so the key is the row's own epoch (capsule_key()).
            key = e.get("capsule_key") or (ro.mission_key(mid, e["epoch"]) if e.get("epoch") is not None else "")
            seals = [r for r in by_key.get(key, []) if r.get("event") == "capsule_sealed"]
            link(f"sealed {key}", any(r.get("safe_to_forget") == "SAFE_TO_FORGET" for r in seals), mid,
                 f"{len(seals)} seal row(s)" if seals else "no capsule_sealed row for the authorized key")
            later = names[i + 1:]
            if "launch_claimed" not in later:
                if "mission_halted" in later:
                    continue        # a halt's own seal: the renewal carries it (checked below)
                link(f"launched after {key}", False, mid, "authorized, no successor launch", open_=live)
                continue
            link(f"authorized before launch {key}", True, mid, "outgoing_stop_authorized precedes launch_claimed")
            _successor_links(link, mid, key, evs[i + 1:], by_key, live)
        # a v2 halt: continuity present and consistent with the renewal
        if "mission_halted" in names:
            cont = rec.get("continuity")
            renewed = [x for x in evs if x.get("event") == "mission_renewed"]
            if not isinstance(cont, dict) or not cont.get("kind"):
                link("halt continuity", False, mid, "v2 HALTED record carries no continuity")
            elif cont["kind"] in ("handoff", "recovery", "inherited"):
                ok = any(x.get("capsule_key") == cont.get("capsule_key") for x in renewed)
                link(f"halt {cont['kind']} renewed with {cont.get('capsule_key')}", ok, mid,
                     "mission_renewed carries the continuity key" if ok else "renewal missing or carries another key")
                if cont["kind"] == "handoff":
                    ok = ("outgoing_stop_authorized" in names
                          and names.index("outgoing_stop_authorized") < names.index("mission_halted"))
                    link("halt handoff sealed before the stop", ok, mid, "authorization precedes the halt")
                if cont["kind"] == "recovery":
                    seals = [r for r in by_key.get(cont.get("capsule_key") or "", [])
                             if r.get("event") == "capsule_sealed" and r.get("seal_origin") == "recovery"]
                    link("halt recovery sealed after the stop", bool(seals) and "continuity_recovery" in names, mid,
                         f"{len(seals)} recovery seal row(s)")
            elif cont["kind"] == "refused":
                link("halt refused: nothing renewed", not renewed and "renewal_refused_no_capsule" in names, mid,
                     "refusal ledgered, nothing renewed" if not renewed else "a refused continuity was renewed")
            else:
                link(f"halt {cont['kind']}", True, mid, cont.get("reason") or "")
        # a renewal's first worker certifies the capsule its predecessor left
        if rec.get("renewed_from") and rec.get("capsule_key") and "launch_claimed" in names:
            idx = names.index("launch_claimed")
            _successor_links(link, mid, rec["capsule_key"], evs[idx:], by_key, live)
    broken = next((x for x in links if x["state"] == "BROKEN"), None)
    return {"verdict": "BROKEN" if broken else "INTACT", "lineage": chain, "links": links, "first_broken": broken}


def _successor_links(link, mid: str, key: str, evs_after: list, by_key: dict, live: bool) -> None:
    """acked -> claimed with a refresh -> certified -> marker lifted, for the successor of `key`."""
    if not any(e.get("event") in ("worker_acked", "worker_adopted") for e in evs_after):
        link(f"acked {key}", False, mid, "successor never acknowledged", open_=live)
        return
    link(f"acked {key}", True, mid, "successor acknowledged")
    rows = by_key.get(key, [])
    claimed = [r for r in rows if r.get("event") == "successor_claimed"]
    if not claimed:
        link(f"claimed {key}", False, mid, "no successor_claimed row", open_=live)
        return
    link(f"claimed+refreshed {key}", all(r.get("refresh") for r in claimed), mid,
         f"{len(claimed)} claim(s), last refresh {claimed[-1].get('refresh')}")
    certified = [r for r in rows if r.get("event") == "resume_certified"]
    if not certified:
        link(f"certified {key}", False, mid, "no resume_certified row", open_=live)
        return
    link(f"certified {key}", True, mid, f"by {certified[-1].get('claimant')}")
    lifted = not any(r.get("event") == "precert_not_lifted" for r in rows)
    link(f"marker lifted {key}", lifted, mid, "no precert_not_lifted row" if lifted else "precert_not_lifted recorded")


def _cli(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="mission_capsule.py", description="capsule-v2 successor side for a mission worker")
    p.add_argument("cmd", choices=("resume", "certify", "status", "audit"))
    p.add_argument("--mission", required=True)
    p.add_argument("--state-dir", default=None)
    for k in ("goal", "branch", "head", "next", "dirty"):
        p.add_argument(f"--{k}", default=None)
    a = p.parse_args(argv)
    sd = state_dir(a.state_dir)
    if a.cmd == "audit":
        # Read-only, any session (T8's out-of-process judge): exit 0 INTACT, 1 BROKEN, 2 UNREADABLE.
        res = audit_mission(a.mission, sd)
        for x in res.get("links") or []:
            print(f"  {x['state']:8} {x['mission']}  {x['link']} -- {x['detail']}")
        fb = res.get("first_broken")
        print(f"AUDIT {res['verdict']}" + (f" -- first broken: {fb['link']} ({fb['mission']})" if fb else "")
              + (f" -- {res['reason']}" if res.get("reason") else ""))
        return {"INTACT": 0, "BROKEN": 1}.get(res["verdict"], 2)
    if a.cmd == "status":
        mk = ro.precert_read(a.mission, sd)
        print(json.dumps({"marker": mk, "gate": ro.gate(mk["capsule_key"], sd) if mk else None,
                          "claim": ro.claim_holder(mk["capsule_key"], sd) if mk else None}, indent=1, default=str))
        return 0
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID") or ""
    if not sid:
        # No ppid or cwd fallback (G12): a guessed identity could certify for another worker.
        print("REFUSED: CLAUDE_CODE_SESSION_ID is unset; only the mission's worker session may run this.")
        return 2
    rec, why = _worker_of(a.mission, sid)
    if rec is None:
        print(f"REFUSED: {why}.")
        return 5
    key = rec.get("capsule_key")
    if not key:
        print(f"NOT RESUMABLE: mission {a.mission} records no capsule_key (it was not rotated under capsule-v2).")
        return 4
    if a.cmd == "certify":
        answers = {k: getattr(a, k) for k in ("goal", "branch", "head", "next", "dirty") if getattr(a, k)}
        # The marker to lift is THIS mission's: after a renewal the capsule names its predecessor.
        rc, _res = ro.certify_flow(key, sid, answers, sd, mission_id=a.mission)
        return rc
    try:
        cap = json.loads(ro.capsule_path(key, sd).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"NOT RESUMABLE: capsule {key} unreadable ({exc.__class__.__name__}).")
        return 4
    data, gwhy = ask_gsd(cap.get("cwd") or rec.get("cwd"), rec.get("workstream"))
    items, _src = render_obligations(data)
    if not items:
        # I4 judges `next` against GSD NOW; with no answer there is nothing to judge it against.
        # Refused before the claim, so a later attempt is not locked out.
        print(f"NOT RESUMABLE NOW: GSD gives no open obligation ({gwhy or 'none recommended'}); retry.")
        return 4
    me = Path(__file__).as_posix()
    cmd = (f"python {me} certify --mission {a.mission} --goal <file> --branch <b> --head <7> "
           f"--next \"<first obligation>\"" + (" --dirty <n>" if cap.get("degraded") else ""))
    return ro.resume_flow(cap, sid, cap.get("cwd") or rec.get("cwd"), sd, certify_cmd=cmd, obligations=items)


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
