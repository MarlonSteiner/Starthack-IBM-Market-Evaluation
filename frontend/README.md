# MarketPulse Lite — Frontend (Vite + React)

A lightweight React + Vite UI for the MarketPulse Lite prototype. It presents a clean, responsive interface that can surface market-moving news, concise summaries, and client-ready insights.

## What this is

This frontend is the presentation layer of the MarketPulse Lite concept: a tool that detects market-moving financial news, summarizes it, and tailors insights for banking clients after human-in-the-loop review.

### Case introduction (context)
- **Problem**: Analysts must constantly scan global news for events that can move markets and affect client portfolios. It’s resource‑intensive and risks missing critical developments.
- **Goal**: Automatically identify relevant news (e.g., Fed decisions, CEO exits, earnings surprises), summarize them, and prepare for human review before delivery to clients.
- **Audience**: W&P analysts and strategists who transform findings into ad‑hoc communications (e.g., CIOs briefing advisors quickly and accurately).

## Features (UI scope)
- Responsive landing and content sections (Hero, Services, Work, Teams, Contact)
- Ready to integrate with a backend for news ingestion and approvals
- Tailwind CSS 4 for rapid styling

## Tech stack
- React 19, Vite 7
- Tailwind CSS 4
- ESLint

## Getting started

```bash
# from repository root
cd frontend
npm install
npm run dev
```

- Dev server defaults to http://localhost:5173
- Build and preview:
```bash
npm run build
npm run preview
```
- Lint:
```bash
npm run lint
```

## Scripts
- **dev**: starts Vite dev server
- **build**: builds production assets
- **preview**: serves the production build locally
- **lint**: runs ESLint

## Project structure
```
frontend/
  index.html
  package.json
  vite.config.js
  public/
  src/
    assets/
    components/
    App.jsx
    main.jsx
    index.css
```

## Integrations (future)
- Connect to a backend that handles: ingesting financial news/APIs, deduplication, classification, summarization, approval state, and weekly brief compilation.

## Notes
- No environment variables are required for the basic UI preview.
- Replace demo sections/assets with real data bindings as the backend matures.
