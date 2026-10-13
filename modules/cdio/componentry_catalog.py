"""Componentry catalog: vendored source -> measured signals -> CDIO motion entries.

componentry.dev (MIT, github.com/harshjdhv/componentry) is a library of animated
React components. It was absorbed into CDIO on 2026-10-13 (see
`vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`). The source is
vendored byte-identical under `vault/knowledge_base/cdio/componentry/`.

This module is the only producer of the 54 `visual-patterns/componentry-*.md`
entries and of `componentry/catalog.json`. It does three things, and no more:

  1. DISCOVER the catalog from upstream's own registry (`apps/web/registry/index.ts`),
     never from a hand-kept list. A component upstream lists but whose source is
     missing is an error, not a silent skip.
  2. MEASURE each source file with fixed regular expressions. Every signal carries
     the line where it was first seen, so each claim in an entry can be checked
     against the source. A signal is a static fact ("the file reads
     prefers-reduced-motion at line 131"), never a runtime claim ("the reduced
     variant is equivalent") -- the static plane cannot see that, and entries say so.
  3. DERIVE the `motion:` block that `modules.cdio.motion_patterns` consumes, from
     the upstream category plus the measured signals. Derivation only narrows:
     a measured cost can raise a component's minimum contract, never lower it.

    python -m modules.cdio.componentry_catalog build   # (re)write catalog + entries
    python -m modules.cdio.componentry_catalog check   # exit 1 on drift
    python -m modules.cdio.componentry_catalog show <slug>
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
VENDOR_DIR = os.path.join(_PP_ROOT, "vault", "knowledge_base", "cdio", "componentry")
REGISTRY = os.path.join(VENDOR_DIR, "apps", "web", "registry", "index.ts")
COMPONENTS_DIR = os.path.join(VENDOR_DIR, "packages", "ui", "src", "components")
CATALOG_JSON = os.path.join(VENDOR_DIR, "catalog.json")
PATTERNS_DIR = os.path.join(_PP_ROOT, "vault", "knowledge_base", "visual-patterns")
ENTRY_PREFIX = "componentry-"
ID_PREFIX = "VP-CMP-"
INDEX_DOC = "vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md"

UPSTREAM = "https://github.com/harshjdhv/componentry"
UPSTREAM_COMMIT = "b602c2872fea85c9f2464016ce3bbe0af17b51b4"

# --------------------------------------------------------------------- signals
# Each regex was calibrated against the vendored source on 2026-10-13. In
# particular `matchMedia` alone is NOT a reduced-motion signal: circuit-board reads
# prefers-color-scheme and dithered-logo reads max-width through it.
SIGNALS = {
    # No bare `reducedMotion =` alternative: it also matches a prop passed down or a
    # `reducedMotion = false` default, which would credit a file that never reads it.
    "reduced_motion": r"prefers-reduced-motion|useReducedMotion\s*\(|motion-reduce:|reducedMotion=[\"']user",
    "webgl": r"getContext\(\s*[\"'](?:webgl2?|experimental-webgl)|@react-three/fiber|from\s+[\"']three[\"']|WebGLRenderer",
    "canvas2d": r"getContext\(\s*[\"']2d",
    "svg": r"<svg\b",
    # Two signals, not one: `requestAnimationFrame` is also used one-shot (a
    # throttle, a deferred measure), so it cannot claim a continuous loop by itself.
    # `infinite` matches only constructs that run until unmounted.
    "infinite": r"repeat:\s*Infinity|setInterval\s*\(|useAnimationFrame|useFrame\s*\(|gsap\.ticker",
    "raf": r"requestAnimationFrame",
    "pauses_offscreen": r"IntersectionObserver|useInView\s*\(|visibilitychange|document\.hidden|whileInView",
    "pointer": r"onMouseMove|onPointerMove|[\"']mousemove[\"']|[\"']pointermove[\"']|onMouseEnter|onPointerEnter|whileHover|onHoverStart",
    "keyboard": r"onKeyDown|onKeyUp|[\"']keydown[\"']|tabIndex",
    "touch": r"onTouchStart|[\"']touchstart[\"']|onPointerDown|[\"']pointerdown[\"']|\bdrag\b|onPan",
    "scroll": r"useScroll\s*\(|onScroll|[\"']scroll[\"']|ScrollTrigger|lenis|onWheel|[\"']wheel[\"']",
    "aria_hidden": r"aria-hidden",
    "accessible_name": r"aria-label|aria-labelledby|role=|sr-only",
    "webgl_fallback": r"WebGLErrorBoundary|webgl-error-boundary|if\s*\(\s*!\s*gl\b|if\s*\(\s*!\s*(?:ctx|context)\b",
}
_SIGNAL_RE = {k: re.compile(v) for k, v in SIGNALS.items()}
_IMPORT_RE = re.compile(r"^import\s[^;]*?from\s+[\"']([^\"']+)[\"']", re.MULTILINE)

# --------------------------------------------------------------------- derivation
EXPRESSIVENESS = ("none", "restrained", "moderate", "high")
MOTION = ("none", "low", "medium", "high")
EXCLUDED = ["checkout", "auth", "admin", "settings", "form", "dashboard",
            "destructive", "docs", "list-detail"]

# upstream category -> (applies_to, min_expressiveness, min_motion_budget, role)
CATEGORY_BASE = {
    "Hero Backgrounds": (["landing", "hero"], "high", "medium", "fondo ambiental de hero"),
    "Visual Effects": (["landing", "hero", "product-tour"], "high", "medium", "efecto visual de escaparate"),
    "ASCII Effects": (["landing", "hero"], "high", "medium", "efecto ASCII de escaparate"),
    "Text Animations": (["landing", "hero", "product-tour"], "moderate", "low", "animacion de titular"),
    "Components": (["landing", "product-tour"], "moderate", "low", "componente de escaparate"),
}

# Keys are quoted when they contain a dash and bare otherwise (`signature: {`).
# A regex that knew only one form dropped a component silently on 2026-10-13, so
# parse_registry also cross-checks the parsed count against every `slug:` field.
_ENTRY_RE = re.compile(
    r'^\s{2}"?([a-z0-9-]+)"?:\s*\{(.*?)^\s{2}\},?\s*$', re.MULTILINE | re.DOTALL)
_SLUG_FIELD_RE = re.compile(r'^\s+slug:\s*"', re.MULTILINE)
_STR_FIELD = r'{0}:\s*(?:\n\s*)?"((?:[^"\\]|\\.)*)"'


def _field(body: str, name: str):
    m = re.search(_STR_FIELD.format(name), body)
    return m.group(1) if m else None


def parse_registry(text: str):
    """Return (components, errors) from upstream's registry source."""
    comps, errors = [], []
    for key, body in _ENTRY_RE.findall(text):
        rec = {f: _field(body, f) for f in ("title", "description", "category", "slug")}
        missing = [f for f, v in rec.items() if v is None]
        if missing:
            errors.append(f"registry entry {key!r}: missing {missing}")
            continue
        if rec["slug"] != key:
            errors.append(f"registry entry {key!r}: slug field is {rec['slug']!r}")
        if rec["category"] not in CATEGORY_BASE:
            errors.append(f"registry entry {key!r}: unknown category {rec['category']!r}")
            continue
        comps.append(rec)
    declared = len(_SLUG_FIELD_RE.findall(text))
    if declared != len(comps) + len(errors):
        errors.append(f"registry declares {declared} slug fields, parser accounted for "
                      f"{len(comps) + len(errors)}: an entry shape is not understood")
    return sorted(comps, key=lambda c: c["slug"]), errors


