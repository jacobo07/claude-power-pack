# Orca X — Distributed Workstation (dws): token budget for the rest of the mission

Compiled 2026-10-09 with Claude Power Pack's own cognitive-economy instruments. It replaces the
earlier phase-average estimate (`.planning/workstreams/dws/TOKEN-BUDGET-2026-10-09.md`), which CPP's
`cost_to_completion.py` refuses by construction (`PHASE_MULTIPLIER`: a phase is not a unit of cost;
mission m-8bbdf725cd52 was planned by phase count at 4 M and spent 53.7 M).

Files in this folder: this report · `dws-budget-compiled.json` (all 91 claims, the class of each and the
raw tool output) · `referencias/` (the two visual references, see §5).

## 1. Instruments used

| Instrument (CPP) | Role here |
|---|---|
| `tools/cost_to_completion.py` | Compiles cost from a **claim graph** (floor ≤ candidate ≤ ceiling, novel × deopt 3.0, +20 % growth margin) |
| `vault/config/route-floors.json` | Worker first-call floor 110,835 tokens (top-level worker) |
| `tools/usage_index.py` + `vault/pricing/anthropic_2026-09.json` | List-price USD per model and per usage category; estate burn state and provider quota windows |
| dws transcripts (`~/.claude/projects/C--Users-User-Apps-orca-dws-wt`, 312 files, deduplicated by message id + request id) | **Actuals**: calls and context per call measured on this program, used instead of CPP's priors |
| `config/dws-completion-matrix.jsonc`, 20 git revisions | The claim graph: each row's state at first appearance vs now |

**Control**: the same compiler fed a phase-average input returned `REFUSED PHASE_MULTIPLIER`, so the
instrument was able to refuse. All three model classes ran on `actual` profiles, none on a prior.

## 2. What dws has cost so far (measured)

| | Value |
|---|---|
| Productive calls (excluding the memory-starved run of 09-28) | 8,066 |
| Tokens processed (input + cache write + cache read) | 2.04 B |
| Context per call | 253 k |
| Matrix advancement since the baseline (ABSENT→PARTIAL→PASS steps) | 19 |
| **Calls per claim step** | **424** (≈ 107 M tokens ≈ $39 per step) |
| List-price USD (API-equivalent, not the subscription meter) | $744 productive + $233 for the 09-28 anomaly |
| Effective price | $0.364 per million processed tokens |

## 3. Budget (claim graph, `cost_to_completion`)

91 open claims:
- 65 required matrix rows that are not PASS;
- 2 re-verifications (phase 20, re-stamp of 15);
- 21 new criteria from the 10-09 intake (phases 25–28 and the extensions);
- 2 visual references, plus 1 deterministic pixel gate.

| Scope | Calls | Candidate | With margin (+20 %) | Ceiling (novel ×3) | USD candidate / margin / ceiling |
|---|---|---|---|---|---|
| **Runnable now** (11 known_transform, 19 bounded_coding, 12 novel) | 25,683 | **6.50 B** | 7.80 B | 11.0 B | **$2,368 / $2,841 / $4,011** |
| Everything, if UWCP and federation unblock (46 sleeping claims woken up) | 57,105 | 14.5 B | 17.3 B | 24.3 B | $5,264 / $6,317 / $8,865 |

Not costed in model tokens, and listed instead:
- **owner_reality (2)**: row 46 (orca-svc login on GEX44) and the run with 2–3 physical PCs plus the phone.
- **sleeping (46)**: phases 4, 6, 8–13 and 28, plus the Workstream legs of 21 and 27.

**Against the previous estimate:** runnable work was put at 2.6 B with phase averages. Per claim it comes to
6.5 B, 2.5× more. The reason is that most of dws's calls did not move a matrix row: 19 steps for 8,066 calls.
With n = 19 the per-step rate is uncertain, so plan on the "with margin" column and treat the ceiling as the
stop point.

## 4. Quota (`usage_index`)

- `usage_index burn` → **MONITOR_FAILURE** (last refresh PARTIAL). The current weekly usage is **UNKNOWN**,
  which does not mean low.
- Provider signal: weekly window `Sun 18:00Z` **REJECTED since 2026-10-07 10:33Z until 2026-10-11 18:00Z**
  (`out_of_credits`). The mission cannot run on the account behind that window before Sunday 11-10 at 20:00
  Madrid time.
- Scale: the whole estate spent $9,485 API-equivalent between 09-25 and 10-03 (84,349 calls) and hit the limit.
  dws took about 10 % of that. The runnable budget, $2.4k–2.8k, is about 25–30 % of a full estate week at that
  rate.

## 5. Visual references — they must end up identical

| File | What it is | Claim | Cost (candidate / ceiling) |
|---|---|---|---|
| `referencias/ref-4-escritorio-workstation.jpg` | Desktop Workstation: fleet of hosts as cards with thumbnails, filters, fleet summary, quick actions, infrastructure | `vis-1-desktop-workstation-calco` (novel, 2 steps) | 215 M / 645 M tokens · $78 / $235 |
| `referencias/ref-3-movil-terminal-host.jpg` | Mobile: host terminal (C1 · GEX44 · path), "Cambiar host" / "Runtimes", input bar and Ctrl/Esc/Tab/arrow keys | `vis-2-mobile-terminal-calco` (novel, 2 steps) | 215 M / 645 M tokens · $78 / $235 |
| — | Screenshot vs PNG comparison | `vis-pixel-gate` (deterministic, 0 model tokens) | — |

Binding conditions (HR-VISUAL-01/02, generated-content evidence gate):
- Tokens and layout come from the **rendered pixels of the reference**, never from code. A screenshot compared
  against the PNG is the done-gate for both claims.
