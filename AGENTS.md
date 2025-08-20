# Repository Guidelines

## Project Structure & Module Organization
- Root SPA: React + TypeScript via Vite.
- Key files: `index.html`, `index.tsx`, `index.css` (root).
- Build output: `dist/` (generated; do not edit).
- DevOps assets: `backend/` (e.g., `docker-compose.yml`, `Caddyfile`); not required for local dev.
- Config: `vite.config.ts` (alias `@` → project root), `tsconfig.json` (ES2022, JSX `react-jsx`).
- Components: prefer function components + hooks. Collocate small pieces near usage in `index.tsx` or extract into `*.tsx` files when refactoring.

## Build, Test, and Development Commands
- `npm install`: Install dependencies.
- `npm run dev`: Start Vite dev server with hot reload.
- `npm run build`: Production build to `dist/`.
- `npm run preview`: Serve the production build locally.

## Coding Style & Naming Conventions
- Language: TypeScript + React 19; target ES2022.
- Formatting: 2‑space indentation, use semicolons, double quotes.
- Imports: use `@/…` for project‑root imports per `vite.config.ts`.
- Styling: Tailwind via CDN in `index.html` plus app‑wide tweaks in `index.css`.

## Testing Guidelines
- No runner configured yet. If adding tests, prefer Vitest + React Testing Library.
- Naming: `*.test.ts` / `*.test.tsx` adjacent to source or in `__tests__/`.
- Aim for meaningful coverage on pure logic and critical UI interactions; avoid brittle snapshot tests.

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise subject. Example: `feat: add yearly billing toggle`.
- PRs: include clear description, motivation, and scope; link issues.
- For UI changes: add screenshots/GIFs and simple verification steps (e.g., `npm run dev` → navigate to the changed section).

## Security & Configuration Tips
- Secrets: never hard‑code keys in code or HTML. Use `.env.local` (not committed). Example: set `GEMINI_API_KEY`.
- Vite: expose env via `define` in `vite.config.ts` as needed.
- Verify `.gitignore` covers env files and `dist/`.
- Review external links and analytics before merging.

