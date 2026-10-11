# EWC premises (E1) -- fact | file:line | verdict
Goal log = one JSON file per event goals/<repo-id>/<goal-id>/NNNNNN.json | modules/gsd_x/goal/log.py:41,100-102,162-174 | VERIFIED
Event fields seq,type,ts,actor,data,prev_digest,digest | log.py:162-174 | VERIFIED
append(expected_seq,...) | log.py:180 | VERIFIED
repo-id = root commit | log.py:84 | VERIFIED
OB_ACCEPTED projected with id,plane,text,done_gate,gate_pin,revision,gate_class | modules/gsd_x/goal/convergence.py:53,117 | VERIFIED
Session scope reuses same dir model via pseudo goal-id session-<sid>, no second store | log.py:100-102 | VERIFIED
Node read path: readdir + JSON.parse NNNNNN.json, no digest check on critical lane | log.py:162-174 | VERIFIED
GoalObligation dataclass; fields via d.get() so new fields default, old events project | convergence.py:72,117-120 | VERIFIED
mission/obligation.py Obligation is a DIFFERENT noun (derived obligations), not Goal Spine | modules/gsd_x/mission/obligation.py:47 | VERIFIED (WU-E1 step 1b wording was wrong)
Canonical CPP plan template for E5 = commands/ultra.md step 3 "Revised Plan" | commands/ultra.md:19 | VERIFIED
No gsd-planner/writing-plans file in worktree | glob | VERIFIED
speckit plan.md.template is feature plans only | vault/templates/speckit/plan.md.template | VERIFIED
Stop chain: closer-guard -> gsd_stop_continuation -> zero-issue-gate | hooks/hook-dispatcher.js:179,196,197 | VERIFIED
Canonical vs live dispatcher identical (sha256 750210EB4D94) | hooks/hook-dispatcher.js | VERIFIED
Canonical vs live closer-guard identical (09303A457C3B) | hooks/closer-guard.js | VERIFIED
Hook tests: hooks/tests/test-*.js (run-all.js) | hooks/tests | VERIFIED
test_hook_boundary drives node HOOK via subprocess input=json, parses stdout | tools/test_hook_boundary.py:82 | VERIFIED
Gates print [PASS]/[FAIL] and HOOK_PASS=n/n | tools/test_hook_boundary.py | VERIFIED
Rollover capsule obligations | tools/mission_capsule.py:58,183 | VERIFIED
Successor card render_card + _capsule_card_lines | tools/gsd_mission.py:1718,1737,2567 | VERIFIED
Both hooks use os.homedir(); override HOME+USERPROFILE | closer-guard.js:72-73; gsd_stop_continuation.js:69-71 | VERIFIED
closer-guard reads transcript tail, lastAssistantTurn | closer-guard.js:756,778 | VERIFIED
gsd_stop_continuation returns continue when no marker | gsd_stop_continuation.js:269 | VERIFIED
opt-in continuation:"stop-block" | gsd_stop_continuation.js:283 | VERIFIED
PROGRAMME.md claims (hasResult~413, classify~459) | closer-guard.js | VERIFIED
Verdict counts: VERIFIED 26 / FALSE 0 (1 brief-wording note on step 1b)
