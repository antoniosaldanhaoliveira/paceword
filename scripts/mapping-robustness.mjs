/**
 * FAIRNESS CHECK: the CTH kernel scored r = -0.23 under MY mapping of Seshat
 * variables onto its three inputs. Is that the mapping's fault?
 * Sweeps every assignment of {Gov, Infra, Info, Money, Hier_n} to the three
 * CTH slots, plus delta_cth on/off. Reports the BEST case for the framework.
 */
import fs from 'fs';
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GENERAL, POLICY_GEOPOLITICAL } from './CTHmodules/cth-policy-variants.js';

const S = JSON.parse(fs.readFileSync('seshat-successions-full.json', 'utf8'));
const mean = a => a.reduce((s,x)=>s+x,0)/a.length;
const pearson = (a,b) => { const ma=mean(a),mb=mean(b); let n=0,da=0,db=0;
  for(let i=0;i<a.length;i++){const x=a[i]-ma,y=b[i]-mb;n+=x*y;da+=x*x;db+=y*y;} return da&&db?n/Math.sqrt(da*db):NaN; };
const rank = v => { const s=[...v].map((x,i)=>[x,i]).sort((p,q)=>p[0]-q[0]); const r=Array(v.length); s.forEach((e,k)=>r[e[1]]=k+1); return r; };
const spearman=(a,b)=>pearson(rank(a),rank(b));
const mae=(p,o)=>mean(p.map((x,i)=>Math.abs(x-o[i])));

const VARS = ['Gov','Infra','Info','Money','Hier_n'];
const obs = S.map(r => r.outcome);
const bridge = new CTHAIBridge(), adapter = new SnapshotAdapter();
let uid = 0;

async function score(pol, eco, soc, useDelta, policy) {
  const preds = [];
  for (const r of S) {
    const id = `M${uid++}`;
    await bridge.registerContext(id, {
      id, year: Math.round(r.t),
      political_stability: r[pol], economic_stability: r[eco], social_cohesion: r[soc],
      delta_cth: useDelta ? Math.max(-0.5, Math.min(0.5, r.prior)) : 0,
      black_swan: 0.5,
    }, policy, { adapter });
    await bridge.runFullPrediction(id);
    preds.push(bridge.contexts.get(id).lastPrediction.synthesis.ultraCTH);
  }
  return { r: pearson(preds, obs), rho: spearman(preds, obs), MAE: mae(preds, obs) };
}

const results = [];
for (const pol of VARS) for (const eco of VARS) for (const soc of VARS) {
  if (pol === eco || eco === soc || pol === soc) continue;
  const out = await score(pol, eco, soc, true, POLICY_GENERAL);
  results.push({ map: `${pol}/${eco}/${soc}`, delta: 'on', policy: 'GENERAL', ...out });
}
// best mapping, re-tested without delta and under a second policy
results.sort((a, b) => b.r - a.r);
const best = results[0].map.split('/');
results.push({ map: results[0].map, delta: 'off', policy: 'GENERAL',
               ...(await score(best[0], best[1], best[2], false, POLICY_GENERAL)) });
results.push({ map: results[0].map, delta: 'on', policy: 'GEOPOLITICAL',
               ...(await score(best[0], best[1], best[2], true, POLICY_GEOPOLITICAL)) });

console.log(`Swept ${results.length} CTH input configurations against n=${S.length} independent successions.\n`);
console.log(`  ${'MAPPING (pol/eco/soc)'.padEnd(26)}${'delta'.padStart(6)}${'policy'.padStart(14)}${'r'.padStart(9)}${'rho'.padStart(9)}${'MAE'.padStart(8)}`);
const sorted = [...results].sort((a, b) => b.r - a.r);
for (const x of sorted.slice(0, 6)) console.log(`  ${x.map.padEnd(26)}${x.delta.padStart(6)}${x.policy.padStart(14)}${x.r.toFixed(4).padStart(9)}${x.rho.toFixed(4).padStart(9)}${x.MAE.toFixed(4).padStart(8)}`);
console.log('  ...');
for (const x of sorted.slice(-3)) console.log(`  ${x.map.padEnd(26)}${x.delta.padStart(6)}${x.policy.padStart(14)}${x.r.toFixed(4).padStart(9)}${x.rho.toFixed(4).padStart(9)}${x.MAE.toFixed(4).padStart(8)}`);

const rs = results.map(x => x.r);
console.log(`\n  BEST CASE FOR THE FRAMEWORK: r = ${Math.max(...rs).toFixed(4)}`);
console.log(`  worst case:                  r = ${Math.min(...rs).toFixed(4)}`);
console.log(`  mean across configurations:  r = ${mean(rs).toFixed(4)}`);
console.log(`  configurations with r > 0:   ${rs.filter(x => x > 0).length}/${rs.length}`);
console.log(`\n  reference — plain linear regression on the same 5 variables,`);
console.log(`  leave-one-NGA-out:           r = +0.3835`);

fs.writeFileSync('mapping-robustness.json', JSON.stringify(results, null, 1));
console.log('\nwrote mapping-robustness.json');
