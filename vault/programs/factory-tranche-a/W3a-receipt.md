# W3a receipt - live mission spend on the worker card

Changed (tools/gsd_mission.py, lines 3584,3644): new _live_spend_card_lines helper; render_card takes spend_fn=None and inserts the block right after the Dirty paths line. Uses live_spend as is; no new owner or measurement.
New: tools/test_w3_live_spend_card.py - W3A_PASS=5/5, exit 0.
tools/test_gsd_mission.py - MC_PASS=233/233, exit 0.

COMMITS: cc39c9b6
