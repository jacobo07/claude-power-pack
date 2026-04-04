#!/usr/bin/env python3
"""
KobiiClaw Initialization Engine — Zero-Shot Repository Discovery.

Introspects any repository, detects tech stack, reconciles universal + tech
rules, and generates .kobiiclaw_manifest.yml.

Usage:
    python init_engine.py /path/to/repo
    python init_engine.py /path/to/repo --deep       # Force RAG for unknown stacks
    python init_engine.py /path/to/repo --force       # Regenerate even if manifest exists
    python init_engine.py /path/to/repo --json        # Output structured JSON
"""

import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────
ENGINE_DIR = Path(__file__).resolve().parent
FINGERPRINTS_PATH = ENGINE_DIR / "tech_fingerprints.json"
UNIVERSAL_RULES_PATH = ENGINE_DIR / "universal_rules.yml"
TECH_RULES_DIR = ENGINE_DIR / "tech_rules"
MANIFESTS_DIR = ENGINE_DIR / "manifests"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [init_engine] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("init_engine")


# ── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class StackDetection:
    language: str
    version: Optional[str] = None
    build_system: str = "unknown"
    framework: Optional[str] = None
    confidence: float = 0.0
    indicators_matched: list[str] = field(default_factory=list)
    secondary: bool = False


@dataclass
class TechStackReport:
    primary: Optional[StackDetection] = None
    secondary: list[StackDetection] = field(default_factory=list)
    scan_duration_ms: int = 0
    total_files_scanned: int = 0
    repo_path: str = ""


@dataclass
class ReconciliationResult:
    rule_id: str
    rule_name: str
    implementation: str
    mutations: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class InitResult:
    success: bool
    manifest_path: Optional[str] = None
    report: Optional[dict] = None
    reconciliation: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None


# ── Phase 1: Introspection & Scanning ──────────────────────────────────────

def load_fingerprints() -> dict:
    """Load tech fingerprint database."""
    with open(FINGERPRINTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_dependencies_json(filepath: Path) -> list[str]:
    """Extract dependency names from package.json."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        deps = list(data.get("dependencies", {}).keys())
        deps += list(data.get("devDependencies", {}).keys())
        return deps
    except (json.JSONDecodeError, OSError):
        return []


def _parse_dependencies_xml(filepath: Path) -> list[str]:
    """Extract artifactId from pom.xml via regex (no XML parser needed)."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")[:65536]
        return re.findall(r"<artifactId>(.*?)</artifactId>", content)
    except OSError:
        return []


def _parse_dependencies_txt(filepath: Path) -> list[str]:
    """Extract package names from requirements.txt."""
    try:
        deps = []
        for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            name = re.split(r"[><=!~\[]", line)[0].strip().lower()
            if name:
                deps.append(name)
        return deps
    except OSError:
        return []


