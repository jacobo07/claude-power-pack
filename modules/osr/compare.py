#!/usr/bin/env python3
"""compare.py -- OSR-2: comparison of a build against a captured reference.

The measured gap this closes. The estate has three visual surfaces and not one
of them compares two artifacts: `osa/gpu_eyes.py` CAPTURES,
`sleepless_qa/verdict/visual.py` asks a vision model whether ONE screenshot
looks broken, and `autoresearch/vision_scorer.py` scores ONE image. A sweep of
1,350 files returned zero hits for pixel, perceptual or image comparison.

What this module refuses to do, by contract:

* It never emits a fidelity number, a percentage or a weighted mean. DAIF-03
  owns the fidelity verdict and its own §1.2 prohibits averaging across
  dimensions by name. This module emits OBSERVATIONS that DAIF-03's dimensions
  consume, and a three-valued verdict per instrument.
* It never judges design quality. `cdio` owns that, and a replica can be
  faithful and ugly because the original was.
* UNMEASURED is a first-class verdict, never a quiet PASS. This is the same
  discipline `gpu_eyes.py` enforces with `visual_qa_passed=None`: absence of a
  measurement is not evidence of a match.

Dependency posture: standard library only. The PNG reader below exists because
requiring an imaging package would make the instrument unavailable on exactly
the hosts that most need it, and an instrument that cannot run reports
UNMEASURED forever.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any, Iterable, Sequence

MATCH = "MATCH"
DIFF = "DIFF"
UNMEASURED = "UNMEASURED"

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 4: 2, 6: 4}


class ImageDecodeError(ValueError):
    """The artifact could not be decoded, so nothing may be claimed about it."""


# ------------------------------------------------------------------ raster

class Raster:
    """An 8-bit-per-channel image, decoded into a flat bytearray."""

    __slots__ = ("width", "height", "channels", "data")

    def __init__(self, width: int, height: int, channels: int, data: bytearray) -> None:
        self.width = width
        self.height = height
        self.channels = channels
        self.data = data

    def pixel(self, x: int, y: int) -> tuple[int, ...]:
        start = (y * self.width + x) * self.channels
        return tuple(self.data[start:start + self.channels])


def decode_png(path: str | Path) -> Raster:
    """Decode a non-interlaced 8-bit PNG using the standard library alone.

    Supports colour types 0, 2, 4 and 6 at bit depth 8 -- which is what every
    screen-capture path in this estate produces (scrot, Playwright, the Windows
    capture helpers). Anything else raises rather than guessing, because a
    silently mis-decoded reference produces confident, wrong divergences.
    """
    raw = Path(path).read_bytes()
    if not raw.startswith(_PNG_SIGNATURE):
        raise ImageDecodeError(f"{path}: not a PNG (signature mismatch)")

    pos = len(_PNG_SIGNATURE)
    header: tuple[int, ...] | None = None
    idat = bytearray()
    while pos + 8 <= len(raw):
        (length,) = struct.unpack(">I", raw[pos:pos + 4])
        ctype = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + length]
        pos += 12 + length  # length + type + body + crc
        if ctype == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat.extend(body)
        elif ctype == b"IEND":
            break

    if header is None:
        raise ImageDecodeError(f"{path}: no IHDR chunk")
    width, height, depth, colour, compression, filt, interlace = header
    if depth != 8:
        raise ImageDecodeError(f"{path}: bit depth {depth} unsupported (need 8)")
    if colour not in _CHANNELS_BY_COLOR_TYPE:
        raise ImageDecodeError(f"{path}: colour type {colour} unsupported")
    if compression != 0 or filt != 0:
        raise ImageDecodeError(f"{path}: non-standard compression/filter method")
    if interlace != 0:
        raise ImageDecodeError(f"{path}: interlaced PNG unsupported")
    if not idat:
        raise ImageDecodeError(f"{path}: no image data")

    channels = _CHANNELS_BY_COLOR_TYPE[colour]
    stride = width * channels
    try:
        inflated = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise ImageDecodeError(f"{path}: inflate failed ({exc})") from exc
    if len(inflated) < height * (stride + 1):
        raise ImageDecodeError(f"{path}: truncated image data")

    out = bytearray(height * stride)
    prev = bytearray(stride)
    src = 0
    for row in range(height):
        ftype = inflated[src]
        src += 1
        line = bytearray(inflated[src:src + stride])
        src += stride
        _unfilter_row(ftype, line, prev, channels, path)
        out[row * stride:(row + 1) * stride] = line
        prev = line
    return Raster(width, height, channels, out)


def _unfilter_row(ftype: int, line: bytearray, prev: bytearray, bpp: int, path: Any) -> None:
    if ftype == 0:
        return
    if ftype == 1:
        for i in range(bpp, len(line)):
            line[i] = (line[i] + line[i - bpp]) & 0xFF
    elif ftype == 2:
        for i in range(len(line)):
            line[i] = (line[i] + prev[i]) & 0xFF
    elif ftype == 3:
        for i in range(len(line)):
            left = line[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
    elif ftype == 4:
        for i in range(len(line)):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = (line[i] + pred) & 0xFF
    else:
        raise ImageDecodeError(f"{path}: unknown row filter {ftype}")


# ------------------------------------------------------- instrument: raster

def compare_rasters(
    reference: str | Path,
    build: str | Path,
    channel_tolerance: int = 2,
    block: int = 32,
) -> dict[str, Any]:
    """Compare two rendered artifacts pixel by pixel, reported by region.

    `channel_tolerance` absorbs antialiasing and renderer noise, which is the
    documented reason a bare pixel diff is untrustworthy on its own. Regions are
    reported as block coordinates rather than a single count, because "1.2% of
    pixels differ" hides whether the difference is spread evenly (a font) or
    concentrated (a control that failed to render).
    """
    try:
        ref = decode_png(reference)
        got = decode_png(build)
    except (OSError, ImageDecodeError) as exc:
        return _unmeasured("raster", str(exc))

    if (ref.width, ref.height) != (got.width, got.height):
        return {
            "instrument": "raster",
            "verdict": DIFF,
            "observations": {
                "dimension_mismatch": {
                    "reference": [ref.width, ref.height],
                    "build": [got.width, got.height],
                }
            },
        }

    channels = min(ref.channels, got.channels)
    differing = 0
    max_delta = 0
    regions: dict[str, int] = {}
    for y in range(ref.height):
        for x in range(ref.width):
            a = ref.pixel(x, y)[:channels]
            b = got.pixel(x, y)[:channels]
            delta = max(abs(int(p) - int(q)) for p, q in zip(a, b))
            if delta > channel_tolerance:
                differing += 1
                max_delta = max(max_delta, delta)
                key = f"{x // block},{y // block}"
                regions[key] = regions.get(key, 0) + 1

    observations: dict[str, Any] = {
        "differing_pixels": differing,
        "total_pixels": ref.width * ref.height,
        "max_channel_delta": max_delta,
        "channel_tolerance": channel_tolerance,
        "differing_regions": sorted(regions.items(), key=lambda kv: -kv[1])[:16],
        "region_count": len(regions),
    }
    return {
        "instrument": "raster",
        "verdict": MATCH if differing == 0 else DIFF,
        "observations": observations,
    }


# ----------------------------------------------------- instrument: geometry

def compare_geometry(
    reference: Iterable[dict[str, Any]],
    build: Iterable[dict[str, Any]],
    tolerance_px: int = 2,
) -> dict[str, Any]:
    """Compare two element-box inventories keyed by a stable element id.

    A box list is what an accessibility tree or a DOM snapshot yields, and it
    catches the class of divergence a raster comparison cannot name: a control
    that moved, resized, disappeared, or appeared where the reference had none.
    Each element is `{"id": str, "x": int, "y": int, "w": int, "h": int}` and
    may carry any additional keys, which are ignored here.
    """
    ref = {e["id"]: e for e in reference if "id" in e}
    got = {e["id"]: e for e in build if "id" in e}
    if not ref and not got:
        return _unmeasured("geometry", "both inventories are empty")

    missing = sorted(set(ref) - set(got))
    extra = sorted(set(got) - set(ref))
    moved: list[dict[str, Any]] = []
    resized: list[dict[str, Any]] = []
    for eid in sorted(set(ref) & set(got)):
        a, b = ref[eid], got[eid]
        dx = int(b.get("x", 0)) - int(a.get("x", 0))
        dy = int(b.get("y", 0)) - int(a.get("y", 0))
        dw = int(b.get("w", 0)) - int(a.get("w", 0))
        dh = int(b.get("h", 0)) - int(a.get("h", 0))
        if max(abs(dx), abs(dy)) > tolerance_px:
            moved.append({"id": eid, "dx": dx, "dy": dy})
        if max(abs(dw), abs(dh)) > tolerance_px:
            resized.append({"id": eid, "dw": dw, "dh": dh})

    verdict = MATCH if not (missing or extra or moved or resized) else DIFF
    return {
        "instrument": "geometry",
        "verdict": verdict,
        "observations": {
            "missing_in_build": missing,
            "extra_in_build": extra,
            "moved": moved,
            "resized": resized,
            "tolerance_px": tolerance_px,
        },
    }


# ----------------------------------------------------- instrument: temporal

def compare_timelines(
    reference: Sequence[dict[str, Any]],
    build: Sequence[dict[str, Any]],
    tolerance_ms: int = 25,
) -> dict[str, Any]:
    """Compare two ordered timelines of named phases.

    Each entry is `{"name": str, "start_ms": int, "end_ms": int}`. Duration is
    compared per phase and the phase ORDER is compared as a sequence, because a
    build can reach the same terminal appearance through a different order --
    the failure OSR-L1 exists to name.
    """
    if not reference or not build:
        return _unmeasured("temporal", "one or both timelines are empty")

    ref = {e["name"]: e for e in reference if "name" in e}
    got = {e["name"]: e for e in build if "name" in e}
    drift: list[dict[str, Any]] = []
    for name in sorted(set(ref) & set(got)):
        a_ms = int(ref[name]["end_ms"]) - int(ref[name]["start_ms"])
        b_ms = int(got[name]["end_ms"]) - int(got[name]["start_ms"])
        if abs(b_ms - a_ms) > tolerance_ms:
            drift.append({"phase": name, "reference_ms": a_ms, "build_ms": b_ms})

    ref_order = [e["name"] for e in reference if "name" in e]
    got_order = [e["name"] for e in build if "name" in e]
    order_changed = ref_order != got_order

    missing = sorted(set(ref) - set(got))
    extra = sorted(set(got) - set(ref))
    verdict = MATCH if not (drift or order_changed or missing or extra) else DIFF
    return {
        "instrument": "temporal",
        "verdict": verdict,
        "observations": {
            "duration_drift": drift,
            "order_changed": order_changed,
            "reference_order": ref_order,
            "build_order": got_order,
            "missing_phases": missing,
            "extra_phases": extra,
            "tolerance_ms": tolerance_ms,
        },
    }


# -------------------------------------------------------------- aggregation

def instrument_report(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Collect instrument results without collapsing them into a number.

    The aggregate is a CONJUNCTION, never an average: any DIFF makes the report
    DIFF, and any UNMEASURED with no DIFF makes it UNMEASURED -- an unmeasured
    dimension is a failed dimension, not a neutral one. This mirrors DAIF-03
    §1.2 rather than restating it as a rival rule.
    """
    collected = list(results)
    if not collected:
        return {"verdict": UNMEASURED, "instruments": [], "reason": "no instrument ran"}
    verdicts = {r.get("verdict", UNMEASURED) for r in collected}
    if DIFF in verdicts:
        overall = DIFF
    elif UNMEASURED in verdicts:
        overall = UNMEASURED
    else:
        overall = MATCH
    return {"verdict": overall, "instruments": collected}


def _unmeasured(instrument: str, reason: str) -> dict[str, Any]:
    return {"instrument": instrument, "verdict": UNMEASURED, "observations": {"reason": reason}}
