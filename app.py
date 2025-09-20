# app.py
import os
import time
import json
import pandas as pd
import streamlit as st

# Import your pipeline (make sure pipeline.py is in the same folder)
from pipeline import process

from dotenv import load_dotenv
load_dotenv()  # loads .env from the project root


# ---------- Page setup ----------
st.set_page_config(page_title="Market News Monitor", layout="wide")
st.title("📈 Market News Monitor")

# ---------- Sidebar controls ----------
st.sidebar.header("Filters")
min_score = st.sidebar.slider("Minimum confidence score", 0.0, 1.0, 0.40, 0.05)
only_high = st.sidebar.checkbox("Show only High severity", False)
query = st.sidebar.text_input("Search in headlines (optional)", value="")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Tip: If it ever seems stuck, your network or a source may be slow. "
    "This app fails fast and caches results for snappy reloads."
)

# ---------- Data fetch (cached) ----------
@st.cache_data(ttl=300, show_spinner=False)  # cache for 5 minutes
def run_pipeline_cached(_min_score: float):
    t0 = time.perf_counter()
    result = process(min_score=_min_score, with_llm=True)
    elapsed = time.perf_counter() - t0
    return result, elapsed

with st.status("Fetching news…", expanded=True) as status:
    st.write(f"Calling pipeline.process(min_score={min_score:.2f})")
    try:
        result, elapsed_s = run_pipeline_cached(min_score)
        st.write(f"Done in {elapsed_s:.2f}s. Items: {len(result.get('items', []))}")
        status.update(label="Fetch complete ✅", state="complete")
    except Exception as e:
        status.update(label="Fetch failed ❌", state="error")
        st.exception(e)
        st.stop()

items = result.get("items", [])
df = pd.DataFrame(items)

# ---------- Apply UI filters ----------
if only_high and not df.empty:
    df = df[df["severity"] == "high"]

if query and not df.empty:
    q = query.lower().strip()
    df = df[df["headline"].str.lower().str.contains(q, na=False)]

# ---------- Summary / KPIs ----------
st.subheader("Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("SEC (EDGAR)", result["counts"].get("sec_edgar", 0))
c2.metric("MarketAux", result["counts"].get("marketaux", 0))
c3.metric("NewsAPI", result["counts"].get("newsapi", 0))
c4.metric("Total (deduped)", result["counts"].get("total_deduped", 0))
c5.metric("Relevant (scored)", result["counts"].get("relevant", 0))

with st.expander("Raw counts JSON"):
    st.json(result["counts"])

# ---------- News Feed Table ----------
st.subheader("News Feed")

display_cols = [
    "published_at", "source", "headline", "tickers",
    "event_type", "urgency", "severity", "confidence",
    "why_it_matters", "url",
]

if df.empty:
    st.info("No items match your filters. Try lowering the minimum score or clearing the search.")
else:
    # Keep only columns that exist (in case some are missing)
    cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

# ---------- Top Briefs ----------
st.subheader("Top Briefs")
if df.empty:
    st.caption("No briefs to show.")
else:
    for _, row in df.head(10).iterrows():
        tickers = ", ".join(row.get("tickers") or [])
        st.markdown(f"**{row.get('headline','')}** {'('+tickers+')' if tickers else ''}")
        st.caption(
            f"Severity: {str(row.get('severity','')).title()} · "
            f"Source: {row.get('source','')} · "
            f"Score: {row.get('confidence',0):.2f}"
        )
        if row.get("why_it_matters"):
            st.write(row["why_it_matters"])
        if row.get("url"):
            st.markdown(f"[Read more]({row['url']})")
        st.divider()

# ---------- Downloads ----------
st.subheader("Export")
csv_bytes = df.to_csv(index=False).encode("utf-8")
json_bytes = json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8")

col_a, col_b = st.columns(2)
col_a.download_button(
    "⬇️ Download CSV",
    data=csv_bytes,
    file_name="news_feed.csv",
    mime="text/csv",
)
col_b.download_button(
    "⬇️ Download JSON",
    data=json_bytes,
    file_name="news_feed.json",
    mime="application/json",
)

# ---------- Diagnostics ----------
with st.expander("Diagnostics"):
    st.write(f"Cached: yes (TTL 300s)")
    st.write(f"Last fetch time: {elapsed_s:.2f}s")
    st.write(f"Rows after filters: {len(df)}")