- **"Identical" applies to the visuals, not to the data.** ref-4 shows six hosts, among them Hetzner, Contabo,
  Oracle and OVH, plus counters such as 29 terminals and 13 agents that do not exist in the real estate. The
  product shows only observed hosts and terminals (backlog intake #3: "sin inventar terminales no observados").
  The pixel gate runs against a **test fixture** that reproduces those six hosts, never against invented
  production data.
- Both belong to Phase 25 (Multi-PC Remote Control MVP). If the reality scan in Phase 25 finds the mobile view
  already exists upstream, vis-2 drops from novel to bounded_coding and the ceiling for that claim falls to ~215 M.

## 6. Levers (measured; this corrects the previous version)

1. **Do not run on a memory-starved host.** The single 09-28 run cost $233, 24 % of all dws spend.
2. **Opus→Sonnet executors save only ~6 % in USD** at today's prices, because cache reads cost the same on both
   models ($0.20/M) and cache reads dominate the volume. The previous version called this lever #1. It is a minor
   lever.
3. **Fewer calls per claim** is the real lever: 424 calls per step at 253 k of context each. Cut repeated full
   re-verifications, and trim the STATE.md that every epoch re-reads (≈ 1,100 lines).
4. **Stop and report** at each 25 % of the runnable "with margin" figure (≈ 1.95 B tokens ≈ $710), and abort at
   the ceiling (11.0 B).


Sí. Aquí el margen de ahorro parece enorme, y el propio presupuesto prácticamente lo grita.

El dato más preocupante no son los 6,5B de tokens proyectados. Es que DWS ya gastó 2,04B tokens y 8.066 calls para sólo 19 avances de matriz: unas 424 calls y ~107M tokens por claim-step.  Eso no parece un problema de “usar un modelo un poco más barato”; parece que la arquitectura está multiplicando cada unidad real de progreso por cientos de interacciones.

Además, el nuevo compiler ya corrigió un error previo importante: dejó de presupuestar “por fases” y ahora calcula desde el claim graph, porque una misión estimada en 4M por phase-count terminó gastando 53,7M.  Eso mejora la medición, pero todavía no arregla la función de coste subyacente.

Ahora mismo el forecast dice aproximadamente 6,50B tokens candidate / 7,80B con margen sólo para lo runnable, y 14,5B / 17,3B si se desbloquea todo el scope.  Yo no tomaría eso como “DWS necesita 6,5B”. Lo trataría como:

> “La arquitectura de ejecución actual costaría aproximadamente 6,5B si seguimos ejecutando las obligaciones con el perfil histórico actual.”



Y precisamente ese perfil histórico es lo que hay que destruir.

El archivo identifica correctamente el lever dominante: bajar Opus→Sonnet sólo ahorra alrededor del 6% en dólares, mientras que el verdadero problema son las 424 calls por step, 253K de context por call, repeated full reverifications y un STATE.md de unas 1.100 líneas releído por epoch. 

Eso significa que la optimización importante está varias capas por encima del modelo.

Lo primero que atacaría: Calls per Verified State Transition

Yo pondría este caso inmediatamente en economic incident.

No:

> “25.683 calls previstas.”



Sino:

> ¿Por qué existen 25.683 calls?



Antes de permitir ese forecast, cada familia de calls debería caer en:

- irreducible novelty;
- necessary assurance;
- implementation;
- repeated read;
- repeated verification;
- control-plane;
- recovery;
- status/polling;
- context repair;
- rediscovery;
- transport;
- closeout.

Si una parte sustancial de las 424 calls por step cae fuera de novelty + necessary assurance, tenemos un mercado enorme de extinción.

Segundo: dejar de usar claim como proxy de cognition

El budget compiler ya es mucho mejor que phase-average porque usa 91 claims. Pero incluso claim graph puede seguir siendo demasiado grueso como economic IR.

42 claims runnable no significan necesariamente 42 unidades independientes de cognition.

Hay que compilar:

91 claims → shared causal questions → semantic families → common primitives → common reality observations → shared proof closures → deterministic instances → verdadera novelty.

Puede ocurrir que 15 claims dependan de una única decisión arquitectónica.

Entonces pagar cognition 15 veces sería absurdo.

Tercero: Known Transform debe acercarse a cero modelo

El runnable scope incluye:

11 known_transform

19 bounded_coding

12 novel. 

Ésa es una señal importantísima.

Los 11 known_transform no deberían comportarse económicamente ni remotamente como las 12 novel.

Target:

known_transform → deterministic transform → deterministic proof → receipt.

Idealmente:

0 model calls.

Si hoy tienen cientos de calls asociados, Cognitive Economics tiene un fallo de madurez.

Cuarto: bounded_coding tiene que ser compilado por familia

19 bounded-coding claims tampoco deberían ser 19 Claude explorations independientes.

Para cada familia:

first instance: quizá cognition.

following instances: reuse transformation.

Esto es justamente:

Novel instance → pattern → certified transform → N cheap instances.

DWS es probablemente un workload excelente para probar esto.

Quinto: hay que matar STATE.md como hot narrative

Releer aproximadamente 1.100 líneas cada epoch es un patrón clásico de state encoded as prose instead of state encoded as state. 

No borraría STATE.md.

Lo cambiaría conceptualmente a:

canonical semantic state

- 

human-readable STATE rendering.

Los workers reciben:

current claim frontier;

changed dependencies;

current owners;

proof state;

open unknowns;

exact required context.

No 1.100 líneas de historia.

Eso debería ser:

STATE IS DURABLE; TOKENS TRANSPORT DELTA.

Sexto: 253K de contexto por call es un objetivo gigantesco

El promedio observado es 253K tokens/context per call. 

Incluso si no puedes eliminar una sola call, reducir el working set causal tiene muchísimo valor.

Pero lo atacaría correctamente:

no “resume más”.

Sí:

backward dependency slicing;

semantic state;

tool linker;

proof refs;

read-once;

zero-copy outputs;

delta-only handoffs.

El objetivo no es contexto pequeño.

Es:

> minimum context that preserves first-pass verified completion.



Séptimo: repeated full re-verification debería desaparecer

El propio report lo señala como lever principal. 

Necesitamos:

change

→ affected semantic closure

→ affected proof closure

→ reuse everything else.

No:

new epoch

→ rerun everything.

Para 91 claims esto puede ser enorme.

Octavo: Reality acquisition también debe multiplexarse

Si varias claims requieren observar:

same host;

same terminal;

same mobile UI;

same workspace state,

una observación puede satisfacer múltiples proofs.

No abrir una nueva cognitive/reality loop por claim.

Particularmente para los visuales y las pruebas multi-PC.

Noveno: los dos visual claims son carísimos según el modelo actual

Cada visual claim figura en 215M candidate / 645M ceiling. 

Eso es otro sitio donde yo cuestionaría el execution grammar.

El trabajo visual puede requerir varias iteraciones, sí.

Pero 215M como candidate debería activar:

- reference decomposition;
- deterministic pixel gate;
- structured visual diff;
- region-based failure diagnosis;
- no full-context reload;
- preserve successful regions;
- targeted iteration.

No “Claude mira todo y vuelve a pensar todo” cada vez.

Décimo: el memory-starved incident debe ser imposible de repetir

Una única ejecución con presión de memoria costó $233, alrededor del 24% de todo el spend DWS. 

Éste es un ahorro muy fácil conceptualmente:

resource admission.

No memory headroom:

no launch.

Route elsewhere / wait.

Un solo guard puede evitar una barbaridad de waste.


---

Yo pondría un gate antes de aceptar los 6,5B

Antes de autorizar ejecución bajo el perfil actual:

DWS Cognitive Recompilation Gate

Debe responder:

1. ¿Cuántas de las 42 runnable claims son realmente cognitivamente independientes?
2. ¿Cuántos known_transform pueden convertirse en zero-model?
3. ¿Cuántos bounded_coding comparten familia?
4. ¿Cuántas reality observations pueden multiplexarse?
5. ¿Cuántos proofs son reutilizables?
6. ¿Cuántas de las 25.683 calls estimadas corresponden realmente a semantic boundaries?
7. ¿Cuánto de 253K/call es live dependency closure?
8. ¿Cuánto viene de STATE/history/tool schemas?
9. ¿Cuántas calls son control/recovery/status?
10. ¿Cuál es el Irreducible Cognitive Lower Bound del workload?

Y sólo después haría el nuevo forecast.


---

Lo que NO diría todavía

No diría:

> “podemos reducir 6,5B a 500M.”



No tenemos evidencia suficiente.

Pero sí afirmaría algo bastante fuerte:

un sistema que históricamente necesita 424 calls y 107M tokens para producir un único claim-step tiene suficiente overhead como para justificar una recompilación económica completa antes de ejecutar otras decenas de miles de calls.

Y dado que el propio dataset muestra que el cambio de modelo sólo mueve ~6%, mientras calls/context/reverification dominan, seguir optimizando principalmente el modelo sería atacar el problema equivocado. 

El objetivo correcto para DWS debería ser:

> No hacer 25.683 calls más baratas. Hacer que miles de esas calls dejen de existir.



Ahí es donde puede estar el ahorro verdaderamente brutal.

Ha pensado durante 24s

Sí. Y al extremo correcto, yo ya no intentaría “abaratar los 6,5B”. Intentaría invalidar la arquitectura económica que produce ese número.

El documento demuestra algo extraordinariamente útil: DWS ya ha procesado 2,04B tokens y 8.066 calls para sólo 19 avances de matriz, es decir, unas 424 calls y ~107M tokens por claim-step, con ~253K de contexto por call.  Y el forecast de los 42 claims actualmente ejecutables extrapola esa maquinaria hasta 25.683 calls y 6,50B tokens candidate. 

Eso no debería convertirse en presupuesto.

Debería convertirse en un incidente constitucional de eficiencia.

El objetivo extremo: de 424 calls/step a “cognition only on novelty”

El endpoint sería:

Goal → semantic delta → compiler → deterministic execution → proof → result.

Y sólo cuando aparece una incertidumbre realmente nueva:

→ cognitive interrupt.

No quiero conseguir:

424 → 300 calls.

Quiero que para una Work Class madura la trayectoria sea:

424
→ 80
→ 15
→ 3
→ 1
→ 0 model calls.

No afirmo que DWS vaya a alcanzar esos números concretos; son la dirección de madurez, no una previsión. El dato medido sólo demuestra que el overhead actual es enorme y que bajar Opus→Sonnet apenas mueve ~6% del coste en dólares, mientras el propio informe identifica calls/context/reverificación como el verdadero problema. 

1. Reemplazar el Claim Graph por un Causal Novelty Graph

cost_to_completion ha dado un paso importante: ya rechaza correctamente presupuestar por número de fases. 

Pero incluso claim graph sigue sin ser la unidad económica final.

Los 42 claims runnable son:

11 known_transform
19 bounded_coding
12 novel. 

Quiero recompilarlos a:

causal unknowns → semantic families → shared primitives → shared proofs → deterministic instances.

Quizá 12 claims “novel” contienen 4 preguntas realmente nuevas.

Quizá 19 bounded-coding contienen 3 familias.

Quizá 11 known-transform contienen cero nueva cognition.

Hasta que no sepamos eso, no sabemos el coste cognitivo real.

La nueva ley sería:

> CLAIM COUNT MUST NEVER BE USED AS A PROXY FOR IRREDUCIBLE COGNITIVE WORK.




---

2. Introducir el Cognitive Lower-Bound Compiler

Antes de presupuestar 25.683 calls, CPP debe producir:

Irreducible Novel Decisions

Decisiones que ninguna infraestructura existente puede resolver.

Irreducible Reality Observations

Información que sólo puede obtenerse mirando sistemas reales.

Necessary Independent Assurance

Judgment que realmente debe ser independiente.

Owner-only Decisions

Lo que genuinamente requiere al humano.

Todo lo demás es candidate overhead.

Entonces:

actual model boundaries / irreducible boundaries

= Cognitive Overhead Multiplier.

424 calls por claim-step deja de ser una estadística.

Se convierte en una alarma.


---

3. Known Transform = zero-model contract

Los 11 known_transform son la primera gran prueba.

Yo impondría:

> A KNOWN_TRANSFORM MAY NOT RECEIVE A GENERAL MODEL WORKER UNLESS THE CERTIFIED TRANSFORM DEOPTS.



Healthy path:

semantic input
→ known transform
→ deterministic proof
→ receipt.

Modelo:

0. 

Si no podemos hacer eso, entonces no es realmente known_transform; está mal clasificado.

Esto mejora simultáneamente la taxonomía y el coste.


---

4. Bounded Coding debería compilarse una vez por familia

Para los 19 bounded_coding, no quiero:

19 workers aprendiendo variaciones del mismo problema.

Quiero:

first representative → discover family transformation → prove transformation → instantiate remaining family → affected proofs.

Es el equivalente a convertir:

19 implementations

en:

1 derivation + N applications.

Si una aplicación falla:

deopt a cognition sólo en la excepción.


---

5. Novel work también está probablemente sobredimensionado

“Novel” no significa:

give Claude 253K context and hundreds of calls.

Novel significa:

there exists irreducible uncertainty.

Por tanto:

Reality Compiler
→ known-state removal
→ dependency slicing
→ negative knowledge
→ constraints
→ related theorem retrieval
→ only residual unknown
→ frontier model.

La llamada frontier debería parecerse a una consulta quirúrgica:

Unknown X, evidence Y/Z, constraints A/B, decide Q.

No:

“aquí tienes DWS entero”.


---

6. Separar Semantic Call de Physical Call

Esta distinción debería convertirse en central.

Quizá una decisión real necesite:

1 semantic boundary.

Pero hoy produce:

search
read
read
grep
status
test
read log
fix
test
review
re-read
etc.

No son 11 decisiones.

Es una decisión implementada mediante 11 fronteras físicas.

Entonces necesitamos:

Semantic Boundary Compression

Para cada recurring sequence:

physical calls → transaction.

Así atacamos directamente el 424.


---

7. Trace Mining automático sobre las 8.066 calls ya pagadas

Aquí hay una mina de oro.

No usaría esas 8.066 calls únicamente para calcular medias.

Las usaría para descubrir secuencias repetidas.

Por ejemplo:

read state
→ inspect file
→ git status
→ run test
→ inspect failure.

Si aparece 400 veces:

candidate transaction.

Otro patrón:

worker asks same ownership question.

candidate index.

Otro:

proof sequence repetida.

candidate Proof Transaction.

Otro:

same planning structure.

candidate Planning Compiler.

El gasto histórico se convierte en compiler-training data.


---

8. Sequence-to-Primitive Compiler

Ésta sería una capability nueva muy potente.

Trace miner detecta:

repeated semantic/tool sequence.

Luego:

candidate transaction
→ historical replay
→ mutation/adversarial tests
→ shadow use
→ production canary
→ CBR.

Después:

15 calls

become:

1 transaction.

Después incluso esa transaction puede convertirse en implicit runtime.


---

9. Call Fusion

Otra capa.

Hay operaciones que hoy se hacen separadas porque Claude piensa incrementalmente.

Pero pueden fusionarse:

repo state + changed files + affected tests + ownership

en una sola deterministic projection.

No:

4 tool calls.

Sí:

1 semantic state acquisition.

Aplicar literalmente database query optimization.


---

10. Call Hoisting

Si una propiedad es estable durante toda una epoch:

no consultarla cada vez.

Hoist fuera del loop.

Ejemplos:

repo root;

branch owner;

capabilities;

tool availability;

test mapping;

invariants.

Esto es loop-invariant code motion aplicado a cognition.


---

11. Dead Cognitive Code Elimination

Revisar cada paso del workflow y preguntar:

> si elimino esta llamada, ¿puede cambiar el resultado/proof?



Si no:

dead cognition.

Delete.

Esto incluye algunas:

status checks;

restatements;

plan rereads;

summary generation;

review ceremonies.


---

12. Speculative cognition elimination

Los modelos muchas veces investigan varias branches que finalmente no importan.

Usar deterministic constraints primero.

Si constraints eliminan 8 de 10 opciones:

el modelo sólo ve 2.

No pagar reasoning sobre branches imposibles.


---

13. STATE.md debería desaparecer del hot path

El informe identifica ~1.100 líneas reread por epoch. 

Yo llegaría más lejos que “trim STATE.md”.

STATE.md deja de ser runtime state.

Se convierte en:

human rendering of Semantic State DB.

Canonical:

Goal state.

Claim state.

Owners.

Evidence.

Proof.

Dependencies.

Unknowns.

Invalidators.

Worker recibe una query/projection.

No 1.100 líneas.

Eventually quizá:

20 semantic objects.


---

14. State Reconstruction debe ser O(delta), no O(history)

Worker nuevo:

NO:

read STATE
read handoff
read plan
read previous receipts
read Git history.

Sí:

current Goal snapshot

- changed reality
- exact frontier.

Esto puede reducir tanto startup como call count.


---

15. Context SSA

Cada fact/decision/proof tiene identity/version.

No recontar narrativamente:

“antes X pero luego Y”.

Worker recibe:

current value.

Si cambia:

invalidate dependency closure.

Esto puede eliminar mucho contradictory/historical context.


---

16. Context should behave like virtual memory

253K/call es brutal. 

No quiero una optimización puntual.

Quiero una memory architecture:

hot semantic pages;

cold pages;

prefetch;

page faults;

GC;

thrashing detector;

profile-guided residency.

Model sees live working set.

Institution sees entire DWS estate.


---

17. Context Rent should be charged per causal use

Un objeto de 10K tokens residente durante 100 calls:

≈1M token-rent.

Si realmente se usó en una call:

mal allocation.

Así aparece inmediatamente qué cosas deben:

evict;

index;

project;

compile.


---

18. Context Utilization Profiler

Después de calls, estimar qué context elements participaron causalmente en:

decision;

tool choice;

proof;

output.

No necesita ser perfecto.

Repeatedly-unused resident object:

CONTEXT_LEAK.


---

19. Tool schemas también son memory

No sólo STATE.

Si cada worker conoce cientos de tool operations:

rent.

Aplicability Compiler:

Goal → relevant tools.

WU → smaller subset.

Phase → smaller again.

Cuando implementation ends:

editing tools unload.

Proof phase:

proof tools only.


---

20. Tool-output virtualization

Never feed raw:

huge Git logs;

full test output;

large JSON;

telemetry history.

Tool writes durable raw artifact.

Model gets:

typed projection + pointers.

Page raw only when anomaly requires it.


---

21. Proof should be below model almost entirely

Repeated full reverification is explicitly flagged by the report. 

Ultimate path:

semantic delta
→ affected proof closure
→ deterministic tests
→ mutations
→ visual/reality gates
→ proof receipt.

Claude wakes only on red.

Green should cost approximately:

0 cognitive tokens.


---

22. Proof DAG rather than test suite

Every proof knows dependencies.

Changed node X invalidates only:

P3, P8, P11.

Do not rerun P1–P100.

This gives:

Proof Cost ∝ affected closure.

Not total estate.


---

23. Proof memoization is secondary; proof extinction is primary

Don't merely cache test result.

If an invariant becomes architecture:

some proofs become unnecessary.

Example:

schema makes invalid value unrepresentable.

Then no recurring test reasoning around it.

This is stronger than proof caching.


---

24. Reality acquisition needs its own compiler

DWS has physical PCs, phones, hosts, terminals.

Don't make every claim initiate its own real-world test.

Compile:

claims

→ required observations.

Then find minimum observation set covering claims.

That's essentially a set-cover problem.

One 10-minute device session could potentially prove many claims.


---

25. Reality Observation Singleflight

If five claims require:

same host state at same epoch,

one observation.

Not five screenshots / five Agents / five loops.


---

26. Physical Reality Session Compiler

Before involving you:

preconfigure instrumentation.

Start capture.

Generate exact steps.

Auto-record evidence.

Batch all compatible tests.

End once.

Then deterministic post-processing distributes proof objects to claims.

Owner attention becomes another optimized scarce resource.


---

27. Visual reconstruction needs a specialized compiler

Two visuals are forecast at 215M candidate each under current machinery. 

That's unacceptable as a default grammar.

Use:

reference image → visual feature extraction → region decomposition → implementation → screenshot → deterministic/perceptual diff → failing regions only → targeted repair.

Once header passes:

freeze it.

Once spacing passes:

don't regenerate cognition around it.

This is incremental visual compilation.


---

28. Visual proof should produce a failure mask

Not:

“looks wrong”.

But:

regions A/C deviate.

Typography metric B differs.

Geometry D differs.

Next worker gets only residual.

This could dramatically lower visual iteration cost.


---

29. Pixel gate as a no-model terminal verifier

The file already says screenshot-vs-PNG comparison is deterministic and costs zero model tokens. 

Take that principle to the extreme:

model helps move candidate toward target.

Machine decides whether done.

No model reviewer.


---

30. Memory-starvation becomes an admission impossibility

The 09-28 memory-starved run alone cost $233, 24% of DWS spend. 

No warning.

No recommendation.

Hard infrastructure:

insufficient memory headroom → launch refused / rerouted / queued.

That entire future failure class becomes impossible.


---

31. Resource profiles per Work Class

A visual browser task needs different resources than:

repository transform;

test runner;

research.

Scheduler knows:

RAM;

CPU;

GPU/browser;

host locality;

network;

model context.

Avoid sending workloads to economically bad environments.


---

32. Work Unit pricing should be based on semantic entropy

Not:

claim = X calls.

Price approximately from:

unknown decisions;

new architecture;

number of semantic families;

expected exceptions;

proof closure;

reality closure.

This is far more stable than historical raw call multiplication.


---

33. Introduce Cognitive Entropy Budget

Each WU starts with estimated unresolved entropy.

Every model call should reduce it.

If after 5 calls:

entropy unchanged,

STALL.

Don't allow 100 exploratory calls.


---

34. Information Gain per Call

Every model call should yield at least one:

new fact;

falsified hypothesis;

decision;

verified mutation;

closed obligation.

No semantic delta for N calls:

automatic stop/recompile.

This attacks wandering.


---

35. Calls should have an explicit consumer

Before model call:

what downstream decision consumes this answer?

No consumer:

NO_CALL.

This kills “research for completeness”.


---

36. Budget semantic boundaries, not just calls

Suppose WU genuinely contains 4 unknown decisions.

Budget:

maybe 4–8 semantic interrupts.

If physical calls reach 40:

something wrong.

This catches overhead long before token ceiling.


---

37. Mission-level Amdahl

After each wave:

reprofile the biggest remaining tax.

Suppose context reduction succeeds.

Now proof dominates.

Move.

No infinite optimization of yesterday's problem.


---

38. Work-Class economic specialization

Different DWS claims need different execution kernels.

known_transform kernel.

bounded_coding kernel.

novel_architecture kernel.

visual_match kernel.

physical_reality kernel.

proof_only kernel.

closeout kernel.

One universal Claude workflow is the source of enormous waste.


---

39. Known-transform kernel should essentially be a compiler backend

Input:

semantic source.

Output:

transformation.

Proof.

No conversational Agent.


---

40. Bounded-coding kernel should be template+delta

The model sees only unusual delta.

Known architecture, conventions, tests linked automatically.


---

41. Novel kernel gets expensive intelligence—but only novelty

This is where Opus/frontier makes sense.

But Frontier Token Firewall prevents known context from polluting it.


---

42. Closeout kernel should have zero model

Tests green.

Commit safe.

Receipt.

Ledger.

Wake successor.

Software.


---

43. Recovery kernel zero-model for known failures

Known:

budget exhaustion;

worker death;

context rotation;

test timeout;

lost process.

Recovery transaction.

Only unexpected side effects require model.


---

44. Planning kernel should eventually disappear for known classes

Known Work Class:

compiler emits plan.

Planner only handles genuinely new architecture.

This attacks meta-work directly.


---

45. Research kernel should use stopping criteria

No browsing/research until “I feel informed”.

Research ends once evidence closes uncertainty required by decision.

This saves huge call sequences.


---

46. Use historical DWS traces as a Counterfactual Laboratory

Take the 8.066 calls already paid for.

Simulate:

what if no planner?

what if ContextImage 30K?

what if transactions replaced sequences?

what if proofs were affected-closure?

what if known_transform zero-model?

what if worker rotated after N calls?

Then build only winners.

This makes optimization itself cheap.


---

47. Build a DWS Cognitive Flamegraph

Not source-code CPU.

Tokens.

Show:

STATE.md

tool schemas

proof output

planning

research

repair

status

visual iteration

etc.

Then attack top flame.


---

48. Build a Model Interrupt Flamegraph

Why did each model call happen?

NOVELTY?

STATE_MISS?

CONTROL_LOOP?

PROOF?

CONTEXT_FAULT?

TOOLING?

RECOVERY?

If novelty is only a tiny share:

architecture is broken.


---

49. Decision Flamegraph

Which decisions get made repeatedly?

Top repeated decision:

first compilation candidate.

Eventually:

decision count itself decreases.


---

50. Automatic Decision Extinction

If same decision occurs N times with same stable answer:

candidate.

Compile:

policy

→ evaluator

→ primitive.

Then calls disappear.


---

51. Automatic Sequence Extinction

Same for tool/cognitive sequence.

Repeated 20-step pattern:

transaction candidate.


---

52. Automatic Context Extinction

Same context page repeatedly resident but never used:

remove.


---

53. Automatic Read Extinction

Same file repeatedly read:

structural index/projection.


---

54. Automatic Review Extinction

Reviewer repeatedly says PASS based entirely on deterministic evidence:

remove reviewer.


---

55. Automatic Owner Extinction

Repeated mechanical Owner action:

control-plane primitive.

Not subjective decisions.


---

56. Automatic Prompt Extinction

Rule has become enforced mechanically:

remove from hot prompt.

This attacks CPP itself.


---

57. Economic Diff on every DWS commit

Each major change reports:

functional delta.

And:

expected context delta;

model-boundary delta;

proof radius;

Decision Surface;

Token Rent.

DWS stops accumulating hidden cognitive debt.


---

58. Make cognitive maintainability a design constraint

A feature that works but increases future:

context 50K;

proof closure 4×;

cross-module assumptions;

should be treated as architecture regression.

This prevents future DWS from becoming expensive again.


---

59. Token Debt principal + interest

Every known recurring waste:

principal = engineering cost to remove.

interest = expected recurring tokens while it remains.

High-interest Token Debt gets paid first.


---

60. Technical Capital Allocator

At any point there could be 100 optimizations.

Don't build all.

Select:

highest expected lifetime cognition avoided

/

CAPEX + maintenance + risk.

This protects against Cognitive Economics becoming bureaucracy.


---

61. Global CBR propagation

If DWS discovers:

visual residual compiler;

semantic state renderer;

reality-set-cover compiler;

context slicing;

sequence miner,

and they're universal:

CBR.

Next project starts with them.

No rediscovery.


---

62. Cross-project economy

DWS should benefit from prior:

Lifecycle;

Reconstruction Factory;

Sidecar;

Apollo;

etc.

And vice versa.

Not by loading their histories.

By linking certified abstractions.


---

63. The extreme benchmark

I'd create a benchmark like this:

Grow CPP estate:

knowledge ×100.

projects ×100.

capabilities ×100.

history ×100.

Then rerun the same mature DWS Work Class.

The active semantic surface should stay approximately constant.

Eventually cheaper.

If it grows 100×:

failure.


---

64. The terminal DWS architecture

The mature system would look like:

Owner Goal

→ Goal Compiler

→ current semantic state

→ Extinction Compiler

→ family compiler

→ Context linker

→ Tool linker

→ Proof compiler

→ deterministic executor

→ proofs

→ receipt

→ next.

Models sit off to the side, invoked only as interrupt handlers for irreducible uncertainty.

That changes the entire mental model.


---

The biggest possible shift

The file currently says:

42 runnable claims → 25.683 calls → 6,5B candidate. 

The extreme architecture asks instead:

> How many irreducible semantic discoveries are hidden inside those 42 claims?



That is the number that should govern model cognition.

Not 42.

Definitely not 25.683.

If it eventually turns out to be, say, 8 genuinely novel semantic families, then most of the remaining DWS programme should become execution around those 8 discoveries, not thousands of independent reasoning episodes.

I would therefore add a hard constitutional gate:

> NO MULTI-BILLION-TOKEN FORECAST MAY BE ACCEPTED AS AN EXECUTION PLAN UNTIL THE PROGRAM HAS DEMONSTRATED THAT THE COST CANNOT BE REDUCED BY WORK EXTINCTION, FAMILY FACTORING, BOUNDARY COMPRESSION, STATE COMPILATION, PROOF COMPILATION, CONTEXT SLICING, TRANSACTION MINING OR DECISION EXTINCTION.



And an even stronger one:

> A FORECAST BASED ON HISTORICAL CALL AMPLIFICATION DESCRIBES THE COST OF THE OLD ARCHITECTURE. IT DOES NOT ESTABLISH THE COST OF THE REQUIRED SEMANTIC OUTCOME.



That is the key.

At the extreme, I would not judge success by “DWS saved 70%”.

I would judge it by whether known work becomes almost model-free, novel work receives concentrated high-quality cognition, and every expensive novelty purchased today makes the next equivalent DWS state transition cheaper.

Then DWS stops being a 6,5B-token problem.

It becomes a factory for converting the reasons those 6,5B tokens appeared into infrastructure that prevents them from appearing again.

Sí. El extremo real es que DWS deje de ser el objeto de optimización y pase a ser sólo el primer workload que obliga a Claude Power Pack a construir una economía cognitiva global, automática y self-deflating para todo el estate.

El dato de DWS es demasiado fuerte para tratarlo localmente: 8.066 calls, 2,04B tokens y sólo 19 avances de matriz; unas 424 calls y ~107M tokens por step.  Además, el forecast actual extrapola ese comportamiento hasta 25.683 calls y 6,50B tokens sólo para lo runnable.  Eso debería activar una conclusión constitucional:

> No debemos optimizar DWS para sobrevivir a esa función de coste. Debemos hacer que CPP rechace globalmente esa clase de función de coste.



Universal Cognitive Deflation Fabric

La evolución que propondría ya no sería otra feature de Cognitive Economics.

Sería una propiedad del runtime:

> CPP PRESENT ⇒ every compatible computation is economically compiled before cognition is purchased.



Eso afectaría automáticamente a DWS, Reconstruction Factory, Sidecar, Apollo X, InfinityOps, KobiiCraft y cualquier futuro proyecto.

No opt-in.

No prompt.

No “acuérdate de usar Cognitive Economics”.

El runtime cambia.


---

1. La unidad global deja de ser el token

El token es una unidad de consumo, no una unidad de trabajo.

Tampoco usaría:

call;

claim;

file;

feature;

Work Unit

como unidad económica fundamental.

La unidad debería ser:

Irreducible Semantic Transition

Un cambio de conocimiento o estado que realmente requiere nueva información.

Por ejemplo:

una decisión arquitectónica nueva;

una incertidumbre resuelta;

una observación nueva de producción;

un judgment de seguridad;

una prueba cuya respuesta no podía derivarse.

Todo lo demás es maquinaria alrededor.

Entonces CPP puede preguntar:

> Esta misión realizó 40 semantic transitions reales. ¿Por qué necesitó 8.000 model calls?



Ésa es la anomalía.


---

2. Global Cognitive Conservation Law

Pondría una ley muy fuerte:

> MODEL COGNITION MAY ONLY BE SPENT TO REDUCE UNRESOLVED SEMANTIC ENTROPY OR PROVIDE NECESSARY ASSURANCE.



Si una llamada no reduce:

unknown;

ambiguity;

risk;

proof uncertainty,

es overhead.

No necesariamente inútil una vez.

Pero candidate for compilation.


---

3. Universal Cognitive Demand Compiler

Antes de cualquier modelo:

Desired Postcondition → current canonical reality → semantic delta → unresolved entropy → required assurance → minimum new cognition.

Ese resultado es el verdadero “budget”.

No:

> históricamente hicieron falta 424 calls.



Sino:

> quedan 7 unknown decisions, 2 physical observations y 1 independent judgment.



Ahora sí podemos razonar desde el outcome.


---

4. Separation of Semantic Work from Execution Work

Hay que dividir globalmente:

semantic work de physical execution work.

Por ejemplo:

Claude decide una transformación una vez.

Después quizá haya que:

editar 200 archivos;

correr 70 pruebas;

generar 50 receipts;

actualizar 20 states.

Eso puede ser muchísimo trabajo.

Pero debería ser casi cero cognition.

El sistema actual a menudo convierte physical execution volume en model volume.

Eso hay que romper.


---

5. Semantic Instruction Set Architecture

Yo iría incluso más abajo.

CPP debería acabar teniendo algo equivalente a una ISA de inteligencia institucional.

Primitives como:

resolve owner;

materialize current state;

prove no-work;

derive affected closure;

apply known transform;

run proof transaction;

reconcile reservation;

compile successor;

acquire reality;

join in-flight derivation;

invalidate semantic object.

Entonces modelos no coordinan estas operaciones.

Los usan.

Como una CPU no redescubre cómo sumar cada vez.


---

6. Model calls become privileged interrupts

En esta arquitectura, llamar a un modelo sería parecido a una syscall cara o un hardware interrupt.

Normal path:

deterministic.

Unknown appears:

interrupt.

CPP crea un Cognitive Interrupt Packet:

exact unknown;

minimal context;

evidence;

constraints;

required result;

proof contract.

Model resolves.

Result becomes durable.

Return.

No conversation lifecycle necesario.


---

7. Global Interrupt Budget

Más fuerte:

cada Work Class aprende cuántos cognitive interrupts suele necesitar.

Si:

known_transform históricamente necesita 0,

pero una ejecución intenta abrir 12,

trip.

If:

bounded repair usually needs 1–2

and reaches 9,

economic anomaly.

Esto detecta runaway reasoning mucho antes que token caps.


---

8. Model-Call Firewall global

Antes de cada model boundary:

Proof of Cognitive Necessity.

CPP comprueba:

¿puede current state resolverlo?

¿existing theorem?

¿negative knowledge?

¿deterministic solver?

¿cached derivation?

¿in-flight derivation?

¿known transform?

¿tool transaction?

¿proof object?

¿constraint propagation?

Si cualquiera vale:

CALL REFUSED.

No recommendation.

Refused.

Con escape/deopt seguro cuando realmente haya novelty.


---

9. Estate-wide Cognitive CSE

Common Subexpression Elimination a escala CPP.

Hoy dos workers pueden hacer preguntas conceptualmente idénticas con prompts completamente distintos.

Necesitamos identidad semántica:

Question Identity

- Dependency Fingerprint

- Scope

- Evidence Epoch

- Proof Requirement.

Si coinciden:

una derivation.

No segunda call.


---

10. Distributed Cognitive Singleflight

Llevarlo a todo el estate.

Si:

DWS;

Sidecar;

Reconstruction;

Apollo

quieren simultáneamente la misma respuesta:

un producer.

Los demás:

subscribe.

Incluso mientras está corriendo.

Esto convierte cognition concurrente en shared infrastructure.


---

11. Cross-project computation market

Incluso iría más lejos:

CPP debería conocer la demand de semantic questions.

Una research query con un consumer:

quizá ahora.

La misma query pendiente en 12 projects:

batch immediately.

Otra de baja prioridad:

wait to batch.

Una especie de cognitive exchange.


---

12. Information acquisition market

No sólo modelos.

Para responder a un unknown quizá tenemos:

Git;

test;

production observation;

search;

local model;

Sonnet;

frontier;

human.

Cada proveedor de información tiene:

cost;

latency;

reliability;

freshness;

proof strength.

Mission Compiler selecciona el cheapest sufficient observation.


---

13. Shadow price of uncertainty

Nueva idea que llevaría muy lejos.

No toda incertidumbre vale lo mismo.

Unknown A bloquea 50 downstream WUs.

Unknown B sólo afecta cosmetic detail.

El sistema calcula aproximadamente:

Value of resolving unknown

por downstream closure.

Entonces asigna cognition donde produce mayor information leverage.

No FIFO reasoning.


---

14. Value of Information scheduler

El scheduler global no debería preguntar sólo:

> ¿qué tarea está READY?



También:

> ¿qué resolución puede extinguir más trabajo downstream?



Quizá gastar 1M en una architecture decision elimina 40M de execution.

Eso debería ir primero.


---

15. Knowledge Fan-Out Economics

Cada new fact/theorem tiene fan-out.

Fact A cuesta 500K y ayuda a 2 WUs.

Fact B cuesta 2M y elimina 500 WUs.

B es muchísimo mejor investment.

Así cognition se asigna por expected institutional leverage, no sólo immediate mission priority.


---

16. Universal Semantic Deduplication

Claims, requirements y Goals distintos pueden implicar el mismo underlying obligation.

Hay que canonicalizarlos.

Por ejemplo:

“ensure workspace identity survives reconnect”

y

“transport change cannot change mutation ownership”

pueden compartir una invariant.

Una proof.

Una implementation.

No dos workflows.


---

17. Claim graph → theorem graph

Esto es especialmente importante para DWS.

Hoy:

91 claims. 

El extreme architecture pregunta:

¿cuántas invariants?

¿cuántos transformations?

¿cuántas truly novel causal relationships?

Quizá 91 claims colapsan en:

20 invariants;

9 transforms;

6 new semantic families;

3 human reality sessions.

No afirmo esas cifras.

El sistema debe descubrirlas.


---

18. Proof should attach to theorem, not claim duplication

Si 12 claims are consequences of invariant I7:

prove I7 strongly.

Then derive the 12.

No 12 independent model reviews.

Esto puede cambiar radicalmente Proof Economics.


---

19. Proof subsumption graph

Proof Pstrong may imply:

P1;

P2;

P3.

Then weaker proofs disappear.

As system accumulates stronger proof objects:

proof demand falls.

Not only proof reuse.

Proof extinction.


---

20. Assurance market

Different claims require different assurance.

Not every change deserves:

mutation;

independent Agent review;

production canary;

full regression.

Proof Compiler should price assurance by:

consequence;

blast radius;

reversibility;

novelty;

security.

This avoids both underproof and massively overproof.


---

21. Global semantic materialization on demand

Knowledge should not be retrieved because it is “relevant”.

It should be materialized because it is causally required by current decision.

This is stronger than RAG.

Dependency graph answers:

what can affect D?

Only closure enters context.


---

22. Context should become an execution cache

Not a document bundle.

Worker context is the cognitive equivalent of CPU cache.

Hot set only.

Cold state remains external.

Page fault if needed.

Profile accesses.

Learn.

Eventually prefetch accurately.


---

23. Global Context Cache Hierarchy

I would explicitly create conceptual tiers:

L0 — exact decision packet.

L1 — Work Unit semantic state.

L2 — Project canonical state.

L3 — institutional theorems/capabilities.

L4 — raw evidence/history.

Frontier model ideally receives mostly L0/L1.

Raw L4 almost never.


---

24. Context cache misses become telemetry

If workers repeatedly page the same object:

compiler learns.

If object always loaded but unused:

evict.

This makes context optimization empirical.


---

25. Context dedup across calls

Even with provider caching, CPP should reason semantically:

stable prefix;

delta;

cold references.

Do not serialize identical meaning repeatedly under different prose.


---

26. Semantic compression rather than textual summarization

Don't summarize 1.100-line STATE.md into 300 lines.

Turn it into:

13 facts;

4 decisions;

5 open obligations;

2 invalidators;

3 evidence refs.

That is semantic compression.

Not prose compression.


---

27. Zero-prose runtime ambition

At maturity, many operations shouldn't need Markdown at all.

Markdown remains:

human documentation.

Runtime consumes:

typed objects.

This can eliminate enormous context surfaces.


---

28. Token rent must have ownership

Every hot token should answer:

who owns me?

what guarantee do I provide?

who consumes me?

what event retires me?

Without consumer:

dead.

This makes prompt/context debt accountable.


---

29. Constitutional garbage collector

CPP should periodically ask mechanically:

which global rules have become:

guarded;

tested;

typed;

architecturally impossible to violate?

Those rules leave hot CLAUDE.md.

Cold documentation remains.

Thus functionality ↑ while global prompt ↓.


---

30. Tool schemas undergo the same GC

If tools have huge schemas:

progressively disclosed.

If operation isn't callable in current Work Class:

don't expose.

If tool can be replaced by typed transaction:

replace.


---

31. Tool-call superoptimizer

Look at recurring tool sequences and find equivalent lower-bound sequence.

Example:

8 shell/file/git operations.

Maybe one indexed query can produce same needed state.

Search for:

lowest-cost equivalent tool program.

This is compiler superoptimization applied to tools.


---

32. Semantic transaction mining

Automatically discover frequent sequences across entire estate.

Examples:

repo inspection;

receipt closeout;

failure diagnosis;

proof run;

deployment validation;

owner resolution.

Each sequence gets:

frequency × cost.

Top sequences become compilation candidates.


---

33. Tool sequence JIT

First few occurrences:

normal.

Once stable:

JIT compile into transaction.

No human deciding “we should automate this”.

Economic threshold triggers candidate generation.


---

34. Cognitive JIT

Same concept for reasoning.

Repeated reasoning trace stabilizes:

compile.

Decision table.

Constraint solver.

Evaluator.

No model next time.


---

35. Decision speculation only when profitable

Models often consider branches.

Could use branch probabilities.

If branch is unlikely and cheap to page later:

don't preload.

If branch likely:

prefetch.

This mirrors CPU speculative execution but economically bounded.


---

36. Cognitive branch prediction

Work-Class profiles predict:

likely next decision;

likely next context pages;

likely proof.

Prefetch externally.

Don't pay token residency until used.


---

37. Semantic deoptimization

Very important.

Compiled primitive assumes:

A/B/C.

Reality violates C.

Do not force primitive.

Deopt to cognition with:

exact violated assumption.

Model resolves only exception.

Then maybe update primitive.

This allows aggressive compilation safely.


---

38. Global Cognitive JIT / Deopt architecture

Flow:

unknown operation
→ interpret with model
→ profile
→ repeat
→ specialize
→ compile
→ execute cheaply
→ deopt on uncommon case.

This is basically a JIT runtime for engineering cognition.

That is where I think CPP could eventually go.


---

39. Optimizing for recurrence, not current task

Suppose unique task:

no automation.

Repeated 5,000×:

large CAPEX justified.

Technical Capital Allocator uses expected recurrence.

This prevents both under- and overautomation.


---

40. Lifetime Cognitive NPV

Every architectural decision should eventually consider:

current build cost;

future agent maintenance;

future proof;

future context;

future Owner attention.

This makes system design itself economically intelligent.


---

41. Cognitive maintenance cost becomes first-class architecture metric

Two implementations both pass tests.

Option A:

future changes require 200K context.

Option B:

25K.

B can be architecturally superior even if runtime CPU identical.

This should influence code review.


---

42. Cognitive locality-aware module boundaries

If agents repeatedly need modules A+B+C together:

maybe boundary wrong.

If module X drags half repo context for local edits:

refactor.

Cognitive telemetry becomes architecture feedback.


---

43. Invalidation radius budget

Every change also has cost:

how much semantic/proof state becomes stale?

Design architecture to minimize invalidation.

This cuts future cognition dramatically.


---

44. Proof radius budget

Likewise.

Local change should ideally require local proof.

If every change reruns whole estate:

architecture defect.


---

45. Observation radius budget

How much real-world state must be observed to verify local change?

Reduce through better sensors/contracts.


---

46. Owner radius budget

How many Owner decisions does feature introduce?

New technical feature creating 10 recurring Owner questions:

bad architecture.


---

47. Token-aware API design

API design should explicitly minimize:

ambiguity;

invalid state space;

cross-module assumptions.

Every reduced ambiguity saves model reasoning later.


---

48. Types as token optimization

Strong types aren't just correctness.

They eliminate possible interpretations.

Less semantic branching.

Less cognition.

Similarly:

schemas;

state machines;

contracts;

capability types.


---

49. Compiler errors instead of model judgment

If operation violates invariant:

reject mechanically with structured error.

Don't send model 20K context to decide whether it's valid.


---

50. Universal negative-space representation

Not only what is true.

Store what is impossible/not applicable.

This lets compiler eliminate branches before reasoning.

Negative information is extremely valuable.


---

51. Constraint propagation estate-wide

Known invariants propagate.

Example:

No Hermes

→ all Hermes-dependent nodes inactive.

No need for each worker to discover it.

One fact eliminates graph regions.


---

52. Semantic constant folding

Project invariant fixed?

Fold branches.

Environment fixed?

Fold.

Architecture selected?

Fold alternatives.

Workers get specialized programme.


---

53. Dead capability elimination

If project cannot use capability:

don't expose it.

No tokens.

No branch.

No accidental invocation.


---

54. Mission specialization becomes continuous

Generic CPP might know 1.000 capabilities.

Current DWS epoch may need 9.

Compiler specializes runtime to 9.

After transition:

maybe 5.

This solves capability-growth context inflation.


---

55. Semantic linked executable

Ultimately each Work Unit gets something analogous to a linked binary:

required policies;

required state;

required tools;

required proofs;

required transforms.

Nothing else.

No giant general-purpose prompt.


---

56. Model-independent continuation

A Work Unit should be executable by:

Claude;

another provider;

local model;

deterministic engine

without mission state living in wording.

This also enables provider arbitrage safely.


---

57. Cognitive ABI stability

The semantic interfaces should be stable:

Goal;

State;

Unknown;

Proof;

Effect;

Authority;

Receipt.

Then underlying models can change without rewriting institution.


---

58. Multi-provider bidding

For one interrupt, available solvers can have cost profiles.

Pick expected verified winner.

Not necessarily cheapest model.

Potential future architecture:

provider/model strategies compete offline.

Champion chosen per Work Class.


---

59. Model ensemble only where information value justifies it

No automatic reviewer.

Independent second model only when:

expected risk reduction > cost.

Otherwise deterministic proof.


---

60. Reviewer extinction

If historical reviewer output correlates 99.9% with machine proof:

candidate remove.

Shadow test.

Then retire reviewer.


---

61. Planner extinction

Same.

If planner output can be recreated from Goal IR + constraints:

planner dies.


---

62. Coordinator extinction

If coordinator mostly:

checks states;

launches workers;

writes handoffs;

it becomes control plane.


---

63. Researcher extinction for known domains

If queries are structured and sources known:

query planner.

Research model only interprets unresolved ambiguity.


---

64. Executor extinction for known transforms

Already covered, but global.

Known transform → compiler backend.


---

65. Debugger extinction for known failures

Failure motif → diagnosis function → repair transaction.

Eventually guard prevents.


---

66. Agent extinction as maturity metric

Counterintuitive but powerful:

a mature system may have fewer Agents, despite more capability.

Because roles become machinery.


---

67. Role Extinction Rate

Track:

planner;

reviewer;

coordinator;

researcher;

executor

functions compiled away.

Not people/models permanently; role occurrences.


---

68. Hot knowledge must pay rent or become cold

Any fact repeatedly hot with low utility:

cold.

Any cold fact repeatedly faulted:

promote.

Generational semantic memory.


---

69. Knowledge promotion/demotion autonomously

New insight:

young.

Used frequently:

promote.

Stable rarely needed:

cold.

Superseded:

archive.

This prevents Knowledge Vault inflation.


---

70. Institutional entropy budget

Knowledge growth produces:

duplicates;

conflicts;

aliases;

stale owners.

Semantic defrag daemon keeps canonical state compact.

Otherwise context retrieval cost creeps upward.


---

71. Global knowledge compaction

Not summaries.

Structural:

same fact → one canonical object.

Variants → provenance.

History → cold.

This avoids summaries-of-summaries rot.


---

72. Economic truth itself needs invalidation

A cost theorem like:

“Sonnet saves only 6% here”

depends on:

prices;

cache pricing;

models;

workload.

If any dependency changes:

stale.

Never turn economics into permanent dogma.

The current DWS measurement specifically says Sonnet saves only about 6% under today's prices and current cache-dominated profile. 


---

73. Economic Theorem Store

So economic findings themselves become versioned semantic objects.

Applicability.

Dependencies.

Reopen conditions.

Exactly like engineering facts.


---

74. Autonomous Economic Scientist

Not an always-on Agent.

Mostly statistical machinery.

Detects:

cost anomaly;

policy regression;

new workload phenotype.

Only model invoked for genuine hypothesis generation.


---

75. Experiments should optimize information gain per token

If we don't know whether 70% of DWS calls are control-loop vs implementation:

run cheapest experiment distinguishing them.

Don't build five optimizations first.

Scientific Economic Plane decides.


---

76. Sequential experimentation

Stop once posterior/confidence sufficient for decision.

Don't consume fixed 10M research budget.


---

77. Causal interaction search

Maybe reducing ContextImage changes repair rate.

Maybe worker fission raises startup cost.

Need interactions.

But don't brute-force all.

Search only plausible high-value interaction edges.


---

78. Shadow execution estate

Compile old and challenger policies for historical missions.

Compare.

No side effects.

Then only canary winners.

This makes global optimization safe.


---

79. Universal Holdout Estate

No universal CBR promotion until:

different domains.

Otherwise DWS-specific trick contaminates CPP.


---

80. Economic mutation testing

Deliberately violate optimization assumption.

Example:

remove required context page.

Does deopt recover?

Feed malformed state.

Does compiler refuse?

This proves savings haven't weakened correctness.


---

81. Optimization proofs themselves should be reusable

Once policy P is proven safe for Work Class family F:

don't re-review policy every project.

Link proof.


---

82. Global Cognitive CI

Each CPP change should test:

functional regressions.

And economic regressions:

hot tokens;

tool-schema rent;

calls;

context;

proof radius;

decision surface.

This prevents slow token inflation.


---

83. Economic budgets become SLOs, not fixed magic numbers

For stable Work Class:

p50/p95.

If cost drifts:

investigate.

Don't freeze historical token cap forever.


---

84. Institutional Cognitive Deflation SLO

Ultimate longitudinal test:

same normalized work.

Month 1: X.

Month 3: lower.

Month 12: much lower.

If rising despite more knowledge:

critical architecture regression.


---

85. Cognitive entropy-to-capital conversion rate

New KPI:

how quickly unknown cognition becomes reusable infrastructure.

Higher = institution compounds faster.


---

86. Knowledge embodiment latency

Time:

lesson discovered

→ enforced machinery.

Lower.

If lesson sits in Markdown for 6 months:

high rent.


---

87. Decision half-life

How long recurring decision remains cognitive before extinction.

Lower.


---

88. Failure half-life

How long recurring failure remains debuggable rather than prevented.

Lower.


---

89. Owner-dependency half-life

How long repeated mechanical human interaction remains human.

Lower.


---

90. Prompt half-life

How long procedural instruction remains hot before embodiment.

Lower.


---

91. Model-boundary half-life

How long recurring semantic transition requires an LLM.

Lower.

These half-lives together show institutional maturity much better than raw token savings.


---

92. Global Cognitive Debt

Combine:

Token Debt.

Decision Debt.

Context Debt.

Proof Debt.

Owner Debt.

Architecture Cognitive Debt.

Failure Debt.

Each has interest.

Technical Capital Allocator chooses which to repay.


---

93. Cognitive debt interest is actual future burn

Not subjective severity.

Expected recurrence × expected excess cost.

This turns architecture prioritization into economics.


---

94. Global Cognitive Balance Sheet

Assets:

certified transforms;

proof objects;

semantic caches;

indices;

failure immunities;

typed state;

compiled policies.

Liabilities:

all debts above.

Track whether net institutional capital grows.


---

95. Cognitive capital depreciation

A transform unused for a year.

Model improves.

API changes.

Maybe maintaining primitive costs more than saved cognition.

Retire it.

The system should not accumulate optimization junk.


---

96. Baseline should become smaller as capability grows

A huge insight.

If each new capability adds:

500 prompt tokens,

CPP eventually collapses.

Therefore:

functional capability ↑ while baseline prose ↓ or bounded.

This should be a hard SLO.


---

97. Zero-Prose Baseline Ratio

What percentage of CPP guarantees require no model awareness?

Target eventually very high.

Not because docs vanish.

Because behavior is embodied.


---

98. Universal compile-or-archive law

Repeated prose either:

becomes machinery

or

goes cold.

Avoid permanent hot doctrine.


---

99. Global “Why am I still…” profiler

CPP should continuously detect five questions from telemetry:

Why am I still reading this?

Why am I still deciding this?

Why am I still transporting this?

Why am I still spawning a model/Agent for this?

Why does Owner still need to do this?

Not as five LLM prompts.

As economic anomaly detectors.


---

100. And one more: Why does this Work Unit exist at all?

This is perhaps strongest.

The most efficient worker is a Work Unit eliminated before birth.

Proof of Non-Work should sit before every spawn.


---

The global architecture I would ultimately target

At the extreme, Claude Power Pack becomes something like a self-optimizing cognitive computer:

Reality Layer
Only deltas enter.

Canonical Semantic State
Current truth, typed and versioned.

Constraint/Theorem Layer
Known invariants remove branches.

Economic Science Plane
Measures reality, detects waste, falsifies hypotheses.

Cognitive Demand Compiler
Finds irreducible unknowns.

Extinction Compiler
Deletes work, reads, decisions, models, Agents, proofs, handoffs.

Semantic Superoptimizer
Chooses/restructures execution.

Context/Tool Linker
Produces tiny working set.

Deterministic Execution Runtime
Executes all mastered work.

Cognitive Interrupt Runtime
Models/humans resolve frontier only.

Proof Compiler
Assurance below model.

Embodiment/JIT Layer
Repeated cognition becomes primitives.

Technical Capital Allocator
Chooses what to compile next.

Scientific Evolution Layer
Replay, shadow, holdout, mutation.

CBR
Promotes winners and retires obsolete representations.

And all of that shares one invariant:

> INSTITUTIONAL INTELLIGENCE MAY APPROACH ARBITRARY SCALE WHILE ACTIVE COGNITIVE SURFACE REMAINS BOUNDED — AND FOR MASTERED WORK, DECREASES.




---

The DWS document currently says the all-unblocked programme could extrapolate to 57.105 calls and 14,5B candidate / 17,3B with margin / 24,3B ceiling under current profiles. 

At the extreme, I would forbid CPP from interpreting those values as “required resources”.

They are:

> a quantified description of how expensive the current execution architecture is.



The required resource is unknowable until we compute the Irreducible Cognitive Lower Bound and compile away the rest.

So I'd elevate a new global constitutional rule:

> HISTORICAL CALL AMPLIFICATION MAY BE USED TO PRICE THE OLD EXECUTION STRATEGY, BUT NEVER TO DEFINE THE INTRINSIC COST OF THE SEMANTIC OUTCOME.



And one above it:

> THE PURPOSE OF CLAUDE POWER PACK IS TO DRIVE THE MARGINAL COGNITIVE COST OF MASTERED ENGINEERING WORK TOWARD ZERO WHILE PRESERVING SCOPE, ASSURANCE AND REALITY.



Then DWS is no longer merely something to optimize.

It becomes the genesis benchmark for an estate-wide Universal Cognitive Deflation Runtime, and every capability built to collapse its 424 calls/step must automatically make every compatible future project cheaper too.

Ha pensado durante 20s

Sí. Y al extremo ya no hablaría de “optimización global de tokens” como una feature. Lo convertiría en una propiedad termodinámica del estate de Claude Power Pack:

> A medida que CPP acumula conocimiento, pruebas, tooling y experiencia, la cantidad de cognición necesaria para ejecutar trabajo ya dominado debe disminuir, no aumentar.



DWS demuestra por qué hace falta este salto. El sistema ha gastado 2,04B tokens y 8.066 calls para 19 avances de matriz —424 calls por claim-step— y después proyecta el mismo régimen hasta 25.683 calls y 6,5B tokens sólo para el scope actualmente runnable.   El propio análisis ya identifica que cambiar Opus→Sonnet sólo mueve aproximadamente un 6%, mientras calls por claim, 253K de contexto y reverificaciones son los grandes levers. 

La respuesta extrema es dejar de optimizar cada workload y construir una economía computacional cognitiva global.

Universal Cognitive Deflation Fabric

No sería otro OS encima de CPP.

Sería el comportamiento económico común de todo CPP.

Cada vez que cualquier proyecto quiere comprar cognition:

DWS
Sidecar
Reconstruction Factory
Apollo X
QuickLease
KobiiCraft
un proyecto futuro

todos pasan por el mismo mercado/compiler institucional.

La ecuación deja de ser:

Task → Agent → tokens

y pasa a ser:

Desired State − Certified Current State = Semantic Demand

y después:

Semantic Demand → deduplicate → propagate constraints → eliminate known work → share derivations → reuse proof → compile deterministic operations → price unresolved uncertainty → purchase only irreducible cognition.


---

1. El objeto fundamental sería el Global Semantic Demand Graph

No empezaría por Work Units.

Ni siquiera por Goals.

Construiría un grafo global de demanda semántica todavía no satisfecha.

Un Goal puede contener 100 claims.

Pero quizá esos 100 claims dependen realmente de:

7 facts nuevos;

3 decisiones;

2 observations;

1 architecture theorem.

Eso es lo que existe económicamente.

Los 100 claims son consumers.

Entonces:

100 claims ≠ 100 cognitive tasks.

Pueden ser:

13 semantic demands + 87 derivations.

Ésta puede ser una reducción brutal.


---

2. Obligations y computations se separarían

Hoy tendemos a mezclar:

“hay que demostrar claim X”

con:

“hay que llamar a Claude para resolver claim X.”

Incorrecto.

Una obligation puede satisfacerse mediante:

existing state;

another stronger proof;

constraint implication;

existing theorem;

known transform;

production observation;

model;

human.

Así que habría dos grafos diferentes:

Obligation Graph

qué debe ser verdad.

Y:

Computation Graph

qué nueva información realmente hay que comprar.

El segundo debería ser muchísimo más pequeño.


---

3. Global Proof of Non-Compute

Ya hemos hablado de:

Proof of Non-Work.

Proof of No Cognition.

Yo lo llevaría a un:

Proof of Non-Compute

Antes de realizar cualquier operación cara:

¿el desired semantic state ya es derivable?

No sólo mediante stored answer.

También mediante:

transitive theorem;

stronger proof;

constraint propagation;

another Goal's result;

current runtime state.

Si sí:

computation does not exist.


---

4. Estate-Wide Semantic E-Graph

Esto sería muy potente.

En compiler optimization, e-graphs almacenan múltiples representaciones equivalentes.

CPP podría mantener equivalencias como:

Goal A

≈ theorem T + transform X.

Claim B

≈ proof Pstrong.

Workflow C

≈ transaction Z.

Entonces el superoptimizer puede buscar entre equivalencias la ejecución de menor coste.

No una única receta estática.


---

5. Global Cognitive Superoptimizer

El compiler debería poder preguntar:

¿Cuál de todas estas ejecuciones equivalentes minimiza:

Expected Verified Cognitive Cost

sin empeorar:

correctness;

proof;

risk;

authority;

Production Reality?

Podría escoger:

existing artifact.

deterministic transform.

shared derivation.

small model.

frontier model.

reality observation.

Owner.

O una combinación.

Ésa sería la verdadera optimización global.


---

6. Semantic Common-Subexpression Elimination en TODO CPP

No sólo dentro de una misión.

Ejemplo:

DWS necesita saber:

“qué capa es propietaria del WorkspaceRef.”

Sidecar necesita lo mismo.

Otro Goal también.

No tres investigaciones.

Canonical semantic expression:

ResolveOwner(WorkspaceRef, dependency epoch X)

Una computation.

N consumidores.


---

7. Incluso cognition en curso se vuelve recurso compartido

Global singleflight:

Worker A empieza derivation D.

Worker B necesita D.

No:

B starts D2.

B subscribes.

Worker C arrives.

Subscribes.

Cuando D termina:

all receive projection.

Esto puede importar muchísimo con decenas de procesos.


---

8. Cognitive Exchange

Llevándolo todavía más lejos, CPP puede tener un mercado interno de semantic demand.

Cada unresolved object tiene:

number of consumers;

blocking fan-out;

consequence;

freshness;

estimated resolution cost;

reuse probability.

Entonces scheduler puede decir:

> Esta investigación cuesta 800K pero desbloquea 31 obligations de cuatro projects.



Más importante que:

> esta WU lleva más tiempo en READY.



Éste sería un information-leverage scheduler.


---

9. Shadow Price of Knowledge

Una nueva derivation no vale sólo por resolver su task.

Tiene un:

Institutional Shadow Value

Expected future consumers

× avoided cognition

× useful lifetime

× confidence.

Esto permite gastar más cognition hoy cuando crea enorme reusable capital.


---

10. Knowledge Fan-Out becomes capital allocation

Ejemplo conceptual:

Decision A cuesta 2M.

Sólo afecta una pantalla.

Decision B cuesta 5M.

Se convertirá en baseline de 1.000 Work Units.

Puede ser mucho mejor comprar B primero.

La prioridad pasa de:

task urgency

a una combinación de:

urgency + downstream fan-out + information value + capital return.


---

11. Cognitive Demand Netting

Todavía más global.

Dos Goals pueden pedir cosas opuestas o solapadas.

Antes de comprar cognition:

netear demandas.

Por ejemplo:

Goal A necesita saber si capability X existe.

Goal B planea construir X.

Primero resolve existence.

Quizá B desaparece.

Esto es literalmente netting financiero aplicado a trabajo cognitivo.


---

12. Global Work Extinction Before Allocation

Technical Capital Allocator no debería asignar presupuesto a un Goal antes de:

global dedup;

dependency propagation;

proof implication;

negative knowledge;

shared demand analysis.

No financiar duplicación primero y descubrirla después.


---

13. Universal Semantic IR

Para que todo esto funcione, CPP necesita una pequeña IR estable.

No mega-schema.

Sólo primitives universales como:

Goal.

Obligation.

Fact.

Unknown.

Decision.

Invariant.

Proof.

Effect.

Authority.

Capability.

Continuation.

Failure.

Artifact.

Invalidator.

La inteligencia institucional vive aquí.

Claude wording no.


---

14. Markdown pasa a ser view, no state

Esto es enorme.

STATE.md.

handoffs.

plans.

reports.

Son interfaces humanas.

Canonical state debería ser semantic IR.

Entonces un worker no “lee el estado”.

Hace una query al estado.


---

15. Global Semantic SSA

Fact X tiene una versión actual.

Decision Y depende de X.

Proof P depende de Y.

Cuando X cambia:

se invalida la closure.

No releer toda la historia.

No narrar:

“primero pensábamos A, luego B”.

Current state wins.


---

16. Global incremental compilation

Cada cambio de realidad recompila sólo affected closure.

No:

mission restarted → entire reasoning again.

Sí:

Reality Delta

→ invalidated nodes

→ affected compilation

→ new minimum execution graph.

Exactamente como incremental compiler/build system.


---

17. Build-system semantics para cognition

Piensa en Bazel/Ninja, pero para intelligence.

Inputs unchanged?

No rebuild.

Proof unchanged?

No reproof.

Decision dependencies unchanged?

No rethink.

Source version unchanged?

No reread.

Tool observation still valid?

No reprobe.

Esto puede eliminar enormes cantidades de cognition.


---

18. Content-addressed cognition

Derivations podrían identificarse por:

semantic request

- 

inputs/dependency hashes

- 

proof requirement.

Mismos inputs:

same result reusable.

Dependency changes:

cache miss.

Mucho más fuerte que conversational memory.


---

19. Global Read-Once Fabric

Un artifact version:

read/parse/index once.

Subsequent workers query:

symbols;

claims;

owners;

dependency closure;

diffs.

No volver a consumirlo en modelos.

Especialmente importante para gigantes:

source;

specs;

logs;

datasets.


---

20. Global Reason-Once Fabric

Similar:

same question

- 

same dependencies

- 

same semantic requirements

= reuse.

No “recuerdo que pensamos esto”.

Canonical derivation.


---

21. Global Fail-Once Fabric

Una tercera:

Known failure under same causal envelope.

Future occurrence:

diagnose automatically.

Eventually prevent.

No debugging again.


---

22. Global Prove-Once Fabric

Una proof object debería declarar:

proposition;

dependencies;

evidence;

strength;

scope;

invalidators.

If still valid:

reuse.

No re-verification by session boundary.


---

23. Stronger proof can subsume weaker proof

Proof graph supports implication.

If Pstrong proves invariant I:

claims C1–C20 may inherit.

This can collapse huge verification trees.


---

24. Global Reality-Once Fabric

Observations also reusable within valid reality epoch.

If ten claims need:

same host state;

same mobile state;

same deployment state,

one observation.

Fan-out evidence.


---

25. Reality acquisition becomes set-cover optimization

This is a genuinely interesting optimization.

Given:

claims C.

Possible observations O.

Each observation proves subset of C.

Find low-cost observation set covering required evidence.

Then a 60-minute physical test might become 10 minutes.


---

26. Owner Interaction Compiler global

Same idea.

Instead of asking you ten times:

collect all Owner-only uncertainties that can be resolved in one decision session.

Batch them.

But only when delay does not hurt.

Owner cognition also gets optimized globally.


---

27. Cognitive futures

Another extreme idea.

CPP may know that soon several Goals will need the same expensive fact.

It could precompute only if:

probability × avoided future cost

exceeds

current computation cost + staleness risk.

This is cost-aware semantic precomputation.

Not speculative LLM spam.


---

28. Knowledge volatility pricing

Every semantic object has volatility.

Stable theorem:

long-lived.

Repo HEAD fact:

valid until change.

Provider pricing:

until pricing version changes.

Current UI state:

short-lived.

Reuse policy based on invalidation risk.


---

29. Cognitive cache replacement policy

What stays hot?

Not simply LRU.

Use:

reuse probability;

reload cost;

size;

volatility;

downstream importance.

A semantic equivalent of weighted caching.


---

30. Cognitive page-fault economics

If an object was not loaded and turns out required:

page fault.

Track cost.

Too many faults:

increase working set.

Too much unused context:

shrink.

CPP learns its optimal ContextImage automatically.


---

31. Context eBPF equivalent

At the extreme, I would instrument context like systems engineers instrument CPU/memory.

Which semantic object:

entered which call;

for how long;

was referenced by which decision;

caused which downstream effect?

Not perfect attribution.

But enough for flamegraphs.


---

32. Global Context Flamegraph

Across CPP:

what consumes most resident tokens?

Maybe:

CLAUDE.md.

tool definitions.

STATE files.

plans.

logs.

Skill docs.

Then optimization follows measured rent.

Not opinions.


---

33. Semantic object rent

Each object:

size × resident calls × consumer reach.

And:

actual useful accesses.

High rent + low utility:

evict/compile.


---

34. Context ownership

Every hot semantic object should know:

why hot?

who consumes?

when can retire?

If no answer:

garbage.


---

35. Global Context Garbage Collector

Automatic semantic GC across:

workers;

projects;

institutional baseline.

Not deleting knowledge.

Moving knowledge out of active cognitive surface.


---

36. Generational institutional memory

Young:

new, uncertain.

Mature hot:

high reuse.

Old stable:

cold index.

Superseded:

archive.

This prevents knowledge accumulation from turning into context accumulation.


---

37. Knowledge is not valuable until liquid

A 100-page insight nobody can cheaply apply is economically illiquid.

A typed theorem with:

applicability;

dependencies;

proof;

owner

is liquid.

Optimize:

knowledge-to-action cost.


---

38. Knowledge Liquidity Market

Technical Capital Allocator can identify expensive-to-activate knowledge and invest in:

index;

schema;

primitive;

API.

This turns static knowledge into reusable capability.


---

39. Semantic compression benchmark

Grow knowledge 10×.

Representative Work Unit active context:

same or less.

If it grows 10×:

fail.

This should be one of the strongest CPP scaling tests.


---

40. Capabilities also must virtualize

Install 1.000 capabilities.

Current worker should not see 1.000.

Capability linker chooses 5.

Thus:

capability count does not imply context count.


---

41. Tool universe virtualization

Same.

Worker doesn't know every tool.

Gets:

linked execution interface.

If unexpected need occurs:

dynamic link.

No giant schema prefix.


---

42. Model universe virtualization

Same concept for models/providers.

The Work Unit doesn't care whether Claude/GLM/local executes.

It requests:

semantic capability class.

Router chooses implementation.


---

43. Provider arbitrage becomes automatic

Not just price.

Expected verified cost:

provider cost

- context floor

- retries

- tool reliability

- proof burden

- latency.

Winner chosen per Work Class.


---

44. Information Quality-of-Service classes

Different unknowns deserve different cognition.

Safety-critical architecture:

frontier + strong proof.

Known formatting:

deterministic.

Low-risk bounded transform:

cheap resolver.

No one-model-fits-all.


---

45. Cognitive microkernel

The hot universal CPP core should become extremely small.

It only needs laws around:

Reality.

Authority.

State.

Effects.

Evidence.

Proof.

Learning.

Everything else dynamically linked.

This is how CPP can get more capable while prompt gets smaller.


---

46. Constitutional compiler

Every time a new Hard Rule proves stable, ask:

Can it become:

type?

schema?

guard?

API?

test?

runtime transition?

If yes:

compile.

Then remove duplicate hot instruction.


---

47. Constitutional Residual as debt

Some constitutional principles genuinely need model judgment.

Keep them.

Everything mechanical remaining in prose:

debt.

Measure.


---

48. Baseline Zero-Prose Ratio

Track:

what fraction of baseline correctness no longer requires reading instructions.

Mature:

high.

Not because docs disappear.

Because execution embodies them.


---

49. Prompt extinction becomes an explicit compiler pass

Rule embodied?

Find all duplicated prompt clauses.

Prove they are redundant.

Retire.

This creates negative token growth as capability increases.


---

50. Tool instruction extinction too

Tool behavior stable and typed?

Reduce description.

Progressive disclosure for edge cases.


---

51. Proof instruction extinction

Proof contract encoded?

No need to tell every worker “remember to run X”.

Proof Compiler owns it.


---

52. Handoff instruction extinction

Continuation Compiler exists?

No handoff prose rules inside every worker.


---

53. Global role extinction

Track role occurrences that become machinery:

planner;

researcher;

reviewer;

coordinator;

recovery agent;

closeout worker.

Mature system may have more capability and fewer Agent roles.


---

54. Agent count becomes anti-KPI for mastered work

For novel research, fine.

For routine Work Class:

multiple Agents = suspicion.

Could be necessary.

But must justify.


---

55. Decision Surface Area global

Count recurring decisions still exposed to models/humans.

This may matter more than total tokens.

Target:

monotonic decrease for mastered domains.


---

56. Decision Surface Density

Decisions exposed per verified state transition.

Should decline.


---

57. Cognitive Interrupt Architecture globally

Models sit outside deterministic path.

Unknown event:

interrupt packet.

Model resolves.

Result becomes state/theorem.

Return.

This architecture makes reasoning observable and attributable.


---

58. Interrupt provenance

Every model call knows why it happened:

NOVELTY.

ASSURANCE.

STATE_MISS.

TOOL_MISS.

CONTROL_LOOP.

CONTEXT_FAULT.

RECOVERY.

OWNER_BOUNDARY.

Then we know whether call existence is healthy.


---

59. Interrupt purity target

For mature Work Classes:

most remaining model calls should be:

NOVELTY or NECESSARY_ASSURANCE.

Anything else:

institutional debt.


---

60. Semantic Interrupt Budget

Instead of only token/call cap:

expected irreducible interrupts.

If predicted 2 but actual 15:

stop/recompile.

This catches pathological call amplification much earlier than billions of tokens.


---

61. Global Call Amplification Ratio

Physical model boundaries

/

irreducible semantic boundaries.

DWS' 424 calls/claim-step is currently a strong warning signal, even though claim-step itself still isn't the ideal semantic denominator. 

Eventually use true semantic boundaries.


---

62. Semantic Progress Velocity

Durable semantic transitions per million processed tokens.

Should climb over time.

Not raw commits.


---

63. Verified Novelty Yield

Reusable new verified information per unit of cognition.

High is good.

A mission consuming 20M to discover a reusable theorem may outperform one consuming 5M on disposable coordination.


---

64. Cognitive Capitalization Rate

What fraction of spend became reusable capital?

Product-only OPEX.

Versus:

product + theorem + primitive + proof.

Target upward where applicable.


---

65. Every expensive incident must capitalize

If DWS spends 107M on a claim-step:

we cannot accept “claim done” alone.

Economic system should ask:

what did we learn that makes next related step cheaper?

No answer:

poor capitalization.


---

66. Automatic post-spend capitalization

After high-cost Work Unit:

extract:

new theorem?

new failure motif?

new transform?

new proof?

new index?

new context profile?

Then register.

Not manual retrospective.


---

67. Cost-of-ignorance ledger

Interesting complementary idea.

Not resolving some unknown also costs money:

blocked Goals;

duplicated work;

Owner delays.

Track expected cost of ignorance.

Then decide when research is worth buying.


---

68. Cost-of-staleness

Using stale knowledge also has expected repair cost.

This balances aggressive reuse.

Don't optimize tokens by blindly trusting old state.


---

69. Cost-of-proof debt

Skipping proof now may create future repair.

Assurance optimizer should compare lifetime costs.

This prevents token-minimization from damaging quality.


---

70. Cost-of-context omission

Similarly:

tiny ContextImage might increase retries.

Profile total cost.

No fetish for minimal prompts.


---

71. Total Verified Cost is the objective

The global optimizer minimizes:

execution

- expected repair

- proof

- recovery

- human interruption

- future maintenance

- recurring context rent.

Not just tokens today.


---

72. Global Economic E-Graph

Represent alternate implementation/execution strategies and their costs.

As measurements evolve:

cost changes.

Optimizer picks champion.

This allows continuous plan improvement without rewriting every prompt.


---

73. Champion/challenger at every layer

Context strategy.

Model router.

Work Unit size.

Proof strategy.

Tool transaction.

All can have challenger.

Offline/shadow first.

Live canary.

Promote winner.


---

74. Automated regret accounting

After execution:

was another known strategy likely cheaper?

Estimate regret.

Repeated regret:

policy update.

This makes scheduler learn.


---

75. Counterfactual replay factory

Historical traces are enormously valuable.

Replay policies offline.

No need to spend live billions to test every optimization.

DWS' existing 8.066 calls become a benchmark corpus, not only sunk cost. 


---

76. Distill expensive history into microbenchmarks

Don't replay whole mission every CI.

Extract:

representative context-heavy task;

proof-heavy task;

coordination-heavy;

novel task;

visual task.

Global Economic CI stays cheap.


---

77. Cognitive mutation testing

Break optimization assumptions deliberately.

Context page missing.

Cache stale.

Tool projection incomplete.

Singleflight producer dies.

Does system deopt safely?

Savings machinery needs adversarial proof.


---

78. Optimization correctness proof

Every saving mechanism needs to demonstrate:

Scope preserved.

Assurance preserved.

Production Reality preserved.

Otherwise cheap but wrong isn't optimization.


---

79. Economic safety envelope separate from learned policy

Learned optimizer can change.

Authority/security/proof minimums deterministic.

No RL-like opaque economy overriding constitution.


---

80. Capital allocator becomes portfolio optimizer

It sees candidates:

Context compiler improvement.

Proof transaction.

Module refactor.

Tool ABI.

Negative-knowledge index.

Which produces largest discounted lifetime saving?

Build that.


---

81. Cognitive investment diversification

Don't spend all meta-budget attacking one hypothesis.

Portfolio can balance:

high-confidence modest return;

high-upside experiment;

necessary infrastructure.

But bounded.


---

82. Meta-optimization stop-loss

If optimization programme itself exceeds expected payback:

stop.

Critical.

Otherwise we'll burn billions saving millions.


---

83. Meta-Cognitive Tax hard SLO

Percentage of cognition used to manage/optimize cognition.

Should trend downward.

Cognitive Economics itself must become mostly deterministic.


---

84. Self-hosting recursively

Eventually:

Context Compiler modification uses Context Compiler.

Proof Compiler uses Proof Compiler.

Capital Allocator experiments use Economic Science Plane.

That's mature self-hosting.


---

85. Cross-project transfer proof

Universal capability built from DWS must make another compatible workload cheaper.

Otherwise:

DWS-local.

Don't prematurely CBR universal.


---

86. Reverse transfer

Improvement discovered elsewhere should make DWS cheaper later.

This proves estate-level compounding is bidirectional.


---

87. Global Economic Theorem Registry

Economic findings themselves become reusable.

For example:

Under profile P:

model downgrade has low value because cache dominates.

But only while dependencies remain true.

The DWS file explicitly frames the ~6% Sonnet saving as dependent on today's pricing/cache-heavy workload. 

So theorem has invalidators:

pricing.

provider.

context mix.


---

88. No global folklore

No hard-coded:

“Sonnet saves 6%.”

Instead:

conditional theorem.

When price changes:

invalidate.

Re-measure cheapest affected slice.


---

89. Global negative investment memory

Gen1 already conceptually points this way.

If optimization was falsified under same envelope:

don't research it again.

The Gen1/Gen2 material explicitly argues that the end state is a closed loop where Gen1 discovers economic truth, Gen2 compiles/extinguishes work, and CBR propagates it. 

This should become universal.


---

90. Global “why does this exist?” hierarchy

For every expense:

Why does this Work Unit exist?

Why does this Agent exist?

Why does this call exist?

Why does this context object exist?

Why does this proof exist?

Why does this Owner interaction exist?

Why does this rule exist?

If the answer is historical inertia:

candidate extinction.


---

91. Zero-work is superior to zero-model

Important hierarchy.

Best:

no Work Unit.

Next:

deterministic Work Unit.

Next:

small cognition.

Worst:

large repeated frontier cognition.

Don't celebrate zero-model if unnecessary physical work still exists.


---

92. Zero-proof is sometimes superior to proof reuse

If architecture makes invalid state impossible:

certain proof classes can disappear.

Again:

embodiment beats caching.


---

93. Zero-context is sometimes superior to context compression

If no decision remains:

don't send compressed context.

Delete cognitive boundary entirely.


---

94. Zero-tool-call is superior to tool batching

If state plane already has answer:

don't query.


---

95. Zero-handoff is superior to compressed handoff

If control plane can advance:

no handoff.


---

96. Zero-Agent is superior to cheaper Agent

If transaction suffices:

no Agent.


---

97. Zero-Owner-operation is superior to a concise request

If authorized policy exists:

execute.


---

98. Extinction-first compiler ordering

So the global compiler priority becomes:

Eliminate Goal sub-obligation → eliminate decision → eliminate cognition → eliminate Agent → eliminate read → eliminate transport → eliminate proof → eliminate context → fuse remaining operations → route remaining cognition cheaply.

This ordering matters.


---

99. Universal Cognitive Deflation Contract

Every stable Work Class must satisfy:

recurrence cost should decline absent new novelty/assurance.

The Gen1/Gen2 dataset explicitly frames the mature outcome this way: known work trends toward zero model cognition, and the combined KPI becomes Institutional Cognitive Deflation rather than a fixed savings percentage.  

Make that constitutional.


---

100. The strongest possible endpoint

Ultimately CPP should work like this:

Owner expresses intent.

CPP computes semantic delta.

Most work vanishes because estate already knows it.

The rest becomes deterministic execution.

A tiny residue is genuine uncertainty.

That residue becomes a cognitive interrupt.

The best available intelligence resolves it.

Proof confirms it.

The new insight becomes institutional capital.

Next recurrence has a smaller uncertainty residue.

Repeat.

Eventually, for mastered domains:

Owner Intent → compiler → deterministic machinery → proof → outcome.

No Agent swarm.

No giant prompt.

No 253K context.

No 424 calls.

No planner.

No reviewer.

No coordinator.

No transcript.

No model unless reality actually introduced something new.


---

The hard global law I would put above Cognitive Economics is therefore:

> THE MARGINAL COGNITIVE COST OF MASTERED WORK MUST APPROACH ZERO AS INSTITUTIONAL INTELLIGENCE INCREASES.



And under it:

> ESTATE GROWTH MUST INCREASE AVAILABLE INTELLIGENCE WITHOUT PROPORTIONALLY INCREASING ACTIVE COGNITIVE SURFACE.



And the economic conservation law:

> EVERY MODEL TOKEN MUST ULTIMATELY BE ATTRIBUTABLE TO IRREDUCIBLE NOVELTY, NECESSARY ASSURANCE, OR THE CREATION OF INSTITUTIONAL CAPITAL THAT REDUCES FUTURE COGNITIVE DEMAND.



If CPP enforces those three laws, DWS's 6,5B-token projection stops being primarily a budget question.

It becomes a benchmark proving how much of today's engineering cognition we can make cease to exist globally.