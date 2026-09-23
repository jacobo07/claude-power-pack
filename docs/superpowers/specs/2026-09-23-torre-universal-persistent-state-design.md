---
title: Torre Universal — rebanada vertical del Constitutive Baseline Ratchet sobre PERSISTENT_STATE
date: 2026-09-23
status: DESIGN — aprobado por el Owner (7 secciones), pendiente de plan de implementación
tier: T3
covers:
  - torre-universal
  - ucr-cif
  - constitutive-baseline-ratchet
  - resident-institutional-kernel
  - mission-baseline-capsule
  - persistent-state-family
  - baseline-consumption-telemetry
---

# Torre Universal — rebanada vertical sobre la familia PERSISTENT_STATE

## 0. Qué pidió el Owner, literalmente

> «que por ejemplo, si yo avanzo con QuickLease, la próxima vez que yo pida algo en
> InfinityOps, se haga con más ingeniería, más cosas tenidas en cuenta, más completitud, sin
> necesidad de que yo pida cada cosa»

En el dataset fuente eso tiene un nombre propio y **no** es el flywheel universal: es el
**Constitutive Baseline Ratchet**. Su granularidad no es «universal», es **familia de sistema**.
QuickLease e InfinityOps no comparten dominio; sí comparten familias — CRUD con estado
persistente · superficie web con efectos · integración con servicio externo · migración de
esquema. La herencia viaja por la familia, no por el proyecto.

## 1. Procedencia y qué NO se afirma

Fuente: `C:\Users\User\Downloads\Dataset Claude Power Pack Universal Construction Ratchet &
Compounding Intelligence Fabric 1 (1).txt` — 3.086.894 bytes, 167.842 líneas.

**Medición, no estimación:** el tokenizador del propio harness devolvió 62.249 tokens para 9.000
líneas ⇒ ≈1,16 M tokens frente a una ventana de 1 M. El fichero no cabe entero y retenerlo entero
es aritméticamente imposible. Se leyeron **líneas 1–40.200 (24%)** en orden, destilando a disco
tras cada bloque:

- `UCR-CIF-destilacion.md` — UCR-CIF v1 + v2, UC-01…UC-15, Protocolo de Ejecución, HIC-OAR
- `UCR-CIF-destilacion-2.md` — IFC-RLAAS, UFIA-EBF, corpus KME/EssentialsX/LuckPerms, **UBC**
- `UCR-CIF-destilacion-3.md` — Constitutive Baseline Ratchet, USIFB, Fable 5, SEEIP, UDFLL, RCFC

**Líneas 40.200–167.842 no leídas.** Este diseño no afirma nada sobre ese 76%. Si un mecanismo
descrito allí contradice lo de abajo, gana el dataset y este spec se corrige.

Hallazgo de estructura relevante: las líneas 60.381–63.920 son documentación de terceros
(Codex/PDF/DOCX) pegada al fichero, no material del Owner.

## 2. Decisiones del Owner tomadas en el brainstorming

| Pregunta | Respuesta |
|---|---|
| Primera familia de sistema | **Estado persistente / CRUD** (`PERSISTENT_STATE`) |
| Alcance de la captura | **Resident Kernel mínimo, host-level** |
| Enfoque | **A — rebanada vertical sobre UNA familia** (frente a backfill-primero o UBC completo) |
| Fuera de alcance | **al backlog**, no descartado |

## 3. Un solo sustrato, no diez fabrics

El §79 del propio dataset prohíbe construir los diez fabrics como silos con sus propios grafos,
registros y detectores. La estancia ya pagó esa factura: 156 módulos importaban limpios, pasaban
sus tests y ningún hook los alcanzaba — incluido el árbitro de ACCEPTANCE de recovery, que nunca
juzgó una recuperación real. De ahí la Liveness Standard, y de ahí que el primer artefacto tenga
que ser un **bucle cerrado con telemetría de consumo**, nunca un registro.

Cinco owners, y nada más:

| Owner | Qué guarda | Estado hoy |
|---|---|---|
| **Institutional System Graph** | familias, instancias, capabilities, autoridad, ciclo de vida | NUEVO |
| **Evidence & Knowledge Plane** | Vault (crece) + UKDL (comprime) + confianza + linaje | EXISTE |
| **Evaluation Plane** | tests, adversarios, mutaciones, contrafactuales | EXISTE (drills, ratchet de mutación) |
| **Baseline & Policy Plane** | el compilador de baseline y la aplicabilidad | NUEVO |
| **Event Stream** | eventos de construcción, fallos, intervenciones del Owner | PARCIAL (hooks) |

