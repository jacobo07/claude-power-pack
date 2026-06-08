#!/usr/bin/env python3
"""Project Intelligence Scanner -- CPP Setup OS Pillar 1 (Sprint 3 / M11).

Builds a ProjectProfile of a repo from disk BEFORE any automation is
recommended. The repo on disk is the source of truth -- no memory, no
invention (source: Dataset CPP Setup 1.txt sec. 7 PROJECT PROFILE
SCANNER). Every field carries its detection SOURCE so an inference is
never presented as a fact (sec. 7.3 "Regla de realidad").

Read-only + stdlib-only. One bounded directory walk; heavy dirs skipped.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field as dc_field
import sys
from enum import Enum
from pathlib import Path

# Allow running as a standalone script from ANY cwd (e.g. /scan-repo invoked
# inside an external repo): put the PP repo root on sys.path so the absolute
# `from modules.setup_os.registry import ...` used by --save resolves in every
# invocation mode (python -m modules.setup_os.scanner OR python <abs>/scanner.py).
_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

MAX_FILES = 20000          # walk cap -- a runaway tree never hangs the scan
_SKIP_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv", "vendor",
    "dist", "build", ".next", "target", ".gradle", ".idea", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "coverage", ".turbo",
})


class Source(str, Enum):
    FILE = "detected_from_file"
    CONFIG = "detected_from_config"
    COMMAND = "detected_from_command"
    INFERRED = "inferred_from_structure"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class Field:
    value: object
    source: Source

    def to_dict(self) -> dict:
        return {"value": self.value, "source": self.source.value}


# Source-file extensions -> language. Used to pick the primary language.
_LANG_EXT = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".ex": "Elixir",
    ".exs": "Elixir", ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".c": "C", ".h": "C", ".cpp": "C++", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".kt": "Kotlin", ".swift": "Swift",
}


class _Index:
    """One bounded walk -> the structures every detector reads from."""

    def __init__(self, root: Path):
        self.root = root
        self.rel_files: set[str] = set()
        self.basenames: Counter = Counter()
        self.lang_counts: Counter = Counter()
        self.truncated = False
        self._walk()

    def _walk(self) -> None:
        n = 0
        for p in self.root.rglob("*"):
            parts = set(p.relative_to(self.root).parts)
            if parts & _SKIP_DIRS:
                continue
            if not p.is_file():
                continue
            n += 1
            if n > MAX_FILES:
                self.truncated = True
                break
            rel = str(p.relative_to(self.root)).replace("\\", "/")
            self.rel_files.add(rel)
            self.basenames[p.name] += 1
            lang = _LANG_EXT.get(p.suffix.lower())
            if lang:
                self.lang_counts[lang] += 1

    def has(self, name: str) -> bool:
        return self.basenames.get(name, 0) > 0

    def any_path(self, *substrings: str) -> bool:
        return any(any(s in rf for s in substrings) for rf in self.rel_files)

    def read_head(self, rel: str, n: int = 8000) -> str:
        try:
            return (self.root / rel).read_text(
                encoding="utf-8", errors="ignore")[:n]
        except OSError:
            return ""


@dataclass
class ProjectProfile:
    project_name: Field
    repo_path: Field
    branch: Field
    language_primary: Field
    language_secondary: Field
    framework_primary: Field
    package_manager: Field
    test_runner: Field
    build_system: Field
    lint_system: Field
    formatter: Field
    ci_cd: Field
    docker_presence: Field
    database_presence: Field
    auth_presence: Field
    payment_presence: Field
    external_api_presence: Field
    frontend_presence: Field
    backend_presence: Field
    cli_presence: Field
    monorepo_presence: Field
    existing_claude_md: Field
    existing_claude_config: Field
    existing_hooks: Field
    existing_skills: Field
    existing_agents: Field
    existing_commands: Field
    mcp_config_presence: Field
    secret_sensitive_files_presence: Field
    env_example_presence: Field
    docs_signal: Field
    test_coverage_signal: Field
    setup_readiness_score: Field
    notes: list = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        for k, v in asdict(self).items():
            if isinstance(v, dict) and set(v) == {"value", "source"}:
                d[k] = v
            else:
                d[k] = v
        # asdict already converted Field -> {value, source(enum)}; fix enum
        for k, v in d.items():
            if isinstance(v, dict) and "source" in v and isinstance(
                    v["source"], Source):
                v["source"] = v["source"].value
        return d


def _present(cond: bool, src: Source) -> Field:
    return Field(cond, src if cond else Source.MISSING)


def scan(path: str | Path | None = None) -> ProjectProfile:
    root = Path(path).resolve() if path else Path.cwd()
    idx = _Index(root)

    # Branch from .git/HEAD (read-only).
    branch_val, branch_src = "unknown", Source.UNKNOWN
    head = root / ".git" / "HEAD"
    if head.is_file():
        try:
            ref = head.read_text(encoding="utf-8", errors="ignore").strip()
            branch_val = ref.split("/")[-1] if "ref:" in ref else ref[:12]
            branch_src = Source.FILE
        except OSError:
            pass

    # Language primary / secondary by source-file frequency.
    langs = idx.lang_counts.most_common(2)
    lang1 = Field(langs[0][0], Source.INFERRED) if langs else Field(
        "unknown", Source.UNKNOWN)
    lang2 = Field(langs[1][0], Source.INFERRED) if len(langs) > 1 else Field(
        None, Source.MISSING)

    # Package manager.
    pm, pm_src = None, Source.MISSING
    for marker, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                         ("package-lock.json", "npm"), ("poetry.lock", "poetry"),
                         ("uv.lock", "uv"), ("Cargo.toml", "cargo"),
                         ("go.mod", "go"), ("requirements.txt", "pip"),
                         ("pyproject.toml", "pip/pyproject"),
                         ("mix.exs", "mix")):
        if idx.has(marker):
            pm, pm_src = name, Source.FILE
            break

    pkg_json = idx.read_head("package.json") if idx.has("package.json") else ""
    pyproj = idx.read_head("pyproject.toml") if idx.has("pyproject.toml") else ""
    reqs = idx.read_head("requirements.txt") if idx.has("requirements.txt") else ""
    dep_blob = (pkg_json + pyproj + reqs).lower()

    # Framework.
    fw, fw_src = None, Source.MISSING
    for needle, name in (("next", "Next.js"), ("nuxt", "Nuxt"),
                         ("svelte", "Svelte"), ("vue", "Vue"),
                         ("react", "React"), ("fastapi", "FastAPI"),
                         ("flask", "Flask"), ("django", "Django"),
                         ("phoenix", "Phoenix"), ("express", "Express")):
        if needle in dep_blob:
            fw, fw_src = name, Source.CONFIG
            break

    # Test runner.
    tr, tr_src = None, Source.MISSING
    if idx.has("conftest.py") or idx.has("pytest.ini") or idx.any_path(
            "tests/", "/test_") or "pytest" in dep_blob:
        tr, tr_src = "pytest", Source.INFERRED
    elif "vitest" in dep_blob:
        tr, tr_src = "vitest", Source.CONFIG
    elif "jest" in dep_blob:
        tr, tr_src = "jest", Source.CONFIG
    elif idx.has("mix.exs"):
        tr, tr_src = "mix test", Source.INFERRED

    # Build / lint / formatter.
    build = Field("make", Source.FILE) if idx.has("Makefile") else (
        Field("gradle", Source.FILE) if idx.has("build.gradle") else
        Field("maven", Source.FILE) if idx.has("pom.xml") else
        Field(None, Source.MISSING))
    lint = Field("ruff", Source.CONFIG) if "ruff" in (pyproj.lower()) or \
        idx.has(".ruff.toml") else (
        Field("eslint", Source.FILE) if idx.has(".eslintrc")
        or idx.any_path(".eslintrc") else Field(None, Source.MISSING))
    fmt = Field("black", Source.CONFIG) if "black" in dep_blob else (
        Field("prettier", Source.FILE) if idx.has(".prettierrc")
        or idx.any_path(".prettierrc") else Field(None, Source.MISSING))

    # CI/CD.
    ci = _present(idx.any_path(".github/workflows/")
                  or idx.has(".gitlab-ci.yml")
                  or idx.has("azure-pipelines.yml"), Source.FILE)

    docker = _present(idx.has("Dockerfile")
                      or idx.any_path("docker-compose"), Source.FILE)
    database = _present(idx.any_path(".sql", "alembic/", "prisma/",
                                     "migrations/")
                        or "sqlalchemy" in dep_blob or "prisma" in dep_blob,
                        Source.INFERRED)
    auth = _present("jwt" in dep_blob or "oauth" in dep_blob
                    or "passport" in dep_blob or "next-auth" in dep_blob,
                    Source.CONFIG)
    payment = _present("stripe" in dep_blob or "paypal" in dep_blob,
                       Source.CONFIG)
    ext_api = _present(any(k in dep_blob for k in
                           ("openai", "anthropic", "supabase", "stripe",
                            "twilio", "sendgrid", "aws-sdk", "boto3")),
                       Source.CONFIG)
    frontend = _present(fw in ("Next.js", "Nuxt", "Svelte", "Vue", "React")
                        or idx.any_path(".tsx", ".jsx", ".svelte", ".vue"),
                        Source.INFERRED)
    backend = _present(fw in ("FastAPI", "Flask", "Django", "Phoenix",
                              "Express") or idx.has("mix.exs"), Source.INFERRED)
    cli = _present(idx.any_path("/cli", "bin/") or "argparse" in dep_blob
                   or "click" in dep_blob, Source.INFERRED)
    monorepo = _present(idx.any_path("packages/", "apps/")
                        or idx.has("pnpm-workspace.yaml")
                        or "workspaces" in pkg_json.lower(), Source.INFERRED)

    # Claude config surface.
    claude_md = _present(idx.has("CLAUDE.md"), Source.FILE)
    claude_cfg = _present(idx.any_path(".claude/"), Source.FILE)
    hooks = _present(idx.any_path(".claude/hooks/", "/hooks/"), Source.FILE)
    skills = _present(idx.any_path(".claude/skills/", "/skills/"), Source.FILE)
    agents = _present(idx.any_path(".claude/agents/", "/agents/"), Source.FILE)
    commands = _present(idx.any_path(".claude/commands/", "/commands/"),
                        Source.FILE)
    mcp = _present(idx.any_path("settings.json", ".mcp.json")
                   or "mcpservers" in idx.read_head("settings.json").lower()
                   if idx.has("settings.json") else False, Source.CONFIG)

    secret_files = _present(idx.any_path(".env", ".pem", "id_rsa", ".key")
                            and not idx.any_path(".env.example",
                                                 ".env.sample"),
                            Source.FILE)
    env_example = _present(idx.any_path(".env.example", ".env.sample"),
                           Source.FILE)
    docs = _present(idx.has("README.md") or idx.any_path("docs/"), Source.FILE)
    coverage = _present(idx.any_path("tests/", "/test_", "_test.")
                        or tr is not None, Source.INFERRED)

    # Setup readiness: presence of good practices, minus naked-secret risk.
    good = sum(bool(x.value) for x in
               (ci, docker, claude_md, env_example, docs, coverage))
    readiness = max(0, min(100, good * 16 - (12 if secret_files.value else 0)))

    notes = []
    if idx.truncated:
        notes.append(f"walk truncated at {MAX_FILES} files -- profile partial")
    if secret_files.value and not env_example.value:
        notes.append("secret-sensitive files present without .env.example "
                     "-- secret firewall recommended before any install")

    return ProjectProfile(
        project_name=Field(root.name, Source.INFERRED),
        repo_path=Field(str(root), Source.FILE),
        branch=Field(branch_val, branch_src),
        language_primary=lang1, language_secondary=lang2,
        framework_primary=Field(fw, fw_src) if fw else Field(None, Source.MISSING),
        package_manager=Field(pm, pm_src) if pm else Field(None, Source.MISSING),
        test_runner=Field(tr, tr_src) if tr else Field(None, Source.MISSING),
        build_system=build, lint_system=lint, formatter=fmt, ci_cd=ci,
        docker_presence=docker, database_presence=database,
        auth_presence=auth, payment_presence=payment,
        external_api_presence=ext_api, frontend_presence=frontend,
        backend_presence=backend, cli_presence=cli,
        monorepo_presence=monorepo, existing_claude_md=claude_md,
        existing_claude_config=claude_cfg, existing_hooks=hooks,
        existing_skills=skills, existing_agents=agents,
        existing_commands=commands, mcp_config_presence=mcp,
        secret_sensitive_files_presence=secret_files,
        env_example_presence=env_example, docs_signal=docs,
        test_coverage_signal=coverage,
        setup_readiness_score=Field(readiness, Source.INFERRED),
        notes=notes)


def summarize(p: ProjectProfile) -> str:
    def v(f: Field):
        return f.value if f.value not in (None, False) else "none"
    return (f"{p.project_name.value}: {v(p.language_primary)}"
            f"{'/' + str(p.language_secondary.value) if p.language_secondary.value else ''}"
            f" project, framework={v(p.framework_primary)}, "
            f"pkg={v(p.package_manager)}, tests={v(p.test_runner)}, "
            f"ci={'yes' if p.ci_cd.value else 'no'}, "
            f"docker={'yes' if p.docker_presence.value else 'no'}, "
            f"claude_config={'yes' if p.existing_claude_config.value else 'no'}, "
            f"readiness={p.setup_readiness_score.value}/100")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Project Intelligence Scanner")
    ap.add_argument("--path", default=".")
    ap.add_argument("--json", action="store_true", help="emit full JSON profile")
    ap.add_argument("--save", action="store_true",
                    help="persist the profile to the Setup-OS registry "
                         "(PP vault/setup_os/profiles/, keyed by repo path) so "
                         "the pp-setup-scan signal knows this repo is profiled")
    args = ap.parse_args(argv)
    p = scan(args.path)
    if args.save:
        try:
            from modules.setup_os.registry import save_profile
            dest = save_profile(args.path, p.to_dict())
            print(f"profile saved: {dest}")
        except Exception as exc:  # noqa: BLE001 -- never fail the scan on save
            print(f"[warn] profile not saved: {type(exc).__name__}: {exc}")
    if args.json:
        print(json.dumps(p.to_dict(), indent=2, default=str))
    else:
        print(summarize(p))
        for n in p.notes:
            print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
