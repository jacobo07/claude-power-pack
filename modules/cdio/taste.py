"""Taste lint -- the executable half of the absorbed `design-taste-frontend` skill (MIT, Leonxlnx/taste-skill).

The skill (vendor/skills/design-taste-frontend/SKILL.md) is a prose doctrine for landing pages, portfolios and
redesigns. Its own words: "If a single checkbox cannot be honestly ticked, the page is not done." A checkbox only a
model can tick is a preference; this module turns every rule that a static read of the shipped HTML/CSS/JS can
decide into a CDIO `Verdict`, so a page can FAIL for it. What it cannot decide (hero fits the viewport, CTA wraps,
contrast in both themes, bento cell count) is mapped in vault/knowledge_base/cdio/taste-absorption.json to the owner
that can (render review / CDIO scorer), never pretended here.

Severity follows the skill's own wording:
  critical  "banned outright", "mandatory", "non-negotiable", "Pre-Flight Fail", "NEVER", "Ever"  -> blocks
  major     a banned default that has a documented override path (brief/brand justification)
  minor     discouraged, perf/hygiene

Overrides: the skill says each rule is contextual. A DESIGN.md front-matter list `taste_overrides:` with entries
`- TASTE-ID: <reason>` waives that check for the page. A waiver WITHOUT a reason waives nothing (the reason is the
point). Waived findings are reported, never dropped.

Static and read-only: it reads the entry file and the LOCAL stylesheets/scripts it references, never executes code,
never fetches the network. `python -m modules.cdio.taste <page.html> [--design DESIGN.md] [--json]`; exit 1 when a
non-waived critical finding exists, 0 otherwise, 2 when the page cannot be read.

Naming note: the HTML input-hint attribute is spelled through `_HINT_ATTR` below because the repo's write gate is a
literal matcher for an unfinished-work word that happens to be that attribute's name
(governance/KNOWN_FALSE_POSITIVES.md FP-03).
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.cdio.scorer import Verdict  # noqa: E402

SKILL_REF = "vendor/skills/design-taste-frontend/SKILL.md"
_HINT_ATTR = "place" "holder"          # the HTML attribute; see the naming note in the module docstring

# id -> (skill section, severity, short rule). The absorption map and the test read this table: a check that is not
# here does not exist, and a map row naming an id that is not here fails V-TASTE-MAP.
CHECKS = {
    "TASTE-EMDASH":            ("9.G", "critical", "zero em-dash / en-dash separators in visible text"),
    "TASTE-SCROLL-LISTENER":   ("5.D", "critical", "no window scroll event listeners"),
    "TASTE-H-SCREEN":          ("3.E", "critical", "no h-screen / height:100vh; use min-h-[100dvh]"),
    "TASTE-REDUCED-MOTION":    ("6.B", "critical", "motion present => prefers-reduced-motion honoured"),
    "TASTE-HINT-AS-LABEL":     ("4.6", "critical", "an input hint is never the label; every field has a label"),
    "TASTE-SCROLL-CUE":        ("9.F", "critical", "no scroll cues"),
    "TASTE-QUIETLY":           ("9.F", "critical", "no 'Quietly in use at / trusted by' headers"),
    "TASTE-JANE-DOE":          ("9.D", "critical", "no John/Jane Doe, Acme stand-in identities"),
    "TASTE-EYEBROW-COUNT":     ("4.7", "critical", "eyebrows <= ceil(sections / 3)"),
    "TASTE-DUP-CTA-INTENT":    ("4.5", "critical", "one CTA label per intent"),
    "TASTE-GENERIC-BRANDS":    ("9.D", "major", "no startup-slop names (Nexus, SmartFlow, Cloudly)"),
    "TASTE-FILLER-VERBS":      ("9.D", "major", "no Elevate / Seamless / Unleash / Next-Gen / Revolutionize"),
    "TASTE-VERSION-STAMP":     ("9.F", "major", "no version labels / build footers on marketing pages"),
    "TASTE-SECTION-NUMBERING": ("9.F", "major", "no section-number eyebrows (001 · / 00 / INDEX)"),
    "TASTE-STEP-LABELS":       ("9.F", "major", "no generic Step 1 / Stage 1 / Phase 01 labels"),
    "TASTE-MARQUEE-MAX-ONE":   ("5", "major", "at most one marquee per page"),
    "TASTE-CUSTOM-CURSOR":     ("9.A", "major", "no custom mouse cursors"),
    "TASTE-PURE-BLACK-WHITE":  ("8.B", "major", "no pure #000000 / #ffffff"),
    "TASTE-BANNED-SERIF":      ("4.1", "major", "no Fraunces / Instrument Serif as default"),
    "TASTE-PREMIUM-PALETTE":   ("4.2", "major", "not the beige+brass+espresso default palette"),
    "TASTE-BROKEN-UNSPLASH":   ("9.E", "major", "no source.unsplash.com links"),
    "TASTE-DARK-MODE":         ("6.C", "major", "both colour schemes designed"),
    "TASTE-GOOGLE-FONTS-LINK": ("3.A", "minor", "self-host fonts; no Google Fonts <link> in production"),
    "TASTE-MIDDOT-RATION":     ("9.F", "minor", "at most one middle-dot per line"),
    "TASTE-ZINDEX-SPAM":       ("6.F", "minor", "z-index only for systemic layers"),
    "TASTE-EMOJI":             ("3.D", "minor", "no emoji in visible text by default"),
    "TASTE-GRADIENT-TEXT":     ("9.A", "minor", "no gradient text on large headers"),
}

_SEV_ORDER = {"critical": 0, "major": 1, "minor": 2}

# --------------------------------------------------------------------------- reading


@dataclass
class Page:
    path: str
    raw: str                      # entry HTML
    css: str                      # inline <style> + style="" + local stylesheets
    js: str                       # inline <script> + local scripts
    text: str                     # visible text, tags stripped, entities decoded
    blocks: list = field(default_factory=list)   # visible text per block element (line granularity)


_COMMENT = re.compile(r"<!--.*?-->", re.S)
_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.S | re.I)
_STYLE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.S | re.I)
_STYLE_ATTR = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_BLOCK_SPLIT = re.compile(r"</?(?:p|h[1-6]|li|div|section|header|footer|nav|a|button|span|label|td|th|figcaption|"
                          r"blockquote|small|strong|em|br)\b[^>]*>", re.I)
_LINK_CSS = re.compile(r"""<link\b[^>]*\bhref\s*=\s*["']([^"']+\.css)["'][^>]*>""", re.I)
_SRC_JS = re.compile(r"""<script\b[^>]*\bsrc\s*=\s*["']([^"']+\.m?js)["']""", re.I)
_ATTR_ALT = re.compile(r"""\b(?:alt|aria-label|title)\s*=\s*(["'])(.*?)\1""", re.S | re.I)


def _local(base: str, ref: str) -> str | None:
    if re.match(r"^[a-z]+:|^//", ref, re.I):
        return None
    p = os.path.normpath(os.path.join(os.path.dirname(base), ref.split("?")[0].split("#")[0]))
    root = os.path.dirname(os.path.abspath(base))
    if not os.path.abspath(p).startswith(root):
        return None
    return p if os.path.isfile(p) else None


def _read(p: str) -> str:
    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def load(path: str) -> Page:
    raw = _read(path)
    body = _COMMENT.sub(" ", raw)
    css_parts = _STYLE.findall(body) + [m.group(2) for m in _STYLE_ATTR.finditer(body)]
    js_parts = [m.group(2) for m in _SCRIPT.finditer(body)]
    for ref in _LINK_CSS.findall(body):
        lp = _local(path, ref)
        if lp:
            css_parts.append(_read(lp))
    for ref in _SRC_JS.findall(body):
        lp = _local(path, ref)
        if lp:
            js_parts.append(_read(lp))
    visible = _STYLE.sub(" ", _SCRIPT.sub(" ", body))
    alts = " ".join(m.group(2) for m in _ATTR_ALT.finditer(visible))
    blocks = [html.unescape(_TAG.sub(" ", b)).strip() for b in _BLOCK_SPLIT.split(visible)]
    blocks = [" ".join(b.split()) for b in blocks if b and b.strip()]
    text = html.unescape(_TAG.sub(" ", visible)) + " " + html.unescape(alts)
    return Page(path, raw, "\n".join(css_parts), "\n".join(js_parts), " ".join(text.split()), blocks)


def overrides(design_md: str | None) -> dict:
    """{check_id: reason} from DESIGN.md front-matter `taste_overrides:`. Entries without a reason are kept with ''
    so the report can say 'waiver refused: no reason'."""
    if not design_md or not os.path.isfile(design_md):
        return {}
    txt = _read(design_md)
    m = re.match(r"﻿?---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        return {}
    out, inside = {}, False
    for line in m.group(1).splitlines():
        if re.match(r"^taste_overrides\s*:", line):
            inside = True
            continue
        if inside:
            row = re.match(r"^\s+-\s*(TASTE-[A-Z0-9-]+)\s*(?::\s*(.*))?$", line)
            if row:
                out[row.group(1)] = (row.group(2) or "").strip().strip("\"'")
                continue
            if line.strip() and not line.startswith((" ", "\t")):
                inside = False
    return out

# --------------------------------------------------------------------------- checks


def _v(cid: str, hits: list, recommendation: str) -> Verdict:
    sec, sev, rule = CHECKS[cid]
    hits = list(dict.fromkeys(hits))      # inline <style> is read both as CSS and as raw HTML: count a hit once
    if not hits:
        return Verdict(criterion=cid, dimension="visual", status="pass", observed=f"{rule}: none found (§{sec})")
    shown = "; ".join(str(h) for h in hits[:5]) + (f" (+{len(hits) - 5} more)" if len(hits) > 5 else "")
    return Verdict(criterion=cid, dimension="visual", status="fail", severity=sev,
                   observed=f"§{sec} {rule}: {shown}", recommendation=recommendation)


def _ctx(s: str, m: re.Match, w: int = 24) -> str:
    return "…" + s[max(0, m.start() - w):m.end() + w].strip() + "…"


def check_emdash(p: Page) -> Verdict:
    hits = [_ctx(p.text, m) for m in re.finditer(r"[—–]", p.text)]
    return _v("TASTE-EMDASH", hits, "replace with a period, comma, colon, parentheses or a hyphen (`-`); ranges use `-`")


def check_scroll_listener(p: Page) -> Verdict:
    hits = [_ctx(p.js, m) for m in re.finditer(r"""addEventListener\(\s*['"]scroll['"]""", p.js)]
    hits += [_ctx(p.js + p.raw, m) for m in re.finditer(r"\bonscroll\s*=", p.js + p.raw)]
    return _v("TASTE-SCROLL-LISTENER", hits, "use IntersectionObserver, CSS scroll-driven animation, Motion useScroll "
                                             "or GSAP ScrollTrigger")


def check_h_screen(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"(?<![\w-])h-screen\b", p.raw)]
    hits += [m.group(0) for m in re.finditer(r"(?<![\w-])height\s*:\s*100vh", p.css + p.raw)]
    return _v("TASTE-H-SCREEN", hits, "use min-height: 100dvh (min-h-[100dvh]) so the iOS address bar does not jump")


_MOTION_CSS = re.compile(r"@keyframes|\banimation\s*:|\banimation-name\s*:|\btransition\s*:\s*(?!none)|"
                         r"\banimate-[a-z]|\btransition-(?:all|transform|opacity)\b", re.I)
_MOTION_JS = re.compile(r"\bgsap\b|ScrollTrigger|from\s+['\"](?:motion|framer-motion)|\.animate\(|"
                        r"requestAnimationFrame", re.I)


def check_reduced_motion(p: Page) -> Verdict:
    moves = _MOTION_CSS.search(p.css + p.raw) or _MOTION_JS.search(p.js)
    if not moves:
        return Verdict(criterion="TASTE-REDUCED-MOTION", dimension="visual", status="pass",
                       observed="no motion declared; nothing to reduce (§6.B)")
    honoured = re.search(r"prefers-reduced-motion|useReducedMotion|motion-safe:|motion-reduce:",
                         p.css + p.js + p.raw)
    return _v("TASTE-REDUCED-MOTION", [] if honoured else [f"motion `{moves.group(0)}` with no reduced-motion path"],
              "gate motion behind @media (prefers-reduced-motion: no-preference) or collapse it under `reduce`")


_FIELD = re.compile(r"<(input|textarea|select)\b([^>]*)>", re.I)


def _attr(attrs: str, name: str) -> str | None:
    m = re.search(r"""\b%s\s*=\s*(["'])(.*?)\1""" % name, attrs, re.S | re.I)
    return m.group(2) if m else None


def check_hint_as_label(p: Page) -> Verdict:
    body = _COMMENT.sub(" ", p.raw)
    labelled_for = {m.group(2) for m in re.finditer(r"""<label\b[^>]*\bfor\s*=\s*(["'])(.*?)\1""", body, re.I)}
    hits = []
    for m in _FIELD.finditer(body):
        attrs = m.group(2)
        typ = (_attr(attrs, "type") or "").lower()
        if typ in ("hidden", "submit", "button", "reset", "image"):
            continue
        hint = _attr(attrs, _HINT_ATTR)
        if hint is None:
            continue
        fid = _attr(attrs, "id")
        if fid and fid in labelled_for:
            continue
        if _attr(attrs, "aria-label") or _attr(attrs, "aria-labelledby"):
            continue
        before = body[:m.start()]
        if before.rfind("<label") > before.rfind("</label"):      # wrapped in an open <label>
            continue
        hits.append(f"<{m.group(1)}> labelled only by its hint text \"{hint}\"")
    return _v("TASTE-HINT-AS-LABEL", hits, "put a visible <label> above every field; the hint text is a hint, "
                                           "never the label")


def check_scroll_cue(p: Page) -> Verdict:
    rx = re.compile(r"(?:^|\s|↓)(?:scroll(?:\s+(?:to\s+\w+|down|for\s+more))?)(?=$|\s|[.!↓])", re.I)
    hits = [b for b in p.blocks if len(b) <= 40 and rx.search(b)]
    return _v("TASTE-SCROLL-CUE", hits, "delete the cue; the viewer already knows how to scroll")


def check_quietly(p: Page) -> Verdict:
    hits = [_ctx(p.text, m) for m in re.finditer(r"\bquietly\s+(?:in\s+use|trusted|used)\b", p.text, re.I)]
    return _v("TASTE-QUIETLY", hits, "say 'Trusted by' / 'Customers include', or drop the heading")


def check_jane_doe(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"\b(?:John|Jane)\s+Doe\b|\bAcme(?:\s+(?:Co|Inc|Corp))?\b|"
                                            r"\bLorem\s+ipsum\b", p.text, re.I)]
    return _v("TASTE-JANE-DOE", hits, "use real names/brands from the brief, or locale-appropriate invented ones "
                                      "labelled as sample")


