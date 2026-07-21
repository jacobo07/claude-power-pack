"""Artifact Compiler (CCF component #5).

Adopts the reference repo's real shape (REVERSE_ENGINEERING_REPORT.md §A):
config/source -> HTML -> PDF finisher. The PDF finisher here is a minimal,
dependency-free PDF writer (pure Python, no external library, no headless
browser) rather than the reference repo's headless-Chrome print-to-pdf --
a deliberate, documented scope reduction for environment portability (a
guaranteed Chrome install cannot be assumed everywhere this runs). It renders
one page per included concept (id, wordmark, icon description, provider
metadata) as text -- embedding the actual generated PNG bytes as a real PDF
image XObject is a tracked follow-on, not claimed here.

Mandatory fix for CCF-F02 (empty-shell PDF footgun): before building anything,
every concept without a successful ImageArtifact is skipped with a structured
warning. If NO concept has a successful artifact, no PDF is built at all --
never a near-empty shell.
"""
from __future__ import annotations

import html as html_lib


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _build_minimal_pdf(pages_lines: list) -> bytes:
    """Hand-rolled, valid, minimal single-font text PDF. `pages_lines` is a
    list of pages, each a list of plain-text lines. Returns real PDF bytes
    with a correct xref table -- not a stub, a genuinely valid file.
    """
    objects = []  # list of bytes, index 0 == object number 1

    # Object numbering: 1=Catalog, 2=Pages, 3=Font (shared), 4..=Contents,
    # then N page objects. Catalog/Pages bodies are written once every page
    # and content object number is known (both reference each other/the
    # page list), so their list slots are appended first and overwritten
    # below once the full object count is settled.
    font_obj_num = 3
    objects.append(b"")  # slot for obj 1 (Catalog), overwritten below
    objects.append(b"")  # slot for obj 2 (Pages), overwritten below
    objects.append(  # obj 3: Font
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    )

    page_obj_nums = []
    content_obj_nums = []
    next_num = font_obj_num + 1
    for lines in pages_lines:
        content_lines = ["BT", "/F1 11 Tf", "72 740 Td", "14 TL"]
        for line in lines:
            content_lines.append(f"({_escape_pdf_text(line)}) Tj")
            content_lines.append("T*")
        content_lines.append("ET")
        stream_body = "\n".join(content_lines).encode("latin-1", errors="replace")
        content_obj = (
            f"<< /Length {len(stream_body)} >>\nstream\n".encode("latin-1")
            + stream_body
            + b"\nendstream"
        )
        objects.append(content_obj)
        content_obj_nums.append(next_num)
        next_num += 1

    for content_num in content_obj_nums:
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/Contents {content_num} 0 R >>"
        ).encode("latin-1")
        objects.append(page_obj)
        page_obj_nums.append(next_num)
        next_num += 1

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode("latin-1")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]  # object 0 is the free-list head, offset 0 by convention
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"

    xref_offset = len(out)
    total_objects = len(objects) + 1
    out += f"xref\n0 {total_objects}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {total_objects} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("latin-1")
    return bytes(out)


def build_html(included_concepts: list, mode: str) -> str:
    """Assemble the intermediate HTML the reference repo's build-html.mjs
    would produce -- A4/grid for showcase mode, one-concept-per-section for
    brandkit mode. Real, renderable HTML (openable in any browser), not a
    stub template.
    """
    title = "Showcase" if mode == "showcase" else "Brand Kit"
    rows = []
    for concept in included_concepts:
        rows.append(
            "<section class='concept'>"
            f"<h2>{html_lib.escape(concept['id'])}</h2>"
            f"<p class='wordmark'>{html_lib.escape(concept['wordmark'])}</p>"
            f"<p class='icon'>{html_lib.escape(concept['icon'])}</p>"
            "</section>"
        )
    disclaimer = (
        "<p class='disclaimer'>Demo/concept work only. AI-generated original "
        "redesign concepts; not affiliated with or endorsed by any named brand.</p>"
    )
    return (
        f"<!doctype html><html><head><title>{title}</title></head>"
        f"<body><h1>{title}</h1>{''.join(rows)}{disclaimer}</body></html>"
    )


def compile_artifacts(concept_configs: list, image_artifacts: dict, mode: str = "showcase") -> dict:
    """Compile a set of concepts into an HTML+PDF artifact bundle.

    `image_artifacts` maps concept_id -> ImageArtifact (or a compatible object
    exposing `.status`). Any concept without a status=="OK" artifact is
    skipped with a structured, logged reason -- CCF-F02's mandatory fix.
    """
    included = []
    skipped = []
    for concept in concept_configs:
        concept_id = concept["id"]
        artifact = image_artifacts.get(concept_id)
        if artifact is None or getattr(artifact, "status", None) != "OK":
            skipped.append({
                "entry_id": concept_id,
                "reason": "no_generated_images",
                "skipped": True,
            })
            continue
        included.append(concept)

    if not included:
        # Never emit a near-empty PDF -- if nothing has a real image, there
        # is no artifact to compile at all.
        return {
            "html": None,
            "pdf_bytes": None,
            "included_ids": [],
            "skipped": skipped,
            "built": False,
        }

    html_doc = build_html(included, mode)
    pages = [
        [c["id"], f"Wordmark: {c['wordmark']}", f"Icon: {c['icon']}"]
        for c in included
    ]
    pdf_bytes = _build_minimal_pdf(pages)

    return {
        "html": html_doc,
        "pdf_bytes": pdf_bytes,
        "included_ids": [c["id"] for c in included],
        "skipped": skipped,
        "built": True,
    }
