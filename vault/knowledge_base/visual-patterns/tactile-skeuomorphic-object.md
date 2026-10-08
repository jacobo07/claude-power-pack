---
id: VP-027
name: Tactile Skeuomorphic Object (boton por capas, cassette, cartas)
type: pattern
domain: visual-patterns
status: active
provenance: REF-KITCHEN-001
evidence_level: research
---

# VP-027 — Tactile Skeuomorphic Object

## Eje

Superficie (D5) — controles que imitan un objeto fisico.

## Tecnica (sin codigo)

Tres estudios de REF-KITCHEN-001 comparten una idea: el control se construye
como un objeto con capas fisicas, y la informacion sigue estando en el
contenido, no en la ilustracion.

**A. Boton tactil.** Cara con forma, borde firme y profundidad que se comprime
al pulsar, construidos capa a capa (OBSERVED). Valores de presion, hover y
deshabilitado: UNKNOWN.

**B. Reproductor de cassette.** Un reproductor de audio con superficie de
control de cassette y bobinas que giran (OBSERVED en la descripcion). Lo
transferible: el componente recibe una **pista de subtitulos WebVTT** ademas del
audio, y muestra tiempo transcurrido y total (OBSERVED). Semantica de
reproducir/pausar/buscar, teclado y bobinas con movimiento reducido: UNKNOWN.

**C. Cartas.** Proporcion 5:7 y tipografia escalada con el ancho. Los indices
de esquina llevan rango y palo, por eso la ilustracion de las figuras es
decorativa (`alt=""`) (OBSERVED). Una mano en abanico que se recorre con hover y
se juega con clic o con un gesto hacia arriba. Camino de teclado para jugar una
carta y movimiento reducido: UNKNOWN.

## Cuando usar

- Productos donde el objeto fisico es la marca o el tema (archivo de audio,
  juego de cartas, editorial de coleccionismo).
- Un unico control protagonista por vista (un boton de continuar en un flujo
  de bienvenida).

## Cuando NO usar

- Sistemas de diseno de producto con muchos controles: un boton tactil entre
  botones planos rompe la jerarquia; o todo el sistema o ninguno.
- Cuando el objeto oculta el control real: un reproductor sin botones con
  nombre accesible, o una mano de cartas sin alternativa de teclado, no es
  utilizable (WCAG 2.1.1). La fuente no documenta ninguno de los dos; quien lo
  implemente debe anadirlos.
- Gestos como unica via (lanzar una carta hacia arriba): necesitan alternativa
  de un solo puntero y de teclado (WCAG 2.5.1).

## Movimiento reducido

Bobinas y abanico: sin rotacion ni desplazamiento continuo; el estado
(reproduciendo, carta seleccionada) se muestra por texto y forma. La fuente no
lo documenta (UNKNOWN): es un requisito de quien implemente.

## Soporte de navegador

Universal (capas con sombras, gradientes y transformaciones; audio HTML con
`track` WebVTT).

## Contraste y WCAG

Los colores de palo de la fuente (rojo y casi negro sobre blanco) deben medirse
en el tamano real del indice de esquina. Los subtitulos (1.2.1 / 1.2.2) son la
parte del cassette que si cumple un criterio; el resto queda por demostrar.

## Coste de mantenimiento

Alto: texturas, estados fisicos y la accesibilidad que la fuente no resuelve.

## Evidence

Investigacion: REF-KITCHEN-001 componentes 1, 4 y 8. Es la entrada con mas
UNKNOWN de la absorcion; no usarla como referencia de accesibilidad.

## Fuentes

- https://www.dqnamo.com/experiments/tactile-button
- https://www.dqnamo.com/experiments/cassette-player
- https://www.dqnamo.com/experiments/playing-cards
  (solo principios; sin licencia declarada).
