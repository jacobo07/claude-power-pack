#!/usr/bin/env python3
"""test_cdio_legal.py -- done-gate for CDIO-10, the legal surface (V-CDIO-LEGAL-*).

Spec: vault/specs/cdio-10-legal-surface.md. Hermetic: reads the dataset, the
vendored templates, the CDIO wiring points and the agents' live mirrors, and
drives the real checker over synthetic sites built in a temp dir.

  V-CDIO-LEGAL-VENDORED   12 templates present and byte-identical to the vendored
                          commit (line endings normalised); NOTICE + CC0 recorded
  V-CDIO-LEGAL-DATASET    CDIO-10 sealed, governed by CDIO-00, source + evidence
  V-CDIO-LEGAL-CRITERIA   every sec.3 criterion names a dimension and a severity
  V-CDIO-LEGAL-SCORABLE   each criterion, failing, is accepted by the real scorer
  V-CDIO-LEGAL-VOCAB      the unfilled-field vocabulary is read from the templates
                          and every web template, unfilled, is caught (positive control)
  V-CDIO-LEGAL-CHECK      bad site BLOCKs on each defect; control site APPROVEs
                          with consent reported UNVERIFIED; unlinked page BLOCKs;
                          --b2b drops consumer sale terms; empty dir exits 2
  V-CDIO-LEGAL-HONEST     PLANNED browser check, not-legal-advice and the
                          not-universalised list stay recorded
  V-CDIO-LEGAL-WIRED      kernel, Lens 4, sec.3 severity, three agents
  V-CDIO-LEGAL-MIRRORS    repo agents == live agents (red drill on drift)
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

# One parser for one grammar: the criterion grammar and mirror comparison are CDIO-08's.
from test_cdio_mobile import (  # noqa: E402
    AGENTS, CDIO, HOME_CLAUDE, _read, _section, mirror_drift, parse_criteria)
from modules.cdio import legal_surface as ls  # noqa: E402

DATASET = os.path.join(CDIO, "CDIO-10-legal-surface.md")
VENDOR = os.path.join(CDIO, "legal-templates")
# sha256[:16] of each template.md with CRLF normalised to LF, at upstream commit
# 6d6805425eabd41bed86fc1e2ec51612760f716c. Change only when re-vendoring.
TEMPLATE_PINS = {
    "advisor-agreement": "bd6851ce93e61bb8",
    "business-associate-agreement": "1f9902a8f60ff5c4",
    "cookie-notice": "f95930b862b2ca87",
    "dpa-global": "27e8c6ea6189900c",
    "dpa-us": "1964d2af87d6af37",
    "employee-offer-letter": "d6245f09c91c1626",
    "master-services-agreement": "c30f258e5378f9f6",
    "mutual-nda": "2b790eda57208b5b",
    "one-way-nda": "639846700c0cda7a",
    "privacy-policy-gdpr": "d51ebccc012a5be6",
    "privacy-policy-us": "9e5dd940135752e6",
    "terms-of-use": "b36712ca8c15160a",
}
WEB_TEMPLATES = ("privacy-policy-us", "privacy-policy-gdpr", "cookie-notice", "terms-of-use")
EXPECTED_CRITERIA = {
    "legal-page-present", "legal-fields-filled", "legal-facts-from-owner",
    "legal-page-linked", "consent-before-tracking", "reject-as-easy-as-accept",
    "jurisdiction-fit", "form-first-layer", "cookie-notice-matches-trackers",
    "legal-language-matches-site", "not-claimed-as-reviewed", "us-opt-out-link",
    "last-updated-stated", "legal-page-readable",
}
VOCAB_FLOOR = 80  # fields found in the vendored templates on 2026-10-08: 99

_passes = 0
_fails = 0


def _ok(name, detail):
    global _passes
    _passes += 1
    print(f"[PASS] {name}: {detail}")


def _fail(name, detail):
    global _fails
    _fails += 1
    print(f"[FAIL] {name}: {detail}")


def _norm_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()[:16]


def _site(root, files):
    for rel, text in files.items():
        p = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
    return root


def _fails_of(rep):
    return sorted((v["criterion"], v["severity"]) for v in rep["verdicts"]
                  if v["status"] == "fail")


FOOTER = ('<footer><a href="/privacidad">Privacidad</a> <a href="/terminos">Términos</a> '
          '<a href="/aviso-legal">Aviso legal</a> <a href="/politica-de-cookies">Cookies</a>'
          '</footer>')
FILLED = "<h1>{t}</h1><p>Mar Azul S.L., NIF B00000000, Calle Mayor 1, Valencia. Actualizado 2026-10-08.</p>"


def control_site(root):
    return _site(root, {
        "app/layout.tsx": ('<script src="https://www.googletagmanager.com/gtag/js"></script>'
                           "<CookieBanner />" + FOOTER),
        "app/privacidad/page.tsx": FILLED.format(t="Política de privacidad"),
        "app/terminos/page.tsx": FILLED.format(t="Términos de uso"),
        "app/aviso-legal/page.tsx": FILLED.format(t="Aviso legal"),
        "app/politica-de-cookies/page.tsx": FILLED.format(t="Política de cookies"),
    })


def v_vendored():
    tdir = os.path.join(VENDOR, "templates")
    present = sorted(d for d in os.listdir(tdir)) if os.path.isdir(tdir) else []
    drifted = [d for d, pin in TEMPLATE_PINS.items()
               if not os.path.isfile(os.path.join(tdir, d, "template.md"))
               or _norm_sha(os.path.join(tdir, d, "template.md")) != pin]
    notice = _read(os.path.join(VENDOR, "NOTICE.md")) if os.path.isfile(
        os.path.join(VENDOR, "NOTICE.md")) else ""
    lic = _read(os.path.join(VENDOR, "LICENSE")) if os.path.isfile(
        os.path.join(VENDOR, "LICENSE")) else ""
    meta_ok = ("6d6805425eabd41bed86fc1e2ec51612760f716c" in notice and "CC0" in notice
               and "CC0" in lic)
    if present != sorted(TEMPLATE_PINS) or drifted or not meta_ok:
        _fail("V-CDIO-LEGAL-VENDORED",
              f"present={len(present)} drifted={drifted} notice+license={meta_ok}")
    else:
        _ok("V-CDIO-LEGAL-VENDORED",
            f"{len(present)} templates match their pins; commit + CC0 recorded")


def v_dataset():
    fm = re.match(r"^---(.*?)---", _read(DATASET), flags=re.S)
    fm = fm.group(1) if fm else ""
    need = ("id: CDIO-10", "status: sealed", "governed_by: CDIO-00",
            "source: General-Legal", "evidence:")
    missing = [n for n in need if n not in fm]
    if missing:
        _fail("V-CDIO-LEGAL-DATASET", f"front matter lacks {missing}")
    else:
        _ok("V-CDIO-LEGAL-DATASET", "sealed, governed by CDIO-00, source + evidence recorded")


def v_criteria():
    found, malformed = parse_criteria(_section(_read(DATASET), 3))
    missing = sorted(EXPECTED_CRITERIA - set(found))
    _, drill_bad = parse_criteria("**`synthetic-no-dimension`** (severity major). text\n")
    if malformed or missing or drill_bad != ["synthetic-no-dimension"]:
        _fail("V-CDIO-LEGAL-CRITERIA",
              f"malformed={malformed} missing={missing} drill={drill_bad}")
    else:
        _ok("V-CDIO-LEGAL-CRITERIA",
            f"{len(found)} criteria well-formed; red drill caught the synthetic one")
    return found


def v_scorable(found):
    from modules.cdio.scorer import Verdict, score_review
    baseline = score_review([Verdict("value-3s", "trust", "pass", observed="ok")]).score
    bad = []
    for name, (dim, sev) in sorted(found.items()):
        r = score_review([Verdict(name, dim, "fail", sev, observed=f"synthetic {name}")])
        if r.dropped or r.score is None or r.score >= baseline:
            bad.append(name)
    if not found or bad:
        _fail("V-CDIO-LEGAL-SCORABLE", f"found={len(found)} bad={bad}")
    else:
        _ok("V-CDIO-LEGAL-SCORABLE", f"{len(found)} criteria accepted, each lowers the score")


def v_vocab():
    vocab = ls.field_vocabulary()
    uncaught = []
    for name in WEB_TEMPLATES:
        text = _read(os.path.join(VENDOR, "templates", name, "template.md"))
        if not ls.find_unfilled(text, vocab):
            uncaught.append(name)
        # the stripped-highlight form must still be caught
        if not ls.find_unfilled(re.sub(r"</?mark>", "", text), vocab):
            uncaught.append(name + " (marks stripped)")
    clean = ls.find_unfilled(FILLED.format(t="Aviso legal") + " see [our FAQ](/faq)", vocab)
    if (len(vocab) < VOCAB_FLOOR or "CompanyName" not in vocab or uncaught or clean):
        _fail("V-CDIO-LEGAL-VOCAB",
              f"vocab={len(vocab)} uncaught={uncaught} false_hits_on_filled={clean}")
    else:
        _ok("V-CDIO-LEGAL-VOCAB",
            f"{len(vocab)} fields read from templates; all {len(WEB_TEMPLATES)} web templates "
            f"caught raw and stripped; filled control clean")


def v_check():
    tmp = tempfile.mkdtemp(prefix="cdio_legal_")
    problems = []
    try:
        # 1. bad site: unfilled privacy, no terms, no aviso legal, tracker without consent
        bad = _site(os.path.join(tmp, "bad"), {
            "index.html": ('<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'
                           '<footer><a href="/privacidad">Privacidad</a></footer>'),
            "privacidad.html": "<p>[CompanyName] processes your data. Effective [DATE].</p>",
        })
        rep = ls.check(bad, "es")
        want = {("legal-page-present", "critical"), ("legal-fields-filled", "critical"),
                ("consent-before-tracking", "critical")}
        got = set(_fails_of(rep))
        n_missing = sum(1 for c, _ in _fails_of(rep) if c == "legal-page-present")
        if not want <= got or n_missing != 3 or rep["score"]["verdict"] != "BLOCK":
            problems.append(f"bad: {sorted(got)} missing_pages={n_missing} "
                            f"verdict={rep['score']['verdict']}")
        if ls.main(["check", bad, "--jurisdiction", "es"]) != 1:
            problems.append("bad: CLI exit != 1")

        # 2. control: every page present, filled, linked; consent mechanism present
        good = control_site(os.path.join(tmp, "good"))
        rep = ls.check(good, "es")
        if _fails_of(rep) or rep["score"]["verdict"] != "APPROVE" or not rep["unverified"]:
            problems.append(f"control: fails={_fails_of(rep)} verdict={rep['score']['verdict']} "
                            f"unverified={rep['unverified']}")
        if ls.main(["check", good, "--jurisdiction", "es"]) != 0:
            problems.append("control: CLI exit != 0")

        # 3. the same control with the terms link removed must BLOCK
        unlinked = control_site(os.path.join(tmp, "unlinked"))
        lay = os.path.join(unlinked, "app", "layout.tsx")
        _site(unlinked, {"app/layout.tsx": _read(lay).replace(
            '<a href="/terminos">Términos</a>', "")})
        rep = ls.check(unlinked, "es")
        if _fails_of(rep) != [("legal-page-linked", "critical")] \
                or rep["score"]["verdict"] != "BLOCK":
            problems.append(f"unlinked: {_fails_of(rep)} {rep['score']['verdict']}")

        # 4. checkout: consumer sale terms required, dropped with --b2b
        shop = control_site(os.path.join(tmp, "shop"))
        _site(shop, {"app/pay.tsx": '<script src="https://js.stripe.com/v3"></script>'})
        need = "sales_terms" in ls.check(shop, "es")["required"]
        b2b = "sales_terms" in ls.check(shop, "es", b2b=True)["required"]
        if not need or b2b:
            problems.append(f"commerce: required={need} with_b2b={b2b}")

        # 5. nothing to scan: no verdict, exit 2
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        if ls.main(["check", empty, "--jurisdiction", "us"]) != 2:
            problems.append("empty: exit != 2")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if problems:
        _fail("V-CDIO-LEGAL-CHECK", "; ".join(problems))
    else:
        _ok("V-CDIO-LEGAL-CHECK",
            "bad BLOCKs on 3 missing + unfilled + no consent; control APPROVEs with consent "
            "UNVERIFIED; unlinked BLOCKs; --b2b drops sale terms; empty exits 2")


def v_honest():
    text = _read(DATASET)
    not_universal = _section(text, 6).lower()
    markers = {
        "browser consent check PLANNED": "**PLANNED**" in _section(text, 8),
        "repeated success not reached": re.search(
            r"\|\s*repeated success\s*\|\s*not reached", _section(text, 8)) is not None,
        "not legal advice": "not legal advice" in text,
        "arbitration not universalised": "arbitration" in not_universal,
        "no CMP vendor mandated": "consent management platform" in not_universal,
    }
    absent = [k for k, ok in markers.items() if not ok]
    if absent:
        _fail("V-CDIO-LEGAL-HONEST", f"no longer recorded: {absent}")
    else:
        _ok("V-CDIO-LEGAL-HONEST", f"{len(markers)} scope limits recorded")


def wiring_gaps(texts):
    checks = {
        "kernel-governs": re.search(r"^governs:.*CDIO-10", texts["kernel"],
                                    flags=re.M) is not None,
        "lens4-pointer": "CDIO-10" in texts["lens4"] and "legal_surface" in texts["lens4"],
        "severity-rule": "CDIO-10" in texts["severity"],
        "agents": all("CDIO-10" in t for t in texts["agents"].values()),
        "reviewer-runs-check": "legal_surface check" in texts["agents"]["cdio-reviewer.md"],
    }
    return [c for c, ok in checks.items() if not ok]


def v_wired():
    c05 = _read(os.path.join(CDIO, "CDIO-05-design-review-pipeline.md"))
    texts = {
        "kernel": _read(os.path.join(CDIO, "CDIO-00-design-intelligence-kernel.md")),
        "lens4": _section(c05, 1),
        "severity": _section(c05, 3),
        "agents": {n: _read(os.path.join(ROOT, "vault", "agents", n)) for n in AGENTS},
    }
    gaps = wiring_gaps(texts)
    drilled = dict(texts, kernel=texts["kernel"].replace("CDIO-10", "CDIO-1X"))
    drill_ok = wiring_gaps(drilled) == ["kernel-governs"]
    if gaps or not drill_ok:
        _fail("V-CDIO-LEGAL-WIRED", f"not wired: {gaps} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-LEGAL-WIRED", "5 wiring points present; drill caught a removed pointer")


def v_mirrors():
    pairs = [(os.path.join(ROOT, "vault", "agents", n), os.path.join(HOME_CLAUDE, "agents", n))
             for n in AGENTS]
    drift = mirror_drift(pairs)
    drill = mirror_drift([(DATASET, pairs[0][0])]) == [os.path.basename(DATASET)]
    if drift or not drill:
        _fail("V-CDIO-LEGAL-MIRRORS", f"drift={drift} drill_ok={drill}")
    else:
        _ok("V-CDIO-LEGAL-MIRRORS", f"{len(pairs)} live copies identical; drill caught drift")


def main():
    if not os.path.isfile(DATASET):
        _fail("V-CDIO-LEGAL-DATASET", "CDIO-10 missing")
        print(f"CDIO_LEGAL_PASS={_passes}/{_passes + _fails}")
        return 1
    v_vendored()
    v_dataset()
    found = v_criteria()
    v_scorable(found)
    v_vocab()
    v_check()
    v_honest()
    v_wired()
    v_mirrors()
    total = _passes + _fails
    print(f"CDIO_LEGAL_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
