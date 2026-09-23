# Backlog — Torre Universal, fuera de alcance de la rebanada PERSISTENT_STATE (2026-09-23)

El Owner aprobó las 7 secciones del diseño
`docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md` y ordenó que **todo
lo que queda fuera de alcance vaya al backlog**, no al descarte. Registrado aquí para que el
diferimiento sea honesto y localizable, no una omisión silenciosa (doctrina «sin FAILs
clasificados en el done-gate»).

Procedencia: dataset «Universal Construction Ratchet & Compounding Intelligence Fabric», leído
hasta la línea 40.200 de 167.842 (24%). **Las líneas 40.200–167.842 no están leídas**; ningún ítem
de abajo afirma nada sobre ese 76%, y la lectura restante es ella misma un ítem de backlog.

## Diferido — razón por ítem

| Sistema | Por qué se difiere | Casa real cuando se construya |
|---|---|---|
| **UBC — Universal Baseline Compiler (multi-familia)** | Es el destino, no la primera rebanada. Sin una familia real atravesando dos repos no hay forma de medir `CRR→0` ni `RFR→0`, que son las únicas pruebas que el dataset acepta. Construirlo completo de entrada produce arquitectura sin medición. | Generalización natural del Baseline & Policy Plane de la rebanada, una vez `PERSISTENT_STATE-B<n>` tenga telemetría de consumo real. |
| **Resto de familias de sistema** (superficie web con efectos · integración con servicio externo · migración de esquema) | Mismo motivo: la rebanada existe para probar el mecanismo en UNA familia. Una segunda familia antes de que la primera mida es coste sin evidencia. | Segunda y tercera rebanada, reutilizando el mismo gate A/B/C/D y los mismos cinco owners. Cada una es una generación de baseline nueva, no un sistema nuevo. |
| **IFC-RLAAS** (capital allocation for engineering intelligence) | Decide *dónde* aplicar presión de mejora. Sin baselines de familia con consumo medido no tiene entradas: asignaría capital sobre estimaciones. El propio dataset avisa: `IFC DECIDES WHERE TO APPLY IMPROVEMENT PRESSURE. IT DOES NOT BECOME THE UNIVERSAL EXECUTOR.` | Modo de análisis sobre el Evidence & Knowledge Plane + la telemetría de consumo, nunca un fabric con registro propio (§79). |
| **UFIA-EBF** (failure mechanisms, distillation L0–L9, immunity I0–I9, Failure Genome) | La rebanada ya consume su idea central — «la unidad es el MECANISMO DE FALLO, no el bug» — en las familias de fallo plausibles de la cápsula. El ladder completo y el Failure Genome con `escape mechanism` son un cuerpo propio. | Modo de análisis sobre el Event Stream. UKDL ya es el sustrato de almacenamiento; lo que falta es el ladder de inmunidad. |
| **USIFB** (legitimidad sobre corrección, Epistemic Integrity, Validity-by-Accident, Agent Escape RCA) | Su valor aparece cuando hay suficientes veredictos automáticos que auditar. Con un solo baseline de familia no hay población que juzgar. Su §79 ya está **absorbido** en la rebanada (los cinco owners) — eso era lo urgente. | Modo de análisis sobre el Evaluation Plane. `UNKNOWN is a finding, never PASS` debería llegar antes que el resto. |
| **RCFC completo** (12 funnels, 12 dimensiones, Novelty Reserve 20%, Subtraction Funnel, Funnel Genome) | Es el motor de descubrimiento, no el de herencia. La petición del Owner es herencia. Construir el embudo antes que el trinquete produce hallazgos que nada institucionaliza. | Alimentador del Discovery Event del Resident Kernel, una vez el kernel capture de verdad. |
| **UDFLL** (D0–D7, Concrete Incident Dossier + Universal Learning Record, triple separación) | Parcialmente absorbido: la rebanada usa DISCOVERY EVENT como unidad y los niveles D0–D7 como filtro. Lo diferido son los **dos documentos nunca mezclados** y el Zero Material Discovery Loss Gate. | Formato de salida del Evidence & Knowledge Plane. `NO UKDL ENTRY WITHOUT A CONSUMER` conecta directo con la telemetría de consumo del §8 del spec. |
| **HIC-OAR** (H0–H12, métricas OSR/FDR/AIR/ORR/HIB/OEV, supervisión S5→S0, work-class L0→L7) | Mide la relación humano-agente. Ortogonal a la herencia entre proyectos y con su propio aparato de métricas; meterlo ahora duplica instrumentación. | Modo de análisis sobre el Event Stream, usando las intervenciones del Owner que el Resident Kernel ya captura. H9 (redescubrimiento institucional) es el mismo fenómeno que RFR. |
| **SEEIP / Wii** (`NO BOOT WITHOUT EXPECTED INFORMATION GAIN`, Zero-Boot Engineering, `TWIN ≠ TRUTH`) | Corpus de ingeniería con observación cara. Sus leyes son transferibles pero no gobiernan la herencia de baseline. | Doctrina, no sistema. Candidata a regla global (`~/.claude/rules/`) antes que a módulo. |
| **Corpus externos**: KobiiMapEngine · EssentialsX · LuckPerms · Fable 5 World Demo | Son **donantes de madurez**, no sistemas a construir. Su valor es poblar `B0` de familias futuras con lecciones ya probadas — inútil hasta que exista el mecanismo que las reciba. | Fuente de candidatas para el gate A/B/C/D, una familia a la vez. LuckPerms es el donante natural de la familia `PERSISTENT_STATE` (`CORRECTNESS IS… VALUE + CONTEXT + AUTHORITY + FRESHNESS + LIFECYCLE + EXECUTION ENVIRONMENT`). |
| **UCR-CIF v2**: tres órdenes de compounding · Meta-Ratchet · Improvement Derivatives · Leverage-of-Leverage · Anti-Bureaucracy Ratchet | Es el trinquete sobre el trinquete: un baseline de *cómo de bien aprende CPP*. Requiere que el trinquete de primer orden exista y haya medido algo. | Segunda generación, después de que `CRR` y `RFR` tengan serie temporal. El Anti-Bureaucracy Ratchet es el que debería llegar primero: es el freno, no el acelerador. |
| **Lectura del 76% restante del dataset** (líneas 40.200–167.842) | ≈1,16 M tokens frente a una ventana de 1 M: leerlo entero y retenerlo entero es aritméticamente imposible en una sesión. Se leyó en orden hasta donde entró, destilando a disco. | Continuación por bloques, destilando a `UCR-CIF-destilacion-4.md` y siguientes. Anclas conocidas sin leer: línea 76.677 (tabla de candidatos de macrosistema), 89.813–90.636 (absorción de CodeRabbit, los ocho *Lifts* de la Torre Universal, «Mi decisión»), 113.888 (tabla «Capacidad universal UCR-CIF / qué absorbe de las 100»). |

