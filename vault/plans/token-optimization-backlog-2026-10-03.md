---
id: BACKLOG-TOKEN-OPTIMIZATION-2026-10-03
date: 2026-10-03
status: OPEN
covers: [token-optimization, weekly-limit, backlog]
machine_backlog: vault/plans/token-optimization-backlog-2026-10-03.json  # consumible por /what-now
---

# Backlog de optimizacion de tokens (2026-10-03)

Motivo: 76 % del limite semanal consumido en ~28 h desde la compra de la cuenta.

## Medicion (ventana 2026-10-02T12Z .. 2026-10-03T21Z)

Instrumento: scripts de solo lectura sobre `~/.claude/projects/**/*.jsonl`, deduplicados por
`message.id` y por realpath (los directorios `claude-power-pack` y `Apps-mcp-video-analyzer`
apuntan al mismo sitio; sin deduplicar sale 6,48B, deduplicado 4,86B).

| Hecho | Valor |
|---|---|
| Tokens de entrada+salida | 4,86B en 18.690 llamadas (98 % lectura de cache) |
| Contexto medio por llamada | ~260k tokens |
| Llamadas con contexto >=200k | 81 % de los tokens (200-400k: 64 %; 400-700k: 17 %) |
| Suelo fijo (1a llamada de cada sesion) | mediana 124k, p10 91k, n=168 |
| Opus / Sonnet / Haiku | 87 % / 13 % / ~0 % de los tokens |
| Sesiones principales concurrentes por hora | 7-37 (tipico 13-28) |
| Prompts humanos | 352 -> 39 llamadas y ~11M tokens por prompt |
| Sesiones con <=1 prompt humano (autonomas) | 114 sesiones, 32 % del gasto |
| Subagentes | 21 % del gasto; 42 % de ello en Opus |
| Proyecto que mas gasta | claude-power-pack: 1,61B (33 %) |
| Read (resultado medio) | 13,8 KB; 41 MB en total |
| Inyeccion de hooks como contexto | UserPromptSubmit 2,1 MB / 1.040; SessionStart ~9,7 KB por sesion; PreToolUse 1,0 MB / 2.206 |

Las estimaciones de ahorro de abajo son cotas superiores y no se han observado.

## Items (los IDs coinciden con el JSON)

### P0: comportamiento operativo (el Owner decide; sin codigo)
- **TOK-01 Sesiones concurrentes <=4.** El gasto escala linealmente con los paneles vivos. Cada panel paga ~124k de suelo en cada llamada. Accion: cerrar paneles; no ejecutar `/lazarus all` por defecto.
- **TOK-02 Congelar los programas meta de economia en PP.** Hoy se escribieron >=10 planes de economia (cognitive-economy, skill-residency, ACV c4-c6, CCP s16, KSR, r2-residency...). PP es el proyecto que mas gasta. La RCA ya concluyo (s18) que las palancas que quedan son profundidad x contexto, y eso lo cubren TOK-04/06, no mas instrumentacion.
- **TOK-03 Pausar Ralph/workers desatendidos.** Hubo sesiones de 1-8 h con <=1 prompt (Orca-X, TUA-X, PP). Lanzarlos solo cuando haya cuota de sobra.
- **TOK-04 Bajar el muro de contexto.** El rollover dispara a ~450k (45 % de 1M, RCA s11). Si se capan a ~200k las llamadas >=200k (12.657 llamadas, media ~311k), la cota superior de ahorro es ~35-40 % del total. Opciones: `/clear` en cada limite de tarea, modelo sin `[1m]`, o bajar el tier del watchdog (`modules/zero-crash/hooks/context-watchdog.py:44-54`).
- **TOK-05 Sonnet por defecto.** `/model sonnet` o `"model"` en settings. Opus solo para decisiones de arquitectura (coincide con la Session Cost Discipline regla 5, que hoy no se cumple).

