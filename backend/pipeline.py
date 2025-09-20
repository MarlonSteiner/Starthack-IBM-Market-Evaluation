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
from pathlib import Path
DEBUG_DIR = Path("out/debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))



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
def _extract_json_block(raw):
    import json, re
    if raw is None:
        return None
    # Accept already-parsed Python objects
    if isinstance(raw, (dict, list)):
        return raw

    s = str(raw).strip()

    # Strip code fences if present
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s,
                   flags=re.IGNORECASE | re.DOTALL).strip()

    # Fast path for clean JSON object/array
    if s[:1] in ("{", "["):
        try:
            return json.loads(s)
        except Exception:
            pass

    # Try first balanced { ... }
    start = s.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(s[start:], start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    block = s[start:i+1]
                    try:
                        return json.loads(block)
                    except Exception:
                        break  # fall through

    # Try array root if there’s any '[' later on
    astart = s.find("[")
    if astart != -1:
        try:
            return json.loads(s[astart:])
        except Exception:
            return None

    return None





# -------------------- Config (via env) --------------------

MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "")
NEWSAPI_API_KEY     = os.getenv("NEWSAPI_API_KEY", "")

QUERY_TERMS = [q.strip() for q in os.getenv(
    "QUERY_TERMS",
    "Fed,ECB,Zins,Inflation,Ergebnis,Quartalszahlen,Prognose,Ausblick,Dividende,"
    "Übernahme,Fusion,CEO,Rücktritt,Abstufung,Hochstufung,Downgrade,Upgrade,Guidance"
).split(",") if q.strip()]


# Macro: Fed, ECB → central bank statements/moves.

# Corporate events: earnings, guidance, dividend, merger, CEO, resigns.

# sell-side actions: downgrade, upgrade. (Upgrade = analyst raises the stock’s rating (e.g., Hold → Buy, Neutral → Overweight).

# Downgrade = analyst lowers the rating (e.g., Buy → Hold, Outperform → Underperform).)

NEWSAPI_DOMAINS = os.getenv(
    "NEWSAPI_DOMAINS",
    "reuters.com,ft.com,wsj.com,bloomberg.com,cnbc.com,marketwatch.com,nzz.ch,handelszeitung.ch"
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
    # Management
    "ceo_exit": ["ceo resigns","steps down","resigns as ceo","appointed ceo","names ceo",
                 "tritt zurück","rücktritt","scheidet aus","neuer ceo","zum ceo ernannt"],
    # M&A
    "mna": ["acquires","acquisition","to buy","merger","merges with","takeover",
            "übernahme","akquisition","kauft","fusion","mehrheitsbeteiligung"],
    # Earnings/Guidance
    "earnings_surprise": ["beats estimates","misses estimates","tops forecasts","cuts outlook","raises outlook","guidance",
                          "übertrifft erwartungen","verfehlt erwartungen","prognose","ausblick angehoben","ausblick gesenkt"],
    # Rating
    "rating_change": ["downgrades","upgrades","cut to","raised to","initiated at",
                      "abstufung","hochstuft","herabgestuft","aufgestuft","aufnahme der bewertung"],
    # Geo/Policy
    "geopolitics": ["sanction","tariff","strike","protest","conflict","attack",
                    "sanktion","zoll","streik","protest","konflikt","angriff"],
    # Capital returns
    "dividend_change": ["dividend","buyback","repurchase",
                        "dividende","aktienrückkauf","rückkaufprogramm"],
    # Bankruptcy
    "bankruptcy": ["bankruptcy","chapter 11","insolvenz","insolvenzverfahren"],
}



def translate_to_de(text: str) -> str:
    if not text:
        return ""
    prompt = f"""Übersetze ins Deutsche in neutralem Finanzstil.
- Erhalte Zahlen, Prozente, Währungen und Ticker unverändert.
- Unternehmens- und Eigennamen nicht übersetzen.
- Keine Halluzinationen, nichts hinzufügen oder weglassen.
- Wenn Text bereits Deutsch ist, unverändert zurückgeben.

TEXT:
{text[:6000]}"""
    raw = _wx_gen(prompt, model_key="summarize")
    # Best-effort: if model returns JSON by habit, strip it; else return as-is
    tr = str(raw or "").strip()
    return tr


def preclassify_keywords(item: Dict[str, Any]) -> None:
    if item.get("source", "").lower() == "sec_edgar": return
    text = ((item.get("headline") or "") + " " + (item.get("body_text") or "")).lower()
    for et, words in KW_MAP.items():
        if any(w in text for w in words):
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

TIER1 = ("reuters","bloomberg","wsj","ft","cnbc","marketwatch",
         "nzz","handelszeitung","handelsblatt","faz","wiwo","boerse.ard","tagesschau","finanzen.net","cash","finews","tagesanzeiger")


from datetime import datetime, timezone

def hours_old(item):
    try:
        dt = datetime.fromisoformat(item["published_at"].replace("Z","+00:00"))
    except Exception:
        return 0.0
    now = datetime.now(timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 3600.0)

def time_decay(item, half_life_hours=72):
    # 24h half-life; =1 when fresh, 0.5 after 24h, etc.
    h = hours_old(item)
    return 0.5 ** (h / half_life_hours)

