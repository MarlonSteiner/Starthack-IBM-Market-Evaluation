# ranker.py
import os, json, joblib, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

MODEL_PATH = Path("models/news_ranker.joblib")
MODEL_PATH.parent.mkdir(exist_ok=True)

WATCHLIST = {"FDX","NVDA","INTC","CRWD","AMD","AAPL","MSFT","GOOGL","AMZN","TSLA"}

def _hours_old(iso: str) -> float:
    try:
        dt = datetime.fromisoformat(iso.replace("Z","+00:00"))
        now = datetime.now(timezone.utc)
        return max(0.0, (now - dt).total_seconds()/3600.0)
    except Exception:
        return 0.0

def build_features(items: List[Dict[str,Any]]) -> pd.DataFrame:
    rows = []
    for it in items:
        src = (it.get("source","") or "").lower()
        head = it.get("headline") or ""
        et = (it.get("event_type") or "other_events")
        urg = (it.get("urgency") or "low")
        kw_list = ("guidance","resigns","resignation","appointed","impairment",
                   "non-reliance","acquisition","merger","downgrade","upgrade","beats","misses")
        kw_hits = sum(kw in head.lower() for kw in kw_list)
        ticks = set(it.get("tickers") or [])
        rows.append(dict(
            _id = it.get("id"),
            sec_8k  = int(src=="sec_edgar" and head.startswith("8-K")),
            sec_10q = int(src=="sec_edgar" and head.startswith("10-Q")),
            sec_10k = int(src=="sec_edgar" and head.startswith("10-K")),
            tier1   = int(any(d in src for d in ("reuters","bloomberg","wsj","ft","cnbc","marketwatch"))),
            urg_high= int(urg=="high"),
            urg_med = int(urg=="med"),
            kw_hits = kw_hits,
            has_tickers = int(bool(ticks)),
            on_watch    = int(bool(ticks & WATCHLIST)),
            llm_conf    = float(it.get("_llm_conf") or 0.5),
            hours_old   = _hours_old(it.get("published_at","") or "1970-01-01T00:00:00Z"),
            event       = et,
            y           = it.get("label")  # optional, for training rows you’ll fill later
        ))
    df = pd.DataFrame(rows)
    # one-hot events
    for ev in df["event"].fillna("other_events").unique():
        df[f"ev_{ev}"] = (df["event"]==ev).astype(int)
    df = df.drop(columns=["event"])
    return df

def fit_from_csv(csv_path: str, out_path: str = str(MODEL_PATH)) -> dict:
    df = pd.read_csv(csv_path)
    y = df["y"].astype(int).values

    X = df.drop(columns=["_id","y"])
    # Drop leaky columns
    drop_cols = [c for c in X.columns if c.startswith("ev_")] + ["urg_high","urg_med"]
    X = X.drop(columns=drop_cols, errors="ignore")

    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    roc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc").mean()
    pr  = cross_val_score(model, X, y, cv=cv, scoring="average_precision").mean()
    model.fit(X, y)
    joblib.dump({"model": model, "cols": list(X.columns)}, out_path)
    return {"roc_auc": float(roc), "pr_auc": float(pr), "path": out_path}


def infer_scores(items: List[Dict[str,Any]], model_path: str = str(MODEL_PATH)) -> Dict[str, float]:
    """Return dict id -> probability (0..1). If model missing, return {}."""
    if not os.path.exists(model_path):
        return {}
    bundle = joblib.load(model_path)
    model, cols = bundle["model"], bundle["cols"]
    df = build_features(items)
    if not len(df):
        return {}
    # align columns
    for c in cols:
        if c not in df.columns:
            df[c] = 0
    X = df[cols]
    proba = model.predict_proba(X)[:,1]
    return dict(zip(df["_id"].tolist(), proba))

def append_training_rows(items: List[Dict[str,Any]], csv_out: str = "out/training_events.csv") -> None:
    """Dump feature rows with y missing; you’ll label later (click/keep/etc.)."""
    df = build_features(items)
    # Don’t overwrite labels if the row already exists
    p = Path(csv_out)
    if p.exists():
        old = pd.read_csv(p)
        merged = pd.concat([old, df], ignore_index=True).drop_duplicates(subset=["_id"], keep="first")
        merged.to_csv(p, index=False)
    else:
        df.to_csv(p, index=False)


def label_from_triage(training_csv="out/training_events.csv",
                      triage_csv="out/triage_material.csv") -> float:
    import pandas as pd, os
    if not os.path.exists(training_csv):
        raise FileNotFoundError(f"{training_csv} not found. Run the pipeline first.")
    if not os.path.exists(triage_csv):
        raise FileNotFoundError(f"{triage_csv} not found. Ensure write_current_perspective() exported it.")

    train = pd.read_csv(training_csv)
    tri   = pd.read_csv(triage_csv)
    if "id" not in tri.columns:
        raise KeyError("Column 'id' missing in triage_material.csv. Add 'id' to keep_cols in write_current_perspective().")

    pos_ids = set(tri["id"])
    train = train.drop_duplicates(subset=["_id"], keep="first").copy()
    train["y"] = train["_id"].isin(pos_ids).astype(int)
    train.to_csv(training_csv, index=False)
    pr = float(train["y"].mean())
    print("Positive rate:", round(pr, 3))
    return pr

def show_weights(model_path=str(MODEL_PATH), top=40):
    import joblib, pandas as pd, numpy as np, os
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"{model_path} not found. Train the model first with fit_from_csv().")
    bundle = joblib.load(model_path)
    coefs = pd.Series(bundle["model"].coef_[0], index=bundle["cols"])
    out = pd.DataFrame({"coef": coefs, "odds_ratio": np.exp(coefs)}) \
            .sort_values("coef", key=lambda s: s.abs(), ascending=False)
    print(out.head(top).to_string())
    return out

