# Recovery graceful-beacon activation -- Owner action (pending)

Verificado 2026-07-10. SCS C83 addendum. HR-001: el agente NO escribe en
`~/.claude/hooks/` ni en `~/.claude/settings.json`; solo documenta los comandos
exactos. Mismo last-mile que `fios-dispatcher-resync-2026-07-10.md`
(T-HOOK-DISPATCHER-DRIFT-001).

## Estado verificado
- Canonical `hooks/session_end_graceful_beacon.js` (repo, en HEAD): **completo**,
  Woz-clean (sin catch vacios), round-trip probado (active -> graceful ->
  classify=graceful-reopen; live terminals -> reload).
- Live `~/.claude/hooks/session_end_graceful_beacon.js`: **NO existe** (sin mirror).
- `~/.claude/settings.json` "SessionEnd": array de bloques
  `{ "hooks": [ { "type":"command", "command":"...node... ...js", "timeout":N } ] }`.
  Hoy contiene learning-sentinel + lazarus-index-aggregator; falta el beacon.
- Efecto de la ausencia: `power_beacon` deja el active-beacon como ultima palabra
  en disco, asi que `classify_startup` lee CADA cierre como `ungraceful-shutdown`,
  incluso un cierre limpio.

## Comando exacto (Owner) -- 2 pasos

### Paso 1 -- Copy-Item (canonical -> live)
```powershell
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\session_end_graceful_beacon.js" "$env:USERPROFILE\.claude\hooks\session_end_graceful_beacon.js" -Force
```

### Paso 2 -- Registrar en settings.json (anadir al array "SessionEnd")
Anadir este bloque como un elemento mas del array `"SessionEnd"` en
`~/.claude/settings.json` (junto a los existentes, no reemplazarlos):
```json
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/session_end_graceful_beacon.js\"",
            "timeout": 5000
          }
        ]
      }
```
Luego `/restart` (los hooks cargan una vez al inicio de sesion; una edicion en
vivo no activa hasta reiniciar).

## Verificacion post-activacion (Owner puede correr)
```powershell
# 1. el hook esta live
Test-Path "$env:USERPROFILE\.claude\hooks\session_end_graceful_beacon.js"   # -> True
# 2. esta registrado en settings.json
Select-String -Path "$env:USERPROFILE\.claude\settings.json" -Pattern 'session_end_graceful_beacon' -Quiet   # -> True
# 3. tras cerrar una sesion limpiamente, el beacon quedo graceful
Get-Content "$env:USERPROFILE\.claude\state\power_beacon.json" | Select-String '"kind": "graceful"'   # -> match
```

## Efecto
Con Copy-Item + registro + `/restart`, un cierre limpio de sesion escribe
`write_graceful_exit`, de modo que el siguiente arranque se clasifica
`graceful-reopen` en vez de `ungraceful-shutdown`. La reentry recorder (G5) solo
graba una recuperacion cuando el arranque es genuinamente ungraceful -- este hook
elimina el falso-ungraceful de todo cierre normal. Fail-open absoluto: cualquier
error se anota en `%TEMP%\pp-graceful-beacon.log` y la sesion cierra igual.
