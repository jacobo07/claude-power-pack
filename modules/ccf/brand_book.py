"""Illustrated brand book PDF (BCAP2B-04 / BI-24). Pure Python, no render toolchain.

Extends the kit-PDF path: the kit PDF depicts the mark on one page per concept; the book is one document
with a fixed page order (principles read from DesignHub's guideline registry, MIT, no code taken): contents,
logo usage, clear space, minimum size, incorrect usage, colour palette, typography. The mark is embedded ONCE as an
Image XObject (the PNG's own IDAT stream, so `asset_validator.validate_kit_pdf` accepts it) and drawn on several pages.
Bookmarks and contents links are low-level PDF objects (an outline tree and /Link annotations).

Honesty limits: only the PDF base-14 fonts, so typography names the DECLARED brand fonts as text and does not
render them; a mark that is not an 8-bit non-interlaced gray/RGB PNG is refused (no silent text-only fallback);
"incorrect usage" tiles are drawn with the real mark under a stretch, a rotation and a low-contrast ground.
validate_brand_book is a structural parser, not a renderer: it proves the objects are there and linked, not how they look.
"""
from __future__ import annotations

import re

from modules.ccf.artifact_compiler import _escape_pdf_text
from modules.ccf.asset_validator import pdf_embedded_images, png_info
from modules.ccf.brand_color import contrast

PAGE_W, PAGE_H = 612, 792
SECTIONS = ("Contents", "Logo usage", "Clear space", "Minimum size", "Incorrect usage", "Colour palette", "Typography")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _rgb01(h: str):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _fill(h): return "%.3f %.3f %.3f rg" % _rgb01(h)
def _stroke(h): return "%.3f %.3f %.3f RG" % _rgb01(h)


class _Page:
    def __init__(self, title):
        self.title, self.ops, self.links = title, [], []

    def text(self, x, y, s, size=11, bold=False, color="#111111"):
        self.ops += ["BT", _fill(color), f"/{'F2' if bold else 'F1'} {size} Tf", f"{x} {y} Td", f"({_escape_pdf_text(s)}) Tj", "ET"]

    def rect(self, x, y, w, h, fill=None, stroke=None, dash=False):
        o = ["q"]
        if fill: o.append(_fill(fill))
        if stroke: o += [_stroke(stroke), "0.75 w"] + (["[4 3] 0 d"] if dash else [])
        o += [f"{x} {y} {w} {h} re", "B" if fill and stroke else ("f" if fill else "S"), "Q"]
        self.ops += o

    def image(self, x, y, w, h, rot_deg=0.0):
        import math
        if rot_deg:
            c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
            self.ops += ["q", f"{w * c:.3f} {w * s:.3f} {-h * s:.3f} {h * c:.3f} {x} {y} cm", "/Im1 Do", "Q"]
        else:
            self.ops += ["q", f"{w} 0 0 {h} {x} {y} cm", "/Im1 Do", "Q"]

    def link(self, x, y, w, h, target_index):
        self.links.append((x, y, w, h, target_index))


def _mark_box(info, max_side):
    k = max_side / max(info["w"], info["h"])
    return info["w"] * k, info["h"] * k


