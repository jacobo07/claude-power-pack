---
id: VP-CMP-fisheye-infinite-grid
name: Fisheye Infinite Grid
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: [landing, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: high
  min_motion_budget: high
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ b602c28 (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "componente de escaparate (Components); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# VP-CMP-fisheye-infinite-grid — Fisheye Infinite Grid

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`.

Descripcion upstream (texto del autor, no verificado aqui): "A dense draggable image wall warped as one continuous fisheye surface with weighted momentum."

## Eje

Movimiento (B3) · categoria upstream `Components` · render `webgl`

## Senales medidas en la fuente

Fuente: `vault/knowledge_base/cdio/componentry/packages/ui/src/components/fisheye-infinite-grid.tsx` (sha256 `485700c746b6`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
| `reduced_motion` | linea 470 |
| `webgl` | linea 313 |
| `canvas2d` | linea 358 |
| `svg` | no detectado |
| `infinite` | no detectado |
| `raf` | linea 535 |
| `pauses_offscreen` | no detectado |
| `pointer` | linea 590 |
| `keyboard` | linea 689 |
| `touch` | linea 41 |
| `scroll` | linea 706 |
| `aria_hidden` | linea 801 |
| `accessible_name` | linea 252 |
| `webgl_fallback` | linea 184 |

Dependencias externas: ninguna fuera de React.

## Por que este contrato minimo

- expressiveness->high: renderiza por frame sobre webgl (linea 535)
- motion_budget->high: renderiza por frame sobre webgl sin pausa fuera de pantalla

## Antes de usar

- Upstream lee la preferencia de movimiento reducido (linea 470). Que la variante reducida sea EQUIVALENTE (la informacion y el cambio de estado llegan sin movimiento) no esta verificado: comprobarlo en navegador con `prefers-reduced-motion: reduce` antes de declarar el suelo cumplido.
- Trabajo continuo (linea 535) sin pausa fuera de pantalla: no se detecta IntersectionObserver, useInView ni visibilitychange. Anadir la pausa o aceptar coste constante de CPU y bateria.

## Cuando usar

- Superficies landing, product-tour cuyo contrato CDIO-07 declara al menos
  `expressiveness: high` y `motion_budget: high`.
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

- https://github.com/harshjdhv/componentry/blob/b602c2872fea85c9f2464016ce3bbe0af17b51b4/packages/ui/src/components/fisheye-infinite-grid.tsx
- https://componentry.dev/docs/components/fisheye-infinite-grid
