#!/usr/bin/env python3
"""jit_ref_correlate.py — Stop-hook: did the agent USE what JIT injected?

A UserPromptSubmit hook cannot observe the agent's later output
(architectural boundary). This Stop hook closes the loop: it reads the
finished session transcript, counts how many of the ## section anchors
that `jit_skill_loader.py` injected for this session actually appear in
the assistant's output, and writes a ref-ratio telemetry row. That ratio
is the empirical signal future auto-optimization uses to tighten each
module's TASK_PROFILE (Apollo "compression is measured, not declared").

READ + PROPOSE ONLY. Writes nothing but a telemetry JSONL. Never mutates
settings, rules, or skills. NOT self-registered (auto-mode classifier
denies agent hook self-registration; Owner applies the one-line patch —
see the ACTIVATION block at the bottom of this file).

Stop-hook contract: stdin JSON {session_id, transcript_path, cwd, ...}.
Joins JIT telemetry on the RAW session_id field (the loader writes the
unsanitized id INTO each row, so _sid() sanitization/synthetic-id
divergence cannot break the join). session_id absent -> skip + log,
exit 0. ANY error -> log + exit 0 (fail-open; a telemetry hook must
never wedge a Stop).
"""
from __future__ import annotations
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
TELEMETRY_DIR = PP_ROOT / "vault" / "telemetry"
LOG = HOME / ".claude" / "logs" / "jit-ref-correlate.log"
LOADER = PP_ROOT / "tools" / "jit_skill_loader.py"


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _load_profiles() -> dict:
    """Import TASK_PROFILES from the loader (single source of truth)."""
    try:
        spec = importlib.util.spec_from_file_location("jsl", LOADER)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return getattr(m, "TASK_PROFILES", {}) or {}
    except Exception as exc:
        _log(f"profile-import-fail {type(exc).__name__}: {exc}")
        return {}


def _injected_rows(raw_sid: str) -> list[dict]:
    """All jit_usage rows across telemetry files whose RAW sid matches."""
    rows: list[dict] = []
    try:
        if not TELEMETRY_DIR.is_dir():
            return rows
        for f in TELEMETRY_DIR.glob("jit_usage_*.jsonl"):
            try:
                for ln in f.read_text(encoding="utf-8").splitlines():
                    if not ln.strip():
                        continue
                    r = json.loads(ln)
                    if r.get("session_id") == raw_sid:
                        rows.append(r)
            except Exception:
                continue
    except Exception:
        pass
    return rows


def _assistant_text(transcript_path: str) -> str:
    """Concatenate assistant text blocks from a Claude Code transcript."""
    buf: list[str] = []
    try:
        p = Path(transcript_path)
        if not p.is_file():
            return ""
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                ev = json.loads(ln)
            except Exception:
                continue
            msg = ev.get("message") if isinstance(ev, dict) else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                buf.append(content)
            elif isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict) and blk.get("type") == "text":
                        buf.append(str(blk.get("text") or ""))
    except Exception:
        pass
    return "\n".join(buf)


def _anchors_for(module: str, tier: str, profiles: dict) -> list[str]:
    """The ## anchor titles JIT injected for this module/tier."""
    if tier == "discovery":
        return []                            # card has no ## sections
    prof = profiles.get(module)
    if tier == "summary" and prof:
        return [h[3:].strip() for h in (prof.get("include") or [])]
    # full tier or unprofiled: read live SKILL.md headers.
    skill = PP_ROOT / "vendor" / "apollo" / "upstream" / module / "SKILL.md"
    try:
        return [m.group(1).strip() for m in
                re.finditer(r"^##\s+(.+)$", skill.read_text("utf-8"), re.M)]
    except Exception:
        return []


def run(data: dict) -> int:
    data = data or {}
    raw_sid = str(data.get("session_id") or "")
    if not raw_sid:
        _log("skip: no session_id (fail-open)")
        return 0
    transcript = str(data.get("transcript_path") or "")
    profiles = _load_profiles()
    inj = _injected_rows(raw_sid)
    if not inj:
        _log(f"skip: no JIT injection rows for sid={raw_sid}")
        return 0
    text = _assistant_text(transcript)
    low = text.lower()

    out_rows = []
    for r in inj:
        module = r.get("module")
        tier = r.get("tier")
        anchors = _anchors_for(module, tier, profiles)
        referenced = [a for a in anchors if a and a.lower() in low]
        n_inj = len(anchors)
        ratio = (len(referenced) / n_inj) if n_inj else None
        out_rows.append({
            "ts": time.time(),
            "session_id": raw_sid,
            "module": module,
            "tier": tier,
            "anchors_injected": anchors,
            "anchors_referenced": referenced,
            "ref_ratio": ratio,
            "transcript_chars": len(text),
        })

    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        san = re.sub(r"[^A-Za-z0-9_-]", "-", raw_sid)[:64]
        p = TELEMETRY_DIR / f"jit_refs_{san}.jsonl"
        with open(p, "a", encoding="utf-8") as fh:
            for r in out_rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        _log(f"sid={raw_sid} correlated {len(out_rows)} module(s)")
    except Exception as exc:
        _log(f"write-fail {type(exc).__name__}: {exc}")
    return 0


__all__ = ["run"]


if __name__ == "__main__":
    import threading

    box = {"raw": ""}

    def _reader():
        try:
            box["raw"] = sys.stdin.read()
        except Exception:
            box["raw"] = ""

    th = threading.Thread(target=_reader, daemon=True)
    th.start()
    th.join(3.0)
    raw = box["raw"]
    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        payload = {}
    try:
        sys.exit(run(payload))
    except Exception:
        sys.exit(0)                          # fail-open: never wedge Stop

# ─────────────────────────────────────────────────────────────────────
# ACTIVATION (Owner-applied — auto-mode classifier denies agent self-
# registration of hooks). Add to ~/.claude/settings.json hooks.Stop:
#
#   { "matcher": "*", "hooks": [ { "type": "command",
#     "command": "python ~/.claude/skills/claude-power-pack/tools/jit_ref_correlate.py" } ] }
#
# Inert until then. Standalone-verified; cold-loads next /restart.
# ─────────────────────────────────────────────────────────────────────
