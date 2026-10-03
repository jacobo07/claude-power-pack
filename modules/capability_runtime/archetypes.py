"""archetypes.py -- what is this capability? (UCEP Phase 2, requirement UCEP-02).

This module owns the question "what kind of capability does this mission build,
in this repository", as a subject: ten structural traits, three archetypes that
are conjunctions of those traits, and a strength for each archetype. It is the
single authority for archetype conjunctions (resolution R-2): any JSON descriptor
a later phase keeps under `vault/tower/archetypes/` may carry an id, a
description and a donor, must reference ids that exist in `ARCHETYPES` here, and
must not restate a conjunction. Archetype ids are single path segments (R-5):
"WORLD_MUTATION/persistent-state" in the governing spec is a description of the
archetype, not part of its id, and `distributed` is a modifier, never an id part.

PRODUCER / READER SPLIT. Structure is read from a per-user cache that
`trait_scan.produce` writes OUT OF BAND (a CLI or a scheduled task). Nothing here
walks a tree: a walk costs 0.3 to 48 seconds on this estate against a 3000 ms
chain deadline on the prompt path (audit G4, RESEARCH F4), so the prompt path
only READS. This module never imports `trait_scan`; the producer imports this
module, never the reverse, and a gate pins that with an AST check.

ABSENT IS NOT ZERO. Every miss reads UNJUDGED with a named cause from the closed
set `UNJUDGED_CAUSES` and fact state UNKNOWN. A cache that was never produced,
a stale or malformed one, an unresolvable root: none of these may read ABSENT,
because a later phase turns ABSENT into a justified NOT_APPLICABLE and an unread
repository must never earn that. `read_traits` always returns all ten traits.

INTENT IS CAPPED. A fact mined from the prompt alone is EXTRACTED, never
OBSERVED, and (built in plan 02-02) can lift an archetype to CONDITIONAL at most.
REQUIRED needs structural evidence AND intent: a verb acting on an object, never
vocabulary alone (D-04). In this first slice only the `persistent` trait has an
intent detector and only WORLD_MUTATION is judged end to end.

Fact states are the vocabulary of `modules.gsd_x.mission.obligation`, imported and
never re-spelled. Family classification (`modules.tower.families`) is reused for
its matcher and fold, and its result is reported as an independent output of
`resolve`: family and archetype answer different questions (D-02).
"""
from __future__ import annotations

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.gsd_x.mission.obligation import (  # noqa: E402
    EXTRACTED, FACT_STATES, OBSERVED, UNKNOWN)
from modules.repo_identity.identity import canonical_repo, repo_key  # noqa: E402
from modules.tower.families import _fold, _match, classify_prompt  # noqa: E402

SCHEMA = "ucep-traits/1"
SUBJECT_SCHEMA = "ucep-subject/1"

# The ten traits of the roadmap, in roadmap order.
TRAITS = ("persistent", "multi_actor", "bulk", "destructive", "distributed",
          "external_effect", "scheduled", "money", "policy_layers", "ui")

# Trait states. UNJUDGED is its own answer and is never a synonym for ABSENT.
PRESENT = "PRESENT"
WEAK = "WEAK"
ABSENT = "ABSENT"
UNJUDGED = "UNJUDGED"
TRAIT_STATES = (PRESENT, WEAK, ABSENT, UNJUDGED)


class Strength:
    """Archetype strengths, kept in a namespace on purpose: a bare module-level
    REQUIRED would collide in meaning with the baseline entry keys of
    `modules.tower.baselines` (RESEARCH F2 naming trap)."""
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    NONE = "NONE"
    ALL = (REQUIRED, CONDITIONAL, NONE)


# What an assessment rests on.
BASIS_STRUCTURAL = "structural"
BASIS_INTENT = "intent"
BASIS_BOTH = "structural+intent"
BASIS_NONE = "none"

