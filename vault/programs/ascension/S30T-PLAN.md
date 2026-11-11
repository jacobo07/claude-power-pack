# S30T: cuello de botella de tipos en KSR (prueba causal y, si se sostiene, contexto de tipos para todo el programa)

## Contexto
Esta misión busca saber si la falta de un modelo de tipos propio de KSR es la causa por la que miles de funciones no compilan o no casan. Si lo es, la misión quita ese freno con infraestructura reutilizable, sin tocar las garantías de certificación.

La copia de seguridad de este plan quedará en PP `vault/programs/ascension/S30T-PLAN.md` en cuanto lo apruebes.

## Realidad verificada hoy

**PROVEN (comprobado sobre el código y los datos):**
- **m2c no recibió ningún contexto en KSR.** `decomp_work/b8d1db7edd42/code/m2c_producer.py:155` lo invoca con `run(["--target","ppc-mwcc-c", src])`, sin `--context`.
- **El contexto de Tennis solo entra al compilar.** `tennis_context.h` (296 líneas, 37 structs) se antepone en `ksr_lane._source` (`pre + xform(raw)`).
- **Compilador y flags.** Compilador Wii/1.7 (sha `f54d5644`). Flags `cv1.FLAGS` y sus brazos sd0/sd8 (`ksr_lane.arms`). Juez: objdiff-cli 3.8.1 más `reloc_oracle` (E0).
- **Censo de NO_COMPILE ya hecho** (t1 `dd634c74`; regla fijada en `3f9f1d8d`):
  - 5,453 funciones;
  - primera causa no-cascada de tipo/prototipo/declaración: 5,248 (96.2%);
  - todas sus causas primarias son de tipos: 5,101;
  - fallos del traductor: 27; otros: 178;
  - incluso excluyendo `UNDEFINED_IDENT` y `UNKNOWN_TYPE_DECL`, el 75% sigue siendo de tipos.
  - Clasificador reutilizado: `diagnostics.parse_diagnostics`, que ya separa las cascadas (códigos 10141/10164/10564).
- **H3 (compilador) tiene poco peso.** El piloto `cmpswap` dio 3/300 CNM al 100% con otro mwcc (t1 `3eee351e`). La pasada completa (`cmpswap_full`, mía, t1 `ad6e0e4c`) sigue corriendo.

**OBSERVED (medido antes, solo en Tennis; nunca se aplicó a KSR):**
- **`m2c_proto` P1:** volver a pasar m2c con la firma propia de cada función subió las lifts limpias de 276 a 293 sobre 1,797 (`evidence/m2c-proto/summary.json`).
- **`shared_types` S1:** 15 de 69 dependientes NO_COMPILE pasaron a compilar, con 0 certificados perdidos (`evidence/ascension/s1/sweep.json`).
- **S18 W6 (modelo + `typectx`):** 79 de 80 NO_COMPILE pasaron a compilar (mediana ~95%), pero casi ninguno llegó a casar.
- **Conclusión previa:** los tipos desbloquean la compilación, pero el último tramo hasta casar es otro problema. Lo mediré por separado y no prometeré certificados.

**Infraestructura que ya existe y que se extiende, no se duplica** (`t1 modules/recon_fabric/`):
- `m2c_proto.py`: m2c con prototipos en el contexto (hoy atado a Tennis).
- `shared_types.py` / `shared_types_sweep.py`: un struct por global raíz.
- `typectx.py`, `shared_field.py`, `d12_struct.py`.
- `ksr_decl*.py` y `ksr_structural.py`: validez de declaraciones a partir de los objetos.
- `ksr_lane.PROFILES`: perfiles aditivos.
- `reloc_oracle.py`.

**Estado de la misión:**
- S29K está cerrada (checkpoint `b8695eed`).
- t1 está en `dd634c74`, escrito por mí.
- No hay otro escritor vivo en t1. Lo vuelvo a comprobar justo antes de armar.

## Hipótesis
- **H1 (faltan tipos)** pasa de PLAUSIBLE a la prueba causal (P1).
- **H2 (traductor):** 27/5,453, débil. Sigue abierta para la parte de las CNM.
- **H3 (compilador):** ~1%.
- **H7 (dependencias entre TUs) y H9 (el binario no determina un tipo único)** se controlan en P2.
- **H10 (pocos hechos compartidos explican muchas funciones):** se mide el efecto por prototipo o struct (ejemplo: `fn_801C1C90` bloquea 93 funciones).
- **H8 (el instrumento falla):** P0 lo valida.

## Fases (cada umbral y cohorte se fija en un commit antes de correr)

**P0. Cierre de la Gate A (≤0.5M tokens)**
- Reconciliar la población: frontier `ksr-v5r` y perfil `s25stage`, 9,269 certificados = 8,687 + 582.
- Validar el clasificador:
  - controles positivos sembrados (mutar fuentes certificadas: quitar un prototipo, dar a un campo puntero el tipo `long`, meter `?`); cada uno tiene que caer en su familia;
  - control negativo: 100 certificadas no deben dar ningún diagnóstico;
  - informar qué proporción son cascadas.
- Integrar el resultado de `cmpswap_full`.

