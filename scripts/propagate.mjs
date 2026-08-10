/**
 * PROPAGATE the empirically-bounded 2026 inputs through the CTH kernel.
 * Turns the registered point estimate into a prediction interval, and measures
 * how much of the input uncertainty actually reaches the output.
 */
import fs from 'fs';
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GEOPOLITICAL } from './CTHmodules/cth-policy-variants.js';

const { anchor_2025, economic_pct, samples } = JSON.parse(fs.readFileSync('iran-2026-samples.json','utf8'));
const ACTOR = { power_index:.72, network_centrality:.68, legitimacy:.22, rationality:.50, charisma:.25,
  ideological_extremity:.80, momentum:.45, historical_role:'stabilizer', duration_of_influence:1,
  actor_volatility:.70, trigger_force:.62 };

const bridge = new CTHAIBridge(), adapter = new SnapshotAdapter();
let n = 0;
const run = async (pol, eco, soc) => {
  const id = `PR${n++}`;
  await bridge.registerContext(id, { id, year: 2026, political_stability: pol, economic_stability: eco,
    social_cohesion: soc, delta_cth: 0, black_swan: .72, observation_loop: .85,
    actor: ACTOR, population: 92_000_000 }, POLICY_GEOPOLITICAL, { adapter });
  await bridge.runFullPrediction(id);
  return bridge.contexts.get(id).lastPrediction.synthesis;
};

const q = (a, p) => { const s = [...a].sort((x,y)=>x-y); return s[Math.min(s.length-1, Math.floor(p*s.length))]; };

console.log(`Propagating ${samples.length} bounded input vectors...\n`);
const outs = [], pols = [], socs = [];
for (let i = 0; i < samples.length; i++) {
  const s = samples[i];
  const pol = s.v2x_rule, soc = (s.v2x_civlib + s.v2xcs_ccsi)/2, eco = s.economic;
  pols.push(pol); socs.push(soc);
  outs.push((await run(pol, eco, soc)).ultraCTH);
  if ((i+1) % 500 === 0) console.log(`  ${i+1}/${samples.length}`);
}

console.log('\n══ INPUT UNCERTAINTY (empirically bounded from V-Dem dynamics) ══');
console.log(`  political_stability  p5 ${q(pols,.05).toFixed(4)}  median ${q(pols,.5).toFixed(4)}  p95 ${q(pols,.95).toFixed(4)}   span ${(q(pols,.95)-q(pols,.05)).toFixed(4)}`);
console.log(`  social_cohesion      p5 ${q(socs,.05).toFixed(4)}  median ${q(socs,.5).toFixed(4)}  p95 ${q(socs,.95).toFixed(4)}   span ${(q(socs,.95)-q(socs,.05)).toFixed(4)}`);
console.log(`  economic_stability   fixed at ${economic_pct.toFixed(4)} (IMF -6.1% GDP = 1.5th percentile of all country-years)`);

console.log('\n══ OUTPUT — PREDICTION INTERVAL ══');
console.log(`  ultraCTH   p5 ${q(outs,.05).toFixed(4)}   median ${q(outs,.5).toFixed(4)}   p95 ${q(outs,.95).toFixed(4)}`);
console.log(`  90% interval width: ${(q(outs,.95)-q(outs,.05)).toFixed(4)}`);
const cmn = outs.filter(x => x < 0.5).length;
console.log(`  CMN (decline) share: ${cmn}/${outs.length} = ${(cmn/outs.length*100).toFixed(1)}%`);
console.log(`\n  registered point prediction: 0.497551`);
console.log(`  bounded median:              ${q(outs,.5).toFixed(6)}`);

console.log('\n══ HOW MUCH INPUT UNCERTAINTY REACHES THE OUTPUT? ══');
const inSpan = q(pols,.95)-q(pols,.05), outSpan = q(outs,.95)-q(outs,.05);
console.log(`  political_stability 90% span   ${inSpan.toFixed(4)}`);
console.log(`  ultraCTH 90% span              ${outSpan.toFixed(4)}`);
console.log(`  transmission ratio             ${(outSpan/inSpan).toFixed(2)}x`);
console.log(`\n  For reference the corpus outcome range is 0.20-0.78 (span 0.58),`);
console.log(`  so the prediction interval covers ${(outSpan/0.58*100).toFixed(0)}% of the outcome scale.`);

fs.writeFileSync('iran-2026-interval.json', JSON.stringify({
  n: outs.length, registered_point: 0.497551,
  input: { political: {p5:q(pols,.05), median:q(pols,.5), p95:q(pols,.95)},
           social: {p5:q(socs,.05), median:q(socs,.5), p95:q(socs,.95)}, economic: economic_pct },
  output: { p5:q(outs,.05), median:q(outs,.5), p95:q(outs,.95),
            width90: outSpan, cmn_share: cmn/outs.length }, anchor_2025 }, null, 1));
console.log('\nwrote iran-2026-interval.json');
