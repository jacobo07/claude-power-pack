---
id: VP-023
name: State-Driven Physical Process (proceso fisico que sigue al estado real)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [checkout]
  excluded_from: [landing, hero, auth, destructive]
  min_expressiveness: restrained
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que el final de un pago se sienta como un objeto entregado (un recibo) sin que la animacion invente un estado que el sistema no ha alcanzado"
---

# VP-023 — State-Driven Physical Process

## Eje

Movimiento (B8) — metafora fisica de un proceso con estados reales.

## Tecnica (sin codigo)

Un objeto fisico (en la fuente, una impresora de recibos) representa las etapas
de un proceso: procesando, imprimiendo, completado. El recibo sale de la maquina
cuando el pago se ha confirmado.

Contrato observado en REF-KITCHEN-001 (OBSERVED):

1. **El estado lo decide el padre, no la animacion**. El componente recibe la
   etapa; no avanza por temporizador propio. Es la regla central: una animacion
   de "procesando" con duracion fija fabrica un estado (CDIO-07, colision de
   confianza).
2. **Avance escalonado por defecto** (20 pasos en 1.75 s, lineal), que imita el
   avance mecanico del papel; variante continua con ease-in-out.
3. **Texto de estado vivo** con `role=status` educado: "Procesando tu pedido",
   "Imprimiendo tu recibo", "Pedido completado".
4. **La salida se oculta a tecnologias de apoyo hasta completarse**: el recibo
   a medio imprimir no se lee; el completo si.
5. **Interruptor global de animacion** ademas del movimiento reducido: ambos
   ponen las duraciones a cero.
6. **Componente compuesto** con partes que fallan fuera de su raiz, para que no
   se use una pieza suelta sin el contexto de estado.

## Cuando usar

- Momento final de un pago o pedido, donde el recibo es el contenido real que el
  usuario quiere conservar.

## Cuando NO usar

- Si la etapa no la confirma el sistema de registro: sin estado real no hay
  animacion honesta.
- Procesos que fallan con frecuencia: la metafora necesita un estado de error
  propio (la fuente no muestra uno; UNKNOWN), y sin el el objeto queda a medias.
- Flujos repetidos muchas veces al dia (TPV, back office): 1.75 s por operacion
  es un coste real.
- El importe y los datos del recibo son afirmaciones: deben venir del sistema de
  registro, nunca de un valor de ejemplo (generated-content-needs-an-evidence-gate).

## Movimiento reducido (equivalente, no ausente)

La etapa cambia sin desplazamiento: el recibo aparece completo al llegar a
"completado"; el texto de estado y los anuncios son identicos.

## Soporte de navegador

Universal. El borde dentado del papel con `clip-path: polygon()` tiene soporte
completo en navegadores actuales.

## Contraste y WCAG

El recibo es texto: 4.5:1 sobre la textura del papel, medido en el punto mas
claro de la textura. El icono de exito no puede ser el unico indicador (el texto
"Pedido completado" lo acompana).

## Coste de mantenimiento

Medio: tres etapas, un estado de error que anadir y texturas como recursos.

## Evidence

Investigacion: REF-KITCHEN-001 componente 3.

## Fuentes

- https://www.dqnamo.com/experiments/receipt-printer (solo principios; sin licencia declarada).
