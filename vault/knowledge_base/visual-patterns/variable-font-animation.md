---
id: VP-009
name: Variable Font Weight/Width Animation
type: pattern
domain: visual-patterns
status: active
---

# VP-009 — Variable Font Weight/Width Animation

## Eje

Movimiento (B1)

## Tecnica (sin codigo)

Animar `font-variation-settings` (ejes `wght`, `wdth`, u otros ejes custom
de la fuente) via transicion CSS o ligado a scroll, para que el wordmark
cambie de peso/anchura en tiempo real sin cambiar de archivo de fuente.

## Cuando usar

- Marca que quiere una identidad "cinetica" — el wordmark respira/reacciona
  al hover, al scroll o a la carga de la pagina.
- Sistemas de marca type-driven donde la tipografia ES el activo principal
  (mas alla del logo grafico).

## Cuando NO usar

- La fuente de marca actual NO es una variable font — este patron no
  funciona sobre una fuente estatica; verificar los ejes disponibles del
  archivo ANTES de disenar la animacion, no asumir que "toda fuente moderna
  es variable".
- Texto de lectura extensa — el cambio de peso en movimiento distrae de la
  lectura sostenida.

## Variantes

- Solo eje de peso (`wght`).
- Peso + anchura combinados (`wght` + `wdth`).
- Ligado a scroll vs ligado a hover/interaccion puntual.

## Tokens requeridos

`--font-family-variable` (debe apuntar a un archivo variable real),
`--weight-min`, `--weight-max`, `--width-min`, `--width-max`.

## Soporte de navegador

Los navegadores modernos (Chrome, Firefox, Safari, Edge) soportan carga y
animacion de variable fonts; el riesgo real no es de navegador sino de
ASSET — muchas fuentes de marca licenciadas solo incluyen el corte estatico,
no la version variable, y hay que verificarlo antes de comprometer el
patron.

## Contraste y WCAG

Bajo riesgo de contraste (no cambia color); el riesgo es de movimiento —
respetar `prefers-reduced-motion` si la animacion es continua o de gran
amplitud.

## Coste de mantenimiento

Alto — depende de tener una fuente variable con los ejes correctos
licenciada y cargada; si la marca cambia de tipografia a una no-variable, el
patron completo deja de ser viable y no hay fallback parcial razonable.

## Evidence

No implementado aun en un proyecto del Owner — patron de investigacion,
pendiente de primera implementacion.

## Fuentes

- [Variable Fonts and Animation – What Is The Potential? — TYPE01](https://type-01.com/variable-fonts-and-animation-what-is-the-potential/)
- [Embleme: Type-Driven Brand System in a Variable Font — Otherwhere Collective](https://otherwherecollective.com/projects/embleme/)
