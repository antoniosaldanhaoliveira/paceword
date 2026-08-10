"""
Deep-history validation, built on Seshat's HONEST unit of resolution.

WHY NOT THE CENTURY GRID: 72% of consecutive century-pairs carry the same PolID,
and 68% of century-to-century complexity changes are exactly zero. Seshat assigns
one coding per polity; the century grid repeats it. Treating 1,333 century
transitions as independent observations would inflate n roughly 3x with copies.

UNIT      polity spell (a polity's occupancy of an NGA)
INPUT     the spell's complexity characteristics: Hier(rescaled), Gov, Infra, Info, Money
OUTCOME   SC(next spell) - SC(this spell), percentile-ranked across all observed
          successions -> empirical [0,1]. High = successor more complex (adaptive
          transformation); low = successor less complex (systemic collapse).
          This is the independent analogue of CTH's RMD/CMN axis.
PRIOR     each spell also carries the PRECEDING succession's change, which is
          observable at prediction time and is the only legitimate trend input.
"""
import json, collections, statistics as st

panel = json.load(open('seshat-panel.json'))
hv = [r['Hier'] for r in panel if r['Hier'] is not None]
hmin, hmax = min(hv), max(hv)
CCN = ['Hier_n', 'Gov', 'Infra', 'Info', 'Money']
for r in panel:
    r['Hier_n'] = (r['Hier']-hmin)/(hmax-hmin) if r['Hier'] is not None else None

def sc(r):
    v = [r[c] for c in CCN if r[c] is not None]
    return sum(v)/len(v) if len(v) >= 4 else None

byn = collections.defaultdict(list)
for r in panel: byn[r['NGA']].append(r)

# ── collapse the century grid into polity spells ─────────────────────────────
spells = []
for nga, rows in byn.items():
    rows.sort(key=lambda x: x['Time'])
    cur = None
    for r in rows:
        if cur is None or r['PolID'] != cur['PolID']:
            if cur: spells.append(cur)
            cur = dict(NGA=nga, PolID=r['PolID'], t_start=r['Time'], t_end=r['Time'], obs=[r])
        else:
            cur['t_end'] = r['Time']; cur['obs'].append(r)
    if cur: spells.append(cur)

for s in spells:
    for c in CCN:
        v = [o[c] for o in s['obs'] if o[c] is not None]
        s[c] = sum(v)/len(v) if v else None
    s['SC'] = sc(s)
    s['duration'] = s['t_end'] - s['t_start'] + 100
    s['n_obs'] = len(s['obs'])
    del s['obs']

spells = [s for s in spells if s['SC'] is not None]
print(f"polity spells with usable SC: {len(spells)}")

# ── successions within an NGA ────────────────────────────────────────────────
bys = collections.defaultdict(list)
for s in spells: bys[s['NGA']].append(s)
succ = []
for nga, ss in bys.items():
    ss.sort(key=lambda x: x['t_start'])
    for i in range(len(ss)-1):
        a, b = ss[i], ss[i+1]
        succ.append(dict(NGA=nga, PolID=a['PolID'], next=b['PolID'], t=a['t_end'],
                         sc0=a['SC'], sc1=b['SC'], raw=b['SC']-a['SC'],
                         duration=a['duration'], **{c: a[c] for c in CCN}))
# prior change, observable before the outcome
for nga, ss in bys.items():
    idx = {s['PolID']: k for k, s in enumerate(ss)}
    for r in succ:
        if r['NGA'] != nga: continue
        k = idx.get(r['PolID'])
        r['prior'] = (ss[k]['SC']-ss[k-1]['SC']) if (k is not None and k >= 1) else 0.0

raws = sorted(r['raw'] for r in succ)
def pct(x):
    lo, hi = 0, len(raws)
    while lo < hi:
        m = (lo+hi)//2
        if raws[m] < x: lo = m+1
        else: hi = m
    return lo/len(raws)
for r in succ: r['outcome'] = pct(r['raw'])

zeros = sum(1 for r in succ if abs(r['raw']) < 1e-9)
print(f"successions: {len(succ)}   NGAs: {len({r['NGA'] for r in succ})}")
print(f"  exact-zero change: {zeros} ({zeros/len(succ)*100:.0f}%)  <- vs 68% on the century grid")
print(f"  declines {sum(1 for r in succ if r['raw']<-1e-9)}   growth {sum(1 for r in succ if r['raw']>1e-9)}")
print(f"  raw change: min {min(raws):+.4f}  median {st.median(raws):+.4f}  max {max(raws):+.4f}")
print(f"  time span: {int(min(r['t'] for r in succ))} to {int(max(r['t'] for r in succ))}")
c = collections.Counter(r['NGA'] for r in succ)
print(f"  successions per NGA: min {min(c.values())} median {int(st.median(c.values()))} max {max(c.values())}")

json.dump(succ, open('seshat-successions.json','w'))
print("\nwrote seshat-successions.json")
