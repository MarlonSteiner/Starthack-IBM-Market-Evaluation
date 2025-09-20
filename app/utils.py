from typing import Optional, Any, Dict
from datetime import datetime, timezone
import hashlib, re

RFC3339 = "%Y-%m-%dT%H:%M:%S%z"

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

def strip_html(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub("<[^<]+?>", "", s).strip()


import re
_CIK_RE = re.compile(r"/edgar/data/(\d+)/", re.IGNORECASE)

def extract_cik_from_url(url: str) -> str | None:
    m = _CIK_RE.search(url or "")
    if m:
        return m.group(1).lstrip("0")
    return None
