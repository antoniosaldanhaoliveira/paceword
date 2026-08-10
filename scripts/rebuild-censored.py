"""
CORRECTION: handle right-censoring.

GWF's data stops 2020-12-31 and stamps every still-living regime with that date.
195 of 631 spells (31%) carry it. The earlier outcome definition read those as
regime failures, inflating recent base rates and contaminating everything
downstream. This rebuilds the panel with censoring handled and re-runs the
walk-forward evaluation.

RULE: a spell ending on the cutoff is CENSORED, not failed.
      - within a censored spell, years more than 2 from the cutoff -> fail_2y = 0
      - years within 2 of the cutoff -> outcome unknown, DROPPED
"""
import pyreadr, pandas as pd, numpy as np, re, json
from sklearn.metrics import brier_score_loss, average_precision_score

CUTOFF = 2020
vdem = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
pitf = pyreadr.read_r('data/democracyData/data/pitf.rda')['pitf']
gwf  = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']

spells, censored = [], 0
for r in gwf[['extended_country_name','gwf_casename','Start','End']].drop_duplicates().itertuples():
    ms, me = re.match(r'^(\d{4})-', str(r.Start)), re.match(r'^(\d{4})-', str(r.End))
    if not (ms and me): continue
    s, e = int(ms.group(1)), int(me.group(1))
    cen = str(r.End).startswith(f'{CUTOFF}-12-31')
    censored += cen
    spells.append((r.extended_country_name, s, e, cen))
print(f"spells {len(spells)}, of which censored at {CUTOFF}: {censored}")

rows = []
for c, s, e, cen in spells:
    for y in range(s, e+1):
        if cen:
            if e - y <= 2: continue           # outcome unknowable
            fail = 0                           # survived the next 2 years
        else:
            fail = int((e - y) <= 2)
        rows.append(dict(country=c, year=y, years_stable=y-s, fail_2y=fail))
sp = pd.DataFrame(rows).drop_duplicates(subset=['country','year'], keep='last')

v = vdem[['country_name','year','e_miferrat']].rename(columns={'country_name':'country'})
p = pitf[['extended_country_name','year','pitf']].rename(columns={'extended_country_name':'country'})
for d in (v, p, sp): d['year'] = d['year'].astype(int)
df = sp.merge(v, on=['country','year'], how='left').merge(p, on=['country','year'], how='left').dropna(subset=['pitf','e_miferrat'])
df.to_csv('panel-cache-censored.csv', index=False)
print(f"country-years: {len(df)}  ({int(df.year.min())}-{int(df.year.max())})")
print(f"base rate BEFORE fix: 0.0709   AFTER fix: {df.fail_2y.mean():.4f}\n")

def tb(v): return '0-4' if v < 5 else '5-14' if v < 15 else '15-29' if v < 30 else '30+'
df['tenure'] = df.years_stable.apply(tb)
df['refclass'] = df.pitf.astype(str) + ' | ' + df.tenure
YEARS = sorted(df.loc[df.year > 1960, 'year'].unique()); SHRINK = 20

def walk(window):
    G, R, O = [], [], []
    for y in YEARS:
        hist = df[(df.year < y) & (df.year >= y-window)]; cur = df[df.year == y]
        if len(hist) < 200 or len(cur) == 0: continue
        b = hist.fail_2y.mean()
        rt = hist.groupby('refclass').fail_2y.agg(['mean','size'])
        sm = (rt['mean']*rt['size'] + b*SHRINK) / (rt['size'] + SHRINK)
        G.append(np.full(len(cur), b)); R.append(cur.refclass.map(sm).fillna(b).values); O.append(cur.fail_2y.values)
    return np.concatenate(G), np.concatenate(R), np.concatenate(O)

print("WALK-FORWARD, censoring corrected")
print(f"  {'window':>8}{'n':>7}{'base':>9}{'Brier(base)':>14}{'Brier(refclass)':>17}{'skill':>9}{'AUPRC':>9}")
res = {}
for w in (10, 15, 20, 30, 50):
    g, r, o = walk(w)
    bg, br = brier_score_loss(o, g), brier_score_loss(o, r)
    sk = 1 - br/bg; ap = average_precision_score(o, r)
    res[f'window_{w}'] = dict(n=int(len(o)), base=float(o.mean()), brier_base=float(bg),
                              brier_ref=float(br), skill=float(sk), auprc=float(ap))
    print(f"  {w:8}{len(o):7}{o.mean():9.4f}{bg:14.5f}{br:17.5f}{sk:+9.4f}{ap:9.4f}")

best = max(res.items(), key=lambda kv: kv[1]['skill'])
W = int(best[0].split('_')[1])
print(f"\n  best window {W}y, Brier skill {best[1]['skill']:+.4f}, AUPRC {best[1]['auprc']:.4f} vs base {best[1]['base']:.4f} (lift {best[1]['auprc']/best[1]['base']:.2f}x)")

# Iran, using the most recent clean window
last = CUTOFF - 3          # last year with a known outcome
hist = df[(df.year <= last) & (df.year > last - W)]
b = hist.fail_2y.mean()
rt = hist.groupby('refclass').fail_2y.agg(['mean','size'])
sm = (rt['mean']*rt['size'] + b*SHRINK) / (rt['size'] + SHRINK)
print(f"\nIRAN — rolling {W}-year window ending {last}, base rate {b:.4f}")
iran = {}
for lbl, rc in [('A: Islamic Republic continuous since 1979','0-Full autocracy | 30+'),
                ('B: Feb 2026 as regime break','0-Full autocracy | 0-4'),
                ('B + partial autocracy','1-Partial autocracy | 0-4'),
                ('B + factionalised partial democracy','2-Partial democracy with factionalism | 0-4')]:
    val = float(sm.get(rc, b)); iran[lbl] = val
    print(f"  {lbl:44}{val:8.4f}")
print(f"  {'rolling base rate':44}{b:8.4f}")

json.dump(dict(walkforward=res, iran=iran, base_rate=float(b), window=W),
          open('corrected-results.json','w'), indent=1)
print("\nwrote corrected-results.json")