def scan_source(text: str) -> dict:
    """Return {signal: first 1-based line or None} plus external imports."""
    lines = text.splitlines()
    out = {}
    for name, rx in _SIGNAL_RE.items():
        out[name] = next((i for i, ln in enumerate(lines, 1) if rx.search(ln)), None)
    deps = sorted({s for s in _IMPORT_RE.findall(text)
                   if not s.startswith((".", "@workspace/")) and s != "react"})
    return {"signals": out, "deps": deps}


def _max(vocab, a, b):
    return a if vocab.index(a) >= vocab.index(b) else b


def derive(meta: dict, scan: dict) -> dict:
    """Derive the motion contract and the before-use list. Only ever narrows."""
    s = scan["signals"]
    applies, expr, budget, role = CATEGORY_BASE[meta["category"]]
    render = ("webgl" if s["webgl"] else "canvas2d" if s["canvas2d"]
              else "svg" if s["svg"] else "dom")
    raised = []
    frame_line = s["infinite"] or s["raf"]
    # A canvas/WebGL surface that schedules frames is a per-frame renderer; on the
    # DOM only an `infinite` construct proves continuity.
    continuous = bool(s["infinite"] or (s["raf"] and render in ("webgl", "canvas2d")))
    if continuous and render in ("webgl", "canvas2d"):
        if expr != "high":
            raised.append(f"expressiveness->high: renderiza por frame sobre {render} "
                          f"(linea {frame_line})")
        expr = "high"
        need = "medium" if s["pauses_offscreen"] else "high"
        if MOTION.index(need) > MOTION.index(budget):
            raised.append(f"motion_budget->{need}: renderiza por frame sobre {render}"
                          + ("" if s["pauses_offscreen"] else " sin pausa fuera de pantalla"))
        budget = _max(MOTION, budget, need)
    elif continuous and MOTION.index(budget) < MOTION.index("medium"):
        raised.append(f"motion_budget->medium: animacion infinita (linea {s['infinite']})")
        budget = "medium"

    before_use = []
    if s["reduced_motion"]:
        before_use.append(
            f"Upstream lee la preferencia de movimiento reducido (linea {s['reduced_motion']}). "
            "Que la variante reducida sea EQUIVALENTE (la informacion y el cambio de estado "
            "llegan sin movimiento) no esta verificado: comprobarlo en navegador con "
            "`prefers-reduced-motion: reduce` antes de declarar el suelo cumplido.")
    else:
        before_use.append(
            "Upstream NO lee `prefers-reduced-motion`. Anadir la variante reducida "
            "equivalente antes de usarlo; sin ella rompe el suelo de CDIO-07 sec.5.")
    if s["pointer"] and not s["keyboard"]:
        before_use.append(
            f"Responde al puntero (linea {s['pointer']}) sin camino de teclado. Nada que "
            "solo se revela con hover puede ser el unico canal de una informacion.")
    if continuous and not s["pauses_offscreen"]:
        before_use.append(
            f"Trabajo continuo (linea {frame_line}) sin pausa fuera de pantalla: no se "
            "detecta IntersectionObserver, useInView ni visibilitychange. Anadir la pausa "
            "o aceptar coste constante de CPU y bateria.")
    elif s["raf"] and not continuous:
        before_use.append(
            f"Programa trabajo por frame (linea {s['raf']}); si es un bucle continuo o "
            "un frame puntual no es decidible por lectura estatica. Medirlo en navegador "
            "antes de fijar el `motion_budget` del contrato.")
    if render == "webgl" and not s["webgl_fallback"]:
        before_use.append(
            "WebGL sin ruta de fallo detectada: sin contexto WebGL el hueco queda vacio. "
            "Envolver en el `webgl-error-boundary` vendorizado o dar un fondo estatico.")
    if render in ("webgl", "canvas2d") and not (s["aria_hidden"] or s["accessible_name"]):
        before_use.append(
            "Canvas sin `aria-hidden` ni nombre accesible. Si es decorativo, ocultarlo al "
            "arbol de accesibilidad; si comunica algo, darle texto equivalente.")
    return {"applies_to": applies, "excluded_from": list(EXCLUDED),
            "min_expressiveness": expr, "min_motion_budget": budget,
            "render": render, "role": role, "raised": raised, "before_use": before_use}


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def build_catalog():
    """Return (catalog_dict, errors). Reads only; writes nothing."""
    errors = []
    try:
        with open(REGISTRY, "r", encoding="utf-8-sig") as fh:
            comps, reg_errors = parse_registry(fh.read())
    except OSError as exc:
        return None, [f"registry unreadable: {exc}"]
    errors.extend(reg_errors)
    out = []
    for meta in comps:
        src = os.path.join(COMPONENTS_DIR, meta["slug"] + ".tsx")
        if not os.path.isfile(src):
            errors.append(f"{meta['slug']}: listed by upstream registry, source missing")
            continue
        with open(src, "r", encoding="utf-8-sig") as fh:
            scan = scan_source(fh.read())
        out.append(dict(meta, source=os.path.relpath(src, _PP_ROOT).replace("\\", "/"),
                        sha256=_sha256(src), **scan, derived=derive(meta, scan)))
    listed = {c["slug"] for c in comps}
    support = sorted(os.path.splitext(n)[0] for n in os.listdir(COMPONENTS_DIR)
                     if n.endswith(".tsx") and os.path.splitext(n)[0] not in listed)
    return {"upstream": UPSTREAM, "commit": UPSTREAM_COMMIT, "license": "MIT",
            "components": out, "support_files": support}, errors