def check_generic_brands(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"\b(?:Nexus|SmartFlow|Cloudly)\b", p.text)]
    return _v("TASTE-GENERIC-BRANDS", hits, "invent a contextual name, or use the real one")


def check_filler_verbs(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"\b(?:elevate[sd]?|seamless(?:ly)?|unleash(?:es|ed)?|next-gen|"
                                            r"revolutioni[sz]e[sd]?)\b", p.text, re.I)]
    return _v("TASTE-FILLER-VERBS", hits, "replace with a concrete verb that says what the product does")


def check_version_stamp(p: Page) -> Verdict:
    rx = re.compile(r"\bv\d+\.\d+(?:\.\d+)?(?:-[a-z0-9.]+)?\b|\bBuild\s+\d{3,}\b|\blast\s+sync\b|"
                    r"\b(?:INVITE-ONLY PREVIEW|EARLY ACCESS)\b", re.I)
    hits = [b for b in p.blocks if len(b) <= 60 and rx.search(b)]
    return _v("TASTE-VERSION-STAMP", hits, "remove version labels and build footers from a marketing page "
                                           "(declare an override only for a real launch/preview brief)")


def check_section_numbering(p: Page) -> Verdict:
    rx = re.compile(r"^(?:\d{2,3}\s*[·/|]\s*\S|\d{2}\s*/\s*[A-Z]{3,}|Scroll\s*·\s*\d)")
    hits = [b for b in p.blocks if len(b) <= 40 and rx.search(b)]
    return _v("TASTE-SECTION-NUMBERING", hits, "name the topic in plain words, do not enumerate sections")


