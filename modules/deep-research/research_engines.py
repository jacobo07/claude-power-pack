#!/usr/bin/env python3
"""research_engines.py — the four research engines for deep_research.

WHY THIS MODULE EXISTS
----------------------
deep_research v0.2.0 is a one-shot pipeline: ask N questions -> take the top 5
organic results of each -> extract prose -> synthesize. It has no opinion about
WHICH questions to ask, WHERE the evidence came from, HOW MUCH to trust a
learning, or WHAT to do when two sources disagree. The observed consequence
(2026-08-18): a learning about topic-cluster saturation was persisted from a
single vendor blog, carrying no marker that its evidence was thin. An operator
reading it cannot tell a measured number from a vendor's assertion, so they bet
the same amount on both.

The fix is not longer learnings. It is learnings that carry how much to bet on
them. Four engines, in pipeline order:

  E1 DECOMPOSITION  — before searching, split the question along five axes
                      (evidence / mechanism / boundary / counterexample /
                      transferability) so the search covers the problem instead
                      of one face of it.
  E2 LANDSCAPE      — classify every fetched source into a quality family
                      (A measured / B academic / C practitioner / D vendor) and
                      refuse to build a claim on family D alone.
  E3 REALITY        — every learning carries the CAPABILITY it confers plus an
                      epistemic level and a source-quality label, and the level
                      is CAPPED by deterministic evidence checks the extractor
                      cannot talk its way past.
  E4 CONTRADICTION  — when sources disagree, say so. Never silently pick one.

DESIGN CONTRACT (inherited from research_quality.py)
----------------------------------------------------
* Every function here is PURE: no network, no LLM, no disk. The whole layer is
  unit-testable offline — see test_research_engines.py.
* Every cap DEGRADES. An unreadable field, an unknown label, a malformed
  response can only ever lower a claim's level, never raise it. Same doctrine as
  modules/fable_distillation/epistemic_ladder.py, which derives an E0-E7 level
  for internally-deposited claims. That ladder measures a DIFFERENT axis (does
  an Owner-authored artifact cite this claim) on a different corpus, so the two
  are siblings, not duplicates. This one measures: what kind of evidence, from
  what kind of source, does an external document actually provide.
* The extractor never certifies its own claim. OBSERVED requires a measurable
  datum that a regex can find; VERIFIED requires corroboration a counter can
  count. A label the evidence does not support is demoted, not trusted.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

__version__ = "1.0.0"


# =========================================================================
# ENGINE 1 — PROBLEM DECOMPOSITION
# =========================================================================
#
# A high-level question searched directly retrieves the most popular framing of
# that question, which is usually the vendor framing. Decomposing first forces
# the search to hit faces of the problem that popularity does not surface: where
# the thing fails, what refutes it, whether it transfers.

AXIS_EVIDENCE = "EVIDENCE"
AXIS_MECHANISM = "MECHANISM"
AXIS_BOUNDARY = "BOUNDARY"
AXIS_COUNTEREXAMPLE = "COUNTEREXAMPLE"
AXIS_TRANSFERABILITY = "TRANSFERABILITY"

DECOMPOSITION_AXES = (
    AXIS_EVIDENCE,
    AXIS_MECHANISM,
    AXIS_BOUNDARY,
    AXIS_COUNTEREXAMPLE,
    AXIS_TRANSFERABILITY,
)

_AXIS_GLOSS = {
    AXIS_EVIDENCE: "what measured data exists, and who measured it",
    AXIS_MECHANISM: "why it works the way it does — the causal chain",
    AXIS_BOUNDARY: "where it stops working, and what the failure looks like",
    AXIS_COUNTEREXAMPLE: "what would refute the premise, and who reports it",
    AXIS_TRANSFERABILITY: "whether it holds in a different size, sector or era",
}

# A decomposition that touches fewer than this many axes has not decomposed —
# it has rephrased. Three is the floor because evidence+mechanism alone is the
# default shape of a naive search; the third axis is what makes it a sweep.
MIN_AXES_COVERED = 3

DECOMPOSITION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "axis": {"type": "string",
                             "enum": list(DECOMPOSITION_AXES)},
                    "researchGoal": {"type": "string"},
                },
                "required": ["query", "axis", "researchGoal"],
            },
        }
    },
    "required": ["questions"],
}


DECOMPOSITION_PROMPT = """\
Decompose the research topic below into specialised sub-questions BEFORE any \
searching happens. Searching the topic directly retrieves the most popular \
framing of it, which is usually whoever sells the solution. Decomposition is \
how we reach the faces of the problem that popularity does not surface.

Return at most {breadth} sub-questions, each tagged with the axis it attacks. \
Cover at least {min_axes} DIFFERENT axes. Never return two questions on the \
same axis unless every axis already has one.

THE FIVE AXES:
  EVIDENCE        — {gloss_evidence}
  MECHANISM       — {gloss_mechanism}
  BOUNDARY        — {gloss_boundary}
  COUNTEREXAMPLE  — {gloss_counterexample}
  TRANSFERABILITY — {gloss_transferability}

WORKED EXAMPLE. For the topic "how do content teams know when a topic cluster \
is saturated and adding more articles stops helping":
  EVIDENCE        -> "what metrics do publishers actually track to detect that \
new articles have stopped earning traffic"
  MECHANISM       -> "why does adding more pages on one subject eventually make \
a site rank worse instead of better"
  BOUNDARY        -> "at what point does content consolidation start losing \
traffic instead of recovering it"
  COUNTEREXAMPLE  -> "which sites kept publishing on the same subject and kept \
gaining traffic, and what was different about them"
  TRANSFERABILITY -> "does saturation behave the same way in AI-generated \
answers as it does in classic search results"

