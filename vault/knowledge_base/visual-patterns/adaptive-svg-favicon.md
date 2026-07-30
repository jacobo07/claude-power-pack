---
id: VP-013
name: Adaptive SVG Favicon
type: pattern
domain: visual-patterns
status: active
---

# VP-013 — Adaptive SVG Favicon

## Eje

Color-tokens (C2)

## Tecnica (sin codigo)

Un favicon en formato SVG con un bloque `<style>` embebido dentro del propio
archivo que usa `@media (prefers-color-scheme: dark)` para cambiar los
colores del icono segun el tema del sistema operativo — sin necesitar dos
archivos ni JS.

## Cuando usar

- Cualquier marca del Owner con presencia web publica donde la pestana del
  navegador deba mantener contraste/legibilidad tanto en modo claro como
  oscuro del SO (no del sitio — del sistema operativo).

## Cuando NO usar

- Herramientas internas/CLI/dashboards de dev sin necesidad de pulido de
  marca en la pestana — no vale la friccion de mantener el fallback.

## Variantes

- CSS embebido dentro del propio SVG (`<style>` + `@media` en un `<defs>`).
- Multiples tags `<link rel="icon">` con atributo `media` apuntando a
  archivos SVG/PNG distintos por esquema de color (mas compatible, mas
  archivos que mantener).

## Tokens requeridos

`--favicon-light`, `--favicon-dark` (referencias a los dos assets/variantes,
no valores de color sueltos).

## Soporte de navegador

Chrome, Firefox y Edge soportan el auto-switch via `prefers-color-scheme`
embebido en el SVG. **Safari NO soporta el auto-switch de favicon** aunque si
soporta `prefers-color-scheme` en CSS normal de pagina — requiere un
fallback ICO/PNG fijo para Safari, no se puede depender solo de la variante
SVG adaptativa.

## Contraste y WCAG

No aplica WCAG de contenido (no es texto ni UI interactiva); el criterio
relevante es puramente de legibilidad de marca en un area de 16-32px, sin
implicacion de accesibilidad normativa.

## Coste de mantenimiento

Bajo — un unico archivo SVG con media query embebida cubre la mayoria de
navegadores; el unico coste adicional es mantener el fallback ICO/PNG para
Safari sincronizado si cambia el diseno del icono.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [How to Create Adaptive Favicons for Light and Dark Modes — Favicon.im](https://favicon.im/blog/favicon-for-light-dark-modes)
- [Building an adaptive favicon — web.dev](https://web.dev/articles/building/an-adaptive-favicon)
- [Adaptive SVG favicon with dark mode — Ben Gammon](https://bengammon.co.uk/adaptive-svg-favicon-with-dark-mode/)
