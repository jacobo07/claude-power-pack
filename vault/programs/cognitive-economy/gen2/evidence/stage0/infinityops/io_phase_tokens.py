"""Measured token spend of the odr-device-trust mission workers, attributed to roadmap phases.

Usage records come from each worker transcript plus its subagent transcripts; an assistant message is
counted once per message id (streamed messages repeat their usage on every line). Each message is
attributed to the phase of the first commit at or after its timestamp; messages after the last commit
belong to the phase in flight (4).
"""
import glob
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime

PROJ = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-io-device-trust")
WORKERS = ["be2a71eb", "50d3a9f0", "affe87e4", "63bc3ed8", "dc79aa64", "5f5bc46f", "4f1b398d", "dfc0acda"]
GIT = r"C:\Program Files\Git\cmd\git.exe"
REPO = r"C:\Users\User\Apps\io-device-trust"
KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


log = subprocess.run([GIT, "-C", REPO, "log", "275b2a55..HEAD", "--format=%ct %s"],
                     capture_output=True, text=True, check=True).stdout.splitlines()
commits = []
for line in log:
    t, subj = line.split(" ", 1)
    m = re.search(r"\(0(\d)-", subj)
    commits.append((int(t), int(m.group(1)) if m else None, subj))
commits.sort()
unphased = [c for c in commits if c[1] is None]


def phase_at(t):
    for ct, ph, _ in commits:
        if ct >= t and ph is not None:
            return ph
    return 4


per_phase = defaultdict(lambda: defaultdict(int))
per_worker = defaultdict(lambda: defaultdict(int))
files_seen = 0
for w in WORKERS:
    main = glob.glob(os.path.join(PROJ, f"{w}-*.jsonl"))
    sid = os.path.basename(main[0])[:-6] if main else None
    files = main + (glob.glob(os.path.join(PROJ, sid, "subagents", "*.jsonl")) if sid else [])
    seen = set()
    for f in files:
        files_seen += 1
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                msg = o.get("message") or {}
                u = msg.get("usage")
                if o.get("type") != "assistant" or not u:
                    continue
                key = (f, msg.get("id") or o.get("uuid"))
                if key in seen:
                    continue
                seen.add(key)
                ph = phase_at(ts(o["timestamp"]))
                for k in KEYS:
                    v = int(u.get(k) or 0)
                    per_phase[ph][k] += v
                    per_worker[w][k] += v
                per_phase[ph]["msgs"] += 1
                per_worker[w]["msgs"] += 1

print(f"transcript files read: {files_seen}; commits: {len(commits)} (unphased: {len(unphased)})")
for c in unphased:
    print("  unphased:", c[2][:90])
hdr = f"{'':10}{'msgs':>7}{'input':>12}{'cache_wr':>14}{'cache_rd':>16}{'output':>12}{'total':>16}"
print(hdr)
for label, table in (("phase", per_phase), ("worker", per_worker)):
    tot = defaultdict(int)
    for k in sorted(table):
        r = table[k]
        total = sum(r[x] for x in KEYS)
        print(f"{label[0]}{k!s:9}{r['msgs']:7}{r['input_tokens']:12,}{r['cache_creation_input_tokens']:14,}"
              f"{r['cache_read_input_tokens']:16,}{r['output_tokens']:12,}{total:16,}")
        for x in KEYS + ("msgs",):
            tot[x] += r[x]
    print(f"{'TOTAL':10}{tot['msgs']:7}{tot['input_tokens']:12,}{tot['cache_creation_input_tokens']:14,}"
          f"{tot['cache_read_input_tokens']:16,}{tot['output_tokens']:12,}{sum(tot[x] for x in KEYS):16,}")
    print()
