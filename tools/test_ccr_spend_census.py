"""V-CCRCENSUS-*: python tools/test_ccr_spend_census.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ccr_spend_census as C


def u(i=0, cr=0, cc=0, o=0):
    return {"input_tokens": i, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cc, "output_tokens": o}


def write(p: Path, rows) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


class T(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="ccr-census-"))

    def test_projection_dedups_by_mid(self):  # V-CCRCENSUS-PROJECTION
        p = write(self.d / "sid-p.jsonl", [
            {"t": "user", "uuid": "x"},
            {"t": "assistant", "mid": "m1", "usage": u(1, 100, 10, 5)},
            {"t": "assistant", "mid": "m1", "usage": u(1, 100, 10, 7)},    # same message, later block
            {"t": "assistant", "mid": "m2", "usage": u(2, 200, 0, 3)}])
        got = C.measure([p])["sid-p"]
        self.assertEqual((got["processed"], got["calls"]), (1 + 100 + 10 + 7 + 2 + 200 + 3, 2))

    def test_stream_json_takes_output_from_result(self):  # V-CCRCENSUS-STREAM
        a = {"type": "assistant", "session_id": "S", "message": {"id": "m1", "usage": u(1, 50, 5, 1)}}
        b = {"type": "assistant", "session_id": "S", "message": {"id": "m2", "usage": u(1, 60, 0, 1)}}
        p = write(self.d / "run.jsonl", [{"type": "system", "session_id": "S"}, a, a, b,
                                         {"type": "result", "session_id": "S", "usage": u(2, 110, 5, 400)}])
        self.assertEqual(C.measure([p])["S"]["processed"], 2 + 110 + 5 + 400)

    def test_resumed_session_across_files(self):  # V-CCRCENSUS-RESUME
        a = {"type": "assistant", "session_id": "S", "message": {"id": "m1", "usage": u(1, 50, 0, 1)}}
        b = {"type": "assistant", "session_id": "S", "message": {"id": "m2", "usage": u(1, 70, 0, 1)}}
        f1 = write(self.d / "r.jsonl", [a, {"type": "result", "session_id": "S", "usage": u(1, 50, 0, 30)}])
        f2 = write(self.d / "r.r1.jsonl", [a, b, {"type": "result", "session_id": "S", "usage": u(1, 70, 0, 20)}])
        self.assertEqual(C.measure([f1, f2])["S"]["processed"], 1 + 50 + 1 + 70 + 30 + 20)

    def test_raw_transcript(self):  # V-CCRCENSUS-RAW
        p = write(self.d / "t.jsonl", [
            {"type": "assistant", "sessionId": "R", "message": {"id": "m1", "usage": u(3, 0, 1000, 50)}},
            {"type": "user", "sessionId": "R", "message": {"content": "hi"}}])
        self.assertEqual(C.measure([p])["R"]["processed"], 1053)

    def test_no_usage_is_unknown_not_zero(self):  # V-CCRCENSUS-UNKNOWN
        p = write(self.d / "e.jsonl", [{"t": "user"}])
        self.assertIsNone(C.measure_one([p], "e"))

    def test_census_rows(self):  # V-CCRCENSUS-ROWS
        data = self.d / "data"
        pack = data / "pack"
        write(pack / "sessions" / "w1.jsonl", [{"t": "assistant", "mid": "m", "usage": u(1, 9, 0, 0)}])
        (pack / "missions.json").write_text(json.dumps([
            {"id": "m-1", "packet": "C:\\x\\vault\\programs\\ccr\\stage2\\WU-E1.md", "owners": ["w1"]},
            {"id": "m-2", "packet": "C:\\x\\vault\\programs\\other\\WU-E1.md", "owners": ["zz"]}]))
        write(pack / "v1" / "stream-r1-OFF.jsonl", [{"t": "assistant", "mid": "v", "usage": u(0, 0, 0, 4)}])
        write(data / "run-A2.jsonl", [{"type": "assistant", "session_id": "g2", "message": {"id": "m", "usage": u(5)}}])
        (data / "drive.log").write_text("T start A2 sid=g2 max_turns=30\nT end A2 sid=g2 rc=0\n"
                                        "T start A3 sid=g3 used=0\n")
        c = C.census(data)
        got = {r["row"]: r["processed"] for r in c["rows"]}
        self.assertEqual(got["Stage 2 E1 (m-1)"], 10)
        self.assertEqual(got["V1 canary stream-r1-OFF"], 4)
        self.assertEqual(got["Stage 3 A2"], 5)
        self.assertIsNone(got["Stage 3 A3"])                          # no run file: UNKNOWN
        self.assertIsNone(got["V1 canary r6-CCR (killed by host memory reaper, no stream)"])
        self.assertEqual(c["sum_known"], 19)
        self.assertNotIn("zz", [r["session"] for r in c["rows"]])
        self.assertIn("UNKNOWN", C.table(c))


if __name__ == "__main__":
    unittest.main()
