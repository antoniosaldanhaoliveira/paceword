"""
CAN WE PRODUCE 2026 CODING "FOLLOWING THE SAME GUIDELINES"?

Short answer: not V-Dem's guidelines. Its expert-coded layer (vartype 'C', 302
indicators) is aggregated by a Bayesian IRT model across multiple INDEPENDENT
country experts, which estimates each coder's bias and threshold. A single new
rating cannot be placed on that latent scale, and several ratings from one
source are not independent coders -- the IRT model would read their correlated
agreement as high reliability and return a falsely narrow credible interval.

What IS defensible: use V-Dem's own history to bound how much these indices can
move in one year, and project 2025 -> 2026 with an empirical band. No new coding,
no borrowed expertise -- just the observed dynamics of the measure itself.
"""
import pyreadr, statistics as st, collections, json, re

df = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
IND = ['v2x_rule', 'v2x_polyarchy', 'v2xcs_ccsi', 'v2x_civlib']

# ── 1. unconditional one-year changes ───────────────────────────────────────
deltas = {i: [] for i in IND}
prev = {}
for r in df.sort_values(['country_name', 'year']).itertuples():
    key = r.country_name
    for i in IND:
        v = getattr(r, i)
        p = prev.get((key, i))
        if p is not None and v == v and p[0] == p[0] and r.year == p[1] + 1:
            deltas[i].append(v - p[0])
        if v == v: prev[(key, i)] = (v, r.year)

def band(x):
    s = sorted(x); n = len(s)
    q = lambda p: s[min(n-1, int(p*n))]
    return q(0.05), q(0.25), q(0.5), q(0.75), q(0.95)

print("HOW MUCH DO V-DEM INDICES MOVE IN ONE YEAR? (all country-years)")
print(f"  {'indicator':16}{'n':>7}{'p5':>9}{'p25':>9}{'median':>9}{'p75':>9}{'p95':>9}{'|Δ|>0.05':>10}")
for i in IND:
    d = deltas[i]; b = band(d)
    big = sum(1 for x in d if abs(x) > 0.05)/len(d)*100
    print(f"  {i:16}{len(d):7}" + "".join(f"{v:+9.4f}" for v in b) + f"{big:9.1f}%")

# ── 2. conditional on autocratic-regime breakdown (GWF end years) ────────────
gwf = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']
ends = set()
for r in gwf.itertuples():
    d = str(r.End) if r.End == r.End else ''
    m = re.match(r'^(\d{4})-', d)
    if m: ends.add((r.extended_country_name, int(m.group(1))))
print(f"\nGWF regime-breakdown events located: {len(ends)}")

cond = {i: [] for i in IND}
vals = {}
for r in df.itertuples():
    for i in IND:
        v = getattr(r, i)
        if v == v: vals[(r.country_name, int(r.year), i)] = v
for (c, y) in ends:
    for i in IND:
        a, b = vals.get((c, y, i)), vals.get((c, y+1, i))
        if a is not None and b is not None: cond[i].append(b - a)

print("ONE-YEAR CHANGE IN THE YEAR AFTER AN AUTOCRATIC REGIME BREAKDOWN")
print(f"  {'indicator':16}{'n':>7}{'p5':>9}{'p25':>9}{'median':>9}{'p75':>9}{'p95':>9}")
for i in IND:
    if len(cond[i]) < 10: continue
    b = band(cond[i])
    print(f"  {i:16}{len(cond[i]):7}" + "".join(f"{v:+9.4f}" for v in b))

# ── 3. project Iran 2026 ────────────────────────────────────────────────────
ir = df[df.country_name == 'Iran']
last = ir[ir.year == 2025]
print("\nIRAN 2026 PROJECTION (anchored on measured 2025, band from regime-breakdown cases)")
print(f"  {'indicator':16}{'2025':>9}{'p5':>10}{'median':>10}{'p95':>10}")
proj = {}
for i in IND:
    a = float(last[i].iloc[0])
    src = cond[i] if len(cond[i]) >= 10 else deltas[i]
    b = band(src)
    lo, md, hi = a+b[0], a+b[2], a+b[4]
    proj[i] = dict(anchor_2025=a, p5=lo, median=md, p95=hi, n_reference=len(src))
    print(f"  {i:16}{a:9.4f}{lo:10.4f}{md:10.4f}{hi:10.4f}")

json.dump(proj, open('iran-2026-projection.json','w'), indent=1)
print("\nwrote iran-2026-projection.json")
print("\nNOTE: this is a PROJECTION with an empirical band, not a V-Dem coding.")
print("It must not be presented as, or merged into, V-Dem data.")
