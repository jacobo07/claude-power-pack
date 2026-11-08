"""Optional dependency registry: stage, licence, footprint, and the licence wall.

Every optional engine is probed, never assumed. A stage whose engine is missing reports UNAVAILABLE.
Engines with non-commercial weights are EXCLUDED and refuse to load. Engines whose licence needs a
human read before commercial use are GATED behind an explicit environment flag.
Sources and verdicts: references/sources.md (research 2026-11-08).
"""

from __future__ import annotations

import importlib.util
import os

REGISTRY: dict[str, dict] = {
    "scenedetect": {"stage": "shots", "licence": "BSD-3-Clause", "pip": "scenedetect", "gpu": False},
    "transnetv2_pytorch": {"stage": "shots", "licence": "MIT", "pip": "transnetv2-pytorch", "gpu": "optional"},
    "paddleocr": {"stage": "text", "licence": "Apache-2.0", "pip": "paddleocr", "gpu": "optional"},
    "sam2": {"stage": "layers", "licence": "Apache-2.0", "pip": "sam2 (from facebookresearch/sam2)", "gpu": True},
    "sam3": {"stage": "layers", "licence": "SAM License (custom)", "pip": "sam3 (facebookresearch/sam3)", "gpu": True,
             "gate": "VRE_ALLOW_SAM3"},
    "torchvision": {"stage": "flow (RAFT)", "licence": "BSD-3-Clause", "pip": "torchvision", "gpu": "optional"},
    "torch": {"stage": "runtime", "licence": "BSD-3-Clause", "pip": "torch", "gpu": "optional"},
    "whisperx": {"stage": "words", "licence": "BSD-2-Clause", "pip": "whisperx", "gpu": "optional",
                 "note": "do not enable diarization (separate model agreement)"},
    "faster_whisper": {"stage": "words", "licence": "MIT", "pip": "faster-whisper", "gpu": "optional"},
    "beat_this": {"stage": "beats", "licence": "MIT (code and weights)", "pip": "beat_this", "gpu": "optional",
                  "note": "never use --dbn: it needs madmom (non-commercial models)"},
    "librosa": {"stage": "onsets (cross-check)", "licence": "ISC", "pip": "librosa", "gpu": False},
    "skimage": {"stage": "judge (SSIM)", "licence": "BSD-3-Clause", "pip": "scikit-image", "gpu": False},
}

EXCLUDED: dict[str, str] = {
    "cotracker": "CC-BY-NC weights; use RAFT (torchvision, BSD-3) for flow instead",
    "madmom": "CC BY-NC-SA models; use beat_this without --dbn",
    "lens": "mixfont/lens is personal/academic/non-commercial only",
}


class ExcludedDependency(RuntimeError):
    pass


def available(name: str) -> bool:
    if name in EXCLUDED:
        raise ExcludedDependency(f"{name} is excluded: {EXCLUDED[name]}")
    entry = REGISTRY.get(name, {})
    gate = entry.get("gate")
    if gate and os.environ.get(gate) != "1":
        return False
    return importlib.util.find_spec(name) is not None


def status() -> list[dict]:
    rows = []
    for name, entry in REGISTRY.items():
        gate = entry.get("gate")
        installed = importlib.util.find_spec(name) is not None
        state = "OK" if installed else "UNAVAILABLE"
        if gate and installed and os.environ.get(gate) != "1":
            state = f"GATED ({gate}=1 after a licence read)"
        rows.append({"name": name, **entry, "state": state})
    rows += [{"name": n, "state": "EXCLUDED", "reason": r} for n, r in EXCLUDED.items()]
    return rows
