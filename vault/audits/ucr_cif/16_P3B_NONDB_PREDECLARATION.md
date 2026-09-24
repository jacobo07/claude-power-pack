---
title: UCR-CIF — P3b: predeclaración del estado persistente SIN base de datos, ANTES de tocar el scanner
date: 2026-09-24
status: PREDECLARADO — se commitea SOLO, antes de cambiar una línea de tools/family_scan.py
binding: si el scanner contradice esto, gana la medición y se registra la contradicción; no se cambia de sujeto
extends: 14_P2_PREDECLARATION.md (sus dos sujetos siguen vinculantes y sin cambios)
---

# P3b — el polo que P2 nunca probó

## 0. El defecto que motiva esto

`family_scan.py` sólo reconoce `PERSISTENT_STATE` por marcadores de backend web: migraciones,
esquema SQL/Prisma, ORM en manifiestos de dependencias, ficheros `.db`/`.sqlite`. P2 probó un
polo DENTRO con base de datos (InfinityOps) y un polo FUERA sin ella (ABSW2-Wii). **Nunca probó
un repo SIN base de datos y CON estado persistente real.** Ese caso existe en el estate y hoy
clasifica FUERA:

- **CavEX** produjo `NOT_APPLICABLE` el 2026-09-24. Es el repo cuyo escritor de `level.dat`
  truncaba antes de serializar y destruyó tres mundos del Owner
  (`~/.claude/rules/instrument-before-claim.md`, entrada 2026-09-22). Es estado persistente por
  la definición del propio spec §4: escritura atómica, contención de corrupción, supervivencia a
  reinicio.

`MISSED ACTIVATION IS A BUG` (spec §7) — gemela de la falsa activación.

## 1. Los sujetos, nombrados antes de diseñar el marcador

| rama | repo | por qué, dicho ANTES de leer su código |
|---|---|---|
| **DENTRO** (nuevo) | `Wii Projects\CavEX` | incidente de destrucción de mundos documentado; elegido por el incidente, no por sus ficheros |
| **DENTRO** (nuevo) | `Vibe Coding Projects\Orca X` | el corpus de reglas globales está lleno de su estado persistido a través de reinicios (`presence-is-not-residency.md`, `durable-exit-transaction.md`); elegido por eso, sin leer su código |
| FUERA (P2, sin cambios) | `Wii Projects\ABSW2-Wii` | vinculante desde commit 3b3ae85 |
| **FUERA** (nuevo) | `Apps\remotion-video-pipeline` | pipeline de render: escribe ficheros de SALIDA, no estado propio que relea. Es el sujeto que tumba un marcador ingenuo de «escribe ficheros» |

Admisión: CavEX y Orca X se eligieron conociendo sus incidentes. Por eso hay un segundo FUERA
elegido para discriminar precisamente el sobre-emparejamiento que ese sesgo favorecería.

## 2. La clase de marcador, declarada antes de medir

Estado persistente propio sin base de datos = **el programa escribe estado duradero que después
relee, y lo trata como algo que no debe corromperse.** Dos marcadores de contenido, leídos sólo
en ficheros fuente y con lectura acotada:

- **`atomic_replace`** — el idiom de sustitución atómica: `os.replace(`, `renameSync(` /
  `fs.rename(` / `fs.promises.rename(`, `ATOMIC_MOVE`, o `rename(` en C/C++ en un fichero que
  también nombra un temporal (`.tmp`).
- **`save_format`** — un literal que nombra un fichero de estado/partida: `level.dat`, `.nbt`,
  `.mca`, `.mcr`, `.sav`, `savegame`.

## 3. Qué cuenta como fallo

- CavEX u Orca X FUERA ⇒ la clase de marcador no ve lo que dice ver. Se registra; no se retoca
  hasta que entren.
- ABSW2-Wii o remotion-video-pipeline DENTRO ⇒ sobre-emparejamiento. **STOP y reporte al Owner**,
  no ajuste.
- InfinityOps FUERA ⇒ regresión del polo original.
- **Todo repo que cambie de FUERA a DENTRO se nombra y se inspecciona uno a uno** con el marcador
  que lo metió. Un predicado puede acertar en los sujetos elegidos y estar mal sobre la clase
  (15_P3 §4).
- Suelo de población: sin cambios (35 proyectos).

## 4. Lo que este fichero NO hace

- No cambia la definición de la familia más allá de dejar de exigir una base de datos.
- No verifica ningún depósito (`portability_proven` sigue en `False`); el lift verificado sigue en 0.
- No declara que la cobertura acotada vea todo repo: un paseo truncado en 4.000 entradas se
  reportará como truncado, nunca como FUERA limpio.
