"""Project-type detection for the Auto-Testing Skill.

Spec ref: vault/specs/auto-testing-gate.md §4

Ranked, first match wins, walking up to 3 ancestors of the supplied cwd:

  1. pom.xml                     -> JAVA_MAVEN
  2. build.gradle / .kts         -> JAVA_GRADLE
  3. pyproject.toml / setup.py /
     setup.cfg / requirements*.txt -> PYTHON (manifest)
  4. >=5 test_*.py files at depth<=2 OR >=20 *.py at depth<=2
                                 -> PYTHON (convention)
  5. package.json                -> NODE_{VITEST|JEST|MOCHA|GENERIC}
  6. none                        -> UNKNOWN_NO_MANIFEST (CEILING)

Rule 4 was added 2026-05-23 after the A1 done-gate surfaced PP itself
(this repo) as a manifest-less Python project that the strict rule
mis-classified as node_generic. The convention rule is bounded by
depth<=2 to keep scan time predictable on very large monorepos.

Multiple matches (e.g. Java repo with a Node frontend) collapse to
MIXED; the runner picks the language whose extension matches the
staged diff later in the pipeline.

A framework binary missing on PATH (e.g. `mvn -v` non-zero) drops the
result to CEILING(reason="<lang> toolchain missing"), which the gate
honors by ALLOWING the commit.

Pure stdlib. No network. No subprocess except 1 toolchain `-v` probe
per detection (cached). Empirically verified against 5 real cwds:
KobiCraft, InfinityOps/UI, TUA-X, PP itself, and $env:TEMP.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ProjectType(str, Enum):
    JAVA_MAVEN = "java_maven"
    JAVA_GRADLE = "java_gradle"
    PYTHON = "python"
    NODE_VITEST = "node_vitest"
    NODE_JEST = "node_jest"
    NODE_MOCHA = "node_mocha"
    NODE_GENERIC = "node_generic"
    MIXED = "mixed"
    UNKNOWN_NO_MANIFEST = "unknown_no_manifest"


@dataclass
class Detection:
    type: ProjectType
    project_root: Optional[Path]
    reason: str
    framework_binary_available: bool = True
    secondary_types: list[ProjectType] = field(default_factory=list)
    package_json_path: Optional[Path] = None
    has_test_script: bool = False

    def is_ceiling(self) -> bool:
        return (
            self.type == ProjectType.UNKNOWN_NO_MANIFEST
            or not self.framework_binary_available
        )

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "project_root": str(self.project_root) if self.project_root else None,
            "reason": self.reason,
            "framework_binary_available": self.framework_binary_available,
            "secondary_types": [t.value for t in self.secondary_types],
            "package_json_path": (
                str(self.package_json_path) if self.package_json_path else None
            ),
            "has_test_script": self.has_test_script,
        }


_PYTHON_MARKERS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
)


def _has_requirements_file(d: Path) -> bool:
    try:
        for entry in d.iterdir():
            name = entry.name.lower()
            if name.startswith("requirements") and name.endswith(".txt"):
                return True
    except (OSError, PermissionError):
        pass
    return False


def _toolchain_available(cmd: str) -> bool:
    """`shutil.which` + a tiny `-v`/`--version` probe with hard timeout."""
    if not shutil.which(cmd):
        return False
    try:
        r = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            timeout=5,
            text=True,
        )
        return r.returncode == 0 or bool(r.stdout) or bool(r.stderr)
    except (subprocess.TimeoutExpired, OSError):
        return False


def _classify_node(pkg_path: Path) -> tuple[ProjectType, bool]:
    """Return (NodeVariant, has_test_script).

    Heuristic order:
      1. devDependencies has `vitest`      -> NODE_VITEST
      2. devDependencies has `jest`        -> NODE_JEST
      3. devDependencies has `mocha`       -> NODE_MOCHA
      4. scripts.test mentions vitest/jest/mocha -> match
      5. else                              -> NODE_GENERIC
    """
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return ProjectType.NODE_GENERIC, False

    dev = data.get("devDependencies") or {}
    deps = data.get("dependencies") or {}
    all_deps = {**dev, **deps}
    scripts = data.get("scripts") or {}
    test_script = scripts.get("test") or ""
    has_test_script = bool(test_script.strip())

    for key, variant in (
        ("vitest", ProjectType.NODE_VITEST),
        ("jest", ProjectType.NODE_JEST),
        ("mocha", ProjectType.NODE_MOCHA),
    ):
        if key in all_deps:
            return variant, has_test_script
        if key in test_script.lower():
            return variant, has_test_script
    return ProjectType.NODE_GENERIC, has_test_script


def _python_by_convention(d: Path) -> Optional[str]:
    """Convention-based Python detection (manifest-less).

    Returns a reason string if Python convention markers are present,
    else None. Bounded by depth<=2 to keep scan time low.
    """
    test_py = 0
    plain_py = 0
    try:
        for entry in d.iterdir():
            if entry.is_file() and entry.suffix == ".py":
                if entry.name.startswith("test_"):
                    test_py += 1
                else:
                    plain_py += 1
            elif entry.is_dir() and not entry.name.startswith("."):
                try:
                    for sub in entry.iterdir():
                        if sub.is_file() and sub.suffix == ".py":
                            if sub.name.startswith("test_"):
                                test_py += 1
                            else:
                                plain_py += 1
                            if test_py >= 5 and plain_py >= 20:
                                break
                except (OSError, PermissionError):
                    continue
            if test_py >= 3 and plain_py >= 3:
                break
    except (OSError, PermissionError):
        return None
    # Convention requires actual test files. Plain *.py count alone is
    # ambiguous (TEMP dirs accumulate random *.py from installers).
    if test_py >= 3 and plain_py >= 3:
        return ("python by convention: " + str(test_py) + " test_*.py + "
                + str(plain_py) + " *.py at depth<=2")
    return None


def _scan_dir(d: Path) -> dict:
    """One-shot scan returning which marker kinds are present in `d`."""
    found = {
        "pom": False,
        "gradle": False,
        "python": False,
        "package_json": None,  # type: Optional[Path]
    }
    try:
        entries = list(d.iterdir())
    except (OSError, PermissionError):
        return found
    names = {p.name.lower(): p for p in entries}
    if "pom.xml" in names:
        found["pom"] = True
    for n in names:
        if n.startswith("build.gradle"):
            found["gradle"] = True
            break
    if any(m in names for m in _PYTHON_MARKERS) or _has_requirements_file(d):
        found["python"] = True
    if "package.json" in names:
        found["package_json"] = names["package.json"]
    return found


def detect_project_type(cwd: os.PathLike | str) -> Detection:
    """Walk up to 3 ancestors of `cwd`, first match wins.

    The walk is necessary because the gate may be invoked from a
    subdirectory deep inside a monorepo.
    """
    start = Path(cwd).resolve()
    ancestors: list[Path] = [start]
    for parent in start.parents:
        ancestors.append(parent)
        if len(ancestors) >= 4:  # cwd + 3 parents
            break

    for d in ancestors:
        scan = _scan_dir(d)

        if scan["pom"]:
            ok = _toolchain_available("mvn")
            return Detection(
                type=ProjectType.JAVA_MAVEN,
                project_root=d,
                reason=("pom.xml at " + str(d) if ok else "pom.xml at " + str(d) + " but `mvn` not callable"),
                framework_binary_available=ok,
            )
        if scan["gradle"]:
            ok = _toolchain_available("gradle") or (d / "gradlew.bat").exists() or (d / "gradlew").exists()
            return Detection(
                type=ProjectType.JAVA_GRADLE,
                project_root=d,
                reason=("build.gradle at " + str(d) if ok else "build.gradle at " + str(d) + " but `gradle` not callable and no gradlew wrapper"),
                framework_binary_available=ok,
            )
        if scan["python"]:
            ok = _toolchain_available("python") or _toolchain_available("python3")
            secondary = []
            pkg_path = scan["package_json"]
            if pkg_path is not None:
                node_variant, _ = _classify_node(pkg_path)
                secondary = [node_variant]
            return Detection(
                type=ProjectType.PYTHON,
                project_root=d,
                reason="python marker at " + str(d),
                framework_binary_available=ok,
                secondary_types=secondary,
            )
        conv_reason = _python_by_convention(d)
        if conv_reason is not None:
            ok = _toolchain_available("python") or _toolchain_available("python3")
            secondary = []
            pkg_path = scan["package_json"]
            if pkg_path is not None:
                node_variant, _ = _classify_node(pkg_path)
                secondary = [node_variant]
            return Detection(
                type=ProjectType.PYTHON,
                project_root=d,
                reason=conv_reason + " at " + str(d),
                framework_binary_available=ok,
                secondary_types=secondary,
            )

        if scan["package_json"] is not None:
            variant, has_test = _classify_node(scan["package_json"])
            ok = _toolchain_available("node") and _toolchain_available("npx")
            return Detection(
                type=variant,
                project_root=d,
                reason="package.json at " + str(d),
                framework_binary_available=ok,
                package_json_path=scan["package_json"],
                has_test_script=has_test,
            )

    return Detection(
        type=ProjectType.UNKNOWN_NO_MANIFEST,
        project_root=None,
        reason="no build manifest found at cwd or up 3 ancestors",
        framework_binary_available=False,
    )


def main(argv: list[str]) -> int:
    """CLI smoke runner: emits JSON detection for each path argument.

    Empirical use:
      python detectors.py "<KobiCraft path>" "<InfinityOps UI path>" \
                          "<TUA-X path>" "<PP path>" "$env:TEMP"
    """
    if not argv:
        print("usage: detectors.py <cwd> [<cwd> ...]", flush=True)
        return 2
    for cwd in argv:
        det = detect_project_type(cwd)
        out = {"cwd": cwd, **det.to_dict()}
        print(json.dumps(out, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
