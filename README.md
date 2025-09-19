MarketPulse Lite

One-liner:
A prototype tool that detects market-moving financial news, summarizes it, and tailors insights to specific bank clients. It helps IBM teams deliver faster, smarter pitches.

Alternatives if you want shorter:

Detect, summarize, and package market-moving news for client-ready briefs.

Hourly news in, three-line insights out, weekly brief ready to send.

Use case
Who is the user

Primary: Relationship Manager or Investment Advisor at a Swiss wealth or asset manager
Goal: brief clients with credible, recent insights and share a weekly “Current Perspectives” summary with minimal effort.

Secondary: Research Analyst or PM
Goal: curate incoming items, edit tone, approve content, ensure compliance.

Tertiary: End client (HNW or institutional)
Goal: receive a concise weekly perspective that explains what happened, why it matters, and the portfolio impact.

Problem

Advisors need timely, trustworthy talking points without trawling dozens of sources. Weekly summaries take too long to prepare and are inconsistent in tone.

Solution

Ingest market news hourly from high-signal sources

Classify relevance to assets and regions

Auto-draft three short lines: What happened, Why it matters, Portfolio impact

Human approves

Compile a weekly PDF showing only items from the last 7 days

Key workflows

Hourly update: system pulls feeds and APIs, dedupes, classifies, drafts three lines.

Curation: analyst reviews the queue, tweaks text, clicks Approve.

Advisor view: Today and Weekly tabs. Copy LinkedIn text or share the PDF.

Weekly brief: compile only approved items from the last 7 days.

Publish: store PDF in IBM Cloud Object Storage and share a pre-signed link.

Data the user should know

For advisors: last refresh time, 7-day coverage window, source and link, publish time, three-line summary, asset and region tags, simple impact chip (up, down, neutral), editorial cutoff, legal disclaimer, quick actions.

For analysts: ingestion status, relevance score, editable fields (title, lead, bullets, tags), approval state with timestamp, error states.

For clients: weekly PDF with week range, approved cards, editorial cutoff, imprint and disclaimer.

Non-functional requirements

Freshness (hourly), reliability (graceful degradation on source failure), auditability (who approved what and when), compliance (sources, cutoff, disclaimer), localization (DE and EN), minimal PII.

IBM Cloud footprint

Compute: FastAPI on IBM Cloud Code Engine

AI: watsonx.ai Granite for summarize and classify

Storage: IBM Cloud Object Storage for PDFs; Postgres for app data

Scheduling: Code Engine cron or Cloud Functions for hourly ingest

Definition of done (MVP)

Only items from the last 7 days are visible and timestamped with last refresh

Each item has title, source, link, three short lines, tags, and impact

Approve flow works end to end

Weekly PDF includes editorial cutoff, authors, imprint, and disclaimer

Deployed on IBM Cloud and accessible to judges

One real example formatted to match “Current Perspectives” tone
