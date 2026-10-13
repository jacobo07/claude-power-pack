#!/usr/bin/env python3
"""Reality set-cover + Owner session compiler (ce-a5 U4).

Input JSON: {"epoch": str, "claims":[{"id", "observations":[obs_id | obs-dict]}],
  "observations":[{obs_id,host,surface,preconditions,est_minutes,owner_needed}],
  "sessions":[{"id","setup_minutes","hosts":[...]|"obs":[...]}]  (optional; default derived),
  "acquired":{obs_id: epoch}, "captured":{obs_id: epoch}}

Model: an observation is acquired ONCE per reality epoch (deduped by obs_id and by
(host,surface,preconditions)) and fans out to every claim that requires it.  Observation
minutes are a fixed cost of the universe; the choice is which sessions (each with a setup
cost) to open.  Weighted set cover over sessions, setup-cost weights, greedy by
setup / newly-covered-observations.  Approximation bound: setup part <= H(m) * OPT_setup,
m = largest session size (H = harmonic number); observation minutes are identical in every
cover, so total <= H(m) * OPT_total.  exhaustive_cover() gives the exact optimum for small inputs.
A claim is never "proven" by planning: status PROVEN only when every observation was captured
in the current epoch; a claim naming an undefined/unschedulable observation stays OPEN.
"""
import itertools, json, sys

DEFAULT_SETUP = 10.0


def _key(o):
    return (o.get("host"), o.get("surface"), tuple(sorted(o.get("preconditions") or [])))


def normalize(spec, dedupe=True):
    """Return (obs: {id: obs}, claim_obs: {claim: [obs ids]}, missing: {claim: [ids]}, alias)."""
    defs = {}
    for o in spec.get("observations", []):
        defs[o["obs_id"]] = o
    claim_obs, missing, alias, instances = {}, {}, {}, {}
    seen_key = {}
    for c in spec.get("claims", []):
        ids = []
        for r in c.get("observations", []):
            if isinstance(r, dict):
                defs.setdefault(r["obs_id"], r)
                r = r["obs_id"]
            if r not in defs:
                missing.setdefault(c["id"], []).append(r)
                continue
            if dedupe:
                k = _key(defs[r])
                rid = seen_key.setdefault(k, r)
                alias[r] = rid
                r = rid
            else:  # mutant: one instance per (claim, obs)
                iid = f"{r}@{c['id']}"
                instances[iid] = dict(defs[r], obs_id=iid)
                r = iid
            ids.append(r)
        claim_obs[c["id"]] = ids
    if dedupe:
        used = {i for v in claim_obs.values() for i in v}
        obs = {i: defs[i] for i in used}
    else:
        obs = instances
    return obs, claim_obs, missing, alias


def derive_sessions(obs, spec):
    if spec.get("sessions"):
        out = []
        for s in spec["sessions"]:
            if "obs" in s:
                members = set(s["obs"])
            else:
                members = {i for i, o in obs.items() if o.get("host") in set(s.get("hosts", []))}
            out.append({"id": s["id"], "setup": float(s.get("setup_minutes", DEFAULT_SETUP)), "obs": members})
        return out
    out = []
    for h in sorted({o.get("host") for o in obs.values()}):
        out.append({"id": f"S-{h}", "setup": DEFAULT_SETUP, "obs": {i for i, o in obs.items() if o.get("host") == h}})
    out.append({"id": "S-all", "setup": DEFAULT_SETUP * 1.5, "obs": set(obs)})
    return out


def _base(i, obs):
    return i.split("@")[0]


def greedy_cover(universe, sessions):
    left, chosen = set(universe), []
    while left:
        best = None
        for s in sessions:
            new = s["obs"] & left
            if not new or s in chosen:
                continue
            ratio = s["setup"] / len(new)
            if best is None or (ratio, s["id"]) < (best[0], best[1]["id"]):
                best = (ratio, s, new)
        if best is None:
            break
        chosen.append(best[1])
        left -= best[2]
    return chosen, left


def exhaustive_cover(universe, sessions):
    best = None
    for r in range(1, len(sessions) + 1):
        for combo in itertools.combinations(sessions, r):
            if set().union(*(s["obs"] for s in combo)) >= set(universe):
                c = sum(s["setup"] for s in combo)
                if best is None or c < best[0]:
                    best = (c, list(combo))
    return best


def harmonic(m):
    return sum(1.0 / k for k in range(1, m + 1))


