import {readFileSync} from 'fs';
const src=readFileSync('entropy-mc.mjs','utf8');
const fn=src.slice(src.indexOf('const clamp'),src.indexOf('console.log(\'═══ 1'));
const mod=await import('data:text/javascript,'+encodeURIComponent(fn+'\nexport{blackSwan};'));
const {blackSwan}=mod;
console.log('Does VaR95 CONVERGE as nSim grows? (a real Monte Carlo must)');
console.log('   nSim        VaR95      step-to-step change');
let prev=null;
for(const n of [25000,50000,75000,100000,200000,400000,800000]){
  const v=blackSwan(.60,.62,n).VaR95;
  console.log(`  ${String(n).padStart(8)}   ${v.toFixed(6)}   ${prev===null?'—':((v-prev>=0?'+':'')+(v-prev).toFixed(6))}`);
  prev=v;
}
console.log('\nA true MC error shrinks ~1/sqrt(n): 25k→800k (32x) should cut error ~5.7x.');
console.log('\nWhy: the sine argument is i*f, so n sets HOW MANY CYCLES are traced.');
for(const n of [25000,100000,800000]) console.log(`  nSim=${String(n).padStart(7)} → wave0 spans ${(0.00073*n/(2*Math.PI)).toFixed(1)} cycles`);