RULES FOR EVERY QUESTION:
  - A real, grammatical question in Spanish or English, with the function words \
present (how / why / what happens when / como / que / por que / cuando).
  - Aim at the PROBLEM and its consequences, never at the vocabulary of the \
solution — the vocabulary is what the research is supposed to discover.
  - No concatenated term piles, no tool names as the query, no code, no flags, \
no file extensions.
  - `researchGoal` states what you expect to learn and why it changes a \
decision someone running a business would make.

<topic>{prompt}</topic>

{learnings_block}"""


def build_decomposition_prompt(prompt: str, breadth: int,
                               learnings: list[str] | None = None) -> str:
    """Assemble the E1 decomposition user message."""
    learnings = learnings or []
    if learnings:
        block = (
            "These are the learnings already collected. Attack the axes they "
            "have NOT answered — do not re-ask what is already known:\n"
            + "\n".join(f"- {ln}" for ln in learnings)
        )
    else:
        block = ""
    return DECOMPOSITION_PROMPT.format(
        prompt=prompt,
        breadth=max(breadth, MIN_AXES_COVERED),
        min_axes=MIN_AXES_COVERED,
        gloss_evidence=_AXIS_GLOSS[AXIS_EVIDENCE],
        gloss_mechanism=_AXIS_GLOSS[AXIS_MECHANISM],
        gloss_boundary=_AXIS_GLOSS[AXIS_BOUNDARY],
        gloss_counterexample=_AXIS_GLOSS[AXIS_COUNTEREXAMPLE],
        gloss_transferability=_AXIS_GLOSS[AXIS_TRANSFERABILITY],
        learnings_block=block,
    )


def normalize_axis(raw: Any) -> str | None:
    """Map an LLM-supplied axis label onto the canonical set, else None.

    Unknown labels return None rather than a default axis: silently bucketing an
    unrecognised label into EVIDENCE would inflate the measured coverage with a
    question nobody classified.
    """
    token = str(raw or "").strip().upper().replace("-", "_").replace(" ", "_")
    return token if token in DECOMPOSITION_AXES else None


def axes_covered(questions: list[dict[str, Any]]) -> set[str]:
    """The distinct canonical axes present in `questions`."""
    out: set[str] = set()
    for q in questions or []:
        if not isinstance(q, dict):
            continue
        axis = normalize_axis(q.get("axis"))
        if axis:
            out.add(axis)
    return out


def missing_axes(questions: list[dict[str, Any]]) -> list[str]:
    """Canonical axes with no question, in declaration order."""
    covered = axes_covered(questions)
    return [a for a in DECOMPOSITION_AXES if a not in covered]


def decomposition_is_sufficient(questions: list[dict[str, Any]]
                                ) -> tuple[bool, str]:
    """True iff the decomposition touches >= MIN_AXES_COVERED distinct axes.

    Returns (ok, reason); `reason` names the shortfall so the caller can put it
    in a single corrective re-ask (Anti-Antipattern Regla 12 bounds it to one).
    """
    covered = axes_covered(questions)
    if len(covered) >= MIN_AXES_COVERED:
        return True, ""
    return False, (
        f"only {len(covered)} axis/axes covered "
        f"({', '.join(sorted(covered)) or 'none'}) — minimum "
        f"{MIN_AXES_COVERED}; missing: {', '.join(missing_axes(questions))}"
    )


def build_decomposition_correction_prompt(questions: list[dict[str, Any]],
                                          breadth: int) -> str:
    """The single corrective re-ask when the decomposition is too narrow."""
    gaps = missing_axes(questions)
    listing = "\n".join(f"  - {a}: {_AXIS_GLOSS[a]}" for a in gaps)
    return (
        "Your decomposition was rejected: it attacks too few axes, so the "
        "search would cover one face of the problem instead of the problem.\n\n"
        f"Axes with NO question yet:\n{listing}\n\n"
        f"Return at most {breadth} questions covering at least "
        f"{MIN_AXES_COVERED} different axes, weighted toward the axes listed "
        "above. Same rules: grammatical questions, aimed at the problem and its "
        "consequences, no term piles, no tool names, no code."
    )


# =========================================================================
# ENGINE 2 — LANDSCAPE COVERAGE GATE
# =========================================================================
#
# A claim is only as good as the kind of document it came from. This engine is
# deterministic on purpose: source provenance is a fact about a URL and a body
# of text, not a judgement call, and a judgement call would need an LLM that
# could be unavailable exactly when the landscape is worst.

FAMILY_MEASURED = "A_MEASURED"        # case studies, post-mortems, A/B results
FAMILY_ACADEMIC = "B_ACADEMIC"        # papers, theses, preprints
FAMILY_PRACTITIONER = "C_PRACTITIONER"  # engineer blogs, talks, RFCs, standards
FAMILY_VENDOR = "D_VENDOR"            # vendor / agency / thought-leader content
FAMILY_UNKNOWN = "UNKNOWN"

SOURCE_FAMILIES = (
    FAMILY_MEASURED, FAMILY_ACADEMIC, FAMILY_PRACTITIONER,
    FAMILY_VENDOR, FAMILY_UNKNOWN,
)

QUALITY_HIGH = "HIGH"
QUALITY_MEDIUM = "MEDIUM"
QUALITY_LOW = "LOW"

# The families that can carry a claim on their own. D corroborates; it never
# founds. UNKNOWN is treated as D — an unclassifiable page has not earned trust.
LOAD_BEARING_FAMILIES = frozenset(
    {FAMILY_MEASURED, FAMILY_ACADEMIC, FAMILY_PRACTITIONER}
)

COVERAGE_COVERED = "COVERED"        # >= 2 load-bearing families
COVERAGE_THIN = "THIN"              # exactly 1 load-bearing family
COVERAGE_UNCLASSIFIED = "UNCLASSIFIED"  # 0 load-bearing, but not marketing
COVERAGE_VENDOR_ONLY = "VENDOR_ONLY"    # 0 load-bearing, all conversion surface

# UNCLASSIFIED exists because the first version of this gate did not have it,
# and the 2026-08-18 live run showed exactly what that costs: 12 of 13 real
# pages scored UNKNOWN, the gate read UNKNOWN as vendor, and all three research
# questions were refused. The classifier's vocabulary was built from software
# engineering, so a content-strategy domain matched nothing and the gate became
# a silent kill switch for every field it had not been taught.
#
# The Owner's rule is that a claim may not stand on FAMILY D alone. A page we
# could not identify is not family D — it is unidentified. Refusal stays
# reserved for pages positively recognised as marketing; an unidentified
# landscape costs the claim confidence (capped at DERIVED) instead of erasing
# the work. A gate that cannot tell "this is marketing" from "I have no rule for
# this" always fails toward silence, and silence looks like health.

_ACADEMIC_HOSTS = (
    "arxiv.org", "doi.org", "springer.com", "link.springer.com",
    "sciencedirect.com", "nature.com", "acm.org", "ieee.org",
    "ieeexplore.ieee.org", "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
    "ssrn.com", "jstor.org", "psycnet.apa.org", "tandfonline.com",
    "onlinelibrary.wiley.com", "journals.plos.org", "plos.org",
    "biorxiv.org", "semanticscholar.org", "researchgate.net",
    "scholar.google.com", "dl.acm.org", "mdpi.com", "frontiersin.org",
    "cambridge.org", "oup.com", "academic.oup.com", "sagepub.com",
    "nber.org", "osf.io", "dialnet.unirioja.es", "scielo.org",
)

_PRACTITIONER_HOSTS = (
    "rfc-editor.org", "ietf.org", "datatracker.ietf.org", "w3.org",
    "whatwg.org", "github.com", "gist.github.com", "stackoverflow.com",
    "news.ycombinator.com", "usenix.org", "infoq.com", "martinfowler.com",
    "developer.mozilla.org", "web.dev", "developers.google.com",
    "developer.chrome.com", "engineering.fb.com", "netflixtechblog.com",
    "aws.amazon.com/blogs/architecture", "blog.cloudflare.com",
    "danluu.com", "brendangregg.com", "jvns.ca", "lwn.net",
)

# Substrings that mark a page as vendor/agency/thought-leader output. These are
# conversion surfaces: the page exists to sell, so its claims are advocacy until
# corroborated. Deliberately about SHAPE, not about naming specific companies.
_VENDOR_TEXT_SIGNALS = (
    "book a demo", "request a demo", "schedule a demo", "free trial",
    "start your free", "get started free", "our platform", "our software",
    "our agency", "our clients", "pricing plans", "talk to sales",
    "contact sales", "sign up free", "solicita una demo", "prueba gratis",
    "nuestra agencia", "nuestros clientes", "nuestra plataforma",
)

_VENDOR_PATH_SIGNALS = (
    "/pricing", "/precios", "/demo", "/free-trial", "/signup", "/sign-up",
    "/solutions", "/soluciones", "/services", "/servicios", "/product/",
    "/platform", "/case-studies/",
)

# Measurement verbs: the page claims to have MEASURED something, not to have
# read about it. Required (with numeric density) for family A.
_MEASUREMENT_SIGNALS = (
    "we measured", "we ran", "we tested", "we tracked", "we analyzed",
    "we analysed", "our data", "our experiment", "our test", "our study",
    "a/b test", "ab test", "split test", "control group", "sample size",
    "post-mortem", "postmortem", "post mortem", "incident report",
    "root cause", "we surveyed", "dataset of", "we compared",
    "medimos", "analizamos", "nuestro experimento", "nuestros datos",
    "grupo de control", "tamaño de muestra", "encuestamos",
)

_ACADEMIC_TEXT_SIGNALS = (
    "abstract", "methodology", "we hypothesize", "we hypothesise",
    "statistically significant", "p < 0", "p<0", "confidence interval",
    "peer-reviewed", "peer reviewed", "et al.", "literature review",
    "doi:", "resumen", "metodología", "revisión de la literatura",
)

# First-hand practice, stated in the page's own voice. Half of these are
# software-flavoured because that is where the list started; the other half are
# DOMAIN-AGNOSTIC on purpose. The 2026-08-18 run proved why: a list made only of
# engineering vocabulary scores every non-engineering page at zero, and a zero
# is indistinguishable from a bad page. A gate is bounded by its vocabulary, so
# the vocabulary has to be about the SHAPE of first-hand reporting, not about
# one industry's nouns.
_PRACTITIONER_TEXT_SIGNALS = (
    "in production", "at scale", "our architecture", "we deployed",
    "trade-off", "tradeoff", "benchmark", "latency", "throughput",
    "rfc ", "specification", "reference implementation",
    "in our experience", "we found that", "we learned", "lessons learned",
    "what worked", "what didn't work", "what did not work", "we've seen",
    "we have seen", "here's what happened", "in practice", "over the years",
    "we recommend based on", "when we tried",
    "en producción", "arquitectura", "implementación de referencia",
    "en nuestra experiencia", "lo que aprendimos", "lecciones aprendidas",
    "en la práctica", "cuando lo probamos",
)

# A measurable datum. Presence is the deterministic proof an OBSERVED label is
# entitled to exist. Kept narrow: a bare integer is not a measurement, a
# percentage / multiple / currency / sample size / durational count is.
_MEASURE_RE = re.compile(
    r"(?:\b\d[\d.,]*\s*(?:%|percent|per\s?cent|por\s?ciento|pp|bps|x\b|×))"
    r"|(?:[$€£]\s?\d[\d.,]*)"
    r"|(?:\b\d[\d.,]*\s?(?:k|m|bn|mm)\b)"
    r"|(?:\bn\s*=\s*\d+)"
    r"|(?:\b\d[\d.,]*\s+(?:days?|weeks?|months?|years?|hours?|minutes?"
    r"|seconds?|users?|customers?|visitors?|sessions?|articles?|pages?"
    r"|posts?|keywords?|sites?|companies?|teams?|respondents?|participants?"
    r"|d[ií]as?|semanas?|meses?|a[nñ]os?|horas?|minutos?|usuarios?"
    r"|clientes?|art[ií]culos?|p[aá]ginas?|empresas?|equipos?)\b)",
    re.IGNORECASE,
)


def has_measurable_datum(text: str) -> bool:
    """True iff `text` carries at least one quantity a reader could verify."""
    return bool(_MEASURE_RE.search(text or ""))


def _count_measurables(text: str, limit: int = 8) -> int:
    n = 0
    for _ in _MEASURE_RE.finditer(text or ""):
        n += 1
        if n >= limit:
            break
    return n


def _host_of(url: str) -> str:
    try:
        return (urlparse(url or "").netloc or "").lower().lstrip("www.")
    except ValueError:
        return ""


def _hits(text: str, needles: tuple[str, ...]) -> int:
    low = (text or "").lower()
    return sum(1 for n in needles if n in low)


def classify_source(url: str, title: str = "", snippet: str = "",
                    body: str = "") -> dict[str, Any]:
    """Classify one fetched source into a quality family. Deterministic.

    Returns {url, host, family, quality, vendor_host, signals}. `signals` is the
    human-readable evidence for the verdict — a classifier whose reasoning is
    invisible cannot be tuned, only guessed at.

    Resolution order is by strength of proof, not by convenience:
      1. an academic host, or academic prose markers          -> B
      2. explicit measurement language + numeric density      -> A
      3. a practitioner host, or practitioner prose markers   -> C
      4. conversion-surface markers                           -> D
      5. nothing identifiable                                 -> UNKNOWN

    A vendor-hosted page that genuinely reports its own measurements resolves to
    family A but is capped at MEDIUM quality: self-reported vendor data is
    evidence, but it is not independent evidence, and pretending otherwise is
    exactly the failure this engine exists to stop.
    """
    host = _host_of(url)
    # Title and snippet are dense signal; the body is long and dilute, so it is
    # sampled rather than scanned whole (a 25 KB page would otherwise let one
    # stray "free trial" in a footer outvote the article).
    head = f"{title}\n{snippet}"
    sample = (body or "")[:6000]
    text = f"{head}\n{sample}"
    path = (url or "").lower()

    signals: list[str] = []

    academic_host = (any(h in host for h in _ACADEMIC_HOSTS)
                     or host.endswith((".edu", ".ac.uk")))
    academic_text = _hits(text, _ACADEMIC_TEXT_SIGNALS)
    practitioner_host = any(h in (host + path) for h in _PRACTITIONER_HOSTS)
    practitioner_text = _hits(text, _PRACTITIONER_TEXT_SIGNALS)
    measurement_text = _hits(text, _MEASUREMENT_SIGNALS)
    measurables = _count_measurables(text)
    vendor_text = _hits(text, _VENDOR_TEXT_SIGNALS)
    vendor_path = any(p in path for p in _VENDOR_PATH_SIGNALS)
    vendor_host = bool(vendor_text or vendor_path)

    if academic_host:
        signals.append(f"academic host ({host})")
    if academic_text:
        signals.append(f"{academic_text} academic prose marker(s)")
    if measurement_text:
        signals.append(f"{measurement_text} measurement marker(s)")
    if measurables:
        signals.append(f"{measurables} measurable datum/data")
    if practitioner_host:
        signals.append(f"practitioner host ({host})")
    if practitioner_text:
        signals.append(f"{practitioner_text} practitioner prose marker(s)")
    if vendor_text:
        signals.append(f"{vendor_text} conversion-surface phrase(s)")
    if vendor_path:
        signals.append("conversion-surface URL path")

    if academic_host or academic_text >= 2:
        family, quality = FAMILY_ACADEMIC, QUALITY_HIGH
    elif measurement_text >= 1 and measurables >= 3:
        family = FAMILY_MEASURED
        quality = QUALITY_MEDIUM if vendor_host else QUALITY_HIGH
        if vendor_host:
            signals.append("vendor-hosted self-report — capped to MEDIUM")
    elif practitioner_host or (practitioner_text >= 2 and not vendor_host):
        # A conversion surface cannot buy family C with first-hand phrasing.
        # Marketing pages say "in our experience" constantly; a recognised
        # practitioner HOST still qualifies, prose alone on a selling page does
        # not. Without this, broadening the vocabulary would have laundered
        # every vendor blog into a load-bearing source — the opposite of the
        # bug being fixed.
        family, quality = FAMILY_PRACTITIONER, QUALITY_MEDIUM
    elif vendor_host:
        family, quality = FAMILY_VENDOR, QUALITY_LOW
    else:
        family, quality = FAMILY_UNKNOWN, QUALITY_LOW
        signals.append("no family marker found")

    return {
        "url": url,
        "host": host,
        "family": family,
        "quality": quality,
        "vendor_host": vendor_host,
        "signals": signals,
    }


def landscape_verdict(classes: list[dict[str, Any]]) -> dict[str, Any]:
    """Judge the source landscape behind ONE query's extraction.

    Returns {verdict, families, load_bearing, quality, source_count, detail}.

    VENDOR_ONLY is a refusal, not a warning. A claim whose entire evidence base
    is somebody's marketing page is not a weak claim, it is an unsourced one —
    and the whole reason this engine exists is that the previous pipeline
    persisted exactly that shape without saying so.

    UNCLASSIFIED is NOT a refusal. It means the classifier had no rule that fit
    these pages, which is a statement about the classifier, not about the pages.
    It costs the claim confidence; it does not delete the run. Collapsing the
    two verdicts is what made the 2026-08-18 run return zero learnings from
    thirteen real sources.
    """
    classes = [c for c in (classes or []) if isinstance(c, dict)]
    families = sorted({str(c.get("family") or FAMILY_UNKNOWN) for c in classes})
    load_bearing = sorted(set(families) & LOAD_BEARING_FAMILIES)

    if load_bearing:
        verdict = (COVERAGE_COVERED if len(load_bearing) >= 2
                   else COVERAGE_THIN)
    elif FAMILY_UNKNOWN in families:
        verdict = COVERAGE_UNCLASSIFIED
    else:
        # Every source was positively recognised as a conversion surface, or
        # nothing was fetched at all. Both are refusals: one has no independent
        # evidence, the other has no evidence.
        verdict = COVERAGE_VENDOR_ONLY

    if FAMILY_MEASURED in load_bearing or FAMILY_ACADEMIC in load_bearing:
        quality = QUALITY_HIGH
    elif FAMILY_PRACTITIONER in load_bearing:
        quality = QUALITY_MEDIUM
    else:
        quality = QUALITY_LOW

    # A HIGH landscape built purely on vendor-hosted self-reports is not HIGH.
    if quality == QUALITY_HIGH:
        supporting = [c for c in classes
                      if c.get("family") in (FAMILY_MEASURED, FAMILY_ACADEMIC)]
        if supporting and all(c.get("vendor_host") for c in supporting):
            quality = QUALITY_MEDIUM

    return {
        "verdict": verdict,
        "families": families,
        "load_bearing": load_bearing,
        "quality": quality,
        "source_count": len(classes),
        "detail": [
            {"url": c.get("url"), "family": c.get("family"),
             "quality": c.get("quality"), "signals": c.get("signals", [])}
            for c in classes
        ],
    }


def rank_sources_for_extraction(classes: list[dict[str, Any]]
                                ) -> list[dict[str, Any]]:
    """Order sources so the load-bearing families are read first.

    Extraction budgets are finite (each markdown is truncated). Feeding the
    vendor page first and the paper last means the truncation eats the paper.
    """
    order = {FAMILY_MEASURED: 0, FAMILY_ACADEMIC: 1, FAMILY_PRACTITIONER: 2,
             FAMILY_VENDOR: 3, FAMILY_UNKNOWN: 4}
    return sorted(classes or [],
                  key=lambda c: order.get(str(c.get("family")), 4))


# =========================================================================
# ENGINE 3 — CAPABILITY + REALITY EXTRACTION
# =========================================================================
#
# The old prompt asked for "what a founder should LEARN" and returned prose with
# no provenance. Two things are added and both are enforced, not requested: the
# CAPABILITY (which decision this changes, not which fact it states) and the
# EPISTEMIC LEVEL, capped by checks the extractor cannot argue with.

EPI_OBSERVED = "OBSERVED"      # a datum measured in the source
EPI_VERIFIED = "VERIFIED"      # corroborated across independent sources
EPI_DERIVED = "DERIVED"        # a logical inference from what the source says
EPI_HYPOTHESIS = "HYPOTHESIS"  # a plausible reading, unconfirmed
EPI_REJECTED = "REJECTED"      # refuted by the evidence gathered

EPISTEMIC_LEVELS = (
    EPI_OBSERVED, EPI_VERIFIED, EPI_DERIVED, EPI_HYPOTHESIS, EPI_REJECTED,
)

# Strength order, per the Owner's ladder: Observed > Verified > Derived >
# Hypothesis > Rejected. Used only for reporting and sorting; the caps below are
# targeted rules, not a min() over this scale, because OBSERVED and VERIFIED
# fail for different reasons and demote to different places.
EPISTEMIC_RANK = {
    EPI_OBSERVED: 4, EPI_VERIFIED: 3, EPI_DERIVED: 2,
    EPI_HYPOTHESIS: 1, EPI_REJECTED: 0,
}

# An unlabelled or unrecognised claim is a HYPOTHESIS. Never OBSERVED, never a
# silent pass: an error in the labelling layer must cost the claim confidence,
# not buy it some.
EPISTEMIC_DEFAULT = EPI_HYPOTHESIS

# VERIFIED means corroborated. Corroboration by one document is not
# corroboration, whatever the extractor calls it.
MIN_SOURCES_FOR_VERIFIED = 2

LEARNING_RECORD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "learnings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "learning": {"type": "string"},
                    "epistemic": {"type": "string",
                                  "enum": list(EPISTEMIC_LEVELS)},
                    "evidence": {"type": "string"},
                    "supporting_sources": {"type": "integer"},
                },
                "required": ["capability", "learning", "epistemic", "evidence"],
            },
        },
        "followUpQuestions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["learnings", "followUpQuestions"],
}


CAPABILITY_LEARNINGS_PROMPT = """\
Given the following contents from a search for <query>{query}</query>, extract \
the CAPABILITIES they confer on an operator — not the facts they state.

