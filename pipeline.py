# pipeline.py
# ---------------------------------------------
# News ingestion + normalization + heuristics + scoring.
# Pure Python module (no UI code, no notebook magics).
# ---------------------------------------------

from __future__ import annotations

import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from watson_helper import _wx_gen
# Third-party deps (install in your venv:  pip install httpx==0.27.2 feedparser==6.0.11 pandas==2.2.2)
try:
    import httpx
    import feedparser
except Exception as e:
    raise ImportError(
        "Required packages not found. Please run:\n"
        "  pip install httpx==0.27.2 feedparser==6.0.11\n"
        f"Import error was: {e}"
    )

# -------------------- Config (via env) --------------------

MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "")
NEWSAPI_API_KEY     = os.getenv("NEWSAPI_API_KEY", "")

QUERY_TERMS     = [q.strip() for q in os.getenv(
    "QUERY_TERMS",
    "Fed,ECB,earnings,merger,CEO,resigns,guidance,dividend,downgrade,upgrade"
).split(",") if q.strip()]

NEWSAPI_DOMAINS = os.getenv(
    "NEWSAPI_DOMAINS",
    "reuters.com,ft.com,wsj.com,bloomberg.com,cnbc.com,marketwatch.com"
)

USER_AGENT = "MarketNewsMonitor/1.0"
TIMEOUT    = 20.0
HEADERS = {
    "User-Agent": "MarketNewsMonitor/1.0 (contact: youremail@example.com)",
    "Accept": "application/json, text/xml, application/xml",
}


SEC_ATOM = [
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&count=100&owner=exclude&output=atom",
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-Q&count=100&owner=exclude&output=atom",
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&count=100&owner=exclude&output=atom",
]

# A light watchlist (override with WATCHLIST env var)
WATCHLIST = {s.strip().upper() for s in os.getenv(
    "WATCHLIST", "FDX,NVDA,INTC,CRWD,AMD,AAPL,MSFT,GOOGL,AMZN,TSLA"
).split(",") if s.strip()}

# -------------------- Normalization helpers --------------------

_HTML_TAGS = re.compile(r"<[^<]+?>")

def strip_html(s: str | None) -> str:
    return "" if not s else _HTML_TAGS.sub("", s).strip()

def to_rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def safe_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        if p:
            h.update(p.encode("utf-8", "ignore"))
    return h.hexdigest()[:16]

def base_item(source: str, url: str, headline: str, body: str, published: datetime) -> Dict[str, Any]:
    _id = safe_hash(source, url, headline)
    return {
        "id": _id,
        "published_at": to_rfc3339(published),
        "source": source or "",
        "url": url or "",
        "headline": (headline or "").strip(),
        "body_text": strip_html(body)[:8000],
        "tickers": [],
        "entities": [],
        "event_type": None,
        "asset_classes": [],
        "sectors": [],
        "regions": [],
        "confidence": None,
        "urgency": None,
        "why_it_matters": None,
        "draft_note": None,
        "hash": _id,
    }

# -------------------- EDGAR: Item → event/urgency --------------------

ITEM_MAP: Dict[str, Tuple[str, str]] = {
    "1.01": ("mna", "high"),
    "1.02": ("termination_material_agreement", "high"),
    "1.03": ("bankruptcy", "high"),
    "2.01": ("mna", "high"),
    "2.02": ("earnings_surprise", "high"),
    "2.03": ("new_debt_obligation", "high"),
    "2.04": ("triggering_event_debt", "high"),
    "2.05": ("impairment", "high"),
    "2.06": ("restructuring_costs", "med"),
    "3.02": ("unregistered_sale", "med"),
    "3.03": ("security_holder_rights_change", "med"),
    "4.01": ("auditor_change", "high"),
    "4.02": ("non_reliance", "high"),
    "5.02": ("ceo_exit", "high"),
    "5.03": ("other_events", "low"),
    "5.07": ("shareholder_vote", "low"),
    "7.01": ("reg_fd", "med"),
    "8.01": ("other_events", "med"),
}
ITEM_REGEX = re.compile(r"Item\s+(\d+\.\d+)", re.IGNORECASE)

