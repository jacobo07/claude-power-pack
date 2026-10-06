# S6 receipt -- zero-model step driver
verdict: PASS (code + tests). Live launch path UNEXERCISED (no worker could be launched, see S1-receipt).
inputs: tools/gsd_mission.py launch path read by grep: it is the Ralph epoch/mission launcher (packet = hand-off source
packet), not a per-unit packet runner, so a standalone driver was built (deviation: ~107 lines vs the <=80 asked).
files: tools/tranche_driver.py, tools/test_tranche_driver.py
commands: python tools/test_tranche_driver.py -> exit 0, DRIVER_PASS=12/12 (green control; missing receipt; unreachable
commit; no COMMITS line; failing test; over-cap spend; unknown spend not green; tranche over-cap refusal; step-max
refusal; admission refusal (session-declare rc 3); pass path where the first worker's measured spend makes the second
step refused; real meter on this sid). First run was 11/12: the PASS-PATH test itself was wrong (fixed, not the driver).
facts: `claude --help` lists --session-id, --permission-mode, --allowedTools, --max-budget-usd; NOT --max-turns, so the
driver does not pass it. Spend enforcement = existing mission_spend.py session-declare + session_budget_guard.js.
COMMITS: b0be32ee
spend: inside coordinator sid e6e0eca7 (not separable); coordinator reading after S6+S4 = 1,981,962.
