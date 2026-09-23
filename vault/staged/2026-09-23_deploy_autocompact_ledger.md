# STAGED FOR OWNER — desplegar el daemon auto-compact con ledger de éxitos

**HR-001.** El fichero vivo está bajo `~/.claude/hooks/`, que es superficie de extensión del
agente. El parche se deja preparado y verificado; **lo aplica el Owner, no el agente**, y no
se rodea.

## Qué se despliega

`hooks/auto-compact-sendkeys-daemon.ps1` — commit `f6fe4ab`. Añade fila de ledger a los dos
caminos de éxito (`compact_dispatched`, `foreground_dispatched`), que antes sólo escribían en
el log del daemon. Sin esto el ledger sólo puede responder «nunca se entregó».

## Verificado antes de pedir el despliegue

| comprobación | resultado |
|---|---|
| `tools/test_autocompact_ledger_symmetry.py` | **4/4** |
| drill de mutación (quitar una escritura) | **3/4**, rojo en `SENT@413` |
| restauración tras la mutación | SHA-256 idéntico |
| bytes no-ASCII (PS 5.1 con `-File`) | **0** |
| errores de parseo PowerShell | **0** |
| deriva propia del espejo vivo | **0 líneas** sólo en el vivo; 19 sólo en el repo, que son las añadidas |

Esa última fila es la que autoriza una copia en vez de una fusión: el vivo es el repo menos
este cambio, así que nada del Owner se pierde al sobrescribir.

## Comando

Con copia de seguridad primero (HR-CASCADE-002 — nunca sobrescribir sin respaldo):

```powershell
$live = Join-Path $env:USERPROFILE '.claude\hooks\auto-compact-sendkeys-daemon.ps1'
Copy-Item $live "$live.bak-2026-09-23" -Force
Copy-Item 'C:\Users\User\.claude\skills\claude-power-pack\hooks\auto-compact-sendkeys-daemon.ps1' $live -Force
(Get-FileHash $live -Algorithm SHA256).Hash
```

El hash debe salir `E0C902C070E6FCC282B00B74F16BB94E0423E37723C3AA4DA92315F29CA1DE08`.

## Cómo saber que sirvió

En el próximo cruce de contexto que se entregue, el ledger
`~/.claude/state/gsd-autorun-ledger.jsonl` debe contener una fila `compact_dispatched`. Hoy
esa fila no puede existir, y ésa es exactamente la razón por la que una consulta sobre el
ledger concluyó —falsamente— que la entrega no había funcionado jamás.

**No se despliega solo.** Un daemon ya corriendo sigue ejecutando el fichero que cargó; el
cambio entra en el siguiente arranque.

## Lo que este parche NO arregla

Por qué falló la entrega del 2026-09-23 a las 12:45 es un defecto distinto y sigue abierto: la
petición se aplazó por `status-busy` y se retiró 2 minutos después porque la última línea del
asistente dejó de ser la esperada, pese a que la emitida y la pedida eran idénticas. Antes de
afirmar la causa hay que leer `Get-LastAssistantLine` y decidir qué cuenta como «última línea
del asistente» cuando el turno lleva texto antes de la orden.
