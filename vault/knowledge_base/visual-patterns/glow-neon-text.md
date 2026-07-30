---
id: VP-005
name: Glow/Neon Text
type: pattern
domain: visual-patterns
status: active
---

# VP-005 — Glow/Neon Text

## Eje

Relleno-texto (A5)

## Tecnica (sin codigo)

Multiples capas de `text-shadow` apiladas (radio creciente, misma tonalidad)
para simular un halo de luz; opcionalmente animadas con `@keyframes` para un
pulso de intensidad.

## Cuando usar

- Marca con identidad tech/gaming/nocturna donde el "brillo" es parte de la
  personalidad visual.
- Estados puntuales (hover, destacado activo) donde el glow refuerza una
  jerarquia, no la reemplaza.

## Cuando NO usar

- UI funcional: botones, labels, inputs — el glow reduce legibilidad y no
  aporta significado funcional.
- Marca con posicionamiento serio/corporativo — el neon connota gaming/nightlife,
  no encaja fuera de ese registro.

## Variantes

- Glow estatico (sin animacion).
- Pulso animado (`@keyframes` de intensidad).
- Multi-color neon (varias capas de `text-shadow` con distinto hue).

## Tokens requeridos

`--glow-color`, `--glow-radius`, `--glow-pulse-duration` (solo si se anima).

## Soporte de navegador

`text-shadow` es una propiedad estable y universalmente soportada desde hace
mas de una decada — sin gaps reales de navegador. El unico riesgo real es de
rendimiento/accesibilidad si se anima, no de compatibilidad.

## Contraste y WCAG

Si el glow es la UNICA forma de indicar estado (ej. "activo"), falla el
criterio de no depender solo del color/efecto — acompanar siempre con un
cambio de texto, icono o forma. Si se anima, respetar
`prefers-reduced-motion` (pulso constante puede afectar a usuarios con
trastornos vestibulares).

## Coste de mantenimiento

Bajo si es estatico; medio si se anima — el keyframe de pulso exige un guard
de `prefers-reduced-motion` explicito, que es facil de olvidar al copiar el
patron a un nuevo componente.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [47 Best CSS Glow Effects (Glowing UI in CSS) — testmuai](https://www.testmuai.com/blog/glowing-effects-in-css/)