def score_item_base(it: dict) -> float:
    s = 0.0
    src = (it.get("source") or "").lower()
    s += SOURCE_W["tier1_press"] if any(d in src for d in TIER1) else SOURCE_W["other_press"]
    et = (it.get("event_type") or "other_events"); urg = (it.get("urgency") or "low")
    s += EVENT_W.get(et, EVENT_W["other_events"]); s += URGENCY_W.get(urg, 0.0)
    if any(kw in (it.get("headline") or "").lower() for kw in (
        "guidance","resigns","resignation","appointed","impairment","non-reliance",
        "acquisition","merger","downgrade","upgrade","beats","misses",
        "ausblick","tritt zurück","übernahme","fusion","abstufung","hochstuft",
        "übertrifft","verfehlt","dividende","aktienrückkauf","insolvenz")): s += KEYWORD_NUDGE
    if it.get("tickers"): s += TICKER_PRESENT
    if set(it.get("tickers") or []) & WATCHLIST: s += WATCHLIST_BOOST
    return min(s, MAX_SCORE)


def severity(score: float) -> str:
    if score >= 0.80: return "high"
    if score >= 0.55: return "med"
    return "low"

# -------------------- LLM scaffolding (safe fallbacks) --------------------

def llm_classify(item: dict) -> dict:
    title = item.get("headline") or ""
    body  = (item.get("body_text") or "")[:1500]
    hints = ", ".join(item.get("tickers") or [])
    prompt = f"""
Du bist ein Klassifizierer für Finanznachrichten (Analysten-Triage).

Gib STRENGES JSON mit folgenden Schlüsseln zurück:
event_type: eins aus [central_bank, earnings_surprise, ceo_exit, mna, rating_change, dividend_change, bankruptcy, regulatory, sector_shock, other_events]
tickers: Array aus Strings (Aktienticker, UPPERCASE)
sectors: Array aus Strings (GICS-ähnlich)
asset_classes: Teilmenge von [Equity, Rates, Credit, Commodities, FX]
regions: Teilmenge von [US, EU, CH, UK, JP, EM]
confidence: Float 0..1 (Sicherheit bzgl. event_type)

TITLE: {title}
BODY: {body}
TICKER_HINTS: {hints or "n/a"}

Nur JSON ausgeben, keine Prosa.
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
        if not j:
            Path(DEBUG_DIR / f"classify_{item.get('id','unknown')}.txt").write_text(raw or "", encoding="utf-8")
            return out

        # Aliases
        evt = j.get("event_type") or j.get("eventType") or j.get("type")
        tix = j.get("tickers")    or j.get("symbols")  or j.get("tickers_list")
        sct = j.get("sectors")    or j.get("sector")   or []
        acl = j.get("asset_classes") or j.get("assetClasses") or []
        rgn = j.get("regions")    or j.get("region")   or []
        conf = j.get("confidence")

        if tix is None:
            tix = []
        out.update({
            "event_type": evt or out["event_type"],
            "tickers": [str(t).upper() for t in (tix or [])],
            "sectors": sct or [],
            "asset_classes": acl or ["Equity"],
            "regions": rgn or ["US"],
            "confidence": float(conf if conf is not None else out["confidence"]),
            "_classify_fallback": False,
        })
        # Save parsed if anything is odd/missing
        if not evt:
            Path(DEBUG_DIR / f"classify_{item.get('id','unknown')}_parsed.json").write_text(
                json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return out

    except Exception:
        return out

MAX_CLASSIFY  = 20  # cap LLM classify for testing
MAX_SUMMARIZE = 20  # cap LLM summarize for testing

WHY_DEFAULTS = {
    "ceo_exit": "Führungswechsel kann Strategie und Guidance verschieben; Nachfolge und Marktreaktion beobachten.",
    "mna": "Bewertung von Käufer und Ziel hängt an Bedingungen, Verwässerung, Synergien und Kartellfreigabe.",
    "earnings_surprise": "Abweichungen vom Konsens ändern Schätzungen und Bewertungen; Guidance entscheidend.",
    "auditor_change": "Prüferwechsel kann Reporting-/Kontrollrisiken signalisieren; Glaubwürdigkeit kurzfristig belastet.",
    "non_reliance": "Nichtverlassenserklärung erhöht Reporting- und Rechtsrisiken; mögliche Restatements.",
    "bankruptcy": "Verfahrensausgang bestimmt Gläubigerrückflüsse und Eigenkapital; erste Maßnahmen beobachten.",
    "dividend_change": "Kapitalrückflüsse signalisieren Bilanzqualität und Allokationsprioritäten.",
    "rating_change": "Analystenstufen bewegen Flüsse, v. a. bei kleineren Caps; Begründung prüfen.",
    "reg_fd": "Wesentliche FD-Offenlegung kann Erwartungen und Schätzungen verschieben.",
    "geopolitics": "Politik- und Lieferkettenrisiken beeinflussen Sektormultiplikatoren und Nachfrage.",
    "other_events": "Potenzielle Relevanz für Titel/Sektor; Details verifizieren.",
}



def llm_summarize(item: dict) -> dict:
    title = item.get("headline") or ""
    body  = (item.get("body_text") or "")[:1500]
    event = item.get("event_type") or "other_events"
    tick  = ", ".join(item.get("tickers") or [])

    prompt = f"""
Du verfasst kompakte Analysten-Karten im Stil von Wellershoff & Partners.

