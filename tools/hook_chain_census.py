# -*- coding: utf-8 -*-
"""Hook-chain census -- the load-INDEPENDENT half of the latency baseline.

Why counts and not milliseconds. A wall-clock reading taken on a contended host
is not a measurement: this estate has recorded a 17x drift on identical payloads,
and the reading that forced this tool was taken at 4.7 % free RAM. A count of
chain members, its declared concurrency and its deadline cannot drift with load,
they come back the same on a quiet host, and they are what actually predicts the
deadline cliff -- a chain is killed when SUM (or SUM/concurrency) crosses its
budget, and whatever has not flushed is lost silently.

So this records, before UCR-CIF adds anything:

    per chain:  members  concurrency  deadline  settings-timeout  headroom class

`headroom` is the structural question a timing run cannot answer on a busy host:
how many MORE members can this chain take before its own budget is at risk, at
the per-hook cost the chain is already assumed to carry.

Four separate claims are kept separate, because collapsing them is how a gate
that never runs looks exactly like a gate that passes:

    DEFINED    -- the script is named in the dispatcher's chain map
    ON_DISK    -- that file exists
    REGISTERED -- settings.json routes the event to the dispatcher
    (EFFECTIVE is deliberately NOT claimed here; only a driven payload shows it)

Exit 2 on instrument failure -- an unparsable dispatcher must not read as an
empty estate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HOME_HOOKS = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
DISPATCHER = os.path.join(HOME_HOOKS, "hook-dispatcher.js")

MIN_CHAINS = 3          # floor: a dispatcher with fewer chains means parsing broke
MIN_MEMBERS = 10        # floor: total members across all chains


def strip_comments(src: str) -> str:
    """Remove // and /* */ so commented-out members are not counted as live."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in src.split("\n"))


def block_after(src: str, anchor: str) -> str:
    """Return the balanced {...} block that follows `anchor`."""
    i = src.find(anchor)
    if i < 0:
        return ""
    j = src.find("{", i)
    if j < 0:
        return ""
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1]
        k += 1
    return ""


def parse_chain_map(src: str):
    """chain name -> [script filenames], from the CHAIN_MAP object literal."""
    blob = block_after(src, "const CHAIN_MAP")
    if not blob:
        return {}
    chains, pos = {}, 0
    # each entry:  'Name-chain': [ ... ]
    for m in re.finditer(r"['\"]([A-Za-z0-9_.-]+(?:-chain|-default))['\"]\s*:\s*\[", blob):
        name = m.group(1)
        start = m.end() - 1
        depth, k = 0, start
        while k < len(blob):
            if blob[k] == "[":
                depth += 1
            elif blob[k] == "]":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        body = blob[start:k + 1]
        # Keep the member's FULL spelling. A chain member is written relative to
        # the dispatcher's own directory ('../skills/.../hooks/x.js',
        # './tests/fixtures/y.js'); reducing it to a basename and looking in one
        # flat directory reports a live hook as missing. That happened twice while
        # building this tool -- once nearly reporting HR-SECRET-001 unenforced --
        # so resolution now mirrors the dispatcher instead of guessing a location.
        scripts = re.findall(r"['\"](\.{0,2}[A-Za-z0-9_./-]*\.(?:js|py|ps1|cjs|mjs))['\"]", body)
        seen, ordered = set(), []
        for s in scripts:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        chains[name] = ordered
        pos = k
    return chains


def parse_num_map(src: str, anchor: str):
    blob = block_after(src, anchor)
    out = {}
    for m in re.finditer(r"['\"]([A-Za-z0-9_.-]+)['\"]\s*:\s*(\d+)", blob):
        out[m.group(1)] = int(m.group(2))
    return out


