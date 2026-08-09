import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GEOPOLITICAL } from './CTHmodules/cth-policy-variants.js';
import fs from 'fs';
const v = JSON.parse(fs.readFileSync('vdem-iran.json','utf8'));

// independent mapping, declared before running
const pol = v.v2x_rule;                                  // rule of law
const soc = (v.v2x_civlib + v.v2xcs_ccsi) / 2;           // civil liberties + civil society
const eco = 0.15;                                        // IMF-derived; no V-Dem equivalent

const ACTOR={power_index:.72,network_centrality:.68,legitimacy:.22,rationality:.50,charisma:.25,
 ideological_extremity:.80,momentum:.45,historical_role:'stabilizer',duration_of_influence:1,
 actor_volatility:.70,trigger_force:.62};

const b=new CTHAIBridge(),a=new SnapshotAdapter();
const run=async(id,p,e,s)=>{await b.registerContext(id,{id,year:2026,political_stability:p,economic_stability:e,
 social_cohesion:s,delta_cth:0,black_swan:.72,observation_loop:.85,actor:ACTOR,population:92e6},POLICY_GEOPOLITICAL,{adapter:a});
 await b.runFullPrediction(id);return b.contexts.get(id).lastPrediction.synthesis;};

console.log('CODING COMPARISON');
console.log(`  political_stability   my judgement 0.220   V-Dem v2x_rule        ${pol.toFixed(3)}`);
console.log(`  social_cohesion       my judgement 0.280   V-Dem civlib+ccsi     ${soc.toFixed(3)}`);
console.log(`  economic_stability    my judgement 0.150   (IMF; no V-Dem proxy) ${eco.toFixed(3)}`);

const mine=await run('MINE',.22,.15,.28), vd=await run('VDEM',pol,eco,soc);
console.log('\nPREDICTION');
console.log(`  hand-coded (registered)   ultraCTH ${mine.ultraCTH.toFixed(6)}  ${mine.rmd_prediction?'RMD':'CMN'}  ${mine.certainty_bracket}`);
console.log(`  V-Dem-sourced             ultraCTH ${vd.ultraCTH.toFixed(6)}  ${vd.rmd_prediction?'RMD':'CMN'}  ${vd.certainty_bracket}`);
console.log(`  Δ from replacing judgement with measured data: ${(vd.ultraCTH-mine.ultraCTH>=0?'+':'')+(vd.ultraCTH-mine.ultraCTH).toFixed(6)}`);