A fact is "topic clusters can saturate". A capability is "you can now detect \
saturation before rankings fall, by watching impressions on new pages instead \
of waiting for traffic loss". The second one changes what somebody does on \
Monday. The first one does not.

Return a maximum of 3 learnings. Return fewer if the contents are thin. A thin \
honest answer beats a padded one — every learning is read back as context on \
every future run, so a weak one is paid for forever.

THE READER: someone who runs a business. They decide where money, people and \
attention go. They are intelligent but they will NOT run a command, edit a \
config file, or read a schema.

EVERY LEARNING IS AN OBJECT WITH FOUR FIELDS:

  capability — one sentence naming the DECISION this changes, phrased as what \
the operator can now do or stop doing. Not the fact. Not the topic.

  learning — the insight itself, plain prose, 1 to 3 sentences, self-contained. \
Carry the concrete numbers, dates, and named entities the contents provide; \
those are what make it worth more than an opinion. State the CONSEQUENCE, not \
just the fact.

  epistemic — how much the reader should bet on it. Choose HONESTLY; an \
automated gate re-checks every label and DEMOTES anything the evidence does not \
support, so an inflated label buys nothing and loses credibility:
    OBSERVED   — a specific figure, date or measured result stated in the \
contents. Requires an actual quantity. If you cannot point at a number, this is \
not OBSERVED.
    VERIFIED   — the same claim appears in two or more of the contents \
