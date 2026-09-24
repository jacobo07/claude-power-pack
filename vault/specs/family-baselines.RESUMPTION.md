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
- Ancla de coherencia: `python tools/test_family_baselines.py` -> 20/20; `tools/test_tower_inheritance.py` -> 16/16.

## Decisiones activas del Owner
Cuatro familias (web_surface, kobiicraft_mode, persistent_state, wii_homebrew). Promocion
AUTOMATICA al instante, el Owner revisa despues. KEOS vive en la GEX44 (no leido aun).

## Deuda medida (no tapar)
- Falsa activacion en preguntas de estado/meta (19_S1 §2) -> slice propio con predeclaracion.
- Harvest re-lee todos los learnings en cada Stop (150-630 ms en KobiiCraft) -> cursor.
- Lift verificado = 0 (C4).

## Proximas 3 acciones
1. **S2** B0 de las 4 familias desde gobierno ya sellado, cada entrada con fichero:linea verificado.
2. **S3** O0: cobertura de B0 sobre repos reales, commit ANTES de S4.
3. **S4** inyeccion por `cli.py` + control positivo + `CPP_FAMILY_BASELINES=off`.

## Empezar
Lee el spec §3-§6, corre las dos gates del ancla, y sigue por la primera accion no sellada.