STIL:
- Neutral, faktenbasiert, knapp. Zahlen zuerst, dann eine Linie Kontext.
- Kurze Hauptsätze, wenige Adjektive. „stieg/fiel/unverändert“, nicht „sprang/stürzte“.
- Makro-bewusst (Basiseffekte, Kern vs. Gesamt, real vs. nominal, Bewertung vs. Ertrag, Politikrahmen).
- Formulierungen: „bleibt“, „deutet auf“, „stützt“, „belastet“, „Spielraum ist gering“, „Risiken sind asymmetrisch“.
- Keine Ratschläge, keine Ausrufe, keine Spekulation außer wenn explizit im INPUT.
- Zahlen mit Einheiten (%, bp, YoY/QoQ, Niveaus, Vergleich).

STRUKTUR (genau 3 Bulletpoints, je 7–18 Wörter):
1) Kontext — Was das Unternehmen/der Emittent ist (Kernaktivität).
2) Narrativ — Was jetzt passiert (Aktion/Ereignis) mit relevantesten Zahlen.
3) Wirkung/Jetzt — Warum es jetzt zählt; Reaktion/Guidance/Bewertung falls vorhanden.

AUSGABE
Gib JSON mit GENAU diesen Schlüsseln zurück:
- "headline": string (<= 90 Zeichen), rein sachlich.
- "bullets": genau 3 kurze Sätze (7–18 Wörter).
- "why_it_matters": ein Satz (<= 40 Wörter), sachlich.

REGELN
- Immer alle Schlüssel ausgeben.
- Wenn Infos nicht reichen: why_it_matters = "Unzureichende Informationen für eine Einordnung."
- Keine Emojis, keine Halbsätze, keine Semikolons.
- Nur belegbare Fakten aus dem INPUT.