independently.
    DERIVED    — your logical inference from what the contents say. The \
contents support it; they do not state it.
    HYPOTHESIS — a plausible reading with no confirmation in the contents.
    REJECTED   — the contents actively refute this. Return it anyway when it \
corrects a common belief; a refuted assumption is one of the most valuable \
things research produces.

  evidence — the specific thing in the contents that justifies the epistemic \
label: the figure, the study, the named company, the count of sources agreeing. \
One sentence. If you cannot write this sentence, lower the epistemic label.

  supporting_sources — an integer: how many of the supplied contents \
independently support this learning.

FORBIDDEN IN THE `learning` AND `capability` FIELDS (an automated gate discards \
these, so writing one wastes the slot):
  - Code in any language. No YAML, no JSON, no SQL, no shell, no Python.
  - Command-line invocations, flags, or CLI tool syntax.
  - Configuration fragments, schema definitions, or bare field names.
  - A tool name presented AS the insight. Naming a tool as evidence of who does \
what is fine; naming it as the takeaway is not.
  - Implementation steps. WHAT changes and WHY it matters, never HOW to type it.

GOOD:
  capability: "You can stop treating a traffic plateau as a content-volume \
problem and start reading it as a signal to consolidate."
  learning: "Publishers tracking cluster performance report that impressions on \
newly published pages flatten weeks before sessions drop, so the plateau is \
visible in search-console data while revenue still looks healthy."
  epistemic: "OBSERVED"
  evidence: "Two of the contents give a specific lag between impression \
flattening and traffic decline, measured in weeks."

