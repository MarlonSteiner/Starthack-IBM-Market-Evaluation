from typing import Dict, Any, List
from datetime import datetime, timezone
from .schema import NewsItem
from .utils import safe_hash, strip_html, to_rfc3339, extract_cik_from_url
import re, json, pathlib

ITEM_MAP = {
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
    event_type, urgency = None, None
    if found:
        priorities = {"high": 3, "med": 2, "low": 1}
        best = (0, None, None)
        for code in found:
            et, urg = ITEM_MAP.get(code, ("other_events", "low"))
            score = priorities[urg]
            if score > best[0]:
                best = (score, et, urg)
        _, event_type, urgency = best
    return event_type, urgency, found

# Optional: local CIK->ticker map
_MAP_PATH = pathlib.Path(__file__).parent.parent / "data" / "company_tickers.json"
CIK_MAP = {}
try:
    if _MAP_PATH.exists():
        CIK_MAP = json.loads(_MAP_PATH.read_text())
except Exception:
    CIK_MAP = {}


def _base_item(source: str, url: str, headline: str, body: str, published: datetime) -> Dict[str, Any]:
    id_ = safe_hash(source, url, headline)
    return NewsItem(
        id=id_,
        published_at=to_rfc3339(published),
        source=source,
        url=url,
        headline=headline.strip(),
        body_text=strip_html(body)[:8000],
        tickers=[],
        entities=[],
        event_type=None,
        regions=[],
        sectors=[],
        confidence=None,
        urgency=None,
        why_it_matters=None,
        draft_note=None,
        hash=id_,
    ).model_dump()

def normalize_edgar(entry: Dict[str, Any]) -> Dict[str, Any]:
    # entry fields from feedparser for SEC Atom
    url = entry.get("link") or ""
    title = entry.get("title", "SEC Filing")
    summary = entry.get("summary", "")
    published = entry.get("published_parsed")
    if published:
        published_dt = datetime(*published[:6], tzinfo=timezone.utc)
    else:
        published_dt = datetime.now(timezone.utc)
    base = _base_item("sec_edgar", url, title, summary, published_dt)
    et, urg, items = classify_edgar_from_summary(summary or "")
    base["event_type"] = et
    base["urgency"] = urg
    base["entities"] = items
    cik = extract_cik_from_url(url)
    if cik and cik in CIK_MAP:
        base["tickers"] = [CIK_MAP[cik]]
    return base

def normalize_marketaux(item: Dict[str, Any]) -> Dict[str, Any]:
    url = item.get("url", "")
    title = item.get("title", "MarketAux")
    desc = item.get("description", "") or item.get("snippet", "")
    published_str = item.get("published_at") or item.get("updated_at") or ""
    try:
        published_dt = datetime.fromisoformat(published_str.replace("Z","+00:00"))
    except Exception:
        published_dt = datetime.now(timezone.utc)
    base = _base_item("marketaux", url, title, desc, published_dt)
    tickers = item.get("symbols") or item.get("entities") or []
    base["tickers"] = [t.get("symbol") if isinstance(t, dict) else t for t in tickers]
    return base

def normalize_newsapi(article: Dict[str, Any]) -> Dict[str, Any]:
    url = article.get("url", "")
    title = article.get("title", "NewsAPI")
    desc = article.get("description", "") or ""
    content = article.get("content", "") or ""
    combined = (desc + "\n\n" + content).strip()
    published_str = article.get("publishedAt") or ""
    try:
        published_dt = datetime.fromisoformat(published_str.replace("Z","+00:00"))
    except Exception:
        published_dt = datetime.now(timezone.utc)
    source_name = (article.get("source") or {}).get("name") or "newsapi"
    base = _base_item(source_name, url, title, combined, published_dt)
    return base
