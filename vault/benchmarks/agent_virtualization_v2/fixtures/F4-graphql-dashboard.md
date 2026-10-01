# Plan: team activity dashboard widget

Context: Next.js 15 frontend using Apollo Client 3.11 against the existing GraphQL
gateway. A Node 22 CLI lives in `tools/` and the team's Claude Code hooks are kept
alongside the project. Developers work on both Windows and macOS.
Audit this plan. It is self-contained: do not explore any repository.

Step 1. Add `src/graphql/activity.graphql` for the widget's main list:

    query ($teamId: ID!) {
      teamActivity(teamId: $teamId) { id kind actor at }
    }

Step 2. Add a second operation for the incident strip on the same widget:

    query RecentIncidents {
      incidents(severity: "high", first: 25) { id title openedAt }
    }

Step 3. Add a CLI, `tools/export_activity.js`, that writes its report to
`reports/activity.json`, wherever the command happens to be launched from.

Step 4. The same CLI caches each team's data at
`os.homedir() + "\\.cache\\activity\\" + teamId + ".json"`.

Step 5. Add a pre-commit guard hook, `activity-guard.js`, at the repository root and
register it from there.

Step 6. Before rendering, the widget sends each GraphQL response to a small LLM call
that answers whether the JSON has the expected shape; it renders only when the model
answers "valid".
