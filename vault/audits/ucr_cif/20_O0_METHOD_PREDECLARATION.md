---
title: UCR-CIF -- S3: metodo de O0 PREDECLARADO, antes de medir un solo repo
date: 2026-09-24
status: PREDECLARADO -- este fichero y vault/tower/o0/probes.json se commitean SOLOS, antes del medidor
spec: docs/superpowers/specs/2026-09-24-family-baselines-design.md §4 (O0 antes de la inyeccion)
binding: un umbral o una sonda cambiados tras ver los numeros invalidan O0; se registra, no se ajusta
---

# O0 -- como era el estate ANTES de que el baseline se inyecte

## 1. Para que existe

S4 va a inyectar el baseline de familia en cada mision nueva. Sin una medicion ANTERIOR no hay
forma de decir despues si sirvio: una vez viva la inyeccion, el «antes» ya no se puede observar
(spec madre §8, G-7). O0 es ese antes.

## 2. Unidad y veredictos

Unidad: **(repo, entrada de B0)**. Cinco veredictos, nunca colapsados:

| veredicto | significa |
|---|---|
| MET | la sonda encuentra la evidencia que la entrada exige |
| NOT_MET | la sonda aplica y no la encuentra |
| NOT_APPLICABLE | ningun fichero del repo dispara `applies_if` |
| UNJUDGED | la entrada no tiene sonda (PROCESS / RENDERED / DESIGN) o el paseo/la llamada fallo |
| (ninguno mas) | |

**Sondas: 11 de 60 entradas** (`vault/tower/o0/probes.json`). Las otras 49 quedan UNJUDGED con su
clase escrita:

- **PROCESS** (24): pasan al construir, desplegar o declarar hecho. Ningun estado de repo las
  prueba; las medira el done-gate de S6 por mision.
- **RENDERED** (6): necesitan la superficie viva; las mide CDIO contra la URL real.
- **DESIGN** (19): propiedad de diseno de codigo que ninguna regex decide con honestidad.

(Conteos medidos sobre `probes.json`: 11 + 49 = 60, cada entrada de B0 exactamente una vez. El
primer borrador de este fichero decia 29/14; era un conteo de memoria y estaba mal.)

Decir «O0 cubre 11/60» es el resultado honesto, no un defecto a esconder.

## 3. Poblacion

Los repos de cada familia segun `modules/tower/families.repo_family_report` (S1, commit
14d6c8a), sobre el repo principal de cada proyecto. Un repo cuya familia sale UNJUDGED queda
fuera y se nombra.

## 4. Metricas -- declaradas ahora

- cobertura del repo en su familia = MET / (MET + NOT_MET) sobre las entradas con sonda;
  NOT_APPLICABLE y UNJUDGED **fuera del denominador y contados aparte**.
- mejor completitud demostrada de la familia = la cobertura maxima entre sus repos.
- **O0 no decide nada.** No tiene umbral; registra.

## 5. Que comparara O1

Mismas sondas, mismos repos, **tras >= 14 dias con S4 vivo**, mas todo repo nuevo de la familia.
**CRR** = fraccion de repos NUEVOS cuya cobertura queda por debajo de la mejor de O0 en su familia.
Un cambio de sondas entre O0 y O1 anula la comparacion.

## 6. Controles del instrumento (antes de creer un numero)

Cada modo de sonda se conduce en fixtures sinteticos por los dos polos (MET y NOT_MET), mas
NOT_APPLICABLE, antes de la corrida real. Una sonda que solo puede devolver una respuesta no
mide nada (instrument-before-claim).
