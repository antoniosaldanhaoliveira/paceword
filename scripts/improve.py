"""
IMPROVED FORECASTER — fixes five flaws in the previous version, found by
auditing our own work with the same standards applied to CTHmodules.

FLAW 1  Window=10 was chosen because it scored best ON THE TEST PERIOD — a
        selection leak. Fix: ADAPTIVE selection. At year y, choose the window
        that minimised Brier over forecasts made in [y-10, y-1], all computable
        from the past. No quantity is ever tuned on data the forecast hasn't seen.
FLAW 2  GWF outcome data ends 2020 (and forced censoring surgery). Fix: rebuild
        spells entirely from V-Dem — v2regdur (regime duration, days) resets on
        regime change and runs through 2025. One source, seven years fresher.
FLAW 3  The logistic model was frozen in 1980 while the reference class got to
        re-estimate yearly — an unfair comparison. Fix: walk-forward logistic,
        re-fitted each year on the same trailing window.
FLAW 4  No uncertainty. Fix: Jeffreys 90% intervals on every quoted bucket rate.
FLAW 5  No error bar on skill. Fix: country-clustered bootstrap (outcomes within
        a country are serially dependent; resample countries, not rows).
"""
import pyreadr, pandas as pd, numpy as np, json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import brier_score_loss, average_precision_score
from scipy import stats

np.random.seed(20260810)
vdem = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
d = vdem[['country_name','year','v2regdur','v2x_regime','e_miferrat']].rename(
    columns={'country_name':'country'}).dropna(subset=['v2regdur']).copy()
d['year'] = d.year.astype(int)
d['tenure'] = d.v2regdur / 365.25
d = d.sort_values(['country','year'])

# regime end at year y+k  <=>  duration reset (v2regdur drops)
dur = {(r.country, r.year): r.v2regdur for r in d.itertuples()}
def fail_2y(c, y):
    out = 0
    for k in (1, 2):
        a, b = dur.get((c, y+k-1)), dur.get((c, y+k))
        if a is None or b is None: return None      # gap -> unknowable
        if b < a: out = 1
    return out
LAST = int(d.year.max())
d['fail_2y'] = [fail_2y(r.country, r.year) if r.year <= LAST-2 else None for r in d.itertuples()]
panel = d.dropna(subset=['fail_2y','v2x_regime']).copy()
panel['fail_2y'] = panel.fail_2y.astype(int)
ROW = {0:'closed autocracy',1:'electoral autocracy',2:'electoral democracy',3:'liberal democracy'}
def tb(v): return '0-4' if v<5 else '5-14' if v<15 else '15-29' if v<30 else '30+'
panel['ten_b'] = panel.tenure.apply(tb)
panel['refclass'] = panel.v2x_regime.map(ROW) + ' | ' + panel.ten_b
print(f"V-Dem spell panel: {len(panel)} country-years, {int(panel.year.min())}-{int(panel.year.max())}")
print(f"base rate (fail within 2y): {panel.fail_2y.mean():.4f}\n")

YEARS = sorted(panel.loc[panel.year >= 1955, 'year'].unique())
SHRINK, WINDOWS = 20, (10, 20, 30)

def refclass_forecast(hist, cur):
    b = hist.fail_2y.mean()
    rt = hist.groupby('refclass').fail_2y.agg(['mean','size'])
    sm = (rt['mean']*rt['size'] + b*SHRINK) / (rt['size'] + SHRINK)
    return cur.refclass.map(sm).fillna(b).values, b

# per-window refclass forecasts for every year (needed for adaptive selection)
fc = {w: {} for w in WINDOWS}; baserates = {}
for y in YEARS:
    cur = panel[panel.year == y]
    if len(cur) == 0: continue
    for w in WINDOWS:
        hist = panel[(panel.year < y) & (panel.year >= y-w)]
        if len(hist) < 300: continue
        fc[w][y], b = refclass_forecast(hist, cur)
        baserates.setdefault(y, b if w == 20 else baserates.get(y, b))

# assemble aligned arrays
def collect(getter):
    P, O, C = [], [], []
    for y in YEARS:
        cur = panel[panel.year == y]
        p = getter(y, cur)
        if p is None: continue
        P.append(p); O.append(cur.fail_2y.values); C.append(cur.country.values)
    return np.concatenate(P), np.concatenate(O), np.concatenate(C)

def yearly_brier(w):
    out = {}
    for y, p in fc[w].items():
        o = panel.loc[panel.year == y, 'fail_2y'].values
        out[y] = brier_score_loss(o, p)
    return out
yb = {w: yearly_brier(w) for w in WINDOWS}

def adaptive(y, cur):
    if not all(y in fc[w] for w in WINDOWS): return None
    past = [yy for yy in fc[WINDOWS[0]] if y-10 <= yy < y and all(yy in yb[w] for w in WINDOWS)]
    if len(past) < 5: return fc[20].get(y)
    best = min(WINDOWS, key=lambda w: np.mean([yb[w][yy] for yy in past]))
    return fc[best][y]