def _yaml_list(vals):
    return "[" + ", ".join(vals) + "]"


def render_entry(c: dict) -> str:
    d, s = c["derived"], c["signals"]
    sig_rows = "\n".join(
        f"| `{k}` | {'linea ' + str(v) if v else 'no detectado'} |" for k, v in s.items())
    deps = ", ".join(f"`{x}`" for x in c["deps"]) or "ninguna fuera de React"
    raised = ("\n".join(f"- {r}" for r in d["raised"])
              or "- Ninguno: el minimo es el de la categoria upstream.")
    before = "\n".join(f"- {b}" for b in d["before_use"])
    desc = c["description"].replace('\\"', '"')
    return f"""---
id: {ID_PREFIX}{c['slug']}
name: {c['title']}
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: {_yaml_list(d['applies_to'])}
  excluded_from: {_yaml_list(d['excluded_from'])}
  min_expressiveness: {d['min_expressiveness']}
  min_motion_budget: {d['min_motion_budget']}
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ {UPSTREAM_COMMIT[:7]} (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "{d['role']} ({c['category']}); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# {ID_PREFIX}{c['slug']} — {c['title']}

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `{INDEX_DOC}`.

Descripcion upstream (texto del autor, no verificado aqui): "{desc}"

## Eje

Movimiento (B3) · categoria upstream `{c['category']}` · render `{d['render']}`

## Senales medidas en la fuente

Fuente: `{c['source']}` (sha256 `{c['sha256'][:12]}`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
{sig_rows}

Dependencias externas: {deps}.

## Por que este contrato minimo

{raised}

## Antes de usar

{before}

## Cuando usar

- Superficies {', '.join(d['applies_to'])} cuyo contrato CDIO-07 declara al menos
  `expressiveness: {d['min_expressiveness']}` y `motion_budget: {d['min_motion_budget']}`.
- Como una pieza expresiva por vista, en el punto de lectura que la justifica.

## Cuando NO usar

- En superficies transaccionales o de trabajo ({', '.join(d['excluded_from'])}): alli el
  movimiento expresivo compite con la tarea y el resolver lo excluye.
- Como acuse, progreso o exito de una operacion real. Es movimiento de escaparate y no
  puede afirmar un resultado que el sistema no ha producido (CDIO-07 sec.12).
- Junto a otras piezas animadas que corran a la vez en la misma vista: el presupuesto de
  movimiento es agregado (CDIO-07 sec.12), no por componente.
- Sin haber resuelto la lista "Antes de usar".

## Evidence

`research`: fuente leida por un escaner estatico; no construido aun en un proyecto del
Owner. Ninguna afirmacion de esta entrada describe el comportamiento en navegador.

## Fuentes

- {UPSTREAM}/blob/{UPSTREAM_COMMIT}/packages/ui/src/components/{c['slug']}.tsx
- https://componentry.dev/docs/components/{c['slug']}
"""


