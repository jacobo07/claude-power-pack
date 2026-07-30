---
id: VP-011
name: Animated Grainy Texture
type: pattern
domain: visual-patterns
status: active
---

# VP-011 — Animated Grainy Texture

No es texto — es tratamiento de fondo. Comparte tecnica base (ruido SVG) con
[[grainy-gradient-background]] (VP-015, D2); esta entrada es la variante
ANIMADA, esa es la variante estatica.

## Eje

Movimiento (B3)

## Tecnica (sin codigo)

Filtro SVG `feTurbulence` (genera ruido Perlin sin imagen de entrada) o un
gradiente CSS abusado para producir estatica, superpuesto a un fondo via
`mix-blend-mode: overlay`, con `background-position` animado en loop para que
el grano parezca "vivo" en vez de una textura fija.

## Cuando usar

- Fondo de seccion hero donde un color/gradiente plano se siente
  demasiado "digital" y se busca una sensacion mas fisica/analogica sin usar
  una fotografia.

## Cuando NO usar

- Detras de texto de lectura — el ruido animado compite con la fijacion
  ocular necesaria para leer.
- Multiples instancias simultaneas en la misma vista — cada capa animada
  suma coste de repintado.

## Variantes

- Ruido estatico (sin animacion) — ver [[grainy-gradient-background]] (D2).
- Ruido animado (`background-position` shift en loop).

## Tokens requeridos

`--noise-opacity`, `--noise-blend-mode`.

## Soporte de navegador

`feTurbulence` (filtros SVG) tiene soporte amplio en navegadores modernos;
`mix-blend-mode` igualmente amplio. Sin gaps criticos documentados — el
riesgo aqui es de RENDIMIENTO, no de compatibilidad.

## Contraste y WCAG

Bajo si se mantiene sutil (opacidad baja) y no hay texto encima; si hay
texto superpuesto al ruido animado, verificar que el `mix-blend-mode` no
reduzca el contraste del texto por debajo del umbral AA en movimiento.

## Coste de mantenimiento

Medio — `feTurbulence` animado o gradientes de ruido pueden ser costosos en
rendimiento si se aplican a multiples elementos grandes a la vez; requiere
perfilar en dispositivos de gama baja antes de shippear.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Grainy Gradients — CSS-Tricks](https://css-tricks.com/grainy-gradients/)
- [Animated Grainy Texture — CSS-Tricks](https://css-tricks.com/snippets/css/animated-grainy-texture/)
- [Making Static Noise From a Weird CSS Gradient Bug — CSS-Tricks](https://css-tricks.com/making-static-noise-from-a-weird-css-gradient-bug/)
