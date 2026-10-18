"""Decision Plane: an Owner decision is a durable, self-contained contract, not chat and not STATE.md prose.

Spec: vault/plans/decision-plane-master-plan-2026-10-17.md (covers: decision-plane, owner-decision).

One append-only JSONL per mission under the long-run state dir. A Decision Object names its question, its evidence
(with a fingerprint), its orthogonal dimensions and its options. An option is SELECTABLE only when applying it needs
no further parameter: every dimension has a value and every amount carries its unit. Selecting yields a typed,
hashed Receipt; a replay is a no-op, a changed fingerprint invalidates the decision, an unknown id is a hard
failure (DanglingDecision), never a fallback to prose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

CLASSES = ("CAPITAL", "SCOPE", "PRODUCT", "SECURITY", "IRREVERSIBLE", "EXTERNAL", "RISK")
OPEN, READY, RESOLVED, SUPERSEDED, INVALIDATED = "OPEN", "READY_FOR_OWNER", "RESOLVED", "SUPERSEDED", "INVALIDATED"
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,23}$")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DIM_KINDS = ("capital", "enum")
PRIVILEGED = ("CAPITAL", "SECURITY", "IRREVERSIBLE", "EXTERNAL")


class DecisionError(Exception):
    pass


class DanglingDecision(DecisionError):
    """A decision id with no durable contract. Never recovered from prose or a remote grep."""


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(evidence: dict) -> str:
    return hashlib.sha256(_canon(evidence).encode("utf-8")).hexdigest()[:16]


def store_path(mission_id: str) -> Path:
    if not _ID.match(mission_id or ""):
        raise DecisionError(f"invalid mission id: {mission_id!r}")
    return lr.state_dir() / f"decisions-{mission_id}.jsonl"


def _append(mission_id: str, row: dict) -> None:
    p = store_path(mission_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(_canon(row) + "\n")


def _rows(mission_id: str) -> list[dict]:
    p = store_path(mission_id)
    if not p.exists():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError as e:   # an unreadable store is not an empty one
                raise DecisionError(f"{p.name}:{n} unreadable: {e}") from e
    return out


def _fold(mission_id: str) -> dict[str, dict]:
    """Current state of every decision: the created object plus the events applied to it, in order."""
    cur: dict[str, dict] = {}
    for r in _rows(mission_id):
        ev, did = r.get("ev"), r.get("id")
        if ev == "created":
            cur[did] = {**r["object"], "status": r["object"].get("status", OPEN)}
        elif did in cur and ev == "resolved":
            cur[did].update(status=RESOLVED, receipt=r["receipt"])
        elif did in cur and ev == "invalidated":
            cur[did].update(status=INVALIDATED, invalidated_reason=r.get("reason"))
        elif did in cur and ev == "superseded":
            cur[did].update(status=SUPERSEDED, superseded_by=r.get("by"))
    return cur


def get(mission_id: str, decision_id: str) -> dict:
    d = _fold(mission_id).get(decision_id)
    if d is None:
        raise DanglingDecision(f"decision {decision_id} has no durable contract on {mission_id}")
    return d


def _option_problems(dec: dict, opt: dict) -> list[str]:
    bad = []
    tok = opt.get("token")
    if not isinstance(tok, str) or not _TOKEN.match(tok):
        bad.append(f"option token {tok!r} is not a short token")
    params = opt.get("params") or {}
    for dim in dec.get("dimensions", []):
        name, kind = dim["name"], dim["kind"]
        v = params.get(name)
        if v is None or v == "":
            bad.append(f"option {tok}: dimension {name} has no value")
        elif kind == "capital":
            if not (isinstance(v, dict) and isinstance(v.get("ceiling"), int) and v["ceiling"] > 0 and v.get("unit")):
                bad.append(f"option {tok}: capital {name} needs an integer ceiling > 0 and a unit")
        elif kind == "enum" and "allowed" in dim and v not in dim["allowed"]:
            bad.append(f"option {tok}: {name}={v!r} outside {dim['allowed']}")
    for extra in params:
        if extra not in {d["name"] for d in dec.get("dimensions", [])}:
            bad.append(f"option {tok}: parameter {extra} is not a declared dimension")
    return bad


def closure_gate(dec: dict) -> list[str]:
    """Empty list = every option is executable as presented. Anything else may not be shown to the Owner."""
    bad = []
    if dec.get("class") not in CLASSES:
        bad.append(f"unknown class {dec.get('class')!r}")
    dims = dec.get("dimensions") or []
    if not dims:
        bad.append("no dimensions declared")
    for d in dims:
        if d.get("kind") not in DIM_KINDS:
            bad.append(f"dimension {d.get('name')}: unknown kind {d.get('kind')!r}")
    opts = dec.get("options") or []
    if len(opts) < 1:
        bad.append("no options")
    toks = [o.get("token") for o in opts]
    if len(set(toks)) != len(toks):
        bad.append("duplicate option tokens")
    for o in opts:
        bad += _option_problems(dec, o)
    rec = (dec.get("recommendation") or {}).get("token")
    if rec is not None and rec not in toks:
        bad.append(f"recommendation {rec} is not an option")
    if not dec.get("evidence"):
        bad.append("no evidence handles")
    if not dec.get("consumers"):
        bad.append("no consumer mission")
    return bad


def create(mission_id: str, spec: dict, now: float | None = None) -> dict:
    """Persist a Decision Object. READY_FOR_OWNER only if the Closure Gate passes; otherwise OPEN and not surfaceable."""
    did = spec.get("id")
    if not isinstance(did, str) or not _ID.match(did):
        raise DecisionError(f"invalid decision id: {did!r}")
    if did in _fold(mission_id):
        raise DecisionError(f"decision {did} already exists on {mission_id}")
    obj = {k: spec.get(k) for k in ("id", "class", "question", "dimensions", "options", "recommendation",
                                    "consumers", "wake_policy", "invalidators")}
    obj["mission"] = mission_id
    obj["evidence"] = dict(spec.get("evidence") or {})
    obj["fingerprint"] = fingerprint(obj["evidence"])
    obj["created_at"] = time.time() if now is None else now
    obj["problems"] = closure_gate(obj)
    obj["status"] = READY if not obj["problems"] else OPEN
    _append(mission_id, {"ev": "created", "id": did, "object": obj})
    return obj


def surface(mission_id: str, decision_id: str) -> dict:
    """What the Owner is shown. Refuses an incomplete decision (the Closure Gate is the only door)."""
    d = get(mission_id, decision_id)
    if d["status"] != READY:
        raise DecisionError(f"{decision_id} is {d['status']}; it cannot be shown"
                            + (f": {d['problems']}" if d.get("problems") else ""))
    return {"id": d["id"], "question": d["question"], "options": d["options"], "recommendation": d["recommendation"],
            "valid_tokens": [o["token"] for o in d["options"]], "anchor": anchor(d)}


def parse_choice(dec: dict, text: str) -> tuple[str | None, list[str]]:
    """Providerless mapping of short Owner input to ONE option token. (token, valid_tokens); token None = ambiguous."""
    valid = [o["token"] for o in dec["options"]]
    low = {t.lower(): t for t in valid}
    hits = {low[w.lower()] for w in _WORD.findall(text or "") if w.lower() in low}
    return (next(iter(hits)) if len(hits) == 1 else None), valid


def _receipt_sha(body: dict) -> str:
    return hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()[:16]


def resolve(mission_id: str, decision_id: str, owner_text: str, evidence_now: dict | None = None,
            now: float | None = None, authority: dict | None = None) -> dict:
    """Owner selection -> typed Receipt. Idempotent; a stale decision is invalidated, never applied.

    A PRIVILEGED class (capital, security, irreversible, external) is resolved only with `authority`: the uuid of an
    Owner-typed transcript entry (resolve_from_transcript). Text a model could have written is not authority."""
    d = get(mission_id, decision_id)
    if d["class"] in PRIVILEGED and d["status"] != RESOLVED and not (authority or {}).get("uuid"):
        raise DecisionError(f"{decision_id} is {d['class']}: only an Owner-typed transcript entry can resolve it")
    token, valid = parse_choice(d, owner_text)
    if d["status"] == RESOLVED:
        if token is not None and token == d["receipt"]["token"]:
            return {"receipt": d["receipt"], "recorded": False}
        raise DecisionError(f"{decision_id} is already resolved as {d['receipt']['token']}")
    if d["status"] != READY:
        raise DecisionError(f"{decision_id} is {d['status']}; it cannot be resolved")
    if token is None:
        raise DecisionError(f"ambiguous or empty selection; valid tokens: {valid}")
    if evidence_now is not None and fingerprint(evidence_now) != d["fingerprint"]:
        _append(mission_id, {"ev": "invalidated", "id": decision_id, "reason": "evidence fingerprint changed"})
        raise DecisionError(f"{decision_id} invalidated: evidence changed since the packet was compiled")
    opt = next(o for o in d["options"] if o["token"] == token)
    body = {"decision": decision_id, "mission": mission_id, "token": token, "params": opt["params"],
            "evidence_fp": d["fingerprint"], "consumers": d["consumers"], "authority": authority}
    receipt = {**body, "at": time.time() if now is None else now, "sha": _receipt_sha(body)}
    _append(mission_id, {"ev": "resolved", "id": decision_id, "receipt": receipt})
    return {"receipt": receipt, "recorded": True}


def anchor(dec: dict) -> str:
    """The string an assistant message must display, verbatim, before an Owner entry can resolve this decision."""
    return f"DP:{dec['id']}:{dec['fingerprint']}"


def resolve_from_transcript(mission_id: str, decision_id: str, transcript_path, evidence_now: dict | None = None,
                            now: float | None = None) -> dict:
    """Resolve from the first Owner-typed entry that follows an assistant entry displaying the decision's anchor.
    Same proof as capital_authority: type=user, origin human, promptSource typed|queued, string content."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from modules.provider_routing import capital_authority as oca
    d = get(mission_id, decision_id)
    seen = False
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as e:
        raise DecisionError(f"transcript unreadable: {e}") from e
    for ln in lines:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if not seen:
            seen = e.get("type") == "assistant" and anchor(d) in oca._text_of(e)
            continue
        if oca._is_owner_typed(e) and parse_choice(d, e["message"]["content"])[0] is not None:
            return resolve(mission_id, decision_id, e["message"]["content"], evidence_now, now,
                           authority={"uuid": e.get("uuid"), "timestamp": e.get("timestamp"), "anchor": anchor(d)})
    raise DecisionError(f"{decision_id}: no Owner-typed selection after an entry displaying {anchor(d)}")


