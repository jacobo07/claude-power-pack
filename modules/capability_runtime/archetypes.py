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
import hashlib
import json
import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.gsd_x.mission.obligation import (  # noqa: E402
    EXTRACTED, FACT_STATES, OBSERVED, UNKNOWN)
from modules.repo_identity.identity import canonical_repo, repo_key  # noqa: E402
from modules.tower.families import (  # noqa: E402
    _SKIP_DIRS as _FAMILY_SKIP_DIRS, _fold, _match, classify_prompt)

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

# Root-level files whose size or mtime joins the cheap fingerprint. Lower-cased
# basenames: every manifest the producer parses plus the root markers it reads. The
# list is written out here because this module must never import `trait_scan`
# (a gate ties the two lists). NTFS moves a directory's mtime only when a direct
# child is created, deleted or renamed, never when a file is edited in place, so a
# manifest edit is invisible to a listing and each manifest is stat'ed on its own.
MANIFEST_NAMES = frozenset({
    "package.json", "requirements.txt", "pyproject.toml", "mix.exs", "pom.xml",
    "build.gradle", "build.gradle.kts", "cargo.toml", "go.mod",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    "dockerfile", "fly.toml", "vercel.json", "schema.prisma", "plugin.yml",
    "paper-plugin.yml"})

# At most this many evidence files are recorded for re-stat, and at most this many
# are re-stat'ed: the reader's cost is bounded whatever a document claims.
EVIDENCE_FILES_MAX = 32

# Age backstop (D-09). The fingerprint carries freshness; age only catches what the
# fingerprint cannot see (a module added below the root). Seven days, not the
# capsule's 24 h: a laptop that was off over a weekend would read STALE every Monday.
TRAIT_MAX_AGE_S = 7 * 24 * 3600

# A cache document larger than this is refused before it is parsed.
CACHE_MAX_BYTES = 256 * 1024

# Git Bash spells C:\Users\x as /c/Users/x (the form `family_scan.main_repo_of` converts).
_MSYS_PATH_RE = re.compile(r"^/([a-zA-Z])/(.*)$")