def compile_plan(spec, dedupe=True):
    epoch = spec.get("epoch", "E0")
    obs, claim_obs, missing, alias = normalize(spec, dedupe)
    acquired = {i for i, e in (spec.get("acquired") or {}).items() if e == epoch}
    captured = {i for i, e in (spec.get("captured") or {}).items() if e == epoch}
    todo = {i for i in obs if _base(i, obs) not in acquired and i not in acquired}
    sessions = derive_sessions(obs, spec)
    chosen, left = greedy_cover(todo, sessions)
    assign, order = {}, []
    for s in chosen:
        mine = sorted((s["obs"] & todo) - set(assign))
        for i in mine:
            assign[i] = s["id"]
    plan = []
    for s in chosen:
        ids = [i for i in assign if assign[i] == s["id"]]
        # order: dependencies (preconditions naming an obs) first, then host/surface
        ids.sort(key=lambda i: (obs[i].get("host") or "", obs[i].get("surface") or "", i))
        ordered, done = [], set()
        def visit(i):
            if i in done or i not in ids:
                return
            done.add(i)
            for p in obs[i].get("preconditions") or []:
                if p in obs:
                    visit(p)
            ordered.append(i)
        for i in ids:
            visit(i)
        owner = [i for i in ordered if obs[i].get("owner_needed")]
        auto = [i for i in ordered if not obs[i].get("owner_needed")]
        steps = [{"kind": "AUTOMATED_PREP", "do": "verify preconditions, stage tooling, start capture",
                  "obs": sorted({p for i in ordered for p in (obs[i].get("preconditions") or []) if p not in obs})}]
        steps += [{"kind": "OWNER", "obs": i, "host": obs[i].get("host"), "surface": obs[i].get("surface"),
                   "minutes": obs[i].get("est_minutes", 0)} for i in owner]
        steps += [{"kind": "AUTOMATED_CAPTURE", "obs": i, "host": obs[i].get("host"),
                   "surface": obs[i].get("surface"), "minutes": obs[i].get("est_minutes", 0)} for i in auto]
        plan.append({"session": s["id"], "setup_minutes": s["setup"], "observations": ordered, "steps": steps,
                     "owner_minutes": s["setup"] + sum(obs[i].get("est_minutes", 0) for i in owner)})
    claims = {}
    for c, ids in claim_obs.items():
        if c in missing:
            claims[c] = {"status": "OPEN", "reason": "MISSING_OBSERVATION", "missing": missing[c]}
        elif any(i in left for i in ids):
            claims[c] = {"status": "OPEN", "reason": "UNSCHEDULABLE_OBSERVATION",
                         "missing": sorted(i for i in ids if i in left)}
        elif ids and all(_base(i, obs) in captured or i in captured for i in ids):
            claims[c] = {"status": "PROVEN", "observations": ids}
        else:
            claims[c] = {"status": "PLANNED", "observations": ids}
    fan = {}
    for c, ids in claim_obs.items():
        for i in ids:
            fan.setdefault(i, []).append(c)
    m = max((len(s["obs"] & todo) for s in sessions), default=0)
    total = sum(p["setup_minutes"] for p in plan) + sum(obs[i].get("est_minutes", 0) for i in todo - left)
    return {"epoch": epoch, "observations_planned": sorted(todo - left), "fanout": fan, "sessions": plan,
            "claims": claims, "total_minutes": total,
            "owner_minutes": sum(p["owner_minutes"] for p in plan),
            "bound": f"greedy setup <= H({m})={harmonic(m):.3f} x optimum setup" if m else "n/a"}


def per_claim_cost(spec):
    """Baseline: every claim acquires its own observations in its own session."""
    obs, claim_obs, missing, _ = normalize(spec, dedupe=False)
    owner = total = n = 0.0
    for c, ids in claim_obs.items():
        if not ids:
            continue
        total += DEFAULT_SETUP + sum(obs[i].get("est_minutes", 0) for i in ids)
        owner += DEFAULT_SETUP + sum(obs[i].get("est_minutes", 0) for i in ids if obs[i].get("owner_needed"))
        n += len(ids)
    return {"observations": int(n), "total_minutes": total, "owner_minutes": owner,
            "sessions": sum(1 for v in claim_obs.values() if v)}


def main(argv):
    spec = json.load(open(argv[1]))
    out = compile_plan(spec)
    out["per_claim_baseline"] = per_claim_cost(spec)
    print(json.dumps(out, indent=1, default=sorted))


if __name__ == "__main__":
    main(sys.argv)
