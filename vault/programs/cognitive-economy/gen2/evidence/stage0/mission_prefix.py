"""Break down the per-call context of mission m-caadc51ab81e with KME's recon_cost_miner.mine_transcript
(imported unchanged). Control: summed context must agree with mission_tokens.py (273,912,110)."""
import collections, glob, json, os, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"C:\Users\User\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files\scripts\kme")
import recon_cost_miner as M  # noqa: E402

PROJ = Path(os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-recon-work-wt-keosdtk-home"))
ARM = datetime(2026, 10, 3, 19, 40, tzinfo=timezone.utc)
EXPECTED = 273_912_110

agg = collections.Counter()
ctx = out = unattr = 0
per_call = []
prefixes_main = []
untallied = collections.Counter()
n = 0
instr_sizes = collections.Counter()
for f in glob.glob(str(PROJ / "**" / "*.jsonl"), recursive=True):
    r = M.mine_transcript(Path(f))
    calls = [c for c in r["calls"] if c["ts"] and M._parse_ts(c["ts"]) and M._parse_ts(c["ts"]) >= ARM]
    if not calls:
        continue
    if len(calls) != len(r["calls"]):
        print("WARN partial-window transcript", f)
    n += 1
    agg.update(r["by_class"])
    ctx += r["context_tokens"]; out += r["output_tokens"]; unattr += r["unattributed"]
    per_call += [c["context"] for c in calls]
    untallied.update(r.get("attachments_untallied") or {})
    if "subagents" not in f and r["first_call_prefix"] is not None:
        prefixes_main.append(r["first_call_prefix"])
    if "subagents" not in f:
        with open(f, encoding="utf-8-sig") as fh:
            for line in fh:
                if '"attachment"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                a = o.get("attachment") if isinstance(o.get("attachment"), dict) else None
                if a and a.get("type") in ("instructions", "nested_memory"):
                    for k in ("path", "filePath", "file"):
                        if isinstance(a.get(k), str):
                            instr_sizes[a[k]] = max(instr_sizes[a[k]], len(json.dumps(a)))
                            break
                    else:
                        content = a.get("content") or a.get("contents")
                        if isinstance(content, list):
                            for it in content:
                                if isinstance(it, dict):
                                    p = it.get("path") or it.get("filePath")
                                    if isinstance(p, str):
                                        instr_sizes[p] = max(instr_sizes[p], len(json.dumps(it)))

print(f"TRANSCRIPTS {n}  CALLS {len(per_call)}")
print(f"CONTROL context={ctx:,} expected={EXPECTED:,} delta={ctx-EXPECTED:+,} ({(ctx-EXPECTED)/EXPECTED:+.2%})")
print(f"OUTPUT {out:,}")
print(f"PER_CALL_CONTEXT median={statistics.median(per_call):,.0f} p90={sorted(per_call)[int(len(per_call)*.9)]:,}")
print(f"FIRST_CALL_PREFIX main sessions (unexplained by tally) n={len(prefixes_main)} median={statistics.median(prefixes_main):,.0f}" if prefixes_main else "no prefix")
tot = sum(agg.values()) + unattr
for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
    print(f"CLASS {k:20s} {v:>14,}  {v/ctx:6.1%}")
print(f"CLASS {'unattributed':20s} {unattr:>14,}  {unattr/ctx:6.1%}")
print("UNTALLIED_ATTACHMENTS", dict(untallied.most_common(8)))
print("INSTRUCTION_FILES (largest, chars)")
for p, s in instr_sizes.most_common(12):
    print(f"  {s:>8,}  {p}")
