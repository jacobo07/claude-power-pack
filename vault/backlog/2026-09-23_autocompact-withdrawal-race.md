# Backlog — entrega del `/compact`: la carrera de la retirada (2026-09-23)

El Owner reportó que la línea `/compact focus on ...` no se tecleó sola. La investigación
cerró un defecto y dejó otro abierto: **el que causó su queja sigue sin medir.** Registrado
aquí para hacerlo próximamente, no como nota suelta en una conversación que se compacta.

## Estado: qué está cerrado y qué no

**CERRADO — commit `f6fe4ab`.** Observabilidad asimétrica del daemon. Los tres caminos de
fallo escribían al ledger; los dos de éxito, no. El ledger era estructuralmente incapaz de
mostrar un compact entregado: sólo podía responder «nunca». Arreglado con `compact_dispatched`
y `foreground_dispatched` — dos eventos distintos a propósito, porque fundirlos dejaría al
ledger sin poder decir cuál de los dos caminos tecleó, y el de primer plano es el que el
2026-09-18 escribió en la sesión de un tercero.

Gate `tools/test_autocompact_ledger_symmetry.py` 4/4 · mutación → 3/4 rojo en la aserción
correcta · restauración SHA-256 idéntica · 0 bytes no-ASCII · 0 errores de parseo. El gate
encontró en su primera corrida un segundo camino sin ledger (`Send-Enter:279`) que la lectura
manual del fichero no vio.

**PENDIENTE DEL OWNER — `vault/staged/2026-09-23_deploy_autocompact_ledger.md`.** HR-001: el
fichero vivo está bajo `~/.claude/hooks/` y el agente no lo escribe. Medido: el espejo vivo
tiene **cero líneas propias**, así que copiar es seguro y no hace falta fusionar. **El arreglo
no surte efecto hasta que se despliegue y el daemon vuelva a arrancar** — uno ya en marcha
sigue ejecutando el fichero que cargó.

**ABIERTO — lo de abajo.**

## El defecto que queda: por qué se retiró esta entrega

```
12:45:16  REQUESTED  typed=[/compact focus on Torre Universal O1 measured, phase 4 auditor pending]
12:45:16  deferred by extension            reason=status-busy
12:47:10  WITHDRAWN  -- last assistant line no longer the requested one (now state=wait)
12:55:12  REFUSED    expected=[/compact...] -- last assistant line never matched
```

La línea pedida y la emitida eran **idénticas** — el `typed=[...]` del log lo prueba. Así que
el fallo no está en el texto.

`Get-ExpectState` (`hooks/auto-compact-sendkeys-daemon.ps1:215`) devuelve `ok` sólo si la
última línea del asistente es exactamente la esperada (`-ceq`); si no, `wait`. La retirada
(`:373`) dispara con `$now.state -ne 'ok'`, **antes** de comparar la línea. Entre 12:45 y
12:47 algo dejó de ser la última línea del asistente.

### Hipótesis — no confirmada, y es lo primero que hay que falsar

El protocolo puede estar pidiéndose algo imposible a sí mismo. BL-0003 exige que el modelo
**emita** la línea `/compact` en su siguiente respuesta; el inbox espera a que la sesión quede
`idle` antes de teclear; y cualquier salida posterior del asistente reemplaza esa línea como
«última». Si el turno que completa la cadena es también el que la invalida, la carrera se
pierde siempre que la extensión tarde en reportar `idle`.

Es la forma de *«un estímulo que destruye la precondición de la que depende»* de
`instrument-before-claim.md`, aplicada a una entrega en vez de a una medición.

**Contraevidencia que la hipótesis debe explicar:** a las 11:02:26 del mismo día **sí** se
entregó, 24 s después de la petición. Una hipótesis que predice fallo siempre no explica ese
éxito. La diferencia plausible es el tiempo hasta `idle` (24 s frente a 1 m 54 s), pero eso
tampoco está medido.

### Primer paso, concreto

1. Leer `Get-LastAssistantLine` y decidir **qué cuenta como «línea del asistente»** cuando el
   turno lleva texto antes de la orden. El turno del 12:45 tenía un párrafo antes de la línea.
2. Comparar los dos casos del mismo día —el que se entregó (11:02) y el que se retiró
   (12:45)— sobre el transcript real, no sobre el log. Dos sujetos reales, misma sesión, mismo
   día: es el contraste más barato disponible y no hay que fabricarlo.
3. Sólo entonces decidir el arreglo. Candidatos, ninguno elegido: comparar por **prefijo**
   en vez de por línea exacta (el daemon ya soporta `expectPrefix`) · anclar la expectativa al
   **turno** y no a la última línea · o no retirar mientras el estado sea `wait` dentro de un
   plazo corto, distinguiendo «cambió a otra cosa» de «aún no ha aparecido».

### Cómo se sabrá que está arreglado

Una fila `compact_dispatched` en `~/.claude/state/gsd-autorun-ledger.jsonl` en el siguiente
cruce de contexto. **Esa fila no puede existir hoy**, y ésa es precisamente la razón por la
que una consulta sobre el ledger concluyó —falsamente— que la entrega nunca había funcionado.
El arreglo de `f6fe4ab` es lo que hace medible a este otro.

## Nota de prioridad

Va antes que O2 (correr HR-NOVELTY-001 sobre el Constitutive Baseline Ratchet) **sólo si el
Owner sigue perdiendo cruces de contexto**. El coste de no arreglarlo es una línea que el
Owner teclea a mano cada vez; el coste de no hacer O2 es construir sobre una clasificación sin
verificar. Ninguno es P0 frente al otro por evidencia: lo decide cuánto molesta en la práctica.

## Trampa de instrumento, ya pagada aquí

Al consultar este ledger, buscar `dispatched|confirmed` devuelve **cero** para el camino
compact, porque ése es el vocabulario del camino *resume*. El cero es UNKNOWN, no evidencia.
Antes de afirmar nada sobre entregas, leer también `~/.claude/hooks/auto-compact-daemon.log`,
que es donde vivían los éxitos.
