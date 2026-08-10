"""
Build the deep-history validation panel from Seshat.

DESIGN — declared before any scoring:
  UNIT      NGA x century (Seshat's own 100-year grid)
  INPUTS    the 5 well-covered complexity characteristics at time t:
              Hier (settlement hierarchy, rescaled), Gov, Infra, Info, Money
            Pop/Terr/Cap are excluded: only 554-935 of 1494 rows carry them.
  OUTCOME   SC(t+100) - SC(t), i.e. did social complexity grow or collapse over
            the following century. This is the independent analogue of CTH's
            "adaptive transformation (RMD) vs systemic collapse (CMN)" axis, and
            it is measured, not coded by anyone with a stake in the framework.
  SCALE     outcome percentile-ranked against ALL observed transitions, so the
            0-1 scale is empirical rather than chosen.

  Note this is a WITHIN-PANEL design: no matching to crisis cases is required,
  which removes the many-to-one problem that limited the earlier n=8 test.
"""
import json, statistics as st, collections

panel = json.load(open('seshat-panel.json'))
CC = ['Hier', 'Gov', 'Infra', 'Info', 'Money']

# Hier is on a 0.5-8.83 scale; the rest are 0-1. Rescale Hier to 0-1.
hv = [r['Hier'] for r in panel if r['Hier'] is not None]
hmin, hmax = min(hv), max(hv)
for r in panel:
    r['Hier_n'] = (r['Hier'] - hmin) / (hmax - hmin) if r['Hier'] is not None else None
CCN = ['Hier_n', 'Gov', 'Infra', 'Info', 'Money']

def sc(r):
    v = [r[c] for c in CCN if r[c] is not None]
    return sum(v) / len(v) if len(v) >= 4 else None   # require >=4 of 5

for r in panel: r['SC'] = sc(r)
usable = [r for r in panel if r['SC'] is not None]
print(f"panel rows {len(panel)} -> usable (>=4 of 5 CCs) {len(usable)}")

# ── time grid per NGA ────────────────────────────────────────────────────────
byn = collections.defaultdict(dict)
for r in usable: byn[r['NGA']][r['Time']] = r
steps = collections.Counter()
for nga, d in byn.items():
    ts = sorted(d)
    for i in range(len(ts)-1): steps[round(ts[i+1]-ts[i])] += 1
print("time-step distribution:", steps.most_common(5))

# ── transitions t -> t+100 ───────────────────────────────────────────────────
trans = []
for nga, d in byn.items():
    for t in sorted(d):
        if t + 100 in d:
            a, b = d[t], d[t+100]
            trans.append(dict(NGA=nga, PolID=a['PolID'], t=t, sc0=a['SC'], sc1=b['SC'],
                              raw=b['SC']-a['SC'], PropCoded=a['PropCoded'],
                              **{c: a[c] for c in CCN}))
print(f"transitions (t -> t+100): {len(trans)}")

# percentile-rank the raw change -> empirical [0,1] outcome
raws = sorted(r['raw'] for r in trans)
def pct(x):
    lo, hi = 0, len(raws)
    while lo < hi:
        m = (lo+hi)//2
        if raws[m] < x: lo = m+1
        else: hi = m
    return lo/len(raws)
for r in trans: r['outcome'] = pct(r['raw'])

print(f"\n  raw change      min {min(raws):+.4f}  median {st.median(raws):+.4f}  max {max(raws):+.4f}")
dec = sum(1 for r in trans if r['raw'] < 0)
print(f"  declines {dec} / {len(trans)} = {dec/len(trans)*100:.0f}%   growth {len(trans)-dec}")
print(f"  NGAs represented: {len({r['NGA'] for r in trans})}")
span = [r['t'] for r in trans]
print(f"  time span: {int(min(span))} to {int(max(span))}")

json.dump(trans, open('seshat-transitions.json', 'w'))
print("\nwrote seshat-transitions.json")
