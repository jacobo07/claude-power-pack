# W3c receipt - MARGINAL_GAIN_LOW

Changed (tools/gsd_mission.py):
1215:gain_samples: list | None = None) -> dict:
5594:# W3c: marginal gain. A pure verdict over a bounded sample list; the hold sits beside
6249:def judge_marginal_gain(samples: list, window: int = MARGINAL_GAIN_WINDOW) -> str:
6262:def _gain_sample(rec: dict, work_dir: str) -> list:
- launch_worker gets gain_samples kwarg, persisted into the record beside progress (extra["gain_samples"]); the relay launch passes rec["gain_samples"].
- Hold: after next_progress, before the NO_PROGRESS branch: relay_held ledger row + row["held"] + continue, only for act in (relay, replace). Hold, never halt. GSD_MARGINAL_GAIN=off keeps the verdict (row["marginal_gain"], gain_samples) but drops the hold. NO_PROGRESS branch unchanged.
- Caveat: a held relay does not persist the new sample (the existing holds do not persist either), so the same samples keep it held until the Owner acts.

Tests: test_w3_marginal_gain.py W3C_PASS=8/8 (incl. V-W3C-MUTATION-RED, V-W3C-WIRED-HELD, V-W3C-WIRED-KILL-SWITCH-RELAYS); test_gsd_mission.py MC_PASS=233/233 rc 0; test_wake_progress.py 11/11 rc 0.
Open items: none. Wiring test uses seams from test_gsd_mission.py with mission_spend.processed_tokens and _git_facts stubbed.

COMMITS: 1b0302b9
