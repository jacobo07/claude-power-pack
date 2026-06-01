# PowerShell 5.1 pipes BOM to native exes -- transversal trap

**Sealed:** 2026-06-01
**Severity:** transversal -- any Windows host where PS 5.1 produces and a strict-parser process consumes
**Sister rule:** v15 Bash blocklist (CLAUDE.md), `vault/lessons/grep-large-file-sentinel-pivot.md`

## The bug

PowerShell 5.1 prepends a 3-byte UTF-8 BOM (`EF BB BF`) to ANY string piped to a native exe via `$str | & exe.exe`. The downstream process sees `﻿` as the first character of stdin. Strict parsers (`JSON.parse` in Node, `json.loads` in Python without `utf-8-sig`) reject the BOM as an unexpected token and error out. If the consumer fail-opens on parse error, the BOM silently turns the consumer into a no-op.

## Where it bit us first

`hooks/secret_firewall_gate.js` -- the PreToolUse Secret Firewall would silently `continue:true` for ALL payloads, including ones with CRITICAL secrets. Every payload arrived BOM-prefixed; `JSON.parse(payload)` always threw; the catch fail-opened. The hook looked operational (PASS / SKIP / FAIL-OPEN cases all returned `continue:true` for the right reasons); it actually never blocked.

Trace from the diagnostic run (M2 done-gate, 2026-06-01):

```
[sf-hook] payload: {"len":123,"head":"﻿{\"tool_name\":\"Write\",..."}
[sf-hook] json-parse-error: {"message":"Unexpected token '﻿', \"﻿{\"tool_na\"... is not valid JSON"}
{"continue":true}
```

The `﻿` (U+FEFF) at position 0 is the BOM. Payload length is 123, not the 120 the producer sent -- the 3 extra bytes are the BOM.

## Defenses (priority order)

1. **Consumer-side BOM strip** -- robust regardless of producer:
   - Node: `if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1);`
   - Python: `text.removeprefix('﻿')` (3.9+), or `open(path, encoding='utf-8-sig')` for files

2. **Producer-side: force PS no-BOM encoding** -- harder to enforce universally:
   ```powershell
   $OutputEncoding = New-Object System.Text.UTF8Encoding $false
   [Console]::OutputEncoding = $OutputEncoding
   ```

3. **Round-trip through a tempfile** -- bulletproof but slow:
   ```powershell
   [System.IO.File]::WriteAllText('.\_tmp.json', $json, (New-Object System.Text.UTF8Encoding $false))
   & node hook.js < .\_tmp.json
   ```
   (`Set-Content -Encoding utf8` on PS 5.1 ALSO writes BOM; use the no-BOM UTF8Encoding ctor or `WriteAllText` directly.)

## Sister rules

- `feedback_python_utf8_bom.md` (memory) -- Python `read_text('utf-8')` keeps BOM; use `'utf-8-sig'`
- `feedback_grep_large_file_sentinel.md` -- Windows Grep tool transversal hang (different mechanism, same family)
- v15 Bash blocklist (CLAUDE.md) -- producer fragility (`tail | head | cat | grep`)
- `vault/lessons/parallel-batch-large-output-cascade.md` -- different consumer-frame failure on Windows

## The rule

Every Node/Python hook, CLI, or service that reads stdin on a Windows host MUST strip a leading BOM. Treat it as a one-line defensive header -- absence is a latent bug, especially when paired with a fail-open `try/catch` that lets the consumer LOOK like it works.

## Cross-refs

- First fix: `hooks/secret_firewall_gate.js` (M2, commit `4ee00ca`)
- Cross-repo doctrine tag: `windows-pipe-bom-strip-v1`
