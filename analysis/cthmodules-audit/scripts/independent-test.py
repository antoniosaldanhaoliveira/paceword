"""
INDEPENDENT-TARGET TEST
Author's corpus inputs/outputs  vs  Seshat Crisis Consequences (expert-coded, 2023).

Seshat codes POLITY-LEVEL crisis periods, not discrete events, so matching is
many-to-one in places. Every match below is declared with a quality tag and the
analysis is run on STRONG+DEFENSIBLE only, then repeated with AMBIGUOUS included.
"""
import csv, re, math, json

SESHAT = 'data/seshat/CrisisConsequencesData_NavigatingPolycrisis_2023.03.csv'
rows = list(csv.DictReader(open(SESHAT, encoding='latin-1')))

def sev(r):
    s = r.get('Severity', '').strip()
    return int(s) if s.lstrip('-').isdigit() else None

sevs = [sev(r) for r in rows if sev(r) is not None]
SMAX = max(sevs)
print(f"Seshat Crisis Consequences: {len(rows)} cases, severity {min(sevs)}–{SMAX}")

def find(name, yr_from=None):
    out = [r for r in rows if r['Polity.Name'].strip().lower() == name.strip().lower()]
    if yr_from is not None:
        out = [r for r in out if r['Polity.Date.From'].strip() == str(yr_from)]
    return out[0] if out else None

# ── declared matches: (CTH id, author's observed, Seshat polity, from, quality) ──
MATCHES = [
    ('AKKADIAN-COLLAPSE-2154BCE', 0.30, 'Akkadian Empire',           -2350, 'STRONG'),
    ('QIN-UNIFICATION-221BCE',    0.58, 'Qin Empire',                 -338, 'STRONG'),
    ('ROMAN-REPUBLIC-CRISIS-49BCE',0.45, 'Roman Republic-Principate',  -133, 'STRONG'),
    ('FALL-OF-ROME-476',          0.28, 'Western Roman Empire',         395, 'STRONG'),
    ('NORMAN-CONQUEST-1066',      0.60, 'Anglo-Saxon England',          410, 'STRONG'),
    ('AN-LUSHAN-REBELLION-755',   0.30, 'Tang Dynasty',                 617, 'DEFENSIBLE'),
    ('ENGLISH-CIVIL-WAR-1642',    0.42, 'Early Modern England',        1642, 'STRONG'),
    ('FRENCH-REVOLUTION-1789',    0.36, 'French Kingdom - Late Bourbon',1660, 'DEFENSIBLE'),
    ('GLORIOUS-REVOLUTION-1688',  0.70, 'Early Modern England',        1642, 'AMBIGUOUS'),  # same case as 1642
    ('MONGOL-CONQUESTS-1206',     0.40, 'Song Dynasty',                1127, 'AMBIGUOUS'),  # victim, not actor
    ('FALL-CONSTANTINOPLE-1453',  0.33, 'Habsburg Empire II',          1453, 'AMBIGUOUS'),  # wrong polity, right year
]

print("\n── DECLARED MATCHES ──")
print(f"  {'CTH EVENT':30}{'AUTHOR':>8}  {'SESHAT POLITY':32}{'SEV':>4}{'INDEP':>8}  QUALITY")
data = []
for cid, obs, poly, yf, q in MATCHES:
    r = find(poly, yf)
    if not r:
        print(f"  {cid:30}{obs:8.2f}  {poly:32}  -- NOT FOUND")
        continue
    s = sev(r)
    indep = 1 - s / SMAX          # high severity -> low adaptive-transformation score
    data.append(dict(id=cid, author=obs, sev=s, indep=indep, q=q))
    print(f"  {cid:30}{obs:8.2f}  {poly:32}{s:4d}{indep:8.3f}  {q}")

def pearson(a, b):
    n = len(a); ma = sum(a)/n; mb = sum(b)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x-ma)**2 for x in a)); db = math.sqrt(sum((y-mb)**2 for y in b))
    return num/(da*db) if da and db else float('nan')

def spearman(a, b):
    rk = lambda v: [sorted(v).index(x)+1 for x in v]
    return pearson(rk(a), rk(b))

for label, keep in [('STRONG+DEFENSIBLE', ('STRONG','DEFENSIBLE')), ('ALL (incl. AMBIGUOUS)', ('STRONG','DEFENSIBLE','AMBIGUOUS'))]:
    d = [x for x in data if x['q'] in keep]
    a = [x['author'] for x in d]; i = [x['indep'] for x in d]
    print(f"\n══ {label}  (n={len(d)}) ══")
    print(f"  Pearson  r(author_coding, Seshat_independent) = {pearson(a,i):+.4f}")
    print(f"  Spearman rho                                  = {spearman(a,i):+.4f}")
    mae = sum(abs(x-y) for x, y in zip(a, i))/len(d)
    print(f"  MAE between the two codings                   = {mae:.4f}")
    agree = sum(1 for x, y in zip(a, i) if (x >= .5) == (y >= .5))
    print(f"  directional agreement (adapt vs decline)      = {agree}/{len(d)} = {agree/len(d)*100:.0f}%")

json.dump(data, open('independent-matches.json','w'), indent=1)
print("\nwrote independent-matches.json")
