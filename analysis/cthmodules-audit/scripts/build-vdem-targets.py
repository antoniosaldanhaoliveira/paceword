"""
Build INDEPENDENT outcome targets for post-1789 corpus events from V-Dem.

PROTOCOL — declared before any scoring:
  For an event in country C at year Y, measure the system's trajectory over the
  following 30 years on two non-normative axes:
     ECON  = log(e_gdppc[Y+30] / e_gdppc[Y])      did material conditions improve
     INST  = v2x_rule[Y+30] - v2x_rule[Y]          did rule of law strengthen
  Each is converted to a percentile against the FULL distribution of all
  (country, year) 30-year windows in V-Dem, so the scale is empirical, not
  chosen by me. Independent target = mean of the two percentiles.

  Deliberately avoids v2x_polyarchy as the primary axis: it is a democracy
  measure and would code Meiji Japan as non-adaptive for being undemocratic,
  importing a normative judgement the author's construct does not make.
"""
import pyreadr, math, json, statistics as st

df = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
H = 30

# ── reference distribution: every country-year window in V-Dem ───────────────
econ_all, inst_all = [], []
by_country = {}
for cn, sub in df.groupby('country_name'):
    s = sub.sort_values('year')
    by_country[cn] = {int(r.year): (r.e_gdppc, r.v2x_rule) for r in s.itertuples()}

for cn, d in by_country.items():
    for y in d:
        if y + H in d:
            g0, r0 = d[y]; g1, r1 = d[y + H]
            if g0 and g1 and g0 == g0 and g1 == g1 and g0 > 0 and g1 > 0:
                econ_all.append(math.log(g1 / g0))
            if r0 == r0 and r1 == r1:
                inst_all.append(r1 - r0)
econ_all.sort(); inst_all.sort()
print(f"reference windows: econ n={len(econ_all)}, inst n={len(inst_all)}, horizon {H}y")

def pct(sorted_vals, x):
    lo, hi = 0, len(sorted_vals)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_vals[mid] < x: lo = mid + 1
        else: hi = mid
    return lo / len(sorted_vals)

# ── declared event -> country mapping, with quality tags ─────────────────────
EVENTS = [
    ('INDUSTRIAL-REVOLUTION-1780', 'United Kingdom',           1789, 'DEFENSIBLE'),  # V-Dem starts 1789
    ('US-CONSTITUTION-1787',       'United States of America', 1789, 'STRONG'),
    ('FRENCH-REVOLUTION-1789',     'France',                   1789, 'STRONG'),
    ('HISPANIC-INDEPENDENCE-1810', 'Mexico',                   1810, 'DEFENSIBLE'),  # one of many polities
    ('MEIJI-RESTORATION-1868',     'Japan',                    1868, 'STRONG'),
    ('WORLD-WAR-I-1914',           'Germany',                  1914, 'AMBIGUOUS'),   # which belligerent?
    ('RUSSIAN-REVOLUTION-1917',    'Russia',                   1917, 'STRONG'),
    ('GREAT-DEPRESSION-1929',      'United States of America', 1929, 'STRONG'),
    ('INDIAN-INDEPENDENCE-1947',   'India',                    1947, 'STRONG'),
    ('CHINESE-REVOLUTION-1949',    'China',                    1949, 'STRONG'),
    ('USSR-COLLAPSE-1991',         'Russia',                   1991, 'STRONG'),
    # ARAB-SPRING-2011 and COVID-19-2020 excluded: Y+30 beyond V-Dem's 2025
]

out = []
print(f"\n  {'EVENT':30}{'COUNTRY':26}{'Y':>6}{'ECON%':>8}{'INST%':>8}{'INDEP':>8}  QUALITY")
for eid, cn, y, q in EVENTS:
    d = by_country.get(cn, {})
    if y not in d or y + H not in d:
        print(f"  {eid:30}{cn:26}{y:6}   -- no window"); continue
    g0, r0 = d[y]; g1, r1 = d[y + H]
    if not (g0 and g1 and g0 == g0 and g1 == g1 and g0 > 0):
        print(f"  {eid:30}{cn:26}{y:6}   -- missing gdppc"); continue
    e = pct(econ_all, math.log(g1 / g0))
    i = pct(inst_all, r1 - r0) if (r0 == r0 and r1 == r1) else None
    indep = (e + i) / 2 if i is not None else e
    out.append(dict(id=eid, country=cn, year=y, econ_pct=e, inst_pct=i, indep=indep, q=q))
    print(f"  {eid:30}{cn:26}{y:6}{e:8.3f}{(i if i is not None else float('nan')):8.3f}{indep:8.3f}  {q}")

json.dump(out, open('vdem-targets.json', 'w'), indent=1)
print(f"\nwrote vdem-targets.json ({len(out)} events)")
