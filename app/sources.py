import httpx, asyncio, feedparser, urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any
from .config import MARKETAUX_API_TOKEN, NEWSAPI_API_KEY, QUERY_TERMS, NEWSAPI_DOMAINS, USER_AGENT, REQUEST_TIMEOUT
from .normalize import normalize_edgar, normalize_marketaux, normalize_newsapi

HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json, text/xml, application/xml"}

# --- SEC EDGAR RSS (Atom) ---
# We poll recent 8-K / 10-Q / 10-K filings via Atom feeds.
SEC_ATOM_ENDPOINTS = [
    # Latest 8-K filings
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&count=100&owner=exclude&output=atom",
    # Latest 10-Q
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-Q&count=100&owner=exclude&output=atom",
    # Latest 10-K
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&count=100&owner=exclude&output=atom",
]

async def fetch_edgar() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        for url in SEC_ATOM_ENDPOINTS:
            try:
                r = await client.get(url)
                r.raise_for_status()
                feed = feedparser.parse(r.text)
                for entry in feed.entries:
                    items.append(normalize_edgar(entry))
            except Exception:
                continue
    return items

# --- MarketAux ---
# Documentation: https://www.marketaux.com/documentation
# Example endpoint: /v1/news/all
async def fetch_marketaux() -> List[Dict[str, Any]]:
    if not MARKETAUX_API_TOKEN:
        return []
    q = " OR ".join([f'\"{t}\"' for t in QUERY_TERMS]) if QUERY_TERMS else "markets"
    params = {
        "api_token": MARKETAUX_API_TOKEN,
        "language": "en",
        "filter_entities": "true",
        "published_after": (datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"),
        "limit": 50,
        "search": q,
    }
    url = "https://api.marketaux.com/v1/news/all?" + urllib.parse.urlencode(params)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=HEADERS) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            articles = data.get("data", [])
            return [normalize_marketaux(a) for a in articles]
        except Exception:
            return []

# --- NewsAPI ---
# Documentation: https://newsapi.org/docs/endpoints/everything
async def fetch_newsapi() -> List[Dict[str, Any]]:
    if not NEWSAPI_API_KEY:
        return []
    q = " OR ".join([f'"{t}"' for t in QUERY_TERMS]) if QUERY_TERMS else "markets"
    params = {
        "q": q,
        "language": "en",
        "pageSize": 50,
        "sortBy": "publishedAt",
        "apiKey": NEWSAPI_API_KEY,
    }
    if NEWSAPI_DOMAINS:
        params["domains"] = NEWSAPI_DOMAINS
    url = "https://newsapi.org/v2/everything?" + urllib.parse.urlencode(params)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=HEADERS) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            articles = data.get("articles", [])
            return [normalize_newsapi(a) for a in articles]
        except Exception:
            return []
