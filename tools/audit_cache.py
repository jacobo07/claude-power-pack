#!/usr/bin/env python3
"""
Audit Cache — Hash-based source file skip for FORENSIC audits.

Generates SHA-256 hashes + structural metadata for source files.
On re-audit, unchanged files can be skipped (read summary instead of full file).

Usage:
    python audit_cache.py --project /path/to/repo --build     # scan and cache
    python audit_cache.py --project /path/to/repo --check-all  # report changes
    python audit_cache.py --project /path/to/repo --summary src/Foo.java  # cached summary
"""

import argparse
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CACHE_DIR = "_audit_cache"
CACHE_FILE = "source_map.json"

# Default file patterns to scan
DEFAULT_PATTERNS = ["**/*.java", "**/*.py", "**/*.ts", "**/*.js", "**/*.yml", "**/*.yaml", "**/*.md"]

# Directories to skip
SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", "__pycache__", ".gradle", "_audit_cache", ".obsidian"}

# Semantic DNA — keyword regex loaded from sidecar JSON (anti-quine: Mistake #43).
# Keeping the literal keywords out of this file prevents the scanner from
# self-matching its own pattern definitions.
_DNA_KEYWORDS_FILE = Path(__file__).parent / "_dna_keywords.json"


def _load_dna_config():
    if not _DNA_KEYWORDS_FILE.exists():
        return {}, {}
    data = json.loads(_DNA_KEYWORDS_FILE.read_text(encoding="utf-8"))
    ci_tags = set(data.get("case_insensitive_tags", []))
    compiled = {}
    for tag, parts in data.get("tags", {}).items():
        pattern = "|".join(f"(?:{p})" for p in parts)
        flags = re.IGNORECASE if tag in ci_tags else 0
        compiled[tag] = re.compile(pattern, flags)
    return compiled, data.get("path_map", {})


DNA_KEYWORD_MAP, DNA_PATH_MAP = _load_dna_config()

# Import extraction regex per extension
IMPORT_REGEX = {
    ".py": re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([.\w]+))", re.MULTILINE),
    ".js": re.compile(r"""(?:require\(['"]([^'"]+)['"]\)|from\s+['"]([^'"]+)['"])"""),
    ".ts": re.compile(r"""(?:require\(['"]([^'"]+)['"]\)|from\s+['"]([^'"]+)['"])"""),
    ".md": re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*?)?\]\]"),
}

# Signature extraction (top declarations) for neural summary
SIG_REGEX = re.compile(
    r"^\s*(?:def|async\s+def|class|function|export\s+(?:default\s+)?(?:async\s+)?function|"
    r"export\s+class|export\s+const|const\s+\w+\s*=\s*(?:async\s+)?\()\s*(\w+[^\n{:]*?)(?=[\n{:])",
    re.MULTILINE,
)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception:
        return 0


def extract_summary(path: Path) -> str:
    """Extract a 1-line structural summary from a source file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"{path.name} | unreadable"

    lines = text.splitlines()
    loc = len(lines)

    # Count imports/includes
    import_count = sum(1 for l in lines if re.match(r'^\s*(import |from |require\(|#include)', l))

    # Extract primary class/function name
    primary = path.stem
    for line in lines[:50]:
        m = re.match(r'(?:public\s+)?class\s+(\w+)', line)
        if m:
            primary = m.group(1)
            break
        m = re.match(r'(?:def|function|const|export\s+(?:default\s+)?(?:function|class))\s+(\w+)', line)
        if m:
            primary = m.group(1)
            break

    return f"{path.name} | {primary} | imports:{import_count} | {loc} LOC"


def extract_neural_summary(path: Path) -> str:
    """3-5 line intent summary: header doc + top 3 signatures. Returns ' | '-joined string."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

    lines = []
    suffix = path.suffix

    if suffix == ".py":
        m = re.search(r'^\s*"""(.+?)"""', text, re.DOTALL | re.MULTILINE)
        if m:
            first = m.group(1).strip().splitlines()[0].strip()
            if first:
                lines.append(f"doc: {first[:140]}")
    elif suffix in (".js", ".ts"):
        m = re.search(r'^/\*\*?\s*(.+?)\s*\*/', text, re.MULTILINE | re.DOTALL)
        if m:
            doc = re.sub(r"\n\s*\*\s*", " ", m.group(1)).strip().splitlines()[0]
            if doc:
                lines.append(f"doc: {doc[:140]}")
    elif suffix == ".md":
        for ln in text.splitlines():
            s = ln.strip()
            if s.startswith("---") or not s:
                continue
            if s.startswith("#"):
                lines.append(f"doc: {s.lstrip('#').strip()[:140]}")
                break
            lines.append(f"doc: {s[:140]}")
            break

    sigs = SIG_REGEX.findall(text)[:3]
    for s in sigs:
        clean = re.sub(r"\s+", " ", s).strip().rstrip("(,:{[ ")
        if clean:
            lines.append(f"sig: {clean[:100]}")

    return " | ".join(lines)


