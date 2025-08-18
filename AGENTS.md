# Repository Guidelines

## Project Structure & Module Organization
- Root SPA: React + TypeScript via Vite. Key files: `index.html`, `index.tsx`, `index.css`.
- Build output: `dist/` (generated; do not edit by hand).
- DevOps assets: `backend/` (e.g., `docker-compose.yml`, `Caddyfile`) for hosting/templates; not required to run the SPA locally.
- Config: `vite.config.ts` (defines alias `@` → project root), `tsconfig.json` (ES2022, JSX `react-jsx`).

## Build, Test, and Development Commands
- `npm install`: Install dependencies.
- `npm run dev`: Start Vite dev server (hot reload).
- `npm run build`: Production build to `dist/`.
- `npm run preview`: Serve the production build locally.

## Coding Style & Naming Conventions
- Language: TypeScript + React 19; target ES2022.
- Indentation: 2 spaces; use semicolons and double quotes to match existing code.
- Components: Prefer function components and hooks; colocate small components near usage in `index.tsx` or split into `*.tsx` files if refactoring.
- Imports: Use `@/…` for project‑root imports per `vite.config.ts`.
- Styling: Tailwind via CDN in `index.html` plus `index.css` for app‑wide tweaks.

## Testing Guidelines
- No test runner is configured yet. If adding tests, prefer Vitest + React Testing Library.
- Naming: `*.test.ts`/`*.test.tsx` adjacent to source or in `__tests__/`.
- Aim for meaningful coverage on pure logic and critical UI behavior; avoid snapshot bloat.

## Commit & Pull Request Guidelines
- Commits: Imperative mood, concise subject. Example: `feat: add yearly billing toggle`.
- PRs: Clear description, motivation, and scope; link issues; include screenshots/GIFs for UI changes and steps to verify (`npm run dev` → navigate to section).
- Do not commit secrets or generated assets in `dist/`.

## Security & Configuration Tips
- Environment: set `GEMINI_API_KEY` in `.env.local` (not committed). Vite exposes it via `define` in `vite.config.ts`.
- Secrets: never hard‑code keys in `index.tsx` or HTML. Use local env files and verify `.gitignore` rules.
- Review external links (checkout URLs, analytics) before merging.