# Why a trait reads UNJUDGED. The first four are reader causes, the rest are
# producer causes; each is made reachable by a gate before Phase 2 ends.
UNJUDGED_CAUSES = ("no-cache", "stale", "cache-malformed", "unresolvable-root",
                   "truncated", "budget-exhausted", "unreadable-subtree",
                   "no-manifest-ecosystem", "no-structural-detector")

# State of the cache document itself.
CACHE_FRESH = "FRESH"
CACHE_MISSING = "NO_CACHE"
CACHE_STALE = "STALE"
CACHE_MALFORMED = "MALFORMED"
CACHE_UNRESOLVABLE = "UNRESOLVABLE"

# An archetype id is ONE path segment: `archetype/<ID>` becomes a directory name
# that the baseline subject discovery walks, so a slash inside an id would invent
# a three-level axis (R-5, RESEARCH Pitfall 11). The `\Z` anchor (not `$`) keeps a
# trailing newline from slipping through.
ARCHETYPE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*\Z")

# Archetypes are declarative conjunctions, and this table is the sole authority
# for them (R-2): the `anchor` trait must be structurally PRESENT for REQUIRED;
# `modifiers` raise the consequence but never create the archetype (consequence
# strengthens an envelope, complexity alone does not); `demoters` are intent
# phrases, in both languages, that lower REQUIRED to CONDITIONAL and never veto.
ARCHETYPES = {
    "WORLD_MUTATION": {
        "anchor": "persistent",
        "modifiers": ("destructive", "bulk", "multi_actor", "distributed", "money"),
        "demoters": ("read-only", "read only", "solo lectura", "dry run",
                     "sin escribir", "simulacion"),
        "description": ('mutation of durable state: the governing spec\'s '
                        '"WORLD_MUTATION/persistent-state" archetype, where '
                        '"persistent-state" describes it and is not part of the id'),
    },
    "EXTERNAL_EFFECT": {
        "anchor": "external_effect",
        "modifiers": ("money", "scheduled", "distributed", "multi_actor"),
        "demoters": ("sandbox", "dry run", "test mode", "modo prueba",
                     "simulado", "sin enviar"),
        "description": "acting on the outside world: sending, posting, calling or charging through a runtime dependency",
    },
    "BACKGROUND_JOB": {
        "anchor": "scheduled",
        "modifiers": ("distributed", "persistent", "external_effect"),
        "demoters": ("one-off", "one off", "una sola vez", "manualmente", "dry run"),
        "description": "work that runs unattended on a schedule, in a loop or from a queue",
    },
}

# Bridge from a trait to the closed N/A vocabulary of the done gate, by VALUE: this
# module never imports the done-gate module, and a gate checks every value is a
# member of its vocabulary. A later phase may justify NOT_APPLICABLE only from a
# trait judged ABSENT, never from UNJUDGED.
TRAIT_NA_REASON = {
    "persistent": "no-persistent-state",
    "multi_actor": "single-actor",
    "bulk": "no-bulk-operation",
    "destructive": "no-destructive-operation",
    "distributed": "not-distributed",
    "external_effect": "no-external-effect",
    "scheduled": "not-scheduled",
    "money": "no-money",
    "policy_layers": "single-policy-layer",
    "ui": "no-user-interface",
}

_INTENT_MAX_CHARS = 20_000
_INTENT_WINDOW = 60
_SPAN_MAX = 160
_EVIDENCE_MAX = 5

# Verb-object vocabulary for the `persistent` intent detector. English only in
# this slice; the bilingual, complete detector arrives with plan 02-02.
_PERSIST_VERBS = ("add", "adds", "adding", "added", "create", "creates", "creating",
                  "created", "save", "saves", "saving", "saved", "store", "stores",
                  "storing", "stored", "persist", "persists", "persisting",
                  "write", "writes", "writing", "update", "updates", "updating",
                  "updated", "delete", "deletes", "deleting", "deleted",
                  "migrate", "migrates", "migrating", "migrated",
                  # Spanish (matched on folded text, so accents are irrelevant)
                  "añade", "añadir", "agrega", "agregar", "crea", "crear", "guarda",
                  "guardar", "actualiza", "actualizar", "borra", "borrar", "elimina",
                  "eliminar", "migra", "migrar", "persiste", "almacena")
