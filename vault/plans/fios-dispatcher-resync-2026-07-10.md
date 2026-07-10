# FIOS dispatcher resync -- Owner action (pending)

Verificado 2026-07-10. Pre-Fable prep. HR-001: el agente NO escribe en
`~/.claude/hooks/`; solo documenta el comando exacto.

## Estado verificado
- Canonical `hooks/hook-dispatcher.js` (repo, HEAD b7ae636): **624 lineas, completo.**
  Contiene FD-07 flywheel, FIOS token_irr, graph_first (GK-12), y todas las entradas
  Stop-chain / PreToolUse recientes.
- Live `~/.claude/hooks/hook-dispatcher.js`: **617 lineas.**
- **Drift = exactamente el bloque FIOS token_irr** (6 lineas de comentario + 1 entrada
  PY_EXE). `Compare-Object` confirma que live es un SUBCONJUNTO ESTRICTO del canonical:
  el Copy-Item solo AGREGA el bloque token_irr, no pisa nada live-only.

## Comando exacto (Owner, 1 linea) + activacion
```powershell
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\hook-dispatcher.js" "$env:USERPROFILE\.claude\hooks\hook-dispatcher.js" -Force
```
Luego `/restart` (los hooks cargan una vez al inicio de sesion; una edicion en vivo no
activa hasta reiniciar).

## Verificacion post-copia (Owner puede correr)
```powershell
Select-String -Path "$env:USERPROFILE\.claude\hooks\hook-dispatcher.js" -Pattern 'frontier_intelligence/token_irr.py' -Quiet
# -> True cuando el Stop-chain FIOS esta live
```

## Efecto
Con el Copy-Item + /restart, el Stop-chain de una sesion FRONTIER (kclaude, que exporta
PP_FRONTIER_SESSION=1) ejecutara `token_irr.py` en cada cierre de turno y emitira
`FIOS IRR: ...` via systemMessage + alimentara CO-12. Sin el Copy-Item, la entrada existe
solo en el canonical y el Stop-chain FIOS permanece inerte (fail-open: no rompe nada).

Mismo last-mile que FD-07 (T-HOOK-DISPATCHER-DRIFT-001). El preflight de kclaude
(session_compiler) YA esta live -- kclaude.ps1 es su propio archivo, no pasa por el
dispatcher, asi que no requiere Copy-Item.
