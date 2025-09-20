# view_ranker_weights.py
import joblib, pandas as pd

BUNDLE = joblib.load("models/news_ranker.joblib")
model, cols = BUNDLE["model"], BUNDLE["cols"]

# 1) Raw LR coefficients (log-odds per unit of the feature)
coef = pd.Series(model.coef_[0], index=cols).sort_values(key=lambda s: s.abs(), ascending=False)
print("Raw coefficients (log-odds per unit):")
print(coef.to_string(float_format=lambda x: f"{x:+.3f}"))
print(f"\nIntercept: {model.intercept_[0]:+.3f}")

# 2) Optional: scale by feature std so you can compare effects fairly
try:
    df = pd.read_csv("out/training_events.csv")
    std = df[cols].std(ddof=0).replace(0, 1)
    std_eff = (coef * std).sort_values(key=lambda s: s.abs(), ascending=False)
    print("\nStd-scaled effects (per 1σ increase):")
    print(std_eff.to_string(float_format=lambda x: f"{x:+.3f}"))
except Exception as e:
    print("\n(Std-scaled view skipped — couldn't read out/training_events.csv)", e)
