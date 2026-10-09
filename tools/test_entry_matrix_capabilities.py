"""A4 W0 step 3: regenerate byte-identical (green) / planted unreachable capability (red)."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "entry_matrix.py"
MD = REPO / "vault/programs/cognitive-economy/a4/CAPABILITY_MATRIX.md"
GIT = r"C:\Program Files\Git\cmd\git.exe"


def run(*args):
    return subprocess.run([sys.executable, "-I", str(TOOL), *args], capture_output=True, text=True).returncode


class T(unittest.TestCase):
    def test_green_identical(self):
        self.assertEqual(run("--capabilities", "--check", str(MD)), 0)

    def test_red_planted_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "root.py").write_text("print('root')\n")
            (d / "lonely.py").write_text("def orphan():\n    return 1\n")
            for c in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
                subprocess.run([GIT, *c], cwd=d, check=True)
            cfg = {"roots": ["root.py"], "rows": [{"id": 1, "name": "planted", "card_state": "ACTIVE_PARTIAL",
                   "anchors": [{"path": "lonely.py", "role": "core"}]}]}
            (d / "cfg.json").write_text(json.dumps(cfg))
            md = d / "out.md"
            self.assertEqual(run("--capabilities", "--root", str(d), "--config", str(d / "cfg.json"), "--out", str(md)), 0)
            self.assertIn("UNREACHABLE", md.read_text())
            self.assertEqual(run("--capabilities", "--root", str(d), "--config", str(d / "cfg.json"), "--check", str(md)), 1)


if __name__ == "__main__":
    unittest.main()
