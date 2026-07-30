---
id: VP-014
name: Glassmorphism Brand Card
type: pattern
domain: visual-patterns
status: active
---

# VP-014 — Glassmorphism Brand Card

Nota: `CDIO-06-aesthetic-families.md` menciona el glassmorphism como
posible familia estetica a nivel evaluativo (juzga si una superficie encaja
en esa familia); esta entrada es la implementacion CONCRETA que faltaba en
el vault — no duplica CDIO-06, la completa.

## Eje

Superficie-textura (D1)

## Tecnica (sin codigo)

`backdrop-filter: blur(8px-20px)` sobre un panel con fondo translucido
(`rgba()` de baja opacidad) y un borde de 1px casi transparente que simula el
canto de un cristal fisico. El panel debe estar sobre un fondo con
suficiente variacion visual (gradiente o imagen) para que el blur sea
perceptible.

## Cuando usar

- Tarjetas/paneles de marca colocados sobre un fondo con gradiente o imagen
  de marca — el efecto necesita contenido detras para tener sentido visual.

## Cuando NO usar

- Sobre fondo solido/plano — sin variacion detras, el blur no aporta nada y
  solo anade coste de rendimiento.
- Multiples paneles glass apilados o muy grandes en la misma vista — el
  coste de rendimiento de `backdrop-filter` escala con el area y el numero
  de instancias.

## Variantes

- Borde hairline sutil vs borde con gradiente de marca.
- Blur bajo (~8px, mas "vidrio esmerilado" ligero) vs blur alto (~20px+, mas
  opaco/dificil de leer el fondo).

## Tokens requeridos

`--glass-bg` (color rgba base), `--glass-border`, `--glass-blur`.

## Soporte de navegador

Amplio en Chrome, Firefox y Edge; Safari requiere el prefijo
`-webkit-backdrop-filter` — omitirlo deja el panel SIN blur en Safari (no
degrada con gracia a un fondo solido, simplemente no aplica el efecto).

## Contraste y WCAG

El contenido detras del panel es, por diseno, IMPREDECIBLE (gradiente
animado, imagen de usuario, etc.) — el contraste del texto DENTRO de la
tarjeta debe verificarse contra el PEOR CASO de fondo posible, no contra el
fondo de referencia usado en diseno. Anadir un `background-color` de
respaldo con opacidad suficiente si el fondo real no esta controlado.

## Coste de mantenimiento

Medio — `backdrop-filter` es costoso en rendimiento sobre scroll largo con
muchos paneles simultaneos (cada uno recalcula el blur del contenido
detras); requiere el prefijo Safari y prueba de contraste en cada fondo
real donde se use.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Master Glassmorphism with CSS filters — Trevor Saint](https://trevorsaint.uk/insights/master-glassmorphism-with-css-filters/)
