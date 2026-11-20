"""Asset validators (CCF, BCAP2-07 / BI-01..BI-09,BI-17,BI-19,BI-22,BI-28).

Pure, dependency-free parsers: a file is evidence only if its BYTES parse as what its name claims.
Every function returns (ok: bool, reason: str). A validator that cannot decide returns False --
absence is never a pass. Callers: modules/ccf/cli.py `package` (kit validation) and
modules/ccf/kit_readiness.py. Nothing here fetches, executes or shells out.
"""
from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
import zlib

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
CONCEPT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

SVG_ALLOWED_TAGS = {
    "svg", "g", "defs", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "title", "desc",
    "lineargradient", "radialgradient", "stop", "clippath", "mask", "text", "tspan", "use", "symbol",
}
SVG_ACTIVE_ATTR = re.compile(r"^on", re.I)
SVG_URL_ATTRS = {"href", "{http://www.w3.org/1999/xlink}href", "src"}


def safe_concept_id(concept_id) -> bool:
    """A concept id becomes a file name and a manifest key: letters, digits, '_' and '-' only."""
    return isinstance(concept_id, str) and CONCEPT_ID_RE.match(concept_id) is not None


def _png_chunks(data: bytes):
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length:
            return None
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        if zlib.crc32(ctype + body) & 0xFFFFFFFF != crc:
            return None
        yield ctype, body
        pos += 12 + length
        if ctype == b"IEND":
            return


def png_info(data: bytes):
    """Return {w,h,depth,ctype,idat} for a fully valid PNG (every chunk CRC checked), else None."""
    if not data or data[:8] != PNG_MAGIC:
        return None
    chunks = list(_png_chunks(data) or [])
    if not chunks or chunks[0][0] != b"IHDR" or chunks[-1][0] != b"IEND" or len(chunks[0][1]) != 13:
        return None
    w, h, depth, ctype, _c, _f, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    idat = b"".join(b for t, b in chunks if t == b"IDAT")
    if not idat or w == 0 or h == 0:
        return None
    try:
        zlib.decompress(idat)
    except zlib.error:
        return None
    return {"w": w, "h": h, "depth": depth, "ctype": ctype, "interlace": interlace, "idat": idat}


def validate_png(data: bytes):
    info = png_info(data)
    return (True, f"png {info['w']}x{info['h']}") if info else (False, "not a complete, CRC-valid PNG")


def validate_svg(data: bytes):
    """Allowlist parse of an untrusted SVG: no script, no event handlers, no foreignObject, no
    external reference. Rejection is the default for anything not understood."""
    if not data:
        return False, "empty svg"
    if re.search(rb"<!ENTITY|<!DOCTYPE", data, re.I):
        return False, "DOCTYPE/ENTITY not allowed"
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        return False, f"unparseable xml: {exc}"
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1].lower() if isinstance(el.tag, str) else ""
        if tag not in SVG_ALLOWED_TAGS:
            return False, f"element <{tag}> not in allowlist"
        for name, value in el.attrib.items():
            local = name.rsplit("}", 1)[-1]
            if SVG_ACTIVE_ATTR.match(local):
                return False, f"event handler attribute {local!r}"
            if name.lower() in SVG_URL_ATTRS or local.lower() == "href":
                if not value.startswith("#"):
                    return False, f"external reference in {local!r}"
            if re.search(r"url\(\s*['\"]?(?!#)", value, re.I) or "javascript:" in value.lower():
                return False, f"external/active url in attribute {local!r}"
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        return False, "root element is not <svg>"
    return True, "svg passes allowlist"


def validate_ico(data: bytes):
    """A real ICO container: ICONDIR(0,1,n) + n directory entries pointing at in-bounds image data.
    A PNG renamed .ico fails because its first bytes are the PNG signature, not ICONDIR."""
    if len(data) < 22 or data[:4] != b"\x00\x00\x01\x00":
        return False, "no ICONDIR header (a renamed PNG is not an ICO)"
    count = struct.unpack("<H", data[4:6])[0]
    if count == 0 or 6 + 16 * count > len(data):
        return False, "bad ICONDIR count"
    for i in range(count):
        size, offset = struct.unpack("<II", data[6 + 16 * i + 8:6 + 16 * i + 16])
        if size == 0 or offset + size > len(data) or offset < 6 + 16 * count:
            return False, f"entry {i} points outside the file"
        img = data[offset:offset + size]
        if not (img[:8] == PNG_MAGIC or struct.unpack("<I", img[:4])[0] == 40):
            return False, f"entry {i} is neither PNG nor BMP data"
    return True, f"ico with {count} image(s)"


def pdf_embedded_images(pdf: bytes) -> list:
    """Image XObjects found in the PDF: [{'width','height','length'}]. Text-only PDFs return []."""
    out = []
    for m in re.finditer(rb"/Subtype\s*/Image", pdf):
        end = pdf.find(b"stream\n", m.end())
        if end < 0:
            continue
        d = pdf[max(0, m.start() - 40):end]
        w = re.search(rb"/Width\s+(\d+)", d)
        h = re.search(rb"/Height\s+(\d+)", d)
        ln = re.search(rb"/Length\s+(\d+)", d)
        if w and h and ln:
            start = end + len(b"stream\n")
            n = int(ln.group(1))
            if pdf[start + n:start + n + 10].lstrip().startswith(b"endstream"):
                out.append({"width": int(w.group(1)), "height": int(h.group(1)), "length": n,
                            "data": pdf[start:start + n]})
    return out


