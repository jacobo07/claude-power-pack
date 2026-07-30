---
id: VP-004
name: Gradient Stroke Text
type: pattern
domain: visual-patterns
status: active
---

# VP-004 — Gradient Stroke Text

## Eje

Relleno-texto (A4)

## Tecnica (sin codigo)

Contorno del texto via `-webkit-text-stroke` (grosor + color), combinado con
`background-clip: text` para que el propio stroke — no el relleno — porte el
gradiente. El interior puede quedar transparente o con relleno solido
distinto del contorno.

## Cuando usar

- Titulos grandes sobre fondo variable (foto, video, gradiente animado)
  donde un relleno solido de texto competiria visualmente con el fondo.
- Cuando la marca quiere un titulo "hueco" que deje ver el fondo a traves.

## Cuando NO usar

- Tamanos de fuente pequenos — el stroke se vuelve ilegible por debajo de un
  umbral de peso/tamano.
- Cuerpo de texto o UI funcional.

## Variantes

- Stroke solido + relleno transparente (texto "hueco").
- Stroke con gradiente + relleno con gradiente distinto (doble capa).

## Tokens requeridos

`--color-[nombre]`, `--color-[nombre]-light`, `--stroke-width`.

## Soporte de navegador

`-webkit-text-stroke` es una propiedad NO estandar con prefijo permanente —
no existe una version sin prefijo garantizada a futuro (a diferencia de
`background-clip: text`, que si tiene camino de estandarizacion). Tratar como
progressive enhancement, nunca como base del layout.

## Contraste y WCAG

Riesgo doble: el contorno debe ser legible contra el fondo variable Y, si el
relleno interior es transparente, el fondo que se ve A TRAVES del texto debe
mantenerse suficientemente distinto del contorno para que la forma de la
letra siga siendo perceptible.

## Coste de mantenimiento

Medio — depende de una propiedad no estandar sin ruta de deprecacion clara;
cualquier cambio de rendering engine (Safari, Chromium) puede alterar el
grosor percibido del stroke sin aviso.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [30 Modern CSS Text Effects (2026)](https://veebilehed24.ee/en/blog/modern-css-text-effects-2026/)
