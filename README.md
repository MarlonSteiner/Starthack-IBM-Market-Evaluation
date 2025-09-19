# Team 5 - Start Hack 2025
## Overview

Welcome to the MarketPulse Lite repository for Start Hack 2025. Our goal is to build a simple platform that detects market-moving news, summarizes it into three clear lines, and compiles a weekly client brief. 🧑🏻‍💻👩🏻‍💻👨🏽‍💻👩🏼‍💻


![stonk gif](https://github.com/user-attachments/assets/c8d5328d-1c0a-4f7c-aff4-85e8d8f539bb)


One-liner
Detect, summarize, and package market-moving news for client-ready briefs. It helps IBM teams deliver faster, smarter pitches.

Demo GIF or screenshot
Drop a short screen recording here

![demo](./docs/demo.gif)

## Tech Stack
Backend — API and data

FastAPI - lightweight Python API

SQLAlchemy with SQLite for local dev and PostgreSQL for IBM Cloud

APScheduler - hourly ingest job

httpx and feedparser - fetch RSS and APIs

WeasyPrint - render the Weekly Brief to PDF

watsonx.ai Granite - summarize and classify news (JSON contract)

IBM Cloud Object Storage - store PDFs in the cloud

Frontend — UI and UX

React (Vite) - fast dev server

Tailwind CSS - clean, modern styling

Axios - API calls to the backend

Cloud and DevEx

IBM Cloud Code Engine - deploy the FastAPI backend

IBM Cloud Functions or Code Engine cron - run hourly ingestion

GitHub - version control and collaboration

GitHub Actions - optional CI

Docker - optional containerized deploy

## Purpose and Goals

Pull high-signal financial news and policy updates each hour

Auto-draft three short lines per item

Was passiert ist

Warum es zählt

Portfolio-Impact

Keep a human in the loop for approval

Compile a Weekly Brief showing only items from the last 7 days

Export a clean PDF with editorial cutoff, authors, imprint, and disclaimer

## How to Get Started
1) Clone the repository
git clone https://github.com/YourOrg/marketpulse-lite.git
cd marketpulse-lite

2) Backend setup

Create and activate a virtual environment:

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate


Install dependencies:

pip install -r backend/requirements.txt


Create .env at repo root:

# watsonx.ai
WX_API_KEY=your_wx_api_key
WX_URL=https://eu-de.ml.cloud.ibm.com
WX_PROJECT_ID=your_project_id
WX_MODEL_ID=ibm/granite-13b-instruct-v2

# Optional market news APIs
POLYGON_API_KEY=
FINNHUB_API_KEY=

# Frontend origin for local CORS
FRONTEND_ORIGIN=http://localhost:5173

# IBM Cloud Object Storage (optional)
COS_ENDPOINT=https://s3.eu-de.cloud-object-storage.appdomain.cloud
COS_API_KEY_ID=
COS_INSTANCE_CRN=
COS_BUCKET=marketpulse-briefs


Run the API:

cd backend
uvicorn app:app --reload --port 8000


Trigger an immediate ingest for demo data:

curl -X POST http://localhost:8000/ingest/now


List recent articles in the last 7 days:

open http://localhost:8000/articles?days=7


Generate a Weekly Brief PDF:

open http://localhost:8000/brief.pdf

3) Frontend setup
cd ../frontend
npm install
npm run dev


Open the URL Vite prints to the console.

Project Structure
marketpulse-lite/
  backend/
    app.py               # FastAPI routes
    classify_wx.py       # watsonx.ai summarizer and classifier
    classify.py          # fallback summarizer (local or OpenAI)
    ingest.py            # hourly fetching logic
    models.py            # SQLAlchemy models
    db.py                # DB engine and session
    pdf.py               # WeasyPrint PDF renderer
    settings.py          # config and ENV reads
    requirements.txt
  frontend/
    src/
      App.jsx
      api.js
      components/
        NewsCard.jsx
        WeeklyBrief.jsx
    package.json
  docs/
    demo.gif             # place your GIF here
  .env                   # local only

Use Case
Who is the user

Primary - Relationship Manager or Investment Advisor in Switzerland
Goal: brief clients with recent, credible insights and share a Weekly Brief.

Secondary - Research Analyst or PM
Goal: curate incoming items, edit tone, approve content, ensure compliance.

Tertiary - Client (HNW or institutional)
Goal: receive a concise weekly perspective with clear implications.

Key workflows

Hourly update fetches and classifies items

Analyst edits and approves

Advisor copies LinkedIn text or shares the PDF

Weekly Brief compiles only approved items from the last 7 days

PDF is stored in IBM Cloud Object Storage and shared with a link

Features at a Glance

Today and Weekly tabs with clean cards

Three short lines per item with asset and region tags

Approve and Copy LinkedIn post actions

Weekly Brief PDF with editorial cutoff and legal footer

IBM Cloud ready: watsonx.ai, Code Engine, Object Storage

IBM Cloud Deployment (quick path)
Code Engine app

Build a Docker image of the backend and push to a registry

Create a Code Engine app from the image

Set environment variables from your .env

Expose the service URL

Hourly cron

Create a cron subscription that calls POST /ingest/cron every hour

Object Storage

Create a COS bucket for PDFs

Set keys and instance CRN as env vars

The backend can upload the weekly PDF and return a pre-signed URL

## Branching Strategy

We use four main branches in this repository:

1. **API** - API development

2. **FRONTEND** - UI and UX

3. **BACKEND** - data and services

4. **DRAFT** - experiments and collaborative drafts

Working with branches

Switch to a branch:
```bash
git checkout <branch-name>
```

Create a new branch:
```bash
git checkout -b <new-branch-name>
```

Pull latest changes:
```bash
git pull origin <branch-name>
```

Push changes:
```bash
git add .
git commit -m "Your commit message"
git push origin <branch-name>
```

Merge changes:
```bash
git checkout <target-branch>
git merge <source-branch>
```

Delete a local branch after merge:
```bash
git branch -d <branch-name>
```
Roadmap

 Source coverage presets for equities, rates, FX, gold, policy

 Simple confidence score on summaries

 German and English output toggles

 PDF theming per client

 LinkedIn API integration for approved posts

 Postgres on IBM Cloud with migrations

License

MIT or Apache 2.0
Add your chosen license here
