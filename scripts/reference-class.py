"""
THE FIX: forecast the REFERENCE CLASS base rate, not the model's probability.

The logistic model has real RANKING skill (AUPRC lift ~1.5x) but NEGATIVE
probabilistic skill (Brier worse than quoting the base rate). Those are different
things and conflating them is a classic error.

Superforecasters do not use a model's probability. They use it to identify which
reference class a case belongs to, then quote that class's observed frequency.
This tests that directly: bucket by regime type x tenure, compute each bucket's
empirical failure rate on TRAIN only, and use it as the forecast.
"""
import os, re, json, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, average_precision_score

CACHE = 'panel-cache.csv'
if os.path.exists(CACHE):
    df = pd.read_csv(CACHE)
else:
    import pyreadr
    vdem = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
    pitf = pyreadr.read_r('data/democracyData/data/pitf.rda')['pitf']
    gwf  = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']
    spells = []
    for r in gwf[['extended_country_name','gwf_casename','Start','End']].drop_duplicates().itertuples():
        ms, me = re.match(r'^(\d{4})-', str(r.Start)), re.match(r'^(\d{4})-', str(r.End))
        if ms and me: spells.append((r.extended_country_name, int(ms.group(1)), int(me.group(1))))
    sp = pd.DataFrame([dict(country=c, year=y, regime_start=s, regime_end=e)
                       for c, s, e in spells for y in range(s, e+1)]
                      ).drop_duplicates(subset=['country','year'], keep='last')
    sp['years_stable'] = sp.year - sp.regime_start
    sp['fail_2y'] = ((sp.regime_end - sp.year) <= 2).astype(int)
    v = vdem[['country_name','year','e_miferrat']].rename(columns={'country_name':'country'})
    p = pitf[['extended_country_name','year','pitf']].rename(columns={'extended_country_name':'country'})
    for d in (v, p, sp): d['year'] = d['year'].astype(int)
    df = sp.merge(v, on=['country','year'], how='left').merge(p, on=['country','year'], how='left').dropna(subset=['pitf','e_miferrat'])
    df.to_csv(CACHE, index=False)

SPLIT, CAL = 1980, 1995
tr = df.year <= SPLIT; ca = (df.year > SPLIT) & (df.year <= CAL); te = df.year > CAL
base = df.loc[tr, 'fail_2y'].mean()
obs = df.loc[te, 'fail_2y'].values
print(f"train {tr.sum()}  calibrate {ca.sum()}  test {te.sum()}")
print(f"train base rate {base:.4f}   test base rate {obs.mean():.4f}\n")

# ── reference-class buckets ─────────────────────────────────────────────────
def tenure_bucket(v):
    return '0-4' if v < 5 else '5-14' if v < 15 else '15-29' if v < 30 else '30+'
df['tenure'] = df.years_stable.apply(tenure_bucket)
df['refclass'] = df.pitf.astype(str) + ' | ' + df.tenure

rates = df.loc[tr].groupby('refclass').fail_2y.agg(['mean','size'])
SHRINK = 20   # shrink small buckets toward the global base rate
rates['smoothed'] = (rates['mean']*rates['size'] + base*SHRINK) / (rates['size'] + SHRINK)
print("REFERENCE-CLASS FAILURE RATES (train only, shrunk toward base rate)")
print(f"  {'class':46}{'n':>6}{'raw':>9}{'smoothed':>10}")
for k, r in rates.sort_values('smoothed', ascending=False).iterrows():
    print(f"  {k:46}{int(r['size']):6}{r['mean']:9.4f}{r['smoothed']:10.4f}")

p_ref = df.loc[te, 'refclass'].map(rates['smoothed']).fillna(base).values

# ── logistic model for comparison ───────────────────────────────────────────
D = pd.get_dummies(df.pitf, prefix='rg')
FE = list(D.columns) + ['e_miferrat','years_stable']
X = pd.concat([D, df[['e_miferrat','years_stable']]], axis=1)[FE].astype(float).values
m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(X[tr.values], df.loc[tr,'fail_2y'].values)
p_raw = m.predict_proba(X[te.values])[:,1]
iso = IsotonicRegression(out_of_bounds='clip').fit(m.predict_proba(X[ca.values])[:,1], df.loc[ca,'fail_2y'].values)
p_iso = iso.predict(p_raw)

bb = brier_score_loss(obs, np.full(len(obs), base))
print(f"\n{'model':34}{'Brier':>10}{'skill':>10}{'AUPRC':>9}")
out = {}
for name, pr in [('base rate only', np.full(len(obs), base)),
                 ('logistic, raw', p_raw),
                 ('logistic, isotonic', p_iso),
                 ('REFERENCE CLASS', p_ref),
                 ('50/50 refclass + isotonic', 0.5*p_ref + 0.5*p_iso)]:
    b = brier_score_loss(obs, pr); sk = 1 - b/bb
    ap = average_precision_score(obs, pr) if np.std(pr) > 0 else float('nan')
    out[name] = dict(brier=float(b), skill=float(sk), auprc=float(ap))
    print(f"  {name:32}{b:10.5f}{sk:+10.4f}{ap:9.4f}")

best = min(out.items(), key=lambda kv: kv[1]['brier'])
print(f"\n  best: {best[0]}   Brier {best[1]['brier']:.5f}   skill {best[1]['skill']:+.4f}")
print("  (positive skill = beats quoting the overall base rate every time)")
json.dump(out, open('reference-class-results.json','w'), indent=1)
print("\nwrote reference-class-results.json")