**P1. Prueba causal, Gate B (≤3M)**
- Generalizar `m2c_proto` para que reciba el título como parámetro. Con Tennis por defecto tiene que salir byte a byte lo mismo que ahora; eso pasa a ser un gate.
- Contexto KSR v0, solo con hechos que fija el ABI:
  - la firma propia de cada función, sacada de sus lifts y de los registros que lee;
  - las globales con el tamaño observado.
  - Lo que no está determinado sale como `void *` o UNKNOWN, nunca como una suposición.
- Cuatro condiciones:

| Condición | Qué es |
|---|---|
| BASE | sin contexto, como ahora |
| TYPE-ONLY | `m2c --context ctxv0`, compilando con el mismo prelude más `ctxv0` |
| SHUFFLE | firmas permutadas dentro de la misma aridad (comprueba que importa el dato concreto) |
| TENNIS | `m2c --context` con el contexto de Tennis (comprueba el efecto de "cualquier contexto") |

- Control de determinismo: BASE re-ejecutado tiene que reproducir las lifts byte a byte.
- Cohortes:
  - desarrollo: 300 NO_COMPILE estratificadas por causa (incluidas las 27 del traductor y 50 "otros" como negativos), 200 CNM y 100 CERTIFIED;
  - **validación aparte:** 300 NO_COMPILE + 200 CNM que no se miran hasta el final.
- Medidas: compila, %, exacta, `reloc_oracle`, efecto en dependientes y coste.
- **Éxito:** en validación, TYPE-ONLY sube la tasa de compilación ≥ +10 pp sobre BASE y ≥ +5 pp sobre SHUFFLE, con 0 regresiones en CERTIFIED (bytes idénticos).
- **Si no se cumple:** se detiene la rama de tipos y el resto del presupuesto se redirige a la siguiente causa medida.

**P2. Gates C, D y G: tipos compartidos y consistencia entre TUs (≤6M + ≤4M)**
- Extender `shared_types` a KSR: un struct por global raíz, unión de los offsets, alternativas cuando los anchos chocan.
- Gate de regresión:
  - reconstruir **las 9,269** fuentes certificadas con el contexto nuevo; los objetos tienen que salir byte a byte iguales (patrón `s26e_e0_sweep`);
  - además `ksr_structural` y `reloc_oracle`.
- Un conflicto se queda en UNKNOWN; nunca se elige el "mejor".
- Mutantes sembrados (un prototipo incompatible, un ancho falso) tienen que ser rechazados.

**P3. Integración real, Gates E, H, I y J (≤5M)**
- Regenerar el lane como perfil aditivo nuevo (`ksr_lane.PROFILES`, por ejemplo `ksr-v5r-ctx1`). El generador de producción actual queda congelado como línea base.
- Barrer el frontier y medir por separado: compilan nuevas / suben de % / bajan de % / exactas / estructuralmente válidas.
- **Certificar canónicamente con el perfil nuevo es una decisión tuya**, como con S26C y su `owner_turn`. Es la única parada en la que la misión te pedirá algo: llegará con números y con certify sin cambios.

**P4. Transferencia, Gate M (≤3M)**
- El mismo operador sobre Tennis, sin ningún dato de KSR, comparado con la P1 histórica de Tennis.
- El veredicto de transferencia es honesto: si no transfiere, se registra como negativo.

**P5. Aprendizaje y cierre, Gates N–V (≤2M + 2M de reserva)**
- Volcar los resultados en las filas G09 de `recon-research.jsonl` (las probadas pasan a E4 o quedan refutadas).
- Conocimiento negativo con su alcance.
- Candidatas a UKDL: reglas duras, de proceso y trampas.
- Prueba de agente nuevo.
- Handoff en dos capas.

## Presupuesto y ejecución
- **Tokens:** autoridad de 20M procesados más 2 recargas de 4M (techo 28M). 0 tokens fresh: todo es m2c, mwcc y objdiff deterministas, sin llamadas a modelo. 0 USD.
- **Límites:** 12 ciclos y 24 h.
- **Armado:** misión Ralph en GEX44, en el directorio t1-campaign, siguiendo la receta de `reference_gex44_mission_arming_recipe`:
  - `arm --no-launch` como última línea y luego `mission_topup.py budget`, con el entorno de la sweep (`CPP_CLAUDE_EXE`);
  - comprobar que el worker queda en `worker_acked` y en RUNNING.
- **Agentes:** un worker y un verificador independiente en las Gates B y E. Al verificador se le da el código y los datos, no las conclusiones.
- **Reglas de parada:**
  - el done-gate pasa;
  - se acaba el presupuesto;
  - P1 falla (se redirige, no se insiste);
  - 3 épocas sin progreso;
  - permiso nuevo necesario (solo la Gate E).

## Lo que no se toca
- Certify, los recibos ni el perfil histórico.
- `~/.codex/config.toml`.
- Push ni deploy.
- No se suben versiones de objdiff ni de mwcc.
- La pasada `cmpswap_full`: solo se lee al terminar.

## Rollback
Todo es aditivo: módulos extendidos con Tennis por defecto idéntico, un perfil nuevo y directorios de evidencia nuevos. Para pararlo, `hold` sobre la misión; para deshacerlo, `git revert` de los commits S30T.

## Verificación
- Cada fase tiene su gate `tools/test_s30t_*.py` en t1, con mutantes sembrados que deben ponerse en rojo.
- Rebuild byte a byte de los 9,269 certificados.
- La Gate B y la E se juzgan con objdiff + `reloc_oracle` sobre la validación aparte.
- Gates de la misión: `test_gsd_mission.py` y `gsd_mission.py status`.