def _read_file_head(filepath: Path, max_bytes: int = 65536) -> str:
    """Read file head for content pattern matching."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except OSError:
        return ""


def scan_repo(repo_path: Path, fingerprints: dict, max_depth: int = 3) -> TechStackReport:
    """Phase 1: Scan repository to detect tech stack. Zero-shot, data-driven."""
    start = time.monotonic()
    skip_dirs = set(fingerprints.get("skip_dirs", []))
    indicators = fingerprints.get("indicators", [])

    # Accumulate matches: key = "stack:build_system"
    matches: dict[str, dict] = {}
    file_count = 0

    def _walk(path: Path, depth: int):
        nonlocal file_count
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: e.name)
        except PermissionError:
            return

        for entry in entries:
            if entry.name.startswith(".") and entry.name != ".github":
                continue

            if entry.is_dir(follow_symlinks=False):
                if entry.name in skip_dirs:
                    continue
                # Check directory indicators
                for ind in indicators:
                    if ind.get("is_dir") and entry.name == ind["file"].split("/")[-1]:
                        _record_match(ind, entry.path, None, None)
                _walk(Path(entry.path), depth + 1)
            elif entry.is_file(follow_symlinks=False):
                file_count += 1
                for ind in indicators:
                    if ind.get("is_dir"):
                        continue
                    if entry.name == ind["file"]:
                        _process_indicator(ind, Path(entry.path), repo_path)

    def _record_match(ind: dict, filepath: str, deps: list | None, content: str | None):
        stack = ind["stack"]
        build = ind.get("build_system", "unknown")
        key = f"{stack}:{build}"

        if key not in matches:
            matches[key] = {
                "language": stack,
                "build_system": build,
                "confidence_base": ind.get("confidence", 0.5),
                "framework": None,
                "version": None,
                "indicators": [],
                "framework_boost": 0.0,
                "content_boost": 0.0,
                "secondary": ind.get("secondary", False),
            }

        m = matches[key]
        m["indicators"].append(filepath)

        # Framework detection
        if deps and "framework_hints" in ind:
            for dep in deps:
                dep_lower = dep.lower()
                for hint_key, hint_val in ind["framework_hints"].items():
                    if hint_key.lower() in dep_lower:
                        m["framework"] = hint_val["framework"]
                        m["framework_boost"] = max(m["framework_boost"], hint_val.get("boost", 0.03))
                        break

        # Content pattern boosts
        if content and "content_patterns_boost" in ind:
            for boost_rule in ind["content_patterns_boost"]:
                patterns = boost_rule["patterns"]
                if any(p.lower() in content.lower() for p in patterns):
                    override_key = f"{boost_rule['override_stack']}:{boost_rule['override_build']}"
                    if override_key not in matches:
                        matches[override_key] = {
                            "language": boost_rule["override_stack"],
                            "build_system": boost_rule["override_build"],
                            "confidence_base": ind.get("confidence", 0.5) + boost_rule["boost"],
                            "framework": None,
                            "version": None,
                            "indicators": [filepath],
                            "framework_boost": 0.0,
                            "content_boost": boost_rule["boost"],
                            "secondary": False,
                        }
                    else:
                        matches[override_key]["content_boost"] = max(
                            matches[override_key]["content_boost"], boost_rule["boost"]
                        )

        # Build system override (e.g., yarn.lock -> yarn instead of npm)
        if "build_system_override" in ind:
            for check_file in ind["build_system_override"]["check_files"]:
                if (repo_path / check_file).exists():
                    new_build = ind["build_system_override"]["map"].get(check_file)
                    if new_build:
                        m["build_system"] = new_build
                        break

        # Version detection
        if content and "version_detection" in ind:
            pattern = ind["version_detection"]["pattern"]
            ver_match = re.search(pattern, content)
            if ver_match:
                m["version"] = ver_match.group(1)

    def _process_indicator(ind: dict, filepath: Path, root: Path):
        deps = None
        content = None

        # Parse dependencies based on file type
        if filepath.name == "package.json":
            deps = _parse_dependencies_json(filepath)
        elif filepath.name == "pom.xml":
            deps = _parse_dependencies_xml(filepath)
            content = _read_file_head(filepath)
        elif filepath.name in ("requirements.txt",):
            deps = _parse_dependencies_txt(filepath)
        elif filepath.name in ("Makefile", "CMakeLists.txt", "pyproject.toml", "build.gradle", "build.gradle.kts"):
            content = _read_file_head(filepath)

        _record_match(ind, str(filepath), deps, content)

    # Execute scan
    _walk(repo_path, 0)

    # Compute final confidence scores
    detections: list[StackDetection] = []
    for key, m in matches.items():
        file_factor = min(1.0, math.log2(max(1, len(m["indicators"]))) / 4.0)
        confidence = (
            m["confidence_base"] * 0.50
            + m["framework_boost"] * 4.0  # boost is 0-0.05, scale to 0-0.20
            + file_factor * 0.15
            + m["content_boost"] * 0.50   # content boost is 0-0.45, scale appropriately
        )
        confidence = min(1.0, max(0.0, confidence))

        detections.append(StackDetection(
            language=m["language"],
            version=m["version"],
            build_system=m["build_system"],
            framework=m["framework"],
            confidence=round(confidence, 3),
            indicators_matched=[str(p) for p in m["indicators"][:5]],
            secondary=m["secondary"],
        ))

    # Sort: non-secondary first, then by confidence
    detections.sort(key=lambda d: (d.secondary, -d.confidence))

    # Split primary vs secondary
    primary = None
    secondary = []
    for d in detections:
        if not d.secondary and primary is None:
            primary = d
        else:
            if d.confidence >= 0.3:
                secondary.append(d)

    # Fallback if no primary
    if primary is None and secondary:
        primary = secondary.pop(0)

    duration_ms = int((time.monotonic() - start) * 1000)
    return TechStackReport(
        primary=primary,
        secondary=secondary,
        scan_duration_ms=duration_ms,
        total_files_scanned=file_count,
        repo_path=str(repo_path),
    )


# ── Phase 2: Runtime Self-Education ────────────────────────────────────────

def load_tech_rules(report: TechStackReport, deep: bool = False) -> dict:
    """Phase 2: Load tech-specific rules for the detected stack."""
    if not report.primary:
        logger.warning("No primary stack detected. Using generic rules.")
        return _load_rules_file("generic.yml")

    # Build lookup key
    lang = report.primary.language.lower().replace("/", "_").replace(" ", "_")
    lang = re.sub(r"[^a-z0-9_]", "", lang)
    build = report.primary.build_system.lower().replace("/", "_").replace(" ", "_")
    build = re.sub(r"[^a-z0-9_]", "", build)

    # Try specific match first, then language-only, then generic
    candidates = [
        f"{lang}_{build}.yml",
        f"{lang}.yml",
        "generic.yml",
    ]

    for candidate in candidates:
        rules = _load_rules_file(candidate)
        if rules:
            logger.info(f"Loaded tech rules: {candidate}")
            return rules

    logger.warning("No matching tech rules found. Using empty rules.")
    return {}


def _load_rules_file(filename: str) -> dict | None:
    """Load a YAML rules file from tech_rules/."""
    filepath = TECH_RULES_DIR / filename
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None


# ── Phase 3: Reconciliation ────────────────────────────────────────────────

def load_universal_rules() -> list[dict]:
    """Load universal rules from YAML."""
    with open(UNIVERSAL_RULES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def reconcile_rules(
    universal: list[dict],
    tech_rules: dict,
    report: TechStackReport,
) -> list[ReconciliationResult]:
    """Phase 3: Cross universal rules with tech-specific rules."""
    results = []
    commands = tech_rules.get("commands", {})
    logs = tech_rules.get("logs", {})
    recovery = tech_rules.get("recovery", {})
    health = tech_rules.get("health_check", {})
    telemetry = tech_rules.get("telemetry", {})
    hot_swap = tech_rules.get("hot_swap", {})

    for rule in universal:
        rule_id = rule["id"]
        mutations = []

        if rule_id == "REMOTE_BUILD":
            impl = commands.get("build", rule.get("fallback", "echo 'no build'"))
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=impl, confidence=1.0 if commands.get("build") else 0.3,
            ))

        elif rule_id == "REMOTE_LOGS":
            log_path = logs.get("runtime_log", "stdout")
            if log_path == "stdout":
                impl = f"journalctl -f --no-pager -n 100"
                mutations.append("No file-based log detected. Using journalctl fallback.")
            else:
                impl = f"tail -f {log_path}"
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=impl, mutations=mutations,
                confidence=1.0 if log_path != "stdout" else 0.5,
            ))

        elif rule_id == "ROLLBACK":
            strategy = recovery.get("strategy", "git_rollback")
            cmd = recovery.get("rollback_cmd", "git checkout HEAD~1 -- .")
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=f"[{strategy}] {cmd}",
                confidence=1.0 if recovery.get("rollback_cmd") else 0.7,
            ))

        elif rule_id == "HEALTH_CHECK":
            proc = health.get("process_pattern", "")
            if proc:
                impl = f"pgrep -f '{proc}'"
            else:
                run_cmd = commands.get("run", "")
                impl = f"pgrep -f '{run_cmd}'" if run_cmd else "echo 'No health check configured'"
                mutations.append("No process pattern defined. Using run command as fallback.")
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=impl, mutations=mutations,
                confidence=1.0 if proc else 0.4,
            ))

        elif rule_id == "TELEMETRY":
            # Auto-select adapter based on detected framework/stack
            adapter = telemetry.get("adapter", "generic")
            if report.primary and report.primary.framework:
                adapter_map = rule.get("adapter_map", {})
                mapped = adapter_map.get(report.primary.framework)
                if mapped:
                    adapter = mapped
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=f"adapter={adapter}",
                confidence=1.0 if adapter != "generic" else 0.6,
            ))

        elif rule_id == "HOT_SWAP":
            if hot_swap.get("supported", False):
                impl = f"[hot_swap] {hot_swap.get('reload_cmd', 'N/A')}"
            else:
                strategy = hot_swap.get("strategy", "fast_restart")
                cmd = hot_swap.get("restart_cmd", rule.get("fallback_cmd", "echo 'restart not configured'"))
                impl = f"[{strategy}] {cmd}"
                mutations.append(f"Hot-swap not supported for {report.primary.language if report.primary else 'unknown'}. Mutated to {strategy}.")
            results.append(ReconciliationResult(
                rule_id=rule_id, rule_name=rule["name"],
                implementation=impl, mutations=mutations,
                confidence=1.0 if hot_swap.get("supported") or hot_swap.get("restart_cmd") else 0.5,
            ))

    return results


# ── Phase 4: Manifest Generation ───────────────────────────────────────────

def _classify_tier(report: TechStackReport) -> str:
    """Classify project complexity tier (ExecutionOS Lite system)."""
    if not report.primary:
        return "LIGHT"

    non_secondary = [s for s in [report.primary] + report.secondary if not s.secondary]
    secondary_count = len([s for s in report.secondary if s.secondary])

    if len(non_secondary) >= 3:
        return "FORENSIC"
    elif len(non_secondary) >= 2 or (len(non_secondary) == 1 and secondary_count >= 2):
        return "DEEP"
    elif report.primary.framework:
        return "STANDARD"
    else:
        return "LIGHT"


def generate_manifest(
    repo_path: Path,
    report: TechStackReport,
    tech_rules: dict,
    reconciliation: list[ReconciliationResult],
) -> Path:
    """Phase 4: Generate .kobiiclaw_manifest.yml."""
    now = datetime.now(timezone.utc).isoformat()
    tier = _classify_tier(report)

    # Build primary stack info
    primary_info = {}
    if report.primary:
        primary_info = {
            "language": report.primary.language,
            "version": report.primary.version,
            "build_system": report.primary.build_system,
            "framework": report.primary.framework,
            "confidence": report.primary.confidence,
        }

    secondary_info = []
    for s in report.secondary:
        secondary_info.append({
            "language": s.language,
            "build_system": s.build_system,
            "framework": s.framework,
            "confidence": s.confidence,
            "purpose": "secondary" if s.secondary else "additional",
        })

    # Find telemetry adapter from reconciliation
    telemetry_adapter = "generic"
    for r in reconciliation:
        if r.rule_id == "TELEMETRY":
            telemetry_adapter = r.implementation.replace("adapter=", "")

    manifest = {
        "# Auto-generated by KobiiClaw Init Engine": None,
        "project": {
            "name": repo_path.name,
            "path": str(repo_path),
            "complexity_tier": tier,
            "scanned_at": now,
            "scan_duration_ms": report.scan_duration_ms,
            "files_scanned": report.total_files_scanned,
        },
        "tech_stack": {
            "primary": primary_info,
            "secondary": secondary_info,
        },
        "commands": tech_rules.get("commands", {}),
        "logs": tech_rules.get("logs", {}),
        "recovery": tech_rules.get("recovery", {}),
        "health_check": tech_rules.get("health_check", {}),
        "telemetry": {
            "adapter": telemetry_adapter,
            "omnicapture_project_id": repo_path.name.lower().replace(" ", "-"),
            "error_severity_map": tech_rules.get("telemetry", {}).get("error_severity_map", {}),
        },
        "hot_swap": tech_rules.get("hot_swap", {}),
        "dependencies": tech_rules.get("dependencies", {}),
        "reconciliation_log": [
            {
                "rule": r.rule_id,
                "implementation": r.implementation,
                "mutations": r.mutations,
                "confidence": r.confidence,
            }
            for r in reconciliation
        ],
    }

    # Remove the comment key (YAML handles it differently)
    manifest.pop("# Auto-generated by KobiiClaw Init Engine", None)

    # Write to repo root (atomic)
    manifest_path = repo_path / ".kobiiclaw_manifest.yml"
    _atomic_write_yaml(manifest_path, manifest, header=f"# Auto-generated by KobiiClaw Init Engine v1.0\n# Repo: {repo_path.name}\n# Scanned: {now}\n# Tier: {tier}\n")

    # Cache copy
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = MANIFESTS_DIR / f"{repo_path.name}_manifest.yml"
    _atomic_write_yaml(cache_path, manifest)

    logger.info(f"Manifest written: {manifest_path}")
    return manifest_path


def _atomic_write_yaml(path: Path, data: dict, header: str = "") -> None:
    """Write YAML atomically via tempfile + rename."""
    content = header + yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


# ── Git HEAD Check (Idempotency) ──────────────────────────────────────────

def _get_git_head(repo_path: Path) -> str | None:
    """Get current git HEAD SHA for idempotency check."""
    head_file = repo_path / ".git" / "HEAD"
    if not head_file.exists():
        return None
    try:
        ref = head_file.read_text(encoding="utf-8").strip()
        if ref.startswith("ref: "):
            ref_path = repo_path / ".git" / ref[5:]
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8").strip()[:12]
        return ref[:12]
    except OSError:
        return None


def _should_rescan(repo_path: Path, manifest_path: Path) -> bool:
    """Check if repo has changed since last manifest generation."""
    if not manifest_path.exists():
        return True

    current_head = _get_git_head(repo_path)
    if not current_head:
        return True  # Not a git repo, always rescan

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Check if HEAD is embedded in manifest comments
        if current_head in content:
            return False  # Same HEAD, no rescan needed
    except OSError:
        pass
    return True


# ── Main Entry Point ───────────────────────────────────────────────────────

def init(
    repo_path_str: str,
    deep: bool = False,
    force: bool = False,
) -> InitResult:
    """Main entry point. Returns structured InitResult."""
    start = time.monotonic()
    repo_path = Path(repo_path_str).resolve()

    # Validation
    if not repo_path.is_dir():
        return InitResult(success=False, error=f"Not a directory: {repo_path}")

    # Idempotency check
    manifest_path = repo_path / ".kobiiclaw_manifest.yml"
    if not force and manifest_path.exists():
        if not _should_rescan(repo_path, manifest_path):
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(f"Manifest up-to-date. Use --force to regenerate. ({duration_ms}ms)")
            return InitResult(
                success=True,
                manifest_path=str(manifest_path),
                duration_ms=duration_ms,
            )

    gaps = []

    # Phase 1: Introspection
    logger.info(f"Phase 1: Scanning {repo_path}...")
    fingerprints = load_fingerprints()
    report = scan_repo(repo_path, fingerprints)

    if not report.primary:
        gaps.append("No tech stack detected. Using generic rules.")
        logger.warning(gaps[-1])

    # Phase 2: Self-Education
    logger.info(f"Phase 2: Loading tech rules for {report.primary.language if report.primary else 'unknown'}...")
    tech_rules = load_tech_rules(report, deep=deep)

    # Phase 3: Reconciliation
    logger.info("Phase 3: Reconciling universal rules...")
    universal = load_universal_rules()
    reconciliation = reconcile_rules(universal, tech_rules, report)

    for r in reconciliation:
        if r.mutations:
            for m in r.mutations:
                logger.info(f"  Mutation [{r.rule_id}]: {m}")
        if r.confidence < 0.5:
            gaps.append(f"Low confidence for {r.rule_id}: {r.confidence}")

    # Phase 4: Manifest Generation
    logger.info("Phase 4: Generating manifest...")
    output_path = generate_manifest(repo_path, report, tech_rules, reconciliation)

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(f"Init complete in {duration_ms}ms. Manifest: {output_path}")

    return InitResult(
        success=True,
        manifest_path=str(output_path),
        report=asdict(report) if report.primary else None,
        reconciliation=[asdict(r) for r in reconciliation],
        gaps=gaps,
        duration_ms=duration_ms,
    )


# ── CLI ────────────────────────────────────────────────────────────────────

def _format_human(result: InitResult) -> str:
    """Format result for human-readable output."""
    lines = []
    lines.append("=" * 60)
    lines.append("KobiiClaw Init Engine — Results")
    lines.append("=" * 60)

    if not result.success:
        lines.append(f"FAILED: {result.error}")
        return "\n".join(lines)

    lines.append(f"Manifest: {result.manifest_path}")
    lines.append(f"Duration: {result.duration_ms}ms")

    if result.report:
        p = result.report.get("primary")
        if p:
            lines.append("")
            lines.append(f"Primary Stack: {p['language']} ({p['build_system']})")
            if p.get("framework"):
                lines.append(f"  Framework: {p['framework']}")
            if p.get("version"):
                lines.append(f"  Version: {p['version']}")
            lines.append(f"  Confidence: {p['confidence']}")

        sec = result.report.get("secondary", [])
        if sec:
            lines.append(f"Secondary: {', '.join(s['language'] for s in sec)}")

        lines.append(f"Files scanned: {result.report.get('total_files_scanned', 0)}")

    if result.reconciliation:
        lines.append("")
        lines.append("Reconciliation:")
        for r in result.reconciliation:
            status = "OK" if r["confidence"] >= 0.7 else "LOW"
            lines.append(f"  [{status}] {r['rule_id']}: {r['implementation'][:60]}")
            for m in r.get("mutations", []):
                lines.append(f"       Mutation: {m}")

    if result.gaps:
        lines.append("")
        lines.append("Gaps:")
        for g in result.gaps:
            lines.append(f"  - {g}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="KobiiClaw Init Engine")
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("--deep", action="store_true", help="Force RAG for tech rules")
    parser.add_argument("--force", action="store_true", help="Regenerate even if manifest exists")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    result = init(args.repo_path, deep=args.deep, force=args.force)

    if args.json:
        print(json.dumps(asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__, indent=2, default=str))
    else:
        print(_format_human(result))

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