Los «fabrics» (UFIA, IFC, USIFB, RCFC, UDFLL…) pasan a ser **modos de análisis** sobre esos cinco
owners. Señal de fallo estructural: si un fabric pide su propia base de datos, se está
convirtiendo en otro silo.

## 4. La unidad: `PERSISTENT_STATE-B<n>`

No existe un baseline global. Existe una **generación versionada por familia**, con un conjunto
constitutivo explícito, y cada entrada nace con su evidencia o no nace.

`B0` **no se inventa**: se backfillea de lo que QuickLease ya demuestre en producción.

Candidatas de la familia, según el dataset (cada una entra sólo si pasa §5):

- identidad de esquema y versión declaradas
- escritura atómica (no hay estado medio observable)
- **supervivencia a reinicio verificada** — no inferida de que el fichero exista
- contención de corrupción: un campo malo no envenena el agregado
- contrato de migración con forward **y** rollback
- `UNKNOWN ≠ ZERO` en lecturas vacías o ausentes
- clave de caché que represente **todas** las dimensiones semánticas de lo cacheado
- autoridad declarada cuando hay más de una representación del mismo hecho

## 5. El gate que convierte un avance en baseline

Cuatro clasificaciones; **sólo C y D ascienden**:

- **A — incidental.** Resolvió un caso. No se generaliza.
- **B — específica del producto.** Correcta aquí, sin significado fuera.
- **C — mejora repetidamente sistemas del mismo tipo.**
- **D — constitutiva.** Construir otra instancia de la familia sin ella sería, objetivamente, una
  regresión de completitud.

La prueba es **la pregunta contrafactual**, barata y falsable:

> ¿Consideraríamos **incompleta** una instancia nueva de esta familia que no tuviera esto?

Sí ⇒ InfinityOps ya no empieza sin ello. No ⇒ queda registrado como B, con su razón, y no
contamina el baseline. Un A o un B registrados son resultado válido del gate, no un fracaso.

Cada promoción registra: evidencia de origen (proyecto, incidente, commit), clasificación,
respuesta contrafactual, y el **Baseline Propagation Set** — IMMEDIATE · RATCHET-ON-TOUCH ·
OPTIONAL MIGRATION — que decide si las instancias existentes se migran ya, al tocarlas, o nunca.

## 6. Resident Institutional Kernel — captura host-level

Pequeño por contrato. **No carga CPP.** Garantiza seis cosas en cualquier repo, esté CPP activo o
no: *capture · identity · provenance · baseline lookup · critical enforcement · writeback*
(`UC-14: UNIVERSAL CAPTURE IS HOST-LEVEL`).

Captura **DISCOVERY EVENTS**, no sólo bugs: fallos de test, excepciones, migraciones fallidas,
fixes sin efecto, hipótesis falsadas, workarounds, **correcciones del Owner** y sorpresas
positivas. Niveles D0–D7: se captura el 100%, se institucionaliza selectivamente. Meter cada error
de compilación en UKDL destruye la señal; ésa es la regla, no una preferencia.

**HR-001 se respeta sin excepción.** El registro del kernel vive bajo `~/.claude`, que es fuente
de extensión: el parche se deja **preparado y verificado para el Owner**, nunca aplicado por el
agente, y nunca se rodea. El entregable incluye, porque el dataset es explícito en que sin
instalación verificada «la promesa de captura universal sería ficticia»:

- el parche de registro, listo para pegar
- un **health check** que diga si el kernel está registrado y vivo
- un **self-test** que conduzca la rama roja (kernel desregistrado ⇒ captura ausente ⇒ gate rojo)
- **detección de instalación rancia**: un kernel registrado con una versión que ya no existe debe
  reportarse como AUSENTE, no como sano

## 7. La cápsula que ve InfinityOps

Al arrancar una misión que toque estado persistente, el Baseline & Policy Plane emite una
**Mission Baseline Capsule** pequeña:

- baseline heredado de la familia, con generación (`PERSISTENT_STATE-B7`)
- capabilities activadas, **cada una con su razón**
- familias de fallo plausibles **para este diff concreto**, no para la familia en abstracto
- contrato de evidencia por claim (qué prueba exige cada afirmación de «hecho»)
- **qué NO aplica y por qué** — la parte que mantiene la cápsula pequeña