INPUT
TITLE: {title}
BODY: {body}
EVENT: {event}
TICKERS: {tick or "n/a"}
""".strip()
    raw = _wx_gen(prompt, model_key="summarize")

    # Fallback
    h = title.strip()
    fallback = {
    "headline": h[:90],
    "bullets": [
        (h[:90] + "."),
        f"Ereignis: {event} · Priorität: {item.get('severity','low')}",
        f"Ticker: {tick or 'n/a'} · Quelle: {item.get('source')}"
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
            Path(DEBUG_DIR / f"summarize_{item.get('id','unknown')}.txt").write_text(raw or "", encoding="utf-8")
            return {**fallback, **meta}

        # Accept common variants
        headline = j.get("headline") or j.get("title")
        bullets  = j.get("bullets") or j.get("points") or j.get("bullet_points")
        why      = (j.get("why_it_matters") or j.get("whyItMatters") or
                    j.get("why-it-matters") or j.get("why") or j.get("rationale"))

        # Convert single-string bullets into a list
        if isinstance(bullets, str):
            bullets = [b.strip("•- \t") for b in bullets.splitlines() if b.strip()]

        # Normalize + enforce 3 bullets
        fb_bul = [
            (h[:90] + "."),
            f"Ereignis: {event} · Priorität: {item.get('severity','low')}",
            f"Ticker: {tick or 'n/a'} · Quelle: {item.get('source')}"
        ]


        final_bullets = []
        if isinstance(bullets, list):
            tmp = [b for b in bullets if str(b).strip()]
            # Keep first 3; pad with fallbacks if fewer
            tmp = tmp[:3]
            while len(tmp) < 3:
                tmp.append(None)
            fb_iter = iter(fb_bul)
            for b in tmp:
                s = (b or "").strip()
                # end with period; trim overly long bullets; keep within ~18 words if possible
                if s and not s.endswith("."):
                    s += "."
                final_bullets.append(s if s else next(fb_iter))
            bullets_fb = False
        else:
            final_bullets = fb_bul
            bullets_fb = True

        headline_fb = not bool(headline)
        why_fb      = not bool(why and str(why).strip())

        # Try one-shot backfill for WHY if missing
        if why_fb:
            backfill = llm_why(item)
            if backfill:
                why = backfill
                why_fb = False

        result = {
            "headline": headline if not headline_fb else fallback["headline"],
            "bullets":  final_bullets,
            "why_it_matters": (str(why).strip() if not why_fb else fallback["why_it_matters"]),
            "_headline_fallback": headline_fb,
            "_bullets_fallback": bullets_fb,
            "_why_fallback": why_fb,
        }
        result["_summary_fallback"] = (result["_headline_fallback"] and
                                       result["_bullets_fallback"] and
                                       result["_why_fallback"])
        return result

    except Exception:
        return {**fallback, **meta}


def llm_why(item: dict) -> str | None:
    """Get ONLY why_it_matters as JSON to backfill when missing."""
    title = item.get("headline") or ""
    body  = (item.get("body_text") or "")[:800]  # keep it short to reduce failure
    event = item.get("event_type") or "other_events"
    tick  = ", ".join(item.get("tickers") or [])

    prompt = f'''
Gib JSON mit genau einem Schlüssel zurück: "why_it_matters".
- Wert: ein prägnanter deutscher Satz (<= 40 Wörter), warum die Meldung marktrelevant ist.
- Wenn Infos nicht reichen: "Unzureichende Informationen für eine Einordnung."

TITLE: {title}
BODY: {body}
EVENT: {event}
TICKERS: {tick or "n/a"}
'''.strip()

    raw = _wx_gen(prompt, model_key="summarize")  # or a dedicated "why" key if you have it
    try:
        j = _extract_json_block(raw)
        v = j.get("why_it_matters") if j else None
        v = (v or "").strip()
        return v or None
    except Exception:
        return None


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
    published_after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).replace(microsecond=0).isoformat()+"Z"
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
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    frm = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).replace(microsecond=0).isoformat() + "Z"
    params = {
        "q": q,
        "language":"en",
        "pageSize": 50,
        "sortBy":"publishedAt",
        "apiKey": NEWSAPI_API_KEY,
        "domains": NEWSAPI_DOMAINS,
        "from": frm,
        "to": now,
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

def process(min_score: float = 0.4, with_llm: bool = True, ml_weight: float = 0.3) -> Dict[str, Any]:
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
    # edgar     = fetch_edgar()
    marketaux = fetch_marketaux()
    newsapi   = fetch_newsapi()
    #print(f"[{_ts()}] fetched → edgar={len(edgar)} marketaux={len(marketaux)} newsapi={len(newsapi)}", flush=True)
    print(f"[{_ts()}] fetched → marketaux={len(marketaux)} newsapi={len(newsapi)}", flush=True)

    # 2) Dedupe
    #all_items = dedupe(edgar + marketaux + newsapi)
    all_items = dedupe(marketaux + newsapi)
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
            impact = score_item_base(it)
            it["_pre_conf"] = impact * time_decay(it)
 # heuristic prior with time decay
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
    if (it.get("source","").lower()=="sec_edgar" and (set(it.get("entities") or []) & MATERIAL_EDGAR))
       or (set(it.get("tickers") or []) & WATCHLIST)
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
        impact = score_item_base(it)                 # no decay
        recent  = impact * time_decay(it)            # with decay
        ml = it.get("_ml_score")
        base = (1.0 - ml_weight) * recent + (ml_weight * float(ml) if ml is not None else 0.0)
        if "_llm_conf" in it: base += 0.05 * (float(it["_llm_conf"]) - 0.5)
        it["confidence"] = max(0.0, min(1.0, base))
        it["severity"]   = severity(impact)          # <-- severity from undecayed score


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
    # 10) Summarize ONLY top-N filtered
    filtered.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

    # Prioritize material 8-K (1.01/2.01/2.02/4.01/4.02/5.02) and news that already have tickers
    MATERIAL_ITEMS = {"1.01","2.01","2.02","4.01","4.02","5.02"}
    # Rank everything by final confidence, prefer material first
    def _is_material(it):
        ents = set(it.get("entities") or [])
        return bool(ents & {"1.01","2.01","2.02","4.01","4.02","5.02"} or (it.get("source","").lower() != "sec_edgar" and it.get("tickers")))

    all_ranked = sorted(all_items, key=lambda x: x.get("confidence", 0.0), reverse=True)
    material = [it for it in all_ranked if _is_material(it)]
    non_material = [it for it in all_ranked if not _is_material(it)]

    TARGET_SUMMARIES = 20  # pick your number
    to_summarize = (material + non_material)[:min(MAX_SUMMARIZE, TARGET_SUMMARIES)]
    print(f"[{_ts()}] [pipeline] LLM summarize on {len(to_summarize)} of {len(all_items)} items…", flush=True)


    if with_llm and to_summarize:
        print(f"[{_ts()}] [pipeline] LLM summarize on {len(to_summarize)} of {len(filtered)} items…", flush=True)
        for i, it in enumerate(to_summarize, 1):
            try:
                if not it.get("event_type"):  # rare rescue
                    cls = llm_classify(it)
                    it["event_type"] = it.get("event_type") or cls.get("event_type")
                summ = llm_summarize(it)

                why = (summ.get("why_it_matters") or "").strip()
                why_fb = False
                if not why:
                    backfill = llm_why(it)
                    if backfill:
                        why = backfill.strip()
                        why_fb = False
                    else:
                        why = WHY_DEFAULTS.get(it.get("event_type") or "other_events", WHY_DEFAULTS["other_events"])
                        why_fb = True

                it["why_it_matters"] = why
                it["_why_fallback"]  = why_fb  # <- drives your CSV metric


                it["why_it_matters"] = why
                it["_why_fallback"]  = why_fb
                it["bullets"]        = summ.get("bullets", [])
                it["draft_note"]     = summ.get("draft_note", f"{it.get('headline','')} — {it.get('url','')}")
                it["_summary_fallback"]  = bool(summ.get("_summary_fallback", True))
                it["_headline_fallback"] = bool(summ.get("_headline_fallback", True))
                it["_bullets_fallback"]  = bool(summ.get("_bullets_fallback", True))
                it["_summarized"]        = True
                # Use LLM headline (German) or translate the original if the LLM headline fell back
                de_headline = (summ.get("headline") or "").strip()
                if not de_headline or summ.get("_headline_fallback", False):
                    de_headline = translate_to_de(it.get("headline", ""))  # best-effort fallback

                it["headline_de"] = de_headline or it.get("headline", "")

                # Make a short German draft one-liner (for Slack/UI)
                # Keep it terse and factual: "Headline — Why it matters"
                it["draft_note_de"] = f"{it['headline_de']} — {it['why_it_matters']}".strip()

            except Exception as e:
                print(f"[{_ts()}] [warn] llm_summarize failed on item {i}: {e}", flush=True)
            if i % 5 == 0:
                print(f"  …summarized {i}/{len(to_summarize)}", flush=True)
    ensure_de_fields(filtered)
    # Clean tail (filtered but not summarized)
    for it in filtered[MAX_SUMMARIZE:]:
        it.pop("bullets", None); it.pop("why_it_matters", None); it.pop("draft_note", None)

    dt = time.perf_counter() - t0
    print(f"[{_ts()}] [pipeline] done in {dt:.2f}s — relevant={len(filtered)}/{len(all_items)}", flush=True)

    classify_fb = sum(1 for it in all_items if it.get("_classified") and it.get("_classify_fallback"))
    summ_fb     = sum(1 for it in filtered  if it.get("_summarized") and it.get("_summary_fallback"))

    return {
        "counts": {
            #"sec_edgar": len(edgar),
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

"""def write_frontend_payload(items: list[dict], counts: dict, path: str = "out/feed.json"):
    from pathlib import Path
    import json
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # pick & normalize fields the UI needs
    def pack(it: dict) -> dict:
        return {
            "id": it.get("id"),
            "published_at": it.get("published_at"),   # ISO string already
            "source": it.get("source"),
            "url": it.get("url"),
            "headline": it.get("headline"),
            "body_text": it.get("body_text"),

            # NLP/classification
            "event_type": it.get("event_type"),
            "entities": it.get("entities") or [],
            "tickers": it.get("tickers") or [],
            "sectors": it.get("sectors") or [],
            "asset_classes": it.get("asset_classes") or [],
            "regions": it.get("regions") or [],

            # scores
            "confidence": it.get("confidence"),
            "severity": it.get("severity"),
            "_pre_conf": it.get("_pre_conf"),
            "_ml_score": it.get("_ml_score"),
            "_llm_conf": it.get("_llm_conf"),

            # summary card
            "bullets": it.get("bullets") or [],
            "why_it_matters": (it.get("why_it_matters") or "").strip() if isinstance(it.get("why_it_matters"), str) else it.get("why_it_matters"),
            "draft_note": it.get("draft_note"),

            # fallbacks/flags so UI can badge quality
            "_classified": bool(it.get("_classified")),
            "_classify_fallback": bool(it.get("_classify_fallback", True)),
            "_summarized": bool(it.get("_summarized")),
            "_summary_fallback": bool(it.get("_summary_fallback", True)),
            "_headline_fallback": bool(it.get("_headline_fallback", True)),
            "_bullets_fallback": bool(it.get("_bullets_fallback", True)),
            "_why_fallback": bool(it.get("_why_fallback", True)),
        }

    payload = {
        "meta": {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "counts": counts,
            "version": 1,
        },
        "items": [pack(it) for it in items],
    }

    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {p.resolve()}")"""

