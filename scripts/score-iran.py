"""
APPLY the forecaster to Iran, and show why the answer depends on one judgement call.
Trains on everything through 2020, then scores Iran under two readings of 2026.
"""
import pyreadr, numpy as np, pandas as pd, re, json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

vdem = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
pitf = pyreadr.read_r('data/democracyData/data/pitf.rda')['pitf']
gwf  = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']

spells = []
for r in gwf[['extended_country_name','gwf_casename','Start','End']].drop_duplicates().itertuples():
    ms, me = re.match(r'^(\d{4})-', str(r.Start)), re.match(r'^(\d{4})-', str(r.End))
    if ms and me: spells.append((r.extended_country_name, int(ms.group(1)), int(me.group(1))))
rows = [dict(country=c, year=y, regime_start=s, regime_end=e)
        for c, s, e in spells for y in range(s, e+1)]
sp = pd.DataFrame(rows).drop_duplicates(subset=['country','year'], keep='last')
sp['years_stable'] = sp.year - sp.regime_start
sp['fail_2y'] = ((sp.regime_end - sp.year) <= 2).astype(int)

v = vdem[['country_name','year','e_miferrat']].rename(columns={'country_name':'country'})
p = pitf[['extended_country_name','year','pitf']].rename(columns={'extended_country_name':'country'})
for d in (v, p, sp): d['year'] = d['year'].astype(int)
df = sp.merge(v, on=['country','year'], how='left').merge(p, on=['country','year'], how='left')
df = df.dropna(subset=['pitf','e_miferrat'])

D = pd.get_dummies(df.pitf, prefix='rg')
CATS = list(D.columns)
FE = CATS + ['e_miferrat','years_stable']
X = pd.concat([D, df[['e_miferrat','years_stable']]], axis=1)[FE].astype(float)
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
model.fit(X, df.fail_2y.values)
print(f"trained on {len(df)} country-years, base rate {df.fail_2y.mean():.4f}")

# Iran's own values
ir_f = vdem[(vdem.country_name=='Iran') & (vdem.year==2025)].e_miferrat
fert = float(ir_f.iloc[0]) if len(ir_f) and ir_f.iloc[0]==ir_f.iloc[0] else float(vdem.e_miferrat.median())
print(f"Iran fertility (V-Dem 2025): {fert:.3f}")
print("Iran PITF regime type (through 2018): 0-Full autocracy")
print("Islamic Republic per GWF: party-based, began 1979-01-16\n")

def score(regime, years_stable, note):
    row = {c: 0.0 for c in CATS}
    key = [c for c in CATS if c.endswith(regime)]
    if key: row[key[0]] = 1.0
    row['e_miferrat'] = fert; row['years_stable'] = float(years_stable)
    pr = model.predict_proba(pd.DataFrame([row])[FE].astype(float))[0,1]
    print(f"  {note:52} p(regime ends within 2y) = {pr:.4f}")
    return float(pr)

print("SCENARIO A — treat the Islamic Republic as continuous since 1979")
a = score('0-Full autocracy', 2026-1979, "47 years of accumulated stability")

print("\nSCENARIO B — treat Feb 2026 (leader killed, contested succession) as a regime break")
b = score('0-Full autocracy', 0, "years_stable reset to 0")
b1 = score('1-Partial autocracy', 0, "and reclassified as partial autocracy")
b2 = score('2-Partial democracy with factionalism', 0, "or as factionalised partial democracy")

print(f"\n  base rate for reference: {df.fail_2y.mean():.4f}")
print(f"  ratio B/A: {b/a:.1f}x   worst case / A: {max(b,b1,b2)/a:.1f}x")

# sensitivity to years_stable, holding regime type fixed
print("\nHAZARD DECAY — p(failure) vs years of accumulated stability, full autocracy")
for ys in (0, 2, 5, 10, 20, 30, 47):
    row = {c: 0.0 for c in CATS}
    k = [c for c in CATS if c.endswith('0-Full autocracy')]
    if k: row[k[0]] = 1.0
    row['e_miferrat'] = fert; row['years_stable'] = float(ys)
    pr = model.predict_proba(pd.DataFrame([row])[FE].astype(float))[0,1]
    print(f"   {ys:3} years  ->  {pr:.4f}")

json.dump(dict(fertility=fert, scenario_A_continuous=a, scenario_B_reset=b,
               scenario_B_partial_autocracy=b1, scenario_B_factionalised=b2,
               base_rate=float(df.fail_2y.mean())), open('iran-forecaster.json','w'), indent=1)
print("\nwrote iran-forecaster.json")
