---
id: VP-015
name: Grainy Gradient Background
type: pattern
domain: visual-patterns
status: active
---

# VP-015 — Grainy Gradient Background

Variante ESTATICA del mismo mecanismo de ruido que
[[animated-grainy-texture]] (VP-011, B3); esta entrada es la version sin
animacion, mas barata en rendimiento.

## Eje

Superficie-textura (D2)

## Tecnica (sin codigo)

Un gradiente solido de marca (linear/radial) con una capa de ruido SVG
(`feTurbulence`) superpuesta via `mix-blend-mode`, para romper el aspecto
"plano/digital" de un gradiente puro sin recurrir a una fotografia. A
diferencia de VP-011, aqui la capa de ruido NO se anima.

## Cuando usar

- Sustituir un fondo de gradiente de marca plano por uno con textura sutil,
  sin el coste de rendimiento de una version animada.
- Fondos hero, secciones de marca, o superficies grandes donde el ruido
  estatico anade profundidad sin distraer.

## Cuando NO usar

- Superficies pequenas (botones, badges) — el ruido se pierde o se ve como
  artefacto de compresion en areas chicas.
- Si ya existe una version animada del mismo fondo en la misma vista — no
  mezclar ruido estatico y animado en el mismo campo visual.

## Variantes

- Ruido via SVG `feTurbulence` (Perlin noise real, mas control).
- Ruido via el "bug" de gradiente CSS documentado en CSS-Tricks (trick
  especifico de motor de renderizado, menos portable entre navegadores).

## Tokens requeridos

`--bg-gradient-base` (los stops del gradiente de marca), `--noise-opacity`.

## Soporte de navegador

`feTurbulence` tiene soporte amplio en navegadores modernos. El "bug" de
gradiente CSS como fuente de ruido es un truco dependiente del motor de
renderizado especifico que lo origino — preferir `feTurbulence` para
portabilidad real entre navegadores.

## Contraste y WCAG

Bajo riesgo si el ruido se mantiene sutil (opacidad baja) y no hay texto
critico superpuesto directamente sobre la zona de mayor densidad de grano;
verificar igualmente el contraste del texto que si vaya encima.

## Coste de mantenimiento

Bajo-medio — es una capa de textura reutilizable entre proyectos de marca,
pero `mix-blend-mode` sobre elementos grandes tiene coste de repintado no
trivial en paginas con mucho scroll.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Creating Patterns With SVG Filters — CSS-Tricks](https://css-tricks.com/creating-patterns-with-svg-filters/)
- [Grainy Gradients — CSS-Tricks](https://css-tricks.com/grainy-gradients/)