# ---------- Minimal Entry Schema Helpers ----------

# Map your severities to the "priority" strings you want
_PRIORITY_MAP = {"high": "Hoch", "med": "Mittel", "low": "Niedrig"}


def _iso_to_date_time(iso_str: str) -> tuple[str, str]:
    """
    Split '2025-09-20T15:59:11Z' into ('2025-09-20', '15:59:11').
    Falls back to current UTC if parsing fails.
    """
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat((iso_str or "").replace("Z", "+00:00"))
    except Exception:
        dt = datetime.now(timezone.utc)
    return dt.date().isoformat(), dt.time().strftime("%H:%M:%S")

_PRIORITY_MAP = {"high": "Hoch", "med": "Mittel", "low": "Niedrig"}

def _event_to_tag(evt: str | None) -> str | None:
    m = {
        "central_bank": "Geldpolitik",
        "earnings_surprise": "Ergebnisse",
        "ceo_exit": "Management",
        "mna": "M&A",
        "rating_change": "Analystenrating",
        "dividend_change": "Kapitalrückführungen",
        "bankruptcy": "Insolvenz",
        "regulatory": "Regulierung",
        "sector_shock": "Sektor",
        "other_events": "Sonstiges",
    }
    return m.get((evt or "other_events").lower(), "Sonstiges")


def _first_sentence(text: str, max_len: int = 280) -> str:
    """Take the first sentence-ish chunk, trim to max_len."""
    s = (text or "").strip()
    if not s:
        return ""
    # Split on sentence enders; fallback to slice
    import re
    parts = re.split(r"(?<=[\.\!\?])\s+", s)
    out = parts[0] if parts else s
    return (out[:max_len] + ("…" if len(out) > max_len else ""))
def _shorten_words(s: str, max_words: int = 12, max_chars: int = 90) -> str:
    """Return at most `max_words` words (and <= max_chars), trimmed cleanly."""
    s = (s or "").strip()
    if not s:
        return ""
    words = s.split()
    out = " ".join(words[:max_words]).strip()
    if len(out) > max_chars:
        out = out[:max_chars].rstrip(" ,;:-—–")
    return out.strip(" .:;-–—")

def _sentences(text: str) -> list[str]:
    """Lightweight sentence splitter; keeps only non-empty trimmed sentences."""
    import re
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]

def _clean_prefixes(s: str) -> str:
    """Strip noisy prefixes like 'Antwort:', 'ANTWORT:', 'Zusammenfassung:', etc."""
    import re
    s = (s or "").strip()
    if not s:
        return ""
    # Remove bracketed labels and common noise tokens
    s = re.sub(r"\[(?i:antwort|summary|note|draft)\]\s*", "", s)
    s = re.sub(r"(?i)^(antwort|antw?ort|antwner|zusammenfassung|summary)\s*:\s*", "", s)
    # Collapse duplicated spaces/dashes
    s = re.sub(r"\s+", " ", s).strip(" —–—-")
    return s