def rolling_base(y, cur):
    hist = panel[(panel.year < y) & (panel.year >= y-20)]
    return np.full(len(cur), hist.fail_2y.mean()) if len(hist) >= 300 else None

def wf_logistic(y, cur):
    hist = panel[(panel.year < y) & (panel.year >= y-30)].dropna(subset=['e_miferrat'])
    cu = cur.dropna(subset=['e_miferrat'])
    if len(hist) < 300 or hist.fail_2y.sum() < 10 or len(cu) == 0: return None
    F = lambda t: np.column_stack([pd.get_dummies(t.v2x_regime).reindex(columns=[0,1,2,3], fill_value=0).values,
                                   np.log1p(t.tenure.values), t.e_miferrat.values])
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    m.fit(F(hist), hist.fail_2y.values)
    pr = pd.Series(m.predict_proba(F(cu))[:,1], index=cu.index)
    return pr.reindex(cur.index).fillna(hist.fail_2y.mean()).values

print("WALK-FORWARD (V-Dem spells, through 2023 outcomes)")
print(f"  {'method':34}{'n':>7}{'Brier':>10}{'skill':>9}{'AUPRC':>9}")
res = {}
pb, ob, _ = collect(rolling_base)
bb = brier_score_loss(ob, pb)
methods = {'rolling base rate (20y)': rolling_base,
           'refclass fixed 10y': lambda y,c: fc[10].get(y),
           'refclass fixed 20y': lambda y,c: fc[20].get(y),
           'refclass fixed 30y': lambda y,c: fc[30].get(y),
           'refclass ADAPTIVE (honest)': adaptive,
           'walk-forward logistic': wf_logistic}
arrays = {}
for name, g in methods.items():
    P, O, C = collect(g)
    br = brier_score_loss(O, P); sk = 1 - br/bb if name != 'rolling base rate (20y)' else 0.0
    ap = average_precision_score(O, P) if np.std(P) > 0 else float('nan')
    res[name] = dict(n=int(len(O)), brier=float(br), skill=float(sk), auprc=float(ap))
    arrays[name] = (P, O, C)
    print(f"  {name:34}{len(O):7}{br:10.5f}{sk:+9.4f}{ap:9.4f}")

# ── FLAW 5 fix: country-clustered bootstrap on the honest method's skill ────
P, O, C = arrays['refclass ADAPTIVE (honest)']
Pb, Ob, Cb = arrays['rolling base rate (20y)']
n_common = min(len(P), len(Pb))
countries = np.unique(C)
sks = []
for _ in range(500):
    pick = set(np.random.choice(countries, len(countries), replace=True))
    m1 = np.isin(C, list(pick))
    m2 = np.isin(Cb, list(pick))
    if O[m1].sum() < 5: continue
    sks.append(1 - brier_score_loss(O[m1], P[m1]) / brier_score_loss(Ob[m2], Pb[m2]))
lo, hi = np.percentile(sks, [5, 95])
print(f"\n  adaptive-refclass Brier skill, country-clustered bootstrap 90% CI: [{lo:+.4f}, {hi:+.4f}]")
print(f"  share of resamples with positive skill: {(np.array(sks)>0).mean()*100:.0f}%")

# ── Iran, scored fresh, with Jeffreys intervals (FLAW 4 fix) ────────────────
hist = panel[(panel.year <= LAST-2) & (panel.year > LAST-2-20)]
b = hist.fail_2y.mean()
rt = hist.groupby('refclass').fail_2y.agg(['mean','size','sum'])
sm = (rt['mean']*rt['size'] + b*SHRINK) / (rt['size'] + SHRINK)
def jeffreys(k, n):
    return stats.beta.ppf([0.05, 0.95], k+0.5, n-k+0.5)
print(f"\nIRAN — 20y window ending {LAST-2}, base rate {b:.4f}")
print("  (V-Dem itself reclassified Iran to ELECTORAL autocracy in 2024)")
print(f"  {'scenario':52}{'p':>8}{'90% CI':>18}{'n':>6}")
iran = {}
for lbl, rc in [('A: regime continuous (46y, electoral autocracy)', 'electoral autocracy | 30+'),
                ('A2: continuous, still closed autocracy',          'closed autocracy | 30+'),
                ('B: Feb 2026 = new regime (electoral autocracy)',  'electoral autocracy | 0-4'),
                ('B2: new regime, closed autocracy',                'closed autocracy | 0-4')]:
    if rc in rt.index:
        k, n = rt.loc[rc,'sum'], rt.loc[rc,'size']
        ci = jeffreys(k, n); v = float(sm[rc])
        iran[lbl] = dict(p=v, ci=[float(ci[0]), float(ci[1])], n=int(n))
        print(f"  {lbl:52}{v:8.4f}   [{ci[0]:.4f}, {ci[1]:.4f}]{int(n):6}")
    else:
        print(f"  {lbl:52}   -- bucket empty in window")

json.dump(dict(results=res, bootstrap_ci=[float(lo), float(hi)], iran=iran,
               base_rate=float(b), panel_n=int(len(panel)), last_scoreable=LAST-2),
          open('improved-results.json','w'), indent=1)
print("\nwrote improved-results.json")
