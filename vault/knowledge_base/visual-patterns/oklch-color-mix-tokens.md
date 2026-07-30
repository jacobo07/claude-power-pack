---
id: VP-012
name: OKLCH + color-mix() Dynamic Brand Tinting
type: pattern
domain: visual-patterns
status: active
---

# VP-012 — OKLCH + color-mix() Dynamic Brand Tinting

## Eje

Color-tokens (C1)

## Tecnica (sin codigo)

Definir UN solo token de marca en espacio de color OKLCH, y derivar todos los
estados (hover, active, tint de superficie, focus ring) via `color-mix()`
interpolando en `oklch` contra blanco/negro/otro token — en vez de hardcodear
un token distinto por cada estado. Mismo principio que los "dos tokens
dark/light" de [[text-bevel-effect]], generalizado a N estados derivados de
UN solo token base.

## Cuando usar

- Cualquier sistema de tokens de marca del Owner que hoy hardcodea variantes
  de hover/active/tint como colores independientes — sustituir esos tokens
  duplicados por derivaciones de `color-mix()`.
- Transiciones de tema (claro/oscuro) donde se quiere animar el porcentaje de
  mezcla en vez de crossfadear dos paletas completas.

## Cuando NO usar

- Si el target de navegadores incluye engines pre-2023 sin soporte de
  `color-mix()`/OKLCH — no hay fallback parcial razonable, es todo o nada
  para ese elemento.
- Colores de marca que YA estan certificados/aprobados exactos por
  guidelines externas (ej. un logo con Pantone especifico) — no derivar esos
  con `color-mix()`, usar el valor exacto.

## Variantes

- Mezcla con blanco/negro para generar tints/shades de un mismo token.
- Mezcla entre dos brand colors para transiciones de tema o degradados de
  marca controlados.

## Tokens requeridos

`--brand-base` (unico token en OKLCH; todos los derivados se calculan en
CSS via `color-mix()`, nunca se guardan como tokens estaticos adicionales).

## Soporte de navegador

`color-mix()` es "Baseline Widely Available" en 2026 en Chrome, Safari,
Firefox y Edge — sin gaps practicos en navegadores evergreen actuales; el
riesgo es solo en soporte legacy explicito.

## Contraste y WCAG

Favorable respecto a otros patrones de este documento: el canal L de OKLCH
mapea directamente a luminosidad percibida, lo que hace MAS facil (no mas
dificil) mantener ratios de contraste consistentes al derivar variantes —
pero sigue siendo obligatorio validar cada estado derivado contra WCAG AA,
no asumir que la derivacion matematica garantiza el ratio.

## Coste de mantenimiento

Bajo — una vez definido el token base, cada estado derivado es una linea de
CSS; reduce mantenimiento respecto al patron previo de hardcodear un token
por estado.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [color-mix() in CSS: The Most Underrated Color Tool of 2026 — ColorUI](https://colorui.io/blog/color-mix-css-guide)
- [Modern CSS Color: OKLCH, color-mix(), Relative Colors 2026 — ColorPick](https://colorpick.app/blog/modern-css-color-oklch-guide)
- [CSS color-mix() for Dynamic Theming — EdgeCases](https://www.edge-cases.com/css/css-color-mix-dynamic-theming)