def _pick_german_sentence(text: str, fallback: str = "") -> str:
    """Pick the first sentence that looks German; else fallback/first."""
    sents = _sentences(_strip_translation_markup(text))
    for s in sents:
        if _looks_german(s):
            return s
    return fallback or (sents[0] if sents else "")

def _two_sentence_body_draft(body_de: str) -> str:
    """Use first one–two sentences from (German) body for review draft."""
    ss = _sentences(body_de)
    if not ss:
        return ""
    # Join the first two sentences if available.
    draft = " ".join(ss[:2]).strip()
    return draft

def to_minimal_entry(it: dict) -> dict:
    # --- Source & time ---
    source = (it.get("source") or "").strip()
    url = (it.get("url") or "").strip()
    date_str, time_str = _iso_to_date_time(it.get("published_at") or "")
    priority = _PRIORITY_MAP.get((it.get("severity") or "low").lower(), "Niedrig")

    # --- Title: short, clean, German-only ---
    raw_head = (it.get("headline_de") or it.get("headline") or "").strip()
    raw_head = _clean_prefixes(_normalize_headline(raw_head))
    if not _looks_german(raw_head):
        raw_head = _clean_prefixes(_normalize_headline(translate_to_de(raw_head)))

    # pick a single German sentence from (possibly long) headline, then shorten
    title_sentence = _pick_german_sentence(raw_head, fallback=raw_head)
    title = _shorten_words(title_sentence, max_words=12, max_chars=90)

    # --- Summary: longer, from body → DE; fallback to long headline ---
    body = (it.get("body_text") or "").strip()
    summary_long = ""
    if body:
        summary_long = _first_sentence(body)
        if summary_long and not _looks_german(summary_long):
            summary_long = translate_to_de(summary_long)
        summary_long = _clean_prefixes(_strip_translation_markup(summary_long))

    # Fallbacks for summary if body was empty/too short
    if not summary_long or len(summary_long) < 30:
        summary_long = raw_head if raw_head else (it.get("headline") or "")
        if summary_long and not _looks_german(summary_long):
            summary_long = translate_to_de(summary_long)
        summary_long = _clean_prefixes(_strip_translation_markup(summary_long))

    # --- Context (why it matters): sanitize & keep German ---
    context = (it.get("why_it_matters") or "").strip()
    if context and not _looks_german(context):
        context = _strip_translation_markup(translate_to_de(context))
    context = _clean_prefixes(context)

    # Avoid identical summary/context → try a different sentence from the body
    if context:
        eq = summary_long.strip().rstrip(".") == context.strip().rstrip(".")
        subset = summary_long in context or context in summary_long
        if eq or subset:
            body_de = body
            if body_de and not _looks_german(body_de):
                body_de = translate_to_de(body_de)
            body_de = _clean_prefixes(_strip_translation_markup(body_de))
            for s in _sentences(body_de):
                if s.strip() and s.strip().rstrip(".") != context.strip().rstrip("."):
                    summary_long = s
                    break

    # --- Draft text for human review: NOT the same as summary ---
    # Prefer LLM bullets if present
    bullets = it.get("bullets") or []
    bullets = [str(b).strip() for b in bullets if str(b).strip()]
    # Clean bullets a bit
    bullets = [_clean_prefixes(_strip_translation_markup(b)) for b in bullets]
    # Build review draft
    if bullets:
        # Join 2–3 bullets into a short review paragraph
        review = " ".join([b if b.endswith(('.', '!', '?')) else (b + ".") for b in bullets[:3]])
    else:
        # Use two sentences from DE body, else expand summary.
        body_de = body
        if body_de and not _looks_german(body_de):
            body_de = translate_to_de(body_de)
        body_de = _clean_prefixes(_strip_translation_markup(body_de))
        review = _two_sentence_body_draft(body_de) or summary_long

    # Ensure review differs from summary; if equal, append context (if not already)
    if review.strip().rstrip(".") == summary_long.strip().rstrip("."):
        if context and context not in review:
            review = f"{review} — {context}"
        else:
            # Slightly expand by appending a second sentence from body/headline
            extra = ""
            sents = _sentences(body_de if body else raw_head)
            if len(sents) >= 2:
                extra = sents[1]
            if extra and extra not in review:
                review = f"{review} {extra}".strip()

    # Finally, if context exists and is not inside the review, append it
    if context and context not in review:
        review = f"{review} — {context}"

    # --- Tags ---
    tags: list[str] = []
    evt_tag = _event_to_tag(it.get("event_type"))
    if evt_tag:
        tags.append(evt_tag)

    regions = it.get("regions") or []
    if isinstance(regions, str):
        regions = [regions]
    assets = it.get("asset_classes") or []
    if isinstance(assets, str):
        assets = [assets]

    REGION_LABEL = {"US":"USA","EU":"EU","CH":"CH","UK":"UK","JP":"Japan","EM":"Schwellenländer","Global":"Global"}
    ASSET_LABEL  = {"Equity":"Aktien","Rates":"Zinsen","Credit":"Kredit","Commodities":"Rohstoffe","FX":"Devisen"}

    for r in regions:
        rs = str(r).strip()
        if rs:
            tags.append(REGION_LABEL.get(rs, rs))
    for a in assets:
        aa = str(a).strip()
        if aa:
            tags.append(ASSET_LABEL.get(aa, aa))

    # De-duplicate preserving order
    seen = set()
    tags = [t for t in tags if not (t in seen or seen.add(t))]

    return {
        "id": it.get("id"),
        "title": title,            # short, clean, German
        "source": source,
        "url": url,
        "date": date_str,
        "time": time_str,
        "priority": priority,
        "summary": summary_long,   # longer, first-sentence-style, German
        "context": context,        # why it matters (German)
        "draftText": review,       # DIFFERENT from summary; 2–3 bullets/body sentences + why
        "tags": tags,
    }


