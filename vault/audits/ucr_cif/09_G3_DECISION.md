---
title: UCR-CIF — G-3 resuelto: el carril advisory no puede portar una premisa de misión
date: 2026-09-23
status: MEASURED — evidencia de producción observada, no corrida sintética
instrument: scratchpad/g3_measure.py sobre ~/.claude/logs/hook-dispatcher-errors.log (27,8 MB, 346.329 líneas)
subject_identity: hook-dispatcher.js sha256 7EE00DAD25EB428DD9076B818668A1AAA39C75618A8CA4A745EAB382952F418F -- copia viva y copia del repo VERIFICADAS IDENTICAS
decides: G-3 (CRITICAL) de 05_PHASE4_PLAN_AUDIT.md · E4 del spec R1 §13
---

# G-3 — decidido con 815 abandonos reales

## 0. Por qué evidencia de producción y no un drill

El host estaba entre **0,2 % y 9,6 % de RAM libre** durante toda la sesión. Conducir el
dispatcher para medirlo habría hecho al instrumento consumir el recurso que mide — el mismo
defecto que `05_PHASE4_PLAN_AUDIT.md` §G-2 le reprocha al harness de FD-04. El log de errores ya
contiene ocho días de la observación exacta que hacía falta, gratis.

**Identidad del sujeto verificada antes de citar nada:** la copia viva
(`~/.claude/hooks/hook-dispatcher.js`) y la del repo son **byte a byte idénticas**. Esta estancia
tiene un split-brain documentado entre ambas, así que la comprobación no era ceremonia: sin ella,
cada número de línea de abajo podría describir un fichero que no corre.

## 1. Lo medido

Ventana **2026-09-15T13:57Z → 2026-09-23T14:37Z**. `CHAIN-DEADLINE-ABANDONED`: **815 eventos**.

| cadena | eventos | tras deadline | antes del pool |
|---|---:|---:|---:|
| **`UserPromptSubmit-chain`** | **639** | 446 | 193 |
| `SessionStart-chain` | **69** | 46 | 23 |
| `PreToolUse-Edit-chain` | 45 | 29 | 16 |
| `PreToolUse-Bash-chain` | 25 | 17 | 8 |
| drills sintéticos | 35 | — | — |
| `PreToolUse-Read-chain` | 2 | 2 | 0 |

**RAM libre en el momento del abandono (n=730): mínimo 0,2 % · mediana 8,2 % · máximo 28,2 %.**

## 2. El hallazgo que decide G-3

> **`gsd_x_tier` —el dueño vivo del Project Birth— aparece NOMBRADO como abandonado en 215 de
> los 639 abandonos de su cadena: el 33,6 %.**

Y ese 33,6 % es un **suelo, no una cuenta**. La rama `before pool` (193 eventos) no nombra a
nadie: registra un número. Skippeó **965 slots de miembro sin nombrar ninguno**, y `gsd_x_tier` es
uno de los cinco miembros no críticos de esa cadena. Así que la pérdida real del dueño vivo está
entre **215 (nombrado) y ~408 (nombrado + no nombrado) de 639**.

Dos consecuencias que no son opinión:

1. **El efecto «Project Birth» que el handoff da por vivo es vivo en MECANISMO y poco fiable en
   ENTREGA.** Ambas cosas son ciertas a la vez. G-1 sigue en pie —no se construye un segundo
   dueño— y G-3 añade que la entrega del único dueño se cae en un tercio largo de los casos donde
   la cadena se pasa de tiempo.
2. **La mediana de RAM libre al abandonar es 8,2 %, pero el máximo es 28,2 %.** Esto **no** es
   sólo un artefacto de inanición: ocurre también en un host cómodo. No se arregla liberando
   memoria.

## 3. Por qué las cuatro arquitecturas candidatas se reducen a una

| opción | veredicto | razón medida |
|---|---|---|
| **D** — el advisory basta; la cápsula no es premisa | **RECHAZADA** | el §11.b.4 del diseño exige que la cápsula cambie una decisión de arranque. Un canal que pierde su portador en ≥33,6 % de los abandonos no porta una premisa. «Project Birth heredó madurez» sería una afirmación sobre un canal que se cae en silencio |
| **B** — mínimo acotado síncrono dentro de `UserPromptSubmit` | **RECHAZADA** | el coste ligante **no es lógica de hook**: son SEIS SPAWNS DE PROCESO (`hook-dispatcher.js:745-750`), con `node -e "0"` a 965 ms y `python -c pass` a 2–4 s en disco saturado. Añadir trabajo síncrono añade spawns a una cadena que ya consume su presupuesto entero. IC-009 lo prohíbe como primer reflejo, y el propio fichero lo dice: *«A deadline cannot make a spawn cheap»* |
| **A ingenua** — precomputar en `SessionStart` | **RECHAZADA** | **`SessionStart-chain` abandona 69 veces**, incluido `session_start_hub.js` hoy a las 14:37:08. No es puerto seguro: mover el productor allí **mueve el acantilado**, que es exactamente lo que `:979-981` advierte de subir la deadline |
| **A′ + C** — productor fuera de banda + estado degradado explícito | **ADOPTADA** | única que saca el cómputo de **toda** cadena con deadline de latencia, y única que hace distinguible el fallo |