BAD:
  capability: "Use a content audit tool."
  learning: "Topic clusters are an important part of modern SEO strategy."
  epistemic: "OBSERVED"
  evidence: "The article says clusters matter."

<contents>
{contents_block}
</contents>"""


def build_capability_learnings_prompt(query: str, contents_block: str) -> str:
    """Assemble the E3 extraction user message."""
    return CAPABILITY_LEARNINGS_PROMPT.format(
        query=query, contents_block=contents_block
    )


def normalize_epistemic(raw: Any) -> str:
    """Map an LLM-supplied epistemic label onto the canonical scale.

    Anything unrecognised becomes HYPOTHESIS. Degrade-only by construction: a
    malformed label can never buy confidence it did not earn.
    """
    token = str(raw or "").strip().upper()
    return token if token in EPISTEMIC_LEVELS else EPISTEMIC_DEFAULT


def cap_epistemic(level: str, learning: str, evidence: str,
                  supporting_sources: int,
                  coverage: str = COVERAGE_COVERED) -> tuple[str, str]:
    """Apply the deterministic caps. Returns (final_level, reason).

    `reason` is empty when nothing was capped; otherwise it states exactly which
    check failed, so the demotion is auditable rather than mysterious.

    The four caps, in the order they can fire:
      1. VENDOR_ONLY landscape        -> REJECTED. Every source was positively
                                          recognised as a conversion surface.
      2. UNCLASSIFIED landscape       -> at most DERIVED. Provenance could not
                                          be established, so nothing above an
                                          inference has been earned — but the
                                          work is kept, because failing to
                                          classify a page is the classifier's
                                          shortcoming, not the page's.
      3. VERIFIED without >= 2 sources -> demote (a lone source is not
                                          corroboration, whatever it is called).
      4. OBSERVED without a measurable -> DERIVED (an observation with no
                                          quantity is an impression).
    """
    level = normalize_epistemic(level)

    if coverage == COVERAGE_VENDOR_ONLY:
        return EPI_REJECTED, (
            "landscape VENDOR_ONLY — every supporting source is a conversion "
            "surface; no load-bearing family (measured / academic / "
            "practitioner) backs this claim"
        )

    if coverage == COVERAGE_UNCLASSIFIED and level in (EPI_OBSERVED,
                                                       EPI_VERIFIED):
        return EPI_DERIVED, (
            f"{level} claims provenance the landscape cannot establish — no "
            "source behind it resolved to a known family; capped at DERIVED"
        )

    text = f"{learning}\n{evidence}"

    if level == EPI_VERIFIED and supporting_sources < MIN_SOURCES_FOR_VERIFIED:
        demoted = EPI_OBSERVED if has_measurable_datum(text) else EPI_DERIVED
        return demoted, (
            f"VERIFIED claims corroboration but only {supporting_sources} "
            f"source(s) support it (minimum {MIN_SOURCES_FOR_VERIFIED}) — "
            f"demoted to {demoted}"
        )

    if level == EPI_OBSERVED and not has_measurable_datum(text):
        return EPI_DERIVED, (
            "OBSERVED claims a measured datum but neither the learning nor its "
            "evidence carries a quantity — demoted to DERIVED"
        )

    return level, ""


def source_quality_label(coverage_quality: str) -> str:
    """The HIGH/MEDIUM/LOW label a learning inherits from its landscape."""
    return (coverage_quality
            if coverage_quality in (QUALITY_HIGH, QUALITY_MEDIUM, QUALITY_LOW)
            else QUALITY_LOW)


def format_labeled_learning(record: dict[str, Any]) -> str:
    """Render one learning record as the single labelled string that is stored.

    The labels lead. An operator scanning the corpus must see how much to bet
    BEFORE they read the claim — a label at the end is a label that arrives
    after the decision has already been formed.
    """
    epi = normalize_epistemic(record.get("epistemic"))
    quality = source_quality_label(str(record.get("source_quality") or ""))
    learning = str(record.get("learning") or "").strip()
    capability = str(record.get("capability") or "").strip()
    evidence = str(record.get("evidence") or "").strip()

    parts = [f"[{epi}][{quality}] {learning}"]
    if capability:
        parts.append(f"Capacidad: {capability}")
    if evidence:
        parts.append(f"Evidencia: {evidence}")
    return " — ".join(parts)


def parse_learning_records(response: dict[str, Any],
                           coverage: dict[str, Any] | None = None,
                           ) -> list[dict[str, Any]]:
    """Normalise the E3 payload into capped, labelled learning records.

    A malformed entry is DROPPED, never patched into existence: inventing a
    capability or an evidence sentence on the model's behalf would fabricate the
    very provenance this engine exists to guarantee.
    """
    coverage = coverage or {}
    cov_verdict = str(coverage.get("verdict") or COVERAGE_COVERED)
    cov_quality = source_quality_label(str(coverage.get("quality") or ""))
    max_sources = int(coverage.get("source_count") or 0)

    out: list[dict[str, Any]] = []
    for raw in (response.get("learnings") or []):
        if not isinstance(raw, dict):
            continue
        learning = str(raw.get("learning") or "").strip()
        capability = str(raw.get("capability") or "").strip()
        evidence = str(raw.get("evidence") or "").strip()
        if not learning or not capability:
            continue

        try:
            supporting = int(raw.get("supporting_sources") or 0)
        except (TypeError, ValueError):
            supporting = 0
        # The extractor cannot claim more corroboration than there were
        # documents. Self-certification is capped by arithmetic.
        if max_sources:
            supporting = min(supporting, max_sources)

        claimed = normalize_epistemic(raw.get("epistemic"))
        final, cap_reason = cap_epistemic(
            claimed, learning, evidence, supporting, cov_verdict
        )
        out.append({
            "capability": capability,
            "learning": learning,
            "evidence": evidence,
            "epistemic_claimed": claimed,
            "epistemic": final,
            "capped": bool(cap_reason),
            "cap_reason": cap_reason,
            "supporting_sources": supporting,
            "source_quality": cov_quality,
            "coverage": cov_verdict,
        })
    return out


def epistemic_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count records by final epistemic level — the run's confidence profile."""
    counts = {lvl: 0 for lvl in EPISTEMIC_LEVELS}
    for r in records or []:
        counts[normalize_epistemic(r.get("epistemic"))] += 1
    return counts


