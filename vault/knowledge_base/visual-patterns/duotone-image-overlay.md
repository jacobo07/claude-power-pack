---
id: VP-008
name: Duotone Image Overlay
type: pattern
domain: visual-patterns
status: active
---

# VP-008 — Duotone Image Overlay

No es un patron de texto — es un tratamiento de fotografia de marca. Se
incluye en el eje A porque comparte mecanismo (dos tokens de color aplicados
sobre un asset) con [[text-bevel-effect]] y [[gradient-text]].

## Eje

Relleno-texto (A8) — tratamiento de imagen, no de texto

## Tecnica (sin codigo)

SVG `feColorMatrix`/`feComponentTransfer` o un filtro CSS de mapeo de dos
tonos aplicado sobre una fotografia: las sombras de la imagen se mapean a un
token oscuro de marca y las luces a un token claro, sustituyendo toda la
gama tonal original por solo dos colores.

## Cuando usar

- Tratamiento consistente de fotografia editorial/producto en toda la marca
  (el caso historico de Spotify: cada foto de campana pasa por el mismo
  duotono para leerse como "una sola marca" aunque las fotos originales sean
  de fuentes distintas).

## Cuando NO usar

- Fotografia de producto donde el color REAL del producto es informacion
  (ej. e-commerce de moda/cosmetica) — el duotono destruye esa informacion.
- Si va a colocarse texto encima de la imagen, verificar que el contraste
  entre los dos tonos elegidos sea suficiente donde caiga el texto.

## Variantes

- Dos tonos planos (mapeo binario sombra/luz).
- Mapeo continuo estilo Spotify (gradiente de 2 colores en vez de 2 bloques).

## Tokens requeridos

`--duotone-shadow`, `--duotone-highlight`.

## Soporte de navegador

Los filtros SVG (`feColorMatrix`, `feComponentTransfer`) tienen soporte
amplio en navegadores modernos; sin gaps criticos documentados, a diferencia
de otros patrones de este eje.

## Contraste y WCAG

Si hay texto superpuesto a la imagen duotono, el contraste debe verificarse
contra AMBOS tonos del duotono (sombra y luz), no solo contra el tono
dominante — el texto puede caer sobre cualquiera de las dos zonas segun el
contenido de la foto.

## Coste de mantenimiento

Bajo-medio — el filtro se aplica una vez por asset (no por instancia), pero
si cambian los tokens de marca, cada imagen ya procesada debe regenerarse.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Using SVG to Create a Duotone Effect on Images — CSS-Tricks](https://css-tricks.com/using-svg-to-create-a-duotone-image-effect/)
