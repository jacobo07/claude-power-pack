---
title: UCR-CIF -- S3 resultado: O0 sellada, antes de la inyeccion
date: 2026-09-24
status: SEALED -- vault/tower/o0/O0_2026-09-24.json, probes sha256 b156db7ab3d80346
method: 20_O0_METHOD_PREDECLARATION.md (commit bf69726)
---

# O0 -- el estate antes de que el baseline se inyecte

## 1. Lo medido

36 pares (repo, familia) sobre 25 repos. 540 veredictos:

| MET | NOT_MET | NOT_APPLICABLE | UNJUDGED |
|---|---|---|---|
| 22 | 24 | 24 | 470 |

470 UNJUDGED es el resultado honesto, no un fallo: 49 de las 60 entradas son PROCESS / RENDERED /
DESIGN por metodo (§2 del metodo) y ningun estado de repo las decide. Las medira S6 por mision.

**Mejor completitud demostrada** (solo sobre entradas con sonda):
`persistent_state` 1.0 (claude-power-pack) · `web_surface` 1.0 (CostaLuz Lawyers) ·
`wii_homebrew` 0.5 (ABSW2-Wii) · `kobiicraft_mode` 0.25 (KobiiCraft Core Files).

## 2. Dos fallos del instrumento, separados de los hallazgos

1. **`repo-private` 13/13 UNJUDGED** en la primera corrida: `gh` no encontraba `git` en el PATH
   no interactivo del host. Fallo de entorno, no un hecho de ningun repo. Reparado en
   `o0_measure.py` (PATH de git para `gh`). **La sonda no cambio.** Ahora: 7 privados, 6 sin
   remoto de GitHub (UNJUDGED honesto: solo locales).
2. **`inventory-open-close-tick-delay` «probe failed»** en ambos repos: la regex predeclarada
   ponia `(?s)` en mitad del patron, y Python lo rechaza. **La sonda tal como se predeclaro no
   podia ejecutarse**; no produjo ningun numero antes de repararla. Cambio: se quita el segundo
   `(?s)` (el primero ya es global). **Esto cambia `probes.json`**: sha256 `85cab0a9cefcc745`
   (predeclarado, bf69726) -> `b156db7ab3d80346` (O0). O1 debe usar `b156db7ab3d80346`.

## 3. Hallazgos

- **Una entrada de B0 contradicha por la practica.** `wii_homebrew-no-posix-headers` (de
  wii-dev-best-practices) dice no incluir `<unistd.h>`. CavEX lo incluye sin guarda en
  `source/durable_file.c:34` y el build Wii esta verde: newlib de devkitPPC lo trae, y de ahi sale
  el `fsync` del arreglo de durabilidad de `level.dat`. **Candidata a revert en la revision del
  Owner**, no se toca aqui.
- **KobiiCraft**: 4/60 handlers de click sin `setCancelled(true)`, 29/42 ficheros de E/S sin
  `runTaskAsynchronously`, 16/36 con close+open sin `runTaskLater`.

## 4. Imprecision declarada (cota superior, no retocada)

Retocar una sonda tras ver sus numeros invalida O0. Por eso se escribe en vez de corregirse:

- `float-literals` barre tambien tests y herramientas del lado host (`knowledge-vault/tests`,
  `tools/`): su NOT_MET es una cota superior.
- `monetary-qualifiers` dispara con cualquier `total =`/`amount =`: su NOT_MET (9 repos) es cota
  superior; parte no es dinero.

Ambas imprecisiones son constantes entre O0 y O1 con la misma sonda, que es lo que la comparacion
necesita. Afinarlas es trabajo de una generacion de sondas nueva, con su propio O0.