def classify_edgar_from_summary(summary: str):
    if not summary:
        return None, None, []
    found = ITEM_REGEX.findall(summary)
    event_type = urgency = None
    if found:
        pr = {"high": 3, "med": 2, "low": 1}
        best = (0, None, None)
        for code in found:
            et, urg = ITEM_MAP.get(code, ("other_events", "low"))
            score = pr[urg]
            if score > best[0]:
                best = (score, et, urg)
        _, event_type, urgency = best
    return event_type, urgency, found

# -------------------- Keyword pre-classifier --------------------

KW_MAP = {
    "ceo_exit":          ["ceo resigns", "steps down", "resigns as ceo", "appointed ceo", "names ceo"],
    "mna":               ["acquires", "acquisition", "to buy", "merger", "merges with", "takeover"],
    "earnings_surprise": ["beats estimates", "misses estimates", "tops forecasts", "cuts outlook", "raises outlook", "guidance"],
    "rating_change":     ["downgrades", "upgrades", "cut to", "raised to", "initiated at"],
    "geopolitics":       ["sanction", "tariff", "strike", "protest", "conflict", "attack"],
    "dividend_change":   ["dividend", "buyback", "repurchase"],
    "bankruptcy":        ["bankruptcy", "chapter 11"],
}

def preclassify_keywords(item: Dict[str, Any]) -> None:
    if item.get("source", "").lower() == "sec_edgar":
        return
    h = (item.get("headline") or "").lower()
    for et, words in KW_MAP.items():
        if any(w in h for w in words):
            item["event_type"] = item.get("event_type") or et
            item["urgency"] = item.get("urgency") or ("high" if et in {"ceo_exit","mna","earnings_surprise","bankruptcy"} else "med")
            return

# -------------------- Ticker enrichment --------------------

_TICK_IN_PARENS = re.compile(r"\((?P<t>[A-Z]{1,5})\)")

STOP_TICKERS = {
    "A","AI","ALL","ANY","ARE","AS","AT","BE","CEO","EPS","ETF","FOR","FY","GO","IPO","IS","NAV",
    "OF","OK","ON","OR","PC","PER","Q1","Q2","Q3","Q4","RFK","THE","TO","UP","US","USD","VAT","YOY","WWW"
}

VALID_TICKERS = {
    "FDX","CRWD","NVDA","INTC","ORCL","ROO","DRI","AXP","HYMTF","NESN.SW","NVO",
    "AAPL","MSFT","GOOGL","AMZN","META","TSLA","JPM","BAC","GS","MS","NFLX","DIS"
}

NAME_TICKER = {
    "fedex": "FDX",
    "crowdstrike": "CRWD",
    "nvidia": "NVDA",
    "intel": "INTC",
    "oracle": "ORCL",
    "deliveroo": "ROO",
    "darden restaurants": "DRI",
    "american express": "AXP",
    "hyundai": "HYMTF",
    "nestlé": "NESN.SW",
    "novo nordisk": "NVO",
}

def enrich_tickers(item: Dict[str, Any]) -> None:
    if item.get("tickers"):
        return
    h = (item.get("headline") or "").lower()

    # 1) company-name hits
    name_hits = {sym for name, sym in NAME_TICKER.items() if name in h}

    # 2) (TICKER) pattern
    paren_hits = {m.group("t") for m in _TICK_IN_PARENS.finditer(item.get("headline", ""))}
    paren_hits = {t for t in paren_hits if t in VALID_TICKERS}

    # 3) URL slug hits (only if exact match with VALID_TICKERS)
    url = (item.get("url") or "").lower()
    slug_hits = {part.upper() for part in url.split("-") if part.upper() in VALID_TICKERS}

    found = sorted(name_hits | paren_hits | slug_hits)
    if found:
        item["tickers"] = found

# -------------------- Dedupe, scoring, severity --------------------

