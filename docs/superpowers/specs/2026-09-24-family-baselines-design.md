---
title: Baselines constitutivos por familia -- la inteligencia de ingenieria que se aplica sin pedirla
date: 2026-09-24
status: DESIGN -- decisiones del Owner tomadas (AskUserQuestion 2026-09-24)
tier: T3
extends: docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md (§4-§8)
covers:
  - family-baselines
  - constitutive-baseline-ratchet
  - mission-family-classifier
  - baseline-generation
  - baseline-auto-promotion
  - baseline-done-gate
  - web-surface-baseline
  - kobiicraft-mode-baseline
  - wii-homebrew-baseline
  - persistent-state-baseline
---

# Baselines constitutivos por familia

## 0. Lo que pidio el Owner

> «si hago algo nuevo y no menciono ciertas cosas que tendria esa cosa en ese baseline, se hacen
> automaticamente. Mejoro KEOS y sube mucho el baseline: eso se transfiere a la torre universal, y a
> partir de entonces cualquier software que cree tiene sugerencias de ingenieria autoimplementadas
> segun lo que seria, por ejemplo, un sitio web de ese mismo baseline, o un setup nuevo de una
> modalidad de KobiiCraft»

Eso NO son las lecciones de C2 (`a6d2042`). Una leccion dice «no hagas X». Un baseline dice «una
instancia de esta familia sin Y esta incompleta». Es el Constitutive Baseline Ratchet del spec
madre (§4-§5), que hasta hoy no tenia ninguna generacion escrita.

## 1. Decisiones del Owner (2026-09-24)

| pregunta | respuesta |
|---|---|
| familias iniciales | **las cuatro**: sitio web/landing · modalidad KobiiCraft · SaaS con estado persistente · homebrew Wii |
| quien aprueba una promocion | **automatica al instante; el Owner revisa despues** y puede revertir |
| KEOS | **vive en la GEX44** (host remoto; no esta en este disco) |

## 2. Medido antes de disenar

- Canal de entrega al agente: EXISTE (`modules/gsd_x/cli.py`, C2). Probado extremo a extremo.
- Motor de aplicabilidad (UBC, `modules/capability_runtime/applicability.py`): EXISTE. Sus 13
  contratos son de *herramientas*, no de *tipos de sistema*.
- **Las familias NO pueden ser contratos de capacidad.** `tier.classify` convierte un contrato
  MANDATORY en DEEP y dos en FORENSIC: registrar «sitio web» como contrato cambiaria el tier de
  cada prompt de web. Se reutiliza el **matcher** de UBC (`_hits`, frontera de palabra) y su
  **gramatica** (triggers + anti_triggers como veto), no su veredicto. Un matcher, una gramatica.
- Generaciones de baseline existentes: **cero**. `PERSISTENT_STATE-B0` nunca se escribio.

## 3. Arquitectura -- una ruta, cinco piezas, cero sistemas nuevos

```
deposito (C1, fd_07)  ->  promocion automatica  ->  <familia>-B<n+1>
                                                         |
prompt  ->  clasificador de familia (matcher de UBC)  ->  baseline aplicable
                                                         |
                          capsula / cli.py (C2)  ->  «implementa sin que te lo pidan»
                                                         |
                          done-gate  ->  cada entrada: APLICADA | NO APLICA + razon
```

1. **Registro de familias** -- `vault/tower/families/<familia>.json`: `triggers`, `anti_triggers`
   (misma gramatica que UBC) y `repo_markers` estructurales (para saber a que familia pertenece
   un repo de origen). Cuatro ficheros.
2. **Generaciones** -- `vault/tower/baselines/<familia>/B<n>.json`, inmutables una vez escritas.
   Una promocion escribe `B<n+1>` = `B<n>` + entradas nuevas; nunca reescribe una generacion.
   Cada entrada: `id`, `requirement` (en imperativo), `why`, `origin` (repo + commit o fichero de
   gobierno), `class` (C|D), `status` (`auto` | `reviewed` | `reverted`), `check` opcional
   (comprobacion maquina: fichero, glob, regex).
3. **B0** -- sale de lo que el Owner **ya sello** como constitutivo en gobierno existente
   (DEPLOY/COPY/REPO_SECURITY governance, CDIO, hard rules de KobiiCraft, doctrina Wii). El sello
   del Owner ES la respuesta contrafactual; no se inventa ninguna entrada.
4. **Promocion automatica** -- decision del Owner. Un deposito NEW/STRONGER con destino
   `hard_rule|benchmark|asset`, que no sea `landed-commit`, de un repo que pertenece a la familia
   F, entra en `F-B<n+1>` con `status=auto`. Revision: `tools/family_baseline.py review` lista lo
   `auto` desde la ultima revision; `revert <id>` escribe `B<n+2>` sin ella. Nada se borra.
   Una entrada que aplica a todas las familias sube a la capa universal (C2).
5. **Inyeccion + done-gate** -- el prompt se clasifica; las entradas de las familias que
   coinciden se inyectan por `cli.py` (acotadas, P4) con la instruccion de implementarlas sin
   pedirlo o declarar `NO APLICA` con razon. El done-gate compara la entrega con la generacion
   inyectada.

## 4. Controles obligatorios

- **Clasificador con los dos polos predeclarados por familia** antes de escribirlo
  (`vault/audits/ucr_cif/18_FAMILY_MISSION_PREDECLARATION.md`, commit propio).
- **Control positivo:** un prompt que no es de ninguna familia no recibe ningun baseline
  (spec madre §8: `FALSE ACTIVATION IS A BUG`).
- **O0 antes de la inyeccion:** cobertura de B0 medida sobre repos reales existentes de cada
  familia, sellada ANTES de que la inyeccion este viva. Sin eso no hay forma de saber si sirvio.
- **Drill de mutacion** por pieza, con el ENLACE mutado ademas de los extremos.
- **Techo de inyeccion:** 8 entradas / 1.400 caracteres por familia; superarlo es fallo del
  compilador, no una nota.

## 5. Kill switch y rollback

- `CPP_FAMILY_BASELINES=off` -> `cli.py` no inyecta baselines (las lecciones de C2 siguen).
- Rollback de una promocion: `revert <id>` escribe una generacion nueva sin ella.
- Rollback total: borrar `vault/tower/baselines/` vuelve al estado de C2 sin tocar nada mas.

## 6. Orden de ejecucion

| rebanada | entrega | done cuando |
|---|---|---|
| S1 | predeclaracion + registro de 4 familias + clasificador de prompt | ambos polos por familia, drill rojo |
| S2 | B0 de las 4 familias desde gobierno sellado, con origen por entrada | cada entrada cita fichero:linea |
| S3 | O0 sellada (cobertura de B0 sobre repos reales) | commit de O0 anterior a S4 |
| S4 | inyeccion por `cli.py` + control positivo + kill switch | extremo a extremo por el hook real |
| S5 | promocion automatica + `review`/`revert` | un deposito real sube solo y se revierte |
| S6 | done-gate | una entrega sin una entrada D no se declara hecha |

## 7. Lo que este diseno NO promete

- **KEOS** vive en la GEX44: su aportacion a `kobiicraft-mode` entra cuando se lea alli
  (S2 o S5), no se supone desde aqui.
- Que la promocion automatica no infle: es la decision del Owner y el riesgo queda medido por
  el volumen por generacion, visible en `review`.
- Que el done-gate bloquee en S6 v1: arranca como informe; bloquear es una decision aparte.