# Depth-2 fingerprints do not descend into trees the producer never walks.
_FP_SKIP_DIRS = frozenset(_FAMILY_SKIP_DIRS)

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
    current working directory is never consulted. On Windows the Git Bash form
    `/c/Users/x` is converted to `C:\\Users\\x` first, so one repository has one key
    however its caller spells it."""
    if not isinstance(root, (str, os.PathLike)):
        return None
    path = os.fspath(root)
    if not isinstance(path, str) or not path:
        return None
    if os.name == "nt":
        msys = _MSYS_PATH_RE.match(path)
        if msys:
            path = msys.group(1).upper() + ":\\" + msys.group(2).replace("/", "\\")
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


def _cache_info(state, path=None, produced_at=None, reason="", walk=None, last_known=None):
    """`last_known` is set only for a STALE cache: the readings the document held
    when it was produced, kept for display and never judged."""
    return {"state": state, "path": path, "produced_at": produced_at,
            "reason": reason, "walk": walk, "last_known": last_known}


def _valid_reading(r):
    return (isinstance(r, dict) and r.get("state") in TRAIT_STATES
            and r.get("fact_state") in FACT_STATES)


# -- freshness: a cheap fingerprint, never a walk -----------------------------------

def _utf8(text):
    return text.encode("utf-8", "surrogatepass")


def _list_dir(path):
    """Entries of one directory sorted by name, or None when it cannot be listed."""
    try:
        with os.scandir(path) as it:
            return sorted(it, key=lambda e: e.name)
    except OSError:
        return None


def _live_stat(entry):
    """A real `os.stat` of a directory entry. NOT `entry.stat()`: on Windows that returns the
    timestamps and size cached in the parent's directory listing, which NTFS refreshes
    lazily. Measured on this host: a directory created a moment earlier listed with an
    mtime 1 ms different from its own `os.stat` and kept it for seconds, so two
    fingerprints taken at different moments disagreed about an untouched repository."""
    return os.stat(entry.path)


def _entry_stat(entry):
    """`name|size|mtime_ns` of a directory entry, or `name|<error type>`."""
    try:
        st = _live_stat(entry)
    except OSError as exc:
        return "%s|%s" % (entry.name, type(exc).__name__)
    return "%s|%d|%d" % (entry.name, st.st_size, st.st_mtime_ns)


def _is_linked_dir(entry):
    try:
        if entry.is_symlink():
            return True
        is_junction = getattr(entry, "is_junction", None)
        return bool(is_junction()) if is_junction else False
    except OSError:
        return True


def fingerprint(root, depth=1):
    """16 hex characters naming the cheap observable state of `root`, by `os.scandir`
    only (never a walk, so it costs about a millisecond on a real repository).

    Depth 1 hashes the sorted names of the root's direct entries and the
    `name|size|mtime_ns` of every root entry whose lower-cased name is in
    `MANIFEST_NAMES` (read as a module global at call time). Depth 2 additionally
    hashes, for each root child directory the producer would walk, its mtime, its
    sorted entry names and the stats of its manifest-named entries. Depth 2 is what
    the producer's skip rule compares; the prompt path only ever pays depth 1. A
    root that cannot be listed fingerprints as `unreadable`."""
    top = _list_dir(root)
    if top is None:
        return "unreadable"
    h = hashlib.sha256()
    for entry in top:
        h.update(_utf8("n|%s\n" % entry.name))
        if entry.name.lower() in MANIFEST_NAMES:
            h.update(_utf8("m|%s\n" % _entry_stat(entry)))
    if depth >= 2:
        for entry in top:
            if entry.name in _FP_SKIP_DIRS or _is_linked_dir(entry):
                continue
            try:
                if not entry.is_dir(follow_symlinks=False):
                    continue
                mtime = _live_stat(entry).st_mtime_ns
            except OSError:
                continue
            kids = _list_dir(entry.path)
            h.update(_utf8("d|%s|%d\n" % (entry.name, mtime)))
            if kids is None:
                h.update(b"unreadable\n")
                continue
            for kid in kids:
                h.update(_utf8("c|%s\n" % kid.name))
                if kid.name.lower() in MANIFEST_NAMES:
                    h.update(_utf8("m|%s\n" % _entry_stat(kid)))
    return h.hexdigest()[:16]


def root_manifest_stats(root):
    """[{name, size, mtime_ns}] for the root's manifest-named files, sorted by name.
    Stored in the cache so a STALE reason can name which manifest moved."""
    out = []
    for entry in _list_dir(root) or ():
        if entry.name.lower() not in MANIFEST_NAMES:
            continue
        try:
            st = _live_stat(entry)
            if entry.is_dir():
                continue
        except OSError:
            continue
        out.append({"name": entry.name, "size": st.st_size, "mtime_ns": st.st_mtime_ns})
    return out


def _join_inside(root, rel):
    """`root` joined with the forward-slash relative path `rel`, or None when `rel` is
    empty, absolute, has a drive or a backslash, or climbs out with `..`."""
    if not isinstance(rel, str) or not rel or "\\" in rel or os.path.isabs(rel):
        return None
    parts = rel.split("/")
    if any(p in ("", "..") for p in parts) or ":" in parts[0]:
        return None
    return os.path.join(root, *parts)


def evidence_stats(root, rel_paths):
    """For at most `EVIDENCE_FILES_MAX` relative paths: `{path, size, mtime_ns}`, or
    `{path, missing: true}` when the file is gone, unreadable or outside `root`."""
    out = []
    for rel in list(rel_paths)[:EVIDENCE_FILES_MAX]:
        full = _join_inside(root, rel)
        try:
            st = os.stat(full) if full is not None else None
        except OSError:
            st = None
        if st is None:
            out.append({"path": rel, "missing": True})
        else:
            out.append({"path": rel, "size": st.st_size, "mtime_ns": st.st_mtime_ns})
    return out


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _valid_evidence_entry(sroot, e):
    if not isinstance(e, dict) or _join_inside(sroot, e.get("path")) is None:
        return False
    return e.get("missing") is True or (_int(e.get("size")) and _int(e.get("mtime_ns")))


def _moved_manifests(sroot, stored):
    """Names of the root manifests that differ between the stored list and now."""
    now = {m["name"]: m for m in root_manifest_stats(sroot)}
    old = {m["name"]: m for m in (stored or ()) if isinstance(m, dict) and "name" in m}
    return sorted(n for n in set(now) | set(old) if now.get(n) != old.get(n))


def _stale_reason(sroot, stored_fp):
    """Why the stored fingerprint no longer describes the repository, or ''."""
    if fingerprint(sroot, 1) != stored_fp["fp1"]:
        moved = _moved_manifests(sroot, stored_fp.get("root_manifests"))
        return "root listing or manifest changed since produced (%s)" % (
            ", ".join(moved) if moved else "directory listing")
    stored = stored_fp["evidence_files"]
    for old, new in zip(stored, evidence_stats(sroot, [e["path"] for e in stored])):
        if old != new:
            return "evidence file changed since produced: %s" % old["path"]
    return ""


def _read_traits(root, state_dir, now=None):
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
        with open(path, "rb") as fh:
            raw = fh.read(CACHE_MAX_BYTES + 1)       # bounded: an oversize file is never parsed
        if len(raw) > CACHE_MAX_BYTES:
            return malformed("larger than %d bytes" % CACHE_MAX_BYTES)
        doc = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        return malformed("%s" % type(exc).__name__)
    if not isinstance(doc, dict):
        return malformed("not an object")
    if doc.get("schema") != SCHEMA:
        return malformed("schema")
    if doc.get("repo_key") != repo_key(sroot):       # a document filed under another repository's name
        return malformed("repo_key")
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
        return malformed("produced_at")
    if not -1e18 < produced_at < 1e18:               # NaN and infinity fail this comparison
        return malformed("produced_at")
    walk = doc.get("walk") if isinstance(doc.get("walk"), dict) else None
    fp = doc.get("fingerprint")
    if not isinstance(fp, dict) or not isinstance(fp.get("fp1"), str):
        return malformed("fingerprint")
    evidence = fp.get("evidence_files")
    if (not isinstance(evidence, list) or len(evidence) > EVIDENCE_FILES_MAX
            or not all(_valid_evidence_entry(sroot, e) for e in evidence)):
        return malformed("evidence files")
    age = (time.time() if now is None else float(now)) - produced_at
    if age > TRAIT_MAX_AGE_S:
        why = "age %d s exceeds the %d s bound (TRAIT_MAX_AGE_S)" % (age, TRAIT_MAX_AGE_S)
    else:
        why = _stale_reason(sroot, fp)
    if why:
        return {"cache": _cache_info(CACHE_STALE, path=path, produced_at=produced_at,
                                     reason="stale: " + why, walk=walk, last_known=traits),
                "traits": _all_unjudged("stale")}
    return {"cache": _cache_info(CACHE_FRESH, path=path, produced_at=produced_at, walk=walk),
            "traits": traits}


def read_traits(root, *, state_dir=None, now=None):
    """What the prompt path sees: one validated file read, a depth-1 `scandir` and at
    most `EVIDENCE_FILES_MAX` stats, never a walk.

    Never raises and never returns fewer than ten traits. A cache is FRESH only while
    the root fingerprint and every recorded evidence file are unchanged; otherwise it
    reads STALE, every trait UNJUDGED `stale`, and the old readings survive only as
    `cache["last_known"]`, for display. Known blind spot: a module added below the root
    is neither an evidence file nor in the depth-1 fingerprint, so only the age backstop
    (`TRAIT_MAX_AGE_S`) and the producer's depth-2 check on its next run catch it.

    Every unusable cache (missing, oversize, unparsable, wrong schema, missing trait,
    unknown state, a `repo_key` that is not this repository's, no `produced_at`, no
    fingerprint block) reads all ten traits UNJUDGED with a named cause, never ABSENT."""
    try:
        return _read_traits(root, state_dir, now)
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


def subject_signature(subject):
    """16 hex characters naming what a subject IS, so a structural transition compiles to
    a different value and the same structure compiles to the same value on any host.

    Inside the signature: the state of each of the ten traits, the state of each of the
    ten intent readings, one `[id, strength, basis, sorted modifiers]` row per archetype
    assessment, and the sorted family ids. Deliberately outside it: the repository root,
    the cache path and its state, `produced_at`, every timestamp, every evidence string
    and every span or reason text. Those describe where and when the reading was taken,
    not what it concluded, and keeping them out is what makes two directories with equal
    structure sign equal. The digest is sha256 over canonical JSON (sorted keys, compact
    separators)."""
    subject = subject or {}
    body = {
        "traits": {t: (r or {}).get("state") for t, r in sorted((subject.get("traits") or {}).items())},
        "trait_intent": {t: (r or {}).get("state")
                         for t, r in sorted((subject.get("trait_intent") or {}).items())},
        "archetypes": [[a.get("id"), a.get("strength"), a.get("basis"),
                        sorted(a.get("modifiers") or [])]
                       for a in subject.get("archetypes") or ()],
        "families": sorted(str(f.get("id")) for f in subject.get("families") or ()),
    }
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def active_archetypes(subject):
    """Ids of the archetypes whose strength is REQUIRED or CONDITIONAL, sorted.

    A family hit never makes an archetype active, and an archetype never implies a
    family: the two outputs of `resolve` are independent (D-02)."""
    return sorted(a["id"] for a in (subject or {}).get("archetypes", ())
                  if a.get("strength") in (Strength.REQUIRED, Strength.CONDITIONAL))


def resolve(prompt, root, *, state_dir=None, now=None, families=None):
    """The capability subject for `prompt` in the repository at `root`.

    Reads the trait cache and the prompt; computes nothing walk-shaped. The result
    is JSON-serializable, and `families` is an independent output (D-02). `now`
    (epoch seconds) is passed to the cache reader's age check."""
    prompt = str(prompt or "")
    sroot = subject_root(root)
    cached = read_traits(root, state_dir=state_dir, now=now)
    intents = intent_facts(prompt)
    subject = {
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
    subject["signature"] = subject_signature(subject)
    return subject
