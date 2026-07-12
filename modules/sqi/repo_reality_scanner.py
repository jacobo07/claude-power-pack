"""SQI-01 — the Reality Scanner. The disk outranks every description of the disk.

Converts a directory into an inventory. Read-only: it never invokes repository code,
because executing a build to learn what the build produces inverts the dependency —
qualification is a downstream step that depends on the inventory the scan has not yet
produced (SQI-01 3.2).

Ordering is manifest-first (3.4). An extension census cannot separate a project's own
language from a vendored one; a manifest is a declaration of intent by the project's own
authors, and where the two disagree, the disagreement is itself the finding.

Every field is an observation with its basis attached, or an explicit unknown (3.10).
There is no third kind of field. An inferred field is a description wearing an
inventory's clothes, and every downstream consumer will mistake it for an observation.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).with_name("discovery_rules.json")

UNKNOWN = "UNKNOWN"


@dataclass
class Observation:
    """A value plus the artifact it was read from. A value without a basis is a claim."""

    value: Any
    basis: str  # "<path>" or "<path>:<line>" or "absent"

    def to_dict(self) -> dict:
        return {"value": self.value, "basis": self.basis}


@dataclass
class LanguageContext:
    """The five parameters of SQI-01 4.1. A repo has as many contexts as languages."""

    language: str
    runner: str
    test_patterns: list[str]
    manifests: list[str]
    lock_state: str  # LOCKED | UNLOCKED | NO_LOCK_CONVENTION | UNKNOWN
    toolchain_constraint: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class RepoRealityProfile:
    repo: str
    root: str
    commit: str
    language_contexts: list[LanguageContext]
    domains: list[str]
    suite_roots: list[str]
    test_artifacts: list[dict]
    declared_guards: list[dict]
    per_rule_hits: dict[str, int]
    uncertainty_count: int
    uncertainty_files: list[str]
    exclusions_applied: list[str]
    unknowns: list[str]
    scan_error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["language_contexts"] = [asdict(c) for c in self.language_contexts]
        return d


def _load_rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8-sig"))


def _git_commit(root: Path) -> str:
    """The commit anchors the map. A photograph with no timestamp has no derivative."""
    git = r"C:\Program Files\Git\cmd\git.exe"
    exe = git if os.path.exists(git) else "git"
    try:
        out = subprocess.run(
            [exe, "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return UNKNOWN


def _is_excluded(rel: Path, exclusions: list[str]) -> bool:
    return any(part in exclusions for part in rel.parts)


def _walk(root: Path, exclusions: list[str]):
    """One pass over the tree. Pruning at directory level, so an excluded subtree costs
    nothing rather than being filtered after the fact."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclusions]
        d = Path(dirpath)
        for fn in filenames:
            yield d / fn


def scan_repo(cwd: str | Path) -> RepoRealityProfile:
    """Inventory a repository from its disk. Never raises: an unreadable tree yields a
    profile whose fields are UNKNOWN and whose scan_error names the blocker."""
    root = Path(cwd).resolve()
    repo = root.name

    try:
        rules = _load_rules()
    except (OSError, ValueError) as exc:
        return RepoRealityProfile(
            repo=repo, root=str(root), commit=UNKNOWN, language_contexts=[],
            domains=[UNKNOWN], suite_roots=[], test_artifacts=[], declared_guards=[],
            per_rule_hits={}, uncertainty_count=0, uncertainty_files=[],
            exclusions_applied=[], unknowns=["discovery_rules"],
            scan_error=f"discovery rules unreadable: {exc}",
        )

    exclusions = rules["exclusions"]
    stacks = rules["stacks"]
    unknowns: list[str] = []

    try:
        all_files = list(_walk(root, exclusions))
    except OSError as exc:
        return RepoRealityProfile(
            repo=repo, root=str(root), commit=_git_commit(root), language_contexts=[],
            domains=[UNKNOWN], suite_roots=[], test_artifacts=[], declared_guards=[],
            per_rule_hits={}, uncertainty_count=0, uncertainty_files=[],
            exclusions_applied=exclusions, unknowns=["tree"],
            scan_error=f"tree unwalkable: {exc}",
        )

    rel_files = [f.relative_to(root) for f in all_files]
    names = {p.name for p in rel_files}

    # Stage 2 of the scan: the manifest layer. A manifest is the densest artifact in any
    # repository -- it names the language, the dependencies, and frequently the runner.
    contexts: list[LanguageContext] = []
    for lang, spec in stacks.items():
        found_manifests = [
            str(p).replace("\\", "/") for p in rel_files if p.name in spec["manifests"]
        ]
        source_hits = any(
            any(fnmatch.fnmatch(p.name, pat) for pat in spec["test_patterns"])
            for p in rel_files
        )
        if not found_manifests and not source_hits:
            continue

        locks = spec["locks"]
        if not locks:
            lock_state = "NO_LOCK_CONVENTION"
        elif any(n in names for n in locks):
            lock_state = "LOCKED"
        elif found_manifests:
            # A manifest declaring dependencies with no resolved lock means the set of code
            # that will execute is undetermined. This predicts a BLOCKED environment from a
            # read of two files, before a single build second is spent (SQI-01 3.6).
            lock_state = "UNLOCKED"
        else:
            lock_state = UNKNOWN

        evidence = found_manifests[:] or ["source-pattern match only (no manifest found)"]
        contexts.append(
            LanguageContext(
                language=lang,
                runner=spec["runner"],
                test_patterns=spec["test_patterns"],
                manifests=found_manifests,
                lock_state=lock_state,
                toolchain_constraint=UNKNOWN,
                evidence=evidence,
            )
        )

    if not contexts:
        # Manifest-absence is a signal, not a gap (SQI-01 3.5). A tree with no build
        # descriptor of any kind is, with high probability, a repository with no
        # executable surface -- not a repository whose manifest the scan failed to find.
        unknowns.append("no_language_context")

    # Stage 4: the test/runner layer. The authored census is built from the filesystem by
    # a process that has never read the project configuration (SQI-02 3.2, the circularity
    # trap). Asking the runner what it knows about yields a reach of 100% forever.
    test_artifacts: list[dict] = []
    per_rule_hits: dict[str, int] = {}
    for p in rel_files:
        for lang, spec in stacks.items():
            for pat in spec["test_patterns"]:
                if fnmatch.fnmatch(p.name, pat):
                    key = f"{lang}:{pat}"
                    per_rule_hits[key] = per_rule_hits.get(key, 0) + 1
                    test_artifacts.append(
                        {
                            "path": str(p).replace("\\", "/"),
                            "stack": lang,
                            "rule": pat,
                            "kind": "test_file",
                        }
                    )
                    break
            else:
                continue
            break

    # The engine's own uncertainty, reported rather than concealed (SQI-02 3.5). A census
    # that cannot state what it might have missed is asserting a completeness it has not
    # earned. These are files that matched no rule but live where tests live.
    matched = {a["path"] for a in test_artifacts}
    uncertainty_dirs = set(rules["uncertainty_dirs"])
    uncertainty_files = [
        str(p).replace("\\", "/")
        for p in rel_files
        if str(p).replace("\\", "/") not in matched
        and any(part.lower() in uncertainty_dirs for part in p.parts[:-1])
        and p.suffix in {".py", ".exs", ".java", ".js", ".ts", ".c"}
    ]

    suite_roots = sorted({str(Path(a["path"]).parent).replace("\\", "/") for a in test_artifacts})

    # Stage 5: the automation layer. A control that is never invoked is not a control.
    declared_guards = _declared_guards(root, rel_files, rules)

    domains = _classify_domains(root, rel_files, contexts, test_artifacts)

    return RepoRealityProfile(
        repo=repo,
        root=str(root),
        commit=_git_commit(root),
        language_contexts=contexts,
        domains=domains,
        suite_roots=suite_roots,
        test_artifacts=test_artifacts,
        declared_guards=declared_guards,
        per_rule_hits=per_rule_hits,
        uncertainty_count=len(uncertainty_files),
        uncertainty_files=uncertainty_files[:50],
        exclusions_applied=exclusions,
        unknowns=unknowns,
    )


