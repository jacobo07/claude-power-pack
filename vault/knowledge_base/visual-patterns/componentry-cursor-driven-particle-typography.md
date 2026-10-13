---
id: VP-CMP-cursor-driven-particle-typography
name: Particle Typography
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: [landing, hero, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: high
  min_motion_budget: high
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ b602c28 (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "animacion de titular (Text Animations); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# VP-CMP-cursor-driven-particle-typography — Particle Typography

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`.

Descripcion upstream (texto del autor, no verificado aqui): "Renders dynamic typography constructed entirely from particles that elegantly disperse and reassemble upon cursor interaction using spring physics."

## Eje

Movimiento (B3) · categoria upstream `Text Animations` · render `canvas2d`

## Senales medidas en la fuente

Fuente: `vault/knowledge_base/cdio/componentry/packages/ui/src/components/cursor-driven-particle-typography.tsx` (sha256 `c771fae987b3`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
| `reduced_motion` | no detectado |
| `webgl` | no detectado |
| `canvas2d` | linea 127 |
| `svg` | no detectado |
| `infinite` | no detectado |
| `raf` | linea 206 |
| `pauses_offscreen` | no detectado |
| `pointer` | linea 247 |
| `keyboard` | no detectado |
| `touch` | linea 249 |
| `scroll` | no detectado |
| `aria_hidden` | no detectado |
| `accessible_name` | no detectado |
| `webgl_fallback` | linea 128 |

Dependencias externas: ninguna fuera de React.

## Por que este contrato minimo

- expressiveness->high: renderiza por frame sobre canvas2d (linea 206)
- motion_budget->high: renderiza por frame sobre canvas2d sin pausa fuera de pantalla

## Antes de usar

- Upstream NO lee `prefers-reduced-motion`. Anadir la variante reducida equivalente antes de usarlo; sin ella rompe el suelo de CDIO-07 sec.5.
- Responde al puntero (linea 247) sin camino de teclado. Nada que solo se revela con hover puede ser el unico canal de una informacion.
- Trabajo continuo (linea 206) sin pausa fuera de pantalla: no se detecta IntersectionObserver, useInView ni visibilitychange. Anadir la pausa o aceptar coste constante de CPU y bateria.
- Canvas sin `aria-hidden` ni nombre accesible. Si es decorativo, ocultarlo al arbol de accesibilidad; si comunica algo, darle texto equivalente.

## Cuando usar

- Superficies landing, hero, product-tour cuyo contrato CDIO-07 declara al menos
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

- https://github.com/harshjdhv/componentry/blob/b602c2872fea85c9f2464016ce3bbe0af17b51b4/packages/ui/src/components/cursor-driven-particle-typography.tsx
- https://componentry.dev/docs/components/cursor-driven-particle-typography
