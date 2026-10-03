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
OBSERVED, and lifts an archetype to CONDITIONAL at most. REQUIRED needs
structural evidence AND intent: a verb acting on an object, never vocabulary alone
(D-04). `ceiling` is the single function that decides every strength (audit G16).
Six traits have a bilingual verb-object intent detector (`TRAIT_INTENT`); the rest
read UNJUDGED `no-intent-detector`. A demoter phrase lowers REQUIRED to
CONDITIONAL and never to NONE (D-03).

Fact states are the vocabulary of `modules.gsd_x.mission.obligation`, imported and
never re-spelled. Family classification (`modules.tower.families`) is reused for
its matcher and fold, and its result is reported as an independent output of
`resolve`: family and archetype answer different questions (D-02).
"""
from __future__ import annotations

import bisect
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

INTENT_MAX_CHARS = 20_000   # only this much of a prompt is ever read (V5: bounded input)
INTENT_WINDOW = 60          # a verb and its object are at most this many characters apart
_SPAN_MAX = 160
_EVIDENCE_MAX = 5

# Verb-object vocabulary for the intent detectors, one entry per trait that HAS a
# detector. THE LIST IS CLOSED AND FITTED: it is a lookup table wearing a rule's
# name (the GSDX-M04 debt recorded in modules.gsd_x.mission.obligation), so a
# wording outside it is missed. Structure-only CONDITIONAL (R-1, see `ceiling`)
# compensates: an intent miss cannot let a naked verb escape. Traits with no entry
# (multi_actor, distributed, policy_layers, ui) read `no-intent-detector`: a noun
# bag for them would reopen the D7 defect at trait level. Phrases are matched on
# folded text (accents irrelevant) and verbs carry their common inflections
# (English base, third person, past, gerund; Spanish infinitive, imperative tu and
# usted, first person plural, participle).
_PERSIST_VERBS = (
    "add", "adds", "adding", "added", "create", "creates", "creating", "created",
    "save", "saves", "saving", "saved", "store", "stores", "storing", "stored",
    "persist", "persists", "persisting", "persisted", "write", "writes", "writing",
    "wrote", "written", "update", "updates", "updating", "updated", "delete",
    "deletes", "deleting", "deleted", "migrate", "migrates", "migrating", "migrated",
    "añade", "añadir", "añada", "añadimos", "añadido", "agrega", "agregar", "agregue",
    "agregamos", "agregado", "crea", "crear", "cree", "creamos", "creado", "guarda",
    "guardar", "guarde", "guardamos", "guardado", "actualiza", "actualizar",
    "actualice", "actualizamos", "actualizado", "borra", "borrar", "borre", "borramos",
    "borrado", "elimina", "eliminar", "elimine", "eliminamos", "eliminado", "migra",
    "migrar", "migre", "migramos", "migrado", "persiste", "persistir", "persista",
    "persistimos", "persistido", "almacena", "almacenar", "almacene", "almacenamos",
    "almacenado")
_PERSIST_OBJECTS = (
    "table", "tables", "migration", "migrations", "record", "records", "row", "rows",
    "schema", "schemas", "column", "columns", "data", "coins", "balance", "balances",
    "inventory", "tabla", "tablas", "migración", "migraciones", "registro", "registros",
    "fila", "filas", "esquema", "esquemas", "columna", "columnas", "datos", "monedas",
    "saldo", "saldos", "inventario", "partida", "partidas")
_DESTRUCT_OBJECTS = _PERSIST_OBJECTS + (
    "user", "users", "account", "accounts", "file", "files", "session", "sessions",
    "usuario", "usuarios", "cuenta", "cuentas", "archivo", "archivos", "sesión",
    "sesiones")

TRAIT_INTENT = {
    "persistent": {"verbs": _PERSIST_VERBS, "objects": _PERSIST_OBJECTS},
    "external_effect": {
        "verbs": ("send", "sends", "sent", "sending", "post", "posts", "posted", "posting",
                  "call", "calls", "called", "calling", "publish", "publishes", "published",
                  "publishing", "notify", "notifies", "notified", "notifying", "email",
                  "emails", "emailed", "emailing", "charge", "charges", "charged", "charging",
                  "envía", "enviar", "envíe", "enviamos", "enviado", "manda", "mandar",
                  "mande", "mandamos", "mandado", "notifica", "notificar", "notifique",
                  "notificamos", "notificado", "publica", "publicar", "publique",
                  "publicamos", "publicado", "llama", "llamar", "llame", "llamamos", "llamado"),
        "objects": ("email", "emails", "mail", "mails", "webhook", "webhooks", "notification",
                    "notifications", "message", "messages", "sms", "request", "requests", "api",
                    "apis", "payment", "payments", "correo", "correos", "notificación",
                    "notificaciones", "mensaje", "mensajes", "aviso", "avisos", "petición",
                    "peticiones", "pago", "pagos")},
    "scheduled": {
        "verbs": ("schedule", "schedules", "scheduled", "scheduling", "run", "runs", "ran",
                  "running", "execute", "executes", "executed", "executing", "trigger",
                  "triggers", "triggered", "triggering", "programa", "programar", "programe",
                  "programamos", "programado", "ejecuta", "ejecutar", "ejecute", "ejecutamos",
                  "ejecutado", "lanza", "lanzar", "lance", "lanzamos", "lanzado"),
        "objects": ("job", "jobs", "task", "tasks", "worker", "workers", "cron", "cronjob",
                    "cronjobs", "backup", "backups", "sync", "cleanup", "report", "reports",
                    "digest", "tarea", "tareas", "trabajo", "trabajos", "proceso", "procesos",
                    "copia", "copias", "sincronización", "limpieza", "informe", "informes",
                    "resumen")},
    "destructive": {
        "verbs": ("delete", "deletes", "deleted", "deleting", "remove", "removes", "removed",
                  "removing", "drop", "drops", "dropped", "dropping", "purge", "purges",
                  "purged", "purging", "truncate", "truncates", "truncated", "truncating",
                  "wipe", "wipes", "wiped", "wiping", "erase", "erases", "erased", "erasing",
                  "borra", "borrar", "borre", "borramos", "borrado", "elimina", "eliminar",
                  "elimine", "eliminamos", "eliminado", "purga", "purgar", "purgue",
                  "purgamos", "purgado", "vacía", "vaciar", "vacíe", "vaciamos", "vaciado"),
        "objects": _DESTRUCT_OBJECTS},
    # Bulk "verbs" are quantifiers: the structure is a quantifier over a destroyable object.
    "bulk": {
        "verbs": ("all", "every", "bulk", "batch", "todos los", "todas las", "en lote",
                  "masivo", "masiva", "masivos", "masivas"),
        "objects": _DESTRUCT_OBJECTS},
    "money": {
        "verbs": ("charge", "charges", "charged", "charging", "bill", "bills", "billed",
                  "billing", "refund", "refunds", "refunded", "refunding", "pay", "pays",
                  "paid", "paying", "invoice", "invoices", "invoiced", "invoicing", "cobra",
                  "cobrar", "cobre", "cobramos", "cobrado", "factura", "facturar", "facture",
                  "facturamos", "facturado", "reembolsa", "reembolsar", "reembolse",
                  "reembolsamos", "reembolsado", "paga", "pagar", "pague", "pagamos", "pagado"),
        "objects": ("customer", "customers", "card", "cards", "payment", "payments",
                    "subscription", "subscriptions", "order", "orders", "invoice", "invoices",
                    "cliente", "clientes", "tarjeta", "tarjetas", "pago", "pagos",
                    "suscripción", "suscripciones", "pedido", "pedidos", "factura", "facturas")},
}


def _fold_unique(phrases):
    seen = []
    for p in phrases:
        f = _fold(p).strip()
        if f and f not in seen:
            seen.append(f)
    return tuple(seen)


# Folded once at import; the detectors only ever see these.
_FOLDED_INTENT = {t: {k: _fold_unique(v) for k, v in spec.items()}
                  for t, spec in TRAIT_INTENT.items()}


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


def _spans(folded_text, folded_phrase):
    """[(start, end)] of every occurrence of `folded_phrase` in `folded_text`.

    The positional companion of `applicability._hits`, which returns presence only
    and no offsets: this exists solely to measure the distance between a verb and
    its object. It builds the pattern exactly as `_hits` does (lowercased text and
    phrase, escaped phrase, word boundaries, no other quantifier), so it cannot
    disagree on presence; `V-ARCH-MATCHER-PARITY` pins that. It is called only on
    phrases that `families._match` (that is, `_hits`) has already confirmed."""
    p = str(folded_phrase).strip().lower()
    if not p:
        return []
    t = (folded_text or "").lower()
    return [(m.start(), m.end()) for m in re.finditer(r"\b" + re.escape(p) + r"\b", t)]


def _present_spans(text, phrases, memo):
    """Spans of the phrases of `phrases` that occur in `text`. Presence comes from
    `_match` (once per phrase list per prompt, memoised); offsets only after it."""
    present = memo.get(phrases)
    if present is None:
        present = memo[phrases] = tuple(_match(text, phrases))
    spans = []
    for phrase in present:
        spans.extend(_spans(text, phrase))
    return spans


def _best_pair(verb_spans, object_spans):
    """The earliest verb-object structure within `INTENT_WINDOW`, or None.

    A verb span and a DIFFERENT, non-overlapping object span, in either order: one
    word playing both roles (`email`) is not a structure. Near-linear: objects
    sorted by start and by end, one bisect per verb for the nearest object on each
    side, so a worst-case prompt cannot make this quadratic."""
    verbs = sorted(set(verb_spans))
    objects = sorted(set(object_spans))
    if not verbs or not objects:
        return None
    by_start = [s for s, _e in objects]
    by_end = sorted(objects, key=lambda se: (se[1], se[0]))
    ends = [e for _s, e in by_end]
    best = None
    for vs, ve in verbs:
        i = bisect.bisect_left(by_start, ve)               # nearest object starting at or after the verb
        if i < len(objects):
            os_, oe = objects[i]
            if os_ - ve <= INTENT_WINDOW:
                cand = ((min(vs, os_), os_ - ve), (min(vs, os_), max(ve, oe)))
                if best is None or cand[0] < best[0]:
                    best = cand
        j = bisect.bisect_right(ends, vs) - 1              # nearest object ending at or before the verb
        if j >= 0:
            os_, oe = by_end[j]
            if vs - oe <= INTENT_WINDOW:
                cand = ((min(vs, os_), vs - oe), (min(vs, os_), max(ve, oe)))
                if best is None or cand[0] < best[0]:
                    best = cand
    return best[1] if best else None


def intent_facts(prompt):
    """Intent readings over all ten traits. Intent never yields ABSENT: a prompt
    that does not mention a trait says nothing about the repository.

    Structure, not bag-of-words: a trait with a detector reads PRESENT (EXTRACTED,
    with the span) only for a verb acting on an object within `INTENT_WINDOW`
    characters; a lone noun such as `schema` matches nothing. A trait without a
    detector reads UNJUDGED `no-intent-detector`. Only the first `INTENT_MAX_CHARS`
    characters are read."""
    prompt = str(prompt or "")
    text = _fold(prompt[:INTENT_MAX_CHARS])
    out = {t: _intent_miss("no-intent-detector") for t in TRAITS}
    memo = {}
    for trait, spec in _FOLDED_INTENT.items():
        pair = _best_pair(_present_spans(text, spec["verbs"], memo),
                          _present_spans(text, spec["objects"], memo))
        if pair is None:
            out[trait] = _intent_miss("no-intent-match")
        else:
            out[trait] = _intent_hit(text[pair[0]:pair[1]][:_SPAN_MAX], "verb-object")
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
    prompt = str(prompt or "")
    intents = trait_intent if trait_intent is not None else intent_facts(prompt)
    out = []
    for aid in sorted(ARCHETYPES):
        anchor = ARCHETYPES[aid]["anchor"]
        structural = traits.get(anchor) or unjudged_reading("cache-malformed")
        intent = intents.get(anchor) or _intent_miss("no-intent-detector")
        # A demoter is a phrase in the prompt (either language) that lowers REQUIRED to
        # CONDITIONAL; it is reported next to the strength and never vetoes (D-03).
        demoted_by = _match(prompt[:INTENT_MAX_CHARS], ARCHETYPES[aid]["demoters"])
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
            "demoted_by": list(demoted_by),
            "unjudged": [anchor] if structural["state"] == UNJUDGED else [],
            "reason": reason,
        })
    return out


def active_archetypes(subject):
    """Ids of the archetypes whose strength is REQUIRED or CONDITIONAL, sorted.

    A family hit never makes an archetype active, and an archetype never implies a
    family: the two outputs of `resolve` are independent (D-02)."""
    return sorted(a["id"] for a in (subject or {}).get("archetypes", ())
                  if a.get("strength") in (Strength.REQUIRED, Strength.CONDITIONAL))


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
