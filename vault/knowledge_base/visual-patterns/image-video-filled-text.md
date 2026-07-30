---
id: VP-006
name: Image/Video-Filled Text
type: pattern
domain: visual-patterns
status: active
---

# VP-006 — Image/Video-Filled Text

## Eje

Relleno-texto (A6)

## Tecnica (sin codigo)

`background-clip: text` con una imagen como `background-image` (en vez de un
gradiente), o `mask-image`/SVG mask para recortar un `<video>` con la forma
del texto. El texto actua como "ventana" hacia el asset.

## Cuando usar

- Hero headline de una sola marca donde el producto/foto/video ES el
  contenido, y el texto es el marco que lo revela.
- Landing pages de producto con un unico asset hero de alta calidad.

## Cuando NO usar

- Cualquier contexto donde el texto deba seguir siendo legible sin depender
  del contenido visual que hay detras — el asset puede tener zonas de bajo
  contraste interno que vuelven ilegibles letras enteras.
- Texto que cambia dinamicamente (i18n, CMS) — el asset debe re-encuadrarse
  a mano para cada longitud de texto distinta.

## Cuando NO usar (WCAG)

Coste WCAG alto por diseno: el "color" percibido de cada letra depende del
contenido de la imagen/video en ese punto exacto, no de un token controlado
— es estructuralmente imposible garantizar contraste uniforme.

## Variantes

- Fill con imagen estatica.
- Fill con `<video>` via mask (el video se reproduce dentro de la forma del
  texto).

## Tokens requeridos

`--brand-fill-asset` (referencia al asset, no un color),
`--text-fallback-color` (color solido de respaldo para navegadores/casos sin
soporte del masking).

## Soporte de navegador

`background-clip: text` con imagen tiene el mismo soporte que con gradiente
(prefijo `-webkit-` en Safari). El masking de `<video>` via `mask-image`/SVG
mask tiene soporte mas desigual entre navegadores — probar el fallback
estatico (`--text-fallback-color`) en cada engine objetivo antes de shippear.

## Contraste y WCAG

Ver "Cuando NO usar (WCAG)" arriba — es el patron de mayor riesgo WCAG de
todo el eje A porque el contraste no es configurable, es una propiedad
emergente del asset.

## Coste de mantenimiento

Alto — el asset debe mantenerse legible dentro de las letras en CADA tamano
de viewport (el recorte de texto no reescala el contenido interno de forma
inteligente); cualquier cambio de copy obliga a re-encuadrar el asset.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Image-Filled Text with CSS Clip Mask — Squarestylist](https://www.squarestylist.com/squarespace/image-filled-text-clip-mask)
- [CSS Masking — Ahmad Shadeed](https://ishadeed.com/article/css-masking/)
