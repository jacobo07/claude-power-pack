#!/usr/bin/env python3
"""CDIO-10 legal surface -- which legal pages a website needs, and whether it has them.

Dataset: vault/knowledge_base/cdio/CDIO-10-legal-surface.md. Templates:
vault/knowledge_base/cdio/legal-templates/ (General-Legal, CC0, vendored verbatim).

Two subcommands:

  plan  --jurisdiction us|eu|es [--commerce] [--saas]
        The pages a site in that jurisdiction needs, the template each one starts
        from, and the gaps no template covers.

  check <site_root> --jurisdiction us|eu|es [--saas] [--json]
        Static scan of a site's source or build. Emits CDIO verdicts scored by the
        real modules/cdio/scorer.py:
          legal-page-present       a required page has no route      (trust, critical)
          legal-fields-filled      a template field is still unfilled (trust, critical)
          legal-page-linked        nothing else in the site links it  (trust, critical)
          consent-before-tracking  eu/es: a cookie-setting tracker and
                                   no consent mechanism anywhere      (trust, critical)
        Exit 0 when the result is APPROVE, 1 otherwise, 2 when nothing was scanned.

What a static scan cannot see is reported, never passed: a consent mechanism that
exists is UNVERIFIED (only a browser can show it blocks the tracker), and tracker
detection is by signature, so "none detected" is listed with the vendors it knows.
This is not legal advice and never claims a page is legally sufficient.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules.cdio.scorer import Verdict, score_review  # noqa: E402

TEMPLATES = os.path.join(ROOT, "vault", "knowledge_base", "cdio", "legal-templates",
                         "templates")
JURISDICTIONS = ("us", "eu", "es")

# A page kind is recognised by one path segment (directory or file stem) matching
# its slug set in full. Slugs are normalised: lower case, accents removed, "_" -> "-".
KIND_SLUGS = {
    "privacy": ("privacy", "privacy-policy", "privacidad", "politica-de-privacidad",
                "politica-privacidad", "datenschutz"),
    "cookies": ("cookie", "cookies", "cookie-policy", "cookie-notice",
                "politica-de-cookies", "politica-cookies"),
    "terms": ("terms", "terms-of-use", "terms-of-service", "terms-and-conditions", "tos",
              "terminos", "terminos-de-uso", "terminos-y-condiciones", "condiciones-de-uso"),
    "legal_notice": ("aviso-legal", "legal-notice", "impressum", "imprint"),
    "sales_terms": ("condiciones-generales", "condiciones-de-contratacion",
                    "condiciones-de-venta", "terms-of-sale", "conditions-of-sale"),
    "dpa": ("dpa", "data-processing-addendum", "data-processing-agreement"),
}

# Template each kind starts from, per jurisdiction. None = no template exists here.
TEMPLATE_FOR = {
    "privacy": {"us": "privacy-policy-us", "eu": "privacy-policy-gdpr",
                "es": "privacy-policy-gdpr"},
    "cookies": {"us": "cookie-notice", "eu": "cookie-notice", "es": "cookie-notice"},
    "terms": {"us": "terms-of-use", "eu": "terms-of-use", "es": "terms-of-use"},
    "legal_notice": {"us": None, "eu": None, "es": None},
    "sales_terms": {"us": None, "eu": None, "es": None},
    "dpa": {"us": "dpa-us", "eu": "dpa-global", "es": "dpa-global"},
}

GAPS = {
    ("privacy", "eu"): "The template is written for a U.S. company with a 'Notice to European "
                       "Users'. For an EU-established controller GDPR is the main text: lead with "
                       "controller identity, purposes with legal basis, retention, rights and the "
                       "supervisory authority (CDIO-10 sec. 4).",
    ("privacy", "es"): "As eu, plus: written in Spanish, AEPD named as the authority, and a first "
                       "information layer next to every form (LOPDGDD art. 11).",
    ("cookies", "eu"): "A notice is not consent. Non-essential cookies need a banner that blocks "
                       "them until accepted, with Reject as prominent as Accept.",
    ("cookies", "es"): "As eu, following the AEPD cookie guide: Reject on the first layer, no "
                       "consent by scrolling, withdrawal as easy as acceptance.",
    ("terms", "eu"): "Remove the arbitration clause, the class-action and jury waivers, and any "
                     "choice of law that removes consumer protection; they are unenforceable "
                     "against EU consumers.",
    ("terms", "es"): "As eu; jurisdiction for consumers is their own domicile.",
    ("legal_notice", "es"): "No template. LSSI-CE art. 10: legal name, NIF, address, email, "
                            "commercial-registry data, and licences or professional body where "
                            "applicable (CDIO-10 sec. 4).",
    ("sales_terms", "eu"): "No template. Consumer sale terms: price with taxes, delivery, 14-day "
                           "withdrawal right with model form, guarantees. Pass --b2b when the "
                           "site sells only to businesses.",
    ("sales_terms", "es"): "No template. TRLGDCU arts. 97-98 pre-contract information and the "
                           "14-day withdrawal right with model form, in Spanish. Pass --b2b "
                           "when the site sells only to businesses.",
}

SCAN_EXT = (".html", ".htm", ".md", ".mdx", ".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue",
            ".svelte", ".astro", ".php", ".liquid", ".njk", ".hbs", ".ejs", ".json")
SKIP_DIRS = {"node_modules", ".git", ".next", ".vercel", ".turbo", ".cache", "coverage",
             ".svelte-kit", ".nuxt", ".output", "__pycache__", ".venv", "venv"}
SKIP_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"}
MAX_BYTES = 2_000_000

# Signatures of vendors that set cookies or similar identifiers in the browser.
COOKIE_TRACKERS = {
    "Google tag / Analytics": r"googletagmanager\.com|google-analytics\.com|\bgtag\s*\(|"
                              r"@next/third-parties/google",
    "Meta Pixel": r"connect\.facebook\.net|\bfbq\s*\(",
    "Hotjar": r"static\.hotjar\.com|_hjSettings",
    "Microsoft Clarity": r"clarity\.ms",
    "LinkedIn Insight": r"snap\.licdn\.com|_linkedin_partner_id",
    "TikTok Pixel": r"analytics\.tiktok\.com|\bttq\.load",
    "Mixpanel": r"cdn\.mxpnl\.com|mixpanel\.init",
    "PostHog": r"posthog\.init|i\.posthog\.com",
    "Segment": r"cdn\.segment\.com",
    "HubSpot": r"js\.hs-scripts\.com|js\.hs-analytics\.net",
    "Intercom": r"widget\.intercom\.io",
    "YouTube embed (not nocookie)": r"youtube\.com/embed",
}
# Analytics that the vendor documents as cookieless: privacy disclosure, not consent.
COOKIELESS_ANALYTICS = {
    "Plausible": r"plausible\.io/js|next-plausible",
    "Vercel Analytics": r"@vercel/analytics",
    "Vercel Speed Insights": r"@vercel/speed-insights",
    "Fathom": r"cdn\.usefathom\.com",
}
CONSENT_RE = re.compile(
    r"cookiebot|onetrust|optanon|klaro|cookieconsent|iubenda|cookieyes|complianz|termly|"
    r"usercentrics|didomi|gtag\(\s*['\"]consent['\"]|CookieBanner|ConsentBanner|"
    r"ConsentManager|cookie-consent", re.I)
COMMERCE_RE = re.compile(r"js\.stripe\.com|@stripe/|checkout\.shopify|lemonsqueezy|"
                         r"paddle\.js|cdn\.paddle\.com|/checkout\b", re.I)

# Unfilled-field markers that do not depend on the vocabulary.
_MARK_RE = re.compile(r"<mark\b|&lt;mark&gt;", re.I)
_INSERT_RE = re.compile(r"\[(?:INSERT|ADD)\b[^\]\n]{0,80}\]", re.I)
_BLANK_RE = re.compile(r"X{3}-X{3}-X{4}|_{4,}")
# Drafting notes addressed to whoever fills the template, e.g. the header row
# "TEMPLATE PRIVACY POLICY AND COOKIE NOTICE (GDPR compliant for U.S. Company ...)".
_NOTE_RE = re.compile(r"\bTEMPLATE [A-Z]{4,}[A-Z ]*|\[Note:[^\]\n]{0,80}")


def _norm(segment: str) -> str:
    s = unicodedata.normalize("NFKD", segment).encode("ascii", "ignore").decode()
    return s.lower().replace("_", "-")


def field_vocabulary(templates_dir: str = TEMPLATES) -> set:
    """Every bracketed field the vendored templates contain, read from the templates.

    `[<mark>CompanyName</mark>]` becomes `[CompanyName]` once the highlight is stripped,
    which is the form an unfilled field takes on a published page. Deriving the set from
    the real templates is deliberate: a hand-written list would only contain the fields
    its author thought of.
    """
    vocab = set()
    if not os.path.isdir(templates_dir):
        return vocab
    for name in sorted(os.listdir(templates_dir)):
        path = os.path.join(templates_dir, name, "template.md")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = re.sub(r"</?mark>", "", fh.read())
        for m in re.finditer(r"\[([^\[\]\n]{2,80})\](?!\()", text):
            token = m.group(1).strip()
            if re.search(r"[A-Za-z]", token):
                vocab.add(token)
    return vocab


def find_unfilled(text: str, vocab: set) -> list:
    """Return the unfilled template fields present in `text` (first hit per kind)."""
    hits = []
    for rx in (_MARK_RE, _INSERT_RE, _BLANK_RE, _NOTE_RE):
        hits.extend(m.group(0) for m in rx.finditer(text))
    for m in re.finditer(r"\[([^\[\]\n]{2,80})\](?!\()", text):
        if m.group(1).strip() in vocab:
            hits.append(m.group(0))
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def page_kind(rel_path: str):
    """Return (kind, slug) when one path segment names a legal page, else None."""
    parts = re.split(r"[\\/]", rel_path)
    stem = os.path.splitext(parts[-1])[0]
    for seg in [*parts[:-1], stem]:
        n = _norm(seg)
        for kind, slugs in KIND_SLUGS.items():
            if n in slugs:
                return kind, n
    return None


def _iter_files(site_root: str):
    for dirpath, dirnames, filenames in os.walk(site_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f in SKIP_FILES or not f.lower().endswith(SCAN_EXT):
                continue
            p = os.path.join(dirpath, f)
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
                with open(p, encoding="utf-8", errors="replace") as fh:
                    yield os.path.relpath(p, site_root), fh.read()
            except OSError:
                continue


def required_kinds(jurisdiction: str, *, cookie_trackers: bool, commerce: bool,
                   saas: bool) -> list:
    """Owner policy (CDIO-10 sec. 1): privacy and terms on every website, always."""
    kinds = ["privacy", "terms"]
    if cookie_trackers:
        kinds.append("cookies")
    if jurisdiction == "es":
        kinds.append("legal_notice")
    if commerce and jurisdiction in ("eu", "es"):
        kinds.append("sales_terms")
    if saas:
        kinds.append("dpa")
    return kinds


def plan(jurisdiction: str, *, commerce: bool = False, saas: bool = False) -> list:
    rows = []
    for kind in ("privacy", "terms", "cookies", "legal_notice", "sales_terms", "dpa"):
        if kind == "legal_notice" and jurisdiction != "es":
            continue
        if kind == "sales_terms" and not (commerce and jurisdiction in ("eu", "es")):
            continue
        if kind == "dpa" and not saas:
            continue
        tpl = TEMPLATE_FOR[kind][jurisdiction]
        gap = GAPS.get((kind, jurisdiction)) or (GAPS.get((kind, "eu"))
                                                if jurisdiction == "es" else None)
        rows.append({
            "kind": kind,
            "required": "if a cookie-setting tracker is used" if kind == "cookies" else "yes",
            "template": os.path.join(TEMPLATES, tpl, "template.md") if tpl else None,
            "gap": gap,
        })
    return rows


def check(site_root: str, jurisdiction: str, *, saas: bool = False,
          b2b: bool = False) -> dict:
    """b2b: the Owner declares the site sells only to businesses, so consumer sale
    terms are not required. A scan cannot tell who the buyer is; the default assumes
    consumers, because that is the reading under which a missing page is a breach."""
    if jurisdiction not in JURISDICTIONS:
        raise ValueError(f"jurisdiction must be one of {JURISDICTIONS}")
    vocab = field_vocabulary()
    files = list(_iter_files(site_root))
    pages, others = {}, []
    for rel, text in files:
        hit = page_kind(rel)
        if hit:
            pages.setdefault(hit[0], []).append((rel, hit[1], text))
        else:
            others.append((rel, text))

    blob = "\n".join(t for _, t in files)
    trackers = sorted(n for n, rx in COOKIE_TRACKERS.items() if re.search(rx, blob, re.I))
    cookieless = sorted(n for n, rx in COOKIELESS_ANALYTICS.items()
                        if re.search(rx, blob, re.I))
    consent = CONSENT_RE.search(blob)
    commerce = COMMERCE_RE.search(blob) is not None
    required = required_kinds(jurisdiction, cookie_trackers=bool(trackers),
                              commerce=commerce and not b2b, saas=saas)

    verdicts, unverified, notes = [], [], []
    for kind in required:
        found = pages.get(kind, [])
        tpl = TEMPLATE_FOR[kind][jurisdiction]
        if not found:
            verdicts.append(Verdict(
                "legal-page-present", "trust", "fail", "critical",
                observed=f"no {kind} page: no path segment matches {list(KIND_SLUGS[kind][:4])}",
                recommendation=(f"build it from legal-templates/templates/{tpl}/template.md"
                                if tpl else f"no template: {GAPS.get((kind, jurisdiction), '')}")))
            continue
        verdicts.append(Verdict("legal-page-present", "trust", "pass",
                                observed=f"{kind}: {found[0][0]}"))

    for kind, found in sorted(pages.items()):
        for rel, slug, text in found:
            unfilled = find_unfilled(text, vocab)
            if unfilled:
                verdicts.append(Verdict(
                    "legal-fields-filled", "trust", "fail", "critical",
                    observed=f"{rel}: {len(unfilled)} unfilled field(s), first {unfilled[:3]}",
                    recommendation="fill each from facts the Owner supplied; never invent one"))
            else:
                verdicts.append(Verdict("legal-fields-filled", "trust", "pass",
                                        observed=f"{rel}: no template field left"))
        slug = found[0][1]
        link_rx = re.compile(r"[\"'`/]" + re.escape(slug) + r"(?:\.html?)?(?=[\"'`/#?)]|$)",
                             re.M)
        if any(link_rx.search(t) for _, t in others):
            verdicts.append(Verdict("legal-page-linked", "trust", "pass",
                                    observed=f"{kind}: '/{slug}' referenced outside the page"))
        else:
            verdicts.append(Verdict(
                "legal-page-linked", "trust", "fail", "critical",
                observed=f"{kind}: no file outside the page references '/{slug}'",
                recommendation="link it from the footer of every page"))

    if trackers and jurisdiction in ("eu", "es"):
        if consent:
            unverified.append(f"consent mechanism found ('{consent.group(0)}'); whether it "
                              f"blocks {trackers} until acceptance needs a browser run")
        else:
            verdicts.append(Verdict(
                "consent-before-tracking", "trust", "fail", "critical",
                observed=f"cookie-setting tracker(s) {trackers} and no consent mechanism found",
                recommendation="add a consent banner that blocks them until accepted"))
    if not trackers:
        notes.append("no cookie-setting tracker detected among the known signatures "
                     f"({len(COOKIE_TRACKERS)} vendors); a vendor outside that list is not seen")
    if cookieless:
        notes.append(f"cookieless analytics {cookieless}: disclose in the privacy page")
    if commerce and jurisdiction == "us":
        notes.append("checkout detected: terms of sale are advisable; not required by this gate")

    result = score_review(verdicts)
    return {
        "site_root": os.path.abspath(site_root),
        "jurisdiction": jurisdiction,
        "files_scanned": len(files),
        "pages": {k: [r for r, _, _ in v] for k, v in sorted(pages.items())},
        "required": required,
        "triggers": {"cookie_trackers": trackers, "cookieless_analytics": cookieless,
                     "consent_mechanism": consent.group(0) if consent else None,
                     "commerce": commerce},
        "verdicts": [v.to_json() for v in verdicts],
        "unverified": unverified,
        "notes": notes,
        "score": result.to_json(),
    }


def _print_report(rep: dict) -> None:
    s = rep["score"]
    print(f"CDIO-10 legal surface  {rep['site_root']}  ({rep['jurisdiction']}, "
          f"{rep['files_scanned']} files)")
    print(f"verdict={s['verdict']} score={s['score']} is_done={s['is_done']}")
    for v in rep["verdicts"]:
        if v["status"] == "fail":
            print(f"  FAIL [{v['severity']}] {v['criterion']}: {v['observed']}")
            if v["recommendation"]:
                print(f"       -> {v['recommendation']}")
    for v in rep["verdicts"]:
        if v["status"] == "pass":
            print(f"  pass {v['criterion']}: {v['observed']}")
    for u in rep["unverified"]:
        print(f"  UNVERIFIED {u}")
    for n in rep["notes"]:
        print(f"  note {n}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--jurisdiction", required=True, choices=JURISDICTIONS)
    p.add_argument("--commerce", action="store_true")
    p.add_argument("--saas", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("site_root")
    c.add_argument("--jurisdiction", required=True, choices=JURISDICTIONS)
    c.add_argument("--saas", action="store_true")
    c.add_argument("--b2b", action="store_true",
                   help="the site sells only to businesses: no consumer sale terms")
    c.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "plan":
        for row in plan(a.jurisdiction, commerce=a.commerce, saas=a.saas):
            print(f"{row['kind']:<13} required: {row['required']}")
            print(f"{'':<13} template: {row['template'] or 'none in legal-templates'}")
            if row["gap"]:
                print(f"{'':<13} gap: {row['gap']}")
        return 0

    if not os.path.isdir(a.site_root):
        print(f"not a directory: {a.site_root}", file=sys.stderr)
        return 2
    rep = check(a.site_root, a.jurisdiction, saas=a.saas, b2b=a.b2b)
    if rep["files_scanned"] == 0:
        print(f"nothing scanned under {a.site_root}: no verdict", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        _print_report(rep)
    return 0 if rep["score"]["is_done"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
