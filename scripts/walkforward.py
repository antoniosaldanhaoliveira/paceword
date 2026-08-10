"""
THE REAL PROBLEM IS NON-STATIONARITY, NOT THE MODEL.

train base rate 0.0609  ->  test base rate 0.0828

A model fitted on a 6.1% world, scored in an 8.3% world, is miscalibrated before
it says anything. Meanwhile the reference classes span 100x in-sample (0.2% for
an old full democracy, 21% for a young factionalised partial democracy), so real
structure clearly exists — it just gets swamped by drift when you freeze the
training window in 1980.

The fix is what forecasters actually do: WALK FORWARD. For every test year,
re-estimate from a rolling window of only prior years. No frozen model, no
leakage. This is also a superforecaster principle — recency-weighted outside view.
"""
import pandas as pd, numpy as np, json
from sklearn.metrics import brier_score_loss, average_precision_score

df = pd.read_csv('panel-cache.csv')
def tenure_bucket(v): return '0-4' if v < 5 else '5-14' if v < 15 else '15-29' if v < 30 else '30+'
df['tenure'] = df.years_stable.apply(tenure_bucket)
df['refclass'] = df.pitf.astype(str) + ' | ' + df.tenure

YEARS = sorted(df.loc[df.year > 1960, 'year'].unique())
SHRINK = 20

def walk(window):
    P_glob, P_ref, OBS = [], [], []
    for y in YEARS:
        hist = df[(df.year < y) & (df.year >= y - window)]
        cur  = df[df.year == y]
        if len(hist) < 200 or len(cur) == 0: continue
        b = hist.fail_2y.mean()
        rates = hist.groupby('refclass').fail_2y.agg(['mean','size'])
        sm = (rates['mean']*rates['size'] + b*SHRINK) / (rates['size'] + SHRINK)
        P_glob.append(np.full(len(cur), b))
        P_ref.append(cur.refclass.map(sm).fillna(b).values)
        OBS.append(cur.fail_2y.values)
    return np.concatenate(P_glob), np.concatenate(P_ref), np.concatenate(OBS)

print(f"walk-forward over {YEARS[0]}-{YEARS[-1]}, re-estimated every year from prior data only\n")
print(f"  {'window':>8}{'n':>7}{'base rate':>11}{'Brier(rolling base)':>21}{'Brier(ref class)':>18}{'skill':>9}{'AUPRC':>9}")
results = {}
for w in (10, 15, 20, 30, 50):
    pg, pr, ob = walk(w)
    bg, br = brier_score_loss(ob, pg), brier_score_loss(ob, pr)
    sk = 1 - br/bg
    ap = average_precision_score(ob, pr)
    results[f'window_{w}'] = dict(n=int(len(ob)), brier_base=float(bg), brier_ref=float(br),
                                  skill=float(sk), auprc=float(ap), base_rate=float(ob.mean()))
    print(f"  {w:8}{len(ob):7}{ob.mean():11.4f}{bg:21.5f}{br:18.5f}{sk:+9.4f}{ap:9.4f}")

best_w = max(results.items(), key=lambda kv: kv[1]['skill'])
print(f"\n  best window: {best_w[0].split('_')[1]} years   Brier skill {best_w[1]['skill']:+.4f}")

# reliability of the winning configuration
w = int(best_w[0].split('_')[1])
pg, pr, ob = walk(w)
print(f"\nRELIABILITY of the rolling reference-class forecast ({w}-year window)")
edges = [0, .02, .05, .10, .20, 1.01]
print(f"  {'bin':>12}{'n':>7}{'predicted':>11}{'observed':>10}{'gap':>9}")
for i in range(len(edges)-1):
    m = (pr >= edges[i]) & (pr < edges[i+1])
    if m.sum() < 20: continue
    print(f"  {edges[i]:.2f}-{edges[i+1]:.2f}{m.sum():7}{pr[m].mean():11.4f}{ob[m].mean():10.4f}{ob[m].mean()-pr[m].mean():+9.4f}")

json.dump(results, open('walkforward-results.json','w'), indent=1)
print("\nwrote walkforward-results.json")