def _compose(brand, info, palette, fonts):
    pages = []
    dark, light = "#111111", "#FFFFFF"
    # contents is page 0, so its links land on pages 1..n-1
    p = _Page("Contents")
    p.text(72, 720, f"{brand} brand book", 22, True)
    pages.append(p)

    p = _Page("Logo usage")
    p.text(72, 720, "Logo usage", 20, True)
    p.text(72, 696, "The mark is used as supplied. Do not redraw, recolour, or add effects.", 11)
    w, h = _mark_box(info, 300)
    p.image(156, 300, w, h)
    pages.append(p)

    p = _Page("Clear space")
    p.text(72, 720, "Clear space", 20, True)
    p.text(72, 696, "Keep a margin of one quarter of the mark width free on every side.", 11)
    w, h = _mark_box(info, 220)
    m = w / 4
    x, y = 196, 360
    p.rect(x - m, y - m, w + 2 * m, h + 2 * m, stroke="#D0021B", dash=True)
    p.image(x, y, w, h)
    p.text(x - m, y - m - 16, f"margin = 1/4 mark width = {m:.0f} pt", 10)
    pages.append(p)

    p = _Page("Minimum size")
    p.text(72, 720, "Minimum size", 20, True)
    p.text(72, 696, "Below the smallest size shown, use the mark only where it stays legible.", 11)
    x = 72
    for side in (144, 72, 36, 24):
        w, h = _mark_box(info, side)
        p.image(x, 480, w, h)
        p.text(x, 460, f"{side} pt", 10)
        x += side + 36
    pages.append(p)

    p = _Page("Incorrect usage")
    p.text(72, 720, "Incorrect usage", 20, True)
    p.text(72, 696, "Never stretch, rotate, or place the mark on a ground of nearly the same colour.", 11)
    w, h = _mark_box(info, 110)
    tiles = (("Stretched", None), ("Rotated", 25.0), ("Low contrast", "ground"))
    for i, (label, kind) in enumerate(tiles):
        x = 72 + i * 170
        p.rect(x, 380, 150, 150, fill=light, stroke="#BBBBBB")
        if kind == "ground":
            p.rect(x, 380, 150, 150, fill="#2A2A2A")
            p.image(x + 20, 410, w, h)
        elif kind:
            p.image(x + 55, 400, w * 0.8, h * 0.8, rot_deg=kind)
        else:
            p.image(x + 10, 420, 130, h * 0.45)
        p.text(x, 360, label, 11, True, "#D0021B")
    pages.append(p)

    p = _Page("Colour palette")
    p.text(72, 720, "Colour palette", 20, True)
    y = 640
    for name, hx in palette.items():
        txt = "#FFFFFF" if contrast("#FFFFFF", hx) >= contrast("#000000", hx) else "#000000"
        p.rect(72, y, 120, 54, fill=hx, stroke="#BBBBBB")
        p.text(80, y + 22, hx.upper(), 11, True, txt)
        p.text(210, y + 32, name, 12, True)
        p.text(210, y + 14, f"contrast on white {contrast('#FFFFFF', hx)}:1, on black {contrast('#000000', hx)}:1", 10)
        y -= 70
    pages.append(p)

    p = _Page("Typography")
    p.text(72, 720, "Typography", 20, True)
    p.text(72, 696, "Declared brand fonts (named, not rendered: this PDF carries only the base-14 fonts).", 11)
    y = 640
    for role, name in fonts:
        p.text(72, y, f"{role}: {name}", 14, True)
        p.text(72, y - 18, "The quick brown fox jumps over the lazy dog (base-14 stand-in)", 11)
        y -= 60
    pages.append(p)

    # contents rows link to pages 1..n-1
    c = pages[0]
    y = 660
    for i, t in enumerate(SECTIONS[1:], start=1):
        c.text(90, y, f"{i}. {t}", 13)
        c.link(72, y - 4, 400, 20, i)
        y -= 30
    return pages


