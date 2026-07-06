# PowerShell 5.1 reads .ps1 with ANSI codepage, not UTF-8

**Sealed:** 2026-05-24 (video-analyzer MCP ngrok setup)
**Affects:** any .ps1 launched via Task Scheduler / `powershell.exe -File` on Windows where the file contains non-ASCII characters.

## Trap

Wrote a Task Scheduler wrapper `boot_server.ps1` with em-dashes in comments:
```powershell
# Bearer is read from .bearer (NOT hardcoded here — rotation friendly).
```
The `—` (U+2014) is UTF-8 bytes `E2 80 94`. PowerShell 5.1 (`powershell.exe`, NOT `pwsh`) reads .ps1 files using the **system ANSI codepage** (cp1252 / cp850 / cp437 depending on locale). Those three bytes get mis-interpreted as three Latin-1 glyphs, which PowerShell's parser then sees as garbage tokens. The parser confuses itself and reports a phantom error 5-15 lines AWAY from the actual culprit:
```
boot_server.ps1: 28 Carácter: 9
+ } catch {
+         ~
Falta la llave de cierre "}" en el bloque de instrucciones
```
The `}` on line 28 is fine. The actual culprit is the em-dash on line 3 (or wherever) that mis-parsed and threw the brace counter off.

## Detection

If `Start-Process powershell.exe -ArgumentList '-File','foo.ps1' -RedirectStandardError x` produces a parse error about an unmatched brace, but the file LOOKS syntactically clean in your editor (which renders UTF-8), check encoding:
```powershell
$bytes = [System.IO.File]::ReadAllBytes('foo.ps1')[0..15]
($bytes | ForEach-Object { $_.ToString('X2') }) -join ' '
```
If you see `EF BB BF` at the start it's UTF-8 BOM — 5.1 handles that correctly. If you see raw UTF-8 sequences (`E2 80 94`, `C3 A9`, etc.) without a BOM, that's the trap.

## Fix (cheap)

Keep all .ps1 files that Task Scheduler launches **7-bit ASCII**:
- `—` -> `--`
- `é`/`á`/`ó` -> ascii equivalents
- `"` (smart quote) -> `"` (straight)
- `'` (smart apostrophe) -> `'`

## Fix (proper)

Write the file with a UTF-8 BOM. In Edit/Write tooling that doesn't add BOMs, you can post-process:
```powershell
$content = Get-Content 'foo.ps1' -Raw
[System.IO.File]::WriteAllText('foo.ps1', $content,
    (New-Object System.Text.UTF8Encoding $true))   # $true = emit BOM
```
But the ASCII path is friction-free for boot wrappers, which never need fancy chars.

## Why this matters cross-project

Any project that uses Task Scheduler / Service Control / `powershell.exe -File` as the trampoline for boot-time work risks this. Symptoms look like the script never ran, or ran without effect. Adds 10-30 min of debugging because:
- Last task result reports SUCCESS / RUNNING (the parser error happens INSIDE PowerShell after task already "started")
- No stderr capture unless you `-RedirectStandardError` (which most Register-ScheduledTask wrappers don't)
- The error message points to the wrong line, so editor inspection of the named line shows valid code

## Cross-ref

- vault/runbooks/video-analyzer-mcp.md
- ASCII-only header comment in C:\Users\User\Apps\mcp-video-analyzer\boot_server.ps1 and boot_tunnel.ps1
- Memory: feedback_powershell_51_script_encoding_ascii_only.md
