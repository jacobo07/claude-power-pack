#!/usr/bin/env python3
"""forensic_probes.py — OVO Phase B+ runtime probe library (MC-OVO-101).

Three probes that close the gap between "delta is statically clean" and
"system actually works under load":

  * RLP  (Runtime Liveness Probe)        — reads _audit_cache/runtime_probe.jsonl
  * AFHL (Anti-Fragility Hack Ledger)    — reads vault/anti_fragility/hacks.jsonl
  * CGAR (Cascade Graph + Adversarial Replay, blast-radius only this MC)
                                         — reads vault/audits/cascade_graph.json

Honest contract — every probe returns one of three states:
  CONFIGURED + clean      → no findings, no verdict cap
  CONFIGURED + findings[] → caps verdict at B (REJECT for core/critical)
  NOT_CONFIGURED          → advisory; never claims PASS, never caps

Usage:
  python tools/forensic_probes.py --project . --probe all --json
  python tools/forensic_probes.py --project . --probe rlp
  python tools/forensic_probes.py --project . --probe afhl --delta-paths "lib/x.js,src/y.py"

Exit codes: 0 ok, 2 argv error.

Schemas:
  vault/forensic/RLP_SCHEMA.md
  vault/forensic/AFHL_SCHEMA.md
  vault/forensic/CGAR_SCHEMA.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Common types
# ---------------------------------------------------------------------------

VALID_PROBES = ("rlp", "afhl", "cgar", "all")
STATE_CONFIGURED = "CONFIGURED"
STATE_NOT_CONFIGURED = "NOT_CONFIGURED"
VERDICT_CAPS = ("none", "B", "REJECT")


@dataclass
class ProbeResult:
    probe: str
    state: str
    verdict_cap: str = "none"
    findings: list[str] = field(default_factory=list)
    advisory: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# RLP — Runtime Liveness Probe
# ---------------------------------------------------------------------------

RLP_DEFAULT_REJECT_BELOW = 0.10
RLP_DEFAULT_B_BELOW = 0.50
RLP_DEFAULT_WARN_BELOW = 0.80
RLP_SUSTAINED_DEGRADATION_SAMPLES = 10


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        try:
            out.append(json.loads(s))
        except json.JSONDecodeError:
            # Tolerate malformed lines (don't crash the probe), but flag.
            out.append({"_malformed": True, "_raw": s[:200]})
    return out


def _rlp_thresholds(project: Path) -> dict:
    p = project / "_audit_cache" / "rlp_thresholds.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _rlp_classify(value: float, baseline: float, direction: str,
                  thresholds: dict) -> tuple[str, str]:
    """Return (severity, reason). severity ∈ {ok, warn, b, reject}."""
    if baseline == 0:
        return "ok", "baseline=0 (cannot classify)"
    reject_below = thresholds.get("reject_below", RLP_DEFAULT_REJECT_BELOW)
    b_below = thresholds.get("b_below", RLP_DEFAULT_B_BELOW)
    warn_below = thresholds.get("warn_below", RLP_DEFAULT_WARN_BELOW)
    if direction == "lower_is_better":
        ratio = baseline / value if value > 0 else float("inf")
    else:
        ratio = value / baseline
    if ratio < reject_below:
        return "reject", f"value={value} ratio={ratio:.2f} < reject_below={reject_below}"
    if ratio < b_below:
        return "b", f"value={value} ratio={ratio:.2f} < b_below={b_below}"
    if ratio < warn_below:
        return "warn", f"value={value} ratio={ratio:.2f} < warn_below={warn_below}"
    return "ok", f"value={value} ratio={ratio:.2f}"


def _rlp_direction(metric: str, threshold_block: dict) -> str:
    """Infer direction from threshold or metric naming."""
    if "direction" in threshold_block:
        return threshold_block["direction"]
    lower_is_better_hints = ("ms", "latency", "lag", "rss", "mem", "errors",
                             "p50", "p95", "p99", "queue_depth")
    return "lower_is_better" if any(h in metric for h in lower_is_better_hints) else "higher_is_better"


def rlp_check(project: Path) -> ProbeResult:
    probe_file = project / "_audit_cache" / "runtime_probe.jsonl"
    if not probe_file.exists():
        return ProbeResult(
            probe="rlp",
            state=STATE_NOT_CONFIGURED,
            advisory=("No _audit_cache/runtime_probe.jsonl — RLP cannot affirm "
                      "runtime health. Project has not opted into liveness probing."),
        )
    samples = _read_jsonl(probe_file)
    if not samples:
        return ProbeResult(
            probe="rlp",
            state=STATE_NOT_CONFIGURED,
            advisory="runtime_probe.jsonl exists but is empty.",
        )

    thresholds_all = _rlp_thresholds(project)
    findings: list[str] = []
    cap = "none"

    # Group by (probe_id, metric), inspect last 10 of each.
    groups: dict[tuple[str, str], list[dict]] = {}
    for s in samples:
        if s.get("_malformed"):
            findings.append(f"malformed sample line: {s.get('_raw','')[:80]}")
            cap = "B"
            continue
        key = (s.get("probe_id", "?"), s.get("metric", "?"))
        groups.setdefault(key, []).append(s)

    for (probe_id, metric), entries in groups.items():
        recent = entries[-RLP_SUSTAINED_DEGRADATION_SAMPLES:]
        threshold_key = f"{probe_id}:{metric}"
        threshold_block = thresholds_all.get(threshold_key, {})
        direction = _rlp_direction(metric, threshold_block)

        per_sample_severities = []
        for s in recent:
            try:
                value = float(s["value"])
                baseline = float(s["baseline"])
            except (KeyError, TypeError, ValueError):
                findings.append(f"{probe_id}:{metric} — sample missing value/baseline")
                cap = "B"
                continue
            severity, reason = _rlp_classify(value, baseline, direction, threshold_block)
            per_sample_severities.append(severity)
            if severity == "reject":
                findings.append(f"{probe_id}:{metric} REJECT — {reason}")
                cap = "REJECT"
            elif severity == "b" and cap != "REJECT":
                findings.append(f"{probe_id}:{metric} B — {reason}")
                cap = "B"

        # Sustained degradation rule
        if (len(per_sample_severities) >= RLP_SUSTAINED_DEGRADATION_SAMPLES
                and all(s in ("warn", "b", "reject") for s in per_sample_severities)
                and cap == "none"):
            findings.append(
                f"{probe_id}:{metric} B — sustained degradation across "
                f"{RLP_SUSTAINED_DEGRADATION_SAMPLES} samples"
            )
            cap = "B"

    return ProbeResult(
        probe="rlp",
        state=STATE_CONFIGURED,
        verdict_cap=cap,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# AFHL — Anti-Fragility Hack Ledger
# ---------------------------------------------------------------------------

AFHL_REQUIRED_FIELDS = ("hack_id", "added", "file", "upstream",
                        "upstream_version_range", "upstream_bug_url",
                        "reason", "validates_via")


def afhl_check(project: Path, delta_paths: list[str]) -> ProbeResult:
    ledger = project / "vault" / "anti_fragility" / "hacks.jsonl"
    if not ledger.exists():
        return ProbeResult(
            probe="afhl",
            state=STATE_NOT_CONFIGURED,
            advisory=("No vault/anti_fragility/hacks.jsonl — AFHL cannot detect "
                      "drift in non-canonical stabilizers."),
        )
    entries = _read_jsonl(ledger)
    # Filter the schema-marker first line if present.
    real_entries = [e for e in entries if "_schema" not in e and not e.get("_malformed")]

    findings: list[str] = []
    cap = "none"
    delta_set = {p.replace("\\", "/") for p in delta_paths}

    for entry in real_entries:
        missing = [f for f in AFHL_REQUIRED_FIELDS if f not in entry]
        if missing:
            findings.append(
                f"hack_id={entry.get('hack_id','?')} missing fields: {missing}"
            )
            cap = "B"
            continue
        hack_path = entry["file"].replace("\\", "/")
        if hack_path in delta_set:
            last_revalidated = entry.get("last_revalidated", "")
            findings.append(
                f"hack_id={entry['hack_id']} touched by delta ({hack_path}) — "
                f"last_revalidated={last_revalidated or 'NEVER'}; "
                f"upstream={entry['upstream']} {entry['upstream_version_range']}; "
                f"validates_via={entry['validates_via']}"
            )
            cap = "B"

    return ProbeResult(
        probe="afhl",
        state=STATE_CONFIGURED,
        verdict_cap=cap,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# CGAR — Cascade Graph (blast-radius only; replay deferred)
# ---------------------------------------------------------------------------

CGAR_CORE_CRITICALITY = ("core", "high")
CGAR_TRANSITIVE_THRESHOLD = 50


def cgar_check(project: Path, delta_paths: list[str]) -> ProbeResult:
    graph_path = project / "vault" / "audits" / "cascade_graph.json"
    if not graph_path.exists():
        return ProbeResult(
            probe="cgar",
            state=STATE_NOT_CONFIGURED,
            advisory="No vault/audits/cascade_graph.json — CGAR cannot compute blast radius.",
        )
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ProbeResult(
            probe="cgar",
            state=STATE_CONFIGURED,
            verdict_cap="B",
            findings=[f"cascade_graph.json is malformed: {exc}"],
        )

    schema = graph.get("schema", "")
    nodes = graph.get("nodes", [])
    if not schema.startswith("ovo-cascade-graph-v") or not nodes:
        return ProbeResult(
            probe="cgar",
            state=STATE_NOT_CONFIGURED,
            advisory=(
                f"cascade_graph.json present (schema={schema!r}) but no v2 nodes "
                f"populated yet. CGAR runs in NOT_CONFIGURED mode."
            ),
        )

    findings: list[str] = []
    cap = "none"
    delta_set = {p.replace("\\", "/") for p in delta_paths}

    for node in nodes:
        node_id = node.get("id", "").replace("\\", "/")
        if node_id not in delta_set:
            continue
        criticality = node.get("criticality", "low")
        kind = node.get("kind", "module")
        blast = node.get("blast_radius", {}) or {}
        transitive = int(blast.get("transitive_callers", 0) or 0)
        downstream = blast.get("downstream_systems", []) or []

        if kind == "migration":
            findings.append(
                f"{node_id} is a migration — REJECT unless reversibility "
                f"is explicit in the response"
            )
            cap = "REJECT"
            continue
        if criticality in CGAR_CORE_CRITICALITY:
            findings.append(
                f"{node_id} is criticality={criticality} — B unless each "
                f"downstream_system is addressed: {downstream}"
            )
            if cap != "REJECT":
                cap = "B"
            continue
        if transitive > CGAR_TRANSITIVE_THRESHOLD:
            findings.append(
                f"{node_id} transitive_callers={transitive} > "
                f"{CGAR_TRANSITIVE_THRESHOLD} — B unless adversarial replay clean"
            )
            if cap != "REJECT":
                cap = "B"

    return ProbeResult(
        probe="cgar",
        state=STATE_CONFIGURED,
        verdict_cap=cap,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Aggregation + CLI
# ---------------------------------------------------------------------------

def aggregate(results: list[ProbeResult]) -> dict:
    """Combine probe results into a single OVO-consumable verdict bundle."""
    cap_rank = {"none": 0, "B": 1, "REJECT": 2}
    overall = "none"
    for r in results:
        if cap_rank[r.verdict_cap] > cap_rank[overall]:
            overall = r.verdict_cap
    return {
        "overall_verdict_cap": overall,
        "probes": [r.to_dict() for r in results],
    }


def render_human(bundle: dict) -> str:
    lines = ["Forensic Probes — summary", "-" * 40]
    lines.append(f"Overall verdict cap: {bundle['overall_verdict_cap']}")
    for p in bundle["probes"]:
        lines.append("")
        lines.append(f"[{p['probe'].upper()}] state={p['state']} cap={p['verdict_cap']}")
        if p["advisory"]:
            lines.append(f"  advisory: {p['advisory']}")
        for f in p["findings"]:
            lines.append(f"  - {f}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="OVO forensic probes (RLP / AFHL / CGAR)"
    )
    parser.add_argument("--project", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    parser.add_argument("--probe", choices=VALID_PROBES, default="all",
                        help="Which probe to run (default: all)")
    parser.add_argument("--delta-paths", default="",
                        help="Comma-separated relative paths from the OVO delta "
                             "(consumed by AFHL/CGAR). Empty = no delta context.")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of human text")
    args = parser.parse_args(argv[1:])

    project = args.project.resolve()
    if not project.exists() or not project.is_dir():
        print(f"forensic_probes.py: project not a directory: {project}",
              file=sys.stderr)
        return 2

    delta_paths = [p.strip() for p in args.delta_paths.split(",") if p.strip()]

    runners = {
        "rlp": lambda: rlp_check(project),
        "afhl": lambda: afhl_check(project, delta_paths),
        "cgar": lambda: cgar_check(project, delta_paths),
    }
    if args.probe == "all":
        results = [runners[p]() for p in ("rlp", "afhl", "cgar")]
    else:
        results = [runners[args.probe]()]

    bundle = aggregate(results)
    if args.json:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    else:
        print(render_human(bundle))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