# =========================================================================
# ENGINE 4 — CONTRADICTION DETECTION
# =========================================================================
#
# The previous pipeline resolved conflicts by whichever source was extracted
# last. That is not synthesis, it is coin-flipping with extra steps. Two sources
# that disagree are a finding; the operator needs to know the field is contested
# so they can decide which context they are in.

CONTRADICTION_AXES = (
    "CONTEXT", "TIMEFRAME", "METHODOLOGY", "SCOPE", "UNKNOWN",
)

_AXIS_EXPLANATION = {
    "CONTEXT": "distinto contexto",
    "TIMEFRAME": "distinto año o periodo",
    "METHODOLOGY": "distinta metodología de medición",
    "SCOPE": "distinto alcance o tamaño",
    "UNKNOWN": "causa no identificada",
}

CONTRADICTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index_a": {"type": "integer"},
                    "index_b": {"type": "integer"},
                    "claim_a": {"type": "string"},
                    "claim_b": {"type": "string"},
                    "axis": {"type": "string",
                             "enum": list(CONTRADICTION_AXES)},
                    "guidance": {"type": "string"},
                },
                "required": ["index_a", "index_b", "claim_a", "claim_b",
                             "axis", "guidance"],
            },
        }
    },
    "required": ["contradictions"],
}


