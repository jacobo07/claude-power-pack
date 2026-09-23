---
title: STAGED PARA EL OWNER — nombrar los miembros abandonados en la rama `before pool`
date: 2026-09-23
status: PREPARADO Y VERIFICADO — NO APLICADO (HR-001)
applies_to: ~/.claude/hooks/hook-dispatcher.js
source_of_truth: ~/.claude/skills/claude-power-pack/hooks/hook-dispatcher.js (commitado)
origin: vault/audits/ucr_cif/09_G3_DECISION.md §6
---

# Despliegue preparado — `CHAIN-DEADLINE-ABANDONED before pool` debe nombrar a quién perdió

## 1. Qué cambia

Una sola llamada a `logError`. La rama `before pool` registraba **un número**; ahora registra
**los nombres**, exactamente como la rama `after` que ya funciona.

```
antes:  pool NOT spawned (5 skipped)
ahora:  pool NOT spawned (5 skipped: ./correction-guard.js, ./prd-keyword-sentinel.js,
        ../skills/claude-power-pack/hooks/gsd_x_tier.js, ...)
```

## 2. Por qué, con la medición

Sobre `~/.claude/logs/hook-dispatcher-errors.log`, ventana 2026-09-15 → 2026-09-23:

- **193** eventos `before pool` en `UserPromptSubmit-chain`
- que abandonaron **965 slots de miembro sin nombrar ni uno**
- lo cual obligó a reportar la pérdida del dueño vivo del Project Birth (`gsd_x_tier`) como un
  **rango 215–408 de 639** en vez de una cuenta

Misma clase de evento, dos niveles de observabilidad — y el barato es el que dispara cuando el
**carril crítico solo** se comió el presupuesto, o sea justo cuando más falta hace saber quién
cayó. Es la asimetría de observabilidad que ya costó el falso cero del ledger de auto-compact,
en otro sitio.

## 3. Estado de verificación — leer esto antes de creerlo

| afirmación | estado |
|---|---|
| sintaxis válida | **VERIFICADO** — `node --check hooks/hook-dispatcher.js` → exit 0 |
| `restSteps` lleva `.script` | **VERIFICADO leyendo la fuente** — `:959` `const restSteps = restIdx.map((i) => runnable[i])`, y `:1005` ya usa `runnable[i].script` |
| simetría con la rama probada | **VERIFICADO** — misma expresión que `:1005`, que produce nombres en producción desde hace 8 días |
| no puede lanzar | **RAZONADO, no conducido** — `.map`/`.join` sobre un array siempre-array; un `.script` ausente renderiza `undefined`, no excepción |
| **drill extremo a extremo** | **NO CONDUCIDO — y esto es una limitación real, no una formalidad** |

### Por qué el drill no se condujo

`hook-dispatcher.js:540` documenta *«Driven by hooks/tests/test-chain-deadline.js, both poles»*.
**Ese test y sus 5 fixtures NO están en el repo.** Viven sólo en `~/.claude/hooks/tests/`
(48 ficheros allí, 11 en el repo, y el repo no tiene directorio `fixtures/` en absoluto).

Conducido igualmente contra la copia del repo, el drill respondió lo que tenía que responder:

```
[UserPromptSubmit-deadline-drill-critstarve-chain] ./tests/fixtures/drill-spawn-sentinel.js
    Error: script missing
```

Importar los ficheros del otro árbol para que mi test pase habría sido meter artefactos de otro
dueño en este repo bajo mi commit. No se hizo. **Se prefiere un verde no reclamado a un verde
prestado.**

## 4. Hallazgo colateral que el Owner debería ver

> **El repo documenta un drill que en el repo no se puede ejecutar.**

`hooks/tests/` tiene 11 ficheros aquí y 48 en el árbol vivo. La divergencia no es del
dispatcher —esa copia está **byte a byte idéntica**, sha256 `7EE00DAD…`— sino de su
**instrumentación**. Es la forma 2 de `documented-capability-must-be-executable`: la capacidad
existe, y su invocación documentada está muerta en este árbol.

No se repara aquí: decidir qué árbol es el dueño canónico de `hooks/tests/` es una decisión del
Owner, no una microdecisión de implementación.

## 5. Cómo aplicarlo (Owner)

El fichero vivo y el del repo eran idénticos antes de este cambio, así que copiar es seguro y no
pisa nada:

```
Copy-Item 'C:\Users\User\.claude\skills\claude-power-pack\hooks\hook-dispatcher.js' `
          'C:\Users\User\.claude\hooks\hook-dispatcher.js' -Force
```

Verificación posterior sugerida: comparar hashes, y en el siguiente `before pool` real comprobar
que la línea trae `skipped:` seguido de nombres.

**El agente no escribe bajo `~/.claude/hooks/`. HR-001, sin excepción y sin rodeo.**