def _expected_files(catalog: dict) -> dict:
    files = {CATALOG_JSON: json.dumps(catalog, indent=2, sort_keys=True,
                                      ensure_ascii=False) + "\n"}
    for c in catalog["components"]:
        files[os.path.join(PATTERNS_DIR, ENTRY_PREFIX + c["slug"] + ".md")] = render_entry(c)
    return files


def _read(path):
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return fh.read()
    except OSError:
        return None


def drift(catalog: dict) -> list:
    """Paths whose on-disk content differs from what the scanner produces, plus
    generated entries on disk that no longer correspond to a component."""
    expected = _expected_files(catalog)
    out = [p for p, body in expected.items() if _read(p) != body]
    on_disk = {os.path.join(PATTERNS_DIR, n) for n in os.listdir(PATTERNS_DIR)
               if n.startswith(ENTRY_PREFIX) and n.endswith(".md")}
    out.extend(sorted(on_disk - set(expected)))
    return [os.path.relpath(p, _PP_ROOT).replace("\\", "/") for p in out]


def write(catalog: dict) -> int:
    n = 0
    for path, body in _expected_files(catalog).items():
        if _read(path) != body:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            n += 1
    return n


def main(argv) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    catalog, errors = build_catalog()
    for e in errors:
        print(f"ERROR {e}")
    if catalog is None or errors:
        return 1
    n = len(catalog["components"])
    if cmd == "build":
        print(f"components={n} support_files={len(catalog['support_files'])} "
              f"written={write(catalog)}")
        return 0
    if cmd == "check":
        d = drift(catalog)
        for p in d:
            print(f"DRIFT {p}")
        print(f"components={n} drift={len(d)}")
        return 1 if d else 0
    if cmd == "show" and len(argv) > 2:
        hit = [c for c in catalog["components"] if c["slug"] == argv[2]]
        print(json.dumps(hit[0] if hit else None, indent=2, ensure_ascii=False))
        return 0 if hit else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
