"""ICC Phase 5: the 2.1.318 SubagentHandback stream shape (real capture) must yield the real report."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import agent_carrier_run as R  # noqa: E402

FIX = ROOT / "tools" / "fixtures" / "handback_stream_2.1.318.jsonl"


def test_handback_report_is_the_reply_not_the_pointer():
    s = R.parse_stream(FIX.read_text(encoding="utf-8").splitlines())
    reply, src = R.carrier_reply(s)
    assert src == "handback"
    assert len(reply) > 500 and "delivered to you as a message" not in reply


def test_pointer_alone_is_not_a_reply():
    ptr = ('{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":'
           '"This agent\'s report was delivered to you as a message from x (its SubagentHandback call)."}]}}')
    reply, src = R.carrier_reply(R.parse_stream([ptr]))
    assert src != "handback"
