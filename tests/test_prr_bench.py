"""V-PRR-BENCH-*: the stub's reply script and the growth-slope fit."""
from modules.prr.bench import stub_api
from modules.prr.bench.longrun import fit


def _body(last, tools=("Bash",)):
    return {"messages": [last], "tools": [{"name": t} for t in tools]}


def test_fresh_turn_gets_tool_use_when_bytes_set():
    stub_api.CFG["tool_bytes"] = 1000
    r = stub_api.plan_reply(_body({"role": "user", "content": "turn 3"}))
    assert r["kind"] == "tool" and "1000" in r["input"]["command"]


def test_tool_result_turn_ends_with_text():
    stub_api.CFG["tool_bytes"] = 1000
    last = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "y"}]}
    assert stub_api.plan_reply(_body(last))["kind"] == "text"


def test_no_tool_when_bytes_zero_control():
    stub_api.CFG["tool_bytes"] = 0
    assert stub_api.plan_reply(_body({"role": "user", "content": "turn 3"}))["kind"] == "text"


def test_summary_request_gets_summary_text():
    stub_api.CFG["tool_bytes"] = 1000
    r = stub_api.plan_reply(_body({"role": "user", "content": "Write a summary of the conversation so far"}))
    assert r["kind"] == "text" and r["text"].startswith("<summary>")


def test_agent_script_spawns_agent_when_offered():
    stub_api.CFG.update(tool_bytes=1000, script="agent")
    r = stub_api.plan_reply(_body({"role": "user", "content": "turn 1"}, tools=("Bash", "Agent")))
    assert r["kind"] == "tool" and r["name"] == "Agent"
    # inside the subagent (no Agent tool offered) it falls back to the Bash fixture
    r2 = stub_api.plan_reply(_body({"role": "user", "content": "prr subagent turn"}, tools=("Bash",)))
    assert r2["name"] == "Bash"
    stub_api.CFG.update(script="bash")


def test_image_script_reads_image():
    stub_api.CFG.update(script="image", image="/tmp/x.png")
    r = stub_api.plan_reply(_body({"role": "user", "content": "turn 1"}, tools=("Bash", "Read")))
    assert r["name"] == "Read" and r["input"]["file_path"] == "/tmp/x.png"
    stub_api.CFG.update(script="bash", image=None)


def test_fit_detects_growth_and_flat():
    grow = fit([(k, 100 + 2 * k) for k in range(25, 125, 25)])
    flat = fit([(k, 300 + (k % 2)) for k in range(25, 525, 25)])
    assert grow["slope_mb_per_100_turns"] == 200.0
    assert abs(flat["slope_mb_per_100_turns"]) < 1.0


def test_fit_abstains_below_three_points():
    assert fit([(1, 1), (2, 2)])["slope_mb_per_100_turns"] is None


def test_last_receipt_picks_newest_stop_for_sid_after_since(tmp_path):
    from modules.prr.bench.longrun import last_receipt
    import json
    p = tmp_path / "r.jsonl"
    rows = [{"event": "Stop", "sid": "a", "ts": 5, "action": "KEEP"},
            {"event": "SessionStart", "sid": "a", "ts": 20, "action": "MARK"},
            {"event": "Stop", "sid": "b", "ts": 30, "action": "RECYCLE"},
            {"event": "Stop", "sid": "a", "ts": 15, "action": "RECYCLE"}]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n", encoding="utf-8")
    assert last_receipt(str(p), "a", 10, wait_s=0)["action"] == "RECYCLE"
    assert last_receipt(str(p), "a", 16, wait_s=0) is None  # stale receipts never drive a recycle


def test_write_policy_hooks_registers_sessionstart_and_stop(tmp_path):
    from modules.prr.bench.longrun import write_policy_hooks
    import json
    (tmp_path / "settings.json").write_text('{"model": "x"}', encoding="utf-8")
    write_policy_hooks(str(tmp_path), "hookcmd")
    cfg = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert cfg["model"] == "x"
    assert cfg["hooks"]["Stop"][0]["hooks"][0]["command"] == "hookcmd"
    assert "SessionStart" in cfg["hooks"]