def _declared_guards(root: Path, rel_files: list[Path], rules: dict) -> list[dict]:
    """Enumerate every declared scanner/linter/type-checker. SQI-02 Part XVII: a guard's
    presence in a repository and a guard's presence in an execution path are separate
    facts, recorded in separate places, and only the second one protects. This half is the
    first fact; the reconciliation engine subtracts the second."""
    guards: list[dict] = []
    seen: set[str] = set()
    manifest_names = {"pyproject.toml", "requirements.txt", "mix.exs", "package.json",
                      "setup.cfg", "pom.xml", "build.gradle"}
    for p in rel_files:
        if p.name not in manifest_names:
            continue
        try:
            text = (root / p).read_text(encoding="utf-8-sig", errors="replace").lower()
        except OSError:
            continue
        for lang, tools in rules["guard_declarations"].items():
            for tool in tools:
                if tool in text and tool not in seen:
                    seen.add(tool)
                    guards.append(
                        {
                            "guard": tool,
                            "stack": lang,
                            "declared_in": str(p).replace("\\", "/"),
                            "state": "declared",  # the ladder is climbed by the reconciler
                        }
                    )
    return guards


def _classify_domains(
    root: Path, rel_files: list[Path], contexts: list[LanguageContext], tests: list[dict]
) -> list[str]:
    """SQI-01 7.2/7.4: sixteen domains, and a unit may hold several. Forcing a single label
    is how one of two applicable standards silently disappears. Signals are artifact reads,
    never code interpretation."""
    domains: list[str] = []
    names = {p.name for p in rel_files}
    parts = {part for p in rel_files for part in p.parts}
    suffixes: dict[str, int] = {}
    for p in rel_files:
        suffixes[p.suffix] = suffixes.get(p.suffix, 0) + 1

    docs = suffixes.get(".md", 0) + suffixes.get(".txt", 0)
    code = sum(suffixes.get(s, 0) for s in (".py", ".js", ".ts", ".exs", ".java", ".c", ".rs"))

    if not contexts:
        return ["content_vault"]

    # An agent system's surfaces are hooks and dispatch points; its characteristic failure
    # is the built-but-unwired control (SQI-01 7.8). This estate is an instance.
    if "hooks" in parts or "agents" in parts or "commands" in parts:
        domains.append("agent_system")
    if "prompts" in parts or any(n.upper().startswith("CLAUDE.MD") for n in names):
        domains.append("prompt_system")
    if docs > code and docs > 20:
        domains.append("content_vault")
    if "package.json" in names and ("src" in parts or "extension" in parts):
        domains.append("frontend_application")
    if "tools" in parts or "scripts" in parts or "bin" in parts:
        domains.append("cli_tool")
    if len({c.language for c in contexts}) > 1:
        domains.append("hybrid_monorepo")
    if "modules" in parts and any(c.language == "python" for c in contexts):
        domains.append("library")
    if "Dockerfile" in names or "docker-compose.yml" in names or "terraform" in parts:
        domains.append("infrastructure")
    if "migrations" in parts:
        domains.append("backend_service")

    return domains or [UNKNOWN]


if __name__ == "__main__":  # pragma: no cover - manual probe
    import sys

    prof = scan_repo(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(prof.to_dict(), indent=2)[:4000])
