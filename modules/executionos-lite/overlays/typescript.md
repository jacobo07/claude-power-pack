# Overlay: TypeScript

- **Strict Mode:** Enable `strict: true` in tsconfig. No `any`, no `@ts-ignore` without justification.
- **Validation:** Zod for runtime validation. Infer types from schemas: `z.infer<typeof Schema>`.
- **Framework:** Next.js App Router preferred. Server components by default, `"use client"` only when needed.
- **ORM:** Prisma or Drizzle. Always generate types. Never raw SQL without parameterization.
- **Testing:** Vitest preferred. React Testing Library for components. No snapshot tests.
- **Error Handling:** Typed error classes. Never `catch (e: any)`. Use Result pattern for expected failures.
- **Imports:** Absolute imports via path aliases. Barrel files only for public API boundaries.
- **Build:** `tsc --noEmit` must pass. ESLint must pass. Both checked before any completion claim.
- **State:** Server state via React Query/SWR. Client state via Zustand. No prop drilling past 2 levels.
- **Security:** Validate all inputs server-side. Sanitize HTML output. CSRF protection on mutations.
