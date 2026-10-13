---
id: VP-CMP-grain-gradient
name: Grain Gradient
type: pattern
domain: visual-patterns
status: active
generated_by: modules/cdio/componentry_catalog.py
motion:
  applies_to: [landing, hero]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: high
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: componentry.dev MIT @ b602c28 (fuente vendorizada, escaner estatico 2026-10-13)
  purpose: "fondo ambiental de hero (Hero Backgrounds); su unico valor es expresivo, por eso exige el contrato minimo indicado"
---

# VP-CMP-grain-gradient — Grain Gradient

Entrada generada por `python -m modules.cdio.componentry_catalog build`. No editar a
mano: el gate `tools/test_cdio_componentry.py` falla si difiere de lo que el escaner
produce. Indice y doctrina: `vault/knowledge_base/cdio/CDIO-11-componentry-catalog.md`.

Descripcion upstream (texto del autor, no verificado aqui): "A breathing color field with flowing shadows, customizable film grain, and soft atmospheric light."

## Eje

Movimiento (B3) · categoria upstream `Hero Backgrounds` · render `webgl`

## Senales medidas en la fuente

Fuente: `vault/knowledge_base/cdio/componentry/packages/ui/src/components/grain-gradient.tsx` (sha256 `45c4862f75b4`). "No detectado" significa que
ninguna de las expresiones de `SIGNALS` aparece en el fichero, no que la propiedad
este ausente en tiempo de ejecucion.

| senal | primera aparicion |
|---|---|
| `reduced_motion` | linea 240 |
| `webgl` | linea 169 |
| `canvas2d` | no detectado |
| `svg` | no detectado |
| `infinite` | no detectado |
| `raf` | linea 273 |
| `pauses_offscreen` | linea 272 |
| `pointer` | no detectado |
| `keyboard` | no detectado |
| `touch` | no detectado |
| `scroll` | no detectado |
| `aria_hidden` | linea 326 |
| `accessible_name` | no detectado |
| `webgl_fallback` | linea 174 |

Dependencias externas: ninguna fuera de React.

## Por que este contrato minimo

- Ninguno: el minimo es el de la categoria upstream.

## Antes de usar

- Upstream lee la preferencia de movimiento reducido (linea 240). Que la variante reducida sea EQUIVALENTE (la informacion y el cambio de estado llegan sin movimiento) no esta verificado: comprobarlo en navegador con `prefers-reduced-motion: reduce` antes de declarar el suelo cumplido.

## Cuando usar

- Superficies landing, hero cuyo contrato CDIO-07 declara al menos
  `expressiveness: high` y `motion_budget: medium`.
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

- https://github.com/harshjdhv/componentry/blob/b602c2872fea85c9f2464016ce3bbe0af17b51b4/packages/ui/src/components/grain-gradient.tsx
- https://componentry.dev/docs/components/grain-gradient
