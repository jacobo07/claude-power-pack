# Python Security

Extends [rules/common/security.md](../common/security.md).

## Subprocess safety

```python
# GOOD: list args, no shell
subprocess.run(["git", "fetch", remote], check=True, timeout=30)

# BAD: shell=True with user input
subprocess.run(f"git fetch {remote}", shell=True)  # command injection
```

Whenever you genuinely need a shell pipeline, use:

```python
subprocess.run(
    ["bash", "-c", "command1 | command2"],
    check=True, capture_output=True, text=True,
)
```

with `shell=False`. The shell IS invoked, but argv is explicit and
no user input is interpolated into the command string.

## pickle / eval / exec

- `pickle.load` on untrusted data == RCE. NEVER do it.
- `eval` / `exec` on user input == RCE. Use `ast.literal_eval` if
  you need to parse a literal Python expression from a trusted source.
- `__import__(name)` with user-supplied name is similar. Use
  explicit `importlib` with an allowlist.

## YAML safety

- `yaml.safe_load` ONLY -- never `yaml.load` without a SafeLoader
- `yaml.safe_dump` for output
- Better yet: prefer JSON for IPC; YAML is for human-edited configs

## Path traversal

```python
from pathlib import Path

def safe_read(user_path: str, base: Path) -> str:
    p = (base / user_path).resolve()
    if not p.is_relative_to(base.resolve()):
        raise ValueError(f"escapes base: {user_path}")
    return p.read_text(encoding="utf-8")
```

## Cryptography

- `secrets` module for tokens, NOT `random` / `Math.random`
- `hashlib.sha256` for hashing (not md5/sha1 except for non-security
  uses like cache keys -- comment it)
- bcrypt / argon2 for password hashing; never SHA + salt
- For signing: `cryptography` library with explicit algorithm

## Secrets management

- `os.environ` reads at startup, validated
- `.env` files NEVER committed (always in `.gitignore`)
- `.env.example` in repo with example variable names only (no real
  values)
- PP-specific: secrets allowlisted in
  `vault/normalize-allowlist.json` for paths+secrets sweep

## Logging hygiene (Python-specific)

```python
import logging
logger = logging.getLogger(__name__)

# GOOD: lazy formatting (no string built unless emitted)
logger.debug("user %s acted on %s", user_id, action_type)

# BAD: eager formatting (built every call, even if logger filters DEBUG)
logger.debug(f"user {user_id} acted on {action_type}")

# NEVER: log secrets
logger.info("api key: %s", api_key)   # NO
```

---

*Portions adapted from ECC rules/python/security.md under MIT License
(c) 2026 Affaan Mustafa.*