def parse_settings():
    """event -> {matchers, timeouts, routes_to_dispatcher}"""
    if not os.path.exists(SETTINGS):
        return {}, "settings.json ABSENT"
    try:
        raw = open(SETTINGS, encoding="utf-8-sig").read()
        cfg = json.loads(raw)
    except Exception as e:
        return {}, "settings.json UNREADABLE: %s" % type(e).__name__
    out = {}
    for event, entries in (cfg.get("hooks") or {}).items():
        timeouts, disp, n = [], False, 0
        for entry in entries or []:
            for h in (entry.get("hooks") or []):
                n += 1
                if h.get("timeout") is not None:
                    timeouts.append(h["timeout"])
                if "hook-dispatcher" in json.dumps(h):
                    disp = True
        out[event] = {"handlers": n, "timeouts": sorted(set(timeouts)),
                      "routes_to_dispatcher": disp}
    return out, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    if not os.path.exists(DISPATCHER):
        print("CONTROL_FAIL dispatcher absent at %s" % DISPATCHER)
        return 2
    src = strip_comments(open(DISPATCHER, encoding="utf-8", errors="replace").read())

    chains = parse_chain_map(src)
    conc = parse_num_map(src, "const CHAIN_CONCURRENCY")
    dead = parse_num_map(src, "const CHAIN_DEADLINE_MS")
    settings, serr = parse_settings()

    total_members = sum(len(v) for v in chains.values())
    print("=== CONTROLS ===")
    print("dispatcher_bytes=%d  chains_parsed=%d  total_members=%d"
          % (os.path.getsize(DISPATCHER), len(chains), total_members))
    if serr:
        print("settings: %s" % serr)
    ok = True
    if len(chains) < MIN_CHAINS:
        print("CONTROL_FAIL chain floor: %d < %d -- the parser probably broke"
              % (len(chains), MIN_CHAINS))
        ok = False
    if total_members < MIN_MEMBERS:
        print("CONTROL_FAIL member floor: %d < %d" % (total_members, MIN_MEMBERS))
        ok = False
    print("CONTROLS=%s" % ("PASS" if ok else "FAIL"))

    print("\n=== CHAIN CENSUS (load-independent baseline) ===")
    print("%-26s %7s %6s %9s %9s  %s" % ("CHAIN", "MEMBERS", "CONC", "DEADLINE", "MISSING", "BUDGET"))
    rows = []
    for name in sorted(chains):
        members = chains[name]
        missing = [m for m in members
                   if not os.path.exists(os.path.join(HOME_HOOKS, m))]
        c = conc.get(name, 0)
        d = dead.get(name, 0)
        # structural headroom: with a deadline, lanes = conc or 1; budget is per lane
        if d:
            lanes = c if c else 1
            budget = "deadline %dms over %d lane(s)" % (d, lanes)
        else:
            budget = "NO DEADLINE -- waits for everything"
        rows.append({"chain": name, "members": members, "member_count": len(members),
                     "concurrency": c, "deadline_ms": d, "missing_on_disk": missing})
        print("%-26s %7d %6s %9s %9d  %s"
              % (name[:26], len(members), c or "-", d or "-", len(missing), budget))

    print("\n=== SETTINGS ROUTING (REGISTERED, which is not LOADED and not EFFECTIVE) ===")
    for event in sorted(settings):
        s = settings[event]
        print("  %-22s handlers=%-3d timeouts=%-14s dispatcher=%s"
              % (event, s["handlers"], ",".join(map(str, s["timeouts"])) or "-",
                 s["routes_to_dispatcher"]))

    missing_any = [(r["chain"], m) for r in rows for m in r["missing_on_disk"]]
    if missing_any:
        print("\n--- DEFINED BUT NOT ON DISK (a chain member that cannot run) ---")
        for ch, m in missing_any:
            print("  %s :: %s" % (ch, m))
    else:
        print("\nEvery defined chain member exists on disk.")

    nodead = [r["chain"] for r in rows if not r["deadline_ms"]]
    if nodead:
        print("\nChains with NO deadline (a slow member can hold the whole chain): %s"
              % ", ".join(nodead))

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        json.dump({"controls_pass": ok, "chains": rows, "settings": settings,
                   "total_members": total_members,
                   "timing_baseline": "UNMEASURED -- host at 4.7% free RAM when captured; "
                                      "a wall-clock reading under contention is not a measurement"},
                  open(args.json_out, "w", encoding="utf-8"), indent=2)
        print("\nwrote %s" % args.json_out)

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
