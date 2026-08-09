/** Closing gaps 2, 3, 4 from the audit. */
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { TimeSeriesAdapter, SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GEOPOLITICAL } from './CTHmodules/cth-policy-variants.js';

const bridge = new CTHAIBridge();
let n = 0;
const run = async (raw, adapter) => {
  const id = `G${n++}`;
  await bridge.registerContext(id, { ...raw, id }, POLICY_GEOPOLITICAL, { adapter });
  await bridge.runFullPrediction(id);
  return bridge.contexts.get(id).lastPrediction.synthesis;
};
const revs = a => { let r = 0; for (let i = 1; i < a.length; i++) if (a[i] < a[i - 1]) r++; return r; };
const spearman = (a, b) => {
  const rk = v => { const s = [...v].sort((x, y) => x - y); return v.map(x => s.indexOf(x) + 1); };
  const [ra, rb] = [rk(a), rk(b)], N = a.length, m = z => z.reduce((s, x) => s + x, 0) / N;
  const [ma, mb] = [m(ra), m(rb)];
  let nu = 0, da = 0, db = 0;
  for (let i = 0; i < N; i++) { const x = ra[i] - ma, y = rb[i] - mb; nu += x * y; da += x * x; db += y * y; }
  return nu / Math.sqrt(da * db);
};

// ══ GAP 2: is the kernel monotone when fed a REAL series (no abs(d))? ══════
console.log('═══ GAP 2 — TimeSeriesAdapter: monotone linear ramp, no Math.abs() ═══');
const ts = new TimeSeriesAdapter();
const ramp = (base, d) => Array.from({ length: 5 }, (_, i) => Math.max(0.01, Math.min(1, base + d * i / 4)));
const tsOut = [];
console.log('  trend    ultraCTH   call        (series before → after)');
for (let d = -0.40; d <= 0.3001; d += 0.05) {
  const dd = +d.toFixed(2);
  const s = await run({ year: 2026, series: { political: ramp(.22, dd), economic: ramp(.15, dd), social: ramp(.28, dd) } }, ts);
  tsOut.push({ d: dd, u: s.ultraCTH });
  console.log(`  ${(dd >= 0 ? '+' : '') + dd.toFixed(2)}    ${s.ultraCTH.toFixed(6)}   ${s.rmd_prediction ? 'RMD adapt' : 'CMN decl '}   ${ramp(.22, dd)[0].toFixed(2)} → ${ramp(.22, dd)[4].toFixed(2)}`);
}
console.log(`\n  reversals: ${revs(tsOut.map(r => r.u))}/${tsOut.length - 1}   Spearman: ${spearman(tsOut.map(r => r.d), tsOut.map(r => r.u)).toFixed(4)}`);
console.log(`  (SnapshotAdapter gave 5/14 reversals, Spearman 0.26)`);

// ══ GAP 3: how much does MY Iran coding drive the answer? ═════════════════
console.log('\n═══ GAP 3 — sensitivity to analyst judgement on the Iran indicators ═══');
const snap = new SnapshotAdapter();
const ACTOR = { power_index: .72, network_centrality: .68, legitimacy: .22, rationality: .50, charisma: .25,
  ideological_extremity: .80, momentum: .45, historical_role: 'stabilizer', duration_of_influence: 1,
  actor_volatility: .70, trigger_force: .62 };
const CODINGS = [
  ['mine (pessimistic)',   .22, .15, .28],
  ['optimistic analyst',   .40, .30, .45],
  ['very optimistic',      .55, .45, .60],
  ['very pessimistic',     .12, .08, .18],
  ['regime-survivalist',   .45, .20, .35],
  ['economy-only-bad',     .50, .10, .50],
];
console.log('  CODING                pol   eco   soc    ultraCTH   call');
const sens = [];
for (const [name, p, e, s] of CODINGS) {
  const r = await run({ year: 2026, political_stability: p, economic_stability: e, social_cohesion: s,
    delta_cth: 0, black_swan: .72, observation_loop: .85, actor: ACTOR, population: 92e6 }, snap);
  sens.push(r.ultraCTH);
  console.log(`  ${name.padEnd(20)} ${p.toFixed(2)}  ${e.toFixed(2)}  ${s.toFixed(2)}   ${r.ultraCTH.toFixed(6)}   ${r.rmd_prediction ? 'RMD adapt' : 'CMN decl'}`);
}
console.log(`\n  range across all six codings: ${Math.min(...sens).toFixed(4)} → ${Math.max(...sens).toFixed(4)}  (span ${(Math.max(...sens) - Math.min(...sens)).toFixed(4)})`);

// ══ GAP 4: multi-token / contested — the "Mule problem" engine ════════════
console.log('\n═══ GAP 4 — multi-token: Mojtaba/IRGC vs the protest movement ═══');
const PROTEST = { power_index: .35, network_centrality: .82, legitimacy: .70, rationality: .55, charisma: .60,
  ideological_extremity: .45, momentum: .75, historical_role: 'disruptor', duration_of_influence: 1,
  actor_volatility: .80, trigger_force: .70 };
const baseRaw = { year: 2026, political_stability: .22, economic_stability: .15, social_cohesion: .28,
  delta_cth: 0, black_swan: .72, observation_loop: .85, population: 92e6 };
const single = await run({ ...baseRaw, actor: ACTOR }, snap);
const multi  = await run({ ...baseRaw, actors: [ACTOR, PROTEST] }, snap);
for (const [label, r] of [['single actor (regime only)', single], ['contested (regime vs street)', multi]]) {
  console.log(`  ${label.padEnd(30)} ultraCTH ${r.ultraCTH.toFixed(6)}   ${r.rmd_prediction ? 'RMD' : 'CMN'}   bracket ${r.certainty_bracket}`);
}
console.log(`  Δ ultraCTH from adding an opposing actor: ${(multi.ultraCTH - single.ultraCTH >= 0 ? '+' : '') + (multi.ultraCTH - single.ultraCTH).toFixed(6)}`);
console.log(`  certainty degraded? ${single.certainty_bracket !== multi.certainty_bracket ? 'YES — ' + single.certainty_bracket + ' → ' + multi.certainty_bracket : 'NO — both ' + single.certainty_bracket}`);
