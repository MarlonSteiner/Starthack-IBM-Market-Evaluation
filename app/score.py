def score_item(it: dict) -> float:
    s = 0.0
    src = (it.get("source") or "").lower()
    et = (it.get("event_type") or "other_events") or "other_events"
    urg = (it.get("urgency") or "low") or "low"
    headline = (it.get("headline") or "").lower()

    # Source weighting
    if src == "sec_edgar":
        if it["headline"].startswith("8-K"):
            s += 0.6
        elif it["headline"].startswith("10-Q"):
            s += 0.3
        elif it["headline"].startswith("10-K"):
            s += 0.25
    else:
        # generic APIs
        s += 0.3

    # Event type / urgency
    high_events = {"ceo_exit", "bankruptcy", "non_reliance", "earnings_surprise", "mna"}
    med_events = {"guidance_change", "rating_change", "reg_fd", "regulatory_sanction", "geopolitics", "unregistered_sale"}

    if et in high_events:
        s += 0.35
    elif et in med_events:
        s += 0.2

    if urg == "high":
        s += 0.15
    elif urg == "med":
        s += 0.05

    # Keyword nudge
    for kw in ["guidance", "resigns", "resignation", "appointed", "impairment", "non-reliance"]:
        if kw in headline:
            s += 0.05

    # clip
    if s > 1.0:
        s = 1.0
    return s
