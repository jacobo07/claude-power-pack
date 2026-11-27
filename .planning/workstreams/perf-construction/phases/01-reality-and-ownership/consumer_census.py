#!/usr/bin/env python3
"""Read-only consumer census for one package under modules/. stdlib only.
usage: consumers.py REPO_ROOT PACKAGE [--public name,name,...]
A file is a REAL consumer when it imports the package (ast Import/ImportFrom, importlib string,
sys.path insertion naming the package) AND uses at least one public name outside the import line.
Prints one line per importing file: KIND(prod|test) path imported-names used-names."""
import ast, os, sys

root, pkg = sys.argv[1], sys.argv[2]
SKIP = {".git", "node_modules", "_audit_cache", ".claude", ".planning", "vault", "__pycache__"}
dotted = "modules." + pkg
rows = []
for dp, dns, fns in os.walk(root):
    dns[:] = [d for d in dns if d not in SKIP]
    rel_dp = os.path.relpath(dp, root)
    if rel_dp == "modules/" + pkg or rel_dp.startswith("modules/" + pkg + os.sep):
        continue
    for fn in fns:
        if not fn.endswith(".py"):
            continue
        rel = os.path.normpath(os.path.join(rel_dp, fn))
        try:
            src = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except (SyntaxError, ValueError, OSError):
            continue
        imported, modalias, dyn = set(), set(), False
        import_lines = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                m = n.module or ""
                if m == dotted or m.startswith(dotted + "."):
                    for a in n.names:
                        imported.add(a.asname or a.name)
                    import_lines.add(n.lineno)
                elif m == "modules" and any(a.name == pkg for a in n.names):
                    for a in n.names:
                        if a.name == pkg:
                            modalias.add(a.asname or a.name)
                    import_lines.add(n.lineno)
                elif n.level and (m == pkg or m.startswith(pkg + ".")) and rel.startswith("modules" + os.sep):
                    for a in n.names:
                        imported.add(a.asname or a.name)
                    import_lines.add(n.lineno)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.name == dotted or a.name.startswith(dotted + "."):
                        modalias.add(a.asname or a.name)
                        import_lines.add(n.lineno)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and (
                    n.value == dotted or n.value.startswith(dotted + ".") or n.value == "modules/" + pkg
                    or ("modules" in n.value and pkg in n.value and "import" in n.value)):
                dyn = True
        if not (imported or modalias or dyn):
            continue
        used = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Name) and n.id in imported and getattr(n, "lineno", 0) not in import_lines:
                used.add(n.id)
            elif isinstance(n, ast.Attribute):
                base = n
                while isinstance(base, ast.Attribute):
                    base = base.value
                if isinstance(base, ast.Name) and base.id in modalias:
                    used.add(base.id + "." + n.attr)
        base_name = os.path.basename(rel)
        is_test = base_name.startswith("test_") or "tests" in rel.split(os.sep)
        kind = "test" if is_test else "prod"
        verdict = "REAL" if used else ("DYNAMIC_ONLY" if dyn and not (imported or modalias) else "IMPORT_UNUSED")
        rows.append((kind, verdict, rel, sorted(imported | modalias), sorted(used)))
for r in sorted(rows):
    print(r[0], r[1], r[2], ",".join(r[3]), "|", ",".join(r[4]))
print("TOTAL", len(rows), "prod_real", sum(1 for r in rows if r[0] == "prod" and r[1] == "REAL"),
      "test_real", sum(1 for r in rows if r[0] == "test" and r[1] == "REAL"))
