# ICC Owner steps

## GEX44 dangling doctrine pointers (ICC Phase 1, HR-001)
GEX44 ~/.claude/CLAUDE.md names two files that do not exist there: knowledge_vault/core/HARD-RULES-DIGEST.md and SESSION_SAFETY_CONTRACT.md. Either copy them from the laptop or remove the two pointers:
  scp ~/.claude/knowledge_vault/core/HARD-RULES-DIGEST.md gex44:/home/kobii/.claude/knowledge_vault/core/ ; scp ~/.claude/SESSION_SAFETY_CONTRACT.md gex44:/home/kobii/.claude/
(creates the dir first if absent: ssh gex44 mkdir -p /home/kobii/.claude/knowledge_vault/core)

