---
title: UCR-CIF -- S1 amendment: predeclaration of the `business_round` family subjects, BEFORE the family file exists
date: 2026-10-27
status: PREDECLARED -- committed ALONE, before vault/tower/families/business_round.json and any B0
spec: docs/superpowers/specs/2026-09-24-family-baselines-design.md section 4; vault/specs/founder-os-v1.md (F6)
binding: if the classifier contradicts this, the measurement wins and is recorded; the subject is not changed
---

# `business_round` -- subjects named before the classifier is written

The family is decided by the PROMPT. It has no `repo_markers`: whether a repository is a business is
exactly what Founder OS must discover from evidence, so a structural marker would pre-decide it. A repo
pole is therefore declared NOT APPLICABLE, not passed.

## 1. By prompt

| IN (must classify) | OUT (must not) |
|---|---|
| "haz una ronda de negocio en este repositorio: encuentra el cuello de botella del embudo de ventas y propone un experimento" | "arregla el crash del escritor de level.dat en la Wii" |
| "run a founder round on this repo: find the business bottleneck and propose one experiment" | "anade una tabla de suscripciones con su migracion al backend de InfinityOps" |
| "mejorar el negocio de este repositorio con /cpp-founder-round" | "hazme una landing para un restaurante con reservas online" |

**Global positive control:** "que hora es" classifies into NO family, including this one.

**Hard case, declared so it can fail:** "haz una landing que explique el modelo de negocio de nuestro SaaS"
-> `web_surface` IN and `business_round` OUT: a web page is being built, no business is being diagnosed.
If the classifier admits both, record it as over-matching BEFORE adjusting anything.

**Second hard case:** "haz una ronda de negocio y de paso arregla el crash del escritor de level.dat"
-> a mixed prompt. Expected: `business_round` IN (the user asked for it). Recorded either way; it tests
whether a veto on a technical token silences a legitimate business request.

## 2. What counts as a failure

- Any IN pole out, or any OUT pole in: a signal failure, recorded.
- "que hora es" in any family: false activation, STOP.
- Any of the four existing families (`web_surface`, `kobiicraft_mode`, `persistent_state`, `wii_homebrew`)
  changing its answer on its own predeclared prompts because this family was added: regression, STOP.
