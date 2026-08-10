"""
A WORKING FORECASTER — the constructive counterpart to the audit.

Rebuilds the Baillie et al. (2021) minimal design from data reachable here, and
validates it the way a forecasting model must be validated: on the future.

UNIT       country-year
OUTCOME    does the incumbent regime end within the next 2 years?  (GWF end-dates)
PREDICTORS 1. PITF regime type      - Goldstone's strongest variable, 5 categories
           2. fertility rate         - proxy for infant mortality; same underlying
                                       construct (demographic transition / state capacity)
           3. years of stability     - years since the incumbent regime began
           (+ log GDP per capita, tested as a 4th)
VALIDATION temporal split. Train on <=1990, test on >1990. No shuffling: a model
           that cannot predict years it never saw is not a forecaster.
METRIC     AUPRC against the base rate. Accuracy is meaningless for rare events.
"""
import pyreadr, numpy as np, pandas as pd, re, json
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

vdem = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
pitf = pyreadr.read_r('data/democracyData/data/pitf.rda')['pitf']
gwf  = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']

# ── regime spells and end years ─────────────────────────────────────────────
spells = []
for r in gwf[['extended_country_name','gwf_casename','Start','End']].drop_duplicates().itertuples():
    ms, me = re.match(r'^(\d{4})-', str(r.Start)), re.match(r'^(\d{4})-', str(r.End))
    if ms and me: spells.append((r.extended_country_name, int(ms.group(1)), int(me.group(1))))
print(f"GWF regime spells: {len(spells)}")

rows = []
for c, s, e in spells:
    for y in range(s, e+1):
        rows.append(dict(country=c, year=y, regime_start=s, regime_end=e))
spell_df = pd.DataFrame(rows).drop_duplicates(subset=['country','year'], keep='last')
spell_df['years_stable'] = spell_df.year - spell_df.regime_start
spell_df['fail_2y'] = ((spell_df.regime_end - spell_df.year) <= 2).astype(int)

# ── join predictors ─────────────────────────────────────────────────────────
v = vdem[['country_name','year','e_miferrat','e_gdppc']].rename(columns={'country_name':'country'})
p = pitf[['extended_country_name','year','pitf']].rename(columns={'extended_country_name':'country'})
for d in (v, p, spell_df): d['year'] = d['year'].astype(int)

df = spell_df.merge(v, on=['country','year'], how='left').merge(p, on=['country','year'], how='left')
df = df.dropna(subset=['pitf','e_miferrat'])
df['log_gdppc'] = np.log(df.e_gdppc.where(df.e_gdppc > 0))
print(f"country-years with full predictors: {len(df)}  ({int(df.year.min())}-{int(df.year.max())})")
print(f"base rate of regime failure within 2y: {df.fail_2y.mean():.4f}  ({df.fail_2y.sum()} events)")

D = pd.get_dummies(df.pitf, prefix='rg')
FEATS_MIN = list(D.columns) + ['e_miferrat', 'years_stable']
FEATS_GDP = FEATS_MIN + ['log_gdppc']
X = pd.concat([D, df[['e_miferrat','years_stable','log_gdppc']]], axis=1)
X['log_gdppc'] = X.log_gdppc.fillna(X.log_gdppc.median())
y = df.fail_2y.values
yr = df.year.values

def evaluate(feats, split, label):
    tr, te = yr <= split, yr > split
    if te.sum() < 50 or y[te].sum() < 5: return None
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    m.fit(X.loc[tr, feats].astype(float), y[tr])
    pr = m.predict_proba(X.loc[te, feats].astype(float))[:, 1]
    base = y[te].mean()
    ap, auc = average_precision_score(y[te], pr), roc_auc_score(y[te], pr)
    print(f"  {label:34}{int(tr.sum()):7}{int(te.sum()):7}{base:9.4f}{ap:9.4f}{auc:8.3f}{ap/base:8.2f}x")
    return dict(label=label, n_train=int(tr.sum()), n_test=int(te.sum()),
                base_rate=float(base), auprc=float(ap), auroc=float(auc), lift=float(ap/base))

print(f"\n{'':36}{'train':>7}{'test':>7}{'base':>9}{'AUPRC':>9}{'AUROC':>8}{'lift':>8}")
results = []
for split in (1970, 1980, 1990, 2000):
    r = evaluate(FEATS_MIN, split, f"3 predictors, train<={split}")
    if r: results.append(r)
print()
for split in (1980, 1990, 2000):
    r = evaluate(FEATS_GDP, split, f"+ log GDPpc,  train<={split}")
    if r: results.append(r)

# ── which variable carries the weight? ──────────────────────────────────────
tr = yr <= 1990
m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
m.fit(X.loc[tr, FEATS_MIN].astype(float), y[tr])
coef = m[-1].coef_[0]
print("\nSTANDARDISED COEFFICIENTS (train<=1990, 3-predictor model)")
for f, c in sorted(zip(FEATS_MIN, coef), key=lambda t: -abs(t[1])):
    print(f"  {f:28}{c:+8.4f}")

json.dump(results, open('forecaster-results.json','w'), indent=1)
print("\nwrote forecaster-results.json")
