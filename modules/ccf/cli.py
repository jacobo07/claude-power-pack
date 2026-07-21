"""cpp creative -- CCF CLI (component #4/S4-B), per vault/plans/CCF_CLI_SPEC.md.

Exit codes (per the CCF build order): 0=success, 1=validation_error,
2=provider_error, 3=gate_blocked, 4=human_required. Every subcommand wires
directly to a real CCF component -- no subcommand is decorative.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

from modules.ccf import (
    artifact_compiler,
    config_schema,
    contract_engine,
    evaluation_engine,
    model_adapter,
    prompt_compiler,
    release_manager,
    trademark_scanner,
)

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_PROVIDER_ERROR = 2
EXIT_GATE_BLOCKED = 3
EXIT_HUMAN_REQUIRED = 4


def _paths(project: str) -> dict:
    ccf_dir = os.path.join(project, ".ccf")
    return {
        "root": project,
        "config": os.path.join(project, "config.json"),
        "spec": os.path.join(project, "spec.json"),
        "ccf_dir": ccf_dir,
        "prompts": os.path.join(ccf_dir, "prompts.json"),
        "scan_report": os.path.join(ccf_dir, "scan_report.json"),
        "image_artifacts": os.path.join(ccf_dir, "image_artifacts.json"),
        "selection": os.path.join(ccf_dir, "selection.json"),
        "human_acks": os.path.join(ccf_dir, "human_acks.json"),
        "evaluation_report": os.path.join(ccf_dir, "evaluation_report.json"),
        "releases_dir": os.path.join(ccf_dir, "releases"),
        "showcase_html": os.path.join(project, "showcase.html"),
        "showcase_pdf": os.path.join(project, "showcase.pdf"),
        "brandkit_html": os.path.join(project, "brandkit.html"),
        "brandkit_pdf": os.path.join(project, "brandkit.pdf"),
    }


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, sort_keys=True)


def _artifact_to_record(artifact) -> dict:
    return {
        "status": artifact.status,
        "provider": artifact.provider,
        "model_id": artifact.model_id,
        "format": artifact.format,
        "resolution": artifact.resolution,
        "latency_ms": artifact.latency_ms,
        "request_id": artifact.request_id,
        "error_detail": artifact.error_detail,
    }


class _ArtifactRecordView:
    """Lightweight re-hydration of a persisted artifact record so
    artifact_compiler (which only reads `.status`) can consume it without
    the CLI depending on the raw ImageArtifact dataclass across a JSON
    round-trip.
    """

    def __init__(self, record: dict):
        self.status = record.get("status")


def cmd_init(args) -> int:
    project = args.project
    paths = _paths(project)
    if args.dry_run:
        print(f"[dry-run] would create {project}/ with config.json and spec.json")
        return EXIT_OK

    if os.path.exists(project) and os.listdir(project):
        print(f"error: project directory {project!r} already exists and is non-empty")
        return EXIT_VALIDATION_ERROR

    os.makedirs(paths["ccf_dir"], exist_ok=True)
    _save_json(paths["config"], config_schema.default_config())

    if args.brief:
        with open(args.brief, "r", encoding="utf-8") as handle:
            brief_text = handle.read()
        spec, questions = contract_engine.compile_spec(brief_text)
        if questions:
            _save_json(paths["spec"], {})
            print(json.dumps({"questions": questions}, indent=2))
            return EXIT_HUMAN_REQUIRED
        _save_json(paths["spec"], spec.to_dict())
    else:
        _save_json(paths["spec"], {})

    print(f"initialized CCF project at {project}")
    return EXIT_OK


def cmd_compile(args) -> int:
    paths = _paths(args.project)
    brief_text = sys.stdin.read() if args.brief == "-" else open(args.brief, encoding="utf-8").read()
    answers = _load_json(args.answers) if args.answers else None

    spec, questions = contract_engine.compile_spec(brief_text, extra_answers=answers)
    if questions:
        print(json.dumps({"questions": questions}, indent=2))
        return EXIT_HUMAN_REQUIRED

    _save_json(paths["spec"], spec.to_dict())
    print(f"compiled Creative Specification for {spec.brand_name!r}")
    return EXIT_OK


def cmd_generate(args) -> int:
    paths = _paths(args.project)
    config, errors = config_schema.load_config(paths["config"])
    if config is None:
        for error in errors:
            print(f"error: {error}")
        return EXIT_VALIDATION_ERROR

    spec = _load_json(paths["spec"], {})
    global_fields = {k: config.get(k) for k in ("theme", "accent", "headFont", "labels")}
    concepts = config["concepts"]
    if args.only:
        concepts = [c for c in concepts if c["id"] == args.only]
        if not concepts:
            print(f"error: no concept with id {args.only!r}")
            return EXIT_VALIDATION_ERROR

    # Load existing state so a --only run updates just its own concepts
    # rather than wiping out every other concept's prior results -- an
    # empty-overwrite footgun in the same family as CCF-F02.
    prompts = _load_json(paths["prompts"], {})
    scan_report = _load_json(paths["scan_report"], {})
    artifact_records = _load_json(paths["image_artifacts"], {})
    any_block, any_provider_error = False, False
    adapter = model_adapter.GPTImage2Adapter()

    for concept in concepts:
        record = prompt_compiler.compile_prompt(concept, spec, global_fields)
        prompts[concept["id"]] = record
        verdict = trademark_scanner.scan(concept["id"], concept["icon"], record["avoid_list"]["semantic"])
        scan_report[concept["id"]] = verdict
        if verdict["verdict"] == "BLOCK":
            any_block = True

        if args.dry_run:
            print(f"[dry-run] {concept['id']}: {record['prompt']}")
            continue

        artifact = adapter.generate(record["prompt"], {})
        artifact_records[concept["id"]] = _artifact_to_record(artifact)
        if artifact.status != "OK":
            any_provider_error = True
            print(f"warning: generation failed for {concept['id']}: {artifact.error_detail}")

    if args.dry_run:
        # dry-run never persists state -- it only previews prompts, per
        # CCF_CLI_SPEC.md ("print the prompts, call nothing").
        return EXIT_OK

    _save_json(paths["prompts"], prompts)
    _save_json(paths["scan_report"], scan_report)
    _save_json(paths["image_artifacts"], artifact_records)

    image_artifact_views = {
        cid: _ArtifactRecordView(rec) for cid, rec in artifact_records.items()
    }
    bundle = artifact_compiler.compile_artifacts(concepts, image_artifact_views, mode="showcase")
    if bundle["built"]:
        with open(paths["showcase_html"], "w", encoding="utf-8") as handle:
            handle.write(bundle["html"])
        with open(paths["showcase_pdf"], "wb") as handle:
            handle.write(bundle["pdf_bytes"])
        print(f"showcase built: {len(bundle['included_ids'])} concept(s) included")
    for skip in bundle.get("skipped", []):
        print(f"skipped {skip['entry_id']}: {skip['reason']}")

    if any_block:
        return EXIT_GATE_BLOCKED
    if any_provider_error:
        return EXIT_PROVIDER_ERROR
    return EXIT_OK


def cmd_select(args) -> int:
    paths = _paths(args.project)
    scan_report = _load_json(paths["scan_report"], {})
    verdict_record = scan_report.get(args.concept)
    if verdict_record is None:
        print(f"error: concept {args.concept!r} was never scanned -- run generate first")
        return EXIT_VALIDATION_ERROR

    verdict = verdict_record["verdict"]
    if verdict == "BLOCK":
        print(f"error: concept {args.concept!r} has an un-cleared trademark BLOCK, cannot select")
        return EXIT_GATE_BLOCKED
    if verdict == "WARN" and not args.ack:
        print(
            f"human_required: concept {args.concept!r} has a WARN verdict "
            f"({verdict_record['justification']}); re-run with --ack to acknowledge"
        )
        return EXIT_HUMAN_REQUIRED

    human_acks = _load_json(paths["human_acks"], {})
    if verdict == "WARN" and args.ack:
        human_acks[args.concept] = True
        _save_json(paths["human_acks"], human_acks)

    selection = {
        "concept_id": args.concept,
        "by": args.by,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    _save_json(paths["selection"], selection)
    print(f"recorded selection: {args.concept!r} by {args.by!r}")
    return EXIT_OK


def cmd_package(args) -> int:
    paths = _paths(args.project)
    config, errors = config_schema.load_config(paths["config"])
    if config is None:
        for error in errors:
            print(f"error: {error}")
        return EXIT_VALIDATION_ERROR

    selection = _load_json(paths["selection"])
    if not selection:
        print("human_required: no concept selection recorded -- run `select` first")
        return EXIT_HUMAN_REQUIRED

    prompts = _load_json(paths["prompts"], {})
    scan_report = _load_json(paths["scan_report"], {})
    artifact_records = _load_json(paths["image_artifacts"], {})
    human_acks = _load_json(paths["human_acks"], {})

    selected_id = selection["concept_id"]
    selected_concept = next((c for c in config["concepts"] if c["id"] == selected_id), None)
    if selected_concept is None:
        print(f"error: selected concept {selected_id!r} not found in config")
        return EXIT_VALIDATION_ERROR

    image_artifact_views = {
        cid: _ArtifactRecordView(rec) for cid, rec in artifact_records.items()
    }
    bundle = artifact_compiler.compile_artifacts([selected_concept], image_artifact_views, mode="brandkit")
    evaluation = evaluation_engine.evaluate_bundle(bundle)

    if bundle["built"]:
        with open(paths["brandkit_html"], "w", encoding="utf-8") as handle:
            handle.write(bundle["html"])
        with open(paths["brandkit_pdf"], "wb") as handle:
            handle.write(bundle["pdf_bytes"])

    result = release_manager.release(
        prompt_records=prompts,
        scan_verdicts=scan_report,
        artifact_bundle=bundle,
        evaluation_result=evaluation,
        selection=selection,
        human_acks=human_acks,
    )
    _save_json(paths["evaluation_report"], evaluation)

    if result["status"] == "BLOCKED":
        print(f"BLOCKED: {result['reason']}")
        print("brand package written for inspection but is NOT release-eligible")
        return EXIT_GATE_BLOCKED

    releases_dir = paths["releases_dir"]
    os.makedirs(releases_dir, exist_ok=True)
    existing = [int(name.split(".")[0]) for name in os.listdir(releases_dir) if name.endswith(".json")]
    version = (max(existing) + 1) if existing else 1
    package_record = dict(result["package"])
    package_record["config_snapshot"] = config
    package_record["spec_snapshot"] = _load_json(paths["spec"], {})
    _save_json(os.path.join(releases_dir, f"{version}.json"), package_record)
    print(f"SEALED: brand package released as version {version}")
    return EXIT_OK


def cmd_audit(args) -> int:
    paths = _paths(args.project)
    prompts = _load_json(paths["prompts"], {})
    previous_scan = _load_json(paths["scan_report"], {})
    new_scan = {}
    any_block = False
    for concept_id, record in prompts.items():
        icon_description = record["prompt"].split("Icon concept: ")[-1].split(" | ")[0]
        verdict = trademark_scanner.scan(concept_id, icon_description, record["avoid_list"]["semantic"])
        new_scan[concept_id] = verdict
        if verdict["verdict"] == "BLOCK":
            any_block = True
        old_verdict = previous_scan.get(concept_id, {}).get("verdict")
        if old_verdict and old_verdict != verdict["verdict"]:
            print(f"{concept_id}: verdict changed {old_verdict} -> {verdict['verdict']}")

    _save_json(paths["scan_report"], new_scan)
    return EXIT_GATE_BLOCKED if any_block else EXIT_OK


def cmd_diff(args) -> int:
    paths = _paths(args.project)
    v1 = _load_json(os.path.join(paths["releases_dir"], f"{args.v1}.json"))
    v2 = _load_json(os.path.join(paths["releases_dir"], f"{args.v2}.json"))
    if v1 is None or v2 is None:
        print("error: one or both release versions not found")
        return EXIT_VALIDATION_ERROR

    all_keys = set(v1) | set(v2)
    diffs = {key: (v1.get(key), v2.get(key)) for key in all_keys if v1.get(key) != v2.get(key)}
    print(json.dumps(diffs, indent=2, default=str))
    return EXIT_OK


def cmd_rollback(args) -> int:
    paths = _paths(args.project)
    release_path = os.path.join(paths["releases_dir"], f"{args.version}.json")
    package_record = _load_json(release_path)
    if package_record is None:
        print(f"error: release version {args.version!r} not found")
        return EXIT_VALIDATION_ERROR

    _save_json(paths["config"], package_record["config_snapshot"])
    _save_json(paths["spec"], package_record["spec_snapshot"])
    print(f"rolled back {args.project} to release version {args.version}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cpp creative", description="Creative Compilation Framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="create a new CCF project (config.json + spec.json)")
    p_init.add_argument("project")
    p_init.add_argument("--brief")
    p_init.add_argument("--dry-run", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_compile = subparsers.add_parser("compile", help="brief -> Creative Specification")
    p_compile.add_argument("project")
    p_compile.add_argument("--brief", required=True)
    p_compile.add_argument("--answers")
    p_compile.set_defaults(func=cmd_compile)

    p_generate = subparsers.add_parser("generate", help="run the Phase-1 concept generation pipeline")
    p_generate.add_argument("project")
    p_generate.add_argument("--only")
    p_generate.add_argument("--dry-run", action="store_true")
    p_generate.set_defaults(func=cmd_generate)

    p_select = subparsers.add_parser("select", help="record the human concept-selection gate")
    p_select.add_argument("project")
    p_select.add_argument("--concept", required=True)
    p_select.add_argument("--by", required=True)
    p_select.add_argument("--ack", action="store_true", help="acknowledge a WARN trademark verdict")
    p_select.set_defaults(func=cmd_select)

    p_package = subparsers.add_parser("package", help="build the brand kit and attempt release")
    p_package.add_argument("project")
    p_package.set_defaults(func=cmd_package)

    p_audit = subparsers.add_parser("audit", help="re-run the Trademark Collision Scanner")
    p_audit.add_argument("project")
    p_audit.set_defaults(func=cmd_audit)

    p_diff = subparsers.add_parser("diff", help="compare two sealed release versions")
    p_diff.add_argument("project")
    p_diff.add_argument("v1")
    p_diff.add_argument("v2")
    p_diff.set_defaults(func=cmd_diff)

    p_rollback = subparsers.add_parser("rollback", help="restore config/spec from a sealed release")
    p_rollback.add_argument("project")
    p_rollback.add_argument("version")
    p_rollback.set_defaults(func=cmd_rollback)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
