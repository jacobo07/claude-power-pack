# ccp-s15-c1 audit (mutation_drill control run + layout) -- 2026-10-03

Sampled 10 test files (cdio, gsd_mission, hard_rules, karimo, lease, post_edit_diagnostics, tco, sdd_os, uqf, mutation_drill).

G1 FIX (answers a) PASS regex `\bPASS\s+<gate>\b` misses 3 of the formats sampled:
   - `[PASS] name: detail` (test_cdio.py:60, test_karimo.py:53): `]` follows PASS, no \s -> CONTROL_INVALID on a healthy gate.
   - `  name  PASS  evidence` (test_sdd_os.py:53): gate precedes the verdict word.
   - Matching formats: `PASS gate ev` (gsd_mission:36, mutation_drill:22, ped:30), `PASS  name` (hard_rules:26, tco:28, uqf:30), `  PASS gate:` (lease:31).
   Fix: accept `PASS\]?[\s:]+<gate>` OR `<gate>\s+PASS\b`; same widening for the FAIL side (sdd_os `name FAIL` is invisible to today's `FAIL <gate>` check too, so those suites were never drillable). Anything else -> CONTROL_INVALID, which is honest (never a wrong verdict), just not usable.

G2 FIX Gate name is matched as a prefix by `\b`: gate V-X also matches `FAIL V-X-2` / `PASS V-X-2` (hyphen is a \b boundary). Control can pass on the wrong line and a sibling gate failing reads KILLED. mutation_drill.py:101 has the same flaw today. Use lookahead `(?![\w-])`.

G3 FIX Control requires a `*_PASS=` line, but UNJUDGED/summary semantics differ: `_PASS=` also matches `V-UQF-PRE-REPORT-PASS`-style gate names inside ordinary lines only if followed by `=`; low risk. Real gap: control ignores the process exit code. A suite that prints the PASS line then crashes at exit, or exits nonzero with all gates passing, is accepted. Record returncode; require control rc==0 only if the mutant verdict logic does not use it (suites use `return 0 if fails==0`).

G4 FIX Same-copy write of the mutant: control may leave state on disk besides .pyc (tmp files, caches, ledgers written next to the subject, sqlite). Mutant run inherits it. PYTHONDONTWRITEBYTECODE covers .pyc only. NOTE-level unless a witness suite writes beside itself; cheap fix = copy the tree twice, or snapshot-compare file list after control and delete new files before the mutant.

G5 FIX P2 ancestor `.git` search: root is the repo, but P2 copies only top-level dirs of subject and test. If the subject is a root-level file (tools/x.py has top dir tools: fine; but `x.py` at root has no dir) rel.parts[0] is the file itself -> copytree on a file raises. Handle len(parts)==1 via shutil.copy2. Also a nested repo (skill dir inside ~/.claude with its own .git) works; a subject in a worktree with `.git` FILE works as designed.

G6 NOTE (answers b) Simpler than P2: keep the existing `root_env` branch but make it automatic when test is not inside subject dir, with repo_root = the test file's parent.parent (tests live in tools/, subject in modules|hooks, both under the pack root). Drops the .git walk. Cost: wrong when the test sits deeper than one level; the .git walk is more general. If kept, P2 is acceptable; the .git-must-contain-test check is the right fail-closed guard.

G7 NOTE (answers c) False-verdict paths still open: (1) test not honouring root: it imports the live repo by absolute path or hardcodes a path (c9/PED_HOOK witness). Copy runs, mutant is never loaded, SURVIVED is a false SURVIVED. Cheap detector: after the control, run once with an obviously-breaking mutant? Better: mutate a harmless marker and assert the module `__file__` ... simplest = require the test to print/accept its root, else document that SURVIVED on non-root_env layouts is only valid when the mutant dir is on sys.path first. (2) Gate that tests the mutated line only on a path not exercised by control data. That is a real SURVIVED, correct. (3) Mutant equivalent to the original, anchors that are no-ops: not detected; add text!=mutated check (HARNESS). (4) Timeout in control -> must be CONTROL_INVALID, not fall through (TIMEOUT has no PASS line, covered by rule, but state it).

G8 NOTE P3 copying vault/pricing + vault/config only when present is fine; but a suite reading any other sibling still returns UNJUDGED, which is the honest outcome. Keep copy_dirs documented as the escape.

Verdict: EXECUTE-WITH-FIXES