_PERSIST_OBJECTS = ("table", "tables", "migration", "migrations", "record", "records",
                    "row", "rows", "schema", "column", "columns", "data", "coins",
                    "tabla", "tablas", "migración", "registro", "registros", "fila",
                    "filas", "esquema", "columna", "datos", "monedas", "saldo",
                    "saldos", "inventario", "partida")


def reading(state, fact_state, evidence=(), reason=""):
    """One trait reading: state, how it is known, at most five evidence strings."""
    return {"state": state, "fact_state": fact_state,
            "evidence": [str(e) for e in list(evidence)[:_EVIDENCE_MAX]],
            "reason": reason}


def unjudged_reading(cause):
    """The reading of a trait nobody could judge. Every miss path calls this by its
    module-global name, so a drill that replaces it replaces it everywhere."""
    return reading(UNJUDGED, UNKNOWN, (), cause)


def _all_unjudged(cause):
    return {t: unjudged_reading(cause) for t in TRAITS}


def subject_root(root):
    """Canonical repository root for `root`, or None.

    Only an absolute, existing directory resolves. A relative or missing path gets
    no key at all: inventing one would file the reader's question under an
    identity no producer ever wrote. The subject root is a required argument; the
    current working directory is never consulted."""
    if not isinstance(root, (str, os.PathLike)):
        return None
    path = os.fspath(root)
    if not isinstance(path, str) or not path:
        return None
    if not os.path.isabs(path) or not os.path.isdir(path):
        return None
    return canonical_repo(os.path.abspath(path))


def default_state_dir():
    """Per-user state directory, computed per call so a temp HOME is honoured.
    Nothing is created here: the reader must not write anything."""
    return os.path.join(os.path.expanduser("~"), ".claude", "state", "tower")


def cache_path(root, state_dir=None):
    """`<state_dir>/traits_<repo_key>.json`, or None when the root is unresolvable."""
    sroot = subject_root(root)
    if sroot is None:
        return None
    return os.path.join(state_dir or default_state_dir(),
                        "traits_%s.json" % repo_key(sroot))


def _cache_info(state, path=None, produced_at=None, reason="", walk=None):
    return {"state": state, "path": path, "produced_at": produced_at,
            "reason": reason, "walk": walk}


def _valid_reading(r):
    return (isinstance(r, dict) and r.get("state") in TRAIT_STATES
            and r.get("fact_state") in FACT_STATES)


def _read_traits(root, state_dir):
    sroot = subject_root(root)
    if sroot is None:
        return {"cache": _cache_info(CACHE_UNRESOLVABLE, reason="unresolvable-root"),
                "traits": _all_unjudged("unresolvable-root")}
    path = cache_path(sroot, state_dir=state_dir)
    if not os.path.isfile(path):
        return {"cache": _cache_info(CACHE_MISSING, path=path, reason="no-cache"),
                "traits": _all_unjudged("no-cache")}

    def malformed(why):
        return {"cache": _cache_info(CACHE_MALFORMED, path=path, reason="cache-malformed: " + why),
                "traits": _all_unjudged("cache-malformed")}

    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return malformed("%s" % type(exc).__name__)
    if not isinstance(doc, dict):
        return malformed("not an object")
    if doc.get("schema") != SCHEMA:
        return malformed("schema")
    stored = doc.get("traits")
    if not isinstance(stored, dict) or set(stored) != set(TRAITS):
        return malformed("trait keys")
    if not all(_valid_reading(stored[t]) for t in TRAITS):
        return malformed("reading vocabulary")
    traits = {t: reading(stored[t]["state"], stored[t]["fact_state"],
                         stored[t].get("evidence") or (), str(stored[t].get("reason") or ""))
              for t in TRAITS}
    try:
        produced_at = float(doc.get("produced_at"))
    except (TypeError, ValueError):
        produced_at = None
    walk = doc.get("walk") if isinstance(doc.get("walk"), dict) else None
    return {"cache": _cache_info(CACHE_FRESH, path=path, produced_at=produced_at, walk=walk),
            "traits": traits}


