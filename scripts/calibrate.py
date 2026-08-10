"""
SUPERFORECASTER TECHNIQUES, APPLIED.

A statistical model cannot be a superforecaster - superforecasting is a process
involving frequent updating on news the model never sees. But three of the things
that make superforecasters good ARE mechanisable, and none of them were in the
model as built:

  1. CALIBRATION  - when it says 8%, does it happen 8% of the time?
  2. EXTREMIZING  - Good Judgment found aggregated forecasts are underconfident;
                    pushing them away from the base rate improves Brier.
  3. PROPER SCORING - Brier decomposed into reliability / resolution / uncertainty,
                    so you know WHICH part is failing.

All evaluated out-of-sample on a temporal split.
"""
import pyreadr, numpy as np, pandas as pd, re, json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, average_precision_score

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

D = pd.get_dummies(df.pitf, prefix='rg')
FE = list(D.columns) + ['e_miferrat','years_stable']
X = pd.concat([D, df[['e_miferrat','years_stable']]], axis=1)[FE].astype(float).values
y = df.fail_2y.values; yr = df.year.values

SPLIT, CAL = 1980, 1995          # train <=1980; calibrate 1981-1995; test >1995
tr, ca, te = yr <= SPLIT, (yr > SPLIT) & (yr <= CAL), yr > CAL
m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
m.fit(X[tr], y[tr])
p_ca, p_te = m.predict_proba(X[ca])[:,1], m.predict_proba(X[te])[:,1]
base = y[te].mean()
print(f"train {tr.sum()} (<={SPLIT})  calibrate {ca.sum()}  test {te.sum()} (>{CAL})")
print(f"test base rate: {base:.4f}\n")

def brier_decomp(pred, obs, bins=10):
    """Brier = reliability - resolution + uncertainty (Murphy decomposition)."""
    edges = np.linspace(0, 1, bins+1); n = len(obs); obar = obs.mean()
    rel = res = 0.0
    rows = []
    for i in range(bins):
        m_ = (pred >= edges[i]) & (pred < edges[i+1] if i < bins-1 else pred <= 1)
        if m_.sum() == 0: continue
        fk, ok, nk = pred[m_].mean(), obs[m_].mean(), m_.sum()
        rel += nk*(fk-ok)**2; res += nk*(ok-obar)**2
        rows.append((edges[i], edges[i+1], nk, fk, ok))
    return rel/n, res/n, obar*(1-obar), rows

print("RELIABILITY — does 'x%' actually happen x% of the time?  (raw model, test set)")
rel, res, unc, rows = brier_decomp(p_te, y[te])
print(f"  {'bin':>12}{'n':>7}{'predicted':>11}{'observed':>10}{'gap':>9}")
for lo, hi, nk, fk, ok in rows:
    print(f"  {lo:.2f}-{hi:.2f}{nk:7}{fk:11.4f}{ok:10.4f}{ok-fk:+9.4f}")
print(f"\n  Brier {brier_score_loss(y[te], p_te):.5f} = reliability {rel:.5f} - resolution {res:.5f} + uncertainty {unc:.5f}")
print(f"  (lower reliability is better; higher resolution is better)")

# ── isotonic recalibration, fitted on the calibration window only ────────────
iso = IsotonicRegression(out_of_bounds='clip').fit(p_ca, y[ca])
p_iso = iso.predict(p_te)

# ── extremizing: push away from the base rate in log-odds ───────────────────
def extremize(p, a, anchor):
    p = np.clip(p, 1e-6, 1-1e-6); an = np.clip(anchor, 1e-6, 1-1e-6)
    lo = np.log(p/(1-p)); la = np.log(an/(1-an))
    return 1/(1+np.exp(-(la + a*(lo-la))))

print("\nSCORING VARIANTS (test set, >1995)")
print(f"  {'model':34}{'Brier':>10}{'skill vs base':>15}{'AUPRC':>9}")
bb = brier_score_loss(y[te], np.full(te.sum(), base))
cands = {'base rate only': np.full(te.sum(), base), 'raw model': p_te, 'isotonic recalibrated': p_iso}
for a in (1.5, 2.0, 2.5):
    cands[f'extremized a={a} (on recalibrated)'] = extremize(p_iso, a, base)
out = {}
for name, pr in cands.items():
    b = brier_score_loss(y[te], pr); sk = 1 - b/bb
    ap = average_precision_score(y[te], pr) if pr.std() > 0 else float('nan')
    out[name] = dict(brier=float(b), skill=float(sk), auprc=float(ap))
    print(f"  {name:34}{b:10.5f}{sk:+15.4f}{ap:9.4f}")

best = min(out.items(), key=lambda kv: kv[1]['brier'])
print(f"\n  best: {best[0]}  (Brier {best[1]['brier']:.5f}, skill {best[1]['skill']:+.4f} vs base rate)")
print("\n  Brier skill > 0 means it beats simply quoting the base rate every time.")
json.dump(out, open('calibration-results.json','w'), indent=1)
print("wrote calibration-results.json")
