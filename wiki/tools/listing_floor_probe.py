"""Listing-floor probe (K3/K4, vault/plans/skill-virtualization-k-slice-2026-10-03.md).

Runs ONE fresh headless session and reports what the model actually received and did:
  startup_tokens  input + cache_creation + cache_read of the FIRST model call (model-visible, not chars)
  listing         chars / entries / described entries of the initial skill_listing attachment
  watch           per named skill: absent | name-only | described (n chars)
  loads           Skill tool_use names and Read paths ending in SKILL.md (page loads)
  layers          chars of the startup window per floor class (tools/floor_regression_gate.py classify)
Appends one JSON row to listing_floor_probe.results.jsonl (or --out). Spawns `claude -p`; costs one session.

  python listing_floor_probe.py --label champion-1 --prompt "Reply with the single word OK."
  python listing_floor_probe.py --label r2 --settings-file s.json --watch a,b --prompt "..." --max-turns 1

--pair (S1 floor decomposition, 2026-10-07): runs the same minimal session twice, ON (normal surfaces) and OFF
(--off-settings passed as --settings, plus --off-env K=V kill switches; never an edit of settings.json or ~/.claude),
and attributes host_forced = OFF tokens, cpp_added = ON - OFF. Anything that makes the OFF reading untrustworthy is
UNDECIDED with a reason and cpp_added None, never 0. Costs two sessions.

  python listing_floor_probe.py --label s1 --prompt "Reply with the single word OK." --pair --off-settings off.json
"""
import argparse, glob, json, os, subprocess, sys, time

CLAUDE = r"C:\Users\User\.local\bin\claude.exe"
MODEL = "claude-opus-5-5"
REPO = os.path.expanduser("~/.claude/skills/claude-power-pack")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listing_floor_probe.results.jsonl")
GATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")

# Floor classes a CPP install can change (each carries harness built-ins too: a listing holds built-in skills).
CONTROLLABLE = ("hooks", "memory_global", "memory_project", "rules", "skill_listing", "agent_listing",
                "other_instructions")


def transcript(sid):
    for _ in range(20):                      # the transcript is flushed by the child; allow a short delay
        hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
        if hits:
            return hits[0]
        time.sleep(0.5)
    return None


def analyse(path, watch):
    listing, first_usage, loads = None, None, []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        a = d.get("attachment") or {}
        if listing is None and a.get("type") == "skill_listing" and a.get("isInitial"):
            listing = a.get("content") or ""
        msg = d.get("message") or {}
        if d.get("type") == "assistant" and first_usage is None and msg.get("usage"):
            u = msg["usage"]
            first_usage = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) \
                + (u.get("cache_read_input_tokens") or 0)
        for b in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                i = b.get("input") or {}
                if b.get("name") == "Skill":
                    loads.append("skill:" + str(i.get("skill")))
                elif b.get("name") == "Read" and str(i.get("file_path", "")).replace("\\", "/").endswith("SKILL.md"):
                    loads.append("read:" + str(i.get("file_path")))
    row = {"startup_tokens": first_usage, "loads": loads}
    if listing is None:
        row["listing"] = "UNMEASURED (no initial skill_listing in transcript)"
        return row
    entries = {}
    for ln in listing.splitlines():
        if ln.startswith("- "):
            n, _, desc = ln[2:].partition(":")
            entries[n.strip()] = desc.strip()
    row["listing"] = {"chars": len(listing), "entries": len(entries), "described": sum(1 for v in entries.values() if v)}
    row["watch"] = {w: ("absent" if w not in entries else (f"described ({len(entries[w])})" if entries[w] else "name-only"))
                    for w in watch}
    return row


# --------------------------------------------------------------------------- floor decomposition (S1)
def layer_class(layer):
    if layer.startswith(("hook_context:", "hook_system_message:")):
        return "hooks"
    if layer in ("memory_global", "memory_project", "rules", "skill_listing", "system_prompt"):
        return layer
    if layer == "other:agent_listing_delta":
        return "agent_listing"
    if layer == "other:instructions":
        return "other_instructions"
    return "harness_other"


def _gate():
    if GATE_DIR not in sys.path:
        sys.path.insert(0, GATE_DIR)
    import floor_regression_gate as g
    return g


def decompose(path):
    """-> {class: chars} of the startup window (the gate's own window reader and classifier), or
    {"unmeasured": reason}. Absent is never an empty dict: an empty dict would read as a zero floor."""
    g = _gate()
    try:
        rows, _assistant, _raw = g.read_window(path)
    except g.Unmeasurable as exc:
        return {"unmeasured": exc.reason}
    comps, _excluded, _digest = g.classify(rows)
    out = {}
    for c in comps:
        k = layer_class(c["layer"])
        out[k] = out.get(k, 0) + c["chars"]
    return dict(sorted(out.items()))


