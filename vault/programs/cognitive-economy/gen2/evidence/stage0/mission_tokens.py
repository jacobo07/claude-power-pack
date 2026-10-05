"""Measure tokens consumed by mission m-caadc51ab81e from its worker transcripts.

Population: every *.jsonl (incl. subagents/) under the worker cwd's project dir whose
entries fall after the arm time. Dedupe assistant usage by message.id (streamed chunks
repeat the same usage). Phase attribution: by commit-time windows from git log.
"""
import collections, datetime as dt, glob, json, os, re, subprocess, sys

PROJ = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-recon-work-wt-keosdtk-home")
WT = r"C:\Users\User\Apps\recon_work\wt_keosdtk_home"
GIT = r"C:\Program Files\Git\cmd\git.exe"
ARM = dt.datetime(2026, 10, 3, 19, 40, tzinfo=dt.timezone.utc)  # 21:40 +02:00

def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

# phase windows from commits: first commit time per phase tag
log = subprocess.run([GIT, "-C", WT, "log", "--reverse", "--format=%cI|%s", "338bbe5..HEAD"],
                     capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
first = {}
for line in log:
    t, s = line.split("|", 1)
    m = re.search(r"\((?:recon-factory-)?(\d{2}(?:\.\d)?)(?:-\d{2})?\)|recon-factory-(\d{2}(?:\.\d)?)", s)
    ph = (m.group(1) or m.group(2)) if m else None
    if ph:
        ph = ph.lstrip("0") or "0"
        first.setdefault(ph, ts(t))
bounds = sorted(first.items(), key=lambda kv: kv[1])
print("PHASE_STARTS", [(p, t.isoformat()) for p, t in bounds])
print("COMMITS", len(log), "last", log[-1][:80] if log else None)

def phase_of(t):
    cur = "0(setup)"
    for p, start in bounds:
        if t >= start:
            cur = p
    return cur

files = [f for f in glob.glob(os.path.join(PROJ, "**", "*.jsonl"), recursive=True)]
seen = set()
tot = collections.Counter()
by_phase = collections.defaultdict(collections.Counter)
by_session = collections.defaultdict(collections.Counter)
calls = 0
first_t = last_t = None
for f in files:
    sid = os.path.relpath(f, PROJ).split(os.sep)[0].replace(".jsonl", "")
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            msg = e.get("message") or {}
            u = msg.get("usage")
            if not u or not e.get("timestamp"):
                continue
            t = ts(e["timestamp"])
            if t < ARM:
                continue
            key = msg.get("id") or e.get("requestId") or e.get("uuid")
            if key in seen:
                continue
            seen.add(key)
            calls += 1
            first_t = t if first_t is None or t < first_t else first_t
            last_t = t if last_t is None or t > last_t else last_t
            c = collections.Counter({
                "input": u.get("input_tokens") or 0,
                "cache_write": u.get("cache_creation_input_tokens") or 0,
                "cache_read": u.get("cache_read_input_tokens") or 0,
                "output": u.get("output_tokens") or 0,
            })
            tot.update(c)
            by_phase[phase_of(t)].update(c)
            by_session[sid].update(c)

def fmt(c):
    allin = c["input"] + c["cache_write"] + c["cache_read"]
    return (f"in={c['input']:,} cw={c['cache_write']:,} cr={c['cache_read']:,} out={c['output']:,} "
            f"| context_total={allin:,} | fresh(in+cw+out)={c['input']+c['cache_write']+c['output']:,}")

print("FILES", len(files), "CALLS", calls, "SPAN", first_t, "->", last_t)
print("TOTAL", fmt(tot))
for p in sorted(by_phase, key=lambda k: (k[0].isdigit() is False, float(re.sub(r"[^\d.]", "", k) or -1))):
    print("PHASE", p, fmt(by_phase[p]))
print("SESSIONS", len(by_session))
for s, c in sorted(by_session.items(), key=lambda kv: -kv[1]["output"])[:8]:
    print("SESS", s[:8], fmt(c))