CONTRADICTION_PROMPT = """\
Below are the learnings collected across every source in this research run. \
Find the places where they CONTRADICT each other.

A contradiction is two learnings that cannot both be true as stated for the same \
reader in the same situation: different numbers for the same quantity, opposite \
causal claims, incompatible recommendations, or one asserting what another \
denies.

Your job is to SURFACE the conflict, not to settle it. Do not pick a winner. Do \
not average them. Do not quietly drop the weaker one. An unresolved \
contradiction reported honestly is more useful than a confident synthesis that \
buried it, because the operator can see that the field is contested and work out \
which situation they are in.

For each contradiction return:
  index_a, index_b — the bracketed indices of the two conflicting learnings
  claim_a, claim_b — what each one actually asserts, in your own words, one \
sentence each
  axis — the most likely reason they differ:
      CONTEXT      — they describe different situations
      TIMEFRAME    — they describe different years or periods
      METHODOLOGY  — they measured different things, or measured differently
      SCOPE        — they describe different sizes, sectors or scales
      UNKNOWN      — you cannot tell from what is here. Use this honestly; a \
fabricated explanation is worse than an admitted gap.
  guidance — one sentence telling the operator which claim applies in which \
situation, or stating plainly that the conflict cannot be resolved from these \
sources.

Return an EMPTY list if the learnings genuinely do not conflict. Manufacturing \
a contradiction to look thorough is a defect. Tension is not contradiction: two \
learnings emphasising different things are compatible.

<learnings>
{listing}
</learnings>"""