def write_minimal_entries(items: list[dict], path: str = "out/feed_min.json"):
    """
    Save ONLY the fields the frontend needs:
    [
      { id, title, source, url, date, time, priority, summary, context, draftText, tags },
      ...
    ]
    """
    from pathlib import Path
    import json
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    entries = [to_minimal_entry(it) for it in items]
    p.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved minimal entries: {p.resolve()}")
    return entries

import pathlib, pandas as pd, json
from collections import Counter

# --- Language/cleanup helpers ---

_DE_HINTS = {"der","die","das","und","oder","nicht","mit","ohne","für","über","bei","auf","im","sein","sind","wird","wurden","hat","haben","dass","weil","wenn","kann","können","Zinsen","Ausblick","Ergebnis","Quartal","Guidance"}

def _looks_german(s: str) -> bool:
    s = (s or "").lower()
    if not s: return False
    if any(ch in s for ch in "äöüß"):  # quick win
        return True
    hits = sum(1 for w in re.findall(r"[a-zA-ZäöüÄÖÜß]+", s) if w in _DE_HINTS)
    return hits >= 2

def _shorten_words(s: str, max_words: int = 16, max_chars: int = 90) -> str:
    s = _strip_translation_markup(s or "")
    words = s.split()
    s2 = " ".join(words[:max_words])
    if len(s2) > max_chars:
        s2 = s2[:max_chars].rsplit(" ", 1)[0] + "…"
    return s2.strip(" .:;-–—")

def _strip_translation_markup(s: str) -> str:
    if not s:
        return ""
    s = str(s)

    # strip code fences
    s = re.sub(r"^```(?:json|text)?\s*|\s*```$", "", s, flags=re.DOTALL | re.IGNORECASE)

    # kill common LLM/translator labels at the start (both DE/EN)
    s = re.sub(r"(?im)^\s*(antwort|reply|response|summary|zusammenfassung)\s*:\s*", "", s)
    s = re.sub(r"(?im)^\s*\[(antwort|reply|response|summary)\]\s*:?\s*", "", s)

    # keep only the last block after any ÜBERSETZUNG: markers
    parts = re.split(r"(?i)über(setzung|setzung)\s*:\s*", s)
    if len(parts) >= 3:
        s = parts[-1]

    # remove 'TEXT:' prefix
    s = re.sub(r"(?im)^text\s*:\s*", "", s)

    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _normalize_headline(s: str) -> str:
    """Single-line, no markup, trim trailing punctuation."""
    s = _strip_translation_markup(s)
    # first line / sentence-ish
    s = s.split(" — ")[0].split(" - ")[0].splitlines()[0].strip()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .:;-–—")


def ensure_de_fields(items: List[Dict[str, Any]]) -> None:
    for it in items:
        # --- Headline (German, cleaned) ---
        raw_head = (it.get("headline_de") or it.get("headline") or "").strip()
        head = _normalize_headline(raw_head)
        if not _looks_german(head):
            head = _normalize_headline(translate_to_de(raw_head))
        it["headline_de"] = head or (it.get("headline") or "").strip()

        # --- Why it matters (German) ---
        why = (it.get("why_it_matters") or "").strip()
        if not why:
            base = _first_sentence(it.get("body_text") or it.get("headline") or "")
            why = translate_to_de(base) if base else ""
        elif not _looks_german(why):
            why = translate_to_de(why)
        it["why_it_matters"] = _strip_translation_markup(why)

        # --- Draft one-liner (always rebuild from the two clean pieces) ---
        it["draft_note_de"] = f"{it['headline_de']} — {it['why_it_matters']}".strip(" —")




