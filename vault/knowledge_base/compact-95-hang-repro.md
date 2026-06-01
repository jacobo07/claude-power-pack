# /compact 95% Hang — Reproduccion empirica

**Fecha:** 2026-06-01
**BL:** BL-COMPACT-001
**Primer reporte:** este ciclo (sin precedente en vault, grep
sobre `vault/` y memoria de proyecto confirmo ningun hit
previo de "compact 95" / "compact hang" / "stuck at 95")

## Sintoma

Owner ejecuta `/compact` desde el chat slash interface. El
indicador visual de progreso avanza hasta aproximadamente
**95%** y se congela indefinidamente. No hay nuevas
escrituras en el `.jsonl` de la sesion. `claude.exe` sigue
vivo con RSS alto (>200MB observado, picos a 451MB) y CPU
baja (<2%). El unico camino de recuperacion actual es
matar el proceso a mano.

Quote literal del Owner (2026-06-01):

> "no, o sea yo hago /compact y a lo mejor se queda en 95% sabes?"

## Root cause (lo mejor que podemos saber sin source-access)

El hang ocurre **DESPUES** de la respuesta de la API. Por
eso llega al 95% y no se queda en 5%: la API ya entrego el
summary. El cuelgue es en lo que viene despues:

1. Rebuild del context window con el summary
2. Write final del nuevo `.jsonl` (o rotacion del anterior)
3. Reload del prompt cache
4. Render final del TTY en claude.exe

Vive en el binary de `claude.exe`. **No es patcheable
desde el Power Pack** — solo podemos darle al Owner una
salida limpia cuando pasa.

## Por que NO hacemos auto-kill heuristico

La heuristica obvia (`RSS > 200MB` AND `CPU < 2%` AND
`.jsonl idle > 5min`) tiene **false positives caros**:

- Si el Owner esta pensando un problema largo (lectura,
  planning, agente sub-dispatched), el watchdog le mata la
  sesion activa.
- La senal visual del 95% no es observable desde
  filesystem/process state — vive en el rendering del TTY
  de Cursor. Sin OCR ni hook al UI, no la tenemos.

Por eso la decision arquitectural es:

- **Rescue script** Owner-triggered, no automatico. El
  Owner ve el 95% stuck y dispara `/compact-rescue`.
- **Detector script** alert-only, opt-in. Nunca mata.
  Notifica y sugiere `/compact-rescue` al Owner.

## Evidencia del entorno (2026-06-01 08:50Z)

| Senal | Valor |
|---|---|
| claude.exe procs vivos | 40 |
| RSS observados (top 3) | 451MB / 373MB / 352MB |
| Daemon SendKeys dispatches | 15 OK / 2 TTL-only |
| `.jsonl` write integrity | OK pre-compact (append-only) |
| Hang location | post-API, pre-final-render |
| Hook fanout pressure | sum 7-15 PreToolUse hooks/Bash |

Correlacion observada: las sesiones con transcript grande
(RSS alto) son las que mas probable cuelgan en post-compact.
Sugiere que el bug se dispara por el size del summary +
rebuild del context — no por la red.

## Trade-offs del rescue

**Lo que se pierde con `/compact-rescue`:**
- El summary del compact en generacion (lo que el modelo
  estaba produciendo cuando claude.exe se cuelga).

**Lo que se conserva:**
- El transcript completo pre-compact. `.jsonl` es
  append-only y cada turn se persiste antes de que el
  compact empiece.
- El `sessionId` se recupera del `.jsonl` o de la env var
  `CLAUDE_CODE_SESSION_ID` → `--resume` lo restaura.

**Resultado neto:** el Owner pierde el summary y vuelve al
estado pre-compact. Puede intentar `/compact` de nuevo o
trabajar sin el (el transcript real esta intacto).

## Por que es Process Rule (PR), no Hard Rule (HR)

PR-COMPACT-001 es un protocolo recuperable. No hay riesgo
de perdida irreversible de datos. El transcript sobrevive
intacto. Hard Rules estan reservadas para bugs con
consecuencia destructiva — el compact hang no califica.

## Cross-refs

- Anti-Waiting doctrine (G): turn debe terminar con texto;
  el rescue tambien debe terminar con un "Que hacer ahora"
  legible — no quedar mudo.
- BL-0056 (`vault/audits/lpa_auto_compact_infeasibility.md`):
  /compact es chat slash command, no terminal command. Solo
  el chat lo puede invocar. El rescue trabaja en la capa
  inferior (process tree) precisamente porque no podemos
  reinvocar /compact desde fuera.
- `auto-compact-sendkeys-daemon.ps1` (BL-0003 bypass): el
  daemon dispara el Enter del `/compact`, pero NO observa
  el resultado. El rescue cubre justo ese gap.

## Reach del fix (honesto)

El rescue **NO arregla el bug de claude.exe**. Solo le da
al Owner una salida limpia cuando pasa. La unica forma de
arreglar el bug de verdad es reportarlo upstream a
Anthropic — eso lo hace M6 con `anthropic-issue-compact-95.md`.
