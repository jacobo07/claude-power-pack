---
title: UCR-CIF — P2: predeclaración de los dos sujetos, ANTES de que exista el clasificador
date: 2026-09-23
status: PREDECLARADO — este fichero se commitea SOLO, antes de escribir una línea del barrido
binding: si el clasificador contradice esto, gana la medición y se registra la contradicción
---

# P2 — los dos sujetos, nombrados antes

## 0. Por qué esto se commitea solo y primero

El §11.a P2 del spec exige *«un clasificador de familia con las dos ramas alcanzables sobre
entradas reales — una misión del estate que debe clasificar dentro y otra que debe quedar fuera,
**nombradas antes de implementarlo**»*.

Nombrarlas después es elegir los sujetos que el clasificador ya sabe clasificar. Eso es un
examen que se aprueba a sí mismo. **Este fichero existe para que la elección sea anterior y
auditable por `git log`.**

## 1. La señal elegida, declarada antes de medir

**Composición de ficheros del repo.** Estructural por construcción: no depende de que nadie haya
etiquetado nada, a diferencia de `task_class`, que ya se probó y **no lleva el eje de familia**
(`13_FAMILY_SIGNAL_PROBE.md`).

Familia bajo prueba: **`PERSISTENT_STATE`** — la primera del spec §2.

Marcadores estructurales que se buscarán (declarados ahora, no después):

- directorios de migración (`migrations/`, `priv/repo/migrations/`, `alembic/`)
- esquema declarado (`schema.prisma`, `schema.sql`, `*.sql` con `CREATE TABLE`)
- ORM / acceso a base de datos en dependencias (`prisma`, `sqlalchemy`, `ecto`, `sqlite3`, `pg`)
- ledgers durables propios (`*.jsonl` bajo un directorio de estado, `*.db`, `*.sqlite`)

## 2. Los dos sujetos

| rama | repo | ruta | por qué, dicho ANTES de mirar sus ficheros |
|---|---|---|---|
| **DENTRO** | **`InfinityOps`** | `C:\Users\User\Desktop\Cursor Projects\InfinityOps` | Es el backend SaaS del Owner: Elixir/OTP/Phoenix con Postgres según `~/.claude/CLAUDE.md` §KobiiAI Stack. **Si el estado persistente no es su familia, la taxonomía está mal, no el repo.** |
| **FUERA** | **`ABSW2-Wii`** | `C:\Users\User\Desktop\Cursor Projects\Wii Projects\ABSW2-Wii` | Homebrew de Wii en C/PowerPC: sin ORM, sin migraciones, sin esquema declarado. **Si un juego de Wii clasifica como CRUD con estado persistente, el clasificador sobre-empareja** y su rama positiva no vale nada. |

Ambos tienen `.git` y por tanto están en la población de 149 repos alcanzables. Se verificó su
existencia **antes** de nombrarlos; no se leyó su contenido.

### 2.a Sujeto descartado, y por qué se dice

La primera elección para la rama FUERA fue `KobiiSports Resort`. **No tiene `.git`**, así que no
está en la población y habría sido un sujeto que el barrido nunca visita — una rama negativa que
pasa por ausencia, no por juicio. Sustituido por `ABSW2-Wii`.

## 3. Qué cuenta como fallo — declarado ahora

- **`InfinityOps` fuera de `PERSISTENT_STATE`** ⇒ la señal o la taxonomía están mal. No se
  «ajusta» el umbral hasta que entre.
- **`ABSW2-Wii` dentro** ⇒ sobre-emparejamiento. Un clasificador que dice «sí» a todo pasa todos
  los tests de activación, que es precisamente lo que P2 existe para impedir.
- **El barrido encuentra 0 repos con marcadores** ⇒ **falla con exit≠0**, nunca reporta limpio.
  Suelo de población declarado: **≥120 repos visitados** de los 149 medidos hoy.
- **Cualquiera de los dos sujetos ausente del barrido** ⇒ resultado inválido, no negativo.

## 4. Lo que este fichero NO hace

- **No** predice el resto de familias. Sólo `PERSISTENT_STATE` está bajo prueba.
- **No** afirma que la composición de ficheros sea la señal correcta. Afirma que es la candidata
  elegida **antes** de medir, y que si falla se registra como fallo de la señal — no se cambia de
  sujeto.
- **No** clasifica misiones todavía. El catálogo (P3) precede a la clasificación de misiones (P2
  completo); esto cubre la mitad de repo.