def extract_semantic_dna(path: Path, project: Path) -> list:
    """Auto-derive #Tags from path parts + content-keyword heuristics."""
    tags = set()
    try:
        rel = path.relative_to(project)
    except ValueError:
        rel = path

    for part in rel.parts:
        if part in DNA_PATH_MAP:
            tags.add(DNA_PATH_MAP[part])

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return sorted(tags)

    for tag, pattern in DNA_KEYWORD_MAP.items():
        if pattern.search(text):
            tags.add(tag)

    return sorted(tags)


def build_stem_map(project: Path) -> dict:
    """Pre-compute {stem: rel_path} map for efficient wikilink/import resolution."""
    stem_map = {}
    for pattern in DEFAULT_PATTERNS:
        for filepath in project.glob(pattern):
            try:
                rel_parts = filepath.relative_to(project)
            except ValueError:
                continue
            if should_skip(rel_parts) or not filepath.is_file():
                continue
            rel = str(rel_parts).replace("\\", "/")
            # Last-write wins; first-found preferred
            stem_map.setdefault(filepath.stem, rel)
    return stem_map


def extract_depends_on(path: Path, project: Path, stem_map: dict) -> list:
    """Resolve relative imports / wikilinks to project-relative paths. Skip stdlib/3rd-party."""
    suffix = path.suffix
    if suffix not in IMPORT_REGEX:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    deps = set()
    for match in IMPORT_REGEX[suffix].finditer(text):
        raw = next((g for g in match.groups() if g), None)
        if not raw:
            continue

        if suffix == ".py":
            # Relative import: starts with '.'
            if raw.startswith("."):
                levels = len(raw) - len(raw.lstrip("."))
                remainder = raw.lstrip(".")
                base = path.parent
                for _ in range(levels - 1):
                    base = base.parent
                parts = remainder.split(".") if remainder else []
                candidate = base.joinpath(*parts).with_suffix(".py") if parts else None
                if candidate and candidate.exists():
                    try:
                        deps.add(str(candidate.relative_to(project)).replace("\\", "/"))
                    except ValueError:
                        pass
            else:
                # Non-relative: try stem-map for local modules (e.g., "audit_cache" → tools/audit_cache.py)
                top = raw.split(".")[0]
                if top in stem_map:
                    deps.add(stem_map[top])
        elif suffix in (".js", ".ts"):
            if raw.startswith("."):
                candidate = (path.parent / raw).resolve()
                for ext in ("", ".js", ".ts", ".mjs", ".cjs"):
                    probe = Path(str(candidate) + ext) if ext else candidate
                    if probe.is_file():
                        try:
                            deps.add(str(probe.relative_to(project)).replace("\\", "/"))
                            break
                        except ValueError:
                            break
        elif suffix == ".md":
            # Obsidian wikilink: [[stem]] or [[path/stem]]
            stem = Path(raw.strip()).name
            if stem in stem_map:
                deps.add(stem_map[stem])

    return sorted(deps)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def build_cache(project: Path) -> dict:
    """Scan project files and build the audit cache."""
    stem_map = build_stem_map(project)
    files = {}
    for pattern in DEFAULT_PATTERNS:
        for filepath in sorted(project.glob(pattern)):
            if should_skip(filepath.relative_to(project)):
                continue
            if not filepath.is_file():
                continue

            rel = str(filepath.relative_to(project)).replace("\\", "/")
            files[rel] = {
                "sha256": hash_file(filepath),
                "size_bytes": filepath.stat().st_size,
                "loc": count_lines(filepath),
                "last_modified": datetime.fromtimestamp(
                    filepath.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "summary": extract_summary(filepath),
                "neural_summary": extract_neural_summary(filepath),
                "semantic_dna": extract_semantic_dna(filepath, project),
                "depends_on": extract_depends_on(filepath, project, stem_map),
            }

    cache = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "2.0",
        "project": str(project),
        "file_count": len(files),
        "files": files,
    }

    cache_dir = project / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILE
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    return cache


def load_cache(project: Path) -> dict | None:
    cache_path = project / CACHE_DIR / CACHE_FILE
    if not cache_path.exists():
        return None
    return json.loads(cache_path.read_text(encoding="utf-8"))