Dos reglas no negociables:

- **`APPLICABILITY PRECEDES ACTIVATION`.** No existe «se aplica el baseline universal entero».
- **`FALSE ACTIVATION IS A BUG`.** Activar gobernanza de sistemas distribuidos en una utilidad
  local no es robustez extra: cuesta complejidad, entrega y ruido de contexto, y se mide igual de
  duro que la omisión. `MISSED ACTIVATION IS A BUG` es su gemela.

## 8. La prueba de que funciona

> `A LEARNING IS NOT INSTITUTIONALIZED WHEN IT IS STORED. IT IS INSTITUTIONALIZED WHEN FUTURE
> BEHAVIOR CHANGES BECAUSE OF IT.`

El done-gate no es «el registro existe». Es **telemetría de consumo**, por entrada del baseline:
ofrecida · recuperada · usada · **cambió una decisión** · previno un fallo · falsa activación ·
ignorada. Una entrada sin consumidor no está institucionalizada y se marca como tal.

Dos métricas de aceptación, ambas con objetivo cero:

- **CRR — Completeness Regression Rate.** Construcciones nuevas que arrancan por debajo de la
  mejor completitud ya demostrada de su clase.
- **RFR — Rediscovered Feature Rate.** Veces que el Owner tiene que volver a pedir algo que ya fue
  constitutivo en un sistema equivalente.

**Drill de mutación obligatorio:** se desconecta el compilador de baseline y la cápsula debe dejar
de emitirse, con el gate en rojo sobre su propia aserción. Un verde que nadie ha falsado no prueba
nada — es exactamente la lección de los 156 módulos inalcanzables. Restauración verificada por
hash.

**Control positivo:** una misión que NO toca estado persistente no debe recibir cápsula de esta
familia. Sin ese control, un compilador que activa siempre pasaría todos los tests de activación.

## 9. Fuera de alcance — declarado, al backlog

IFC-RLAAS · RCFC completo · USIFB · UFIA-EBF como fabric propio · los corpus externos
(EssentialsX, LuckPerms, Fable 5, KME) · SEEIP · HIC-OAR · el resto de familias de sistema
(superficie web con efectos, integración externa, migración de esquema) · el UBC completo
multi-familia · la Meta-Ratchet y los Improvement Derivatives de v2.

Todo ello es el destino, nada entra en esta rebanada. Registrado en
`vault/backlog/2026-09-23_torre-universal-out-of-scope.md` con razón por ítem, no descartado.

## 10. Riesgos y lo que este diseño NO promete

- **No promete** que el kernel capture en repos que el Owner nunca abra con Claude Code. La
  captura host-level cubre el host, no el planeta.
- **No promete** que `B0` sea correcto a la primera. Nacerá con evidencia débil y se corregirá
  **por consumo** — la telemetría del §8 es el mecanismo de corrección, no un informe.
- **No promete** nada sobre el 76% del dataset sin leer (§1).
- **Riesgo principal:** que esto se convierta en el silo número once. Mitigación estructural: los
  cinco owners del §3 y la prohibición de base de datos propia por fabric.
- **Riesgo secundario:** falsa activación. Mitigación: se mide como bug, con el control positivo
  del §8.

## 11. Done-gate de esta rebanada

Todos, o no está hecho:

1. `PERSISTENT_STATE-B0` existe con ≥1 entrada promovida por el gate del §5, con su evidencia de
   origen real en QuickLease y su respuesta contrafactual escrita.
2. El Resident Kernel captura DISCOVERY EVENTS en un repo sin CPP, demostrado en vivo — no
   inferido de que el fichero de log exista.
3. El parche de `~/.claude` está preparado, con health check, self-test y detección de instalación
   rancia. **Aplicado por el Owner, nunca por el agente** (HR-001).
4. Una misión real en InfinityOps recibe una Mission Baseline Capsule derivada de evidencia de
   QuickLease, y la telemetría registra al menos un evento **«cambió una decisión»**.
5. El control positivo pasa: una misión sin estado persistente no recibe esta cápsula.
6. El drill de mutación va rojo al desconectar el compilador, y la restauración se verifica por
   hash.
7. `python modules/liveness/reachability.py` no nombra ningún módulo nuevo inalcanzable.

Nada de lo anterior es «documentado». Cada punto es una observación.