def invalidate(mission_id: str, decision_id: str, reason: str) -> None:
    get(mission_id, decision_id)
    _append(mission_id, {"ev": "invalidated", "id": decision_id, "reason": reason})


def supersede(mission_id: str, old_id: str, new_id: str) -> None:
    get(mission_id, old_id)
    get(mission_id, new_id)
    _append(mission_id, {"ev": "superseded", "id": old_id, "by": new_id})


def unresolved(mission_id: str) -> list[str]:
    """Decisions that still block their consumers (a WAITING mission wakes when this empties)."""
    return [i for i, d in _fold(mission_id).items() if d["status"] in (OPEN, READY)]


# --- delivery: a receipt travels as a verified bundle; the consumer applies and wakes, no model in between -------
HOSTS = {"gex44": {"ssh": "gex44", "pp": "/home/kobii/.claude/skills/claude-power-pack",
                   "env": "CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude"}}


def consumer_hosts() -> dict:
    """consumer mission -> host name, from a durable file next to the stores. No entry = local consumer."""
    p = lr.state_dir() / "decision-hosts.json"
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def export_bundle(mission_id: str, decision_id: str) -> dict:
    rows = [r for r in _rows(mission_id) if r.get("id") == decision_id and r.get("ev") in ("created", "resolved")]
    kinds = {r["ev"] for r in rows}
    if kinds != {"created", "resolved"}:
        raise DecisionError(f"{decision_id}: only a resolved decision can be delivered (have {sorted(kinds)})")
    return {"rows": rows, "mission": mission_id, "id": decision_id}


