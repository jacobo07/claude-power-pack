---
id: VP-CMP-scroll-based-velocity
name: Velocity Scroll
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: [landing, hero, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ b602c28 (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "animacion de titular (Text Animations); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# VP-CMP-scroll-based-velocity — Velocity Scroll

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`.

Descripcion upstream (texto del autor, no verificado aqui): "Text that moves horizontally based on scroll speed."

## Eje

Movimiento (B3) · categoria upstream `Text Animations` · render `dom`

## Senales medidas en la fuente

Fuente: `vault/knowledge_base/cdio/componentry/packages/ui/src/components/scroll-based-velocity.tsx` (sha256 `4fccb1db6aa6`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
| `reduced_motion` | no detectado |
| `webgl` | no detectado |
| `canvas2d` | no detectado |
| `svg` | no detectado |
| `infinite` | linea 11 |
| `raf` | no detectado |
| `pauses_offscreen` | no detectado |
| `pointer` | no detectado |
| `keyboard` | no detectado |
| `touch` | no detectado |
| `scroll` | linea 32 |
| `aria_hidden` | no detectado |
| `accessible_name` | no detectado |
| `webgl_fallback` | no detectado |

Dependencias externas: `framer-motion`.

## Por que este contrato minimo

- motion_budget->medium: animacion infinita (linea 11)

## Antes de usar

- Upstream NO lee `prefers-reduced-motion`. Anadir la variante reducida equivalente antes de usarlo; sin ella rompe el suelo de CDIO-07 sec.5.
- Trabajo continuo (linea 11) sin pausa fuera de pantalla: no se detecta IntersectionObserver, useInView ni visibilitychange. Anadir la pausa o aceptar coste constante de CPU y bateria.

## Cuando usar

- Superficies landing, hero, product-tour cuyo contrato CDIO-07 declara al menos
  `expressiveness: moderate` y `motion_budget: medium`.
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

- https://github.com/harshjdhv/componentry/blob/b602c2872fea85c9f2464016ce3bbe0af17b51b4/packages/ui/src/components/scroll-based-velocity.tsx
- https://componentry.dev/docs/components/scroll-based-velocity
