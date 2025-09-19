# MarketPulse Lite

A prototype tool that detects market‑moving financial news, summarizes it, and tailors insights to specific bank clients — helping teams deliver faster, smarter pitches.

## Case introduction

- **Problem**: To build a clear financial perspective, analysts and strategists must constantly scan global news for market‑moving events and portfolio‑relevant developments. This is resource‑intensive and risks missing critical items.
- **Goal**: Develop a prototype that automatically identifies news relevant to financial markets (e.g., Fed decisions, CEO exits, earnings surprises), summarizes them, and prepares them for human‑in‑the‑loop review before delivery to clients.
- **Audience**: End users are analysts who turn this information into ad‑hoc communication for clients (e.g., CIOs who must brief advisors quickly and accurately or adapt portfolios accordingly).

## Solution overview

- Ingest market news from high‑signal public sources and/or APIs
- Classify relevance to assets and regions
- Auto‑draft three short lines: What happened, Why it matters, Portfolio impact
- Human approves before publication
- Weekly brief compiles approved items from the last 7 days

## Key workflows

- Hourly update: pull feeds/APIs, dedupe, classify, draft three lines
- Curation: analyst reviews queue, tweaks text, approves
- Advisor view: Today and Weekly tabs; copy text or share PDF
- Weekly brief: compile only approved items from the last 7 days
- Publish: store PDF and share via pre‑signed link

## Data the user should see

- For analysts: ingestion status, relevance score, editable fields (title, lead, bullets, tags), approval state with timestamp, error states
- For advisors: last refresh time, 7‑day coverage window, source and link, publish time, three‑line summary, tags, simple impact chip, editorial cutoff, legal disclaimer, quick actions
- For clients: weekly PDF with week range, approved cards, editorial cutoff, imprint and disclaimer

## Non‑functional requirements

- Freshness (hourly)
- Reliability (graceful degradation on source failure)
- Auditability (who approved what and when)
- Compliance (sources, cutoff, disclaimer)
- Localization (DE and EN)
- Minimal PII

## IBM Cloud footprint (target)

- Compute: FastAPI on IBM Cloud Code Engine
- AI: watsonx.ai Granite for summarization and classification
- Storage: IBM Cloud Object Storage for PDFs; Postgres for app data
- Scheduling: Code Engine cron or Cloud Functions for hourly ingest

## Repository structure

```
.
├─ README.md
├─ frontend/              # Vite + React UI
│  ├─ package.json
│  └─ ...
```

## Frontend quickstart

```bash
# from repository root
cd frontend
npm install
npm run dev
```

- Dev server: http://localhost:5173
- Build/preview:
```bash
npm run build
npm run preview
```

## Use case summary

The bot acts as an early‑warning system:
- Detects relevant news
- Flags and summarizes it
- Provides context (why it matters)
- Delivers draft text for human review

**Business case**: Saves analysts’ time, increases client responsiveness, and strengthens the team’s role as trusted interpreter.

## IBM resources

- IBMid registration: https://www.ibm.com/docs/en/controller/11.1.1?topic=authentication-ibmid-registration
- watsonx Orchestrate: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate
- Cloud Pak for Data learning path: https://developer.ibm.com/learningpaths/get-started-watson-studio/
