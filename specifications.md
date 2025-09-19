Tiny taxonomy (v1)

central_bank, ceo_exit, cfo_exit, mna, earnings_surprise, guidance_change, dividend_change, rating_change, regulatory_sanction, geopolitics, other

Output fields (what every item must have)

id, published_at, source, url, headline, body_text, tickers[], event_type, sectors[], regions[], confidence (0–1), urgency (low/med/high), why_it_matters

Write this into your README so everyone codes to the same target.

1) Make your ingestion “analyst-aware” before LLMs

Add quick, deterministic signals so the model starts with better inputs.

A) EDGAR → event_type + urgency (rule-based)

Use the 8-K item codes:

Item 5.02 → ceo_exit (high); 2.02 → earnings_surprise (high); 1.01 → mna/material_agreement (high); 4.02 → non-reliance (high); 5.03 → bylaws/fiscal_year_change (low); 7.01 → reg_fd (med); 3.02 → unregistered_sale (med); 8.01 → other_events (med)

(You can drop in the helper I gave earlier; it fills event_type, urgency, and keeps the found item codes in entities.)

B) Show tickers for EDGAR items

Parse CIK from the SEC URL and map to tickers with a small JSON (start with the names you care about; expand later).

C) Compute a confidence score

Simple heuristic: source type + event_type + urgency (+ watchlist boost). Save it in confidence so the UI can sort.

2) Add the LLMs (Watsonx.ai Granite) where they add value

Now that every record has sane defaults:

(a) Classifier (fill gaps + sectors/asset classes)

Few-shot prompt (Granite) to:

confirm event_type (or set when null),

infer sectors[], asset_classes, and extra tickers mentioned in text,

return a confidence (0–1).

(b) Summarizer (W&P tone)

Prompt to produce:

3 crisp bullets + “Why it matters” (1 line, CIO-style),

include tickers and key numbers,

be neutral, no hype.

(c) Draft client note

3–4 sentences: action → implications → next watchpoint; editable in the UI.

Wire these as functions in a new app/nlp.py (e.g., llm_classify(item), llm_summarize(item)), and call them from /classify_summarize or directly inside /ingest behind a ?with_llm=true query flag.

3) Orchestrate the flow (Watsonx Orchestrate)

A simple flow:

Poll /ingest

Classify & summarize (for new items only)

Route: if confidence ≥ 0.75 → send alert (Slack/Teams); else → review queue

Await human approve/edit → persist draft_note

This is your “agentic AI” story.

4) UI (1 page, Streamlit or React)

Columns:

Feed (time-ordered, deduped, severity chips)

AI view (3 bullets + why-it-matters + confidence, event_type)

Draft (editable; copy button; save)

Filters: asset class, watchlist tickers, min confidence.

5) Evaluation (show this in judging)

Build a gold set of 100 items (Relevant? Which event_type?).

Report precision@20 and a tiny alert latency metric.

Show a before/after “time-to-blurb” (manual vs. your tool).

Concrete next steps in your repo

Add the rule-based classifier (EDGAR item→event/urgency) and CIK→ticker map.

Add confidence scoring and a ?min_score= filter to /ingest.

Create app/nlp.py with two stubs:

llm_classify(item) -> event_type, sectors, tickers(+), confidence

llm_summarize(item) -> bullets[], why_it_matters, draft_note

Add a /process endpoint that:

pulls from /ingest,

runs the two LLM calls,

returns analyst-ready items.

(Optional) Add a watchlist.json and boost confidence when a ticker/CIK matches.

If you want, tell me 5–10 tickers you care about (e.g., FDX, KR, JPM, MSFT, AAPL) and I’ll give you a ready-made company_tickers.json and a minimal watchlist.json, plus the exact Granite prompts wired for app/nlp.py.