"""Listing-floor probe (K3/K4, vault/plans/skill-virtualization-k-slice-2026-10-03.md).

Runs ONE fresh headless session and reports what the model actually received and did:
  startup_tokens  input + cache_creation + cache_read of the FIRST model call (model-visible, not chars)
  listing         chars / entries / described entries of the initial skill_listing attachment
  watch           per named skill: absent | name-only | described (n chars)
  loads           Skill tool_use names and Read paths ending in SKILL.md (page loads)
Appends one JSON row to listing_floor_probe.results.jsonl. Spawns `claude -p`; costs one session.

  python listing_floor_probe.py --label champion-1 --prompt "Reply with the single word OK."
  python listing_floor_probe.py --label r2 --settings-file s.json --watch a,b --prompt "..." --max-turns 1
"""
import argparse, glob, json, os, subprocess, sys, time

CLAUDE = r"C:\Users\User\.local\bin\claude.exe"
MODEL = "claude-opus-5-5"
REPO = os.path.expanduser("~/.claude/skills/claude-power-pack")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listing_floor_probe.results.jsonl")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--settings-file")
    ap.add_argument("--max-turns", type=int, default=1)
    ap.add_argument("--watch", default="")
    ap.add_argument("--cwd", default=REPO, help="session working directory (champion and challenger must match in kind)")
    a = ap.parse_args()
    cmd = [CLAUDE, "-p", a.prompt, "--model", MODEL, "--output-format", "json", "--max-turns", str(a.max_turns)]
    if a.settings_file:
        cmd += ["--settings", json.dumps(json.load(open(a.settings_file, encoding="utf-8")))]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=a.cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    rec = {"label": a.label, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "settings_file": a.settings_file, "cwd": a.cwd,
           "rc": r.returncode, "wall_s": round(time.time() - t0, 1)}
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        rec["error"] = "no JSON result on stdout: " + (r.stderr or r.stdout)[-300:]
        print(json.dumps(rec)); return 1
    rec.update(session_id=res.get("session_id"), cost_usd=res.get("total_cost_usd"), turns=res.get("num_turns"),
               result=str(res.get("result", ""))[:300])
    tp = transcript(rec["session_id"])
    rec.update(analyse(tp, [w for w in a.watch.split(",") if w]) if tp else {"listing": "UNMEASURED (transcript not found)"})
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
