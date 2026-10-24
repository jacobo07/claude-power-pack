# Summary 02-01
Landed arm_preflight + wiring. Refuses measured NO_PHASES/ALL_COMPLETE (/gsd- routes) and measured low memory (launching arms); UNAVAILABLE/unreadable = unmeasured, never refuse, never pass; authority absence and rotation repair = warn.
Tests: test_arm_preflight 16/16; test_gsd_mission 233/233, chain 11/11, goal_control 27/27, arm_worker_guard 6/6.