def verify_bundle(bundle: dict) -> tuple[dict, dict]:
    """Everything the consumer relies on is recomputed here; nothing in the bundle is trusted for its own sake."""
    by = {r.get("ev"): r for r in bundle.get("rows", [])}
    if set(by) != {"created", "resolved"}:
        raise DecisionError("bundle needs exactly a created and a resolved row")
    obj, rec = by["created"]["object"], by["resolved"]["receipt"]
    if obj.get("id") != rec.get("decision") or obj.get("mission") != rec.get("mission"):
        raise DecisionError("receipt does not belong to the decision object")
    if fingerprint(obj.get("evidence") or {}) != obj.get("fingerprint") or rec.get("evidence_fp") != obj["fingerprint"]:
        raise DecisionError("evidence fingerprint mismatch")
    if closure_gate(obj):
        raise DecisionError(f"decision fails the Closure Gate: {closure_gate(obj)}")
    opt = next((o for o in obj["options"] if o["token"] == rec.get("token")), None)
    if opt is None or opt["params"] != rec.get("params"):
        raise DecisionError("receipt token/params are not an option of the decision")
    body = {k: rec.get(k) for k in ("decision", "mission", "token", "params", "evidence_fp", "consumers", "authority")}
    if _receipt_sha(body) != rec.get("sha"):
        raise DecisionError("receipt sha mismatch")
    if obj["class"] in PRIVILEGED and not (rec.get("authority") or {}).get("uuid"):
        raise DecisionError(f"{obj['class']} receipt carries no Owner-typed authority")
    return obj, rec


