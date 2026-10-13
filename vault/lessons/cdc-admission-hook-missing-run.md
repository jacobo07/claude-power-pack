# cognitive_admission.js had no run(): the dispatcher chain entry was inert (CDC C3, found in C4)
- Symptom: C3 declared the Agent-edge admission live; the repo dispatcher listed the hook but a spawn was never denied through the real dispatcher CLI.
- Trigger: hook module exported decide() only; the dispatcher calls run().
- Root cause: C3 tests drove decide() and the hook file directly, never the dispatcher path.
- Fix: added run() (commit 4c9ea6f4); tools/test_cognitive_admission_dispatch.py drives PreToolUse-Agent-default.
- Prevention: every hook proof goes through the dispatcher CLI, not the module function.
- Regression proof: test_cognitive_admission_dispatch.py 4/4 (first spawn admitted, duplicate denied, kill switch admits).
