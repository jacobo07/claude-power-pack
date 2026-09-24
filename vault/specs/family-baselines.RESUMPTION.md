# RESUMPTION -- Baselines constitutivos por familia (Torre Universal)

**Repo:** `C:\Users\User\.claude\skills\claude-power-pack`, rama `feature/knowledge-acquisition`.
**Tesis:** lo que el Owner construye sube el baseline de su familia; cualquier mision nueva de esa
familia recibe ese baseline y lo implementa sin que se lo pidan. Spec:
`docs/superpowers/specs/2026-09-24-family-baselines-design.md` (T3).

## Estado sellado (git log es la verdad)
- C1 `8ad7bcf` captura automatica (landed commits -> bus -> ledger; tope arreglado).
- C2 `a6d2042` capa universal + lecciones como texto por `modules/gsd_x/cli.py`.
- C3 `b7bf685` 42 capsulas; tarea `PP-Tower-Capsules` registrada (03:45/15:45), probada: `state/tower/production.jsonl`.
- `247ffc0` spec + predeclaracion S1. `14d6c8a` S1 clasificador (20/20, drill 5/5).
- `c95ebbc` **S2 sellado**: B0 de las 4 familias, 60 entradas, cita literal anclada (15/15, drill 4/4).
- Ancla de coherencia: `tools/test_family_baselines.py` 20/20 · `tools/test_baseline_generations.py` 15/15 · `tools/test_tower_inheritance.py` 16/16.

## Decisiones activas del Owner
Cuatro familias (web_surface, kobiicraft_mode, persistent_state, wii_homebrew). Promocion
AUTOMATICA al instante, el Owner revisa despues. KEOS vive en la GEX44 (no leido aun).

## Deuda medida (no tapar)
- Falsa activacion en preguntas de estado/meta (19_S1 §2) -> slice propio con predeclaracion.
- Harvest re-lee todos los learnings en cada Stop (150-630 ms en KobiiCraft) -> cursor.
- Lift verificado = 0 (C4).

- **S3 sellado**: metodo `bf69726`, O0 `vault/tower/o0/O0_2026-09-24.json`, sondas sha256
  `b156db7ab3d80346` (O1 DEBE usar ese hash). Resultado: `vault/audits/ucr_cif/21_O0_RESULT.md`.
- Pendiente de revision del Owner: B0 `wii_homebrew-no-posix-headers` contradicha por CavEX.

## Proximas 3 acciones
1. **S4** inyeccion por `cli.py` + control positivo + `CPP_FAMILY_BASELINES=off`.
2. **S5** promocion automatica (decision del Owner) + `review`/`revert`; leer KEOS en la GEX44.
3. **S6** done-gate por mision (mide las 49 entradas PROCESS/RENDERED/DESIGN que O0 no puede).

## Empezar
Lee el spec §3-§6, corre las dos gates del ancla, y sigue por la primera accion no sellada.