def read_traits(root, *, state_dir=None):
    """What the prompt path sees: one file read, never a walk.

    Never raises and never returns fewer than ten traits. Freshness by
    fingerprint and age is added in plan 02-04, test first."""
    try:
        return _read_traits(root, state_dir)
    except Exception as exc:  # noqa: BLE001 -- a reader that raises drops the whole chain
        return {"cache": _cache_info(CACHE_MALFORMED,
                                     reason="cache-malformed: %s" % type(exc).__name__),
                "traits": _all_unjudged("cache-malformed")}


def _intent_hit(span, reason):
    return {"state": PRESENT, "fact_state": EXTRACTED, "span": span, "reason": reason}


def _intent_miss(reason):
    return {"state": UNJUDGED, "fact_state": UNKNOWN, "span": "", "reason": reason}


def _phrase_positions(text, phrases):
    out = []
    for p in phrases:
        for m in re.finditer(r"\b" + re.escape(p) + r"\b", text):
            out.append((m.start(), m.end()))
    return out


def _persistent_intent(prompt):
    """A verb acting on a state object, either order, within a short window.

    Structure, not bag-of-words: a lone noun such as `schema` matches nothing."""
    text = _fold(prompt)[:_INTENT_MAX_CHARS]
    verbs = _match(text, _PERSIST_VERBS)
    objects = _match(text, _PERSIST_OBJECTS)
    if not verbs or not objects:
        return _intent_miss("no-intent-match")
    best = None
    for vs, ve in _phrase_positions(text, verbs):
        for os_, oe in _phrase_positions(text, objects):
            if os_ >= ve:
                gap = os_ - ve
            elif vs >= oe:
                gap = vs - oe
            else:
                continue
            if gap <= _INTENT_WINDOW:
                key = (min(vs, os_), gap)
                if best is None or key < best[0]:
                    best = (key, text[min(vs, os_):max(ve, oe)])
    if best is None:
        return _intent_miss("no-intent-match")
    return _intent_hit(best[1][:_SPAN_MAX], "verb-object")


def intent_facts(prompt):
    """Intent readings over all ten traits. Intent never yields ABSENT: a prompt
    that does not mention a trait says nothing about the repository."""
    prompt = str(prompt or "")
    out = {t: _intent_miss("no-intent-detector") for t in TRAITS}
    out["persistent"] = _persistent_intent(prompt)
    return out


def ceiling(anchor_state, intent_hit, demoted):
    """The ONLY place an archetype strength is decided -> (strength, basis).

    This is where audit gap [G16] is enforced: a word must never be able to make
    an archetype REQUIRED. Rules, in this order:

      anchor PRESENT, intent, not demoted -> (REQUIRED,    structural+intent)
      anchor PRESENT, intent, demoted     -> (CONDITIONAL, structural+intent)
      anchor PRESENT, no intent           -> (CONDITIONAL, structural)   [R-1]
      anchor WEAK, intent                 -> (CONDITIONAL, structural+intent)
      anchor WEAK, no intent              -> (CONDITIONAL, structural)
      anchor ABSENT or UNJUDGED, intent   -> (CONDITIONAL, intent)       [D-06]
      anything else                       -> (NONE, none)

    REQUIRED needs structure that is PRESENT AND an intent fact AND no demoter. A
    WEAK anchor never reaches REQUIRED. Intent without a PRESENT anchor is at most
    CONDITIONAL, and the caller stamps its fact state EXTRACTED. A demoter lowers
    REQUIRED to CONDITIONAL and never produces NONE (D-03): the intent vocabulary
    is closed and fitted (GSDX-M04), so a miss must not let a naked verb escape.
    """
    intent_hit, demoted = bool(intent_hit), bool(demoted)
    if anchor_state == PRESENT:
        if intent_hit:
            if demoted:
                return Strength.CONDITIONAL, BASIS_BOTH
            return Strength.REQUIRED, BASIS_BOTH
        return Strength.CONDITIONAL, BASIS_STRUCTURAL
    if anchor_state == WEAK:
        return Strength.CONDITIONAL, (BASIS_BOTH if intent_hit else BASIS_STRUCTURAL)
    if anchor_state in (ABSENT, UNJUDGED) and intent_hit:
        return Strength.CONDITIONAL, BASIS_INTENT
    return Strength.NONE, BASIS_NONE