def rebuild_neural(project: Path) -> dict:
    """Re-extract neural_summary + semantic_dna + depends_on for all cached files.
    Skips rehashing — hash/loc/size/mtime preserved. Useful after tuning DNA_KEYWORD_MAP."""
    cache = load_cache(project)
    if not cache:
        print("No audit cache found. Run --build first.", file=sys.stderr)
        sys.exit(1)

    stem_map = build_stem_map(project)
    updated = 0
    missing = 0
    for rel, entry in cache.get("files", {}).items():
        filepath = project / rel
        if not filepath.exists():
            missing += 1
            continue
        entry["neural_summary"] = extract_neural_summary(filepath)
        entry["semantic_dna"] = extract_semantic_dna(filepath, project)
        entry["depends_on"] = extract_depends_on(filepath, project, stem_map)
        updated += 1

    cache["schema_version"] = "2.0"
    cache["neural_rebuilt_at"] = datetime.now(timezone.utc).isoformat()
    (project / CACHE_DIR / CACHE_FILE).write_text(
        json.dumps(cache, indent=2), encoding="utf-8"
    )
    print(f"Neural fields rebuilt: {updated} files updated, {missing} missing (hashes preserved).")
    return cache


def check_all(project: Path) -> None:
    """Report changed vs unchanged files since last audit."""
    cache = load_cache(project)
    if not cache:
        print("No audit cache found. Run --build first.")
        sys.exit(1)

    old_files = cache.get("files", {})
    unchanged = 0
    changed = []
    new_files = []
    deleted = []

    # Check current files
    current = set()
    for pattern in DEFAULT_PATTERNS:
        for filepath in sorted(project.glob(pattern)):
            if should_skip(filepath.relative_to(project)):
                continue
            if not filepath.is_file():
                continue

            rel = str(filepath.relative_to(project)).replace("\\", "/")
            current.add(rel)

            if rel not in old_files:
                new_files.append(rel)
            elif hash_file(filepath) != old_files[rel]["sha256"]:
                changed.append(rel)
            else:
                unchanged += 1

    # Check for deleted files
    for rel in old_files:
        if rel not in current:
            deleted.append(rel)

    print(f"=== Audit Cache Check ===")
    print(f"Project: {project}")
    print(f"Cache from: {cache.get('generated_at', 'unknown')}\n")
    print(f"  UNCHANGED (skip): {unchanged}")
    print(f"  CHANGED (re-read): {len(changed)}")
    print(f"  NEW (read):        {len(new_files)}")
    print(f"  DELETED:           {len(deleted)}")

    if changed:
        print(f"\nChanged files:")
        for f in changed:
            print(f"  {f}")
    if new_files:
        print(f"\nNew files:")
        for f in new_files:
            print(f"  {f}")
    if deleted:
        print(f"\nDeleted files:")
        for f in deleted:
            print(f"  {f}")

    tokens_saved = unchanged * 200  # ~200 tokens avg per skipped file
    print(f"\nEstimated token savings: ~{tokens_saved} tokens (skipping {unchanged} unchanged files)")


def show_summary(project: Path, filepath: str) -> None:
    """Print cached summary for a specific file."""
    cache = load_cache(project)
    if not cache:
        print("No audit cache found. Run --build first.")
        sys.exit(1)

    # Normalize path
    filepath = filepath.replace("\\", "/")
    entry = cache.get("files", {}).get(filepath)

    if not entry:
        print(f"File not in cache: {filepath}")
        sys.exit(1)

    print(f"File: {filepath}")
    print(f"Hash: {entry['sha256']}")
    print(f"Size: {entry['size_bytes']} bytes | {entry['loc']} LOC")
    print(f"Modified: {entry['last_modified']}")
    print(f"Summary: {entry['summary']}")
    if entry.get("semantic_dna"):
        print(f"Semantic DNA: {' '.join(entry['semantic_dna'])}")
    if entry.get("neural_summary"):
        print(f"Neural: {entry['neural_summary']}")
    if entry.get("depends_on"):
        print(f"Depends on ({len(entry['depends_on'])}):")
        for d in entry["depends_on"]:
            print(f"  - {d}")


def main():
    parser = argparse.ArgumentParser(description="Audit Cache \u2014 hash-based source file skip")
    parser.add_argument("--project", type=Path, required=True, help="Project root path")
    parser.add_argument("--build", action="store_true", help="Scan and build cache")
    parser.add_argument("--check-all", action="store_true", help="Report changed vs unchanged")
    parser.add_argument("--summary", type=str, help="Show cached summary for a file")
    parser.add_argument("--rebuild-neural", action="store_true",
                        help="Re-extract neural_summary + semantic_dna + depends_on only (skip rehashing)")
    args = parser.parse_args()

    project = args.project.resolve()
    if not project.exists():
        print(f"ERROR: Project not found: {project}")
        sys.exit(1)

    if args.build:
        cache = build_cache(project)
        print(f"Audit cache built: {cache['file_count']} files indexed at {project / CACHE_DIR / CACHE_FILE}")
    elif args.rebuild_neural:
        rebuild_neural(project)
    elif args.check_all:
        check_all(project)
    elif args.summary:
        show_summary(project, args.summary)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
