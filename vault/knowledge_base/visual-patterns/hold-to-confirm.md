---
id: VP-019
name: Hold-to-Confirm (friccion proporcional + deshacer)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [destructive, settings, admin]
  excluded_from: [landing, hero, product-tour, checkout, auth]
  min_expressiveness: restrained
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que una accion destructiva exija intencion sostenida y ofrezca vuelta atras, sin un dialogo modal extra"
---

# VP-019 — Hold-to-Confirm

## Eje

Interaccion (E1) — confirmacion por pulsacion sostenida.

## Tecnica (sin codigo)

El boton destructivo no actua al pulsar: actua al **mantener** la pulsacion
durante un tiempo fijo. Un relleno avanza de forma lineal mientras se mantiene,
asi el progreso que se ve es exactamente el tiempo que falta.

Contrato observado en REF-KITCHEN-001 (OBSERVED):

1. **Duracion fija y lineal** (1600 ms en la fuente). Lineal, porque el relleno
   es un reloj y un reloj con easing miente sobre el tiempo restante.
2. **Soltar antes deshace el relleno con rapidez** (180 ms, ease-out). La
   cancelacion tiene que verse; desaparecer de golpe parece un fallo.
3. **Cancelan**: soltar, alejar el puntero mas de ~8 px fuera del boton, perder
   el foco, perder la captura del puntero y pasar a `disabled`.
4. **Solo el boton principal** del raton inicia la pulsacion.
5. **Teclado con paridad**: Enter o Espacio mantenidos inician la pulsacion, la
   repeticion de tecla se ignora y soltar la tecla cancela.
6. **Estado accesible**: `aria-busy` refleja que se esta manteniendo; el
   contenido decorativo del relleno esta oculto a tecnologias de apoyo.
7. **La callback recibe el modo de entrada** (teclado o puntero), para medir y
   para elegir el foco posterior.
8. **Despues de confirmar**: estado "confirmado" visible y, en el flujo de la
   fuente, un aviso con **deshacer temporizado** antes de cerrar.

## Cuando usar

- Borrados y acciones irreversibles de coste medio que hoy se resuelven con un
  modal "¿Seguro?" que la gente acepta sin leer.
- Superficies de administracion o ajustes donde la accion se repite y un modal
  por cada una seria peor.

## Cuando NO usar

- Acciones frecuentes y baratas: la friccion se vuelve castigo.
- Acciones de coste alto (borrar una cuenta, transferir dinero): ahi hace falta
  un resumen de lo que se va a perder (CDIO-09), no solo tiempo.
- Usuarios con temblor o movilidad reducida sin alternativa: debe existir otra
  via (por ejemplo, confirmar en un dialogo) o una duracion configurable
  (WCAG 2.5.1 / 2.2.1 en espiritu: no depender de una sola forma de gesto
  sostenido).
- Como sustituto del deshacer: la pulsacion reduce errores, el deshacer los
  corrige; uno no reemplaza al otro.

## Movimiento reducido (equivalente, no ausente)

El relleno no anima: el boton muestra el estado de pulsacion y el tiempo sigue
corriendo igual. La friccion (mantener) se conserva; solo desaparece el
movimiento. `aria-busy` y el estado final no cambian.

## Soporte de navegador

Universal: Pointer Events con captura del puntero y eventos de teclado. Tactil:
evitar el menu contextual de pulsacion larga del sistema en el boton.

## Contraste y WCAG

El texto debe seguir legible sobre el relleno en cualquier punto del avance
(medir el peor punto: texto encima del borde del relleno). El anillo de foco
debe ser visible. El aviso de deshacer necesita un tiempo suficiente y
anunciarse de forma educada.

## Coste de mantenimiento

Medio: hay que probar las seis cancelaciones, no solo el camino feliz.

## Evidence

Investigacion: REF-KITCHEN-001 componente 5. Sin implementacion propia todavia.
La duracion del deshacer es UNKNOWN en la fuente.

## Fuentes

- https://www.dqnamo.com/experiments/hold-to-confirm (solo principios; sin licencia declarada).