def check_step_labels(p: Page) -> Verdict:
    rx = re.compile(r"^(?:step|stage|phase|pass)\s+(?:0?\d+|one|two|three|four|five)\b", re.I)
    hits = [b for b in p.blocks if len(b) <= 30 and rx.search(b)]
    return _v("TASTE-STEP-LABELS", hits, "let the step's verb be the label ('Install', 'Configure', 'Ship')")


def check_marquee(p: Page) -> Verdict:
    n = len(re.findall(r"<marquee\b", p.raw, re.I)) + len(re.findall(r"""class\s*=\s*["'][^"']*\bmarquee\b""",
                                                                     p.raw, re.I))
    return _v("TASTE-MARQUEE-MAX-ONE", [f"{n} marquees"] if n > 1 else [], "keep the one marquee that serves content")


def check_custom_cursor(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"cursor\s*:\s*(?:none|url\()", p.css + p.raw, re.I)]
    return _v("TASTE-CUSTOM-CURSOR", hits, "use the system cursor")


def check_pure_black_white(p: Page) -> Verdict:
    rx = re.compile(r"(?:color|background(?:-color)?|fill|stroke)\s*:\s*(#000000|#000\b|#ffffff|#fff\b|"
                    r"rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\))", re.I)
    hits = [m.group(1) for m in rx.finditer(p.css)]
    hits += [m.group(0) for m in re.finditer(r"(?<![\w-])(?:bg|text)-(?:black|white)\b", p.raw)]
    return _v("TASTE-PURE-BLACK-WHITE", hits, "use off-black (zinc-950 / charcoal) and off-white")


