"""Demo spec: the regenerable, semantic source of truth for one product demo.

A spec says WHAT to show (steps against semantic targets, beats, callouts, stages,
output budget). It never carries pixel coordinates: geometry is measured at
capture time from the real DOM, so a callout follows the element even when the
layout moves, and a missing element is a refusal rather than a wrong animation.

JSON on purpose: no YAML dependency, and the file is hashed into provenance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

ACTIONS = {"goto", "fill", "select", "check", "click", "press", "wait_text", "assert_absent"}
TARGETED = {"fill", "select", "check", "click", "press"}
TARGET_KINDS = ("role", "label", "testid", "text", "css")
STAGES = {"raw", "browser", "laptop", "phone"}
FORMATS = {"mp4", "webm", "poster"}


class SpecError(ValueError):
    """The spec cannot describe a reproducible demo. Message names the field."""


@dataclass
class Target:
    kind: str
    value: str
    name: str | None = None        # accessible name, only for kind == "role"

    def describe(self) -> str:
        if self.kind == "role":
            return f"role={self.value} name={self.name!r}"
        return f"{self.kind}={self.value!r}"


@dataclass
class Step:
    id: str
    do: str
    target: Target | None = None
    value: str | None = None
    value_env: str | None = None   # secret supplied by the environment, never stored
    path: str | None = None
    text: str | None = None
    timeout_ms: int = 15_000
    film: bool = True              # False = setup (sign-in etc.), not part of the timeline
    typed: bool = True             # fill: capture progressive typing states
    hold_ms: int | None = None     # presented hold after this step settles
    callout: str | None = None     # presentation text anchored to this step's target

    @property
    def secret(self) -> bool:
        return self.value_env is not None


@dataclass
class Viewport:
    name: str
    width: int
    height: int
    dsf: float = 2.0
    stage: str = "raw"
    is_mobile: bool = False


@dataclass
class Output:
    fps: int = 30
    max_seconds: float = 40.0
    max_bytes: int = 12_000_000
    formats: list = field(default_factory=lambda: ["mp4", "poster"])
    default_hold_ms: int = 1400
    typing_ms_per_char: int = 45


@dataclass
class DemoSpec:
    id: str
    base_url: str
    steps: list
    viewports: list
    output: Output
    title: str = ""
    locale: str = "en-US"
    timezone: str = "UTC"
    forbid_text: list = field(default_factory=list)
    fixture_text: list = field(default_factory=list)
    # Names of env vars whose VALUES are synthetic and may appear on screen (a per-run
    # demo account email). The value never enters the spec, so the spec hash is stable.
    fixture_env: list = field(default_factory=list)
    allow_http_errors: list = field(default_factory=list)
    brand_accent: str = "#2563eb"
    source_path: Path | None = None
    sha256: str = ""

    def step(self, step_id: str) -> Step:
        for s in self.steps:
            if s.id == step_id:
                return s
        raise KeyError(step_id)


def _need(obj: dict, key: str, where: str):
    if key not in obj or obj[key] in (None, ""):
        raise SpecError(f"{where}: missing required field '{key}'")
    return obj[key]


def _target(raw, where: str, allow_css: bool) -> Target:
    if not isinstance(raw, dict):
        raise SpecError(f"{where}: target must be an object like {{'role': 'button', 'name': 'Save'}}")
    kinds = [k for k in TARGET_KINDS if k in raw]
    if len(kinds) != 1:
        raise SpecError(f"{where}: target needs exactly one of {TARGET_KINDS}, got {sorted(raw)}")
    kind = kinds[0]
    if kind == "css" and not allow_css:
        raise SpecError(f"{where}: css targets are brittle; prefer role/label/testid, "
                        f"or set \"allow_css\": true on the spec to accept the drift risk")
    if kind == "role" and not raw.get("name"):
        raise SpecError(f"{where}: a role target needs an accessible 'name' to be unambiguous")
    return Target(kind=kind, value=str(raw[kind]), name=raw.get("name"))


def parse(data: dict, source_path: Path | None = None) -> DemoSpec:
    """Validate and build a DemoSpec. Every refusal names the offending field."""
    if not isinstance(data, dict):
        raise SpecError("spec root must be a JSON object")
    sid = _need(data, "id", "spec")
    base_url = str(_need(data, "base_url", "spec")).rstrip("/")
    allow_css = bool(data.get("allow_css", False))

    raw_steps = _need(data, "steps", "spec")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise SpecError("spec: 'steps' must be a non-empty list")
    steps, seen = [], set()
    for i, rs in enumerate(raw_steps):
        where = f"steps[{i}]"
        step_id = str(_need(rs, "id", where))
        if step_id in seen:
            raise SpecError(f"{where}: duplicate step id '{step_id}'")
        seen.add(step_id)
        do = _need(rs, "do", where)
        if do not in ACTIONS:
            raise SpecError(f"{where}: unknown action '{do}', expected one of {sorted(ACTIONS)}")
        tgt = _target(rs.get("target"), where, allow_css) if do in TARGETED else None
        if do in ("fill", "select") and rs.get("value") is None and not rs.get("value_env"):
            raise SpecError(f"{where}: '{do}' needs 'value' or 'value_env'")
        if rs.get("value") is not None and rs.get("value_env"):
            raise SpecError(f"{where}: give 'value' or 'value_env', not both")
        if do == "goto" and not rs.get("path"):
            raise SpecError(f"{where}: 'goto' needs 'path'")
        if do in ("wait_text", "assert_absent") and not rs.get("text"):
            raise SpecError(f"{where}: '{do}' needs 'text'")
        if do == "press" and not rs.get("value"):
            raise SpecError(f"{where}: 'press' needs a key in 'value'")
        callout = rs.get("callout")
        if callout and tgt is None:
            raise SpecError(f"{where}: a callout must anchor to a target; '{do}' has none")
        steps.append(Step(
            id=step_id, do=do, target=tgt,
            value=None if rs.get("value") is None else str(rs["value"]),
            value_env=rs.get("value_env"), path=rs.get("path"), text=rs.get("text"),
            timeout_ms=int(rs.get("timeout_ms", 15_000)), film=bool(rs.get("film", True)),
            typed=bool(rs.get("typed", True)),
            hold_ms=None if rs.get("hold_ms") is None else int(rs["hold_ms"]),
            callout=callout,
        ))
    if not any(s.film for s in steps):
        raise SpecError("spec: no step has film=true; there is nothing to show")

    raw_vps = _need(data, "viewports", "spec")
    vps = []
    for i, rv in enumerate(raw_vps):
        where = f"viewports[{i}]"
        stage = rv.get("stage", "raw")
        if stage not in STAGES:
            raise SpecError(f"{where}: stage '{stage}' not in {sorted(STAGES)}")
        vps.append(Viewport(name=str(_need(rv, "name", where)), width=int(_need(rv, "width", where)),
                            height=int(_need(rv, "height", where)), dsf=float(rv.get("dsf", 2.0)),
                            stage=stage, is_mobile=bool(rv.get("is_mobile", stage == "phone"))))
    names = [v.name for v in vps]
    if len(set(names)) != len(names):
        raise SpecError("spec: viewport names must be unique")

    ro = data.get("output", {})
    out = Output(fps=int(ro.get("fps", 30)), max_seconds=float(ro.get("max_seconds", 40.0)),
                 max_bytes=int(ro.get("max_bytes", 12_000_000)),
                 formats=list(ro.get("formats", ["mp4", "poster"])),
                 default_hold_ms=int(ro.get("default_hold_ms", 1400)),
                 typing_ms_per_char=int(ro.get("typing_ms_per_char", 45)))
    bad = set(out.formats) - FORMATS
    if bad:
        raise SpecError(f"output.formats: unknown {sorted(bad)}, expected subset of {sorted(FORMATS)}")
    if not (1 <= out.fps <= 60):
        raise SpecError("output.fps must be 1..60")

    canon = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return DemoSpec(
        id=str(sid), base_url=base_url, steps=steps, viewports=vps, output=out,
        title=str(data.get("title", sid)), locale=str(data.get("locale", "en-US")),
        timezone=str(data.get("timezone", "UTC")),
        forbid_text=[str(t) for t in data.get("forbid_text", [])],
        fixture_text=[str(t) for t in data.get("fixture_text", [])],
        fixture_env=[str(t) for t in data.get("fixture_env", [])],
        allow_http_errors=[str(t) for t in data.get("allow_http_errors", [])],
        brand_accent=str(data.get("brand_accent", "#2563eb")),
        source_path=source_path, sha256=hashlib.sha256(canon).hexdigest(),
    )


def load(path: str | Path) -> DemoSpec:
    p = Path(path)
    try:
        # utf-8-sig: specs written by Windows tooling may carry a BOM.
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SpecError(f"spec file not found: {p}") from None
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec is not valid JSON: {p}: {exc}") from None
    return parse(data, p.resolve())
