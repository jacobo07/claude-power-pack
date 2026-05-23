# Apollo GraphQL Ground Rules (inline card — auto-warmed on GraphQL signal)

- ALWAYS name operations: `query GetUser {` — never anonymous `query {`.
- ALWAYS pass dynamic arguments as `$variables`; never inline string/number literals.
- NEVER duplicate a field within one selection set.
- NEVER over-fetch: select only fields the caller uses; extract shared shapes into fragments.
- Mutations return only fields you will read back.

Full procedural modules (lazy-load on demand, do NOT auto-read):
`~/.claude/skills/claude-power-pack/vendor/apollo/upstream/<module>/SKILL.md`
Modules: apollo-client, apollo-server, apollo-mcp-server, apollo-connectors,
apollo-federation, apollo-router, graphql-schema, graphql-operations, rover, apollo-ios, apollo-kotlin.
