from __future__ import annotations

import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from watson_helper import _wx_gen, wx_healthcheck
from ranker import infer_scores, append_training_rows
from datetime import timedelta
import json

try:
    import httpx
    import feedparser
except Exception as e:
    raise ImportError(
        "Required packages not found. Please run:\n"
        "  pip install httpx==0.27.2 feedparser==6.0.11\n"
        f"Import error was: {e}"
    )


import re, json

print("[watsonx]", wx_healthcheck())

def _extract_json_block(raw: str):
    if not raw:
        return None
    s = raw.strip()
    # remove code fences if model wrapped output
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE|re.DOTALL)
    # grab the first {...} block
    m = re.search(r"\{.*\}", s, flags=re.DOTALL)
    if not m:
        return None
    return json.loads(m.group(0))


# -------------------- Config (via env) --------------------

MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "")
NEWSAPI_API_KEY     = os.getenv("NEWSAPI_API_KEY", "")

QUERY_TERMS     = [q.strip() for q in os.getenv( # used by both MarketAux + NewsAPI
    "QUERY_TERMS",
    "Fed,ECB,earnings,merger,CEO,resigns,guidance,dividend,downgrade,upgrade"
).split(",") if q.strip()]

# Macro: Fed, ECB → central bank statements/moves.

# Corporate events: earnings, guidance, dividend, merger, CEO, resigns.

# sell-side actions: downgrade, upgrade. (Upgrade = analyst raises the stock’s rating (e.g., Hold → Buy, Neutral → Overweight).

# Downgrade = analyst lowers the rating (e.g., Buy → Hold, Outperform → Underperform).)

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