def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen, out = set(), []
    for it in items:
        key = safe_hash(it.get("source",""), it.get("url",""), it.get("headline",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def score_item(it: Dict[str, Any]) -> float:
    s = 0.0
    src = (it.get("source") or "").lower()
    et  = (it.get("event_type") or "other_events")
    urg = (it.get("urgency") or "low")
    head = (it.get("headline") or "").lower()

    # Source weighting
    if src == "sec_edgar":
        if it["headline"].startswith("8-K"): s += 0.6
        elif it["headline"].startswith("10-Q"): s += 0.3
        elif it["headline"].startswith("10-K"): s += 0.25
    elif any(d in src for d in ["reuters","bloomberg","wsj","ft","cnbc","marketwatch"]):
        s += 0.35
    else:
        s += 0.25

    # Event/urgency
    high_events = {"ceo_exit","bankruptcy","non_reliance","earnings_surprise","mna"}
    med_events  = {"guidance_change","rating_change","reg_fd","regulatory_sanction","geopolitics","unregistered_sale","dividend_change"}
    if et in high_events: s += 0.35
    elif et in med_events: s += 0.2
    if urg == "high": s += 0.15
    elif urg == "med": s += 0.05

    # Keyword nudge
    for kw in ["guidance","resigns","resignation","appointed","impairment","non-reliance","acquisition","merger","downgrade","upgrade","beats","misses"]:
        if kw in head:
            s += 0.05

    # Ticker + watchlist boost
    tickers = set(it.get("tickers") or [])
    if tickers:
        s += 0.05
        if WATCHLIST & tickers:
            s += 0.15

    return min(s, 1.0)

def severity(score: float) -> str:
    if score >= 0.80: return "high"
    if score >= 0.55: return "med"
    return "low"

# -------------------- LLM scaffolding (safe fallbacks) --------------------

def llm_classify(item: dict) -> dict:
    """Return event_type, tickers, sectors, asset_classes, regions, confidence (0-1)."""
    title = item.get("headline") or ""
    body  = (item.get("body_text") or "")[:1500]
    hints = ", ".join(item.get("tickers") or [])
    prompt = f"""
You are a financial news classifier for an analyst triage tool.

Return STRICT JSON with keys:
event_type: one of [central_bank, earnings_surprise, ceo_exit, mna, rating_change, dividend_change, bankruptcy, regulatory, sector_shock, other_events]
tickers: array of strings (uppercase tickers)
sectors: array of strings (GICS-like)
asset_classes: array subset of [Equity, Rates, Credit, Commodities, FX]
regions: array subset of [US, EU, CH, UK, JP, EM]
confidence: float 0..1 (your certainty about event_type)

TITLE: {title}
BODY: {body}
TICKER_HINTS: {hints or "n/a"}

Return ONLY JSON, no prose.
""".strip()

    raw = _wx_gen(prompt)
    # Safe fallback default
    out = {"event_type":"other_events","tickers":item.get("tickers") or [],
           "sectors":[], "asset_classes":["Equity"], "regions":["US"], "confidence":0.55}
    if not raw:
        return out
    # Try to parse JSON
    try:
        j = json.loads(raw.strip().splitlines()[-1])
        # merge defensively
        for k in out.keys():
            if k in j and j[k] is not None:
                out[k] = j[k]
        # normalize types
        out["tickers"] = [str(t).upper() for t in (out.get("tickers") or [])]
        out["confidence"] = float(out.get("confidence") or 0.55)
        return out
    except Exception:
        return out

MAX_CLASSIFY  = 20   # cap LLM classify for testing
MAX_SUMMARIZE = 20   # cap LLM summarize for testing

def llm_summarize(item: dict) -> dict:
    title = item.get("headline") or ""
    body  = (item.get("body_text") or "")[:1500]
    event = item.get("event_type") or "other_events"
    tick  = ", ".join(item.get("tickers") or [])
    prompt = f"""
You draft analyst-ready cards in W&P's neutral, empirical tone.

Return STRICT JSON with keys:
headline: string <= 90 chars
bullets: array of 3 strings (concise)
why_it_matters: string <= 40 words

Constraints:
- No advice or speculation; keep to verifiable facts + concise context.
- Use cautious language when uncertainty is high.
- If information is insufficient, say so briefly.

INPUT
TITLE: {title}
BODY: {body}
EVENT: {event}
TICKERS: {tick or "n/a"}

Return ONLY JSON, no prose.
""".strip()

    raw = _wx_gen(prompt)
    # Fallback
    h = title.strip()
    fallback = {
        "headline": h[:90],
        "bullets": [
            (h[:90] + "."),
            f"Event: {event} · Severity: {item.get('severity','low')}",
            f"Tickers: {tick or 'n/a'} · Source: {item.get('source')}"
        ],
        "why_it_matters": "Potential impact on covered names and sector sentiment; confirm details as they develop."
    }
    if not raw:
        return fallback
    try:
        j = json.loads(raw.strip().splitlines()[-1])
        # basic validation
        if not isinstance(j.get("bullets"), list) or len(j["bullets"]) < 3:
            j["bullets"] = fallback["bullets"]
        if not j.get("headline"):
            j["headline"] = fallback["headline"]
        if not j.get("why_it_matters"):
            j["why_it_matters"] = fallback["why_it_matters"]
        return j
    except Exception:
        return fallback


# -------------------- Fetchers --------------------

def fetch_edgar() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        for url in SEC_ATOM:
            try:
                r = client.get(url)
                r.raise_for_status()
                feed = feedparser.parse(r.text)
                for e in feed.entries:
                    link = e.get("link") or ""
                    title = e.get("title","SEC Filing")
                    summary = e.get("summary","")
                    published = e.get("published_parsed")
                    if published:
                        dt = datetime(*published[:6], tzinfo=timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)
                    itm = base_item("sec_edgar", link, title, summary, dt)
                    et, urg, codes = classify_edgar_from_summary(summary)
                    itm["event_type"] = et
                    itm["urgency"] = urg
                    itm["entities"] = codes
                    items.append(itm)
            except Exception:
                continue
    return items

def fetch_marketaux() -> List[Dict[str, Any]]:
    if not MARKETAUX_API_TOKEN:
        return []
    q = " OR ".join([f'"{t}"' for t in QUERY_TERMS]) or "markets"
    params = {
        "api_token": MARKETAUX_API_TOKEN,
        "language":"en",
        "filter_entities":"true",
        "published_after": datetime.now(timezone.utc).replace(microsecond=0).isoformat()+"Z",
        "limit": 50,
        "search": q
    }
    url = "https://api.marketaux.com/v1/news/all"
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json().get("data", [])
    except Exception:
        return []
    out = []
    for a in data:
        _url = a.get("url","")
        title = a.get("title","MarketAux")
        desc  = a.get("description","") or a.get("snippet","")
        ts    = a.get("published_at") or a.get("updated_at") or ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
        itm = base_item("marketaux", _url, title, desc, dt)
        syms = a.get("symbols") or a.get("entities") or []
        itm["tickers"] = [s.get("symbol") if isinstance(s,dict) else s for s in syms]
        out.append(itm)
    return out

def fetch_newsapi() -> List[Dict[str, Any]]:
    if not NEWSAPI_API_KEY:
        return []
    q = " OR ".join([f'"{t}"' for t in QUERY_TERMS]) or "markets"
    params = {
        "q": q,
        "language":"en",
        "pageSize": 50,
        "sortBy":"publishedAt",
        "apiKey": NEWSAPI_API_KEY,
        "domains": NEWSAPI_DOMAINS
    }
    url = "https://newsapi.org/v2/everything"
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            articles = r.json().get("articles", [])
    except Exception:
        return []
    out = []
    for a in articles:
        _url   = a.get("url","")
        title  = a.get("title","NewsAPI")
        desc   = a.get("description","") or ""
        content = a.get("content","") or ""
        combined = (desc + "\n\n" + content).strip()
        ts = a.get("publishedAt") or ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
        source_name = (a.get("source") or {}).get("name") or "newsapi"
        itm = base_item(source_name, _url, title, combined, dt)
        out.append(itm)
    return out

# -------------------- Main pipeline --------------------
import time
from datetime import datetime

def _ts():
    return datetime.now().strftime("%H:%M:%S")

def process(min_score: float = 0.6, with_llm: bool = True) -> Dict[str, Any]:
    t0 = time.perf_counter()
    print(f"[{_ts()}] [pipeline] start (min_score={min_score}, with_llm={with_llm})", flush=True)

    print(f"[{_ts()}] [pipeline] fetching sources…", flush=True)
    # edgar     = fetch_edgar()
    marketaux = fetch_marketaux()
    newsapi   = fetch_newsapi()
    """print(f"[{_ts()}] [pipeline] fetched counts → edgar={len(edgar)} "
          f"marketaux={len(marketaux)} newsapi={len(newsapi)}", flush=True)"""

    #all_items = dedupe(edgar + marketaux + newsapi)
    all_items = dedupe(marketaux + newsapi)
    print(f"[{_ts()}] [pipeline] after dedupe: total={len(all_items)}", flush=True)
    
    # --- TEST MODE: keep only the first 20 for LLM work ---
    subset_for_llm = all_items[:MAX_CLASSIFY]
    print(f"[pipeline] limiting LLM classify to first {len(subset_for_llm)} items", flush=True)

    # --- Enrich + keyword preclassify BEFORE scoring ---
    print(f"[{_ts()}] [pipeline] enrich + preclassify…", flush=True)
    for idx, it in enumerate(all_items, 1):
        try:
            enrich_tickers(it)
            preclassify_keywords(it)
        except Exception as e:
            print(f"[{_ts()}] [warn] enrich/preclassify failed on item#{idx}: {e}", flush=True)

    # --- Optional: LLM classify BEFORE filtering (to influence scoring) ---
    if with_llm:
        print(f"[pipeline] LLM classify on {len(subset_for_llm)} items…", flush=True)
        for i, it in enumerate(subset_for_llm, 1):
            cls = llm_classify(it)
            it["event_type"]    = it.get("event_type") or cls.get("event_type")
            it["tickers"]       = list({*(it.get("tickers") or []), *cls.get("tickers", [])})
            it["sectors"]       = it.get("sectors") or cls.get("sectors") or []
            it["asset_classes"] = it.get("asset_classes") or cls.get("asset_classes") or []
            it["regions"]       = it.get("regions") or cls.get("regions") or []
            it["_llm_conf"]     = float(cls.get("confidence") or 0.5)
            if i % 5 == 0:
                print(f"  …classified {i}/{len(subset_for_llm)}", flush=True)



    # --- Score + severity ---
    print(f"[{_ts()}] [pipeline] scoring + severity…", flush=True)
    for it in all_items:
        base = score_item(it)
        if "_llm_conf" in it:
            base = max(base, min(1.0, 0.6*base + 0.5*it["_llm_conf"]))  # simple blend
        it["confidence"] = base
        it["severity"]   = severity(base)

    # --- Filter AFTER blending ---
    filtered = [it for it in all_items if it["confidence"] >= min_score]
    print(f"[{_ts()}] [pipeline] filtered relevant: {len(filtered)} (threshold={min_score})", flush=True)
    
    # Sort by confidence so we summarize the most relevant first
    filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    to_summarize = filtered[:MAX_SUMMARIZE]
    print(f"[pipeline] LLM summarize on {len(to_summarize)} of {len(filtered)} items…", flush=True)

    if with_llm:
        for i, it in enumerate(to_summarize, 1):
            summ = llm_summarize(it)
            it["bullets"]        = summ.get("bullets", [])
            it["why_it_matters"] = summ.get("why_it_matters", "Potential portfolio impact; confirm details.")
            it["draft_note"]     = summ.get("draft_note", f"{it.get('headline','')} — {it.get('url','')}")
            if i % 5 == 0:
                print(f"  …summarized {i}/{len(to_summarize)}", flush=True)


    # --- Optional: LLM summarize ONLY on filtered items ---
    """f with_llm and filtered:
        print(f"[{_ts()}] [pipeline] LLM summarize on {len(filtered)} items…", flush=True)
        for i, it in enumerate(filtered, 1):
            if i % 10 == 0:
                print(f"[{_ts()}]   …summarized {i}/{len(filtered)}", flush=True)
            try:
                cls = llm_classify(it)  # quick refresh in case event_type was still None
                it["event_type"]    = it.get("event_type") or cls.get("event_type")
                it["tickers"]       = list({*(it.get("tickers") or []), *cls.get("tickers",[])})
                it["sectors"]       = cls.get("sectors") or it.get("sectors") or []
                it["asset_classes"] = cls.get("asset_classes") or it.get("asset_classes") or []
                it["regions"]       = cls.get("regions") or it.get("regions") or []
                if isinstance(cls.get("confidence"), (int, float)):
                    it["confidence"] = max(it["confidence"], float(cls["confidence"]))

                summ = llm_summarize(it)
                it["bullets"]        = summ.get("bullets", [])
                it["why_it_matters"] = summ.get("why_it_matters", "Potential portfolio impact; confirm details.")
                it["draft_note"]     = summ.get("draft_note", f"{it.get('headline','')} — {it.get('url','')}")
            except Exception as e:
                print(f"[{_ts()}] [warn] llm_summarize failed on item {i}: {e}", flush=True)"""

    dt = time.perf_counter() - t0
    print(f"[{_ts()}] [pipeline] done in {dt:.2f}s — relevant={len(filtered)}/{len(all_items)}", flush=True)

    return {
        "counts": {
            #"sec_edgar": len(edgar),
            "marketaux": len(marketaux),
            "newsapi": len(newsapi),
            "total_deduped": len(all_items),
            "relevant": len(filtered),
        },
        "items": filtered,
    }


def print_analyst_brief(items, *, top_n=10):
    # sort by confidence (desc)
    items = sorted(items, key=lambda x: x.get("confidence", 0.0), reverse=True)[:top_n]
    print("\n=== Analyst Brief (Top {}) ===".format(len(items)))
    for i, it in enumerate(items, 1):
        sev  = (it.get("severity") or "low").title()
        et   = (it.get("event_type") or "other_events").replace("_"," ")
        tick = ", ".join(it.get("tickers") or []) or "n/a"
        src  = it.get("source") or ""
        url  = it.get("url") or ""
        # if summarized, use bullets; else fallback
        bullets = it.get("bullets") or [
            (it.get("headline","")[:90] + "."),
            f"Event: {et} · Severity: {sev}",
            f"Tickers: {tick} · Source: {src}"
        ]
        print(f"\n[{i}] {it.get('headline','')[:120]}")
        for b in bullets[:3]:
            print(f" • {b}")
        wim = it.get("why_it_matters") or "Potential portfolio impact; confirm details."
        print(f"   Why it matters: {wim}")
        print(f"   Link: {url}")


import pathlib, pandas as pd, json
from collections import Counter

if __name__ == "__main__":
    out = process(min_score=0.65, with_llm=True)
    import pathlib, re, pandas as pd

    MATERIAL_ITEMS = {"5.02","2.02","2.01","4.01","1.01"}   # CEO exit, results, M&A, auditor change, material agreement

    def extract_company(headline: str) -> str:
        # Works for "8-K - Company Name (0001234567) (Filer)" → "Company Name"
        m = re.search(r"8-K(?:/A)?\s*-\s*(.+?)\s*\(\d{6,}\)", headline or "", flags=re.IGNORECASE)
        return m.group(1).strip() if m else (headline or "").strip()

    def is_material_row(row) -> bool:
        ents = set(row.get("entities") or [])
        if ents & MATERIAL_ITEMS:
            return True
        # keep News items that already have tickers (e.g., CNBC CRWD/ROO)
        if row.get("source","").lower() != "sec_edgar" and row.get("tickers"):
            return True
        return False

    # --- add these helpers above write_current_perspective ---
    def as_list(x):
        # Normalize values to a list
        import pandas as pd
        if isinstance(x, (list, tuple)):
            return list(x)
        if x is None or (isinstance(x, float) and (x != x)) or (hasattr(pd, "isna") and pd.isna(x)):  # NaN safe
            return []
        # if a single string/object slipped in, wrap it
        return [x]

    def norm_bullets(bul):
        bul = as_list(bul)
        out = []
        for b in bul[:3]:
            b = str(b).replace("·", "-").replace("¬∑", "-").strip()
            if not b:
                continue
            if not b.endswith("."):
                b += "."
            out.append(b)
        return out


    def write_current_perspective(items: list[dict], top_n_per_section: int = 6):
        p = pathlib.Path("out"); p.mkdir(exist_ok=True)
        df = pd.DataFrame(items)

        # ensure list-like columns exist and are normalized
        for col in ["entities", "tickers", "bullets"]:
            if col not in df.columns:
                df[col] = [[]] * len(df)
            df[col] = df[col].apply(as_list)

        df["is_material"] = df.apply(is_material_row, axis=1)
        df_mat = df[df["is_material"]].copy()

        df_mat["company"] = df_mat["headline"].apply(extract_company)
        df_mat["bullets_clean"] = df_mat["bullets"].apply(norm_bullets)

        # order by severity/confidence/recency
        # (optional: map severity to rank so "High" > "Med" > "Low" reliably)
        sev_rank = {"high": 3, "med": 2, "low": 1}
        df_mat["sev_rank"] = df_mat["severity"].str.lower().map(sev_rank).fillna(0)
        df_mat = df_mat.sort_values(by=["sev_rank","confidence","published_at"], ascending=[False, False, False])

        sections = [
            ("CEO/Board changes",      df_mat[df_mat["entities"].apply(lambda x: bool(set(x) & {"5.02"}))]),
            ("Earnings/Results",       df_mat[df_mat["entities"].apply(lambda x: bool(set(x) & {"2.02"}))]),
            ("M&A / Material deals",   df_mat[df_mat["entities"].apply(lambda x: bool(set(x) & {"1.01","2.01"}))]),
            ("Auditor/Non-reliance",   df_mat[df_mat["entities"].apply(lambda x: bool(set(x) & {"4.01","4.02"}))]),
            ("Other notable (watchlist/news)",
            df_mat[~df_mat["entities"].apply(lambda x: bool(set(x) & {"5.02","2.02","1.01","2.01","4.01","4.02"}))].head(20))
        ]

        with open(p / "brief.md", "w", encoding="utf-8") as f:
            f.write("# Current Perspective — Auto-draft\n")
            for title, sub in sections:
                sub = sub.head(top_n_per_section)
                if sub.empty:
                    continue
                f.write(f"\n## {title}\n")
                for _, r in sub.iterrows():
                    tick = ", ".join(r.get("tickers") or []) or "n/a"
                    ev   = (r.get("event_type") or "other_events").replace("_"," ")
                    sev  = (r.get("severity") or "low").title()
                    comp = r.get("company") or r.get("headline","")
                    f.write(f"\n**{comp}** — {ev}; **{sev}**\n")
                    for b in r.get("bullets_clean") or []:
                        f.write(f"- {b}\n")
                    why = r.get("why_it_matters") or "Potential impact on covered names and sector sentiment."
                    f.write(f"_Why it matters:_ {why}\n")
                    if tick != "n/a":
                        f.write(f"_Tickers:_ {tick}\n")
                    url = r.get("url") or ""
                    if url:
                        f.write(f"[Source]({url})\n")

        keep_cols = ["published_at","source","company","headline","tickers",
                    "event_type","entities","severity","confidence","why_it_matters","url"]
        df_mat[keep_cols].to_csv(p / "triage_material.csv", index=False)
        print("Saved: out/brief.md, out/triage_material.csv")
    write_current_perspective(out["items"], top_n_per_section=6)

    # show where they were written
    import pathlib, os
    out_dir = pathlib.Path("out").resolve()
    print(f"Saved files in {out_dir}")
    print(f" - {out_dir / 'brief.md'}")
    print(f" - {out_dir / 'triage_material.csv'}")