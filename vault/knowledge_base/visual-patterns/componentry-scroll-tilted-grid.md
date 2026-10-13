---
id: VP-CMP-scroll-tilted-grid
name: Scroll Tilted Grid
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: [landing, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: moderate
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ b602c28 (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "componente de escaparate (Components); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# VP-CMP-scroll-tilted-grid — Scroll Tilted Grid

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`.

Descripcion upstream (texto del autor, no verificado aqui): "A cinematic image grid that tilts and resolves into focus as each frame crosses the viewport."

## Eje

Movimiento (B3) · categoria upstream `Components` · render `dom`

## Senales medidas en la fuente

Fuente: `vault/knowledge_base/cdio/componentry/packages/ui/src/components/scroll-tilted-grid.tsx` (sha256 `6d82d640c310`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
| `reduced_motion` | linea 169 |
| `webgl` | no detectado |
| `canvas2d` | no detectado |
| `svg` | no detectado |
| `infinite` | no detectado |
| `raf` | linea 97 |
| `pauses_offscreen` | linea 179 |
| `pointer` | no detectado |
| `keyboard` | no detectado |
| `touch` | no detectado |
| `scroll` | linea 5 |
| `aria_hidden` | linea 223 |
| `accessible_name` | linea 202 |
| `webgl_fallback` | no detectado |

Dependencias externas: `framer-motion`, `lenis/react`.

## Por que este contrato minimo

- Ninguno: el minimo es el de la categoria upstream.

## Antes de usar

- Upstream lee la preferencia de movimiento reducido (linea 169). Que la variante reducida sea EQUIVALENTE (la informacion y el cambio de estado llegan sin movimiento) no esta verificado: comprobarlo en navegador con `prefers-reduced-motion: reduce` antes de declarar el suelo cumplido.
- Programa trabajo por frame (linea 97); si es un bucle continuo o un frame puntual no es decidible por lectura estatica. Medirlo en navegador antes de fijar el `motion_budget` del contrato.

## Cuando usar

- Superficies landing, product-tour cuyo contrato CDIO-07 declara al menos
  `expressiveness: moderate` y `motion_budget: low`.
- Como una pieza expresiva por vista, en el punto de lectura que la justifica.

## Cuando NO usar

- En superficies transaccionales o de trabajo (checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail): alli el
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

- https://github.com/harshjdhv/componentry/blob/b602c2872fea85c9f2464016ce3bbe0af17b51b4/packages/ui/src/components/scroll-tilted-grid.tsx
- https://componentry.dev/docs/components/scroll-tilted-grid
