---
title: UCR-CIF -- S1 resultado: clasificador de familia, predeclaracion cumplida y dos defectos de poblacion
date: 2026-09-24
status: MEASURED -- 18/18 sujetos predeclarados + 2 mecanismos; drill 5/5 ROJO; restauracion SHA-256 identica
predeclaration: 18_FAMILY_MISSION_PREDECLARATION.md (commit 247ffc0)
instrument: modules/tower/families.py + vault/tower/families/*.json · gate tools/test_family_baselines.py
---

# S1 -- resultado

## 1. Sujetos predeclarados: 18/18

Los ocho polos de prompt, los ocho de repo, el control positivo («que hora es» -> ninguna familia)
y el caso duro («landing para anunciar la nueva modalidad de KobiiCraft» -> web si, modalidad no,
por el anti-trigger `landing`).

**Un fallo en la primera corrida, registrado antes de repararlo:** `KobiiCraft Core Files` salia
FUERA de `kobiicraft_mode`. No era el marcador: el repo tiene **48.461 entradas** y el primer
`pom.xml` esta en la **5.408**, detras del tope de 4.000 heredado de `family_scan`. Mismo defecto
que ABSW2 en `17_P3B`. Reparacion: paseo de 100.000 (la pertenencia se calcula al promocionar, no
en el camino del prompt) y un paseo cortado devuelve **UNJUDGED**, nunca FUERA.

## 2. Poblacion -- lo que los sujetos elegidos no podian ver

**158 prompts reales** (120 transcripts recientes): 135 sin familia, 23 activaciones.
**Defecto medido, NO reparado en S1: preguntas de estado y meta-preguntas activan.**

- 15 de las 19 activaciones de `kobiicraft_mode` son por `arena`, casi todas «¿queda mucho de
  arena 5? mandame el handoff».
- La pregunta que abrio esta mision activa `wii_homebrew` porque la **ruta** contiene `Wii Projects`.
- La peticion del Owner de este mismo diseno activa `web_surface` porque cita «sitio web» como
  ejemplo.

Coste acotado (8 entradas, 3 primeros prompts por sesion), pero es `FALSE ACTIVATION IS A BUG`.
La reparacion (construir vs. preguntar) necesita su propia predeclaracion; retocar triggers
despues de ver estos prompts seria elegir el umbral tras el numero.

**42 repos:** Orca X (Electron) en ninguna familia; SaaS con frontend Next en `web_surface` Y
`persistent_state` (multi-familia esperado); `ksr_rehydrate` en `wii_homebrew`. Por confirmar con
el Owner: **LuckyFly** queda fuera de `kobiicraft_mode`.

## 3. Drill

| mutante | cae en |
|---|---|
| veto de anti-trigger quitado | V-FAMB-HARD-CASE |
| prompt sin plegar acentos | V-FAMB-MECH-ACCENT-FOLD |
| truncacion tragada como FUERA | V-FAMB-MECH-TRUNCATED-IS-UNJUDGED |
| enlace al delegado `family_scan` cortado | V-FAMB-REPO-IN-persistent_state |
| apertura vieja (4.000) | V-FAMB-REPO-IN-kobiicraft_mode |

Restauracion `families.py` SHA-256 identica (`535dc14d21d8`).
