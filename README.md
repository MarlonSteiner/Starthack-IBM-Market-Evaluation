# Financial News Ingestor (EDGAR + MarketAux + NewsAPI)

A minimal FastAPI service that exposes a single `/ingest` endpoint to pull fresh items from:
- **SEC EDGAR Atom RSS** (8-K, 10-Q, 10-K)
- **MarketAux** news API (requires API token)
- **NewsAPI** (requires API key)

All results are normalized to a unified schema and deduplicated.

## Quickstart

1) Create a virtual env and install deps:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Copy env example and add your keys:
```bash
cp .env.example .env
# Fill MARKETAUX_API_TOKEN and NEWSAPI_API_KEY
```

3) Run the API:
```bash
./run.sh
# or: uvicorn app.main:app --reload
```

4) Call the endpoint:
```bash
curl -X POST http://localhost:8000/ingest | jq
```

### Notes

- **SEC feeds** don’t require keys and are high-signal for market-moving filings.
- **MarketAux** and **NewsAPI** are polled with a query built from `QUERY_TERMS` in `.env`.
- Output JSON fields:
```
id, published_at, source, url, headline, body_text, tickers[], entities[],
event_type, regions[], sectors[], confidence, urgency, why_it_matters, draft_note, hash
```
- This service focuses on *ingestion only*. Next steps: push to a queue/DB, LLM classify/summarize, and alerting.

## Customization

- Edit `QUERY_TERMS` in `.env` (e.g., "Fed,ECB,rate hike,CEO,resigns,merger,earnings").
- Restrict NewsAPI to trusted `NEWSAPI_DOMAINS` for quality control.
- Add more sources by creating a new `fetch_*` function in `app/sources.py` and mapping it through `normalize_*` helper.

## Legal & Operational

- Respect each API’s terms and rate limits.
- For scraping sites without APIs, check robots.txt and ToS, and add caching/backoff.
