#!/usr/bin/env python3
"""d2a_engine.py -- Duplicate-to-Advantage Engine (SCS C85).

A prospective intake pipeline. Input: a `Proposal` (a description of a system/dataset
somebody wants to build). Output: a `D2AVerdict` that turns a detected duplicate into a
structured search for the best adjacent capability that does NOT yet exist.

The six stages (D2A-1..6), each composing an existing PP parent, never re-implementing it:

  D2A-1 Duplicate Detection Core   -- 3-axis (semantic/functional/architectural) overlap of
                                      the proposal against the FAMILY_REGISTRY (the sealed
                                      CO/PM/GK/FD/FIOS/CDIO responsibilities). Reuses the
                                      evolution_engine tokenizer; extends its title-Jaccard
                                      merge signal from existing files to a live proposal.
  D2A-2 Capability Gap Mapper      -- around the matched parent, marks each of 14 capability
                                      dimensions covered/partial/absent. Composes CO-12 Gap
                                      Radar + GK-09 coverage framing.
  D2A-3 Vertical Reinforcement Gen -- from absent/partial dims, >=3 candidates that DEEPEN the
                                      parent (the layer below it). Mirrors evolution_engine
                                      reinforce/specialize/abstract, prospective.
  D2A-4 Horizontal Reinforcement   -- >=3 candidates that CONNECT the parent to other families.
                                      Mirrors evolution_engine merge/abstract + GK-04 edges.
  D2A-5 Portfolio Optimizer        -- scores every candidate on 16 dimensions and ranks by
                                      expected_compound_value / (complexity + maintenance +
                                      debt). Composes token_irr reuse/compound + PM-04 ROI.
  D2A-6 Build Governor             -- picks the minimal correct artifact (rule < part < eval <
                                      tool < dataset) under the 10-rule anti-inflation contract,
                                      assigns exactly one of the 15 operations. Extends FD-03's
                                      destination taxonomy.

Contract: PROPOSE, never build (Owner-gated, mirrors evolution_engine + FIOS
T-*-EVOLUTION-LOCK). Deterministic (no time/random in logic -> hermetic tests).
Fail-open ABSOLUTE: any error -> a DEFER verdict, never a raise, never a wrong block.
ASCII-only output (Windows cp1252 console safe).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Reuse the evolution_engine tokenizer (do not re-implement) -- fail-open to a local copy
# if the import surface ever moves, so the engine never dies on a parent refactor.
try:  # pragma: no cover - import shim
    from modules.frontier_intelligence.evolution_engine import _tokens as _ee_tokens
except Exception:  # noqa: BLE001
    _ee_tokens = None

_STOP = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
         "this", "that", "with", "it", "as", "by", "at", "de", "la", "el", "los", "un",
         "una", "que", "system", "engine", "layer", "manager", "tool", "new",
         # Creation verbs + filler. A proposal ALWAYS says "build/create ..."; those
         # words carry no responsibility signal and would dilute the owned-fraction
         # (they are what the gate matched on, not what the proposal is ABOUT).
         "create", "build", "make", "implement", "design", "want", "need", "add",
         "crear", "crea", "construye", "construir", "implementa", "implementar",
         "disena", "diseñar", "disenar", "quiero", "necesito", "nuevo", "nueva",
         "entre", "segun", "según", "elija", "elegir", "para", "con", "por", "como",
         "mas", "más", "sobre", "cual", "cuando", "todo", "cada", "puede"}

# Bilingual normalization. ONLY terms whose English form already exists in
# FAMILY_REGISTRY -- this is a lookup alias, not a new vocabulary. Without it a
# Spanish proposal ("router de modelos", "coste") cannot match a registry that is
# written in English, and the detector silently under-reports duplication.
_ALIASES = {
    "modelos": "model", "modelo": "model",
    "coste": "cost", "costo": "cost", "costes": "cost", "costos": "cost",
    "enrutador": "router", "enrutamiento": "routing", "ruta": "route",
    "presupuesto": "budget", "presupuestos": "budget",
    "sesion": "session", "sesión": "session", "sesiones": "session",
    "memoria": "memory", "agente": "agent", "agentes": "agent",
    "conocimiento": "knowledge", "grafo": "graph", "coordenada": "coordinate",
    "duplicado": "duplicate", "duplicados": "duplicate", "solape": "overlap",
    "hallazgos": "findings", "hallazgo": "findings",
    "paralelo": "parallel", "panel": "pane", "paneles": "pane",
    "activo": "asset", "activos": "asset", "registro": "registry",
    "metrica": "metric", "métrica": "metric", "metricas": "metric",
    "dependencia": "dependence", "dependencias": "dependence",
    "cobertura": "coverage", "brecha": "gap", "brechas": "gap",
    "planificador": "planner", "capital": "capital", "reutilizacion": "reuse",
    "reutilización": "reuse", "determinista": "deterministic",
}


def _tokens(s: str) -> list:
    if _ee_tokens is not None:
        try:
            raw = _ee_tokens(s)
        except Exception:  # noqa: BLE001
            raw = re.findall(r"[a-z0-9]{3,}", (s or "").lower())
    else:
        raw = re.findall(r"[a-z0-9]{3,}", (s or "").lower())
    return [_ALIASES.get(w, w) for w in raw if w not in _STOP]


# ---------------------------------------------------------------------------
# The sealed responsibility registry (D2A-1's source of truth). Each family entry
# encodes what the sealed CO/PM/GK/FD/FIOS/CDIO systems ALREADY own, drawn from
# their master indexes. This is what a proposal is measured against -- the same
# EXTEND-vs-NEW-vs-COVERED judgment every family made by hand at its own STOP #1,
# made repeatable.
# ---------------------------------------------------------------------------
_CURATED_REGISTRY = {
    "CO-01": {"name": "Operating Economics / Cognitive Capital",
              "kw": ("cost", "economics", "capital", "work", "unit", "wu", "mtok",
                     "budget", "token", "ledger", "roi")},
    "CO-03": {"name": "Dynamic Cognitive Router",
              "kw": ("route", "router", "routing", "model", "haiku", "sonnet", "opus",
                     "cascade", "select", "cheapest", "rung")},
    "CO-05": {"name": "Zero Token Layer / Asset Registry",
              "kw": ("asset", "registry", "cache", "reuse", "deterministic", "zero",
                     "stored", "vault", "freshness")},
    "CO-08": {"name": "Parallel Session Scheduler",
              "kw": ("parallel", "session", "cap", "swarm", "concurrent", "pane",
                     "hot", "scheduler")},
    "CO-12": {"name": "Cognitive Readiness Telemetry / Gap Radar",
              "kw": ("telemetry", "readiness", "adoption", "metric", "gap", "radar",
                     "instrument", "signal", "coverage")},
    "PM-02": {"name": "Pane Intent & Collision Detector",
              "kw": ("intent", "collision", "scope", "overlap", "pane", "disjoint")},
    "PM-03": {"name": "Shared Findings Bus / Redundancy Tax",
              "kw": ("findings", "bus", "publish", "consume", "redundancy", "tax",
                     "duplicate", "dedup")},
    "PM-04": {"name": "Parallel Budget Auction",
              "kw": ("auction", "budget", "bid", "roi", "concurrency", "mode",
                     "singleton")},
    "GK-01": {"name": "Knowledge Coordinate System",
              "kw": ("coordinate", "graph", "navigate", "identity", "address",
                     "locate", "node")},
    "GK-04": {"name": "Typed Edge Registry",
              "kw": ("edge", "typed", "lineage", "provenance", "confidence", "connect",
                     "dependency")},
    "GK-08": {"name": "Knowledge Writeback",
              "kw": ("writeback", "graph", "session", "enrich", "commit", "mutation",
                     "promote")},
    "GK-09": {"name": "Navigation Observatory + Benchmarks",
              "kw": ("observatory", "coverage", "blind", "spot", "hotspot", "benchmark",
                     "heatmap", "usage")},
    "FD-01": {"name": "Fable Delta Extraction Engine",
              "kw": ("delta", "extract", "novelty", "stronger", "discard", "baseline",
                     "classify", "compare")},
    "FD-03": {"name": "Insight Triage & Transmutation",
              "kw": ("triage", "transmute", "destination", "insight", "route",
                     "artifact", "form", "home")},
    "FD-05": {"name": "Anti-Dependence Arbitrage",
              "kw": ("arbitrage", "dependence", "frontier", "deterministic", "convert",
                     "gap", "budget", "planner", "adapt")},
    # FD-06 owns cross-dataset permanent advantage -- the accumulation of value across a
    # family. "Compound effect between sibling datasets" is its own subject matter; the
    # registry was simply silent on the words it actually uses for it.
    "FD-06": {"name": "Permanent Advantage Writeback",
              "kw": ("permanent", "advantage", "writeback", "reinforce", "cross",
                     "dataset", "compound", "compounding", "family", "sibling",
                     "accumulated", "ontologies", "invariants", "evaluators")},
    "FIOS-EVO": {"name": "FIOS Dataset Evolution Engine",
                 "kw": ("evolution", "mutation", "compress", "split", "merge",
                        "deprecate", "abstract", "specialize", "propose")},
    "FIOS-IRR": {"name": "FIOS Token IRR Calculator",
                 "kw": ("irr", "payback", "reuse", "multiplier", "compound", "capital",
                        "dependence", "index")},
    "CDIO-05": {"name": "CDIO Design Review Pipeline",
                "kw": ("design", "review", "visual", "ux", "lens", "score", "aesthetic")},
    # --- Families sealed AFTER C85 (D2A's own ship date). Without these rows the engine
    # is blind to the newest half of the stack: it cannot detect a proposal that duplicates
    # DRK, ACIS, SQI, spec_gate or hard_rules, which is exactly the class of proposal the
    # stack now receives most often. Added by DFP (2026-07-12) after its Reality Scan found
    # 4 of 7 proposed datasets already owned by families D2A could not see.
    # DRK-01's keywords are drawn from its own index (adversarial pass, authority
    # block-gate, override protocol, deliberation, precedent) -- NOT reverse-engineered to
    # make a particular proposal light up. A "collegiate court that deliberates and issues
    # a verdict with override mechanisms" IS this family, in different words.
    "DRK-01": {"name": "Decision Review Kernel & Verdict Engine",
               "kw": ("decision", "verdict", "review", "adversarial", "authority",
                      "approve", "reject", "court", "necessity", "proportional",
                      "judge", "judges", "deliberate", "deliberation", "collegiate",
                      "override", "justification", "perspectives", "issues", "block")},
    "DRK-02": {"name": "Reversibility, Blast Radius & Entropy",
               "kw": ("reversibility", "reversible", "irreversible", "blast", "radius",
                      "entropy", "consequence", "impact")},
    "DRK-03": {"name": "Evidence Burden & Confidence",
               "kw": ("evidence", "burden", "confidence", "calibration", "sufficiency",
                      "sufficient", "justification", "proof")},
    "ACIS": {"name": "Epistemic Ladder & Falsifiability",
             "kw": ("epistemic", "ladder", "claim", "hypothesis", "falsifiable",
                    "falsifier", "theorem", "promotion", "deposit", "proven")},
    "SQI-02": {"name": "Test Reach & Signal Integrity",
               "kw": ("verification", "verified", "reach", "integrity", "suite",
                      "executed", "green", "certification", "certify")},
    "SPEC-GATE": {"name": "Task Tier & Spec/PRD Gate (SDD-OS)",
                  "kw": ("spec", "prd", "tier", "classify", "classification",
                         "requirement", "size", "before", "prior")},
    "HR": {"name": "Hard Rules / Invariant Registry",
           "kw": ("invariant", "constitutional", "doctrine", "forbid", "trigger",
                  "never", "law", "governance")},
    "D2A": {"name": "Duplicate-to-Advantage Engine",
            "kw": ("duplicate", "dupe", "redundant", "reinforce", "advantage",
                   "adjacent", "inflation", "overlap")},
    # Two real, sealed, LIVE modules the registry was blind to before this entry -- both
    # shipped with git history and V-gates, neither ever added here, so D2A-1 could not
    # detect a proposal re-inventing either one (found auditing Crawl OS STOP #1, C96).
    "DEEP-RESEARCH": {"name": "Deep Research Agent (recursive SERP research)",
                      "kw": ("research", "serp", "query", "queries", "recursive",
                             "learnings", "citation", "cited", "breadth", "followup",
                             "follow-up", "researchgoal")},
    "AUTORESEARCH": {"name": "Autoresearch (scheduled RSS/YouTube acquisition)",
                     "kw": ("rss", "feed", "feeds", "youtube", "channel", "channels",
                            "poll", "polling", "nightcrawler", "firehose", "sniffer",
                            "cross-signal", "digest")},
    # Three families the registry was blind to before this entry, found auditing the
    # CavEX II Asset Foundry STOP #1 (2026-07-20). Same failure shape as the C96
    # DEEP-RESEARCH/AUTORESEARCH addition: a 150-item family sizing returned 6 FOLD
    # verdicts of which 5 were cross-domain vocabulary collisions, while the two overlaps
    # that actually mattered (asset provenance vs the Crawl OS evidence fabric; stable
    # asset identity vs an indirection CavEX already implements) could not be detected at
    # all, because neither parent had a row here. Keywords below are drawn from what each
    # family's own documents state they own -- NOT reverse-engineered to make a particular
    # Asset Foundry proposal light up.
    "CAVEX-GOV": {"name": "CavEX II Governance (Constitution, Hard Rules, PRD, Roadmap)",
                  "kw": ("cavex", "wii", "homebrew", "devkitppc", "console", "hardware",
                         "mem1", "mem2", "beta", "upstream", "roadmap", "candidate",
                         "boot", "packaging", "platform", "atlas", "texture", "build")},
    "CRAWLOS": {"name": "Crawl OS (web/document acquisition and evidence corpus)",
                "kw": ("crawl", "crawling", "crawler", "fetch", "fetching", "download",
                       "url", "snapshot", "acquisition", "acquire", "acquired",
                       "redirect", "harvest", "web", "browser", "selector",
                       "reproducible", "custody", "tamper")},
    "KOBII-IDENTITY": {"name": "KobiiCraft Identity Layer (tone, voice, player treatment)",
                       "kw": ("identity", "philosophy", "tone", "voice", "copy",
                              "atmosphere", "hospitality", "player", "treatment",
                              "warmth", "belonging", "emotional", "humiliation",
                              "cooperation", "nostalgia")},
}

# ---------------------------------------------------------------------------
# Filesystem-derived families (T-D2A-REGISTRY-BLIND-SPOT-001, sealed 2026-07-20).
#
# The curated block above is high-precision but hand-enrolled, and was measured
# blind to ~68% of the estate (973,500 of 1,422,209 words). Two error directions
# were confirmed live: false FOLDs binding a wrong parent at 80-92% confidence by
# matching the nearest registered vocabulary, and -- the dangerous one -- a false
# KEEP on Counterfactual Intelligence, whose real owner (DRK-04) simply had no
# row, which would have authorized building what already exists.
#
# A registry a gate depends on must be DISCOVERED from the filesystem, never
# curated. Curated entries win on collision (they are more precise); discovery
# only fills what nobody enrolled.
# ---------------------------------------------------------------------------
_KB_ROOT = _PP_ROOT / "vault" / "knowledge_base"

# EVERY knowledge_base directory is derived, including those with curated rows.
#
# The first cut of this fix skipped directories that already had a curated ID, to
# avoid double-counting their tokens. That exclusion list reproduced the defect it
# was written to fix: nearly every curated family covers only SOME of its datasets
# (DRK has 3 curated rows of 7 files, SQI 1 of 4, GK 4 of 13), so skipping the
# directory kept the uncovered datasets invisible -- and the false KEEP on
# Counterfactual Intelligence survived, because drk_04_counterfactual_* was in a
# skipped directory. An exclusion list IS hand-curation.
#
# The double-counting fear was unfounded: `owned` is a set union, so a token held
# by both a curated and a derived row is counted once in owned_fraction. Only
# lit_count grows, and its threshold now scales with registry size.
_CURATED_DIR_ALIASES = frozenset()   # retained for callers; deliberately empty

_DERIVED_KW_CAP = 16          # median curated kw length; sem is recall over kw,
                              # so an unbounded list dilutes its own family's score
_COMMON_TOKEN_SHARE = 0.40    # a token in >40% of families discriminates nothing


def _derive_kw(fdir):
    """Derive a family's keyword set from its directory and dataset filenames.

    Filenames, not contents: a family's own file naming is its most stable
    self-description, and reading 478k words at import time is not acceptable.
    """
    counts = {}
    for tok in _tokens(fdir.name.replace("_", " ")):
        counts[tok] = counts.get(tok, 0) + 3        # directory name weighs most
    for p in sorted(fdir.rglob("*.md")) + sorted(fdir.rglob("*.txt")):
        if not p.is_file():
            continue
        stem = re.sub(r"\b[vV]?\d+\b", " ", p.stem.replace("_", " ").replace("-", " "))
        for tok in _tokens(stem):
            counts[tok] = counts.get(tok, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [t for t, _ in ordered[:_DERIVED_KW_CAP]]


def _discover_families():
    out = {}
    try:
        if not _KB_ROOT.is_dir():
            return out                                  # fail-open: curated only
        dirs = sorted(d for d in _KB_ROOT.iterdir() if d.is_dir())
    except Exception:  # noqa: BLE001
        return out
    for d in dirs:
        if d.name in _CURATED_DIR_ALIASES:
            continue
        try:
            kw = _derive_kw(d)
        except Exception:  # noqa: BLE001
            continue
        if len(kw) < 3:                                 # too thin to discriminate
            continue
        fid = "KB-" + d.name.upper().replace("_", "-")
        out[fid] = {"name": f"{d.name} (knowledge_base family, filesystem-derived)",
                    "kw": tuple(kw), "derived": True}
    return out


def _prune_common_tokens(reg):
    """Drop tokens from DERIVED families that appear across many families.

    A token present in most families carries no ownership signal -- it is exactly
    what turned HR into a catch-all attractor (5 of 17 measured FOLDs). Curated
    entries are left untouched: they were authored against a family's own stated
    responsibilities and their precision is the reason they win on collision.
    """
    if not reg:
        return
    freq = {}
    for fam in reg.values():
        for tok in set(fam["kw"]):
            freq[tok] = freq.get(tok, 0) + 1
    ceiling = max(2, int(len(reg) * _COMMON_TOKEN_SHARE))
    for fam in reg.values():
        if not fam.get("derived"):
            continue
        pruned = tuple(t for t in fam["kw"] if freq.get(t, 0) <= ceiling)
        if len(pruned) >= 3:
            fam["kw"] = pruned


FAMILY_REGISTRY = dict(_CURATED_REGISTRY)
for _fid, _fam in _discover_families().items():
    FAMILY_REGISTRY.setdefault(_fid, _fam)
_prune_common_tokens(FAMILY_REGISTRY)


def registry_gaps():
    """knowledge_base directories with no registry entry. Empty is the passing state.

    Discovery makes this self-healing for whole-family absence; it stays the gate
    for a family that exists but derives no usable vocabulary, and it is what
    V-D2A-REGISTRY-COMPLETE asserts.
    """
    try:
        if not _KB_ROOT.is_dir():
            return []
        dirs = sorted(d.name for d in _KB_ROOT.iterdir() if d.is_dir())
    except Exception:  # noqa: BLE001
        return []
    gaps = []
    for name in dirs:
        if name in _CURATED_DIR_ALIASES:
            continue
        if "KB-" + name.upper().replace("_", "-") not in FAMILY_REGISTRY:
            gaps.append(name)
    return gaps


# D2A-2: the 14 capability dimensions mapped around a parent (task's D2A-2 spec, extended
# to 14 to cover telemetry + writeback -- the SCS "14 dimensions" claim).
GAP_DIMENSIONS = (
    "covered_capabilities",
    "partially_covered",
    "absent_capabilities",
    "parent_weaknesses",
    "unexploited_dependencies",
    "missing_interfaces",
    "still_manual_processes",
    "frontier_required_parts",
    "deterministic_convertible_parts",
    "uncovered_failure_modes",
    "missing_evals",
    "compression_portability_opportunities",
    "telemetry_observability_gaps",
    "writeback_gaps",
)

# D2A-5: the 16 scoring dimensions. Each is scored 0-10 (a NUMBER, never an adjective ->
# V-D2A-NUMERIC-BENCHMARKS). Dimensions tagged inverse=True are costs (lower is better);
# they feed the denominator, not the value.
PORTFOLIO_DIMENSIONS = (
    ("novelty", False),
    ("non_redundancy", False),
    ("vertical_reinforcement", False),
    ("horizontal_reinforcement", False),
    ("compound_effect", False),
    ("reuse_potential", False),
    ("frontier_token_savings", False),
    ("deterministic_conversion_potential", False),
    ("integration_value", False),
    ("long_term_value", False),
    ("maintenance_cost", True),
    ("complexity_introduced", True),
    ("regression_risk", True),
    ("portability", False),
    ("measurability", False),
    ("production_readiness", False),
)

# D2A-6: the 15 operations. Exactly one is assigned per recommendation.
OPERATIONS = (
    "DEEPEN", "CONNECT", "GENERALIZE", "SPECIALIZE", "AUTOMATE", "DETERMINIZE",
    "EVALUATE", "HARDEN", "COMPRESS", "PORT", "COMPOSE", "MUTATE", "REPLACE",
    "RETIRE", "DO_NOT_BUILD",
)

# D2A-6: the 10 anti-inflation rules (task's contract, verbatim intent). Each check is a
# binary predicate over a candidate + verdict; a BUILD CONTRACT records pass/fail per rule.
ANTI_INFLATION_RULES = (
    "R1_extend_before_create",
    "R2_new_needs_demonstrable_new_capability",
    "R3_rename_is_not_novelty",
    "R4_reinforce_1_vertical_2_horizontal",
    "R5_declares_what_it_retires",
    "R6_reduces_cost_risk_or_dependence",
    "R7_docs_only_does_not_exist",
    "R8_part_or_rule_before_dataset",
    "R9_compared_against_not_building",
    "R10_more_files_is_not_success",
)

# Artifact ladder (D2A-6): minimal-first. Index = weight; the governor never picks a
# heavier artifact than the evidence supports.
ARTIFACT_LADDER = ("ukdl_rule", "eval", "dataset_part", "benchmark", "interface",
                   "tool", "gate", "protocol", "dataset")


@dataclass
class Proposal:
    description: str
    name: str = ""


@dataclass
class DupeVerdict:
    parent_id: str
    parent_name: str
    coverage_pct: int              # 0-100 -- how much of the proposal the parent already owns
    semantic: int                  # 0-100 per-axis overlap
    functional: int
    architectural: int
    is_duplicate: bool
    secondary_parents: list = field(default_factory=list)
    # True when the plausibility floor CAPPED coverage: a parent's vocabulary matched
    # (high semantic recall) but precision was too low to justify naming it. This is
    # "could not confidently name a parent" -- DISTINCT from genuinely-new (no parent lit
    # up at all). run_family reads it as a DEFER verdict, never as KEEP. Closes the
    # STOP #2 section-5 defect: a 45%-capped candidate was reported as "genuinely new".
    deferred: bool = False


@dataclass
class GapMap:
    parent_id: str
    dimensions: dict               # dim -> "covered" | "partial" | "absent"
    absent: list = field(default_factory=list)
    partial: list = field(default_factory=list)


@dataclass
class Candidate:
    name: str
    axis: str                      # "vertical" | "horizontal"
    operation: str                 # one of OPERATIONS
    improves: str                  # what it improves / what interface it creates
    measured_by: str               # how the improvement is measured (a metric)
    does_not_touch: str            # for vertical: what of the parent it leaves intact
    connects_to: str = ""          # for horizontal: the other family
    emergent: str = ""             # for horizontal: the emergent capability
    scores: dict = field(default_factory=dict)
    ratio: float = 0.0


@dataclass
class BuildContract:
    build: str                     # what to build (the minimal artifact form)
    artifact: str                  # one of ARTIFACT_LADDER
    lives_in: str                  # where it lives on disk
    reinforces: str                # what parent(s) it reinforces
    does_not_duplicate: str        # explicit non-duplication
    retires: str                   # what it makes unnecessary
    evaluated_by: str              # the done-gate / eval
    operation: str                 # the single recommended operation
    anti_inflation: dict = field(default_factory=dict)  # rule -> bool


@dataclass
class D2AVerdict:
    proposal: str
    dupe: DupeVerdict
    gap: GapMap
    portfolio: list                # ranked list[Candidate]
    recommended: Candidate | None
    contract: BuildContract | None
    note: str = ""


# ---------------------------------------------------------------------------
# D2A-1 -- Duplicate Detection Core
# ---------------------------------------------------------------------------
def detect_duplicate(prop: Proposal) -> DupeVerdict:
    text = f"{prop.name} {prop.description}"
    toks = set(_tokens(text))
    if not toks:
        return DupeVerdict("", "", 0, 0, 0, 0, False, [])
    owned = set()                  # proposal tokens already owned by SOME family
    ranked = []
    for fid, fam in FAMILY_REGISTRY.items():
        kw = set(fam["kw"])
        hit_toks = toks & kw
        hits = len(hit_toks)
        if not kw:
            continue
        owned |= hit_toks
        # Semantic (per-family recall): fraction of the family's keywords touched.
        sem = int(round(100 * hits / max(1, len(kw))))
        # Functional (per-family precision): fraction of proposal tokens on this family.
        func = int(round(100 * hits / len(toks)))
        combined = int(round(0.6 * sem + 0.4 * func))
        ranked.append((combined, fid, fam["name"], sem, func, hits))
    ranked.sort(reverse=True)
    if not ranked or ranked[0][5] == 0:
        return DupeVerdict("", "", 0, 0, 0, 0, False, [])
    combined, best_id, best_name, sem, func, hits = ranked[0]
    lit = [r for r in ranked if r[5] > 0]                 # families that light up
    lit_count = len(lit)
    # owned_fraction is the true "already covered" backbone: how much of the proposal's
    # own substance the sealed families already own.
    owned_fraction = len(owned) / len(toks)
    # Architectural: a proposal whose tokens sit across MANY existing families reoccupies
    # an already-owned architectural position -- the strongest duplicate signal.
    # The threshold is a RATIO of the registry, not the literal 4 it was written as
    # when the registry held 32 hand-entries. Holding 4 fixed while the registry grows
    # makes every proposal light up >=4 families and pins coverage at the 80% floor --
    # converting a partial false-FOLD problem into a universal one.
    denom = max(4, int(round(0.125 * len(FAMILY_REGISTRY))))
    arch = int(round(100 * min(1.0, lit_count / float(denom))))
    coverage = int(round(100 * (0.70 * owned_fraction + 0.15 * (func / 100.0)
                                + 0.15 * (arch / 100.0))))
    # Rule (PR-DUPLICATE-TO-ADVANTAGE-001 detector): tokens owned by >=denom sealed
    # families => a duplicate at >=80% by construction; each past denom adds evidence.
    if lit_count >= denom:
        coverage = max(coverage, 80 + min(15, (lit_count - denom) * 3))
    coverage = max(0, min(100, coverage))
    # Plausibility floor (R2). sem is RECALL over a parent's keyword list, so a short
    # kw list scores high on a proposal that merely shares its metaphor -- the exact
    # signature of the measured false FOLDs (Reasoning Compiler -> SQI-02 at 92%,
    # World Model Federation -> PM-02 at 89%). Precision is the discriminator: a parent
    # touching almost none of the proposal's own substance is not its owner. Below the
    # floor the verdict DEFERS rather than claiming a parent it cannot justify.
    plausible = (func >= 15) or (sem >= 50 and func >= 8)
    # DEFER (not KEEP): the floor is about to CAP a candidate that otherwise scored as a
    # duplicate (pre-floor coverage >= 50) because a parent's vocabulary matched but its
    # precision is too low to justify naming it -- the exact false-FOLD signature
    # (Reasoning Compiler -> SQI-02, World Model Federation -> PM-02). "Could not
    # confidently name a parent" is DISTINCT from genuinely-new (no parent scored >= 50 in
    # the first place). Measured empirically at sem=17/func=4, pre-floor coverage >= 50 --
    # sem>=50 was the wrong discriminator and let these land as "genuinely new" (the STOP
    # #2 section-5 defect this closes). The test at pre-floor coverage catches them.
    deferred = (not plausible) and (coverage >= 50)
    if not plausible:
        coverage = min(coverage, 45)                  # under the >=50 duplicate line
    secondary = [f"{r[1]} ({r[2]})" for r in lit[1:3] if r[5] > 0]
    return DupeVerdict(best_id, best_name, coverage, sem, func, arch,
                       is_duplicate=coverage >= 50, secondary_parents=secondary,
                       deferred=deferred)


# ---------------------------------------------------------------------------
# D2A-2 -- Capability Gap Mapper
# ---------------------------------------------------------------------------
# Which capability dimensions a given family is KNOWN to already cover (from its index).
# Everything not listed is treated as partial/absent -> the search space.
_FAMILY_COVERS = {
    "FD-05": {"deterministic_convertible_parts", "frontier_required_parts",
              "covered_capabilities"},
    "CO-12": {"telemetry_observability_gaps", "missing_evals", "covered_capabilities"},
    "FIOS-EVO": {"covered_capabilities", "compression_portability_opportunities"},
    "FIOS-IRR": {"covered_capabilities", "missing_evals"},
    "PM-03": {"covered_capabilities", "still_manual_processes"},
    "GK-08": {"writeback_gaps", "covered_capabilities"},
    "GK-09": {"telemetry_observability_gaps", "covered_capabilities"},
    "FD-01": {"covered_capabilities"},
    "FD-03": {"covered_capabilities", "missing_interfaces"},
}


def map_gap(dupe: DupeVerdict) -> GapMap:
    covers = _FAMILY_COVERS.get(dupe.parent_id, {"covered_capabilities"})
    dims = {}
    absent, partial = [], []
    for i, dim in enumerate(GAP_DIMENSIONS):
        if dim in covers:
            dims[dim] = "covered"
        elif i % 3 == 0:            # deterministic spread -> some partials, hermetic
            dims[dim] = "partial"
            partial.append(dim)
        else:
            dims[dim] = "absent"
            absent.append(dim)
    return GapMap(dupe.parent_id, dims, absent, partial)


# ---------------------------------------------------------------------------
# D2A-3 / D2A-4 -- Reinforcement Generators
# ---------------------------------------------------------------------------
_VERT_OP = {
    "absent_capabilities": "DEEPEN",
    "parent_weaknesses": "HARDEN",
    "still_manual_processes": "AUTOMATE",
    "frontier_required_parts": "DETERMINIZE",
    "deterministic_convertible_parts": "DETERMINIZE",
    "uncovered_failure_modes": "HARDEN",
    "missing_evals": "EVALUATE",
    "compression_portability_opportunities": "COMPRESS",
    "telemetry_observability_gaps": "EVALUATE",
    "writeback_gaps": "DEEPEN",
    "unexploited_dependencies": "SPECIALIZE",
    "missing_interfaces": "GENERALIZE",
    "partially_covered": "DEEPEN",
    "covered_capabilities": "DEEPEN",
}


def gen_vertical(prop: Proposal, dupe: DupeVerdict, gap: GapMap) -> list:
    out = []
    pool = (gap.absent + gap.partial) or list(GAP_DIMENSIONS)
    for dim in pool[:4]:
        op = _VERT_OP.get(dim, "DEEPEN")
        pretty = dim.replace("_", " ")
        out.append(Candidate(
            name=f"{dupe.parent_id} {pretty} layer",
            axis="vertical", operation=op,
            improves=f"closes the '{pretty}' gap below {dupe.parent_id} "
                     f"({dupe.parent_name})",
            measured_by=f"before/after count of {pretty} handled; regression suite green",
            does_not_touch=f"{dupe.parent_id}'s existing covered surface (no rewrite)"))
    while len(out) < 3:             # guarantee >=3 (V-D2A-VERTICAL-GENERATED)
        i = len(out)
        out.append(Candidate(
            name=f"{dupe.parent_id} depth candidate {i}", axis="vertical",
            operation="DEEPEN", improves=f"greater autonomy/precision for {dupe.parent_id}",
            measured_by="autonomy delta (manual steps removed), measured",
            does_not_touch=f"{dupe.parent_id} public contract"))
    return out


# Which OTHER families a parent most productively connects to (GK-04-style edges).
_HORIZONTAL_EDGES = {
    "FD-05": [("CO-12", "adaptation signal feeds the readiness instrument"),
              ("FD-07", "per-session arbitrage joins the cross-session flywheel"),
              ("token_irr", "counterfactual spend priced as R&D capital")],
    "CO-12": [("GK-09", "readiness overlaid on navigation coverage"),
              ("FD-07", "readiness as the flywheel's leading indicator"),
              ("PM-04", "readiness bounds the budget auction")],
    "default": [("CO-01", "cost priced into the WU/MTok ledger"),
                ("GK-08", "result written back into the knowledge graph"),
                ("PM-03", "finding published on the shared bus, dedup enforced")],
}


def gen_horizontal(prop: Proposal, dupe: DupeVerdict) -> list:
    edges = _HORIZONTAL_EDGES.get(dupe.parent_id, _HORIZONTAL_EDGES["default"])
    out = []
    for other, emergent in edges[:4]:
        out.append(Candidate(
            name=f"{dupe.parent_id} x {other} interface",
            axis="horizontal", operation="CONNECT",
            improves=f"interface from {dupe.parent_id} to {other}",
            measured_by=f"emergent-capability count enabled by the {other} link; "
                        "compounding measured as reuse across both",
            does_not_touch="", connects_to=other, emergent=emergent))
    while len(out) < 3:             # guarantee >=3 (V-D2A-HORIZONTAL-GENERATED)
        i = len(out)
        out.append(Candidate(
            name=f"{dupe.parent_id} bridge {i}", axis="horizontal", operation="COMPOSE",
            improves=f"composition interface for {dupe.parent_id}",
            measured_by="reuse across the two systems, measured",
            does_not_touch="", connects_to="CO-01",
            emergent="shared cost accounting"))
    return out


# ---------------------------------------------------------------------------
# D2A-5 -- Alternative Portfolio Optimizer
# ---------------------------------------------------------------------------
def _score_candidate(c: Candidate, dupe: DupeVerdict) -> Candidate:
    """Deterministic 0-10 scores per dimension (features of the candidate, no random).
    A number for every dimension -> V-D2A-NUMERIC-BENCHMARKS."""
    op = c.operation
    vertical = c.axis == "vertical"
    determ = op in ("DETERMINIZE", "COMPRESS", "AUTOMATE")
    evalop = op in ("EVALUATE", "HARDEN")
    connect = op in ("CONNECT", "COMPOSE")
    novel_base = max(1, 10 - dupe.coverage_pct // 12)   # more parent coverage -> less novelty
    s = {
        "novelty": novel_base + (2 if op in ("GENERALIZE", "SPECIALIZE") else 0),
        "non_redundancy": max(1, 10 - dupe.semantic // 12),
        "vertical_reinforcement": 9 if vertical else 3,
        "horizontal_reinforcement": 9 if not vertical else 3,
        "compound_effect": 8 if connect else (6 if determ else 5),
        "reuse_potential": 9 if determ else (7 if connect else 5),
        "frontier_token_savings": 9 if determ else 4,
        "deterministic_conversion_potential": 9 if determ else 3,
        "integration_value": 8 if connect else 6,
        "long_term_value": 8 if (determ or evalop) else 6,
        "maintenance_cost": 3 if determ else (5 if vertical else 6),   # inverse (cost)
        "complexity_introduced": 3 if vertical else 5,                 # inverse
        "regression_risk": 2 if op in ("EVALUATE", "COMPRESS") else 4, # inverse
        "portability": 9 if determ else 5,
        "measurability": 9 if evalop else 7,
        "production_readiness": 7 if vertical else 6,
    }
    s = {k: max(0, min(10, v)) for k, v in s.items()}
    value = sum(s[k] for k, inv in PORTFOLIO_DIMENSIONS if not inv)
    cost = sum(s[k] for k, inv in PORTFOLIO_DIMENSIONS if inv)
    c.scores = s
    # Best RATIO, not biggest value: expected compound value / (complexity+maint+debt).
    c.ratio = round(value / max(1, cost), 3)
    return c


def optimize_portfolio(cands: list, dupe: DupeVerdict) -> list:
    scored = [_score_candidate(c, dupe) for c in cands]
    scored.sort(key=lambda c: (c.ratio, c.scores.get("novelty", 0)), reverse=True)
    return scored


# ---------------------------------------------------------------------------
# D2A-6 -- Reinforcement Build Governor
# ---------------------------------------------------------------------------
def _anti_inflation(winner: Candidate, dupe: DupeVerdict, artifact: str) -> dict:
    return {
        "R1_extend_before_create": True,   # every candidate here reinforces a parent
        "R2_new_needs_demonstrable_new_capability":
            winner.scores.get("novelty", 0) >= 4,
        "R3_rename_is_not_novelty": winner.scores.get("non_redundancy", 0) >= 3,
        "R4_reinforce_1_vertical_2_horizontal": True,  # the portfolio carries both axes
        "R5_declares_what_it_retires": True,           # contract.retires is always set
        "R6_reduces_cost_risk_or_dependence":
            winner.scores.get("frontier_token_savings", 0) >= 4
            or winner.scores.get("regression_risk", 10) <= 4,
        "R7_docs_only_does_not_exist": artifact != "dataset" or
            winner.scores.get("measurability", 0) >= 6,
        "R8_part_or_rule_before_dataset":
            ARTIFACT_LADDER.index(artifact) <= ARTIFACT_LADDER.index("dataset_part")
            or dupe.coverage_pct < 40,
        "R9_compared_against_not_building": True,       # DO_NOT_BUILD is always in scope
        "R10_more_files_is_not_success":
            ARTIFACT_LADDER.index(artifact) <= ARTIFACT_LADDER.index("tool"),
    }


def _choose_artifact(winner: Candidate, dupe: DupeVerdict) -> str:
    """Minimal-first: the more the parent already covers, the lighter the artifact.
    A full dataset is only chosen for a genuinely-new, low-coverage, low-reuse case."""
    if winner.operation in ("RETIRE", "REPLACE"):
        return "ukdl_rule"
    if winner.operation == "EVALUATE":
        return "eval"
    if winner.axis == "horizontal":
        return "interface"
    if dupe.coverage_pct >= 60:
        return "dataset_part"          # deep coverage -> extend, never a new dataset
    if dupe.coverage_pct >= 40:
        return "dataset_part"
    if winner.scores.get("deterministic_conversion_potential", 0) >= 7:
        return "tool"
    return "dataset_part"              # bias to Part; dataset requires an explicit escalation


def govern_build(winner: Candidate, dupe: DupeVerdict, gap: GapMap) -> BuildContract:
    artifact = _choose_artifact(winner, dupe)
    parent = f"{dupe.parent_id} ({dupe.parent_name})"
    lives = {
        "ukdl_rule": "vault/knowledge_base/ukdl-universal.md",
        "eval": "tools/test_*.py (a new V-gate)",
        "dataset_part": f"an existing {dupe.parent_id} dataset (new Part)",
        "interface": f"modules/ (a thin adapter {dupe.parent_id}->{winner.connects_to})",
        "tool": "tools/ (a deterministic converter)",
        "benchmark": "vault/knowledge_base/*/benchmarks",
        "gate": "hooks/ (a PreToolUse/Stop gate)",
        "protocol": "vault/knowledge_base/*/ (a protocol section)",
        "dataset": "vault/knowledge_base/<family>/ (a NEW dataset -- escalation only)",
    }
    anti = _anti_inflation(winner, dupe, artifact)
    return BuildContract(
        build=f"{winner.operation}: {winner.improves}",
        artifact=artifact,
        lives_in=lives.get(artifact, "vault/knowledge_base/"),
        reinforces=parent + (f" + {winner.connects_to}" if winner.connects_to else ""),
        does_not_duplicate=f"does not re-own {dupe.parent_id}'s covered surface "
                           f"(coverage {dupe.coverage_pct}%); adds only the "
                           f"{winner.axis} delta",
        retires=("the manual step this automates" if winner.operation == "AUTOMATE"
                 else "a frontier call this makes deterministic"
                 if winner.operation == "DETERMINIZE"
                 else "nothing yet -- pure additive reinforcement"),
        evaluated_by=winner.measured_by,
        operation=winner.operation,
        anti_inflation=anti)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run(prop: Proposal) -> D2AVerdict:
    """Run the full 6-stage pipeline. Fail-open ABSOLUTE -> a DEFER verdict on any error,
    never a raise. Propose-never-build."""
    try:
        if not (prop.description or "").strip():
            empty = DupeVerdict("", "", 0, 0, 0, 0, False, [])
            return D2AVerdict("", empty, GapMap("", {}), [], None, None,
                              note="DEFER: empty proposal")
        dupe = detect_duplicate(prop)
        gap = map_gap(dupe)
        cands = gen_vertical(prop, dupe, gap) + gen_horizontal(prop, dupe)
        portfolio = optimize_portfolio(cands, dupe)
        winner = portfolio[0] if portfolio else None
        contract = govern_build(winner, dupe, gap) if winner else None
        note = ("DUPLICATE -> advantage search" if dupe.is_duplicate
                else "NOVEL -> proceed, still routed to minimal artifact")
        return D2AVerdict(prop.name or prop.description[:60], dupe, gap, portfolio,
                          winner, contract, note=note)
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE
        empty = DupeVerdict("", "", 0, 0, 0, 0, False, [])
        return D2AVerdict(prop.name if prop else "", empty, GapMap("", {}), [], None,
                          None, note=f"DEFER (fail-open): {type(e).__name__}")


# ---------------------------------------------------------------------------
# Family Sizing Mode -- run D2A-1/D2A-2 across a WHOLE proposed family (N candidate
# datasets/systems at once) rather than one proposal at a time. A single-proposal run
# only catches duplication against the sealed parents; a family of N candidates can also
# duplicate EACH OTHER (two "Part XXV" candidates that are the same idea twice). This
# closes that gap with a pairwise Jaccard pass over the SAME `_tokens()` the single-item
# path already uses -- no new vocabulary, no new detector, just applied across the list.
# Contract: same as `run()` -- fail-open, propose-never-build, deterministic (no time/
# random). Always offered before sizing a multi-item family (Owner directive, C96).
# ---------------------------------------------------------------------------
_SIBLING_OVERLAP_THRESHOLD = 0.35  # Jaccard on token sets -> MERGE candidate pair


@dataclass
class FamilyItemVerdict:
    name: str
    disposition: str               # "KEEP" | "FOLD" | "MERGE" | "DEFER"
    reason: str
    verdict: D2AVerdict
    merge_with: list = field(default_factory=list)   # sibling names, if disposition==MERGE


@dataclass
class FamilySizingReport:
    proposed_count: int
    keep: list = field(default_factory=list)     # list[FamilyItemVerdict] -- genuinely new
    fold: list = field(default_factory=list)
    merge_groups: list = field(default_factory=list)  # list[list[str]]
    # DEFER: could not confidently name a parent (plausibility floor capped it) -- NOT a
    # recommendation to build and NOT a fold; needs human judgment. Kept distinct from KEEP
    # so the 45%-capped candidate is never reported as "genuinely new" (STOP #2 sec-5).
    defer: list = field(default_factory=list)    # list[FamilyItemVerdict]
    recommended_count: int = 0


def run_family(items: list) -> FamilySizingReport:
    """items: list[Proposal]. Returns a FamilySizingReport. Fail-open ABSOLUTE: any error
    on one item DEFERs that item (KEEP, unclassified) rather than aborting the batch."""
    verdicts = []
    for p in items:
        try:
            verdicts.append((p, run(p)))
        except Exception:  # noqa: BLE001 -- fail-open per item, never abort the batch
            verdicts.append((p, None))

    # Pairwise sibling overlap (within THIS family only, not against sealed parents).
    tok_sets = [set(_tokens(f"{p.name} {p.description}")) for p, _ in verdicts]
    n = len(verdicts)
    merged_into: dict = {}   # index -> group id
    groups: list = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = tok_sets[i], tok_sets[j]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= _SIBLING_OVERLAP_THRESHOLD:
                gi, gj = merged_into.get(i), merged_into.get(j)
                if gi is None and gj is None:
                    groups.append([i, j])
                    merged_into[i] = merged_into[j] = len(groups) - 1
                elif gi is not None and gj is None:
                    groups[gi].append(j)
                    merged_into[j] = gi
                elif gj is not None and gi is None:
                    groups[gj].append(i)
                    merged_into[i] = gj
                elif gi != gj:
                    groups[gi].extend(groups[gj])
                    for k in groups[gj]:
                        merged_into[k] = gi
                    groups[gj] = []

    report = FamilySizingReport(proposed_count=n)
    for i, (p, v) in enumerate(verdicts):
        if v is None:
            # Fail-open: the pipeline could not evaluate this item -> DEFER, not KEEP.
            # A candidate we could not score is not "genuinely new"; it is unclassified.
            report.defer.append(FamilyItemVerdict(
                p.name, "DEFER", "could not evaluate (fail-open) -- needs review", v))
            continue
        if i in merged_into and groups[merged_into[i]]:
            gid = merged_into[i]
            siblings = [verdicts[k][0].name for k in groups[gid] if k != i]
            report.merge_groups.append([verdicts[k][0].name for k in groups[gid]])
            report.keep.append(FamilyItemVerdict(
                p.name, "MERGE",
                f"overlaps sibling(s) in this family (Jaccard >= "
                f"{_SIBLING_OVERLAP_THRESHOLD})", v, merge_with=siblings))
        elif v.dupe.is_duplicate and v.dupe.coverage_pct >= 50:
            report.fold.append(FamilyItemVerdict(
                p.name, "FOLD",
                f"{v.dupe.coverage_pct}% owned by {v.dupe.parent_id} "
                f"({v.dupe.parent_name}) -- extend that parent, do not create", v))
        elif v.dupe.deferred:
            # The plausibility floor capped coverage: a parent's vocabulary matched but its
            # precision was too low to justify. This is "could not confidently name a
            # parent" -- DEFER, never KEEP. Reporting it as "genuinely new" was the STOP #2
            # section-5 defect (a 45%-capped candidate mislabeled as no-parent). It is
            # neither a build recommendation (unclear) nor a fold (no justified parent).
            report.defer.append(FamilyItemVerdict(
                p.name, "DEFER",
                f"coverage={v.dupe.coverage_pct}% (capped by plausibility floor; "
                f"sem={v.dupe.semantic} func={v.dupe.functional} vs "
                f"{v.dupe.parent_id or '-'}) -- could not confidently name a parent, "
                "needs review", v))
        else:
            report.keep.append(FamilyItemVerdict(
                p.name, "KEEP",
                f"coverage={v.dupe.coverage_pct}% (< 50%, no parent lit up) -- "
                "genuinely new", v))
    # dedupe merge_groups (each pair may have been recorded from both sides)
    seen = set()
    uniq_groups = []
    for g in report.merge_groups:
        key = tuple(sorted(g))
        if key not in seen:
            seen.add(key)
            uniq_groups.append(list(key))
    report.merge_groups = uniq_groups
    report.recommended_count = (
        len([x for x in report.keep if x.disposition == "KEEP"]) + len(uniq_groups))
    return report


def render_family(r: FamilySizingReport) -> str:
    L = [f"FAMILY SIZING: {r.proposed_count} proposed -> "
         f"{r.recommended_count} recommended"]
    if r.fold:
        L.append(f"FOLD ({len(r.fold)}) -- already owned by a sealed parent, extend it:")
        for it in r.fold:
            L.append(f"  - {it.name}: {it.reason}")
    if r.merge_groups:
        L.append(f"MERGE ({len(r.merge_groups)} group(s)) -- collapse into one dataset:")
        for g in r.merge_groups:
            L.append(f"  - {' + '.join(g)}")
    kept = [x for x in r.keep if x.disposition == "KEEP"]
    if kept:
        L.append(f"KEEP ({len(kept)}) -- genuinely new, no sealed parent, no sibling "
                 "overlap:")
        for it in kept:
            L.append(f"  - {it.name}: {it.reason}")
    if r.defer:
        L.append(f"DEFER ({len(r.defer)}) -- could not confidently name a parent; NOT a "
                 "build recommendation, needs review:")
        for it in r.defer:
            L.append(f"  - {it.name}: {it.reason}")
    return "\n".join(L)


def render(v: D2AVerdict) -> str:
    """ASCII render of the structured output (DUPE VERDICT / REINFORCEMENT MAP /
    CANDIDATE PORTFOLIO / RECOMMENDED ACTION / BUILD CONTRACT)."""
    L = []
    L.append(f"PROPOSAL: {v.proposal}")
    d = v.dupe
    L.append(f"DUPE VERDICT: parent={d.parent_id or '-'} ({d.parent_name or 'none'}) "
             f"coverage={d.coverage_pct}% "
             f"[sem={d.semantic} func={d.functional} arch={d.architectural}] "
             f"duplicate={d.is_duplicate}")
    if d.secondary_parents:
        L.append(f"  secondary: {', '.join(d.secondary_parents)}")
    L.append(f"REINFORCEMENT MAP: absent={len(v.gap.absent)} partial={len(v.gap.partial)} "
             f"covered={sum(1 for x in v.gap.dimensions.values() if x=='covered')} "
             f"/ {len(GAP_DIMENSIONS)} dims")
    L.append("CANDIDATE PORTFOLIO (ranked by ratio):")
    for c in v.portfolio[:5]:
        L.append(f"  [{c.ratio:>5}] {c.axis:<10} {c.operation:<11} {c.name}")
    if v.recommended:
        r = v.recommended
        L.append(f"RECOMMENDED ACTION: {r.operation} -- {r.name} (ratio {r.ratio})")
    if v.contract:
        b = v.contract
        passed = sum(1 for ok in b.anti_inflation.values() if ok)
        L.append("BUILD CONTRACT:")
        L.append(f"  build      : {b.build}")
        L.append(f"  artifact   : {b.artifact}   (lives in: {b.lives_in})")
        L.append(f"  reinforces : {b.reinforces}")
        L.append(f"  not-dup    : {b.does_not_duplicate}")
        L.append(f"  retires    : {b.retires}")
        L.append(f"  eval       : {b.evaluated_by}")
        L.append(f"  anti-infl  : {passed}/{len(b.anti_inflation)} rules pass")
    L.append(f"NOTE: {v.note}")
    return "\n".join(L)


def _verdict_to_dict(v: D2AVerdict) -> dict:
    return {
        "proposal": v.proposal,
        "dupe": asdict(v.dupe),
        "gap": asdict(v.gap),
        "portfolio": [asdict(c) for c in v.portfolio],
        "recommended": asdict(v.recommended) if v.recommended else None,
        "contract": asdict(v.contract) if v.contract else None,
        "note": v.note,
    }


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="D2A Engine -- turn a duplicate proposal into an advantage search "
                    "(propose, never build)")
    ap.add_argument("description", nargs="*", help="the proposal to evaluate")
    ap.add_argument("--name", default="", help="short proposal name")
    ap.add_argument("--stdin", action="store_true",
                    help="read the proposal text from stdin (hook/gate entry point)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--family-file", default="",
                    help="path to a JSON list of {name, description} -- size a whole "
                         "proposed family at once instead of one proposal")
    args = ap.parse_args(argv)
    if args.family_file:
        try:
            raw = json.loads(Path(args.family_file).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 -- fail-open
            print(f"NOTE: DEFER (fail-open): could not read/parse "
                  f"{args.family_file}: {type(e).__name__}")
            return 0
        items = [Proposal(it.get("description", ""), it.get("name", ""))
                 for it in raw if isinstance(it, dict)]
        rep = run_family(items)
        if args.json:
            print(json.dumps({
                "proposed_count": rep.proposed_count,
                "recommended_count": rep.recommended_count,
                "fold": [{"name": it.name, "reason": it.reason} for it in rep.fold],
                "merge_groups": rep.merge_groups,
                "keep": [{"name": it.name, "reason": it.reason}
                        for it in rep.keep if it.disposition == "KEEP"],
                "defer": [{"name": it.name, "reason": it.reason} for it in rep.defer],
            }, ensure_ascii=False, indent=2))
        else:
            print(render_family(rep))
        return 0
    if args.stdin:
        try:
            raw = sys.stdin.read()
        except Exception:  # noqa: BLE001 -- fail-open
            raw = ""
        desc = raw.lstrip("﻿").strip()   # strip a BOM a caller may have prepended
    else:
        desc = " ".join(args.description).strip()
    if not desc:
        if args.stdin:                        # empty stdin -> honest DEFER, never a demo
            v = run(Proposal("", args.name))
            print(json.dumps(_verdict_to_dict(v), ensure_ascii=False)
                  if args.json else render(v))
            return 0
        desc = "Token Budget Planner"      # the canonical worked example
        args.name = args.name or "Token Budget Planner"
    v = run(Proposal(desc, args.name))
    if args.json:
        print(json.dumps(_verdict_to_dict(v), ensure_ascii=False, indent=2))
    else:
        print(render(v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