---

# Segunda pasada — huecos que la taxonomía del dataset no ve

La tabla de arriba está organizada por *sistema del dataset diferido*. Esa taxonomía es de la
fuente y tiene un punto ciego: el propósito del Owner no es un sistema, es un comportamiento. Todo
lo que hace falta para que ese comportamiento ocurra y no es uno de los diez fabrics se cayó por
el hueco. Brainstorming del 2026-09-23; el Owner eligió registrar **A + B + C completos**.

**Disciplina de instrumento:** lo verificado es que el spec y la primera tabla **no contienen**
estos ítems — están escritos en esta sesión. Lo que **no** está medido es si alguno ya existe
resuelto en el repo. Por eso cada ítem lleva su primer paso, y en varios ese primer paso *es*
comprobarlo antes de construir nada.

## A — Precondiciones de medición. Sin ellas el done-gate del spec es infalsable

**Éstas no son diferidas: son parte de la rebanada.** Un done-gate que no se puede falsar es el
verde de los 156 módulos otra vez.

| Ítem | Por qué bloquea el propósito | Primer paso |
|---|---|---|
| **A1 · Clasificador de familia y su falsación** | El spec asume que algo decide que una misión de InfinityOps *es* de la familia `PERSISTENT_STATE`, y no dice qué ni cómo. Un clasificador que responde «sí» a todo pasa todos los tests de activación y ninguno de no-activación: es `FALSE ACTIVATION IS A BUG` una capa por encima de donde el spec lo puso. | Escribir el predicado con **las dos ramas alcanzables sobre entradas reales**: nombrar una misión del estate que debe clasificar dentro y otra que debe quedar fuera, antes de implementarlo. Si una de las dos ramas no tiene ejemplo real, el predicado mide otra cosa. |
| **A2 · Catálogo de familias DESCUBIERTO, nunca curado** | Si las familias se enumeran a mano, medimos memoria y no realidad. Una familia no declarada no puntúa UNKNOWN: **desaparece del denominador**, y la ausencia se lee como salud. Es literalmente PR-COVERAGE-BY-CONSTRUCTION-001, que esta estancia ya pagó con la Liveness Ledger (ocho componentes inscritos a mano). | Enumerar familias desde una señal estructural del estate (esquemas, migraciones, módulos de persistencia), no desde una lista escrita por nadie. Poner **suelo de población**: un barrido que deja de encontrar nada debe fallar, no reportar limpio. |
| **A3 · Medición A/A de CRR y RFR antes de tocar nada** | `CRR→0` y `RFR→0` no significan nada sin saber cuánto valen hoy. Un umbral elegido después de ver los números no es un umbral. Es el ítem **más barato de toda la lista** y el que decide si el resto es demostrable o decorativo. | Contar, sobre el historial real del estate, cuántas veces el Owner ha tenido que volver a pedir algo que ya era constitutivo en un sistema equivalente. Predeclarar el método **por escrito y antes** de la primera medición contada. |
| **A4 · Techo de tokens de la cápsula** | Se paga en cada misión, para siempre. Sin techo medido, el éxito del trinquete *es* el coste del trinquete — y nadie lo ve venir, porque cada entrada individual parece razonable por separado. | Fijar un presupuesto en tokens para la Mission Baseline Capsule y hacer que superarlo sea un fallo del compilador, no una nota. El Anti-Bureaucracy Ratchet de v2 (diferido arriba) es su versión general. |