def render_view(obj: dict, rec: dict) -> str:
    """Text is a VIEW of the receipt, for the worker's prompt and the mission's directive list."""
    p, opt = rec["params"], next(o for o in obj["options"] if o["token"] == rec["token"])
    cap = p.get("capital") or {}
    return (f"OWNER DECISION {obj['id']} (receipt {rec['sha']}, binding; settles any open 'OWNER DECISION NEEDED' on this "
            f"topic in STATE.md and in a blocked-on-Owner state): option {rec['token']} - {opt.get('label', '')}. "
            f"Capital ceiling {cap.get('ceiling'):,} {cap.get('unit')}; scope {p.get('scope')}; efficiency policy "
            f"{p.get('efficiency')} (cost reduction stays on whatever the ceiling). Record it as resolved in STATE.md and "
            "continue with the next runnable work now; do not wait for the Owner again on this point.")


def _wake(mission: str, view: str, *, sessions, runner, stop_runner, pid_alive, host_fetch, now) -> dict:
    import gsd_mission as gm
    import gsd_epoch as ge
    rec = gm.load(mission)
    if rec is None:
        return {"ok": False, "why": "mission not on this host"}
    if rec["state"] in gm.TERMINAL:
        return {"ok": False, "why": f"mission is {rec['state']}"}
    gm.add_directive(mission, view, now=now)
    rec = gm.load(mission)
    owner = rec.get("owner") or {}
    sess = sessions if sessions is not None else gm.host_sessions()
    row = gm._host_row(owner.get("session_id"), sess) if owner.get("session_id") and sess is not None else None
    if not owner.get("session_id"):
        return {"ok": False, "why": "no owner: the next launch card carries the decision"}
    if owner.get("kind") != "background":
        return {"ok": False, "why": "interactive owner: not resumed; the decision is on the mission"}
    if sess is None:
        return {"ok": False, "why": "host unreachable: the next launch card carries the decision"}
    if row is None or row.get("state") in ("stopped", "failed", "exited"):
        return {"ok": False, "why": "owner not live: the next launch card carries the decision"}
    kw = {k: v for k, v in (("pid_alive", pid_alive), ("host_fetch", host_fetch)) if v is not None}
    ok, how = gm.stop_owner(owner, sess, runner=stop_runner, **kw)
    if not ok:
        return {"ok": False, "why": f"owner did not stop ({how}); the next launch card carries the decision"}
    return ge.continue_worker(mission, rec, prompt=view,
                              decision={"decision": ge.CONTINUE, "cause": ge.TURN_CONTINUATION,
                                        "reason": "owner decision receipt"},
                              runner=runner, stop_runner=stop_runner, now=now)


