# PARTS C + H + R — TOKEN OPTIMIZATION TOOLS

## C: Basic Optimization
| Trigger | Action |
|---------|--------|
| "token audit" | Rank sources by cost, flag >500 |
| "compress this" | Rewrite shorter, preserve semantics |
| "dedup check" | Find overlapping rules |
| "memory audit" | Audit memory for bloat (E6+E7+E8) |
| "PRD version" | Check PRD needs updating |

## H: Reinforced Tools
| Tool | Command |
|------|---------|
| ExecutionOS compressor | `python modules/token-optimizer/executionos_compressor.py` |
| CLAUDE.md linter | `python modules/token-optimizer/claudemd_linter.py` |
| Cross-project dedup | `python modules/token-optimizer/cross_project_dedup.py` |
| Plugin waste detector | `node modules/token-optimizer/plugin_waste_detector.js` |

## R: Token Forensics
`python modules/token-optimizer/token_autopsy.py` — parses JSONL session logs for burn report.
