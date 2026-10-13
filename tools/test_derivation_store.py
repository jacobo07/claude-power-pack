"""CDC C6 gates: derivation store + research_reuse hook (hit, miss, stale, in-flight, abandoned lock, kill switch).

Mutation drill: each deny predicate is disabled in a throwaway copy of the hook; its test must turn RED.
Two-session proof: PROOF_OUT=<path> writes both jsonl rows (session A stores, session B is served).
All hook runs are synchronous subprocesses: the hook starts no detached effect.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import derivation_store as ds  # noqa: E402

HOOK = PP / "hooks" / "research_reuse.js"
NODE = os.environ.get("NODE_BIN") or "node"
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def hook(state, sid, tool, inp, post=None, hook=HOOK, env_extra=None):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state))
    for k in ("CPP_RESEARCH_GATE", "CPP_RESEARCH_LOCK_S", "CPP_RESEARCH_NEG_FILES", "CPP_GOAL"):
        env.pop(k, None)
    env.update(env_extra or {})
    ev = {"session_id": sid, "hook_event_name": "PostToolUse" if post is not None else "PreToolUse",
          "tool_name": tool, "cwd": str(state), "tool_input": inp}
    if post is not None:
        ev["tool_response"] = post
    p = subprocess.run([NODE, str(hook)], input=json.dumps(ev), capture_output=True, text=True, env=env, timeout=60)
    try:
        out = json.loads(p.stdout or "{}")
    except ValueError:
        out = {}
    d = out.get("hookSpecificOutput", {})
    return d.get("permissionDecision") == "deny", d.get("permissionDecisionReason", "") or d.get("additionalContext", ""), out


def bind(state, sid):
    (Path(state) / "cognitive-unit").mkdir(parents=True, exist_ok=True)
    (Path(state) / "cognitive-unit" / f"{sid}.json").write_text(json.dumps({"unit": "u", "route": "r"}), encoding="utf-8")


def mutant(tmp, name, old, new):
    src = HOOK.read_text(encoding="utf-8")
    assert old in src, name
    src = src.replace(old, new).replace("require('./lib/goal_binding')", f"require({json.dumps(str(PP / 'hooks' / 'lib' / 'goal_binding'))})")
    p = Path(tmp) / f"mut_{name}.js"
    p.write_text(src, encoding="utf-8")
    return p


def main():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(t / "py")
        # ---- python store API
        dep = t / "dep.txt"
        dep.write_text("v1", encoding="utf-8")
        check("store-key-normalised", ds.make_key("  Hello   WORLD ", "s") == ds.make_key("hello world", "s"), "whitespace/case")
        check("store-miss", ds.get("q", "s", [str(dep)]) is None, "empty store")
        r = ds.complete("q", "s", [str(dep)], "answer", "prov", ttl_s=3600)
        check("store-hit", (ds.get("q", "s", [str(dep)]) or {}).get("key") == r["key"], "fresh + deps unchanged")
        dep.write_text("v2", encoding="utf-8")
        check("store-stale-dep-miss", ds.get("q", "s", [str(dep)]) is None, "dep changed -> miss")
        dep.write_text("v1", encoding="utf-8")
        check("store-ttl-expired", ds.get("q", "s", [str(dep)], now=time.time() + 7200) is None, "ttl 3600 < 7200")
        who, k = ds.begin("lq", "s", owner="A")
        who2, lk = ds.begin("lq", "s", owner="B")
        check("store-singleflight", who == "owner" and who2 == "subscribe" and lk.get("owner") == "A", f"{who}/{who2}")
        who3, _ = ds.begin("lq", "s", owner="C", now=time.time() + ds.LOCK_STALE_S + 5)
        check("store-abandoned-lock-recovery", who3 == "owner", "lock stale after 30 min -> recovered")
        ds.abandon("lq", "s")
        check("store-abandon", ds.begin("lq", "s", owner="D")[0] == "owner", "abandon frees the lock")
        # ---- key parity python <-> node
        kn = subprocess.run([NODE, "-e", f"console.log(require({json.dumps(str(HOOK))}).keyOf('search: Foo  Bar'))"],
                            capture_output=True, text=True).stdout.strip()
        check("key-parity-py-js", kn == ds.make_key("search: foo bar", "research"), kn[:12])

        # ---- hook
        s = t / "hs"
        s.mkdir()
        q = {"query": "how does bun jsc gc release memory"}
        d, msg, _ = hook(s, "A", "WebSearch", q)
        check("hook-miss-allows", not d and "NEGATIVE" not in msg, "miss -> allow, lock taken")
        d, msg, _ = hook(s, "B", "WebSearch", q)
        check("hook-inflight-subscribe", d and "subscribe:" in msg and ".lock" in msg, msg[:90])
        d, msg, _ = hook(s, "A", "WebSearch", q)
        check("hook-inflight-same-sid-allows", not d, "own lock does not block")
        hook(s, "A", "WebSearch", q, post={"results": ["x" * 50]})
        k = ds.make_key("search: " + q["query"], "research")
        check("hook-post-stores", (s / "derivation-store" / f"{k}.json").exists() and not (s / "derivation-store" / f"{k}.lock").exists(), "record, lock dropped")
        d, msg, _ = hook(s, "B", "WebSearch", q)
        check("hook-hit-unbound-advisory", not d and "answers" in msg, "unbound -> context only")
        bind(s, "B")
        d, msg, _ = hook(s, "B", "WebSearch", q)
        check("hook-hit-bound-denies", d and "answers" in msg, msg[:90])
        d, msg, _ = hook(s, "B", "WebSearch", q, env_extra={"CPP_RESEARCH_GATE": "off"})
        check("hook-kill-switch", not d and msg == "", "CPP_RESEARCH_GATE=off")
        d, _, _ = hook(s, "B", "WebSearch", {"query": "something else entirely new"})
        check("hook-other-query-miss", not d, "different question")
        # fetch key includes url
        hook(s, "A", "WebFetch", {"url": "https://x.test/a", "prompt": "p"}, post="body text")
        bind(s, "A")
        d, _, _ = hook(s, "A", "WebFetch", {"url": "https://x.test/a", "prompt": "p"})
        check("hook-fetch-hit", d, "same url+prompt")
        # stale lock window
        s2 = t / "hs2"
        hook(s2, "A", "WebSearch", {"query": "stale lock question here"})
        d, _, _ = hook(s2, "B", "WebSearch", {"query": "stale lock question here"}, env_extra={"CPP_RESEARCH_LOCK_S": "0"})
        time.sleep(0)  # lock_s=0 and ts<now -> stale
        check("hook-abandoned-lock-recovers", not d, "stale lock taken over")
        # negative knowledge
        neg = t / "neg.md"
        neg.write_text("- TRAP-9 quantum flux capacitor retrofit options dead end. Reopen when the vendor ships firmware 3.\n", encoding="utf-8")
        d, msg, _ = hook(s2, "A", "WebSearch", {"query": "quantum flux capacitor retrofit options"}, env_extra={"CPP_RESEARCH_NEG_FILES": str(neg)})
        check("hook-negative-knowledge", not d and "NEGATIVE KNOWLEDGE" in msg and "firmware 3" in msg, msg[:120])
        # fail open on garbage
        p = subprocess.run([NODE, str(HOOK)], input="{not json", capture_output=True, text=True)
        check("hook-fail-open", p.stdout.strip() == "{}" and p.returncode == 0, "garbage stdin")

        # ---- mutation drill: every deny predicate disabled must turn its test red
        s3 = t / "hs3"
        m1 = mutant(t, "nodeny_bound", "return bound(ev, sid) ? deny(", "return false ? deny(")
        hook(s3, "A", "WebSearch", q, hook=m1)
        hook(s3, "A", "WebSearch", q, post="r" * 20, hook=m1)
        bind(s3, "B")
        d, _, _ = hook(s3, "B", "WebSearch", q, hook=m1)
        check("mutant-bound-deny-red", not d, "mutant lets the duplicate through (control test would FAIL)")
        m2 = mutant(t, "noinflight", "if (cur && cur.owner !== sid) return deny(", "if (false) return deny(")
        s4 = t / "hs4"
        hook(s4, "A", "WebSearch", q, hook=m2)
        d, _, _ = hook(s4, "B", "WebSearch", q, hook=m2)
        check("mutant-inflight-red", not d, "mutant has no subscribe deny")
        m3 = mutant(t, "nokill", "if (off() || !ev) return null;", "if (!ev) return null;")
        d, msg, _ = hook(s3, "B", "WebSearch", q, hook=m3, env_extra={"CPP_RESEARCH_GATE": "off"})
        check("mutant-kill-switch-red", d, "mutant ignores the kill switch")

        # ---- proof: two sessions, same research question
        out = os.environ.get("PROOF_OUT")
        if out:
            sp = t / "proof"
            pq = {"query": "does the bun runtime release rss after gc"}
            rows = []
            d1, m1_, _ = hook(sp, "sess-A", "WebSearch", pq)
            rows.append({"session": "sess-A", "phase": "ask", "deny": d1, "msg": m1_})
            hook(sp, "sess-A", "WebSearch", pq, post={"results": ["rss is not returned to the OS"]})
            rows.append({"session": "sess-A", "phase": "stored"})
            bind(sp, "sess-B")
            d2, m2_, _ = hook(sp, "sess-B", "WebSearch", pq)
            ans = ""
            kk = ds.make_key("search: " + pq["query"], "research")
            ap = sp / "derivation-store" / "answers" / f"{kk}.txt"
            ans = ap.read_text(encoding="utf-8") if ap.exists() else ""
            rows.append({"session": "sess-B", "phase": "ask", "deny": d2, "msg": m2_, "served_answer": ans})
            Path(out).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            check("proof-second-session-served", (not d1) and d2 and "rss is not returned" in ans, "rows written")

    print(f"{passes} pass / {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