def apply_capital(consumer: str, ceiling: int, evidence: dict) -> dict:
    """D6: a CUMULATIVE ceiling becomes the consumer's own breaker envelope. The consumer's meter covers only itself, so
    its trip budget is the ceiling minus what the predecessors spent, and the estimate the breaker judges is that budget
    over the trip ratio. Fails closed without predecessor meters in the evidence: a ceiling is never guessed."""
    import gsd_mission as gm
    meters = (evidence or {}).get("meters")
    if not isinstance(meters, dict) or not meters:
        raise DecisionError("a ceiling change needs evidence.meters (spend per mission on the cumulative meter)")
    rec = gm.load(consumer)
    if rec is None:
        raise DecisionError(f"mission {consumer} is not on this host")
    spent_before = 0
    for m, v in meters.items():
        if m == consumer:
            continue
        cur = (gm.load(m) or {}).get("cost_mark") or {}
        spent_before += max(int(v), int(cur.get("tokens") or 0))     # a predecessor can only have grown since the snapshot
    own = int(((rec.get("cost_mark") or {}).get("tokens")) or 0)
    import mission_spend as ms
    ratio = float(rec.get("token_trip_ratio") or ms.DEFAULT_TRIP_RATIO)
    budget = ceiling - spent_before
    if budget <= own:
        raise DecisionError(f"ceiling {ceiling:,} leaves {budget:,} for {consumer}, which already spent {own:,}")
    estimate = int(budget / ratio)
    if rec.get("token_estimate") != estimate:
        gm.set_envelope(consumer, token_estimate=estimate)
    return {"consumer": consumer, "ceiling": ceiling, "predecessors": spent_before, "trip_budget": budget,
            "ratio": ratio, "token_estimate": estimate, "changed": rec.get("token_estimate") != estimate}


def consume_bundle(bundle: dict, wake: bool = True, sessions=None, runner=None, stop_runner=None, pid_alive=None,
                   host_fetch=None, now: float | None = None) -> dict:
    """Verify, persist, apply, wake. Idempotent per receipt sha. A ceiling equal to the old trip applies nothing; a
    different one is applied through apply_capital (D6) BEFORE anything is recorded, so a refusal leaves no receipt."""
    obj, rec = verify_bundle(bundle)
    mid, did = obj["mission"], obj["id"]
    cap = (rec["params"] or {}).get("capital")
    have = _fold(mid).get(did)
    if have and have["status"] == RESOLVED and have["receipt"]["sha"] != rec["sha"]:
        raise DecisionError(f"{did} already resolved with receipt {have['receipt']['sha']}")
    applied = None
    if cap and cap["ceiling"] != (obj.get("evidence") or {}).get("old_trip"):
        if len(obj["consumers"]) != 1:
            raise DecisionError(f"{did}: a ceiling change needs exactly one consumer meter, got {obj['consumers']}")
        applied = apply_capital(obj["consumers"][0], int(cap["ceiling"]), obj.get("evidence") or {})
    if have and have["status"] == RESOLVED:
        return {"receipt": rec, "recorded": False, "applied": applied,
                "woke": {"ok": False, "why": "already consumed (idempotent)"}}
    if have is None:
        _append(mid, {"ev": "created", "id": did, "object": obj})
    _append(mid, {"ev": "resolved", "id": did, "receipt": rec})
    view = render_view(obj, rec)
    woke = {"ok": False, "why": "wake not requested"}
    if wake:
        woke = {c: _wake(c, view, sessions=sessions, runner=runner, stop_runner=stop_runner, pid_alive=pid_alive,
                         host_fetch=host_fetch, now=now) for c in obj["consumers"]}
    return {"receipt": rec, "recorded": True, "woke": woke, "applied": applied}