def _tokens(row):
    v = (row or {}).get("startup_tokens")
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None


def attribute(on, off):
    """ON / OFF probe rows -> {verdict MEASURED|UNDECIDED, host_forced, cpp_added, reason}. The OFF reading is
    trusted only when its window was read and carries no hook context (the kill switch demonstrably took effect)."""
    t_on, t_off = _tokens(on), _tokens(off)
    res = {"on_tokens": t_on, "off_tokens": t_off, "host_forced": None, "cpp_added": None}
    off_layers = (off or {}).get("layers")
    if t_on is None:
        reason = "on_unmeasured"
    elif t_off is None:
        reason = "off_unmeasured"
    elif not isinstance(off_layers, dict) or "unmeasured" in off_layers:
        reason = "off_window_unmeasured"
    elif off_layers.get("hooks"):
        reason = "kill_switch_ineffective"
    elif t_off > t_on:
        reason = "off_exceeds_on"
    else:
        res.update(verdict="MEASURED", host_forced=t_off, cpp_added=t_on - t_off, reason=None)
        return res
    res.update(verdict="UNDECIDED", reason=reason)
    return res


def rank(on_layers, off_layers=None):
    """Controllable classes by ON chars, largest first; off_chars is None where OFF did not measure the class."""
    off_layers = off_layers if isinstance(off_layers, dict) and "unmeasured" not in off_layers else {}
    rows = [{"class": k, "on_chars": v, "off_chars": off_layers.get(k, 0 if off_layers else None)}
            for k, v in (on_layers or {}).items() if k in CONTROLLABLE]
    return sorted(rows, key=lambda r: (-r["on_chars"], r["class"]))


# --------------------------------------------------------------------------- running sessions
def run(label, prompt, settings_file=None, max_turns=1, watch=(), cwd=REPO, env_extra=None):
    cmd = [CLAUDE, "-p", prompt, "--model", MODEL, "--output-format", "json", "--max-turns", str(max_turns)]
    if settings_file:
        cmd += ["--settings", json.dumps(json.load(open(settings_file, encoding="utf-8")))]
    env = dict(os.environ, **(env_extra or {}))
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
                       env=env)
    rec = {"label": label, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "settings_file": settings_file, "cwd": cwd,
           "env_extra": sorted((env_extra or {}).keys()), "rc": r.returncode, "wall_s": round(time.time() - t0, 1)}
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        rec["error"] = "no JSON result on stdout: " + (r.stderr or r.stdout)[-300:]
        return rec
    rec.update(session_id=res.get("session_id"), cost_usd=res.get("total_cost_usd"), turns=res.get("num_turns"),
               result=str(res.get("result", ""))[:300])
    tp = transcript(rec["session_id"])
    if tp:
        rec.update(analyse(tp, list(watch)))
        rec["layers"] = decompose(tp)
    else:
        rec["listing"] = "UNMEASURED (transcript not found)"
    return rec


def _env_pairs(items):
    out = {}
    for item in items or []:
        k, sep, v = item.partition("=")
        if not sep or not k:
            raise ValueError(f"--off-env expects K=V, got {item!r}")
        out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--settings-file")
    ap.add_argument("--max-turns", type=int, default=1)
    ap.add_argument("--watch", default="")
    ap.add_argument("--cwd", default=REPO, help="session working directory (champion and challenger must match in kind)")
    ap.add_argument("--out", default=None, help="results file (default: listing_floor_probe.results.jsonl)")
    ap.add_argument("--pair", action="store_true", help="ON then OFF session; attribute host-forced vs CPP-added")
    ap.add_argument("--off-settings", help="settings file passed as --settings to the OFF session only")
    ap.add_argument("--off-env", action="append", default=[], help="K=V env kill switch for the OFF session only")
    a = ap.parse_args()
    out = a.out or OUT
    watch = [w for w in a.watch.split(",") if w]
    if a.pair:
        if not (a.off_settings or a.off_env):
            print(json.dumps({"error": "--pair needs --off-settings or --off-env: an OFF run with nothing switched "
                                       "off would attribute noise"}))
            return 2
        on = run(a.label + ":on", a.prompt, a.settings_file, a.max_turns, watch, a.cwd)
        off = run(a.label + ":off", a.prompt, a.off_settings, a.max_turns, watch, a.cwd, _env_pairs(a.off_env))
        rec = {"label": a.label, "mode": "pair", "class": "minimal-prompt@" + os.path.basename(a.cwd.rstrip("\\/")),
               "prompt": a.prompt, "on": on, "off": off, "attribution": attribute(on, off),
               "rank": rank(on.get("layers"), off.get("layers"))}
    else:
        rec = run(a.label, a.prompt, a.settings_file, a.max_turns, watch, a.cwd)
        if "error" in rec:
            print(json.dumps(rec)); return 1
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