def _rule_reason(anchor, structural, intent, strength, basis, demoted_by):
    """Name the rule that fired, so a reader of the assessment can audit it."""
    a = "anchor %s %s" % (anchor, structural["state"])
    i = "intent %s" % ("PRESENT" if intent["state"] == PRESENT
                       else "%s (%s)" % (intent["state"], intent.get("reason") or "no intent"))
    if strength == Strength.NONE:
        return "%s (%s); %s" % (a, structural.get("reason") or "no evidence", i)
    if demoted_by:
        return "%s; %s; demoted by %s: REQUIRED lowered to CONDITIONAL" % (a, i, demoted_by)
    return "%s; %s; basis %s" % (a, i, basis)


def assess(traits, prompt, trait_intent=None):
    """One assessment per archetype id, in sorted order, every strength decided by
    `ceiling` (resolved by its module-global name at call time).

    `fact_state` is OBSERVED when the basis contains structural evidence, EXTRACTED
    for intent alone, UNKNOWN for none. `unjudged` lists the anchor when its
    structural reading is UNJUDGED, so a later phase can name the missing fact."""
    intents = trait_intent if trait_intent is not None else intent_facts(prompt)
    out = []
    for aid in sorted(ARCHETYPES):
        anchor = ARCHETYPES[aid]["anchor"]
        structural = traits.get(anchor) or unjudged_reading("cache-malformed")
        intent = intents.get(anchor) or _intent_miss("no-intent-detector")
        demoted_by = []
        strength, basis = ceiling(structural["state"], intent["state"] == PRESENT,
                                  bool(demoted_by))
        if basis == BASIS_INTENT:
            fact_state = EXTRACTED
        elif BASIS_STRUCTURAL in basis:
            fact_state = OBSERVED
        else:
            fact_state = UNKNOWN
        reason = _rule_reason(anchor, structural, intent, strength, basis, demoted_by)
        out.append({
            "id": aid,
            "strength": strength,
            "basis": basis,
            "fact_state": fact_state,
            "anchor": anchor,
            "anchor_state": structural["state"],
            "anchor_fact_state": structural["fact_state"],
            "intent_state": intent["state"],
            "intent_fact_state": intent["fact_state"],
            "intent_span": intent.get("span", ""),
            "demoted_by": [],
            "unjudged": [anchor] if structural["state"] == UNJUDGED else [],
            "reason": reason,
        })
    return out


def resolve(prompt, root, *, state_dir=None, families=None):
    """The capability subject for `prompt` in the repository at `root`.

    Reads the trait cache and the prompt; computes nothing walk-shaped. The result
    is JSON-serializable, and `families` is an independent output (D-02)."""
    prompt = str(prompt or "")
    sroot = subject_root(root)
    cached = read_traits(root, state_dir=state_dir)
    intents = intent_facts(prompt)
    return {
        "schema": SUBJECT_SCHEMA,
        "root": sroot,
        "repo_key": repo_key(sroot) if sroot else None,
        "cache": cached["cache"],
        "traits": cached["traits"],
        "trait_intent": intents,
        "archetypes": assess(cached["traits"], prompt, intents),
        "families": [{"id": fid, "hits": hits}
                     for fid, hits in classify_prompt(prompt, families)],
    }