def deliver(mission_id: str, decision_id: str, host: str) -> dict:
    """Ship the verified bundle to the consumer host and run its consumer. One command; no model carries content."""
    import subprocess
    h = HOSTS.get(host)
    if h is None:
        raise DecisionError(f"unknown host {host!r}")
    bundle = export_bundle(mission_id, decision_id)
    sha = bundle["rows"][-1]["receipt"]["sha"]
    remote = f"/tmp/dp-bundle-{sha}.json"
    up = subprocess.run(["ssh", "-o", "BatchMode=yes", h["ssh"], f"cat > {remote}"], input=json.dumps(bundle).encode(),
                        capture_output=True, timeout=60)
    if up.returncode != 0:
        raise DecisionError(f"upload to {host} failed: {up.stderr.decode(errors='replace')[-200:]}")
    run = subprocess.run(["ssh", "-o", "BatchMode=yes", h["ssh"],
                          f"cd {h['pp']} && {h['env']} python3 tools/decision_plane.py consume --file {remote}"],
                         stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    return {"returncode": run.returncode, "stdout": run.stdout.strip(), "stderr": run.stderr.strip()[-400:]}


def route(mission_id: str, decision_id: str) -> list[dict]:
    """The event router: each consumer on a remote host gets the receipt; a local consumer reads the store."""
    d = get(mission_id, decision_id)
    if d["status"] != RESOLVED:
        raise DecisionError(f"{decision_id} is {d['status']}; nothing to route")
    hosts, out = consumer_hosts(), []
    for c in d["consumers"]:
        h = hosts.get(c)
        out.append({"consumer": c, "host": h, **(deliver(mission_id, decision_id, h) if h else {"returncode": 0,
                    "stdout": "local consumer: reads the store", "stderr": ""})})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="decision_plane")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--mission", required=True)
    c.add_argument("--file", required=True, help="JSON decision spec")
    s = sub.add_parser("show")
    s.add_argument("--mission", required=True)
    s.add_argument("--decision", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--mission", required=True)
    r.add_argument("--decision", required=True)
    r.add_argument("--choice", required=True, help="the Owner's short input")
    rt = sub.add_parser("resolve-transcript", help="resolve from an Owner-typed transcript entry, then route the receipt")
    rt.add_argument("--mission", required=True)
    rt.add_argument("--decision", required=True)
    rt.add_argument("--transcript", required=True)
    rt.add_argument("--no-route", action="store_true")
    cs = sub.add_parser("consume", help="consumer side: verify a bundle, persist it, apply it, wake the owner")
    cs.add_argument("--file", required=True)
    cs.add_argument("--no-wake", action="store_true")
    dv = sub.add_parser("deliver", help="ship a resolved decision to a host and run its consumer")
    dv.add_argument("--mission", required=True)
    dv.add_argument("--decision", required=True)
    dv.add_argument("--host", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "resolve-transcript":
            out = resolve_from_transcript(a.mission, a.decision, a.transcript)
            print(f"RESOLVED {a.decision} token={out['receipt']['token']} sha={out['receipt']['sha']} "
                  f"recorded={out['recorded']}")
            for r in ([] if a.no_route else route(a.mission, a.decision)):
                print(f"ROUTED consumer={r['consumer']} host={r.get('host')} rc={r['returncode']} {r['stdout']}")
            return 0
        if a.cmd == "consume":
            out = consume_bundle(json.loads(Path(a.file).read_text(encoding="utf-8-sig")), wake=not a.no_wake)
            print(f"CONSUMED {out['receipt']['decision']} sha={out['receipt']['sha']} recorded={out['recorded']} "
                  f"woke={json.dumps(out['woke'], default=str)}")
            return 0
        if a.cmd == "deliver":
            r = deliver(a.mission, a.decision, a.host)
            print(f"DELIVERED rc={r['returncode']} {r['stdout']} {r['stderr']}")
            return 0 if r["returncode"] == 0 else 1
        if a.cmd == "create":
            o = create(a.mission, json.loads(Path(a.file).read_text(encoding="utf-8")))
            print(f"DECISION {o['id']} status={o['status']} problems={o['problems']}")
            return 0 if o["status"] == READY else 3
        if a.cmd == "show":
            print(json.dumps(surface(a.mission, a.decision), indent=2))
            return 0
        out = resolve(a.mission, a.decision, a.choice)
        print(f"RESOLVED {a.decision} token={out['receipt']['token']} sha={out['receipt']['sha']} "
              f"recorded={out['recorded']}")
        return 0
    except DecisionError as e:
        print(f"DECISION REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
