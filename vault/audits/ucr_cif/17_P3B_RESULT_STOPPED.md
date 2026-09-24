---
title: UCR-CIF — P3b resultado: los sujetos pasan, el polo FUERA cae con apertura completa. STOP.
date: 2026-09-24
status: STOPPED — condición de parada predeclarada alcanzada (16_P3B §3). Decisión del Owner pendiente.
predeclaration: 16_P3B_NONDB_PREDECLARATION.md (commit 1972831)
instrument: tools/family_scan.py con marcadores atomic_replace + save_format (NO commiteado)
---

# P3b — resultado

## 1. Con el paseo acotado (4.000 entradas), todo parece correcto

43 proyectos, 26 DENTRO / 17 FUERA, ambos polos. Los cinco sujetos predeclarados, OK:
InfinityOps IN · ABSW2-Wii OUT · **CavEX IN** (`save_format`) · **Orca X IN** (`atomic_replace`) ·
remotion OUT. 9 repos pasan de FUERA a DENTRO; inspeccionados uno a uno, los 9 poseen estado
propio (Power Pack, google-account-router, kme, ksr_rehydrate vía `wbcos_core.py`, AKOS, Orca X,
CavEX, CavEX-II-Reps, KobiiHub vía `activeset/record.py`).

Gate `tools/test_family_scan.py` 7/7. Drill: cegar `os.replace` → rojo en V-FAMSCAN-ATOMIC-IN;
quitar la exigencia de `.tmp` en C → rojo en V-FAMSCAN-C-RENAME-NEEDS-TMP. Restauración SHA-256
idéntica (`cd4141b816b0`).

## 2. Con el paseo completo, el polo FUERA cae

Tres FUERA venían de paseos **truncados**. Re-escaneados sin tope:

| repo | acotado | completo | qué lo mete |
|---|---|---|---|
| **ABSW2-Wii** (FUERA vinculante) | OUT | **IN** | `tools/lua_pipeline.py:501` — escribe un **artefacto generado** vía `.tmp` + `os.replace` |
| LuckyFly | OUT | **IN** | `tools/build_horizoncraft_world.py` — **genera** un `level.dat` como release asset |
| Computer Personal Ops | OUT | OUT | — (tope de 20.000 lecturas de fuente alcanzado: FUERA no limpio) |

**El OUT de ABSW2-Wii lo sostenía la truncación, no el juicio.** Es exactamente el sobre-
emparejamiento que 16_P3B §3 declaró como STOP.

## 3. El defecto, nombrado

`atomic_replace` y `save_format` no distinguen **poseer estado** de **producir un artefacto**. Este
estate escribe de forma atómica también sus salidas (es doctrina propia), así que el idiom atómico
es una señal de *cuidado al escribir*, no de *estado que se relee*. Dos falsos positivos de
marcador más, sin impacto en la clasificación: `ksr_rehydrate/tools/gen_bowling_audio.py`
(sustituye un asset) y `KobiiHub/tools/wiidisc/model.py` (`"savegame"` es un nombre de etiqueta
XML).

Segunda lección, del instrumento: **un polo negativo sostenido por un paseo truncado es un polo
que nunca se juzgó.** El reporte de truncación añadido en esta pasada es lo que lo destapó.

## 4. Qué NO se ha hecho, a propósito

- `family_scan.py` y `tower_capsule.py --all` quedan **sin commitear**.
- `family_scan_result.json` **restaurado** a su versión commiteada: la corrida acotada afirmaba
  `predeclared_met` y la apertura completa lo refuta.
- **No se han producido cápsulas para el estate.** Hacerlo ahora repartiría activaciones con un
  clasificador con falsa activación medida.
- No se ha retocado ningún marcador. Ajustarlo tras ver a ABSW2 es elegir el umbral después del
  número.

## 5. Opciones para el Owner

1. **Emparejar escritura con relectura**: el mismo literal de ruta escrito atómicamente **y** leído
   por el código de runtime (fuera de `tools/`). Requiere predeclaración nueva.
2. **Excluir `tools/` y scripts de build** del barrido de contenido. Más barato, y sigue siendo un
   ajuste tras ver el dato; también requiere predeclaración nueva.
3. **Redefinir la familia** como «escribe ficheros duraderos con cuidado de integridad», lo que
   convierte ABSW2-Wii en DENTRO y revoca el sujeto de P2. Decisión de taxonomía, no técnica.
