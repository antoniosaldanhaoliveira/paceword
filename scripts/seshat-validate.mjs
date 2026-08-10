/**
 * DEEP-HISTORY VALIDATION — the properly powered test.
 *
 * n = 399 polity successions, 35 NGAs, -9300 to 1800.
 * Inputs and outcomes BOTH from Seshat. Nothing coded by the framework's author.
 *
 * CTH input mapping, declared before scoring:
 *   political_stability <- Gov            (government sophistication)
 *   economic_stability  <- mean(Money, Infra)
 *   social_cohesion     <- Info           (information systems)
 *   delta_cth           <- prior succession's SC change (observable at t; NOT the outcome)
 *   black_swan          <- 0.5            (neutral; Seshat carries no shock measure)
 *
 * CROSS-VALIDATION is leave-one-NGA-out (35 folds). Successions inside an NGA
 * share polities and history, so row-wise CV would leak.
 */
import fs from 'fs';
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GENERAL } from './CTHmodules/cth-policy-variants.js';

const S = JSON.parse(fs.readFileSync('seshat-successions.json', 'utf8'));
const bridge = new CTHAIBridge(), adapter = new SnapshotAdapter();

console.log(`Running CTH kernel on ${S.length} successions...`);
let n = 0;
for (const r of S) {
  const id = `SESH-${n++}`;
  await bridge.registerContext(id, {
    id, year: Math.round(r.t),
    political_stability: r.Gov,
    economic_stability: (r.Money + r.Infra) / 2,
    social_cohesion: r.Info,
    delta_cth: Math.max(-0.5, Math.min(0.5, r.prior)),
    black_swan: 0.5,
  }, POLICY_GENERAL, { adapter });
  await bridge.runFullPrediction(id);
  r.ultra = bridge.contexts.get(id).lastPrediction.synthesis.ultraCTH;
  if (n % 100 === 0) console.log(`  ${n}/${S.length}`);
}

// ── helpers ─────────────────────────────────────────────────────────────────
const mean = a => a.reduce((s, x) => s + x, 0) / a.length;
const mae  = (p, o) => mean(p.map((x, i) => Math.abs(x - o[i])));
const pearson = (a, b) => {
  const ma = mean(a), mb = mean(b);
  let nu = 0, da = 0, db = 0;
  for (let i = 0; i < a.length; i++) { const x = a[i]-ma, y = b[i]-mb; nu += x*y; da += x*x; db += y*y; }
  return da && db ? nu/Math.sqrt(da*db) : NaN;
};
const rank = v => { const s = [...v].map((x,i)=>[x,i]).sort((p,q)=>p[0]-q[0]); const r = Array(v.length); s.forEach((e,k)=>r[e[1]]=k+1); return r; };
const spearman = (a, b) => pearson(rank(a), rank(b));

// ridge least squares via normal equations
function fit(X, y, lam = 1e-6) {
  const p = X[0].length, A = Array.from({length:p},()=>Array(p).fill(0)), bv = Array(p).fill(0);
  for (let i = 0; i < X.length; i++) {
    for (let j = 0; j < p; j++) { bv[j] += X[i][j]*y[i]; for (let k = 0; k < p; k++) A[j][k] += X[i][j]*X[i][k]; }
  }
  for (let j = 0; j < p; j++) A[j][j] += lam;
  // gaussian elimination
  for (let j = 0; j < p; j++) {
    let piv = j;
    for (let i = j+1; i < p; i++) if (Math.abs(A[i][j]) > Math.abs(A[piv][j])) piv = i;
    [A[j], A[piv]] = [A[piv], A[j]]; [bv[j], bv[piv]] = [bv[piv], bv[j]];
    if (Math.abs(A[j][j]) < 1e-12) continue;
    for (let i = 0; i < p; i++) {
      if (i === j) continue;
      const f = A[i][j]/A[j][j];
      for (let k = j; k < p; k++) A[i][k] -= f*A[j][k];
      bv[i] -= f*bv[j];
    }
  }
  return bv.map((v, j) => Math.abs(A[j][j]) < 1e-12 ? 0 : v/A[j][j]);
}

const CC = ['Hier_n','Gov','Infra','Info','Money'];
const feats5   = r => [1, ...CC.map(c => r[c])];
const featPrior= r => [1, r.prior];

// ── leave-one-NGA-out CV ────────────────────────────────────────────────────
const NGAS = [...new Set(S.map(r => r.NGA))];
const out = { kernel: [], const05: [], clim: [], lin5: [], linPrior: [] }, obs = [];
for (const g of NGAS) {
  const tr = S.filter(r => r.NGA !== g), te = S.filter(r => r.NGA === g);
  const b5 = fit(tr.map(feats5), tr.map(r => r.outcome));
  const bp = fit(tr.map(featPrior), tr.map(r => r.outcome));
  const cm = mean(tr.map(r => r.outcome));
  for (const r of te) {
    obs.push(r.outcome);
    out.kernel.push(r.ultra);
    out.const05.push(0.5);
    out.clim.push(cm);
    out.lin5.push(Math.max(0, Math.min(1, feats5(r).reduce((s,x,i)=>s+x*b5[i], 0))));
    out.linPrior.push(Math.max(0, Math.min(1, featPrior(r).reduce((s,x,i)=>s+x*bp[i], 0))));
  }
}

console.log(`\n══ LEAVE-ONE-NGA-OUT RESULTS  (n = ${obs.length}, ${NGAS.length} folds) ══\n`);
console.log(`  ${'MODEL'.padEnd(26)}${'MAE'.padStart(8)}${'r'.padStart(9)}${'rho'.padStart(9)}`);
const rows = [
  ['CTH kernel (ultraCTH)', out.kernel],
  ['constant 0.5',          out.const05],
  ['climatology (mean)',    out.clim],
  ['linear, 5 Seshat CCs',  out.lin5],
  ['linear, prior change',  out.linPrior],
];
const res = {};
for (const [name, p] of rows) {
  const m = mae(p, obs), r = pearson(p, obs), rh = spearman(p, obs);
  res[name] = { MAE: m, r, rho: rh };
  console.log(`  ${name.padEnd(26)}${m.toFixed(4).padStart(8)}${(isNaN(r)?0:r).toFixed(4).padStart(9)}${(isNaN(rh)?0:rh).toFixed(4).padStart(9)}`);
}
const best = rows.map(([n_, p]) => [n_, mae(p, obs)]).sort((a, b) => a[1]-b[1])[0];
console.log(`\n  best MAE: ${best[0]} (${best[1].toFixed(4)})`);
console.log(`  kernel beats constant?    ${mae(out.kernel,obs) < mae(out.const05,obs) ? 'YES' : 'NO'}`);
console.log(`  kernel beats climatology? ${mae(out.kernel,obs) < mae(out.clim,obs) ? 'YES' : 'NO'}`);
console.log(`  kernel beats linear-5CC?  ${mae(out.kernel,obs) < mae(out.lin5,obs) ? 'YES' : 'NO'}`);

fs.writeFileSync('seshat-validation-results.json', JSON.stringify({
  n: obs.length, folds: NGAS.length, design: 'leave-one-NGA-out', results: res }, null, 1));
console.log('\nwrote seshat-validation-results.json');
