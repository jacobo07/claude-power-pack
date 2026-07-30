---
id: VP-003
name: Metallic/Chrome Text
type: pattern
domain: visual-patterns
status: active
---

# VP-003 — Metallic/Chrome Text

## Eje

Relleno-texto (A3)

## Tecnica (sin codigo)

Gradiente multi-stop (4-6 paradas) sobre `background-clip: text` que imita
los highlights especulares de una superficie metalica — alterna zonas claras
(reflejo) y oscuras (sombra del metal) en vez de una transicion suave de 2
tonos.

## Cuando usar

- Wordmark premium de una sola palabra donde la marca quiere transmitir
  "material fisico" (oro/plata/cobre) en vez de color plano.
- Contextos de lujo, coleccionable o edicion limitada.

## Cuando NO usar

- Mas de una palabra o frases largas — el efecto exige que el ojo perciba
  el conjunto como un objeto, no como texto corrido.
- Marca con posicionamiento minimalista/tech-plano — el metalico compite con
  esa identidad en vez de reforzarla.

## Variantes

Oro, plata, cobre, bronce — cada uno con su propia paleta de 4-6 stops.

## Tokens requeridos

`--metal-[oro|plata|cobre]-base`, `--metal-[...]-highlight`,
`--metal-[...]-shadow` (minimo 3 stops nombrados, no interpolados a mano).

## Soporte de navegador

Misma base que Gradient Text (VP-002): requiere prefijo `-webkit-` en Safari.
Sin gaps adicionales — es una composicion de gradiente, no una API nueva.

## Contraste y WCAG

Alto riesgo: los stops "highlight" del metalico suelen ser casi blancos y los
"shadow" casi negros dentro del MISMO bloque de texto — verificar el punto
mas claro contra el fondo, igual que en VP-002, pero con margen mas ajustado
porque hay mas stops extremos.

## Coste de mantenimiento

Medio — afinar 4-6 stops por variante de metal a mano es propenso a drift
visual; cualquier cambio de tono de marca obliga a re-tunear toda la rampa,
no solo 2 valores.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Metallic Text Effect CSS Generator — design.dev](https://design.dev/tools/metallic-effect-generator/)
- [8 Amazing Metallic Effects Built With CSS & JavaScript — Speckyboy](https://speckyboy.com/metallic-effects-css-javascript/)
