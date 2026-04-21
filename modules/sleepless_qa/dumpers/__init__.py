"""
Dumpers package — runtime-class adapters + auto-detection registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Type

from .base import ActionScript, ActionStep, Dumper, DumperError, EvidenceBundle, HTTPResponse
from .cli import CLIDumper
from .minecraft import MinecraftDumper
from .python_daemon import PythonDaemonDumper
from .web import WebDumper

REGISTRY: dict[str, Type[Dumper]] = {
    "web": WebDumper,
    "minecraft": MinecraftDumper,
    "python_daemon": PythonDaemonDumper,
    "cli": CLIDumper,
}


def get_dumper(runtime_class: str) -> Type[Dumper]:
    try:
        return REGISTRY[runtime_class]
    except KeyError as exc:
        raise DumperError(
            f"Unknown runtime_class={runtime_class!r}. Known: {sorted(REGISTRY)}"
        ) from exc


def autodetect(repo_path: Path) -> str:
    """
    Sniff repo_path for manifest files and return the best-fit runtime_class.

    Priority: package.json (web) > plugin.yml (minecraft) > pyproject.toml/requirements.txt (python_daemon) > fallback cli
    """
    repo_path = Path(repo_path)
    if (repo_path / "package.json").exists() or (repo_path / "next.config.js").exists():
        return "web"
    if (repo_path / "plugin.yml").exists() or (repo_path / "paper-plugin.yml").exists():
        return "minecraft"
    if (repo_path / "pom.xml").exists() and any((repo_path / "src").rglob("plugin.yml")):
        return "minecraft"
    if (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists():
        return "python_daemon"
    if (repo_path / "Makefile").exists() or (repo_path / "go.mod").exists():
        return "cli"
    return "cli"


__all__ = [
    "ActionScript",
    "ActionStep",
    "Dumper",
    "DumperError",
    "EvidenceBundle",
    "HTTPResponse",
    "WebDumper",
    "MinecraftDumper",
    "PythonDaemonDumper",
    "CLIDumper",
    "REGISTRY",
    "get_dumper",
    "autodetect",
]
