### MEDIUM -- React / Next.js (when applicable)

> **For React-specific review, prefer `react-reviewer` via `/react-review`.** This block remains as a fallback only — when the diff contains `.tsx`/`.jsx` files, both agents should be invoked. See `agents/react-reviewer.md` for the full React-specific CRITICAL/HIGH rule set (hooks rules, `dangerouslySetInnerHTML`, RSC boundaries, accessibility, render performance).

- **Missing dependency arrays**: `useEffect`/`useCallback`/`useMemo` with incomplete deps — use exhaustive-deps lint rule
- **State mutation**: Mutating state directly instead of returning new objects
- **Key prop using index**: `key={index}` in dynamic lists — use stable unique IDs
- **`useEffect` for derived state**: Compute derived values during render, not in effects
- **Server/client boundary leaks**: Importing server-only modules into client components in Next.js

