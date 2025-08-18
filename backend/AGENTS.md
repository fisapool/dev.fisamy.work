# Repository Guidelines

## Project Structure & Module Organization
- Root SPA: React + TypeScript via Vite. Key files: `index.html`, `index.tsx`, `index.css`.
- Build output: `dist/` (generated; do not edit or commit).
- DevOps assets: `backend/` (e.g., `docker-compose.yml`, `Caddyfile`) for hosting/templates; not required for local SPA.
- Config: `vite.config.ts` (alias `@` → project root), `tsconfig.json` (ES2022, JSX `react-jsx`).
- Place small components near usage; extract to `*.tsx` files when they grow.

## Build, Test, and Development Commands
- `npm install`: Install dependencies.
- `npm run dev`: Start Vite dev server with hot reload.
- `npm run build`: Production build to `dist/`.
- `npm run preview`: Serve the production build locally.

## Coding Style & Naming Conventions
- Language: TypeScript + React 19; target ES2022.
- Formatting: 2‑space indent, semicolons, double quotes.
- Components: Function components + hooks. Co‑locate small pieces; otherwise split into `*.tsx`.
- Imports: Use `@/…` for project‑root imports (from `vite.config.ts`).
- Styling: Tailwind via CDN in `index.html`; app‑wide tweaks in `index.css`.

## Testing Guidelines
- No runner configured yet. Prefer Vitest + React Testing Library when adding tests.
- Naming: `*.test.ts` / `*.test.tsx` adjacent to source or in `__tests__/`.
- Aim for meaningful coverage of pure logic and critical UI paths; avoid snapshot bloat.
- Example (once configured): `npm run test` or `vitest run`.

## Commit & Pull Request Guidelines
- Commits: Imperative mood, concise subject (e.g., `feat: add yearly billing toggle`).
- PRs: Clear description, motivation, and scope; link issues. Include screenshots/GIFs for UI changes and verification steps (`npm run dev` → navigate to section).
- Do not commit generated assets in `dist/`.

## Security & Configuration Tips
- Environment: set `GEMINI_API_KEY` in `.env.local` (untracked). Exposed via `define` in `vite.config.ts`.
- Never hard‑code secrets in `index.tsx` or HTML. Verify `.gitignore` rules for local env files.
- Review external links and analytics before merging.

