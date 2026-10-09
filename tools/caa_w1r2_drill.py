import json, subprocess, sys, tempfile, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = [
 ("edge-triggered", "V-WAIT-PRESAT", "if sat is False:",
  'if sat is False or events[0].data.get("declared_observation") is True:'),
 ("no-CAS", "V-WAIT-CONCURRENT", "return None, True",
  'return type("E", (), {"seq": seq})(), False'),
 ("skipped-invalidator", "V-WAIT-INVALIDATOR", "if inv_val is True:", "if False:"),
 ("worktree-read", "V-WAIT-WORKTREE",
  'present = ctx.run([ctx.git, "cat-file", "-e", spec], cwd=repo).returncode == 0',
  "present = (Path(repo) / path).exists()"),
 ("UNKNOWN-as-satisfied", "V-WAIT-REFUSED",
  'raise Unknown("predicate unreadable: %s" % json.dumps(evidence))', "sat = True"),
 ("contains-ignored", "V-WAIT-CONTENT", 'if leaf.get("contains") is not None:', "if False:"),
]
want = set(sys.argv[1:])
unknown = want - {m[0] for m in M}
if unknown:
    sys.exit("unknown mutant(s): %s; known: %s" % (sorted(unknown), [m[0] for m in M]))
d = tempfile.mkdtemp(prefix="drillspec_")
for name, gate, old, new in M:
    if want and name not in want:
        continue
    sp = os.path.join(d, name + ".json")
    json.dump({"file": "tools/mission_wait.py", "test": "tools/test_mission_wait.py", "gate": gate,
               "old": old, "new": new, "repo_root": R}, open(sp, "w"))
    r = subprocess.run([sys.executable, os.path.join(R, "tools", "mutation_drill.py"), "--spec", sp],
                       capture_output=True, text=True, timeout=600, cwd=R)
    last = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    print("MUTANT %s gate=%s rc=%d | %s" % (name, gate, r.returncode, " / ".join(last[-2:])))