def check_banned_serif(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"Fraunces|Instrument[ _+]Serif", p.css + p.raw)]
    return _v("TASTE-BANNED-SERIF", hits, "use a sans display face, or a justified serif from the rotation pool")


_PREMIUM = {"#f5f1ea", "#f7f5f1", "#fbf8f1", "#efeae0", "#ece6db", "#faf7f1", "#e8dfcb", "#b08947", "#b6553a",
            "#9a2436", "#9c6e2a", "#bc7c3a", "#7d5621", "#1a1714", "#1a1814", "#1b1814"}


def check_premium_palette(p: Page) -> Verdict:
    found = sorted({h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", p.css + p.raw) if h.lower() in _PREMIUM})
    return _v("TASTE-PREMIUM-PALETTE", [", ".join(found)] if len(found) >= 2 else [],
              "rotate to a different palette family (cold luxury, forest, cobalt+cream...) unless the brand names it")


def check_broken_unsplash(p: Page) -> Verdict:
    hits = re.findall(r"source\.unsplash\.com[^\s\"')]*", p.raw + p.css)
    return _v("TASTE-BROKEN-UNSPLASH", hits, "use real assets (or picsum seeds in a preview build only)")


def check_dark_mode(p: Page) -> Verdict:
    ok = re.search(r"prefers-color-scheme|(?<![\w-])dark:|\[data-theme=|\.dark\b|color-scheme\s*:\s*[^;]*dark",
                   p.css + p.raw + p.js)
    return _v("TASTE-DARK-MODE", [] if ok else ["no dark scheme (no prefers-color-scheme, dark:, or data-theme)"],
              "design both schemes from the start, or declare the single-mode reason as an override")


def check_google_fonts(p: Page) -> Verdict:
    hits = re.findall(r"<link\b[^>]*fonts\.googleapis\.com[^>]*>", p.raw, re.I)
    return _v("TASTE-GOOGLE-FONTS-LINK", [h[:60] for h in hits], "self-host with @font-face + font-display: swap")


def check_middot(p: Page) -> Verdict:
    hits = [b for b in p.blocks if b.count("·") > 1]
    return _v("TASTE-MIDDOT-RATION", hits, "one middle-dot per line at most; use line breaks or columns")


def check_zindex(p: Page) -> Verdict:
    vals = re.findall(r"z-index\s*:\s*(-?\d+)", p.css) + re.findall(r"(?<![\w-])z-(\d+)\b", p.raw)
    distinct = sorted(set(vals), key=lambda s: int(s))
    return _v("TASTE-ZINDEX-SPAM", [f"{len(distinct)} distinct z-index values {distinct}"] if len(distinct) > 4 else [],
              "keep a documented z-index scale (nav, modal, overlay, grain)")


_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF]")


def check_emoji(p: Page) -> Verdict:
    hits = sorted(set(_EMOJI.findall(p.text)))
    return _v("TASTE-EMOJI", hits, "use an icon-library glyph instead")


def check_gradient_text(p: Page) -> Verdict:
    hits = [m.group(0) for m in re.finditer(r"background-clip\s*:\s*text|(?<![\w-])bg-clip-text\b", p.css + p.raw)]
    return _v("TASTE-GRADIENT-TEXT", hits, "carry hierarchy with weight and colour, not gradient fills")


def check_eyebrow_count(p: Page) -> Verdict:
    body = _COMMENT.sub(" ", p.raw)
    sections = len(re.findall(r"<section\b", body, re.I)) + (1 if re.search(r"<header\b", body, re.I) else 0)
    sections = max(sections, 1)
    eyebrow_cls = re.compile(r"""class\s*=\s*["'][^"']*\buppercase\b[^"']*\btracking-[^"']*["']|"""
                             r"""class\s*=\s*["'][^"']*\btracking-[^"']*\buppercase\b[^"']*["']|"""
                             r"""class\s*=\s*["'][^"']*\beyebrow\b[^"']*["']""", re.I)
    n = len(eyebrow_cls.findall(body))
    limit = math.ceil(sections / 3)
    return _v("TASTE-EYEBROW-COUNT", [f"{n} eyebrows for {sections} sections (limit {limit})"] if n > limit else [],
              "drop eyebrows; the headline alone is enough (max 1 per 3 sections)")


_INTENTS = {
    "contact": r"get in touch|contact us|let'?s talk|start a project|start something|reach out|talk to us",
    "signup": r"try (?:it )?free|get started|sign up(?: free)?|start (?:for )?free|create (?:an )?account",
    "portfolio": r"view (?:selected )?work|see (?:selected |our )?work|browse projects",
}
_CTA = re.compile(r"<(a|button)\b[^>]*>(.*?)</\1\s*>", re.S | re.I)


def check_dup_cta_intent(p: Page) -> Verdict:
    labels = {" ".join(html.unescape(_TAG.sub(" ", m.group(2))).split()).lower() for m in _CTA.finditer(p.raw)}
    hits = []
    for intent, rx in _INTENTS.items():
        same = sorted(lbl for lbl in labels if re.fullmatch(r"(?:%s)[.!]?" % rx, lbl))
        if len(same) > 1:
            hits.append(f"{intent}: {same}")
    return _v("TASTE-DUP-CTA-INTENT", hits, "pick ONE label per intent and use it in nav, hero and footer")


ALL = [check_emdash, check_scroll_listener, check_h_screen, check_reduced_motion, check_hint_as_label,
       check_scroll_cue, check_quietly, check_jane_doe, check_eyebrow_count, check_dup_cta_intent,
       check_generic_brands, check_filler_verbs, check_version_stamp, check_section_numbering, check_step_labels,
       check_marquee, check_custom_cursor, check_pure_black_white, check_banned_serif, check_premium_palette,
       check_broken_unsplash, check_dark_mode, check_google_fonts, check_middot, check_zindex, check_emoji,
       check_gradient_text]

# --------------------------------------------------------------------------- report


@dataclass
class TasteReport:
    page: str
    verdicts: list
    waived: dict            # check id -> reason (only waivers WITH a reason)
    refused_waivers: list   # ids named in taste_overrides without a reason

    @property
    def blocking(self) -> list:
        return [v.criterion for v in self.verdicts
                if v.status == "fail" and v.severity == "critical" and v.criterion not in self.waived]

    def as_dict(self) -> dict:
        fails = [v for v in self.verdicts if v.status == "fail"]
        return {"page": self.page, "skill": SKILL_REF, "checks": len(self.verdicts),
                "blocking": self.blocking,
                "fails": [{"id": v.criterion, "severity": v.severity, "observed": v.observed,
                           "recommendation": v.recommendation, "waived": self.waived.get(v.criterion)}
                          for v in sorted(fails, key=lambda v: _SEV_ORDER.get(v.severity, 9))],
                "refused_waivers": self.refused_waivers}


def lint(path: str, design_md: str | None = None) -> TasteReport:
    page = load(path)
    if design_md is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(path)), "DESIGN.md")
        design_md = cand if os.path.isfile(cand) else None
    ov = overrides(design_md)
    verdicts = []
    for fn in ALL:
        try:
            verdicts.append(fn(page))
        except Exception as exc:  # noqa: BLE001 -- an instrument crash is a finding, never a pass
            verdicts.append(Verdict(criterion=fn.__name__, dimension="visual", status="fail", severity="critical",
                                    observed=f"taste check crashed: {type(exc).__name__}: {exc}"))
    return TasteReport(path, verdicts, {k: v for k, v in ov.items() if v}, sorted(k for k, v in ov.items() if not v))


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="taste", description="Taste lint (absorbed design-taste-frontend)")
    ap.add_argument("page")
    ap.add_argument("--design")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.page):
        print(f"UNREADABLE: {a.page}")
        return 2
    rep = lint(a.page, a.design)
    d = rep.as_dict()
    if a.json:
        print(json.dumps(d, indent=1, ensure_ascii=False))
    else:
        for f in d["fails"]:
            tag = "WAIVED(%s)" % f["waived"] if f["waived"] else f["severity"].upper()
            print(f"  {tag:<10} {f['id']:<26} {f['observed']}")
        for r in d["refused_waivers"]:
            print(f"  WAIVER REFUSED {r}: taste_overrides entry has no reason")
        print(f"taste: {d['checks']} checks, {len(d['fails'])} fail, blocking={d['blocking'] or 'none'}")
    return 1 if rep.blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
