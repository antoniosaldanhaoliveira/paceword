"""
BOUND 2026, THEN PROPAGATE IT.

Step 1 — tighten the reference class. GWF codes the Islamic Republic (1979-) as
'party-based'. Condition the one-year-change distribution on party-based /
party-personal regimes that ended, AND on a comparable institutional baseline
(v2x_rule in 0.10-0.35, where Iran sits at 0.209).

Step 2 — bound the economic input. IMF projects Iran 2026 GDP -6.1%. Percentile-
rank that against V-Dem's own distribution of one-year log GDP-per-capita changes,
so economic_stability is placed empirically rather than by judgement.

Step 3 — emit bootstrap samples of the 2026 input vector for the kernel to consume.
"""
import pyreadr, json, math, re, random, statistics as st

random.seed(20260809)
df = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
gwf = pyreadr.read_r('data/democracyData/data/REIGN.rda')['REIGN']
IND = ['v2x_rule', 'v2x_civlib', 'v2xcs_ccsi']

vals = {}
for r in df.itertuples():
    for i in IND + ['e_gdppc']:
        v = getattr(r, i)
        if v == v: vals[(r.country_name, int(r.year), i)] = v

# ── reference class: party-based / party-personal regimes that ended ─────────
PARTY = {'party-based', 'party-personal', 'party-personal-military', 'party-military'}
ends_all, ends_party = set(), set()
for r in gwf.itertuples():
    d = str(r.End) if r.End == r.End else ''
    m = re.match(r'^(\d{4})-', d)
    if not m: continue
    y = int(m.group(1)); c = r.extended_country_name
    ends_all.add((c, y))
    if str(r.gwf_regimetype) in PARTY: ends_party.add((c, y))

def deltas(events, ind, baseline=None):
    out = []
    for (c, y) in events:
        a, b = vals.get((c, y, ind)), vals.get((c, y+1, ind))
        if a is None or b is None: continue
        if baseline and not (baseline[0] <= a <= baseline[1]): continue
        out.append(b - a)
    return out

BASE = (0.10, 0.35)
print("REFERENCE CLASSES — one-year change in the year after regime end\n")
print(f"  {'class':44}{'ind':14}{'n':>5}{'p5':>9}{'median':>9}{'p95':>9}")
sets = [('all regime breakdowns', ends_all, None),
        ('party-based family', ends_party, None),
        ('party-based + baseline v2x_rule 0.10-0.35', ends_party, BASE)]
chosen = {}
for label, ev, bl in sets:
    for ind in IND:
        d = deltas(ev, ind, bl)
        if len(d) < 8:
            print(f"  {label:44}{ind:14}{len(d):5}   (too few)"); continue
        s = sorted(d); q = lambda p: s[min(len(s)-1, int(p*len(s)))]
        print(f"  {label:44}{ind:14}{len(d):5}{q(.05):+9.4f}{st.median(d):+9.4f}{q(.95):+9.4f}")
        if bl is BASE: chosen[ind] = d
    print()

# fall back to the party class if the baseline filter left too little
for ind in IND:
    if ind not in chosen or len(chosen[ind]) < 20:
        chosen[ind] = deltas(ends_party, ind, None)
        if len(chosen[ind]) < 20: chosen[ind] = deltas(ends_all, ind, None)
print("reference n used per indicator:", {k: len(v) for k, v in chosen.items()})

# ── economic input, placed empirically ──────────────────────────────────────
gd = []
byc = {}
for (c, y, i), v in vals.items():
    if i == 'e_gdppc': byc[(c, y)] = v
for (c, y), v in byc.items():
    w = byc.get((c, y+1))
    if w and v and v > 0 and w > 0: gd.append(math.log(w/v))
gd.sort()
imf = math.log(1 - 0.061)          # IMF projection for Iran 2026: -6.1%
lo, hi = 0, len(gd)
while lo < hi:
    m = (lo+hi)//2
    if gd[m] < imf: lo = m+1
    else: hi = m
eco_pct = lo/len(gd)
print(f"\nECONOMIC INPUT")
print(f"  IMF 2026 projection for Iran: -6.1% GDP")
print(f"  percentile against {len(gd)} country-year GDP changes in V-Dem: {eco_pct:.4f}")
print(f"  -> economic_stability = {eco_pct:.4f}  (was 0.15 by judgement)")

# ── bootstrap 2026 input vectors ───────────────────────────────────────────
anchor = {i: float(df[(df.country_name=='Iran') & (df.year==2025)][i].iloc[0]) for i in IND}
print(f"\n2025 anchors: " + "  ".join(f"{i}={anchor[i]:.4f}" for i in IND))
N = 2000
samples = []
for _ in range(N):
    s = {i: max(0.0, min(1.0, anchor[i] + random.choice(chosen[i]))) for i in IND}
    s['economic'] = eco_pct
    samples.append(s)
for i in IND:
    v = sorted(x[i] for x in samples)
    print(f"  2026 {i:14} p5 {v[int(.05*N)]:.4f}  median {v[N//2]:.4f}  p95 {v[int(.95*N)]:.4f}")

json.dump({'anchor_2025': anchor, 'economic_pct': eco_pct, 'samples': samples},
          open('iran-2026-samples.json','w'))
print(f"\nwrote iran-2026-samples.json ({N} bootstrap input vectors)")
