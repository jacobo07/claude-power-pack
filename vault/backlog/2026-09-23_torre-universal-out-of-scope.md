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

## Nota de prioridad

Ninguno de los ítems es P0 mientras la rebanada `PERSISTENT_STATE` no esté medida — construir
cualquiera antes reintroduce exactamente el fallo que el §79 del dataset prohíbe y que esta
estancia ya pagó una vez (156 módulos inalcanzables, `/cpp-compound` atascado en los pasos 7+8).

Los dos primeros candidatos cuando la rebanada cierre, por orden:

1. **Segunda familia de sistema** — es lo que convierte «funcionó una vez» en «funciona por
   clase». `A SINGLE PASS PROVES POSSIBILITY; REPEATED PASS PROVES RELIABILITY`.
2. **Lectura del 76% restante** — barata, y es la única forma de saber si algo de lo de arriba ya
   está resuelto en el dataset de una manera que este diseño contradice.
