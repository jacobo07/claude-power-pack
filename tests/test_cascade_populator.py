"""tests/test_cascade_populator.py — MC-OVO-107

Real-fixture tests for tools/cascade_populate_js.py. No mocks; every
test plants real .js files in tmpdir and asserts on actual populator
output.

Run:
    python -m unittest tests.test_cascade_populator -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cascade_populate_js as cp  # noqa: E402


def _write(project: Path, rel: str, content: str) -> Path:
    p = project / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestEmptyProject(unittest.TestCase):
    def test_empty_project_yields_zero_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            g = cp.populate(Path(td))
            self.assertEqual(g["nodes"], [])
            self.assertEqual(g["edges"], [])
            self.assertEqual(g["_stalemates"], [])
            self.assertEqual(g["schema"], "ovo-cascade-graph-v2")

    def test_only_non_js_files_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "README.md", "# nothing here")
            _write(project, "tools/script.py", "def x(): pass\n")
            g = cp.populate(project)
            self.assertEqual(len(g["nodes"]), 0)


class TestRequireAndImport(unittest.TestCase):
    def test_commonjs_require_resolves_local(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "lib/util.js", "exports.x = 1;\n")
            _write(project, "lib/main.js", "const u = require('./util');\n")
            g = cp.populate(project)
            self.assertEqual(len(g["nodes"]), 2)
            edges = [(e["from"], e["to"]) for e in g["edges"]]
            self.assertIn(("lib/main.js", "lib/util.js"), edges)

    def test_es6_import_resolves_local(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "src/a.js", "export const a = 1;\n")
            _write(project, "src/b.js", "import {a} from './a';\nconsole.log(a);\n")
            g = cp.populate(project)
            edges = [(e["from"], e["to"]) for e in g["edges"]]
            self.assertIn(("src/b.js", "src/a.js"), edges)

    def test_external_require_marked_unresolved(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "lib/x.js", "const fs = require('fs');\n")
            g = cp.populate(project)
            externals = [e for e in g["edges"] if e.get("unresolved")]
            self.assertEqual(len(externals), 1)
            self.assertIn("non-local require", externals[0]["reason"])
            self.assertEqual(externals[0]["to"], "<external:fs>")


class TestShebangAndStalemate(unittest.TestCase):
    def test_shebang_is_stripped_not_stalemated(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "bin/cli.js", "#!/usr/bin/env node\nconst x = 1;\n")
            g = cp.populate(project)
            self.assertEqual(g["_stalemates"], [])
            self.assertEqual(len(g["nodes"]), 1)

    def test_es2020_nullish_coalescing_stalemates_honestly(self):
        # esprima 4.x doesn't support `??`. The populator MUST report
        # STALEMATE — never silently emit a node.
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "src/modern.js", "const x = a ?? b;\n")
            g = cp.populate(project)
            self.assertEqual(g["nodes"], [])
            self.assertEqual(len(g["_stalemates"]), 1)
            self.assertEqual(g["_stalemates"][0]["file"], "src/modern.js")
            self.assertIn("Unexpected token", g["_stalemates"][0]["reason"])

    def test_garbage_file_stalemates(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "broken.js", "this is not valid javascript {{{}}}}}")
            g = cp.populate(project)
            self.assertEqual(g["nodes"], [])
            self.assertEqual(len(g["_stalemates"]), 1)


class TestDefinitionsAndBlastRadius(unittest.TestCase):
    def test_function_and_class_definitions_collected(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "x.js",
                   "function foo(){} class Bar{} const f = ()=>1;\n")
            g = cp.populate(project)
            defs = g["nodes"][0]["definitions"]
            names = sorted(d["name"] for d in defs)
            # Anonymous arrow doesn't get an id; only named decls collected.
            self.assertEqual(names, ["Bar", "foo"])

    def test_blast_radius_direct_and_transitive(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            # B is consumed by A and C; A is consumed by D.
            # Inbound to B: {A, C} → direct=2.
            # Transitive (1 hop further from B): {A, C, D} → 3.
            _write(project, "B.js", "module.exports = 1;\n")
            _write(project, "A.js", "require('./B');\n")
            _write(project, "C.js", "require('./B');\n")
            _write(project, "D.js", "require('./A');\n")
            g = cp.populate(project)
            b = next(n for n in g["nodes"] if n["id"] == "B.js")
            self.assertEqual(b["blast_radius"]["direct_callers"], 2)
            self.assertEqual(b["blast_radius"]["transitive_callers"], 3)

    def test_unconnected_module_has_zero_blast_radius(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "isolated.js", "const x = 1;\n")
            g = cp.populate(project)
            n = g["nodes"][0]
            self.assertEqual(n["blast_radius"]["direct_callers"], 0)
            self.assertEqual(n["blast_radius"]["transitive_callers"], 0)


class TestSkipDirs(unittest.TestCase):
    def test_node_modules_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "node_modules/lib/a.js", "module.exports = 1;\n")
            _write(project, "src/b.js", "const x = 1;\n")
            g = cp.populate(project)
            self.assertEqual(len(g["nodes"]), 1)
            self.assertEqual(g["nodes"][0]["id"], "src/b.js")


class TestMergeWrite(unittest.TestCase):
    def test_merge_preserves_other_populator_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "vault" / "audits").mkdir(parents=True)
            existing = {
                "schema": "ovo-cascade-graph-v2",
                "generated_at": "old",
                "project": "x",
                "nodes": [{"id": "src/foo.py", "kind": "module",
                           "_populator": "cascade_populate_py"}],
                "edges": [{"from": "a", "to": "b", "type": "consumed_by",
                           "_populator": "cascade_populate_py"}],
                "_stalemates": [],
                "_legacy_v1": {"classes": ["LegacyClass"]},
            }
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps(existing), encoding="utf-8")
            _write(project, "lib/x.js", "const y = 1;\n")

            g = cp.populate(project)
            cp.merge_write(project, g)

            written = json.loads(
                (project / "vault" / "audits" / "cascade_graph.json")
                .read_text(encoding="utf-8"))
            populators = {n.get("_populator") for n in written["nodes"]}
            self.assertIn("cascade_populate_py", populators)
            self.assertIn("cascade_populate_js", populators)
            # Legacy v1 preserved.
            self.assertEqual(written["_legacy_v1"]["classes"], ["LegacyClass"])

    def test_re_run_replaces_own_nodes_not_others(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            _write(project, "a.js", "module.exports = 1;\n")
            cp.merge_write(project, cp.populate(project))
            # Add a new file and re-run.
            _write(project, "b.js", "module.exports = 2;\n")
            cp.merge_write(project, cp.populate(project))
            written = json.loads(
                (project / "vault" / "audits" / "cascade_graph.json")
                .read_text(encoding="utf-8"))
            ids = sorted(n["id"] for n in written["nodes"])
            self.assertEqual(ids, ["a.js", "b.js"])


if __name__ == "__main__":
    unittest.main()