## B — Mecanismos que el propósito exige y ningún fabric nombra

| Ítem | Por qué bloquea el propósito | Primer paso |
|---|---|---|
| **B1 · Revocación de una entrada constitutiva** | Un trinquete que sólo sube es burocracia con otro nombre. `B0` nace con evidencia débil por diseño, así que alguna entrada será errónea; sin camino de vuelta, el error queda institucionalizado con más fuerza que el acierto. | Estados de revocación con actor, fecha y evidencia en contra. Append-only: revocar **supersede**, nunca sobrescribe — el par «se creyó esto, luego esto» es el registro. |
| **B2 · Inventario de deuda de herencia por instancia** | En el instante en que QuickLease promueve a `B1`, QuickLease queda por debajo de sí mismo. El spec tiene RATCHET-ON-TOUCH; lo que no tiene es quién debe qué, así que la deuda es invisible hasta que alguien tropieza. | Una vista derivada, no una lista mantenida a mano: instancia × generación de baseline × entradas pendientes. Sólo encoge. |
| **B3 · Precedencia baseline-de-familia vs `CLAUDE.md` del proyecto** | Sin regla declarada, la primera colisión la resuelve quien escriba último. Y las colisiones son seguras: el baseline dirá cosas sobre escritura atómica o migraciones que algún proyecto ya resuelve a su manera. | Declarar la precedencia **antes** de la primera colisión, y que una colisión no resuelta sea un hallazgo visible, no una resolución silenciosa. |
| **B4 · Transporte cross-host** | El kernel es host-level, así que el baseline vive en `~/.claude` y no en el repo. Máquina nueva, el VPS, o una reinstalación: amnesia institucional completa y silenciosa. Todo lo que QuickLease enseñó desaparece sin un solo error. | Decidir si el baseline de familia es **contenido versionado** (viaja con el repo de Power Pack) o estado de host (no viaja). Medir qué ocurre hoy en el VPS antes de diseñar; puede que la respuesta ya exista. |
| **B5 · Override Ledger** | Cuando el Owner rechaza una cápsula, ese rechazo es la señal más cara del sistema entero: es el Owner corrigiendo al baseline. Sin registro se pierde justo la que más vale, y el baseline repite el mismo error en la siguiente misión. | Registrar override con razón, y tratar una razón repetida como candidata a revocación (B1). Un override sin razón es un override que no se puede evaluar después. |
| **B6 · Separación cliente / doctrina** | QuickLease e InfinityOps pueden ser de clientes distintos. La **ley abstracta** viaja entre proyectos; el nombre de una tabla, un esquema o un dato de un cliente **no**. El riesgo no está nombrado en ninguna parte del diseño. | Aplicar la triple separación Evidence / Interpretation / Doctrine de UDFLL (diferida arriba) exactamente aquí: sólo la capa Doctrine cruza de proyecto a proyecto, y un gate lo comprueba. |
| **B7 · Escritores concurrentes sobre una familia** | Dos paneles promoviendo a la vez a `PERSISTENT_STATE` es el caso normal en esta máquina, no el raro. La doctrina de árbol compartido del estate protege ficheros, y una generación de baseline no es un fichero. | Preferir fichero NUEVO por promoción sobre extender uno compartido, que es la defensa que ya funciona aquí. Antes de eso: comprobar si dos promociones simultáneas son siquiera representables. |

