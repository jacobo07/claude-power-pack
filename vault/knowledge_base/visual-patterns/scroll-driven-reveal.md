---
id: VP-010
name: Scroll-Driven Reveal (zero-JS)
type: pattern
domain: visual-patterns
status: active
---

# VP-010 — Scroll-Driven Reveal (zero-JS)

## Eje

Movimiento (B2)

## Tecnica (sin codigo)

`animation-timeline: view()` combinado con `animation-range` (ej.
`entry 0% entry 40%`) para que una animacion CSS declarativa avance segun la
visibilidad del elemento en el viewport, sin ninguna linea de JavaScript de
scroll-listener.

## Cuando usar

- Revelar un logotipo, seccion de marca o bloque hero a medida que entra en
  viewport, en un proyecto donde evitar JS de scroll es una prioridad de
  rendimiento.

## Cuando NO usar

- Cualquier producto donde Safari sea un target obligatorio SIN fallback
  aceptable — el elemento debe verse correctamente (aunque sea estatico) sin
  la animacion.
- Interacciones que requieran logica condicional compleja (branching segun
  direccion de scroll, velocidad, etc.) — eso si necesita JS real.

## Variantes

- `view()`: progreso ligado a la visibilidad del elemento (mejor para reveals
  puntuales de un elemento especifico).
- `scroll()`: progreso ligado al scroll del contenedor completo (mejor para
  barras de progreso o parallax de pagina entera).

## Tokens requeridos

`--reveal-range-start`, `--reveal-range-end` (como porcentajes de entrada,
no valores de pixel fijos).

## Soporte de navegador

Chrome/Edge/Opera soportan `animation-timeline` desde Chrome 115+; Firefox lo
soporta solo detras de un flag; Safari no lo soporta en absoluto a fecha de
esta entrada. **Fallback estatico obligatorio**: el contenido debe ser
completamente legible y funcional sin la animacion en Safari/Firefox
default.

## Contraste y WCAG

Bajo riesgo de contraste (no cambia color); riesgo de movimiento — cualquier
reveal debe respetar `prefers-reduced-motion` (mostrar el estado final
directamente, sin animacion de entrada).

## Coste de mantenimiento

Medio — la sintaxis es declarativa y zero-JS, pero el fallback estatico para
Safari/Firefox debe mantenerse y probarse por separado, duplicando
efectivamente la superficie de QA visual.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [A Practical Introduction to Scroll-Driven Animations — Codrops](https://tympanus.net/codrops/2024/01/17/a-practical-introduction-to-scroll-driven-animations-with-css-scroll-and-view/)
- [Scroll-driven animation timelines — MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations/Timelines)
- [Unleash the Power of Scroll-Driven Animations — CSS-Tricks](https://css-tricks.com/unleash-the-power-of-scroll-driven-animations/)