def build_contradiction_prompt(learnings: list[str]) -> str:
    """Assemble the E4 detection user message over the run's full corpus."""
    listing = "\n".join(f"[{i}] {ln}" for i, ln in enumerate(learnings))
    return CONTRADICTION_PROMPT.format(listing=listing)


def normalize_contradiction_axis(raw: Any) -> str:
    token = str(raw or "").strip().upper()
    return token if token in CONTRADICTION_AXES else "UNKNOWN"


def parse_contradictions(response: dict[str, Any], learning_count: int
                         ) -> list[dict[str, Any]]:
    """Validate the E4 payload against the actual corpus.

    Every row must point at two DISTINCT learnings that exist. A row citing an
    index out of range is discarded — a contradiction between a real learning
    and an imagined one is a hallucination, and reporting it would poison the
    one section of the report whose entire value is that it is honest.
    """
    out: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for row in (response.get("contradictions") or []):
        if not isinstance(row, dict):
            continue
        try:
            a = int(row.get("index_a"))
            b = int(row.get("index_b"))
        except (TypeError, ValueError):
            continue
        if a == b:
            continue
        if not (0 <= a < learning_count and 0 <= b < learning_count):
            continue
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        claim_a = str(row.get("claim_a") or "").strip()
        claim_b = str(row.get("claim_b") or "").strip()
        guidance = str(row.get("guidance") or "").strip()
        if not (claim_a and claim_b and guidance):
            continue
        seen.add(key)
        out.append({
            "index_a": a,
            "index_b": b,
            "claim_a": claim_a,
            "claim_b": claim_b,
            "axis": normalize_contradiction_axis(row.get("axis")),
            "guidance": guidance,
        })
    return out


def format_contradiction(row: dict[str, Any]) -> str:
    """Render one contradiction in the Owner-specified report format."""
    axis = normalize_contradiction_axis(row.get("axis"))
    return (
        f"**CONTRADICCIÓN** — Fuente [{row['index_a']}] afirma: "
        f"{row['claim_a']} · Fuente [{row['index_b']}] afirma: "
        f"{row['claim_b']}\n"
        f"El conflicto NO está resuelto. Explicación probable: "
        f"{_AXIS_EXPLANATION[axis]} ({axis}).\n"
        f"Para el operador: {row['guidance']}"
    )


def format_contradiction_section(rows: list[dict[str, Any]]) -> str:
    """The `## Contradicciones detectadas` block appended to every report.

    The section is written even when the list is empty. A silent absence is
    ambiguous — it reads identically whether the engine found nothing or never
    ran — and this whole engine exists to remove that ambiguity.
    """
    if not rows:
        return (
            "## Contradicciones detectadas\n\n"
            "Ninguna. Las fuentes procesadas no se contradicen entre sí en los "
            "puntos extraídos. Esto no significa consenso del campo: significa "
            "que las fuentes que este run alcanzó coinciden.\n"
        )
    body = "\n\n".join(format_contradiction(r) for r in rows)
    return (
        f"## Contradicciones detectadas ({len(rows)})\n\n"
        "Los conflictos siguientes se reportan SIN resolver, a propósito. "
        "Elegir un ganador en silencio sería inventar una certeza que las "
        "fuentes no dan.\n\n"
        f"{body}\n"
    )
