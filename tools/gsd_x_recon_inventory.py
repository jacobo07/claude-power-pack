"""Material events since the reconcile boundary, grouped by stream. Reuses the reconciler's
own materiality predicate (imported, not re-implemented) over ONE git log call."""
import collections, json, re, subprocess, sys
from pathlib import Path

PP = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
sys.path.insert(0, str(PP / "tools"))
import gsd_x_claim_reconcile as rc  # noqa: E402

since = rc.DEFAULT_SINCE
out = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "-C", str(PP), "log", "--reverse",
                      "--name-only", "--format=\x1e%H\x1f%ad\x1f%s", "--date=short", f"{since}..HEAD"],
                     capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
covered = rc.referenced_shas(rc.load_claims())
events, skipped = [], collections.Counter()
for block in out.split("\x1e")[1:]:
    head, _, rest = block.partition("\n")
    sha, date, subject = head.split("\x1f", 2)
    files = [f.strip() for f in rest.splitlines() if f.strip()]
    if not files:
        skipped["zero files"] += 1; continue
    if all(f.startswith("vault/datasets/gsd_x/") for f in files):
        skipped["ledger bookkeeping"] += 1; continue
    sub = [f for f in files if not rc.is_narration_or_generated(f)]
    if not sub:
        skipped["narration/generated"] += 1; continue
    if sha[:7] in covered:
        skipped["already covered"] += 1; continue
    m = re.match(r"^(\w+)(?:\(([^)]+)\))?!?:", subject)
    scope = (m.group(2) or m.group(1)) if m else "unscoped"
    events.append({"sha": sha[:7], "date": date, "subject": subject, "scope": scope.lower(), "files": sub})

groups = collections.defaultdict(list)
for e in events:
    groups[e["scope"]].append(e)
print(f"since={since} uncovered_material={len(events)} skipped={dict(skipped)} groups={len(groups)}")
for s, es in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(es):4d}  {s:28s} {es[0]['date']}..{es[-1]['date']}  e.g. {es[0]['subject'][:70]}")
Path(sys.argv[1]).write_text(json.dumps(groups, indent=1), encoding="utf-8")
