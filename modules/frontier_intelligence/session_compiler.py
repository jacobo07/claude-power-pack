#!/usr/bin/env python3
"""session_compiler.py -- FIOS I-1 Session/Conversation Compiler (merges V-1 + V-2).

FD-00 is the session DOCTRINE (the eight-stage protocol as rules). This module is
the EXECUTABLE that walks it: it takes a session DECLARATION -- objective +
constraints + unknowns + candidate questions -- and compiles a concrete, ordered,
budgeted session plan (the "Session Zero" the frontier session launches from).

It COMPOSES, never re-implements:
  - FD-00 admission gate (`check_admission`) ranks each candidate question against
    the CO-03/CO-05 floor: ADMIT = frontier-worthy; ROUTE_CHEAPER/DECLINE/
    ANSWER_FROM_ASSET = drop or cheapen. No routing logic is re-implemented here.
  - FD-07 deposits ledger (`_load_deposits`) IS the floor for the repo -- what the
    stack already knows -- so a question whose answer is already deposited is at-floor.
  - The FD-02 leverage taxonomy (irreversible / system-generating / critique /
    dependence-reducing) is REFERENCED as the ORDER heuristic among admitted
    questions; it is not re-derived as a parallel compiler (FD-02 owns that doctrine).
  - The question_harvester (FIOS I-4) fills an EMPTY declaration: when the Owner
    declares an objective but no candidate_questions, preflight harvests them from
    the stack's own state (PR-HARVEST-BEFORE-FRONTIER-001) -- Session #1 launched
    with 0 candidates; that stage is never empty again.

Candidate questions may be plain strings or dicts ({text, source_ref,
expected_asset, depends_on}); the dict form preserves provenance through ranking
so the session can tag PM-03 findings with the question's fingerprint (FD-07
`question_ref` -- per-question ROI, read by CO-12, never a parallel metric).

The output is the 9-component plan the spec requires (+ the FD-04 portability
agenda), rendered to `vault/sessions/SESSION_ZERO_<iso>.md` (or a supplied dir):
  1 minimal verified context   2 ROI-ranked questions   3 optimal order
  4 recommended budget (5 categories)   5 next-session escalation criteria
  6 early-stop / saturation criteria   7 writeback plan   8 distillation plan
  9 Opus / Claude-Code transfer plan   10 portability agenda (FD-04 targets)

Fail-open ABSOLUTE: any error yields a best-effort plan (or an honest empty one),
never an exception -- a planning tool must not block the session it plans for.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# FD-02 leverage-axis signals -- REFERENCED to ORDER admitted questions, not to
# re-compile them. Whole-word / phrase matched (same discipline as fd_00_gate).
# Bilingual EN+ES: the D2A gate proved Spanish prompts under-detect on EN-only
# keywords (owned-fraction 34% -> 90% after aliasing) -- same fix applied here.
_IRREVERSIBLE_KW = ("architecture", "architect", "protocol", "data model", "schema",
                    "design", "irreversible", "commit", "standard", "foundation",
                    "arquitectura", "protocolo", "esquema", "estandar", "fundacion",
                    "irreversible", "disena", "diseno")
_SYSTEM_KW = ("always", "every", "reusable", "recipe", "policy", "invariant",
              "how should we", "general rule", "pattern", "framework",
              "siempre", "cada", "reutilizable", "receta", "politica",
              "invariante", "regla general", "patron")
_CRITIQUE_KW = ("what is wrong", "flaw", "fails", "critique", "adversarial",
                "under what", "attack", "break", "weakness", "edge case",
                "que falla", "fallo", "defecto", "critica", "romper",
                "debilidad", "caso borde", "bajo que")
_DEPENDENCE_KW = ("deterministic", "without a model", "without a frontier",
                  "cheaper", "reduce dependence", "checklist", "rule that",
                  "small model", "offline",
                  "determinista", "sin modelo", "mas barato",
                  "reducir dependencia", "modelo pequeno")
# Default 5-category budget split (FIOS-OPS-2 folded in as a field). Sums to 1.0;
# emergency is the reserve the session redistributes from as it learns.
_BUDGET_SPLIT = {
    "discovery": 0.30, "architecture": 0.25, "critique": 0.20,
    "validation": 0.15, "emergency": 0.10,
}
# Formal session states (FIOS-COS-2 folded in). Binary entry criteria -- never
# advance without the prior state's exit condition met (FD-00 "done is a recorded
# transition"). Kept as a table so the plan renders it, not as a live FSM engine.
_STATE_MACHINE = [
    ("Discovery", "objective + unknowns declared; floor loaded"),
    ("Exploration", "highest-leverage admitted question asked"),
    ("Architecture", "an above-floor NEW/STRONGER delta captured"),
    ("Critique", "the delta adversarially stressed (its flaw sought)"),
    ("Validation", "the delta's portability target declared"),
    ("Compression", "the delta reduced to its operational contract"),
    ("Writeback", "the delta written to its exact stack location"),
    ("Done", "all deposits closed OR an honest DISCARD recorded"),
]
# A minimal-context budget guard: the plan's context section must stay small so the
# frontier session starts lean (the spec's <2000-token contract). ~4 chars/token
# is the rough industry proxy; bounded conservatively.
_CTX_TOKEN_BUDGET = 2000
_CTX_CHAR_BUDGET = _CTX_TOKEN_BUDGET * 4
# Candidate-vs-candidate overlap band: at/above this Jaccard two candidates ask
# the same thing; the higher-leverage one survives, the drop is LOGGED (never
# silent). The gate dedups vs the FLOOR; this dedups the portfolio itself.
_DEDUP_JACCARD = 0.60
_AGENDA_CAP = 10               # portability-agenda rows rendered (bounded)
_QUESTION_COL = 80             # question text width in the section-2 table
_STOP = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
         "this", "that", "with", "how", "what", "we", "our", "us", "do", "does"}

# Single fingerprint algorithm ecosystem-wide -- the harvester owns it. Direct
# same-package import: a divergence-prone fallback mirror was deleted here (a
# copy that can only ever drift protects nothing a hard import failure would
# not surface louder).
from modules.frontier_intelligence.question_harvester import question_fingerprint  # noqa: E402


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _iso_stamp(dt: datetime) -> str:
    """Colon-free ISO stamp usable in a Windows filename."""
    return dt.strftime("%Y-%m-%dT%H%M%SZ")


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{3,}", (s or "").lower()) if w not in _STOP}


def _has(text: str, phrases) -> bool:
    t = (text or "").lower()
    for p in phrases:
        if " " in p:
            if p in t:
                return True
        elif re.search(rf"\b{re.escape(p)}\b", t):
            return True
    return False


@dataclass
class SessionDeclaration:
    """The Owner's session intent -- the compiler's input."""
    objective: str = ""
    constraints: list = field(default_factory=list)
    unknowns: list = field(default_factory=list)
    candidate_questions: list = field(default_factory=list)   # str | dict entries
    repo: str = ""
    token_budget: int = 0          # 0 = unspecified -> percentages only, no absolute
    horizon_months: int = 12       # for the next-session escalation framing


@dataclass
class RankedQuestion:
    text: str
    verdict: str                   # ADMIT | ROUTE_CHEAPER | DECLINE | ANSWER_FROM_ASSET | DEFER
    frontier_worthy: bool
    leverage: float                # [0,1] order key among admitted questions
    axes: dict = field(default_factory=dict)
    reason: str = ""
    source_ref: str = ""           # provenance (harvester source or Owner-declared)
    expected_asset: str = ""       # the permanent form the answer must take
    depends_on: str = ""           # fingerprint of a prerequisite question
    fingerprint: str = ""          # tag for PM-03 findings -> FD-07 question_ref


@dataclass
class SessionPlan:
    stamp: str
    repo: str
    objective: str
    context: str                   # component 1 (bounded)
    context_tokens_est: int
    questions: list                # component 2/3 (RankedQuestion, ordered)
    budget: dict                   # component 4
    escalation: list               # component 5
    stopping: list                 # component 6
    writeback_plan: list           # component 7
    distillation_plan: list        # component 8
    transfer_plan: list            # component 9
    floor_size: int                # deposits already on the floor
    note: str = ""
    dropped: list = field(default_factory=list)        # dedup log (never silent)
    follow_ups: list = field(default_factory=list)     # dependency-deferred questions
    portability_agenda: list = field(default_factory=list)  # component 10 (FD-04)


# --------------------------------------------------------------------------- #
# Floor -- what the stack already knows for this repo (FD-07 deposits ledger).
# --------------------------------------------------------------------------- #
def _floor_claims(repo: str, *, state_dir=None) -> list:
    """The repo's prior deposits = the floor a question is measured against.
    Fail-open -> []. Reads the FD-07 ledger; never re-implements it."""
    try:
        from modules.fable_distillation.fd_07_flywheel import _load_deposits
        return _load_deposits(repo, state_dir)
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Leverage ordering (FD-02 axes REFERENCED, not re-compiled).
# --------------------------------------------------------------------------- #
def _leverage(question: str) -> tuple[float, dict]:
    """Score a question on the four FD-02 leverage axes and sum. Used only to
    ORDER the questions FD-00 already admitted -- the admission gate decides
    worthiness, this decides sequence. Deterministic, no model."""
    axes = {
        "irreversible": 1.0 if _has(question, _IRREVERSIBLE_KW) else 0.0,
        "system_generating": 1.0 if _has(question, _SYSTEM_KW) else 0.0,
        "critique": 1.0 if _has(question, _CRITIQUE_KW) else 0.0,
        "dependence_reducing": 1.0 if _has(question, _DEPENDENCE_KW) else 0.0,
    }
    score = sum(axes.values()) / len(axes)
    return (round(score, 3), axes)


def _qnorm(q) -> dict | None:
    """Normalize a candidate (str or dict) to {text, source_ref, expected_asset,
    depends_on}. Fail-open -> None (a bad candidate is skipped, never fatal)."""
    try:
        if isinstance(q, dict):
            text = str(q.get("text", "") or "").strip()
            if not text:
                return None
            return {"text": text,
                    "source_ref": str(q.get("source_ref", "") or ""),
                    "expected_asset": str(q.get("expected_asset", "") or ""),
                    "depends_on": str(q.get("depends_on", "") or "")}
        text = str(q or "").strip()
        return {"text": text, "source_ref": "", "expected_asset": "",
                "depends_on": ""} if text else None
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def rank_questions(candidates, *, kb_dir=None, route_fn=None,
                   state_dir=None) -> list:
    """Rank candidate questions: FD-00 admission decides frontier-worthiness, the
    FD-02 leverage axes decide order among the worthy ones. A question whose answer
    the floor already covers is DECLINE'd by the gate and drops. Candidates may be
    strings or provenance dicts (harvester output). Fail-open."""
    out = []
    try:
        from modules.fable_distillation.fd_00_gate import check_admission
    except Exception:  # noqa: BLE001 -- fail-open: no gate -> everything is a DEFER
        check_admission = None  # type: ignore
    for cand in candidates or []:
        c = _qnorm(cand)
        if not c:
            continue
        q = c["text"]
        meta = {"source_ref": c["source_ref"], "expected_asset": c["expected_asset"],
                "depends_on": c["depends_on"],
                "fingerprint": question_fingerprint(q)}
        if check_admission is None:
            lev, axes = _leverage(q)
            out.append(RankedQuestion(q, "DEFER", False, lev, axes,
                                      "admission gate unavailable", **meta))
            continue
        try:
            dec = check_admission(q, kb_dir=kb_dir, route_fn=route_fn,
                                  state_dir=state_dir)
            lev, axes = _leverage(q)
            out.append(RankedQuestion(
                text=q, verdict=dec.verdict, frontier_worthy=(dec.action == "admit"),
                leverage=lev, axes=axes, reason=dec.reason, **meta))
        except Exception as e:  # noqa: BLE001 -- one bad question never breaks the plan
            lev, axes = _leverage(q)
            out.append(RankedQuestion(q, "DEFER", False, lev, axes, f"error: {e}",
                                      **meta))
    # Frontier-worthy first, then by leverage desc, then stable by original text.
    out.sort(key=lambda r: (not r.frontier_worthy, -r.leverage))
    return out


def dedupe_ranked(ranked) -> tuple[list, list]:
    """Candidate-vs-candidate dedup (the FD-00 gate dedups vs the FLOOR; this
    dedups the portfolio itself). Greedy over the ranked order so the
    higher-priority phrasing survives. Returns (kept, dropped_log); the drop is
    LOGGED, never silent (no-silent-caps doctrine). Fail-open -> (ranked, [])."""
    try:
        kept, dropped, kept_toks = [], [], []
        for q in ranked or []:
            toks = _tokens(q.text)
            dup_of = None
            for i, kt in enumerate(kept_toks):
                if not toks or not kt:
                    continue
                j = len(toks & kt) / (len(toks | kt) or 1)
                if j >= _DEDUP_JACCARD:
                    dup_of = kept[i]
                    break
            if dup_of is not None:
                dropped.append({"text": q.text, "fingerprint": q.fingerprint,
                                "dup_of": dup_of.fingerprint})
                continue
            kept.append(q)
            kept_toks.append(toks)
        return (kept, dropped)
    except Exception:  # noqa: BLE001 -- fail-open
        return (list(ranked or []), [])


def split_dependencies(ranked) -> tuple[list, list]:
    """Honor `depends_on`: a question whose prerequisite is also in the portfolio
    is a FOLLOW-UP (asked after its prerequisite's answer lands), not a lead
    question. A depends_on pointing outside the portfolio stands alone.
    Fail-open -> (ranked, [])."""
    try:
        fps = {q.fingerprint for q in ranked or []}
        main, follow = [], []
        for q in ranked or []:
            if q.depends_on and q.depends_on in fps and q.depends_on != q.fingerprint:
                follow.append(q)
            else:
                main.append(q)
        return (main, follow)
    except Exception:  # noqa: BLE001 -- fail-open
        return (list(ranked or []), [])


# --------------------------------------------------------------------------- #
# Budget (FIOS-OPS-2 folded in as a field).
# --------------------------------------------------------------------------- #
def _budget(token_budget: int) -> dict:
    """The 5-category R&D budget. Percentages always; absolute token allocations
    only when a total was declared. Emergency is the redistribution reserve."""
    out = {}
    for cat, pct in _BUDGET_SPLIT.items():
        row = {"pct": pct}
        if token_budget and token_budget > 0:
            row["tokens"] = int(round(token_budget * pct))
        out[cat] = row
    return out


# --------------------------------------------------------------------------- #
# Compile.
# --------------------------------------------------------------------------- #
def _bounded_context(decl: SessionDeclaration, floor: list) -> tuple[str, int]:
    """Component 1: the minimal verified context, held under the <2000-token
    contract. Names the objective, the declared unknowns, and a COUNT of what the
    floor already covers (never inlines floor bodies -- that would blow the budget)."""
    lines = [f"Objetivo: {decl.objective.strip() or '(sin declarar)'}"]
    if decl.constraints:
        lines.append("Constraints: " + "; ".join(str(c) for c in decl.constraints[:8]))
    if decl.unknowns:
        lines.append("Unknowns declarados: " + "; ".join(str(u) for u in decl.unknowns[:8]))
    lines.append(f"Floor (ya conocido por el repo): {len(floor)} deposito(s) previos "
                 "-- no re-preguntar lo cubierto.")
    text = "\n".join(lines)
    if len(text) > _CTX_CHAR_BUDGET:                 # honest truncation, never silent
        text = text[:_CTX_CHAR_BUDGET].rsplit("\n", 1)[0] + "\n[...contexto truncado al contrato <2000 tok]"
    return (text, len(text) // 4)


def _proven_floor(repo: str, state_dir=None) -> frozenset:
    """FD-04 join surface (fail-open -> empty: behave as pre-FD-04)."""
    try:
        from modules.fable_distillation.fd_04_prover import proven_fingerprints
        return frozenset(proven_fingerprints(repo, state_dir))
    except Exception:  # noqa: BLE001
        return frozenset()


def _portability_agenda(floor: list, proven: frozenset = frozenset()) -> list:
    """Component 10: the FD-04 validation agenda -- every unproven deposit on the
    floor is a downgrade-test target for THIS session (the prior session's
    frontier-only deltas become the next session's proof work by construction).
    A deposit the FD-04 prover has PROVEN leaves the agenda -- the shrink is the
    measurable yield signal."""
    agenda = []
    for d in floor or []:
        try:
            if d.get("portability_proven") or d.get("fingerprint") in proven:
                continue
            agenda.append({
                "fingerprint": d.get("fingerprint", "?"),
                "portability_target": d.get("portability_target", "?"),
                "destination": d.get("destination", "?"),
                "claim": re.sub(r"\s+", " ", str(d.get("claim", "")))[:_QUESTION_COL]})
        except Exception:  # noqa: BLE001 -- one bad row never breaks the agenda
            continue
    return agenda[:_AGENDA_CAP]


def compile_session(decl: SessionDeclaration, *, kb_dir=None, route_fn=None,
                    state_dir=None, now: datetime | None = None) -> SessionPlan:
    """Compile a declaration into the 9-component session plan (+ the FD-04
    portability agenda). Pure (no file write) -- render_plan() and write_plan()
    handle materialization. Fail-open."""
    try:
        floor = _floor_claims(decl.repo, state_dir=state_dir)
        ctx, ctx_tok = _bounded_context(decl, floor)
        ranked = rank_questions(decl.candidate_questions, kb_dir=kb_dir,
                                route_fn=route_fn, state_dir=state_dir)
        deduped, dropped = dedupe_ranked(ranked)
        questions, follow_ups = split_dependencies(deduped)
        worthy = [q for q in questions if q.frontier_worthy]
        # Component 6: early-stop / saturation criteria (S-SATURATION folded in).
        stopping = [
            "PARAR si las preguntas restantes son todas DECLINE/ROUTE_CHEAPER "
            "(la respuesta ya esta en el floor) -- la sesion esta saturada.",
            "PARAR si dos respuestas consecutivas repiten el mismo fingerprint "
            "de delta sin mover la metrica CO-12 (spin degenerado, FD-07 II.2).",
            "PARAR si el presupuesto 'discovery' se agota sin un delta NEW -- "
            "el dominio esta at-floor; cambiar de tema o cerrar.",
        ]
        # Component 5: next-session escalation criteria (FIOS-INT-2 folded in).
        escalation = [
            "Sesion siguiente = validar los deltas 'frontier-only' de esta "
            "(probar portabilidad a mid/small/deterministic, FD-04).",
            "Escalar a una campana multi-sesion solo si quedan >=3 preguntas "
            "frontier-worthy sin responder tras agotar el presupuesto.",
            f"Horizonte de compounding declarado: {decl.horizon_months} meses "
            "(dD/dt debe ser negativo, no plano).",
        ]
        # Component 7: writeback plan.
        writeback_plan = [
            "Al cierre: el Stop hook FD-07 (PP_FRONTIER_SESSION=1) drena el bus "
            "PM-03 y deposita cada delta clasificado en el ledger idempotente.",
            "Cada finding PM-03 debe llevar el `question_ref` (columna ref de la "
            "seccion 2) para que el deposito enlace con la pregunta que lo pago.",
            "Reglas/traps -> candidato UKDL (Owner promueve); recetas -> CO-05 "
            "(solo verified+recurrent); nada se auto-muta.",
            "Emitir las senales CO-12 (fd_frontier_call_admitted, fd_delta_deposited).",
        ]
        # Component 8: distillation plan (what becomes what).
        distillation_plan = [
            "Delta arquitectonico -> dataset Part / Process Rule.",
            "Delta-regla ('nunca/siempre') -> Hard Rule (UKDL candidato).",
            "Delta-receta determinista -> asset CO-05 (rung-1) -> retira la clase "
            "del bill frontier.",
            "Delta-critica -> benchmark / gate.",
        ]
        # Component 9: transfer plan (Opus / Claude Code).
        transfer_plan = [
            "Todo delta con target de portabilidad mid-model debe re-ejecutarse en "
            "Opus/Sonnet antes de sellar (baja la dependencia frontier).",
            "Los deltas deterministas se transfieren a Claude Code como recetas/"
            "checklists ejecutables sin modelo.",
            "Un delta que solo funciona con el modelo frontier NO esta destilado: "
            "queda como hipotesis hasta que FD-04 pruebe el downgrade.",
        ]
        note = (f"{len(worthy)} pregunta(s) frontier-worthy de "
                f"{len(ranked)} candidata(s)")
        if dropped:
            note += f", {len(dropped)} descartada(s) por dedup"
        if follow_ups:
            note += f", {len(follow_ups)} follow-up(s) dependiente(s)"
        return SessionPlan(
            stamp=_iso_stamp(_now(now)), repo=decl.repo or "(repo sin declarar)",
            objective=decl.objective, context=ctx, context_tokens_est=ctx_tok,
            questions=questions, budget=_budget(decl.token_budget),
            escalation=escalation, stopping=stopping,
            writeback_plan=writeback_plan, distillation_plan=distillation_plan,
            transfer_plan=transfer_plan, floor_size=len(floor), note=note,
            dropped=dropped, follow_ups=follow_ups,
            portability_agenda=_portability_agenda(
                floor, _proven_floor(decl.repo, state_dir)))
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE
        return SessionPlan(
            stamp=_iso_stamp(_now(now)), repo=str(decl.repo), objective=decl.objective,
            context="(error al compilar -- fail-open)", context_tokens_est=0,
            questions=[], budget=_budget(decl.token_budget), escalation=[],
            stopping=[], writeback_plan=[], distillation_plan=[], transfer_plan=[],
            floor_size=0, note=f"compile error (fail-open): {e}")


# --------------------------------------------------------------------------- #
# Render + write.
# --------------------------------------------------------------------------- #
def _qcell(text: str) -> str:
    return text[:_QUESTION_COL].replace("|", "/")


def render_plan(plan: SessionPlan) -> str:
    """Render the plan as the SESSION_ZERO markdown (the 9+1 components)."""
    L = [f"# SESSION ZERO -- {plan.stamp}", "",
         f"> Repo: `{plan.repo}`  ·  Floor: {plan.floor_size} deposito(s)  ·  {plan.note}",
         "> Generado por FIOS session_compiler (FD-00 gate + FD-07 floor + FD-02 axes"
         " + question_harvester).",
         "> Ley PR-FRONTIER-AS-RD-001: cada token frontier es capital de I+D.", ""]
    L += ["## 1. Contexto minimo verificado (<2000 tok)",
          f"*(estimado ~{plan.context_tokens_est} tok)*", "", "```",
          plan.context, "```", ""]
    L += ["## 2. Preguntas priorizadas por ROI  ·  ## 3. Orden optimo", ""]
    if plan.questions:
        L.append("| # | worthy | leverage | verdict | asset esperado | ref | fuente | pregunta |")
        L.append("|---|---|---|---|---|---|---|---|")
        for i, q in enumerate(plan.questions, 1):
            mark = "SI" if q.frontier_worthy else "no"
            L.append(f"| {i} | {mark} | {q.leverage:.2f} | {q.verdict} | "
                     f"{q.expected_asset or '-'} | `{q.fingerprint}` | "
                     f"{_qcell(q.source_ref) or 'owner'} | {_qcell(q.text)} |")
        L.append("")
        L.append("Cada finding PM-03 de la sesion debe llevar `question_ref` = la "
                 "columna `ref` de su pregunta (FD-07 lo deposita con provenance).")
    else:
        L.append("*(sin preguntas candidatas -- declara `candidate_questions` o "
                 "ejecuta el question_harvester)*")
    L.append("")
    if plan.dropped:
        L.append(f"**Dedup ({len(plan.dropped)} descartada(s), log honesto):**")
        L += [f"- `{d.get('fingerprint','?')}` dup-of `{d.get('dup_of','?')}`: "
              f"{_qcell(str(d.get('text','')))}" for d in plan.dropped]
        L.append("")
    if plan.follow_ups:
        L.append(f"**Follow-ups dependientes ({len(plan.follow_ups)}) -- preguntar "
                 "tras la respuesta de su prerequisito:**")
        L += [f"- `{q.fingerprint}` (tras `{q.depends_on}`): {_qcell(q.text)}"
              for q in plan.follow_ups]
        L.append("")
    L += ["## 4. Presupuesto recomendado (5 categorias)", "",
          "| categoria | % | tokens |", "|---|---|---|"]
    for cat, row in plan.budget.items():
        L.append(f"| {cat} | {int(row['pct']*100)}% | {row.get('tokens', '-')} |")
    L.append("")
    for title, items in (("5. Criterios de escalado a siguiente sesion", plan.escalation),
                         ("6. Criterios de parada anticipada (saturacion)", plan.stopping),
                         ("7. Plan de writeback al finalizar", plan.writeback_plan),
                         ("8. Plan de destilacion (que -> que)", plan.distillation_plan),
                         ("9. Plan de transferencia a Opus / Claude Code", plan.transfer_plan)):
        L.append(f"## {title}")
        L += [f"- {it}" for it in items] or ["- (n/a)"]
        L.append("")
    L.append("## 10. Agenda de portabilidad (FD-04 -- deltas del floor sin probar)")
    if plan.portability_agenda:
        L.append("| deposito | destino | target | claim |")
        L.append("|---|---|---|---|")
        for a in plan.portability_agenda:
            L.append(f"| `{a['fingerprint']}` | {a['destination']} | "
                     f"{a['portability_target']} | {_qcell(a['claim'])} |")
        L.append("")
        L.append("Probar el downgrade de cada fila (FD-04): un delta sin prueba de "
                 "portabilidad sigue siendo hipotesis, no capital.")
    else:
        L.append("*(sin deltas pendientes de portabilidad en el floor)*")
    L.append("")
    L += ["## Maquina de estados de la sesion (binaria, no avanzar sin cerrar la previa)",
          "", "| estado | criterio de entrada |", "|---|---|"]
    for st, crit in _STATE_MACHINE:
        L.append(f"| {st} | {crit} |")
    L.append("")
    return "\n".join(L)


def write_plan(plan: SessionPlan, *, out_dir=None) -> Path | None:
    """Write the rendered plan to vault/sessions/SESSION_ZERO_<stamp>.md (or a
    supplied dir). Fail-open -> None on any I/O error."""
    try:
        base = Path(out_dir) if out_dir else (_PP_ROOT / "vault" / "sessions")
        base.mkdir(parents=True, exist_ok=True)
        p = base / f"SESSION_ZERO_{plan.stamp}.md"
        p.write_text(render_plan(plan), encoding="utf-8")
        return p
    except OSError:
        return None


def _decl_from_obj(data: dict) -> SessionDeclaration:
    return SessionDeclaration(
        objective=str(data.get("objective", "")),
        constraints=list(data.get("constraints", []) or []),
        unknowns=list(data.get("unknowns", []) or []),
        candidate_questions=list(data.get("candidate_questions", []) or []),
        repo=str(data.get("repo", "") or os.getcwd()),
        token_budget=int(data.get("token_budget", 0) or 0),
        horizon_months=int(data.get("horizon_months", 12) or 12))


def _decl_from_env_or_file(repo: str, env=None) -> SessionDeclaration | None:
    """Resolve a session declaration from a repo-local `.pp_frontier.json` (a full
    declaration) or the `PP_SESSION_OBJECTIVE` env (+ optional `PP_SESSION_QUESTIONS`
    / `PP_SESSION_BUDGET`). Returns None when neither exists -> the preflight stays
    silent: a plan with no declared objective is boilerplate, not a plan."""
    env = env if env is not None else os.environ
    try:
        f = Path(repo) / ".pp_frontier.json"
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8-sig") or "{}")
            data.setdefault("repo", repo)
            return _decl_from_obj(data)
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    obj = str(env.get("PP_SESSION_OBJECTIVE", "") or "").strip()
    if not obj:
        return None
    qs = [q.strip() for q in re.split(r"[;\n]", str(env.get("PP_SESSION_QUESTIONS", "") or ""))
          if q.strip()]
    try:
        budget = int(env.get("PP_SESSION_BUDGET", "0") or 0)
    except (TypeError, ValueError):
        budget = 0
    return SessionDeclaration(objective=obj, candidate_questions=qs, repo=repo,
                              token_budget=budget)


def _auto_harvest(repo: str) -> list:
    """PR-HARVEST-BEFORE-FRONTIER-001: an empty portfolio is filled from the
    stack's own state before launch. Fail-open -> [] (never blocks the launch)."""
    try:
        from modules.frontier_intelligence.question_harvester import (
            harvest, as_declaration_questions)
        return as_declaration_questions(harvest(repo))
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def preflight(repo: str, *, out_dir=None, env=None, now: datetime | None = None):
    """kclaude frontier preflight. If the Owner declared an objective, compile the
    SESSION_ZERO and return a 3-line ASCII summary (kclaude prints it); no
    declaration -> None (silent). An objective WITHOUT candidate questions
    auto-harvests them (disable with PP_SESSION_NO_HARVEST=1). Fail-open -> None,
    never raises: a preflight must not block the launch it prepares."""
    try:
        env_map = env if env is not None else os.environ
        decl = _decl_from_env_or_file(repo, env_map)
        if decl is None:
            return None
        harvested = 0
        no_harvest = str(env_map.get("PP_SESSION_NO_HARVEST", "")).strip() in (
            "1", "true", "yes")
        if not decl.candidate_questions and not no_harvest:
            decl.candidate_questions = _auto_harvest(repo)
            harvested = len(decl.candidate_questions)
        plan = compile_session(decl, now=now)
        p = write_plan(plan, out_dir=out_dir)
        worthy = sum(1 for q in plan.questions if q.frontier_worthy)
        where = f"  ({p})" if p else "  (write fail-open)"
        harvest_note = f" | auto-harvest {harvested}" if harvested else ""
        return "\n".join([
            f"FIOS: SESSION_ZERO generado para {plan.repo}{where}",
            f"FIOS: preguntas frontier-worthy {worthy}/{len(plan.questions)}"
            f"{harvest_note} | floor {plan.floor_size} deposito(s)",
            "FIOS: presupuesto discovery 30% architecture 25% critique 20% "
            "validation 15% emergency 10%",
        ])
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="FIOS Session Compiler -- declaration -> SESSION_ZERO plan")
    ap.add_argument("--objective", default="")
    ap.add_argument("--repo", default="")
    ap.add_argument("--question", action="append", dest="questions", default=[])
    ap.add_argument("--budget", type=int, default=0)
    ap.add_argument("--harvest", action="store_true",
                    help="merge harvested candidate questions into the declaration")
    ap.add_argument("--json-in", action="store_true",
                    help="read the full declaration as JSON on stdin")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--print", action="store_true", help="print the plan, do not write")
    ap.add_argument("--preflight", action="store_true",
                    help="kclaude frontier preflight: compile from env/.pp_frontier.json, "
                         "write SESSION_ZERO + print a 3-line summary; silent if no declaration")
    args = ap.parse_args(argv)
    if args.preflight:
        line = preflight(args.repo or os.getcwd(),
                         out_dir=Path(args.out_dir) if args.out_dir else None)
        if line:
            print(line)
        return 0
    if args.json_in and not sys.stdin.isatty():
        try:
            decl = _decl_from_obj(json.loads(sys.stdin.read() or "{}"))
        except (json.JSONDecodeError, ValueError):
            decl = SessionDeclaration(repo=os.getcwd())
    else:
        decl = SessionDeclaration(objective=args.objective,
                                  candidate_questions=args.questions,
                                  repo=args.repo or os.getcwd(),
                                  token_budget=args.budget)
    if args.harvest:
        decl.candidate_questions = list(decl.candidate_questions) + _auto_harvest(decl.repo)
    plan = compile_session(decl)
    if args.print:
        print(render_plan(plan))
    else:
        p = write_plan(plan, out_dir=args.out_dir)
        print(f"SESSION_ZERO written: {p}" if p else "write failed (fail-open)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
