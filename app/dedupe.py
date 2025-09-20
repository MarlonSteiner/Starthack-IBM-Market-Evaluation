from typing import List, Dict, Any, Tuple
from .utils import safe_hash

def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []
    for it in items:
        key = safe_hash(it.get("source",""), it.get("url",""), it.get("headline",""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)
    return deduped