if __name__ == "__main__":
    out = process(min_score=0.4, with_llm=True)
    c = out["counts"]
    print(f"LLM classify: {c['classified']} items; fallbacks: {c['classify_fallback']}")
    print(f"LLM summarize: {c['summarized']} items; fallbacks: {c['summarize_fallback']}")
    def write_current_perspective(items: list[dict], top_n_per_section: int = 6):
        p = pathlib.Path("out"); p.mkdir(exist_ok=True)
        df = pd.DataFrame(items)

        # If nothing passed the filter, write empty artifacts and return
        if df.empty:
            (p / "brief.md").write_text("# Aktuelle Perspektive — Auto-Entwurf\n", encoding="utf-8")
            pd.DataFrame(columns=[
                "id","published_at","source","company","headline","tickers",
                "event_type","entities","severity","confidence","why_it_matters","url",
                "_classified","_classify_fallback","_llm_conf",
                "_summarized","_summary_fallback","_headline_fallback","_bullets_fallback","_why_fallback"
            ]).to_csv(p / "triage_material.csv", index=False)
            print("Saved: out/brief.md (empty), out/triage_material.csv (empty)")
            return

        # Ensure required columns exist
        required_cols = ["headline","tickers","event_type","entities","severity","confidence","published_at","why_it_matters","url","bullets"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = []  # ok for empty lengths

        # Simple company extractor (no EDGAR patterns)
        def extract_company_from_headline(h: str) -> str:
            h = (h or "").strip()
            if not h:
                return ""
            # Split on common separators: " - ", " — ", ": "
            for sep in [" — ", " - ", ": "]:
                if sep in h:
                    return h.split(sep, 1)[0].strip()
            return h

        # Utility helpers
        def as_list(x):
            if isinstance(x, (list, tuple)): return list(x)
            return [] if x is None or (isinstance(x, float) and pd.isna(x)) else [x]

        def norm_bullets(bul):
            bul = as_list(bul)
            out = []
            for b in bul[:3]:
                b = str(b).replace("·", "-").replace("¬∑", "-").strip()
                if not b: continue
                if not b.endswith("."): b += "."
                out.append(b)
            return out

        def coalesce_why(event_type, why):
            if why is None or (isinstance(why, float) and pd.isna(why)) or not str(why).strip():
                return WHY_DEFAULTS.get(event_type or "other_events", WHY_DEFAULTS["other_events"])
            return str(why).strip()

        # Normalize list/flag columns
        for col in ["entities", "tickers", "bullets"]:
            df[col] = df[col].apply(as_list)

        for flag in ["_summary_fallback","_headline_fallback","_bullets_fallback","_why_fallback","_classify_fallback"]:
            if flag not in df.columns:
                df[flag] = True
            df[flag] = df[flag].fillna(True).astype(bool)

        # Material definition (no EDGAR codes): items that already have tickers OR non-"other_events"
        df["is_material"] = ((df["event_type"].fillna("other_events") != "other_events") | (df["tickers"].apply(bool))).astype(bool)
        df_mat = df[df["is_material"]].copy()

        # Add derived columns
        df_mat["company"] = df_mat["headline"].apply(extract_company_from_headline)
        df_mat["bullets_clean"] = df_mat["bullets"].apply(norm_bullets)

        # Rank: severity -> confidence -> recency
        sev_rank = {"high": 3, "med": 2, "low": 1}
        df_mat["sev_rank"] = df_mat["severity"].str.lower().map(sev_rank).fillna(0)
        df_mat = df_mat.sort_values(by=["sev_rank","confidence","published_at"], ascending=[False, False, False])

        # Sections (event_type driven)
        def ev(e): return (e or "").lower()
        sec_ceo        = df_mat[df_mat["event_type"].apply(lambda e: ev(e) == "ceo_exit")]
        sec_earn       = df_mat[df_mat["event_type"].apply(lambda e: ev(e) == "earnings_surprise")]
        sec_mna        = df_mat[df_mat["event_type"].apply(lambda e: ev(e) == "mna")]
        sec_reg        = df_mat[df_mat["event_type"].apply(lambda e: ev(e) in {"regulatory","non_reliance","auditor_change"})]
        sec_other      = df_mat[~df_mat.index.isin(pd.concat([sec_ceo,sec_earn,sec_mna,sec_reg]).index)]

        sections = [
            ("CEO-/Vorstandswechsel",      sec_ceo),
            ("Ergebnisse/Berichte",        sec_earn),
            ("M&A / Wesentliche Deals",    sec_mna),
            ("Regulatorik / Berichterstattung", sec_reg),
            ("Weitere relevante (Watchlist/News)", sec_other.head(20)),
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
                    evn  = (r.get("event_type") or "other_events").replace("_"," ")
                    sev_map = {"high": "Hoch", "med": "Mittel", "low": "Niedrig"}
                    sev = sev_map.get(str(r.get("severity") or "low").lower(), "Niedrig")

                    comp = r.get("company") or r.get("headline","")
                    f.write(f"\n**{comp}** — {evn}; **{sev}**\n")
                    for b in r.get("bullets_clean") or []:
                        f.write(f"- {b}\n")
                    raw_val = r.get("why_it_matters")
                    is_blank = raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)) or (isinstance(raw_val, str) and not raw_val.strip())
                    why_effective = coalesce_why(r.get("event_type"), raw_val)
                    flag = " (default why)" if is_blank else " (LLM why)"
                    f.write(f"_Warum es wichtig ist{flag}:_ {why_effective}\n")
                    if tick != "n/a":
                        f.write(f"_Ticker:_ {tick}\n")

                    url = r.get("url") or ""
                    if url:
                        f.write(f"[Quelle]({url})\n")

        keep_cols = ["id","published_at","source","company","headline","tickers",
                    "event_type","entities","severity","confidence","why_it_matters","url",
                    "_classified","_classify_fallback","_llm_conf",
                    "_summarized","_summary_fallback","_headline_fallback","_bullets_fallback","_why_fallback"]
        df_mat.reindex(columns=keep_cols).to_csv(p / "triage_material.csv", index=False)
        print("Saved: out/brief.md, out/triage_material.csv")
    write_current_perspective(out["items"])  
    try:
        df_dbg = pd.read_csv(pathlib.Path("out/triage_material.csv"))
        non_fallback_whys = (~df_dbg["_why_fallback"]).sum()
        print(f"non-fallback WHYs in triage_material.csv: {non_fallback_whys} / {len(df_dbg)}")
    except Exception as e:
        print("debug count error:", e)

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

    

   #write_frontend_payload(out["items"], out["counts"], path="out/feed.json")
    _ = write_minimal_entries(out["items"], path="out/feed_min.json")  # <- different filename



    # show where they were written
    import pathlib, os
    out_dir = pathlib.Path("out").resolve()
    print(f"Saved files in {out_dir}")
    print(f" - {out_dir / 'brief.md'}")
    print(f" - {out_dir / 'triage_material.csv'}")