STOP_TICKERS = { # discard these as false positives
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

def enrich_tickers(item: Dict[str, Any]) -> None: # add tickers if missing
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

def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]: # remove duplicates
    seen, out = set(), []
    for it in items:
        key = safe_hash(it.get("source",""), it.get("url",""), it.get("headline",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

# ---- Weights (tweak in one place) ----
SOURCE_W = {
    "sec_8k": 0.45,   # filings are high-signal but not always high-impact
    "sec_10q": 0.30,
    "sec_10k": 0.25,
    "tier1_press": 0.30,   # Reuters/BBG/WSJ/FT/CNBC/MW
    "other_press": 0.20,
}
EVENT_W = {
    "ceo_exit": 0.35,
    "bankruptcy": 0.35,
    "non_reliance": 0.35,
    "earnings_surprise": 0.30,
    "mna": 0.30,
    "guidance_change": 0.20,
    "rating_change": 0.20,
    "reg_fd": 0.10,
    "geopolitics": 0.20,
    "unregistered_sale": 0.15,
    "dividend_change": 0.15,
    "other_events": 0.05,
}
URGENCY_W = {"high": 0.15, "med": 0.06, "low": 0.00}
KEYWORD_NUDGE = 0.03
TICKER_PRESENT = 0.04
WATCHLIST_BOOST = 0.12
MAX_SCORE = 1.0

TIER1 = ("reuters","bloomberg","wsj","ft","cnbc","marketwatch")

from datetime import datetime, timezone

def hours_old(item):
    try:
        dt = datetime.fromisoformat(item["published_at"].replace("Z","+00:00"))
    except Exception:
        return 0.0
    now = datetime.now(timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 3600.0)

def time_decay(item, half_life_hours=24):
    # 24h half-life; =1 when fresh, 0.5 after 24h, etc.
    h = hours_old(item)
    return 0.5 ** (h / half_life_hours)

def score_item(it: dict) -> float:
    s = 0.0
    src = (it.get("source") or "").lower()
    head = (it.get("headline") or "")
    et = (it.get("event_type") or "other_events")
    urg = (it.get("urgency") or "low")

    # Source
    if src == "sec_edgar":
        if head.startswith("8-K"):   s += SOURCE_W["sec_8k"]
        elif head.startswith("10-Q"): s += SOURCE_W["sec_10q"]
        elif head.startswith("10-K"): s += SOURCE_W["sec_10k"]
        else:                         s += SOURCE_W["sec_8k"] * 0.7
    elif any(d in src for d in TIER1): s += SOURCE_W["tier1_press"]
    else:                               s += SOURCE_W["other_press"]

    # Event & urgency
    s += EVENT_W.get(et, EVENT_W["other_events"])
    s += URGENCY_W.get(urg, 0.0)

    # Keyword nudges (small)
    for kw in ("guidance","resigns","resignation","appointed","impairment",
               "non-reliance","acquisition","merger","downgrade","upgrade","beats","misses"):
        if kw in head.lower():
            s += KEYWORD_NUDGE

    # Tickers
    tickers = set(it.get("tickers") or [])
    if tickers:
        s += TICKER_PRESENT
        if (tickers & WATCHLIST):
            s += WATCHLIST_BOOST

    # Time decay (optional: apply to the impact portion only)
    s = s * time_decay(it, half_life_hours=24)

    return min(s, MAX_SCORE)

def severity(score: float) -> str:
    if score >= 0.80: return "high"
    if score >= 0.55: return "med"
    return "low"

# -------------------- LLM scaffolding (safe fallbacks) --------------------

def llm_classify(item: dict) -> dict: # turn a raw article into structured data 
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

    raw = _wx_gen(prompt, model_key="classify")
    # Safe fallback default
    out = {
        "event_type": "other_events",
        "tickers": item.get("tickers") or [],
        "sectors": [],
        "asset_classes": ["Equity"],
        "regions": ["US"],
        "confidence": 0.55,
        "_classify_fallback": True,
    }
    if not raw:
        return out
    # Try to parse JSON
    try:
        j = _extract_json_block(raw)
        # merge defensively
        for k in out.keys():
            if k in j and j[k] is not None:
                out[k] = j[k]
        # normalize types
        out["tickers"] = [str(t).upper() for t in (out.get("tickers") or [])]
        out["confidence"] = float(out.get("confidence") or 0.55)
        out["_classify_fallback"] = False
        return out
    except Exception:
        return out

MAX_CLASSIFY  = 20   # cap LLM classify for testing
MAX_SUMMARIZE = 20   # cap LLM summarize for testing

WHY_DEFAULTS = {
    "ceo_exit": "Leadership change can reset strategy/guidance; watch succession and market reaction.",
    "mna": "Deal terms can re-rate acquirer/target; dilution, synergies and antitrust path drive impact.",
    "earnings_surprise": "Beat/miss vs consensus shifts estimates and valuation; check guidance details.",
    "auditor_change": "Auditor switches can flag reporting/control risk; credibility often pressured short term.",
    "non_reliance": "Restatement/non-reliance raises financial reporting concerns and legal/regulatory risk.",
    "bankruptcy": "Case outcomes drive creditor recoveries and equity value; watch first-day motions.",
    "dividend_change": "Capital returns signal balance-sheet health and capital allocation priorities.",
    "rating_change": "Sell-side actions can move flows, esp. in smaller caps; read the thesis details.",
    "reg_fd": "Material disclosures under Reg FD may move expectations and estimates.",
    "geopolitics": "Policy/supply-chain risk can affect sector multiples and demand.",
    "other_events": "Potential impact on covered names and sector sentiment; confirm details as they develop."
}



def llm_summarize(item: dict) -> dict: # return json with headline, bullets, why_it_matters, for frontend display
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

    raw = _wx_gen(prompt, model_key="summarize")
    # Fallback
    h = title.strip()
    fallback = {
    "headline": h[:90],
    "bullets": [
        (h[:90] + "."),
        f"Event: {event} · Severity: {item.get('severity','low')}",
        f"Tickers: {tick or 'n/a'} · Source: {item.get('source')}"
    ],
    "why_it_matters": WHY_DEFAULTS.get(event, WHY_DEFAULTS["other_events"])
}

    meta = {
        "_summary_fallback": True,
        "_headline_fallback": True,
        "_bullets_fallback": True,
        "_why_fallback": True,
    }

    if not raw:
        return {**fallback, **meta}

    try:
        j = _extract_json_block(raw)
        if not j:
            return {**fallback, **meta}

        # decide field-by-field
        headline = j.get("headline")
        bullets  = j.get("bullets")
        why      = j.get("why_it_matters")

        headline_fb = not bool(headline)
        bullets_fb  = not (isinstance(bullets, list) and len(bullets) >= 3)
        why_fb      = not bool(why and str(why).strip())

        result = {
            "headline": headline if not headline_fb else fallback["headline"],
            "bullets":  bullets  if not bullets_fb  else fallback["bullets"],
            "why_it_matters": (str(why).strip() if not why_fb else fallback["why_it_matters"]),
            "_headline_fallback": headline_fb,
            "_bullets_fallback": bullets_fb,
            "_why_fallback": why_fb,
        }
        result["_summary_fallback"] = (headline_fb and bullets_fb and why_fb)
        return result
    except Exception:
        return {**fallback, **meta}


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
    published_after = (datetime.now(timezone.utc) - timedelta(hours=12)).replace(microsecond=0).isoformat()+"Z"
    params = {
        "api_token": MARKETAUX_API_TOKEN,
        "language":"en",
        "filter_entities":"true",
        "published_after": published_after,
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

def process(min_score: float = 0.6, with_llm: bool = True, ml_weight: float = 0.7) -> Dict[str, Any]:
    """
    Pipeline:
      1) Fetch → dedupe → enrich → pre-score (heuristic)
      2) Select LLM subset: MATERIAL 8-K first, then by priority (pre-score + small nudges)
      3) LLM classify subset (event/tickers + _llm_conf)
      4) ML infer (_ml_score)
      5) Final score = (1-ml_weight)*heur + ml_weight*ml + small LLM nudge
      6) Filter, summarize, persist training rows
    """
    t0 = time.perf_counter()
    print(f"[{_ts()}] [pipeline] start (min_score={min_score}, with_llm={with_llm}, ml_weight={ml_weight})", flush=True)

    # 1) Fetch
    print(f"[{_ts()}] [pipeline] fetching sources…", flush=True)
    edgar     = fetch_edgar()
    marketaux = fetch_marketaux()
    newsapi   = fetch_newsapi()
    print(f"[{_ts()}] fetched → edgar={len(edgar)} marketaux={len(marketaux)} newsapi={len(newsapi)}", flush=True)

    # 2) Dedupe
    all_items = dedupe(edgar + marketaux + newsapi)
    print(f"[{_ts()}] [pipeline] after dedupe: total={len(all_items)}", flush=True)

    for it in all_items:
        it["_classified"]  = False   # will flip to True inside the LLM classify loop
        it["_summarized"]  = False
        
    # 3) Enrich + keyword preclassify + pre-score (heuristic only)
    print(f"[{_ts()}] [pipeline] enrich + preclassify + pre-score…", flush=True)
    for idx, it in enumerate(all_items, 1):
        try:
            enrich_tickers(it)
            preclassify_keywords(it)
            it["_pre_conf"] = score_item(it)  # heuristic prior with time decay
        except Exception as e:
            print(f"[{_ts()}] [warn] enrich/preclassify failed on item#{idx}: {e}", flush=True)

    # 4) Choose LLM classify subset
    MATERIAL_EDGAR = {"1.01","2.01","2.02","4.01","4.02","5.02"}  # MA, M&A, results, auditor/non-reliance, CEO
    def _is_tier1(src: str) -> bool:
        s = (src or "").lower()
        return any(d in s for d in TIER1)

    def _is_edgar_8k(it) -> bool:
        return (it.get("source", "").lower() == "sec_edgar" and (it.get("headline", "").startswith("8-K")))

    def _on_watchlist(it) -> bool:
        return bool(set(it.get("tickers") or []) & WATCHLIST)

    def _priority_score(it) -> float:
        # Score-first, small nudges for EDGAR 8-K, Tier-1, watchlist
        pre = float(it.get("_pre_conf", 0.0))
        bonus = 0.0
        if _is_edgar_8k(it):                 bonus += 0.05
        if _is_tier1(it.get("source")):      bonus += 0.03
        if _on_watchlist(it):                bonus += 0.02
        return pre + bonus

    # Guardrail: always include material EDGAR
    must_classify = [
        it for it in all_items
        if (it.get("source", "").lower() == "sec_edgar" and (set(it.get("entities") or []) & MATERIAL_EDGAR))
    ]

    # Fill the rest by priority; keep uniqueness; cap at MAX_CLASSIFY
    seen_ids = {it["id"] for it in must_classify}
    rest_sorted = sorted(all_items, key=_priority_score, reverse=True)
    subset_for_llm = must_classify + [it for it in rest_sorted if it["id"] not in seen_ids]
    subset_for_llm = subset_for_llm[:MAX_CLASSIFY]
    print(f"[{_ts()}] [pipeline] LLM classify target count: {len(subset_for_llm)}", flush=True)

    # 5) LLM classify subset (to improve event/tickers + get _llm_conf)
    if with_llm and subset_for_llm:
        print(f"[{_ts()}] [pipeline] LLM classify…", flush=True)
        for i, it in enumerate(subset_for_llm, 1):
            try:
                cls = llm_classify(it)
                it["event_type"]    = it.get("event_type") or cls.get("event_type")
                it["tickers"]       = list({*(it.get("tickers") or []), *cls.get("tickers", [])})
                it["sectors"]       = it.get("sectors") or cls.get("sectors") or []
                it["asset_classes"] = it.get("asset_classes") or cls.get("asset_classes") or []
                it["regions"]       = it.get("regions") or cls.get("regions") or []
                it["_llm_conf"]     = float(cls.get("confidence") or 0.5)
                it["_classify_fallback"] = bool(cls.get("_classify_fallback", True))
                it["_classified"]        = True
            except Exception as e:
                print(f"[{_ts()}] [warn] llm_classify failed on item {i}: {e}", flush=True)
            if i % 5 == 0:
                print(f"  …classified {i}/{len(subset_for_llm)}", flush=True)

    # 6) ML ranker inference
    ml_scores = infer_scores(all_items)  # {} if no model yet
    used_ml = 0
    for it in all_items:
        ms = ml_scores.get(it["id"])
        if ms is not None:
            it["_ml_score"] = float(ms)
            used_ml += 1
    print(f"[{_ts()}] [pipeline] ML scores available for {used_ml}/{len(all_items)} items", flush=True)

    # 7) Final score + severity (ML-led blend + tiny LLM nudge)
    print(f"[{_ts()}] [pipeline] scoring + severity…", flush=True)
    for it in all_items:
        heur = score_item(it)  # recompute with latest event/tickers (safe)
        ml   = it.get("_ml_score")
        if ml is not None:
            base = (1.0 - ml_weight) * heur + ml_weight * float(ml)
        else:
            base = heur  # cold-start fallback

        # very small nudge from LLM certainty (centered at 0.5)
        if "_llm_conf" in it:
            base += 0.05 * (float(it["_llm_conf"]) - 0.5)

        base = max(0.0, min(1.0, base))
        it["confidence"] = base
        it["severity"]   = severity(base)

    # 8) Filter AFTER blending
    filtered = [it for it in all_items if it["confidence"] >= min_score]
    print(f"[{_ts()}] [pipeline] filtered relevant: {len(filtered)} (threshold={min_score})", flush=True)

    # 9) Persist feature rows for future labeling/training
    try:
        from pathlib import Path
        Path("out").mkdir(parents=True, exist_ok=True)
        append_training_rows(all_items, csv_out="out/training_events.csv")
    except Exception as e:
        print(f"[{_ts()}] [warn] append_training_rows failed: {e}", flush=True)

    # 10) Summarize ONLY top-N filtered
    filtered.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    to_summarize = filtered[:MAX_SUMMARIZE]
    if with_llm and to_summarize:
        print(f"[{_ts()}] [pipeline] LLM summarize on {len(to_summarize)} of {len(filtered)} items…", flush=True)
        for i, it in enumerate(to_summarize, 1):
            try:
                if not it.get("event_type"):  # rare rescue
                    cls = llm_classify(it)
                    it["event_type"] = it.get("event_type") or cls.get("event_type")
                summ = llm_summarize(it)
                it["bullets"]        = summ.get("bullets", [])
                it["why_it_matters"] = summ.get("why_it_matters", "Potential portfolio impact; confirm details.")
                it["draft_note"]     = summ.get("draft_note", f"{it.get('headline','')} — {it.get('url','')}")
                it["_summary_fallback"]  = bool(summ.get("_summary_fallback", True))
                it["_headline_fallback"] = bool(summ.get("_headline_fallback", True))
                it["_bullets_fallback"]  = bool(summ.get("_bullets_fallback", True))
                it["_why_fallback"]      = bool(summ.get("_why_fallback", True))
                it["_summarized"]        = True
            except Exception as e:
                print(f"[{_ts()}] [warn] llm_summarize failed on item {i}: {e}", flush=True)
            if i % 5 == 0:
                print(f"  …summarized {i}/{len(to_summarize)}", flush=True)

    # Clean tail (filtered but not summarized)
    for it in filtered[MAX_SUMMARIZE:]:
        it.pop("bullets", None); it.pop("why_it_matters", None); it.pop("draft_note", None)

    dt = time.perf_counter() - t0
    print(f"[{_ts()}] [pipeline] done in {dt:.2f}s — relevant={len(filtered)}/{len(all_items)}", flush=True)

    classify_fb = sum(1 for it in all_items if it.get("_classified") and it.get("_classify_fallback"))
    summ_fb     = sum(1 for it in filtered  if it.get("_summarized") and it.get("_summary_fallback"))

    return {
        "counts": {
            "sec_edgar": len(edgar),
            "marketaux": len(marketaux),
            "newsapi": len(newsapi),
            "total_deduped": len(all_items),
            "relevant": len(filtered),
            "classified": sum(it.get("_classified", False) for it in all_items),
            "summarized": sum(it.get("_summarized", False) for it in filtered),
            "classify_fallback": classify_fb,
            "summarize_fallback": summ_fb,
        },
        "items": filtered,
    }



"""def print_analyst_brief(items, *, top_n=10):
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
        print(f"   Link: {url}")"""


import pathlib, pandas as pd, json
from collections import Counter

if __name__ == "__main__":
    out = process(min_score=0.4, with_llm=True)
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

    def coalesce_why(event_type, why):
        import pandas as pd
        # treat None/NaN/empty as missing and backfill by event
        if why is None or (isinstance(why, float) and pd.isna(why)) or not str(why).strip():
            return WHY_DEFAULTS.get(event_type or "other_events", WHY_DEFAULTS["other_events"])
        return str(why).strip()


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
                    why = coalesce_why(r.get("event_type"), r.get("why_it_matters"))
                    f.write(f"_Why it matters:_ {why}\n")
                    if tick != "n/a":
                        f.write(f"_Tickers:_ {tick}\n")
                    url = r.get("url") or ""
                    if url:
                        f.write(f"[Source]({url})\n")

        keep_cols = ["id", "published_at","source","company","headline","tickers",
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