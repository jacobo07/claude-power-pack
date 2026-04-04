# Self-Healing Patterns Catalog

## KobiiCraft Server Patterns (25)

| # | Pattern | Auto-Fix Action |
|---|---------|----------------|
| 1 | ClassNotFoundException | Recompile + redeploy |
| 2 | Duplicate JAR in plugins/ | Delete old, restart |
| 3 | YAML syntax error in config | Restore from backup |
| 4 | Economy bridge null (Vault) | Verify Vault plugin, restart |
| 5 | OutOfMemoryError | Alert + request restart |
| 6 | TPS < 15 for 60 seconds | Alert + identify heavy plugin |
| 7 | Plugin disabled after startup | Read stack trace, recompile |
| 8 | World save failed | Check disk space |
| 9 | Host connection timeout | Retry 3x with exponential backoff |
| 10 | API auth 401/403 | Refresh token |
| 11 | SFTP upload failed | Retry with fresh connection |
| 12 | Build failed (Maven) | Parse error, attempt auto-fix |
| 13 | JAR size 0 bytes | Delete + recompile |
| 14 | Plugin version mismatch | Alert (manual needed) |
| 15 | Citizens hook failure | Check JAR version compatibility |
| 16 | PlaceholderAPI null expansion | Register missing placeholder |
| 17 | Scoreboard flicker | Reduce update frequency |
| 18 | Chat format conflict | Check for duplicate handlers |
| 19 | Command collision | Alert with both conflicting plugins |
| 20 | Permission node missing | Alert with suggestion |
| 21 | Resource pack download failed | Verify URL + file size |
| 22 | Async chunk load warning | Alert with stack trace |
| 23 | Entity count > 500 in chunk | Alert + check MobCap settings |
| 24 | Potion effect leak | Nuclear purge (3-layer clear) |
| 25 | Deprecated API usage | Log for next compile cycle |

## Gameplay Bug Detection (13)

| # | Bug | Detection | Response |
|---|-----|-----------|----------|
| 1 | Slow falling persists | Log analysis for effect duration | Force purge |
| 2 | Boss teleport erratic | Multiple setVelocity calls in logs | Alert developer |
| 3 | GUI clicks not registering | InventoryClickEvent without handler | Alert |
| 4 | Bet not resolving | Created but no resolution in 5s | Alert |
| 5 | Economy balance < 0 | Vault balance check | Freeze withdrawals |
| 6 | Duplicate bet acceptance | Two players accept same bet | Alert + rollback |
| 7 | Match stuck in state | State unchanged > 5 min | Force transition |
| 8 | Player trapped in arena | In region, no active match | Teleport to spawn |
| 9 | Display crash | Exception in render log | Disable + blacklist |
| 10 | Token balance desync | File vs runtime mismatch | Force file reload |
| 11 | Kill reward not given | Kill event without deposit | Alert |
| 12 | Scoreboard overlap | Multiple scoreboards competing | Check priority |
| 13 | Chest GUI duplication | Item count change after close | Rollback inventory |

## Universal Patterns (domain-agnostic)

### API Error Self-Healing (from AADEF SelfHealingAgent)
1. Error intercepted → check PatternStore for known fix
2. Known fix found → apply cached fix, record success
3. Unknown error → query LLM (Claude/Ollama) with error + last-known-good schema
4. LLM proposes patch → apply tentatively
5. Monitor next 10 requests → all succeed → auto-commit to PatternStore
6. Any fail → rollback to last-known-good, alert human

### Adding New Patterns
```elixir
# Register a new pattern in PatternStore
PatternStore.register("new_fingerprint", %{
  pattern_key: "DescriptivePatternName",
  action: :your_fix_action
})
```

For non-Elixir: maintain a JSON/YAML pattern file with the same structure. The pattern should include: fingerprint (how to detect), action (what to do), and confidence (how sure we are this fix works).
