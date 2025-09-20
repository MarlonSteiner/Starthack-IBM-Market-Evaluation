from fastapi import FastAPI
from typing import Dict, Any
import asyncio
from .sources import fetch_edgar, fetch_marketaux, fetch_newsapi
from .dedupe import dedupe
from .score import score_item

app = FastAPI(title="Financial News Ingestor", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(min_score: float = 0.0) -> Dict[str, Any]:
    # Run all sources concurrently
    edgar_task = asyncio.create_task(fetch_edgar())
    marketaux_task = asyncio.create_task(fetch_marketaux())
    newsapi_task = asyncio.create_task(fetch_newsapi())
    edgar, marketaux, newsapi = await asyncio.gather(edgar_task, marketaux_task, newsapi_task)

    all_items = edgar + marketaux + newsapi
    all_items = dedupe(all_items)

    # score & filter
    for it in all_items:
        it["confidence"] = score_item(it)
    filtered = [it for it in all_items if it.get("confidence", 0) >= min_score]

    return {
        "counts": {
            "sec_edgar": len(edgar),
            "marketaux": len(marketaux),
            "newsapi": len(newsapi),
            "total_deduped": len(all_items),
            "relevant": len(filtered),
        },
        "items": filtered,
    }