def validate_kit_pdf(pdf: bytes, png: bytes):
    """A brand-kit PDF must DEPICT the mark: it parses, and carries an image XObject whose
    pixel data is exactly the selected PNG's IDAT stream."""
    if not pdf or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-32:]:
        return False, "not a complete PDF"
    info = png_info(png)
    if info is None:
        return False, "source PNG invalid"
    for img in pdf_embedded_images(pdf):
        if img["width"] == info["w"] and img["height"] == info["h"] and img["data"] == info["idat"]:
            return True, "pdf embeds the selected mark"
    return False, "pdf carries no image of the selected mark (text-only report is a CONCEPT_REPORT)"


def _gray_16(data: bytes):
    """Box-downsample an 8-bit gray/RGB/RGBA non-interlaced PNG to 16x16 luminance, or None."""
    info = png_info(data)
    if not info or info["depth"] != 8 or info["interlace"] or info["ctype"] not in (0, 2, 6):
        return None
    bpp = {0: 1, 2: 3, 6: 4}[info["ctype"]]
    w, h = info["w"], info["h"]
    raw = zlib.decompress(info["idat"])
    stride = w * bpp
    if len(raw) != h * (stride + 1):
        return None
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
            elif f != 0:
                return None
        rows.append(line)
        prev = line

    def lum(x, y):
        px = rows[y][x * bpp:(x + 1) * bpp]
        v = px[0] if bpp == 1 else (299 * px[0] + 587 * px[1] + 114 * px[2]) / 1000
        return v if bpp != 4 else v * px[3] / 255 + 255 * (1 - px[3] / 255)

    grid = []
    for gy in range(16):
        r = []
        for gx in range(16):
            x0, x1 = gx * w // 16, max((gx + 1) * w // 16, gx * w // 16 + 1)
            y0, y1 = gy * h // 16, max((gy + 1) * h // 16, gy * h // 16 + 1)
            vals = [lum(x, y) for y in range(y0, min(y1, h)) for x in range(x0, min(x1, w))]
            r.append(sum(vals) / len(vals))
        grid.append(r)
    return grid


def small_size_check(data: bytes, min_contrast: float = 40.0, min_edge_cells: int = 6):
    """BI-28/BR-12: at 16x16 the mark must keep structure. A uniform blob (no luminance range and
    almost no edges) fails; an undecodable PNG fails (unmeasured is never pass)."""
    grid = _gray_16(data)
    if grid is None:
        return False, "cannot measure 16px legibility (unsupported/undecodable PNG)"
    flat = [v for r in grid for v in r]
    rng = max(flat) - min(flat)
    edges = sum(1 for y in range(16) for x in range(15) if abs(grid[y][x] - grid[y][x + 1]) > 20) + \
        sum(1 for y in range(15) for x in range(16) if abs(grid[y][x] - grid[y + 1][x]) > 20)
    if rng < min_contrast or edges < min_edge_cells:
        return False, f"16px render is a blob (luminance range {rng:.0f}, edge cells {edges})"
    return True, f"16px keeps structure (range {rng:.0f}, edge cells {edges})"


def check_font(font_name: str, wordmark: str, font_registry: dict):
    """BI-19/BR-10: a wordmark font must be a registered, licensed font whose glyph set covers
    every character of the wordmark. No silent substitution: unknown -> reject."""
    entry = (font_registry or {}).get(font_name)
    if not entry:
        return False, f"font {font_name!r} is not registered (no silent substitution)"
    if not entry.get("license"):
        return False, f"font {font_name!r} has no recorded license"
    missing = sorted({ch for ch in wordmark if not ch.isspace() and ch not in entry.get("glyphs", "")})
    if missing:
        return False, f"font {font_name!r} lacks glyphs: {''.join(missing)}"
    return True, "font registered, licensed, glyphs cover the wordmark"


_SPDX = {"mit": "MIT", "apache": "Apache-2.0", "bsd": "BSD", "gpl": "GPL", "agpl": "AGPL", "mpl": "MPL",
         "isc": "ISC", "unlicense": "Unlicense", "cc0": "CC0"}


def _license_from_text(text: str):
    t = text.lower()
    for key, name in (("gnu affero", "AGPL"), ("gnu general public", "GPL"), ("apache license", "Apache-2.0"),
                      ("permission is hereby granted, free of charge", "MIT"), ("mozilla public", "MPL"),
                      ("redistribution and use in source and binary forms", "BSD"), ("isc license", "ISC")):
        if key in t:
            return name
    return None


def license_conflict(readme: str, license_text: str):
    """BI-06/BR-14: README-declared license vs actual LICENSE text. Returns (blocked, reason).
    Any disagreement, or an undeterminable side, blocks code ingestion (principles only)."""
    actual = _license_from_text(license_text or "")
    m = re.search(r"\b(AGPL|GPL|LGPL|Apache(?:[- ]2\.0)?|MIT|BSD|MPL|ISC|Unlicense|CC0)\b", readme or "", re.I)
    claimed = None
    if m:
        k = m.group(1).lower().split("-")[0].split(" ")[0]
        claimed = _SPDX.get(k, m.group(1))
    if actual is None:
        return True, "LICENSE text not recognised: code ingestion blocked"
    if claimed is None:
        return True, "README declares no license: cannot cross-check"
    if claimed != actual:
        return True, f"README claims {claimed} but LICENSE is {actual}: license conflict"
    return False, f"README and LICENSE agree: {actual}"
