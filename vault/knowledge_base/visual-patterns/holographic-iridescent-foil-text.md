---
id: VP-007
name: Holographic/Iridescent Foil Text
type: pattern
domain: visual-patterns
status: active
---

# VP-007 — Holographic/Iridescent Foil Text

## Eje

Relleno-texto (A7)

## Tecnica (sin codigo)

Gradiente animado multicolor (rosa/azul/verde/amarillo desplazandose) sobre
`background-clip: text`, animando `background-position` en un loop para
simular el cambio de reflejo del foil holografico al moverse la luz.

## Cuando usar

- Marca con posicionamiento premium/coleccionable (edicion limitada, drop,
  NFT-adjacent, gaming de coleccion) donde el efecto "carta holografica" es
  el lenguaje visual esperado por la audiencia.

## Cuando NO usar

- Cualquier contexto donde la legibilidad sostenida importe mas que el
  impacto inicial — la animacion continua fatiga la lectura.
- Marca minimalista/corporativa — el efecto es fuertemente connotado y no es
  neutral.

## Variantes

- Animacion ligada al tiempo (loop automatico).
- Animacion ligada al scroll o al movimiento del cursor (el reflejo "sigue"
  la interaccion, mas fiel a la metafora de foil fisico).

## Tokens requeridos

`--foil-stop-1` .. `--foil-stop-n` (multiples paradas de color),
`--foil-animation-duration`.

## Soporte de navegador

Misma base que Gradient Text — sin gaps de compatibilidad, pero la animacion
continua de `background-position` tiene coste de repintado real en
dispositivos de gama baja.

## Contraste y WCAG

Alto: al ser una animacion continua entre multiples hues, el contraste
contra el fondo varia en el tiempo — un frame puede pasar WCAG AA y el
siguiente no. Requiere verificar el PEOR frame del ciclo, no un frame
promedio. Debe respetar `prefers-reduced-motion` (congelar en un frame
valido, no simplemente detener a mitad de transicion).

## Coste de mantenimiento

Alto — animacion continua + gradiente de muchos stops implica mas superficie
de verificacion de contraste (todo el ciclo, no un estado) y mas coste de
rendimiento que cualquier otro patron del eje A.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [CSS Holographic Effect: Iridescent and Chrome — Effect.Labs](https://effect-labs.com/en/pages/blog/effet-holographique-css.html)
- [Iridescent foil letterpress effect — CodePen](https://codepen.io/electrifried/pen/REjQdM)