def build_brand_book(brand: str, mark_png: bytes, palette: dict, fonts: list) -> bytes:
    """Return real PDF bytes, or raise ValueError naming the first thing wrong (no partial book)."""
    if not brand or not str(brand).strip():
        raise ValueError("brand name is required")
    info = png_info(mark_png)
    if info is None:
        raise ValueError("mark is not a complete, CRC-valid PNG")
    if info["depth"] != 8 or info["interlace"] or info["ctype"] not in (0, 2):
        raise ValueError("mark must be an 8-bit non-interlaced gray or RGB PNG (alpha/palette cannot be embedded losslessly here)")
    if not palette:
        raise ValueError("palette is empty")
    for name, hx in palette.items():
        if not isinstance(hx, str) or not _HEX.match(hx):
            raise ValueError(f"palette colour {name!r} is not #RRGGBB: {hx!r}")
    if not fonts:
        raise ValueError("no declared fonts (no silent default)")

    pages = _compose(str(brand), info, palette, fonts)
    n = len(pages)
    # object numbers: 1 catalog, 2 pages, 3 F1, 4 F2, 5 image, 6 outlines, 7..7+n-1 outline items,
    # then per page: content, page, then link annots
    img_n, outl_n, first_item = 5, 6, 7
    base = first_item + n
    content_n = [base + 2 * i for i in range(n)]
    page_n = [base + 2 * i + 1 for i in range(n)]
    annot_start = base + 2 * n
    objs = {}
    annot_nums = []
    k = annot_start
    for pi, pg in enumerate(pages):
        nums = []
        for (x, y, w, h, tgt) in pg.links:
            objs[k] = (f"<< /Type /Annot /Subtype /Link /Rect [{x} {y} {x + w} {y + h}] /Border [0 0 0] "
                       f"/Dest [{page_n[tgt]} 0 R /XYZ 0 {PAGE_H} null] >>").encode("latin-1")
            nums.append(k)
            k += 1
        annot_nums.append(nums)

    colors = 3 if info["ctype"] == 2 else 1
    cs = "/DeviceRGB" if colors == 3 else "/DeviceGray"
    objs[1] = f"<< /Type /Catalog /Pages 2 0 R /Outlines {outl_n} 0 R /PageMode /UseOutlines >>".encode()
    objs[2] = f"<< /Type /Pages /Kids [{' '.join(f'{x} 0 R' for x in page_n)}] /Count {n} >>".encode()
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objs[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
    objs[img_n] = (f"<< /Type /XObject /Subtype /Image /Width {info['w']} /Height {info['h']} /ColorSpace {cs} "
                   f"/BitsPerComponent 8 /Filter /FlateDecode /DecodeParms << /Predictor 15 /Colors {colors} "
                   f"/Columns {info['w']} /BitsPerComponent 8 >> /Length {len(info['idat'])} >>\nstream\n").encode("latin-1") \
        + info["idat"] + b"\nendstream"
    objs[outl_n] = f"<< /Type /Outlines /First {first_item} 0 R /Last {first_item + n - 1} 0 R /Count {n} >>".encode()
    for i, pg in enumerate(pages):
        prev = f" /Prev {first_item + i - 1} 0 R" if i else ""
        nxt = f" /Next {first_item + i + 1} 0 R" if i < n - 1 else ""
        objs[first_item + i] = (f"<< /Title ({_escape_pdf_text(pg.title)}) /Parent {outl_n} 0 R{prev}{nxt} "
                                f"/Dest [{page_n[i]} 0 R /XYZ 0 {PAGE_H} null] >>").encode("latin-1")
        body = "\n".join(pg.ops).encode("latin-1", errors="replace")
        objs[content_n[i]] = f"<< /Length {len(body)} >>\nstream\n".encode() + body + b"\nendstream"
        an = f" /Annots [{' '.join(f'{x} 0 R' for x in annot_nums[i])}]" if annot_nums[i] else ""
        objs[page_n[i]] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                           f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << /Im1 {img_n} 0 R >> >> "
                           f"/Contents {content_n[i]} 0 R{an} >>").encode("latin-1")

    out = bytearray(b"%PDF-1.4\n")
    offs = {}
    for num in sorted(objs):
        offs[num] = len(out)
        out += f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n"
    top = max(objs) + 1
    xref = len(out)
    out += f"xref\n0 {top}\n0000000000 65535 f \n".encode()
    for num in range(1, top):
        out += f"{offs[num]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {top} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return bytes(out)


