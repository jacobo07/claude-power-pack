"""Hook registration integrity gate (incident 2026-09-16 20:02 -> 2026-09-18 13:55).

An ad-hoc exec-form rewrite of ~/.claude/settings.json kept `args: [hook-dispatcher.js]`
and dropped `--event=<chain>` from all six dispatcher registrations. The dispatcher then
answered `{}` / exit 0, which the harness reads as "every hook passed", and the secret
firewall, bash guard, Stop chain and UserPromptSubmit chain were off for ~42 h while
every existing suite stayed green -- none of them had the live registry as its subject.

This gate judges REGISTRATIONS, not hooks:
  * every dispatcher registration carries a routing identity naming a real chain;
  * matcher <-> chain pairing agrees with the dispatcher's own NO_EVENT_ROUTES table;
  * the security-critical chains are all registered, once each;
  * argv tails that other hooks need (research-domain-guard --event=pre/post) survive;
  * the dispatcher refuses to answer a no-event call with success-shaped silence.

Usage:
  python tools/test_hook_registration_integrity.py            # red/green drills + runtime
  python tools/test_hook_registration_integrity.py --live     # ALSO judge ~/.claude/settings.json
  python tools/test_hook_registration_integrity.py --live-only --settings <path>
Exit 0 = all PASS. Exit 1 = a FAIL. Exit 3 = could not judge (unreadable input).
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# HOOKREG_DISPATCHER lets the mutation drill point the gate at a pre-fix dispatcher copy.
DISPATCHER = Path(os.environ.get("HOOKREG_DISPATCHER") or REPO / "hooks" / "hook-dispatcher.js")
# HOOKREG_SETTINGS lets the launcher drill judge a fixture instead of the live registry.
LIVE_SETTINGS = Path(os.environ.get("HOOKREG_SETTINGS") or Path.home() / ".claude" / "settings.json")
NODE = r"C:\Program Files\nodejs\node.exe" if os.name == "nt" else "node"

# Registrations whose chains are security- or recovery-critical: absence is RED.
REQUIRED_CHAINS = {
    "PreToolUse-Bash-chain", "PreToolUse-Edit-chain", "PreToolUse-Read-chain",
    "PostToolUse-default", "Stop-chain", "UserPromptSubmit-chain",
}
# Non-dispatcher hooks whose argv tail is load-bearing: (event, script basename) -> required arg.
REQUIRED_TAILS = {
    ("PreToolUse", "research-domain-guard.js"): "--event=pre",
    ("PostToolUse", "research-domain-guard.js"): "--event=post",
}

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def argv_of(h: dict) -> list[str]:
    """Canonical argv for either registration shape (shell string or exec form)."""
    if h.get("args") is not None:
        return [str(h.get("command", ""))] + [str(a) for a in h["args"]]
    return [t.strip('"') for t in re.findall(r'"[^"]*"|\S+', str(h.get("command", "")))]


def dispatcher_meta() -> dict:
    code = ("const d=require(process.argv[1]);process.stdout.write(JSON.stringify("
            "{routes:d.NO_EVENT_ROUTES,chains:d.CHAIN_NAMES,events:d.EVENT_NAMES}))")
    p = subprocess.run([NODE, "-e", code, str(DISPATCHER)], capture_output=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError(f"cannot load dispatcher exports: {p.stderr.decode(errors='replace')[:300]}")
    return json.loads(p.stdout)


def judge(settings: dict, meta: dict) -> list[str]:
    """Return the list of violations for a settings document (empty = valid)."""
    bad: list[str] = []
    known = set(meta["chains"]) | set(meta["events"])
    route_of = {}
    for r in meta["routes"]:
        route_of[r["chain"]] = (r["hook"], None if r["tools"] is None else set(r["tools"]))
    seen: dict[str, int] = {}
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return ["settings has no hooks object"]
    for ev, groups in hooks.items():
        for g in groups or []:
            matcher = g.get("matcher")
            for h in g.get("hooks") or []:
                argv = argv_of(h)
                joined = " ".join(argv)
                if "hook-dispatcher.js" in joined:
                    target = next((a for a in argv if a.endswith("hook-dispatcher.js")), None)
                    if target and not Path(os.path.expanduser(target)).exists():
                        bad.append(f"{ev}|{matcher}: dispatcher target missing: {target}")
                    evs = [a.split("=", 1)[1] for a in argv if a.startswith("--event=")]
                    if not evs:
                        bad.append(f"{ev}|{matcher}: dispatcher registration has NO --event= (routing identity lost)")
                        continue
                    chain = evs[0]
                    if chain not in known:
                        bad.append(f"{ev}|{matcher}: --event={chain} names no dispatcher chain")
                        continue
                    seen[chain] = seen.get(chain, 0) + 1
                    if chain in route_of:
                        want_hook, want_tools = route_of[chain]
                        got_tools = None if not matcher or matcher == "*" else set(matcher.split("|"))
                        if want_hook != ev or want_tools != got_tools:
                            bad.append(f"{ev}|{matcher}: pairing disagrees with NO_EVENT_ROUTES for {chain} "
                                       f"(expects {want_hook}|{'|'.join(sorted(want_tools)) if want_tools else None})")
                for (rev, script), tail in REQUIRED_TAILS.items():
                    if ev == rev and script in joined and tail not in argv:
                        bad.append(f"{ev}|{matcher}: {script} lost required arg {tail}")
    for c in sorted(REQUIRED_CHAINS):
        n = seen.get(c, 0)
        if n == 0:
            bad.append(f"required chain {c} is not registered")
        elif n > 1:
            bad.append(f"chain {c} registered {n} times (duplicate)")
    return bad


# ---------------------------------------------------------------- fixtures
def _dispatcher_hooks(d: dict):
    for ev, groups in d["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                if "hook-dispatcher.js" in " ".join(argv_of(h)):
                    yield ev, g, h


def incident_transform(d: dict) -> dict:
    """The exact lossy regex from session 2174d82b: keep only the quoted/first .js path."""
    d = copy.deepcopy(d)
    for ev, groups in d["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                argv = argv_of(h)
                js = next((a for a in argv if a.endswith((".js", ".cjs"))), None)
                if js and argv[0].lower().endswith("node.exe"):
                    h["command"], h["args"] = argv[0], [js]
    return d


def canonical(base: dict, meta: dict) -> dict:
    """The canonical registration set, rebuilt from the dispatcher's own table onto the REAL
    settings schema. A registration whose own --event names a known chain that NO_EVENT_ROUTES
    does not list (e.g. SessionStart-chain, which only ever routes by its explicit --event) keeps
    that chain. Every other registration is rebuilt from the route for its (event, matcher), so a
    routed chain is never trusted from disk. A bare next() here raised StopIteration on the live
    registry, which carries SessionStart-chain (2026-10-10)."""
    good = copy.deepcopy(base)
    routed = {r["chain"] for r in meta["routes"]}
    for ev, g, h in list(_dispatcher_hooks(good)):
        m = g.get("matcher")
        own = [a.split("=", 1)[1] for a in argv_of(h) if a.startswith("--event=")]
        if own and own[0] in meta["chains"] and own[0] not in routed:
            chain = own[0]
        else:
            r = next((r for r in meta["routes"] if r["hook"] == ev and
                      (r["tools"] is None) == (not m or m == "*") and
                      (r["tools"] is None or set(r["tools"]) == set(str(m).split("|")))), None)
            chain = r["chain"] if r else None
        if chain is None:
            continue   # left as found: judge() names it (no --event), the gate goes red, nothing crashes
        h["command"] = NODE.replace("\\", "/")
        # The registration target is the LIVE dispatcher path, independent of HOOKREG_DISPATCHER
        # (which only swaps the implementation the runtime drills execute).
        h["args"] = [str(Path.home() / ".claude" / "hooks" / "hook-dispatcher.js").replace("\\", "/"),
                     f"--event={chain}"]
    for ev, groups in good["hooks"].items():
        for gg in groups:
            for h in gg["hooks"]:
                for (rev, script), tail in REQUIRED_TAILS.items():
                    if ev == rev and script in " ".join(argv_of(h)) and tail not in argv_of(h):
                        h.setdefault("args", [])
                        h["args"].append(tail)
    return good


def mutate(d: dict, fn) -> dict:
    d = copy.deepcopy(d)
    fn(d)
    return d


def main() -> int:
    live = "--live" in sys.argv or "--live-only" in sys.argv
    live_only = "--live-only" in sys.argv
    sp = LIVE_SETTINGS
    if "--settings" in sys.argv:
        sp = Path(sys.argv[sys.argv.index("--settings") + 1])
    try:
        meta = dispatcher_meta()
        base = json.loads(sp.read_text(encoding="utf-8-sig"))
    except Exception as e:  # verifier failure outranks any subject verdict
        print(f"UNJUDGEABLE: {e}")
        return 3

    if not live_only:
        # Positive control: the canonical registration set, rebuilt from the dispatcher's own
        # table onto the REAL settings schema, must pass. Built, not trusted from disk.
        good = canonical(base, meta)
        v = judge(good, meta)
        (_ok if not v else _fail)("V-HOOKREG-KNOWN-GOOD", "canonical set passes" if not v else "; ".join(v))
        # Regression (2026-10-10): a registration that routes only by its explicit --event (a chain the
        # dispatcher knows but NO_EVENT_ROUTES does not list) crashed the builder with StopIteration.
        # The drill chain must be the live shape: its event has NO matcher-free route, so no fallback
        # can stand in for it (review 2026-10-10: PostToolUse-Bash-chain under PostToolUse matched
        # the PostToolUse-default route, its own chain was overwritten, and the gate passed vacuously).
        free = {r["hook"] for r in meta["routes"] if r["tools"] is None}
        unrouted = sorted(c for c in set(meta["chains"]) - {r["chain"] for r in meta["routes"]}
                          if c.split("-")[0] not in free)
        if not unrouted:
            _fail("V-HOOKREG-UNROUTED-EVENT", "the dispatcher lists no unrouted chain on an event without a fallback")
        else:
            doc = copy.deepcopy(base)
            ch = unrouted[0]
            doc["hooks"].setdefault(ch.split("-")[0], []).append({"hooks": [{"type": "command", "command": NODE,
                "args": [str(Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"), f"--event={ch}"]}]})
            try:
                built = canonical(doc, meta)
                kept = any(f"--event={ch}" in argv_of(h) for _, _, h in _dispatcher_hooks(built))
                vv = [x for x in judge(built, meta) if ch in x]
                (_ok if kept and not vv else _fail)(
                    "V-HOOKREG-UNROUTED-EVENT",
                    f"{ch} kept its own --event, judged valid" if kept and not vv
                    else f"--event={ch} kept={kept}; {'; '.join(vv) or 'no violation'}")
            except StopIteration:
                _fail("V-HOOKREG-UNROUTED-EVENT", f"builder crashed on {ch} (StopIteration)")
        n_disp = sum(1 for _ in _dispatcher_hooks(good))
        (_ok if n_disp >= 6 else _fail)("V-HOOKREG-POPULATION-FLOOR", f"{n_disp} dispatcher registrations found (floor 6)")

        def red(gate, doc, needle):
            vv = judge(doc, meta)
            hit = [x for x in vv if needle in x]
            (_ok if hit else _fail)(gate, hit[0] if hit else f"expected '{needle}', got {vv or 'NO VIOLATION'}")

        red("V-HOOKREG-INCIDENT-SHAPE", incident_transform(good), "NO --event=")
        red("V-HOOKREG-INCIDENT-TAIL", incident_transform(good), "lost required arg --event=pre")

        def wrong_event(d):
            for _, _, h in _dispatcher_hooks(d):
                h["args"] = [a if not a.startswith("--event=") else "--event=Nope-chain" for a in h["args"]]
                break
        red("V-HOOKREG-WRONG-EVENT", mutate(good, wrong_event), "names no dispatcher chain")

        def swap_pair(d):
            for _, _, h in _dispatcher_hooks(d):
                if "--event=PreToolUse-Bash-chain" in h["args"]:
                    h["args"] = [a.replace("Bash-chain", "Read-chain") for a in h["args"]]
        red("V-HOOKREG-MATCHER-MISMATCH", mutate(good, swap_pair), "pairing disagrees")

        def drop_chain(name):
            def f(d):
                for ev, groups in d["hooks"].items():
                    for g in groups:
                        g["hooks"] = [h for h in g["hooks"] if f"--event={name}" not in argv_of(h)]
            return f
        red("V-HOOKREG-SECURITY-ABSENT", mutate(good, drop_chain("PreToolUse-Edit-chain")), "PreToolUse-Edit-chain is not registered")
        red("V-HOOKREG-STOP-ABSENT", mutate(good, drop_chain("Stop-chain")), "Stop-chain is not registered")
        red("V-HOOKREG-UPS-ABSENT", mutate(good, drop_chain("UserPromptSubmit-chain")), "UserPromptSubmit-chain is not registered")

        def bad_target(d):
            for _, _, h in _dispatcher_hooks(d):
                h["args"][0] = "C:/nowhere/hook-dispatcher.js"
                break
        red("V-HOOKREG-TARGET-MISSING", mutate(good, bad_target), "dispatcher target missing")

        def shell_form_without_event(d):  # the OTHER shape must be judged too
            for _, _, h in _dispatcher_hooks(d):
                h.pop("args", None)
                h["command"] = f'"{NODE}" "{Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"}"'
                break
        red("V-HOOKREG-SHELLFORM-NO-EVENT", mutate(good, shell_form_without_event), "NO --event=")

        # ---- runtime: the dispatcher itself must not answer a no-event call with silence
        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ, CLAUDE_STATE_DIR=td)
            probe = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Glob", "session_id": "hookreg-drill",
                                "cwd": td, "tool_input": {"pattern": "*.nothing"}})
            p = subprocess.run([NODE, str(DISPATCHER)], input=probe.encode(), capture_output=True, env=env, timeout=60)
            out = p.stdout.decode(errors="replace").strip()
            silent_pass = p.returncode == 0 and out in ("", "{}")
            (_fail if silent_pass else _ok)("V-HOOKREG-NOEVENT-NOT-SILENT",
                                           f"rc={p.returncode} stdout={out[:60]!r} stderr={p.stderr.decode(errors='replace')[:90]!r}")
            receipt = Path(td) / "dispatcher-no-event.jsonl"
            rec = receipt.read_text(encoding="utf-8").strip().splitlines() if receipt.exists() else []
            (_ok if rec else _fail)("V-HOOKREG-NOEVENT-RECEIPT-ISOLATED",
                                   f"receipt in CLAUDE_STATE_DIR: {rec[-1][:120] if rec else 'ABSENT'}")

        # ---- routing table: payload -> chain is total and unambiguous for the six routes
        code = ("const d=require(process.argv[1]);const c=[['PreToolUse','Bash'],['PreToolUse','PowerShell'],"
                "['PreToolUse','Write'],['PreToolUse','NotebookEdit'],['PreToolUse','Grep'],['PostToolUse','Read'],"
                "['Stop',undefined],['UserPromptSubmit',undefined],['PreToolUse','Glob']];"
                "process.stdout.write(JSON.stringify(c.map(([h,t])=>d.deriveEventFromPayload({hook_event_name:h,tool_name:t}))))")
        got = json.loads(subprocess.run([NODE, "-e", code, str(DISPATCHER)], capture_output=True, timeout=60).stdout)
        want = ["PreToolUse-Bash-chain", "PreToolUse-Bash-chain", "PreToolUse-Edit-chain", "PreToolUse-Edit-chain",
                "PreToolUse-Read-chain", "PostToolUse-default", "Stop-chain", "UserPromptSubmit-chain", None]
        (_ok if got == want else _fail)("V-HOOKREG-DERIVE-ROUTES", f"got {got}")

    if live:
        v = judge(base, meta)
        (_ok if not v else _fail)(f"V-HOOKREG-LIVE[{sp.name}]", "all registrations valid" if not v else " || ".join(v))

    print(f"HOOKREG_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
