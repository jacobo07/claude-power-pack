---
title: UCR-CIF — P3: el catálogo de familias, descubierto. Y el estate tiene 42 proyectos, no 164.
date: 2026-09-23
status: MEASURED — predeclaración cumplida, ambos polos alcanzados, mutación conducida y restaurada por hash
instrument: tools/family_scan.py
predeclaration: vault/audits/ucr_cif/14_P2_PREDECLARATION.md (commit 3b3ae85, ANTERIOR al scanner)
closes: P3 del spec §11.a · la mitad de repo de P2
---

# P3 — la señal funciona, y la población no era la que creíamos

## 1. Resultado

| | |
|---|---|
| **proyectos distintos visitados** | **42** |
| clasificados **DENTRO** de `PERSISTENT_STATE` | **17 (40 %)** |
| clasificados **FUERA** | **25 (60 %)** |
| **ambos polos alcanzados** | **SÍ** |
| suelo de población | 35 (ver §3) |

Frecuencia de marcadores: `migrations_dir` 11 · `orm_dependency` 9 · `durable_ledger` 9 ·
`declared_schema` 4.

**Los dos sujetos predeclarados, ambos correctos:**

| sujeto | esperado | obtenido | marcadores |
|---|---|---|---|
| `InfinityOps` | DENTRO | **DENTRO** | `migrations_dir`, `orm_dependency` |
| `ABSW2-Wii` | FUERA | **FUERA** | ninguno |

El conjunto DENTRO se lee como lo que es —InfinityOps · TUA-X · CostaLuz Lawyers · Club Náutico ·
SalesTrainer · nexumops-saas · Internal SaaS Bootstrap Engine · infinityops-mail-studio…— o sea
las apps de negocio del estate. **La señal de composición de ficheros SÍ lleva el eje de familia**,
donde `task_class` no lo llevaba (`13_FAMILY_SIGNAL_PROBE.md`).

## 2. El hallazgo que vale más que el catálogo

> **El estate tiene 42 proyectos distintos, no 149 ni 164 «repos». La diferencia son worktrees de
> git, y el factor es 3,9×.**

La primera corrida del scanner reportó **118 DENTRO de 164**, y su lista estaba dominada por
`TUA-X-acmf`, `TUA-X-bdci`, `TUA-X-brand001`, `TUA-X-cbin-recommend`… e
`InfinityOps-gscfix`, `-journal`, `-bis-capab`. **Un proyecto con quince worktrees aportaba quince
clasificaciones**, así que aquello no era una distribución sobre el estate: era una distribución
sobre checkouts.

Y el detalle que lo hace doctrina: **`repo_identity.canonical_repo` NO arregla esto, y hace bien**.
Trata el `.git` de un worktree como marcador válido **a propósito** (`identity.py:46-49`), para que
cada worktree conserve su propio estado. Eso es correcto para estado-por-repo y equivocado para una
población. El colapso hay que hacerlo leyendo el puntero `gitdir:` del worktree.

**Consecuencia transversal:** cualquier tasa por repo que esta estancia haya calculado sobre
checkouts está inflada ~4×. Los 11 ledgers de depósitos FD-07 son ledgers **por checkout**, no por
proyecto.

## 3. El suelo de población falló, y eso fue el sistema funcionando

`14_P2_PREDECLARATION.md` declaró **suelo 120**. Al colapsar worktrees la población cayó a 42 y el
scanner **salió con exit 2**:

```
SWEEP FAILED: 42 < 120. The sweep may have stopped seeing repos.
Refusing to report a clean result.
```

**El suelo estaba declarado sobre la unidad equivocada** — contaba checkouts. No era demasiado
estricto: era sobre otra magnitud.

**Se movió a 35, y se dice que se movió.** Mover un umbral después de ver el número está
normalmente prohibido, y aquí se permite por una razón que hay que enunciar en vez de asumir: el
umbral original no medía lo mismo. El nuevo deja ~17 % de encogimiento antes de fallar, y el
barrido sigue **fallando** en vez de reportar limpio. La justificación vive en el propio
`family_scan.py`, junto a la constante, no en un documento aparte.

## 4. Un defecto propio que la predeclaración NO habría cazado

La primera versión emparejaba dependencias por **subcadena**: `dep in blob`. `orm_dependency`
disparó en **129 de 163** repos, porque **`ecto` es subcadena de `vector`, `detector`, `selector`,
`director`, `inspector`** — contenido ordinario de cualquier `package.json`.

**Los dos sujetos predeclarados seguían siendo correctos con el bug puesto.** Por eso hubo que
mirar también la **distribución de la población**: *un predicado puede acertar en los casos que
elegiste y estar equivocado sobre la clase*. Con límites de palabra: 129 → **109** sobre checkouts,
y FUERA casi se dobló (25 → 46).

## 5. Drill de mutación — conducido

Mutante: `present = list(MARKERS)` — clasificar todo DENTRO, el clásico «clasificador que dice sí
a todo».

| aserción | mundo sano | mundo falso |
|---|---|---|
| clasificados DENTRO / FUERA | 17 / 25 | **42 / 0** |
| `BOTH POLES REACHED` | `True` | **`False`** |
| `ABSW2-Wii` | OUT, OK | **IN, `**MISMATCH**`** |
| veredicto | — | **`PREDECLARED EXPECTATION NOT MET`** |

**Restauración verificada por SHA-256 idéntico** (`F01B45AD…E16C` antes y después).

El drill prueba lo que importa: **el polo FUERA es real**, no un artefacto de que ningún repo
disparara. Sin él, un clasificador que activa siempre pasa todos los tests de activación — que es
literalmente lo que P2 existe para impedir.

## 6. Lo que este fichero NO afirma

- **No** afirma que las 17 clasificaciones DENTRO sean todas correctas. **`FIFA 11 Mod` clasifica
  DENTRO y es sospechoso**: es un mod de juego. No se ha verificado qué marcador lo mete, y queda
  como posible falso positivo nombrado, no barrido bajo la alfombra.
- **No** clasifica **misiones**, sólo repos. P2 completo —una misión dentro y otra fuera— sigue
  abierto; esto cubre la mitad de repo.
- **No** descubre más familias que `PERSISTENT_STATE`. Las otras tres del spec §0 (superficie web
  con efectos · integración externa · migración de esquema) no se han sondeado.
- **No** está conectado a nada. `family_scan.py` es un scanner de línea de comandos; **ningún
  `MissionContext` consume todavía su etiqueta**. Eso es el conector, y sigue siendo la deuda.
- **Apertura de liveness declarada:** vive en `tools/`, que
  `modules/liveness/reachability.py` **no barre**. Su silencio sobre este fichero es ausencia del
  denominador, nunca salud.

## 7. Qué desbloquea

CRR, RFR y BIR estaban bloqueadas por «no existe clasificador de familia»
(`11_O0_PRETREATMENT_BASELINE.md` §2). **Ese bloqueo se levanta a medias**: ya hay eje de familia
sobre repos, con ambos polos y con drill. Falta el eje sobre **misiones** y el conector a
`applicability.py` antes de que ninguna de las tres pueda calcularse.
