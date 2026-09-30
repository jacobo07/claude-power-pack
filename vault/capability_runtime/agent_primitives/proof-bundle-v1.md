## Output contract: proof bundle v1

This contract replaces any other output format in your role. Your final reply is
ONE fenced `json` block and nothing else. The parent validates it mechanically;
prose outside the block is discarded, and a malformed block is rejected.

```json
{
  "bundle": "proof-bundle/v1",
  "spec": "{spec}",
  "spec_hash": "{spec_hash}",
  "state_version": "{state_version}",
  "summary": "<one or two sentences, at most 400 characters>",
  "claims": [
    {"id": "C1", "statement": "<one finding>", "status": "OBSERVED",
     "severity": "high", "evidence": ["path/to/file.py:42"]}
  ],
  "counterevidence": ["<what you checked that argues against a claim>"],
  "unknowns": ["<what you could not determine, and why>"],
  "recommendation": "<the single next action>",
  "artifacts": [],
  "pages_read": ["<deep pages of your role you Read, by path>"]
}
```

Rules the validator enforces:

- `spec`, `spec_hash` and `state_version` are copied exactly as given above.
- `status` is one of OBSERVED, PROVEN, INFERRED, UNKNOWN, CONFLICTING.
- An OBSERVED or PROVEN claim cites at least one `path:line` you actually read.
- `severity` is one of critical, high, medium, low, info.
- Nothing found is a valid result: `claims` may be empty. Never invent a finding.
- Put what you could not check in `unknowns`, never in `claims` as if it were absent.