### P1: configuracion
- **TOK-06 Suelo de 124k a <60k.** El inventario previo midio lo que se puede quitar: CLAUDE.md+rules 44,7k, listado de skills 6,5k, hooks 4,8k, MCP 2k, plugins 1,4k (`wiki/raw/2026-10-02-token-economy-internal-inventory.md`). Cada 10k menos de suelo equivale a ~187M tokens en esta ventana (~3,8 %). Objetivos: global CLAUDE.md 40.117 B (en el limite de 40k), PP CLAUDE.md 35.875 B (bloque HARD RULES con entradas de prueba como HR-002), MEMORY.md 16 KB.
- **TOK-07 Plugins/skills sin uso.** 280/319 skills nunca se invocan. Desactivar plugins enteros (gsd, bmad, carl) en los repos que no los usan. Superpowers inyecta su skill completa en cada SessionStart.
- **TOK-08 Hooks que inyectan texto en cada llamada.** Avisos de Woz, Cross-project baseline, Graph-First, Tower baseline (13 KB en este prompt) y SKILL ADVISOR. Una vez inyectado, el texto se queda en el contexto el resto de la sesion. Dejar solo los que bloquean algo real.
- **TOK-09 ULTRA / governance / USAP / vault reads como opt-in.** La doctrina obliga a 7 fases, lecturas de vault en STANDARD y a activar todas las skills. Eso explica parte de las 39 llamadas por prompt. PR-MODE-SELECTION-001 ya dice que ULTRA cuesta de 3 a 5 veces mas.
- **TOK-10 Subagentes en modelo barato.** `model: sonnet`/`haiku` en el frontmatter de los agentes (Explore, gsd-*, pp-*). La cota previa es <=3,8 % (inventario), pero es inmediato.

### P2: higiene
- **TOK-11 Read acotado.** Usar offset/limit y Grep antes de Read. La relectura previa estaba en el 19,6 %.
- **TOK-12 Recuperacion opt-in por panel.** El banner de SessionStart empuja a relanzar 7 paneles.
- **TOK-13 Cerrar paneles ociosos.** Segun el inventario previo, idle >1 h = 73 % de las reconstrucciones de cache.
- **TOK-14 Trabajos de fondo.** compound-learnings se auto-invoco 27 veces sin avanzar, y graphify/indexado reescribe `_knowledge_graph` (visto a las 23:32). Verificar cuales llaman al modelo.
- **TOK-15 Alarma que pueda disparar.** cost_gate usa 100M output/dia, con ~19M medidos, asi que nunca dispara. Hay que basarla en la fila de cuota del proveedor (RCA s15).

### P3: medicion
- **TOK-16** Excluir `.claude/worktrees/` de las busquedas (`.rgignore`).
- **TOK-17** Deduplicar por realpath en cualquier lector de transcripts (el junction duplica 1,6B).

### Diferido (bloqueado por: reset semanal)
- **TOK-18** El Owner eligio "esperar al reset" (2026-10-04). El prompt "Cognitive Microkernel / Context MMU" (/cpp-gsd-long) se tratara como obligaciones nuevas del Goal existente `cpp-cognitive-economy` (`vault/plans/cognitive-economy-program-2026-10-03.md`, done-gate `tools/test_cognitive_economy_program.py`). Modo EXTEND, sin Goal nuevo, sin Agent Teams, en Sonnet y con presupuesto fijo que decide el Owner. Prompt guardado verbatim: `vault/plans/cognitive-microkernel-brief-2026-10-04.md` (89 KB, ~22k tokens; NUNCA en la tarjeta de cada epoch, solo puntero).

**Configuracion APROBADA por el Owner (2026-10-05): "yes, arm it but after the quota weekly reset".**
**Reset semanal de esta cuenta: 2026-10-11 18:00 UTC (20:00 hora de Espana).** No armar antes.
- Host: GEX44 (`ssh gex44`, usuario kobii, cuenta nueva ya logueada). No hay clon de PP alli: crear uno propio segun la receta de armado en GEX44 (memoria `reference_gex44_mission_arming_recipe.md`).
- Perfil lean via `CLAUDE_CONFIG_DIR` solo para la mision (hoy GEX44 carga CLAUDE.md 25 KB, 23 rules, 186 skills, 95 agents, 134 hooks). Conservar los hooks de continuidad (context-watchdog, mission_wall/rollover_wall). Probar UNA rotacion real antes de dejarla desatendida.
- Modelo: Sonnet para ejecucion; Opus solo para el ULTRA-plan y la auditoria.
- Rollover a ~180k (no ~450k).
- Tope duro: 0,8B tokens. Estimacion 0,4-0,65B (sin optimizar 1,3-2,4B; ancla medida: familia cognitive-economy 1,71B / 6.245 llamadas / 273k ctx medio desde 10-02).
- Alcance: EXTEND del Goal `cpp-cognitive-economy`; pilares ya falsificados -> NO-BUILD de entrada; sin Agent Teams en el reality scan.
- Primera parada: reality scan + ULTRA-plan inline -> aprobacion del Owner antes de cualquier ejecucion desatendida.
