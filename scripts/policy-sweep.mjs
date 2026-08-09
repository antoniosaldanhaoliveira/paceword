/** Does the Iran directional call survive a change of Policy? */
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import DEFAULT_POLICY from './CTHmodules/cth-policy-schema.js';
import { POLICY_GENERAL, POLICY_GEOPOLITICAL, POLICY_ECONOMIC, POLICY_TECHNOLOGICAL, POLICY_REVOLUTIONARY }
  from './CTHmodules/cth-policy-variants.js';

const POLICIES = [
  ['DEFAULT',       DEFAULT_POLICY],
  ['GENERAL',       POLICY_GENERAL],
  ['GEOPOLITICAL',  POLICY_GEOPOLITICAL],
  ['ECONOMIC',      POLICY_ECONOMIC],
  ['TECHNOLOGICAL', POLICY_TECHNOLOGICAL],
  ['REVOLUTIONARY', POLICY_REVOLUTIONARY],
];

const IRAN = {
  year: 2026, political_stability: 0.22, economic_stability: 0.15, social_cohesion: 0.28,
  black_swan: 0.72, observation_loop: 0.85, population: 92_000_000,
  actor: { power_index: .72, network_centrality: .68, legitimacy: .22, rationality: .50, charisma: .25,
           ideological_extremity: .80, momentum: .45, historical_role: 'stabilizer',
           duration_of_influence: 1, actor_volatility: .70, trigger_force: .62 }
};

const bridge = new CTHAIBridge(), adapter = new SnapshotAdapter();
let n = 0;
const run = async (policy, delta) => {
  const id = `P${n++}`;
  await bridge.registerContext(id, { ...IRAN, id, delta_cth: delta }, policy, { adapter });
  await bridge.runFullPrediction(id);
  const p = bridge.contexts.get(id).lastPrediction;
  return { u: p.synthesis.ultraCTH, rmd: p.synthesis.rmd_prediction,
           br: p.synthesis.certainty_bracket, eng: p.engines ?? p };
};

// ── 1. Blind setting (delta_cth = 0) under every policy ─────────────────────
console.log('\n═══ IRAN, BLIND (delta_cth = 0) — ALL SIX POLICIES ═══');
console.log('  POLICY           ultraCTH   CALL      BRACKET');
const blind = [];
for (const [name, pol] of POLICIES) {
  const r = await run(pol, 0);
  blind.push({ name, ...r });
  console.log(`  ${name.padEnd(15)} ${r.u.toFixed(6)}   ${(r.rmd ? 'RMD adapt' : 'CMN decl ').padEnd(9)} ${r.br}`);
}
const us = blind.map(b => b.u);
console.log(`\n  spread across policies: ${Math.min(...us).toFixed(4)} → ${Math.max(...us).toFixed(4)}  (range ${(Math.max(...us) - Math.min(...us)).toFixed(4)})`);
console.log(`  directional call:       ${new Set(blind.map(b => b.rmd)).size === 1 ? 'UNANIMOUS ' + (blind[0].rmd ? 'RMD' : 'CMN') : 'SPLIT ✗'}`);

// ── 2. Full delta sweep × policy ────────────────────────────────────────────
const DELTAS = [-0.40, -0.30, -0.20, -0.10, 0, 0.10, 0.20, 0.30];
console.log('\n═══ delta_cth × POLICY  (ultraCTH; * = flips to RMD/adapt) ═══');
console.log('  POLICY           ' + DELTAS.map(d => ((d >= 0 ? '+' : '') + d.toFixed(2)).padStart(7)).join(''));
const grid = {};
for (const [name, pol] of POLICIES) {
  const row = [];
  for (const d of DELTAS) row.push(await run(pol, d));
  grid[name] = row;
  console.log(`  ${name.padEnd(15)} ` + row.map(r => (r.u.toFixed(3) + (r.rmd ? '*' : ' ')).padStart(7)).join(''));
}

// ── 3. Stability of the call ────────────────────────────────────────────────
const all = Object.values(grid).flat();
const flips = all.filter(r => r.rmd).length;
console.log(`\n  cells: ${all.length}   RMD/adapt: ${flips}   CMN/decline: ${all.length - flips}`);
console.log(`  global ultraCTH range: ${Math.min(...all.map(r => r.u)).toFixed(4)} → ${Math.max(...all.map(r => r.u)).toFixed(4)}`);

// ── 4. Monotonicity per policy ──────────────────────────────────────────────
console.log('\n═══ Is ultraCTH monotone in delta_cth, per policy? ═══');
for (const [name] of POLICIES) {
  const u = grid[name].map(r => r.u);
  let rev = 0;
  for (let i = 1; i < u.length; i++) if (u[i] < u[i - 1]) rev++;
  console.log(`  ${name.padEnd(15)} reversals ${rev}/${u.length - 1}   ${rev === 0 ? 'monotone ✓' : 'NON-MONOTONE ✗'}`);
}

// ── 5. Which engine dominates? ──────────────────────────────────────────────
console.log('\n═══ ENGINE RISK BREAKDOWN (delta_cth = 0) ═══');
const KEYS = ['foundation_risk', 'temporal_risk', 'dynamics_risk', 'chaos_shield_risk', 'butterfly_risk', 'analytical_vulnerability'];
console.log('  POLICY           ' + KEYS.map(k => k.split('_')[0].slice(0, 8).padStart(10)).join(''));
for (const [name, pol] of POLICIES) {
  const r = await run(pol, 0);
  const e = r.eng;
  console.log(`  ${name.padEnd(15)} ` + KEYS.map(k => {
    const v = e?.[k]; const num = typeof v === 'number' ? v : v?.score ?? v?.value;
    return (typeof num === 'number' ? num.toFixed(4) : '—').padStart(10);
  }).join(''));
}