## C — Deuda de estate que bloquea el bucle (no es diseño, es lo que ya está roto)

Registrado aquí porque bloquea el propósito, marcado aparte porque **no forma parte de la Torre**:
son fallos conocidos del estate que ya están en memoria y que este diseño necesita cerrados.

| Ítem | Por qué bloquea el propósito |
|---|---|
| **C1 · `/cpp-compound` atascado en los pasos 7+8** | Es literalmente el bucle de compounding. Si no cierra, la telemetría de consumo del §8 del spec no se consolida y el done-gate no tiene salida. Ya registrado: cero artefactos **es** el veredicto correcto, y el cierre del bucle va en Node. |
| **C2 · Deriva del mirror (5 pares DRIFT) + apertura `.ps1` en `modules/mirror_discovery/discovery.py`** | Esto *es* «instalación rancia» por construcción: el kernel registrado en `~/.claude` y el kernel del repo divergiendo sin que nada lo diga. El §6 del spec exige detectar precisamente eso, y el detector viviría sobre un sustrato que ya deriva. |
| **C3 · `continuation_transport` con el camino de entrega sin ejercitar** | Un camino de entrega no ejercitado no es un camino. Mismo patrón que el árbitro de ACCEPTANCE que nunca juzgó una recuperación real. |

## Nota de prioridad

**El grupo A no es diferido.** Son precondiciones de medición de la propia rebanada: sin ellas el
done-gate que el Owner aprobó no se puede falsar, y A3 además caduca — una vez empiece a correr el
trinquete ya no hay forma de medir cómo era antes. A3 primero, y antes de la primera promoción.

Todo lo demás de la primera tabla sigue sin ser P0 mientras la rebanada no esté medida: construir
cualquiera antes reintroduce el fallo que el §79 del dataset prohíbe y que esta estancia ya pagó
una vez.

Orden sugerido una vez A esté cubierto:

1. **B1 + B5** — juntas. Una permite corregir el baseline, la otra captura la corrección. Por
   separado, cada una es la mitad inútil de un bucle.
2. **C1** — desbloquea la consolidación de la telemetría.
3. **Segunda familia de sistema** — convierte «funcionó una vez» en «funciona por clase».
   `A SINGLE PASS PROVES POSSIBILITY; REPEATED PASS PROVES RELIABILITY`.
4. **Lectura del 76% restante** — barata, y la única forma de saber si algo de todo lo anterior ya
   está resuelto en el dataset de una manera que este diseño contradice.