def validate_brand_book(pdf: bytes, mark_png: bytes, min_pages: int = len(SECTIONS)):
    """Structural proof: complete PDF, >= min_pages pages, the mark's pixel stream embedded, mark drawn on >= 4 pages,
    one bookmark per page, every link annotation resolving to a real page object, xref offsets pointing at objects."""
    if not pdf or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-32:]:
        return False, "not a complete PDF"
    info = png_info(mark_png)
    if info is None:
        return False, "source PNG invalid"
    m = re.search(rb"/Type /Pages /Kids \[([^\]]*)\] /Count (\d+)", pdf)
    if not m:
        return False, "no page tree"
    kids = [int(x) for x in re.findall(rb"(\d+) 0 R", m.group(1))]
    if int(m.group(2)) != len(kids) or len(kids) < min_pages:
        return False, f"page count {len(kids)} (declared {m.group(2).decode()}) < {min_pages}"
    if not any(i["width"] == info["w"] and i["height"] == info["h"] and i["data"] == info["idat"] for i in pdf_embedded_images(pdf)):
        return False, "mark pixel stream not embedded"
    drawn = sum(1 for k in kids if b"/Im1 Do" in _object(pdf, _content_of(pdf, k)))
    if drawn < 4:
        return False, f"mark drawn on {drawn} pages (< 4)"
    om = re.search(rb"/Type /Outlines /First (\d+) 0 R /Last (\d+) 0 R /Count (\d+)", pdf)
    if not om or int(om.group(3)) != len(kids):
        return False, "outline missing or not one bookmark per page"
    for item in range(int(om.group(1)), int(om.group(2)) + 1):
        d = re.search(rb"/Dest \[(\d+) 0 R", _object(pdf, item))
        if not d or int(d.group(1)) not in kids:
            return False, f"bookmark object {item} does not resolve to a page"
    links = 0
    for k in kids:
        for a in re.findall(rb"(\d+) 0 R", (re.search(rb"/Annots \[([^\]]*)\]", _object(pdf, k)) or [None, b""])[1]):
            d = re.search(rb"/Dest \[(\d+) 0 R", _object(pdf, int(a)))
            if not d or int(d.group(1)) not in kids:
                return False, f"link annotation {a.decode()} does not resolve to a page"
            links += 1
    if links < min_pages - 1:
        return False, f"{links} contents links (< {min_pages - 1})"
    return True, f"{len(kids)} pages, mark on {drawn}, {len(kids)} bookmarks, {links} links"


def _object(pdf: bytes, num: int) -> bytes:
    sx = re.search(rb"startxref\s+(\d+)", pdf)
    if not sx:
        return b""
    xo = int(sx.group(1))
    lines = pdf[xo:].split(b"\n")
    try:
        off = int(lines[2 + num][:10])
    except (IndexError, ValueError):
        return b""
    end = pdf.find(b"endobj", off)
    head = f"{num} 0 obj".encode()
    return pdf[off:end] if pdf[off:off + len(head)] == head and end > 0 else b""


def _content_of(pdf: bytes, page_num: int) -> int:
    m = re.search(rb"/Contents (\d+) 0 R", _object(pdf, page_num))
    return int(m.group(1)) if m else 0


def inputs_from_concept(concept: dict):
    """(palette, fonts) read from a CCF concept, or None when it declares no #RRGGBB colour or no font.
    `colours` is free text or a list, so only literal hex values count; names like "forest green" are not guessed into hex."""
    raw = concept.get("colours")
    items = raw if isinstance(raw, list) else [raw or ""]
    hexes = []
    for it in items:
        hexes += re.findall(r"#[0-9A-Fa-f]{6}\b", str(it))
    font = str(concept.get("font") or "").strip()
    if not hexes or not font:
        return None
    palette = {f"Colour {i + 1}": h for i, h in enumerate(dict.fromkeys(h.upper() for h in hexes))}
    return palette, [("Brand font", font)]
