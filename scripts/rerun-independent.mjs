/**
 * PROPER RE-RUN: score the CTH kernel against INDEPENDENT (Seshat) targets
 * instead of the author's own outcome coding.
 */
import fs from 'fs';
import { buildUniversalCorpus } from './CTHmodules/cth-corpus.js';
import { CTHMasterPredictorEngine } from './CTHmodules/cth-core.js';
import { POLICY_GENERAL } from './CTHmodules/cth-policy-variants.js';

const matches = JSON.parse(fs.readFileSync('independent-matches.json', 'utf8'));
const corpus = buildUniversalCorpus();
const engine = new CTHMasterPredictorEngine();

const byId = new Map(corpus.map(e => [e.input.id, e]));
const use = matches.filter(m => m.q !== 'AMBIGUOUS');
console.log(`Scoring ${use.length} events with STRONG/DEFENSIBLE Seshat matches.\n`);

const recs = [];
for (const m of use) {
  const ev = byId.get(m.id);
  if (!ev) { console.log(`  !! ${m.id} not found in corpus`); continue; }
  const p = await engine.predictEvent(ev.input, POLICY_GENERAL);
  recs.push({ id: m.id, ultra: p.synthesis.ultraCTH, author: m.author, indep: m.indep,
              delta: ev.input.macro_context?.deltaCTH ?? null });
}

console.log(`  ${'EVENT'.padEnd(30)}${'ultraCTH'.padStart(9)}${'AUTHOR'.padStart(8)}${'SESHAT'.padStart(8)}`);
for (const r of recs) console.log(`  ${r.id.padEnd(30)}${r.ultra.toFixed(4).padStart(9)}${r.author.toFixed(3).padStart(8)}${r.indep.toFixed(3).padStart(8)}`);

const mae = (p, o) => p.reduce((s, x, i) => s + Math.abs(x - o[i]), 0) / p.length;
const mean = a => a.reduce((s, x) => s + x, 0) / a.length;
const pearson = (a, b) => {
  const ma = mean(a), mb = mean(b);
  let n = 0, da = 0, db = 0;
  for (let i = 0; i < a.length; i++) { const x = a[i]-ma, y = b[i]-mb; n += x*y; da += x*x; db += y*y; }
  return da && db ? n / Math.sqrt(da*db) : NaN;
};

const U = recs.map(r => r.ultra), A = recs.map(r => r.author), I = recs.map(r => r.indep), D = recs.map(r => r.delta);

console.log('\n══ SCORED AGAINST THE AUTHOR\'S OWN TARGETS (what the repo reports) ══');
console.log(`  kernel MAE            ${mae(U, A).toFixed(4)}`);
console.log(`  constant-0.5 MAE      ${mae(A.map(() => .5), A).toFixed(4)}`);
console.log(`  r(ultraCTH, target)   ${pearson(U, A).toFixed(4)}`);

console.log('\n══ SCORED AGAINST INDEPENDENT SESHAT TARGETS (never done before) ══');
console.log(`  kernel MAE            ${mae(U, I).toFixed(4)}`);
console.log(`  constant-0.5 MAE      ${mae(I.map(() => .5), I).toFixed(4)}`);
console.log(`  climatology MAE       ${mae(I.map(() => mean(I)), I).toFixed(4)}   (predict the mean)`);
console.log(`  r(ultraCTH, target)   ${pearson(U, I).toFixed(4)}`);
console.log(`  r(deltaCTH, target)   ${pearson(D, I).toFixed(4)}   <- the leakage feature, vs independent truth`);

// leave-one-out 1-feature linear regression on deltaCTH -> independent target
const loo = [];
for (let k = 0; k < recs.length; k++) {
  const xs = D.filter((_, i) => i !== k), ys = I.filter((_, i) => i !== k);
  const mx = mean(xs), my = mean(ys);
  let num = 0, den = 0;
  for (let i = 0; i < xs.length; i++) { num += (xs[i]-mx)*(ys[i]-my); den += (xs[i]-mx)**2; }
  const sl = den ? num/den : 0;
  loo.push(my + sl * (D[k] - mx));
}
console.log(`  linear(deltaCTH) LOO  ${mae(loo, I).toFixed(4)}`);

console.log('\n══ VERDICT ══');
const kernelBeatsConst = mae(U, I) < mae(I.map(() => .5), I);
const kernelBeatsClim  = mae(U, I) < mae(I.map(() => mean(I)), I);
const kernelBeatsLin   = mae(U, I) < mae(loo, I);
console.log(`  beats constant-0.5 on independent targets? ${kernelBeatsConst ? 'YES' : 'NO'}`);
console.log(`  beats climatology  on independent targets? ${kernelBeatsClim ? 'YES' : 'NO'}`);
console.log(`  beats linear       on independent targets? ${kernelBeatsLin ? 'YES' : 'NO'}`);
console.log(`\n  n = ${recs.length}. Underpowered — treat as a first probe, not a settled result.`);
