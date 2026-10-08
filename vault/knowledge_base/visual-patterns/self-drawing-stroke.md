---
id: VP-024
name: Self-Drawing Stroke (firma y loader de trazo que se resuelve)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, hero, product-tour, onboarding]
  excluded_from: [checkout, auth, form, destructive, dashboard]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que una marca (firma, logo) se dibuje o espere con el trazo de la propia marca y se resuelva solo cuando el trabajo termina"
---

# VP-024 — Self-Drawing Stroke

## Eje

Movimiento (B9) — trazo SVG que se dibuja.

## Tecnica (sin codigo)

El trazo se normaliza a longitud 1 (`pathLength=1`), de modo que un patron de
guiones de longitud 1 desplazado de 1 a 0 lo dibuja de principio a fin sin
medir la ruta. Dos variantes absorbidas de REF-KITCHEN-001 (OBSERVED):

**A. Firma (una vez).** Se dibuja al montar en ~2.8 s con una curva suave
propia. Es una imagen: `role=img` y una etiqueta que dice que representa.

**B. Loader de marca que se resuelve.** Mientras carga, un segmento corto de
trazo recorre el contorno del logo en bucle lineal sobre un contorno tenue
(~18 % de opacidad). Al llegar la senal real de completado, el bucle **cierra el
contorno en lugar de cortarse**, despues aparece el relleno, y una callback de
"terminado" se dispara una sola vez (con un tiempo maximo de seguridad). Ancho y
alto son estables desde el primer render para no mover la maquetacion. Es un
estado: `role=status` con etiqueta.

## Cuando usar

- A: firma de autor, pie de carta, cierre de una historia de marca.
- B: espera de duracion desconocida en una superficie de marca (arranque de app,
  primera carga), donde el logo ya estaria en pantalla.

## Cuando NO usar

- B como indicador de progreso de una tarea larga: no dice cuanto falta; para
  esperas de mas de unos segundos hace falta progreso real.
- B resuelto por temporizador en lugar de por la senal de completado: fabrica un
  estado (CDIO-07).
- A repetido en cada visita a la misma pagina: la segunda vez es espera, no
  expresion.
- Logos con muchos subtrazos: un solo trazo normalizado no representa bien
  marcas compuestas (la fuente usa una sola ruta para el bucle).

## Movimiento reducido (equivalente, no ausente)

A: el trazo aparece completo (duracion casi nula). B: se muestra la marca
rellena y se dispara "terminado" de inmediato; el estado y su anuncio son los
mismos.

## Soporte de navegador

Universal: `pathLength`, `stroke-dasharray` y `stroke-dashoffset` en SVG estan
soportados en todos los navegadores actuales.

## Contraste y WCAG

El trazo es contenido grafico: 3:1 contra el fondo (1.4.11) si identifica la
marca. El contorno tenue del loader es decoracion. WCAG 2.2.2 no aplica a A
(dura menos de 5 s); B debe resolverse o mostrar progreso.

## Coste de mantenimiento

Bajo para A; medio para B (fases, tiempo de seguridad, disparo unico).

## Evidence

Investigacion: REF-KITCHEN-001 componentes 13 y 14. Duraciones por defecto del
loader UNKNOWN.

## Fuentes

- https://www.dqnamo.com/experiments/signature
- https://www.dqnamo.com/experiments/logo-trace-loader
  (solo principios; sin licencia declarada).
