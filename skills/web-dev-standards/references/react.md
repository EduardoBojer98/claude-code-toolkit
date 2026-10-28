# React + Vite + TypeScript + Tailwind

Part of web-dev-standards. Load for React/Vite apps.

- Strict TypeScript; typed props; no `any` without a comment; one component per file, `PascalCase.tsx`.
- State close to where it's used; derive instead of duplicating; URL state for filters and tabs.
- Every async view has loading, empty and error states.
- Tailwind v4 with `@theme` tokens; extract repeated utility groups into components, not `@apply` everywhere.
- Code-split routes; check bundle size before adding a dependency; Vitest for logic, Playwright for flows.
- Secrets never in client code (`VITE_` vars are public); `.env.example` committed.

