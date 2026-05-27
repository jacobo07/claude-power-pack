# Python Hooks (PP-specific)

PP hooks are JS/Node-based at the harness level (in `~/.claude/hooks/`),
but Python is the language for hook business logic in the PP repo
(under `tools/` and `modules/`).

This file documents Python-side hook integration patterns.

## Hook contract (Python invoked from JS)

Hooks invoke Python via:

```js
const result = spawnSync("python", ["tools/some_check.py"], {
    input: JSON.stringify(hookPayload),
    encoding: "utf-8",
});
```

The Python script reads stdin as JSON, writes a JSON response to
stdout, and exits 0 (allow) / 1 (block) / 2 (advisory).

## Reading hook input

```python
import json, sys

def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"bad input: {exc}"}),
              file=sys.stderr)
        return 0   # fail-open: don't block on bad hook input
    # ... process payload
    return 0
```

## Writing hook output

```python
def emit_advisory(message: str) -> None:
    print(json.dumps({
        "advisory": True,
        "additionalContext": message,
    }))
```

Hook stdout is captured and (depending on the hook type) injected
back into the model's context as `additionalContext`. KEEP IT SHORT
(< 1000 chars typical, < 5000 hard cap).

## Fail-open default

A broken hook must NEVER break the harness. Wrap the body in:

```python
if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:
        print(json.dumps({"hook_error": type(exc).__name__,
                          "msg": str(exc)}), file=sys.stderr)
        rc = 0   # don't block
    raise SystemExit(rc)
```

## Hook + TIS integration

When a hook produces meaningful telemetry (token cost, decision,
score), emit a TIS event using `tools/tis.py::append_log`. The
hook becomes auditable in `tis_report.py --by-skill`.

```python
from tools import tis
tis.append_log(tis.TokenEvent(
    session_id=tis.get_session_id(),
    timestamp_iso=datetime.now(timezone.utc).isoformat(),
    skill_name="my-hook",
    model="claude-code-hook",   # zero-priced telemetry
    input_tokens=len(prompt) // 4,
    output_tokens=len(advisory) // 4,
    call_label="hook-fired",
    project=os.getcwd(),
))
```

## Hook fanout pattern (L8 lesson)

Hooks fire 7-15 times per Write/Bash invocation. Heavy hooks (>100ms)
under load cause `internal-error` cascades. PP-specific mitigations:

- Use `hook-dispatcher.js` consolidation pattern (planned, BL future)
- Each hook completes in < 50ms typical
- No subprocess spawning inside a hook unless absolutely necessary

---

*Hook semantics largely PP-native; the JSON-in / JSON-out contract is
standard across ECC-style and Claude Code-native hooks.*
