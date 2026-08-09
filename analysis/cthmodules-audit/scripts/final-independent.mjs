/**
 * THE AFTERNOON'S WORK
 * Score the CTH kernel against independent outcome targets from two sources
 * that know nothing about CTHmodules:
 *   Seshat Crisis Consequences (expert-coded crisis severity, ancient -> 1918)
 *   V-Dem (measured 30-year economic + institutional trajectory, 1789 -> 2025)
 */
import fs from 'fs';
import { buildUniversalCorpus } from './CTHmodules/cth-corpus.js';
import { CTHMasterPredictorEngine } from './CTHmodules/cth-core.js';
import { POLICY_GENERAL } from './CTHmodules/cth-policy-variants.js';

const seshat = JSON.parse(fs.readFileSync('independent-matches.json', 'utf8')).filter(m => m.q !== 'AMBIGUOUS');
const vdem   = JSON.parse(fs.readFileSync('vdem-targets.json', 'utf8')).filter(m => m.q !== 'AMBIGUOUS');
const corpus = buildUniversalCorpus();
const engine = new CTHMasterPredictorEngine();
const byId   = new Map(corpus.map(e => [e.input.id, e]));

// ── where the two independent sources overlap, do they agree with each other? ──
const overlap = seshat.filter(s => vdem.some(v => v.id === s.id))
  .map(s => ({ id: s.id, seshat: s.indep, vdem: vdem.find(v => v.id === s.id).indep }));
console.log('══ DO THE TWO INDEPENDENT SOURCES AGREE WITH EACH OTHER? ══');
for (const o of overlap) console.log(`  ${o.id.padEnd(28)} Seshat ${o.seshat.toFixed(3)}   V-Dem ${o.vdem.toFixed(3)}   |Δ| ${Math.abs(o.seshat-o.vdem).toFixed(3)}`);
console.log(`  (n=${overlap.length} overlapping events)\n`);

// combined target: mean of available independent sources — declared before scoring
const combined = new Map();
for (const s of seshat) combined.set(s.id, { vals: [s.indep], src: ['Seshat'] });
for (const v of vdem) {
  if (combined.has(v.id)) { combined.get(v.id).vals.push(v.indep); combined.get(v.id).src.push('V-Dem'); }
  else combined.set(v.id, { vals: [v.indep], src: ['V-Dem'] });
}

const recs = [];
for (const [id, { vals, src }] of combined) {
  const ev = byId.get(id);
  if (!ev) continue;
  const p = await engine.predictEvent(ev.input, POLICY_GENERAL);
  recs.push({ id, ultra: p.synthesis.ultraCTH, author: ev.observed_outcome,
              indep: vals.reduce((a, b) => a + b, 0) / vals.length, src: src.join('+'),
              delta: ev.input.macro_context?.deltaCTH ?? 0 });
}
recs.sort((a, b) => a.id.localeCompare(b.id));

console.log('══ FULL INDEPENDENT-TARGET TABLE ══');
console.log(`  ${'EVENT'.padEnd(30)}${'ultraCTH'.padStart(9)}${'AUTHOR'.padStart(8)}${'INDEP'.padStart(8)}  SOURCE`);
for (const r of recs) console.log(`  ${r.id.padEnd(30)}${r.ultra.toFixed(4).padStart(9)}${r.author.toFixed(3).padStart(8)}${r.indep.toFixed(3).padStart(8)}  ${r.src}`);

const mean = a => a.reduce((s, x) => s + x, 0) / a.length;
const mae  = (p, o) => p.reduce((s, x, i) => s + Math.abs(x - o[i]), 0) / p.length;
const pearson = (a, b) => {
  const ma = mean(a), mb = mean(b);
  let n = 0, da = 0, db = 0;
  for (let i = 0; i < a.length; i++) { const x = a[i]-ma, y = b[i]-mb; n += x*y; da += x*x; db += y*y; }
  return da && db ? n / Math.sqrt(da*db) : NaN;
};
const spearman = (a, b) => { const rk = v => v.map(x => [...v].sort((p,q)=>p-q).indexOf(x)+1); return pearson(rk(a), rk(b)); };

// LOO linear regression on the 4 corpus features -> independent target
const feats = r => [r.delta, r.author * 0 + 1];  // intercept + deltaCTH only (n too small for 4f)
const looLinear = (recs, targetKey) => {
  const preds = [];
  for (let k = 0; k < recs.length; k++) {
    const tr = recs.filter((_, i) => i !== k);
    const xs = tr.map(r => r.delta), ys = tr.map(r => r[targetKey]);
    const mx = mean(xs), my = mean(ys);
    let num = 0, den = 0;
    for (let i = 0; i < xs.length; i++) { num += (xs[i]-mx)*(ys[i]-my); den += (xs[i]-mx)**2; }
    preds.push(my + (den ? num/den : 0) * (recs[k].delta - mx));
  }
  return preds;
};

const U = recs.map(r => r.ultra), A = recs.map(r => r.author), I = recs.map(r => r.indep);
console.log(`\n══ RESULTS  (n = ${recs.length}) ══`);
console.log('\n  Agreement between the author\'s coding and independent reality:');
console.log(`    Pearson  r(author, independent)   ${pearson(A, I).toFixed(4)}`);
console.log(`    Spearman rho                      ${spearman(A, I).toFixed(4)}`);
console.log('\n  Kernel performance:');
console.log(`    r(ultraCTH, author's targets)     ${pearson(U, A).toFixed(4)}`);
console.log(`    r(ultraCTH, independent targets)  ${pearson(U, I).toFixed(4)}`);
console.log('\n  MAE against INDEPENDENT targets:');
const linI = looLinear(recs, 'indep');
const rows = [
  ['CTH kernel (ultraCTH)', mae(U, I)],
  ['constant 0.5',          mae(I.map(() => .5), I)],
  ['climatology (mean)',    mae(I.map(() => mean(I)), I)],
  ['linear(deltaCTH) LOO',  mae(linI, I)],
  ["author's hand coding",  mae(A, I)],
];
for (const [n, v] of rows) console.log(`    ${n.padEnd(24)} ${v.toFixed(4)}`);
const best = rows.slice().sort((a, b) => a[1] - b[1])[0];
console.log(`\n    best: ${best[0]}`);
console.log(`    kernel beats constant?    ${mae(U,I) < mae(I.map(()=>.5),I) ? 'YES' : 'NO'}`);
console.log(`    kernel beats climatology? ${mae(U,I) < mae(I.map(()=>mean(I)),I) ? 'YES' : 'NO'}`);
console.log(`    kernel beats linear?      ${mae(U,I) < mae(linI,I) ? 'YES' : 'NO'}`);

fs.writeFileSync('final-independent-results.json', JSON.stringify({
  n: recs.length, records: recs,
  r_author_vs_independent: pearson(A, I), spearman_author_vs_independent: spearman(A, I),
  r_kernel_vs_author: pearson(U, A), r_kernel_vs_independent: pearson(U, I),
  mae: Object.fromEntries(rows.map(([k, v]) => [k, v])),
  overlap_between_sources: overlap,
}, null, 1));
console.log('\nwrote final-independent-results.json');
