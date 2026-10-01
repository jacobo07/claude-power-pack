"""Risk facts: what a task statement ASKS to do that is costly to get wrong.

One interpretation of each risk fact, for every consumer (first consumer: spec_gate.classify_tier,
W2 of vault/plans/sdd-os-evolution-2026-10-01.md). Lives beside the autonomy gate because that
module already owns irreversibility and outward-facing effects; its own `classify` still uses its
older patterns (named debt, see the plan's W2 section).

A risk word is not a risk fact. Four things separate them:
  intent    fenced code, pasted-text markers and long quoted spans are reference material, not the
            request ("the log says DROP TABLE" asks for nothing)
  negation  a clause whose verb is negated before the match ("don't drop any tables") is dropped
  object    a verb only counts with the right target: deleting a table is destructive, deleting a
            helper function or offering a "delete" button is not
  target    production means a production target or an un-targeted deploy; staging/test/local is not

Deterministic, stdlib only, EN + ES. Accents are folded before matching. Each fact names the rule
that produced it, so a changed classification can be traced to one line of this file.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

DESTRUCTIVE_DATA = "destructive_data"
PUBLIC_CONTRACT = "public_contract"
AUTH_SECRETS = "auth_secrets"
PRODUCTION = "production"
IRREVERSIBLE_EXTERNAL = "irreversible_external"
RISK_DIMS = (DESTRUCTIVE_DATA, PUBLIC_CONTRACT, AUTH_SECRETS, PRODUCTION, IRREVERSIBLE_EXTERNAL)

FOUND, NONE_DETECTED, UNASSESSED = "FOUND", "NONE_DETECTED", "UNASSESSED"

# A quoted span this long is pasted reference text; shorter quotes are usually identifiers.
_QUOTE_MIN_WORDS = 4
# Below this many words outside the reference material, there is no separate request.
_MIN_INTENT_WORDS = 3
_WORD = re.compile(r"[a-z0-9]{2,}")
_FENCE = re.compile(r"(```|~~~).*?(\1|\Z)", re.S)
_PASTED = re.compile(r"\[pasted text #?\d+[^\]]*\]", re.I)
_QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”|«[^»]*»")
# One whitespace char each side, never `\s+...\s+`: that form backtracked quadratically across a
# long whitespace run (36 s on 40k spaces, on the per-prompt hook path -- code review W2, F4).
_CLAUSE = re.compile(r"[.;!?\n,]+|\s(?:but|pero|just|only|solo|then|luego)\s")
# "no" counts only as a word ("no-op" is not a negation -- review F3).
_NEGATOR = re.compile(r"\b(?:don'?t|do not|does not|doesn'?t|never|without|not|no(?!-)|nunca|sin|ni)\b")
# A negator scopes over the next few words, not the whole clause: "there are no tests yet so
# delete the old records table" asks for a delete (review F3).
_NEGATION_WINDOW_WORDS = 3   # covers "don't drop", "do not deploy", "no me estarias eliminando"

# A verb immediately followed by one of these names a UI element ("delete button"), not an act.
_UI_NOUN = r"(?!\s+(?:buttons?|options?|dialogs?|confirmations?|menus?|modals?|actions?|icons?|links?|" \
           r"boton(?:es)?|opcion(?:es)?|dialogos?)\b)"


def _rx(body: str) -> re.Pattern:
    return re.compile(body)


_DESTROY_VERB = _rx(r"\b(?:drop(?:s|ped|ping)?|delet(?:e|es|ed|ing)|truncat\w*|trunca(?:r)?|purg(?:e|es|ed|ing)|"
                    r"wip(?:e|es|ed|ing)|eras(?:e|es|ed|ing)|destroy\w*|remov(?:e|es|ed|ing)|"
                    r"borr(?:a|ar|e|o|ad[oa]s?|ando|al[oa]s?)|elimin\w*|vaci(?:a|ar))\b" + _UI_NOUN)
_DATA_OBJECT = _rx(r"\b(?:tables?|databases?|dbs?|schemas?|records?|rows?|columns?|collections?|buckets?|"
                   r"users?|accounts?|customers?|backups?|data|datasets?|tablas?|bases? de datos|"
                   r"registros?|filas?|columnas?|colecciones?|usuarios?|cuentas?|clientes?|datos|"
                   r"copias de seguridad)\b")

_PUBLIC_ADJ = _rx(r"\b(?:public|publico|publica|external(?:ly)?|third[- ]party|customer[- ]facing)\b")
_CONTRACT_NOUN = _rx(r"\b(?:apis?|sdks?|contracts?|interfaces?|endpoints?|schemas?|signatures?|packages?|"
                     r"librar(?:y|ies)|clients?|parametros?|parameters?)\b")
# Changing an existing surface. "add" is deliberately absent: a new endpoint breaks no consumer.
# Verb forms, never bare stems: `chang\w*` matched "changelog", `alter\w*` "alternative",
# `quit\w*` "quite", `notific\w*` "notificaciones", `configur\w*` "configuration".
_CHANGE = (r"chang(?:e|es|ed|ing)|updat(?:e|es|ed|ing)|modif(?:y|ies|ied|ying)|"
           r"replac(?:e|es|ed|ing)|remov(?:e|es|ed|ing)|delet(?:e|es|ed|ing)|"
           r"cambi(?:a|ar|alo|ala|ando)|actualiz(?:a|ar|alo|ala|ando)|modific(?:a|ar|alo|ala)|"
           r"quit(?:a|ar|alo|ala)|elimin(?:a|ar|alo|ala|ando)")
_CONTRACT_VERB = _rx(r"\b(?:" + _CHANGE + r"|renam(?:e|es|ed|ing)|deprecat\w*|break(?:s|ing)?|broke|"
                     r"alter(?:s|ed|ing)?|drop(?:s|ped|ping)?|renombr(?:a|ar|alo|ala|ando))\b")
_BREAKING = _rx(r"\b(?:breaking(?: change)?|backwards?[- ]incompatible|incompatible|"
                r"cambio incompatible|rompe (?:la )?compatibilidad)\b")

_AUTH_OBJECT = _rx(r"\b(?:secrets?|api[ -]?keys?|private keys?|ssh keys?|signing keys?|encryption keys?|"
                   r"credentials?|passwords?|access tokens?|auth tokens?|api tokens?|bearer tokens?|"
                   r"oauth|scopes?|permissions?|roles?|rbac|acls?|authentication|authorization|auth|login|"
                   r"2fa|mfa|sso|claves?|contrasenas?|credenciales|permisos)\b")
_AUTH_VERB = _rx(r"\b(?:" + _CHANGE + r"|rotat(?:e|es|ed|ing)|grant(?:s|ed|ing)?|revok(?:e|es|ed|ing)|"
                 r"add(?:s|ed|ing)?|expos(?:e|es|ed|ing)|stor(?:e|es|ed|ing)|leak(?:s|ed|ing)?|"
                 r"reset(?:s|ting)?|set|migrat(?:e|es|ed|ing)|disabl(?:e|es|ed|ing)|enabl(?:e|es|ed|ing)|"
                 r"configur(?:e|es|ed|ing|a|ar)|rota(?:r)?|anad(?:e|ir|elo|ela)|concede|revoca(?:r)?)\b")

_PROD_TARGET = _rx(r"\b(?:production|prod|produccion|live (?:server|site|environment)|en vivo|go[- ]live)\b")
_PROD_ACTION = _rx(r"\b(?:deploy\w*|releas\w*|ship\w*|roll ?out|push\w*|migrat\w*|run|runs|apply|applies|"
                   r"restart\w*|truncat\w*|drop(?:s|ped|ping)?|delet(?:e|es|ed|ing)|updat(?:e|es|ed|ing)|"
                   r"chang(?:e|es|ed|ing)|sub(?:e|ir|elo|ela|idlo)|"
                   # Spanish as VERB forms only: a bare stem matches nouns ("lanzamiento" = launch,
                   # "aplicacion", "ejecutivo", "borrador" = draft) -- measured on a read-only prod probe.
                   r"lanz(?:a|ar|alo|ala)|despleg(?:ar|ado|ando)|desplieg(?:a|alo|ue)|"
                   r"ejecut(?:a|ar|alo|ala)|aplic(?:a|ar|alo|ala)|publica(?:r|lo|la)?|publish\w*|"
                   r"borr(?:a|ar|alo|ala)|elimin(?:a|ar|alo|ala|ando))\b")
# `despleg\w*` matched "desplegables" (dropdowns) in a real UI prompt: verb forms only.
_DEPLOY = _rx(r"\b(?:deploy(?:s|ed|ing)?|despleg(?:ar|ado|ando)|desplieg(?:a|alo|ue|uen)|go[- ]live|"
              r"release to|ship to|roll ?out)\b")
_PUBLISH = _rx(r"\b(?:publish(?:es|ed|ing)?|publica(?:r|lo|la|mos)?(?=\s+(?:la|el|los|las|todo|toda|esto|"
               r"eso|lo|ya|un|una|mi|tu)\b))\b")
_NON_PROD = _rx(r"\b(?:staging|stage|test|testing|local|locally|localhost|dev|development|preview|sandbox|qa)\b")

_SEND_VERB = _rx(r"\b(?:send(?:s|ing)?|sent|notif(?:y|ies|ied)|broadcast\w*|charg(?:e|es|ed|ing)|"
                 r"refund\w*|bill(?:s|ed)?|pay(?:s|ing)?|transfer\w*|envi(?:a|ar|alo|ales|e)|"
                 r"mand(?:a|ar|alo|ales)|cobr(?:a|ar|ale|arle)|reembols(?:a|ar|ale)|"
                 r"notific(?:a|ar|alo|ales))\b" + _UI_NOUN)
_SEND_OBJECT = _rx(r"\b(?:emails?|newsletters?|messages?|sms|notifications?|subscribers?|customers?|users?|"
                   r"leads|cards?|payments?|invoices?|money|funds|correos?|mensajes?|suscriptores|"
                   r"clientes|usuarios|tarjetas?|pagos?|facturas?)\b")


@dataclass(frozen=True)
class RiskFact:
    dim: str
    rule: str
    match: str


@dataclass(frozen=True)
class RiskAssessment:
    state: str                  # FOUND | NONE_DETECTED | UNASSESSED (nothing left to read)
    facts: tuple = ()
    intent: str = ""

    @property
    def dims(self) -> tuple:
        return tuple(d for d in RISK_DIMS if any(f.dim == d for f in self.facts))


def fold(text: str) -> str:
    """Lowercase, accents removed (ñ -> n), curly apostrophes straightened, whitespace kept."""
    nfkd = unicodedata.normalize("NFKD", (text or "").replace("’", "'").replace("‘", "'"))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# A quote that IS an artifact name: `name.ext` (not "v2.0"), or a quote that starts with a path.
# A path somewhere inside a long quote is not enough -- logs carry paths too.
_ARTIFACT = re.compile(r"\w\.[A-Za-z][A-Za-z0-9]{0,4}\b|^.[A-Za-z]:\\|^./")
_ARTIFACT_MAX_WORDS = 12


def _quote_or_reference(m: re.Match) -> str:
    """Keep short quotes (identifiers) and quotes naming a file or path (the artifact the request
    acts on -- measured: a quoted "... Backlog System 1.md" was stripped and the task lost its
    tier signal). Drop long quoted spans: pasted output, logs, status lines."""
    q = m.group(0)
    if "\n" not in q and len(q.split()) <= _ARTIFACT_MAX_WORDS and _ARTIFACT.search(q):
        return q
    return q if len(q.split()) < _QUOTE_MIN_WORDS and "\n" not in q else " "


def intent_text(text: str) -> str:
    """The request with reference material removed: fences, pasted-text markers, and quoted spans
    of four words or more (short quotes are usually identifiers and stay)."""
    t = _FENCE.sub(" ", text or "")
    t = _PASTED.sub(" ", t)
    t = _QUOTED.sub(_quote_or_reference, t)
    return fold(t)


def _clauses(intent: str) -> list[str]:
    return [c.strip() for c in _CLAUSE.split(intent) if c and c.strip()]


def _live(clause: str, m: re.Match) -> bool:
    """False when a negator sits within the few words before the match."""
    window = " ".join(clause[:m.start()].split()[-_NEGATION_WINDOW_WORDS:])
    return not _NEGATOR.search(window)


def _first_live(rx: re.Pattern, clause: str) -> re.Match | None:
    for m in rx.finditer(clause):
        if _live(clause, m):
            return m
    return None


def _clause_facts(c: str) -> list[RiskFact]:
    out: list[RiskFact] = []
    v = _first_live(_DESTROY_VERB, c)
    o = _DATA_OBJECT.search(c)
    if v and o:
        out.append(RiskFact(DESTRUCTIVE_DATA, "destroy-verb+data-object", f"{v.group(0)} .. {o.group(0)}"))

    adj = _first_live(_PUBLIC_ADJ, c)
    noun = _CONTRACT_NOUN.search(c)
    if adj and noun and _first_live(_CONTRACT_VERB, c):
        out.append(RiskFact(PUBLIC_CONTRACT, "public-adj+contract-noun", f"{adj.group(0)} .. {noun.group(0)}"))
    else:
        b = _first_live(_BREAKING, c)
        if b:
            out.append(RiskFact(PUBLIC_CONTRACT, "breaking-change", b.group(0)))

    av = _first_live(_AUTH_VERB, c)
    ao = _AUTH_OBJECT.search(c)
    if av and ao:
        out.append(RiskFact(AUTH_SECRETS, "change-verb+auth-object", f"{av.group(0)} .. {ao.group(0)}"))

    tgt = _first_live(_PROD_TARGET, c)
    if tgt and _PROD_ACTION.search(c):
        out.append(RiskFact(PRODUCTION, "action+production-target", tgt.group(0)))
    elif not _NON_PROD.search(c):
        d = _first_live(_DEPLOY, c) or _first_live(_PUBLISH, c)
        if d:
            out.append(RiskFact(PRODUCTION, "untargeted-deploy-or-publish", d.group(0)))

    sv = _first_live(_SEND_VERB, c)
    so = _SEND_OBJECT.search(c)
    if sv and so:
        out.append(RiskFact(IRREVERSIBLE_EXTERNAL, "send-or-charge+recipient", f"{sv.group(0)} .. {so.group(0)}"))
    return out


def assess(text: str) -> RiskAssessment:
    intent = intent_text(text)
    if len(_WORD.findall(intent)) < _MIN_INTENT_WORDS:
        # Nothing but reference material: then the reference IS the request (a mission pasted
        # inside a fence or quotes). Measured 2026-10-01: 3 of 150 real prompts had this shape,
        # and stripping them silently downgraded T2/T3 missions to the T1 default.
        intent = fold(_PASTED.sub(" ", text or ""))
    if not intent.strip():
        return RiskAssessment(UNASSESSED, (), intent)
    facts: list[RiskFact] = []
    for c in _clauses(intent):
        for f in _clause_facts(c):
            if all(f.dim != g.dim for g in facts):
                facts.append(f)
    return RiskAssessment(FOUND if facts else NONE_DETECTED, tuple(facts), intent)


__all__ = ["RISK_DIMS", "RiskFact", "RiskAssessment", "assess", "intent_text", "fold",
           "FOUND", "NONE_DETECTED", "UNASSESSED", "DESTRUCTIVE_DATA", "PUBLIC_CONTRACT",
           "AUTH_SECRETS", "PRODUCTION", "IRREVERSIBLE_EXTERNAL"]
