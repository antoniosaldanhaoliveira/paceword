import fs from 'fs';
const src = fs.readFileSync('CTHmodules/cth-corpus.js','utf8');
const rows = [...src.matchAll(/\['([A-Z0-9\-]+)',\s*(-?\d+),\s*'(\w+)',\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([+-][\d.]+),\s*([\d.]+),\s*([\d.]+)/g)]
  .map(m => ({id:m[1], year:+m[2], cat:m[3], observed:+m[4], pol:+m[5], eco:+m[6], soc:+m[7], delta:+m[8], swan:+m[9], loop:+m[10]}));
console.log('corpus size:', rows.length);

const corr = (a,b) => {
  const n=a.length, ma=a.reduce((s,x)=>s+x,0)/n, mb=b.reduce((s,x)=>s+x,0)/n;
  let num=0,da=0,db=0;
  for(let i=0;i<n;i++){const x=a[i]-ma,y=b[i]-mb;num+=x*y;da+=x*x;db+=y*y;}
  return num/Math.sqrt(da*db);
};
const obs = rows.map(r=>r.observed);
for (const k of ['delta','pol','eco','soc','swan','loop','year']) {
  console.log(`  r(${k.padEnd(6)}, observed_outcome) = ${corr(rows.map(r=>r[k]), obs).toFixed(4)}`);
}

// Trivial linear model on deltaCTH ALONE, fitted by least squares
const x = rows.map(r=>r.delta);
const n=x.length, mx=x.reduce((s,v)=>s+v,0)/n, my=obs.reduce((s,v)=>s+v,0)/n;
let num=0,den=0; for(let i=0;i<n;i++){num+=(x[i]-mx)*(obs[i]-my);den+=(x[i]-mx)**2;}
const slope=num/den, icpt=my-slope*mx;
const pred = x.map(v=>icpt+slope*v);
const mae = pred.reduce((s,p,i)=>s+Math.abs(p-obs[i]),0)/n;
const r2 = 1 - pred.reduce((s,p,i)=>s+(p-obs[i])**2,0)/obs.reduce((s,o)=>s+(o-my)**2,0);
console.log(`\nBASELINE: observed = ${icpt.toFixed(4)} + ${slope.toFixed(4)} * deltaCTH   (one input, one line of algebra)`);
console.log(`  MAE = ${mae.toFixed(4)}   R^2 = ${r2.toFixed(4)}`);
