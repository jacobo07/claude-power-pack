"""tools/run_sqi.py — the SQI unified runner.

Runs the three engines in dependency order and writes a durable, citable artifact:

    scan_repo   ->  what is on the disk
    qualify     ->  may any result from this host be interpreted at all
    reconcile   ->  what fraction of authored protection is actually reached

The artifact matters as much as the numbers. SQI-02 Part VI names six stages in the reach
chain, and the sixth -- passed -> evidence-producing -- is the one NO repository in the
founding audit instrumented. A pass that leaves no durable artifact has protected the code
on exactly one occasion, for exactly one observer, and has contributed nothing to the
estate's memory. Nothing downstream can compare against a terminal buffer. So this runner
writes `vault/audits/sqi_report_<date>.md` and a JSON sidecar, and the sidecar is what a
baseline guardian will diff tomorrow.

Each layer is independently fail-open: a failure in one does not cancel the others, and a
layer that cannot run reports UNKNOWN rather than a zero.

    python tools/run_sqi.py [path]        default: the repository containing this file
    python tools/run_sqi.py --quiet       write the artifacts, print only the verdict line
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.sqi.repo_reality_scanner import scan_repo
from modules.sqi.environment_qualifier import qualify, QUALIFIED, PARTIALLY_QUALIFIED
from modules.sqi.reconcile import reconcile
from modules.sqi import baseline_guardian as guardian

HERMETIC_RUNS = 3  # the estate's own standard: three runs from a clean state, same result


def _audit_dir() -> Path:
    """Overridable via SQI_AUDIT_DIR. The done-gate exercises this runner end-to-end, and a gate
    that writes to the repository's real audit directory would overwrite the very artifact it is
    validating -- a global write, which is the classic way a suite stops being hermetic and
    starts failing on its own second run."""
    override = os.environ.get("SQI_AUDIT_DIR")
    return Path(override) if override else ROOT / "vault" / "audits"


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)  # a redirected audit dir lives outside the repo


def _pct(x: float | None) -> str:
    return "UNKNOWN" if x is None else f"{x * 100:.1f}%"


def _flag(argv: list[str], name: str) -> str:
    """`--reason "..."` / `--author "..."`. Both are needed to LOWER a baseline, and neither has
    a default, because an unattributed acceptance is exactly the escape the firewall exists to
    prevent (§12.7)."""
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
    return ""


def _render(profile, env, rep, verdict, target: Path, stamp: str) -> str:
    L: list[str] = []
    A = L.append

    A(f"# SQI Report — {rep.repo}")
    A("")
    A(f"> Generated {stamp} by `tools/run_sqi.py`. Commit `{rep.commit[:8]}`.")
    A("> The executable layer of the SQI corpus. Doctrine: `vault/knowledge_base/sqi/`.")
    A("")

    # The headline is deliberately the loss, not the reach. Nobody remediates a
    # percentage; people remediate a list of paths (SQI-02 8.10).
    A("## Verdict")
    A("")
    A(f"- **Baseline guardian:** `{verdict.verdict}`"
      + ("  ← **THE BUILD FAILS**" if verdict.failing else ""))
    A(f"- **Signal integrity:** `{rep.signal_integrity_verdict}` → ontology "
      f"`{rep.ontology_verdict}`")
    A(f"- **Environment:** `{env.state}` — verdict ceiling: {env.verdict_ceiling}")
    A(f"- **Reach under the authoritative invocation:** `{rep.authoritative_reach_state}`")
    A(f"- **Orphaned test files:** **{rep.orphaned_count}** of {rep.authored_count} authored")
    A("")

    A("## Baseline guardian (SQI-02 Part XII)")
    A("")
    A(verdict.summary)
    A("")
    if verdict.regressions:
        A("Increases are free. A **decrease fails the build** — and the identities of what "
          "vanished are named, because a delta of three is an alarm and three names are an "
          "action (§12.5).")
        A("")
        A("| gate | root | baseline | observed | lost |")
        A("|---|---|---|---|---|")
        for r in verdict.regressions:
            A(f"| `{r.gate}` | `{r.root}` | {r.baseline} | {r.observed} | "
              f"{len(r.lost_identities)} |")
        A("")
        for r in verdict.regressions:
            A(f"**`{r.gate}` @ `{r.root}`** — {r.note}")
            A("")
            for i in r.lost_identities[:25]:
                A(f"- lost: `{i}`")
            if len(r.lost_identities) > 25:
                A(f"- … and {len(r.lost_identities) - 25} more")
            A("")
        A("A decrease **never** auto-updates the baseline. Lowering it requires a separate, "
          "attributed act — `run_sqi.py --accept-baseline --reason \"…\" --author \"…\"` — "
          "because the party whose change caused the decrease may not, in the same task, author "
          "the update that permits it (§12.7). The guardian does not prevent deletion; it "
          "prevents deletion from being **invisible**.")
        A("")
    else:
        A(f"Baseline: `{Path(verdict.baseline_path).name}` · environment "
          f"`{verdict.baseline_env}` · ratcheted this run: {verdict.updated}")
        A("")

    if rep.findings:
        A("## Findings")
        A("")
        for f in rep.findings:
            first, _, rest = f.partition("\n")
            A(f"- {first}")
            if rest.strip():
                A("")
                A("  ```")
                for line in rest.strip().splitlines():
                    A(f"  {line}")
                A("  ```")
        A("")

    A("## 1. Repository reality (SQI-01)")
    A("")
    A(f"- Languages: {', '.join(c.language for c in profile.language_contexts) or 'none'}")
    A(f"- Domains: {', '.join(profile.domains)}")
    A(f"- Lock state: " + ", ".join(
        f"{c.language}={c.lock_state}" for c in profile.language_contexts) or "n/a")
    A(f"- Authored test artifacts: {len(profile.test_artifacts)}")
    A(f"- Discovery rule hits: `{json.dumps(profile.per_rule_hits)}`")
    A(f"- **Engine uncertainty:** {profile.uncertainty_count} files matched no rule but "
      f"live where tests live")
    A("")

    A("## 2. Environment qualification (SQI-03)")
    A("")
    A("| gate | result | observed |")
    A("|---|---|---|")
    for g in env.gates:
        mark = {True: "PASS", False: "**FAIL**", None: "UNKNOWN"}[g.passed]
        obs = (g.observed or "").replace("|", r"\|")[:90]
        A(f"| `{g.gate}` | {mark} | {obs} |")
    A("")
    if env.blockers:
        A("Blockers (verbatim):")
        A("")
        A("```")
        for b in env.blockers:
            A(b)
        A("```")
        A("")

    A("## 3. Test reach reconciliation (SQI-02)")
    A("")
    A("### Canonical invocation set")
    A("")
    A("| oracle | command | authoritative | status | exit | files | cases | verdict |")
    A("|---|---|---|---|---|---|---|---|")
    for i in rep.invocations:
        A(f"| {i.oracle} | `{i.command}` | {'**yes**' if i.authoritative else 'no'} | "
          f"`{i.status}` | {i.exit_code} | {len(i.executed_files)} | "
          f"{i.executed_cases if i.executed_cases is not None else 'UNKNOWN'} | "
          f"`{i.verdict}` |")
    A("")
    A("Precedence (SQI-02 §9.4): a CI job is authoritative where one exists, because it is "
      "the only oracle backed by an observation rather than an intention. Where none "
      "exists, the zero-argument default is authoritative — it is what a human, a hook, or "
      "an agent with no prior context will actually type. **Documentation is never "
      "authoritative.**")
    A("")

    A("### Metrics")
    A("")
    A("| metric | value |")
    A("|---|---|")
    A(f"| Test File Reach | {_pct(rep.test_file_reach)} ({len(rep.reached_files)}/{rep.authored_count}) |")
    A(f"| Test Case Reach | {_pct(rep.test_case_reach)} |")
    A(f"| Suite Activation Ratio | {_pct(rep.suite_activation_ratio)} |")
    A(f"| **Orphaned Test Count** | **{rep.orphaned_count}** (absolute) |")
    A(f"| Orphaned Ratio | {_pct(rep.orphaned_ratio)} |")
    A(f"| Silent Collection Loss | {rep.silent_collection_loss} |")
    A(f"| Executed Protection Ratio | {_pct(rep.executed_protection_ratio)} |")
    A(f"| Surprise set (self-audit) | {len(rep.surprise_files)} |")
    A(f"| Hermetic runs | {rep.hermetic_runs} → stable: {rep.hermetic_stable} |")
    A("")
    A("Test Case Reach is `UNKNOWN` and is not estimated. Establishing it requires parsing "
      "every orphaned file, which nothing in this pipeline has ever done. **The unknown is "
      "the finding** (SQI-02 §7.6): a repository that cannot state how many cases it has "
      "authored cannot compute the metric that would tell it how many are protecting "
      "anything, and an engine that filled the gap with an estimate would manufacture the "
      "exact false confidence it exists to destroy.")
    A("")

    A("### Self-reach (mandatory — SQI-02 §5.10)")
    A("")
    A(f"- Engine: `{rep.self_reach['engine']}` · reached: **{rep.self_reach['reached']}** · "
      f"report admissible: **{rep.self_reach['admissible']}**")
    for p in rep.self_reach.get("reached_by", []):
        A(f"- exercised by `{p}`")
    A("")
    A("*An auditor exempt from its own audit is not an auditor.* A report without a "
      "positive self-reach assertion is inadmissible.")
    A("")

    A(f"### Unprotected surface ({len(rep.unprotected_surface)} elements)")
    A("")
    A("Module packages with **zero references from any test the canonical invocation "
      "reaches**. This is the only metric here whose denominator is risk rather than tests "
      "(SQI-02 §8.6) — the metric that catches a green suite standing beside an "
      "unprotected surface.")
    A("")
    for s in rep.unprotected_surface:
        A(f"- `modules/{s}`")
    A("")

    A(f"### Orphaned test files ({rep.orphaned_count})")
    A("")
    A("The list, not the percentage. A reader shown 98 paths reacts differently from a "
      "reader shown a percentage, and the difference in reaction is the entire point of "
      "publishing it (SQI-02 §8.2).")
    A("")
    for p in rep.orphaned_files:
        A(f"- `{p}`")
    A("")

    A("## Reproduce")
    A("")
    A("```")
    A("python tools/run_sqi.py")
    A("```")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    args = [a for a in argv if not a.startswith("--")]
    target = Path(args[0]).resolve() if args else ROOT

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Layer 1 — reality. Fail-open: a scan that cannot run yields a profile of unknowns.
    try:
        profile = scan_repo(target)
    except Exception:  # noqa: BLE001 - a crashed layer must not cancel the others
        print("SQI: reality scanner crashed\n" + traceback.format_exc(), file=sys.stderr)
        return 1

    # Layer 2 — qualification. Never raises by contract.
    try:
        env = qualify(target, profile=profile)
    except Exception:  # noqa: BLE001
        print("SQI: environment qualifier crashed\n" + traceback.format_exc(), file=sys.stderr)
        return 1

    # Layer 3 — reconciliation. The verdict ceiling from layer 2 is an INPUT here: a result
    # from an unqualified environment may not be interpreted as a product fact (SQI-03 4.9).
    try:
        rep = reconcile(
            target,
            hermetic_runs=HERMETIC_RUNS,
            env_qualified=env.state in (QUALIFIED, PARTIALLY_QUALIFIED),
        )
    except Exception:  # noqa: BLE001
        print("SQI: reconciliation engine crashed\n" + traceback.format_exc(), file=sys.stderr)
        return 1

    # Layer 4 -- the guardian. The three layers above measure a STATE; this measures the
    # DERIVATIVE, and it is the only one of the four that can REFUSE. Until it existed, the
    # reach figure trended in a report that nothing consumed -- and a quality signal that is
    # emitted and never read is functionally identical to one that was never computed (§8.4).
    try:
        verdict = guardian.check(
            rep,
            env.env_hash,
            repo=target,
            accept="--accept-baseline" in argv,
            reason=_flag(argv, "--reason"),
            author=_flag(argv, "--author"),
        )
    except Exception:  # noqa: BLE001 -- a crashed guardian is UNKNOWN, never a silent pass
        verdict = guardian.GuardianVerdict(
            verdict=guardian.UNKNOWN, regressions=[], baseline_env=None,
            observed_env=env.env_hash, updated=False, baseline_path="",
            summary="guardian crashed", error=traceback.format_exc(limit=3),
        )

    audit_dir = _audit_dir()
    audit_dir.mkdir(parents=True, exist_ok=True)
    md_path = audit_dir / f"sqi_report_{date}.md"
    json_path = audit_dir / f"sqi_report_{date}.json"

    md_path.write_text(_render(profile, env, rep, verdict, target, stamp), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "generated": stamp,
                "reality": profile.to_dict(),
                "environment": env.to_dict(),
                "reconciliation": rep.to_dict(),
                "guardian": verdict.to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # CO-12 telemetry. The sink already accepts an arbitrary signal kind, so SQI extends it
    # rather than forking a second telemetry bus -- T-SQI-PARALLEL-SYSTEM-001. Fail-open
    # ABSOLUTE: a telemetry write must never break the measurement it describes.
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal

        record_signal(
            "sqi_reconcile",
            {
                "repo": rep.repo,
                "commit": rep.commit[:8],
                "sqi_orphaned_ratio": rep.orphaned_ratio,
                "sqi_test_file_reach": rep.test_file_reach,
                "sqi_orphaned_count": rep.orphaned_count,
                "sqi_authored_count": rep.authored_count,
                "sqi_signal_integrity": rep.signal_integrity_verdict,
                "sqi_authoritative_reach": rep.authoritative_reach_state,
                "sqi_self_reach": rep.self_reach["reached"],
                "sqi_environment": env.state,
                "sqi_unprotected_surface": len(rep.unprotected_surface),
            },
        )
    except Exception:  # noqa: BLE001 -- telemetry is never load-bearing
        pass

    if not quiet:
        print(f"SQI report -> {_rel(md_path)}")
        print(f"SQI sidecar -> {_rel(json_path)}")
        print()
        for f in rep.findings:
            print("FINDING:", f.splitlines()[0])
        print()

    if not quiet and verdict.regressions:
        print()
        for r in verdict.regressions:
            print(f"REGRESSION [{r.gate}] {r.root}: {r.baseline} -> {r.observed}")
            for i in r.lost_identities[:10]:
                print(f"    lost: {i}")
            if len(r.lost_identities) > 10:
                print(f"    ... and {len(r.lost_identities) - 10} more")
        print()

    print(
        f"SQI_VERDICT={rep.signal_integrity_verdict} "
        f"ontology={rep.ontology_verdict} "
        f"env={env.state} "
        f"reach={_pct(rep.test_file_reach)} "
        f"orphaned={rep.orphaned_count}/{rep.authored_count} "
        f"authoritative_reach={rep.authoritative_reach_state} "
        f"self_reach={rep.self_reach['reached']} "
        f"guardian={verdict.verdict}"
    )
    print(f"SQI_GUARDIAN: {verdict.summary}")

    # The exit code is where measuring becomes gating. It is NOT a pass/fail on the LEVEL of
    # reach -- gating a level would fail every honest repository forever. It gates the
    # DERIVATIVE: an unexplained decrease, and nothing else (§12.2). An inadmissible report
    # (the auditor exempt from its own audit) also refuses, at a distinct code.
    if verdict.failing:
        return 1
    return 0 if rep.self_reach["admissible"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
