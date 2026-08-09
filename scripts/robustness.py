"""
ROBUSTNESS: my V-Dem target used a 30-year horizon and (gdppc, rule-of-law).
Both were my choices. Does the conclusion survive other reasonable ones?
Sweeps horizon x indicator pair, recomputing r(author, independent) each time.
"""
import pyreadr, math, json, itertools

df = pyreadr.read_r('data/vdemdata/data/vdem.RData')['vdem']
AUTHOR = {  # author's observed_outcome, from cth-corpus.js
 'INDUSTRIAL-REVOLUTION-1780':0.68,'US-CONSTITUTION-1787':0.78,'FRENCH-REVOLUTION-1789':0.36,
 'HISPANIC-INDEPENDENCE-1810':0.48,'MEIJI-RESTORATION-1868':0.72,'RUSSIAN-REVOLUTION-1917':0.33,
 'GREAT-DEPRESSION-1929':0.38,'INDIAN-INDEPENDENCE-1947':0.65,'CHINESE-REVOLUTION-1949':0.44}
EV = [('INDUSTRIAL-REVOLUTION-1780','United Kingdom',1789),('US-CONSTITUTION-1787','United States of America',1789),
      ('FRENCH-REVOLUTION-1789','France',1789),('HISPANIC-INDEPENDENCE-1810','Mexico',1810),
      ('MEIJI-RESTORATION-1868','Japan',1868),('RUSSIAN-REVOLUTION-1917','Russia',1917),
      ('GREAT-DEPRESSION-1929','United States of America',1929),('INDIAN-INDEPENDENCE-1947','India',1947),
      ('CHINESE-REVOLUTION-1949','China',1949)]

def pearson(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    da=math.sqrt(sum((x-ma)**2 for x in a)); db=math.sqrt(sum((y-mb)**2 for y in b))
    return num/(da*db) if da and db else float('nan')

INDICATORS = ['v2x_rule','v2x_polyarchy','v2x_civlib','v2xcs_ccsi']
cache={}
def series(ind):
    if ind in cache: return cache[ind]
    d={}
    for cn,sub in df.groupby('country_name'):
        d[cn]={int(r.year):(getattr(r,'e_gdppc'),getattr(r,ind)) for r in sub.sort_values('year').itertuples()}
    cache[ind]=d; return d

print(f"  {'HORIZON':>8}  {'INDICATOR':16}{'n':>4}{'r(author,indep)':>18}{'  verdict'}")
results=[]
for H in (20,30,40,50):
    for ind in INDICATORS:
        by=series(ind)
        econ_all=[]; inst_all=[]
        for cn,d in by.items():
            for y in d:
                if y+H in d:
                    g0,r0=d[y]; g1,r1=d[y+H]
                    if g0 and g1 and g0==g0 and g1==g1 and g0>0: econ_all.append(math.log(g1/g0))
                    if r0==r0 and r1==r1: inst_all.append(r1-r0)
        econ_all.sort(); inst_all.sort()
        def pct(s,x):
            lo,hi=0,len(s)
            while lo<hi:
                m=(lo+hi)//2
                if s[m]<x: lo=m+1
                else: hi=m
            return lo/len(s) if s else float('nan')
        A=[];I=[]
        for eid,cn,y in EV:
            d=by.get(cn,{})
            if y not in d or y+H not in d: continue
            g0,r0=d[y]; g1,r1=d[y+H]
            if not(g0 and g1 and g0==g0 and g1==g1 and g0>0): continue
            e=pct(econ_all,math.log(g1/g0))
            i=pct(inst_all,r1-r0) if (r0==r0 and r1==r1) else None
            A.append(AUTHOR[eid]); I.append((e+i)/2 if i is not None else e)
        if len(A)>=5:
            r=pearson(A,I); results.append(r)
            print(f"  {H:8}  {ind:16}{len(A):4}{r:18.4f}{'   positive' if r>0.3 else '   ~zero' if abs(r)<=0.3 else '   negative'}")

print(f"\n  {len(results)} specifications tested")
print(f"  r range: {min(results):+.4f} to {max(results):+.4f}   mean {sum(results)/len(results):+.4f}")
print(f"  specifications with r > 0.3 (meaningful agreement): {sum(1 for r in results if r>0.3)}/{len(results)}")