## 4. La decisión

**A′ — el productor de la cápsula no corre en ninguna cadena sujeta a deadline de latencia.**
Escribe un artefacto persistido desde un punto del ciclo de vida que no está en el camino crítico
del prompt (cierre de sesión / writeback / invocación explícita). `UserPromptSubmit` **sólo lee**.

La razón es la que el propio dispatcher ya aprendió y escribió en `:979-981`:

> *«A budget is a constant and a spawn's cost is a function of host load, so raising
> CHAIN_DEADLINE_MS only moves the cliff. Not spawning is the fix that holds at any load.»*

Una lectura de fichero dentro del `gsd_x_tier` **ya registrado** no añade ni un spawn. El coste
marginal de la cápsula sobre la cadena caliente pasa a ser el de un `readFileSync`.

**C — la degradación tiene que ser legible por el CONSUMIDOR, no sólo por `logError`.**

Aquí está la mitad de G-3 que nadie había medido (E4 del spec). El dispatcher **sí** distingue el
abandono con clase propia —`CHAIN-DEADLINE-ABANDONED`, greppable, con `hostPressure()`, con
reaping— y está bien diseñado. Pero lo escribe con `logError(...)`, es decir **al log del
dispatcher**. El consumidor —el modelo que recibe el prompt— sólo ve el merge de
`settled[idx]`, y un miembro abandonado simplemente no aporta nada.

> **En la capa del dispatcher, abandonado ≠ silencioso. En la capa del consumidor, abandonado ==
> silencioso.** Observables idénticos.

Es el tercer peldaño de `rules/guard-event-reachability.md` —*un guardia que dispara y no puede
ser oído*— que este mismo fichero cita en `:690`. El dispatcher lo resolvió para su propio
diagnóstico y no para el modelo.

Por tanto la cápsula lleva **estado explícito en su propio artefacto**, y su ausencia se lee del
artefacto, nunca del silencio: `AVAILABLE` · `NOT_APPLICABLE` · `EMPTY_BY_EVIDENCE` ·
`PRODUCER_FAILURE` · `STALE` · `UNKNOWN`. `ABANDONED_BY_DEADLINE` deja de ser una posibilidad del
consumidor porque el consumidor ya no computa: lee. Si no hay fichero, el estado es `UNKNOWN`
—dicho—, no ausencia.

## 5. Qué hace esto falsable (el punto de G-3)

Antes: una cápsula abandonada y una que no tenía nada que decir eran el mismo observable, así que
O4 no podía fallar por la razón correcta. Después:

| mundo | observable del consumidor |
|---|---|
| familia no aplica | `NOT_APPLICABLE` + razón |
| aplica, sin baseline todavía | `EMPTY_BY_EVIDENCE` |
| el productor reventó | `PRODUCER_FAILURE` + timestamp |
| el artefacto es viejo | `STALE` + edad |
| nunca se produjo | `UNKNOWN` |
| todo bien | `AVAILABLE` + generación |

Seis mundos, seis observables. **Ahora O4 puede fallar**, que es el requisito.

## 6. Defecto adyacente encontrado, con ROI acotado

La rama `before pool` (`hook-dispatcher.js:986-988`) registra **un número**:
`pool NOT spawned (N skipped)`. La rama `after` (`:1005-1007`) registra **los nombres**:
`still running: <scripts>`.

Misma clase de evento, dos niveles de observabilidad. Coste medido: **965 slots de miembro
abandonados sin que nadie pueda decir cuáles**, en 193 eventos. Es la asimetría de observabilidad
del §LIV, dentro del propio mecanismo que existe para que un abandono no se lea como un pase
limpio — y es lo que me obligó a dar un rango (215–408) donde debería haber una cuenta.

`restSteps` está en ámbito en esa rama. La reparación es simétrica a la rama que ya funciona.
**HR-001:** el fichero vivo está bajo `~/.claude/hooks/`; el agente **no lo escribe**. Se corrige
la copia del repo y se deja el despliegue preparado para el Owner, igual que
`vault/staged/2026-09-23_deploy_autocompact_ledger.md`.

## 7. Lo que este fichero NO afirma

- **No** mide cuántas veces la cápsula *habría* cambiado una decisión. Eso es O0 + O4.
- **No** afirma que 215 sea la cuenta de pérdidas del dueño vivo. Es el **suelo**; el techo es
  ~408 y la diferencia existe *porque* la rama `before pool` no nombra a nadie (§6).
- **No** decide dónde vive exactamente el productor fuera de banda. Decide que **no** vive en una
  cadena con deadline de latencia, que es lo que G-3 bloqueaba.
- **No** cambia ningún valor de `CHAIN_DEADLINE_MS`. Subir la deadline mueve el acantilado; el
  propio fichero lo midió y lo escribió.

## 8. Error de instrumento propio en esta medición

El primer agrupado se hizo con un patrón que capturaba el **timestamp** en vez del nombre de
cadena, y produjo una tabla de ~500 grupos de tamaño 1 que no significaba nada. Se detectó porque
el resultado era absurdo a simple vista, no porque el instrumento avisara. Rehecho con un regex
anclado en `[<chain>] CHAIN-DEADLINE-ABANDONED`. Cuarta instancia propia del día.
