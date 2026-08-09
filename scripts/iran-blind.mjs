/**
 * BLIND FORWARD TEST — Iran, coded 2026-08-09.
 *
 * PROTOCOL: every input below is coded from PUBLISHED indicators observable
 * today. The outcome is NOT known to anyone — it resolves 2029-08-09.
 * This is the opposite of the corpus, where inputs were coded with hindsight.
 */
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GEOPOLITICAL } from './CTHmodules/cth-policy-variants.js';
import PredictionRegistry from './CTHmodules/cth-prediction-registry.js';

// ── INPUT CODING (justified from published data, blind to outcome) ───────────
const CODING = {
  political_stability: [0.22, 'Khamenei killed 2026-02-28; Mojtaba appointed amid contested succession; impeachment moves vs FM Araghchi; ultrahardliner/pragmatist split; executions for espionage'],
  economic_stability:  [0.15, 'IMF: GDP -6.1%, inflation 68.9% (2026); rial 1.9M/USD from ~1.0M; min wage covers 37% of basic basket; bread +140% YoY'],
  social_cohesion:     [0.28, 'Protests in all 31 provinces since 2025-12-28; thousands killed Jan 8-9 crackdown; retiree/youth protests ongoing Aug 2026'],
  black_swan:          [0.72, 'Exogenous military intervention is the dominant driver; ~900 strikes in 12h; Hormuz disruption'],
  observation_loop:    [0.85, 'Extreme reflexivity: regime explicitly reacts to published collapse forecasts (Asimov ignorance-axiom violation)'],
};

const ACTOR = { // Mojtaba Khamenei / IRGC consolidation
  power_index: 0.72, network_centrality: 0.68, legitimacy: 0.22, rationality: 0.50,
  charisma: 0.25, ideological_extremity: 0.80, momentum: 0.45,
  historical_role: 'stabilizer', duration_of_influence: 1, actor_volatility: 0.70, trigger_force: 0.62
};

const RESOLUTION = {
  description: 'Islamic Republic of Iran systemic trajectory, 3-year horizon from 2026-08-09',
  resolution_criterion:
    'observed_outcome = 0.4*A + 0.3*B + 0.3*C assessed on 2029-08-09. ' +
    'A (source: V-Dem v2x_regime / Polity5): velayat-e faqih remains the governing authority (1.0) / contested or transitional (0.5) / replaced (0.0). ' +
    'B (source: IMF World Economic Outlook, Iran annual average CPI): <25% (1.0) / 25-50% (0.5) / >50% (0.0). ' +
    'C (source: UCDP/PRIO Armed Conflict Dataset, best estimate, Iran, prior 12 months): <1000 battle-related deaths (1.0) / 1000-10000 (0.5) / >10000 (0.0). ' +
    'If a named source is unavailable at resolution, the successor dataset published by the same institution is used.',
  resolution_date: '2029-08-09',
  policy_version: 'POLICY_GEOPOLITICAL 4.1'
};

const mk = (delta) => ({
  id: 'IRAN-SYSTEMIC-2026', year: 2026,
  political_stability: CODING.political_stability[0],
  economic_stability:  CODING.economic_stability[0],
  social_cohesion:     CODING.social_cohesion[0],
  delta_cth: delta,
  black_swan: CODING.black_swan[0],
  observation_loop: CODING.observation_loop[0],
  actor: ACTOR, population: 92_000_000
});

const bridge = new CTHAIBridge();
const adapter = new SnapshotAdapter();
const run = async (id, delta) => {
  await bridge.registerContext(id, mk(delta), POLICY_GEOPOLITICAL, { adapter });
  await bridge.runFullPrediction(id);
  return bridge.contexts.get(id).lastPrediction;   // raw predictEvent result (has .synthesis)
};

console.log('\n═══ INPUT CODING (blind — outcome unknown to all parties) ═══');
for (const [k, [v, why]] of Object.entries(CODING)) console.log(`  ${k.padEnd(20)} ${v.toFixed(2)}  ${why}`);

// ── RUN 1: the honest blind setting. We do NOT know deltaCTH, so it is 0. ────
const blind = await run('IRAN-BLIND', 0);
const s = blind.synthesis;
const pred = blind;
console.log('\n═══ RUN 1 — BLIND (delta_cth = 0, the only honest forward setting) ═══');
console.log(`  ultraCTH            ${s.ultraCTH.toFixed(6)}`);
console.log(`  prediction          ${s.rmd_prediction}`);
console.log(`  certainty bracket   ${s.certainty_bracket}`);
console.log(`  hash                ${pred.hash?.slice(0, 32)}`);

// ── RUN 2: sensitivity to the one input a real forecaster cannot know ───────
console.log('\n═══ RUN 2 — SENSITIVITY SWEEP over delta_cth ═══');
console.log('  delta_cth   ultraCTH    prediction');
const sweep = [];
for (const d of [-0.40, -0.30, -0.20, -0.10, 0, 0.10, 0.20, 0.30]) {
  const r = await run(`IRAN-D${d}`, d);
  const sy = r.synthesis;
  sweep.push({ d, u: sy.ultraCTH });
  console.log(`  ${(d >= 0 ? '+' : '') + d.toFixed(2)}       ${sy.ultraCTH.toFixed(6)}    ${sy.rmd_prediction}`);
}
const lo = Math.min(...sweep.map(x => x.u)), hi = Math.max(...sweep.map(x => x.u));
console.log(`\n  SWING: ${lo.toFixed(4)} → ${hi.toFixed(4)}  (range ${(hi - lo).toFixed(4)})`);
console.log(`  For reference, the entire corpus outcome range is 0.20 → 0.78 (range 0.58).`);

// ── REGISTER the blind prediction in the (empty) pre-registration ledger ────
const reg = new PredictionRegistry('./results/iran-ledger.json');
const entry = reg.register(pred, RESOLUTION);
console.log('\n═══ PRE-REGISTERED (SHA-256 committed, unresolvable until 2029) ═══');
console.log(`  id                  ${entry.id}`);
console.log(`  predicted_ultraCTH  ${entry.predicted_ultraCTH}`);
console.log(`  rmd_prediction      ${entry.rmd_prediction}`);
console.log(`  resolution_date     ${entry.resolution_date}`);
console.log(`  commitment_hash     ${entry.commitment_hash?.slice(0, 32)}`);
console.log(`  verify()            ${JSON.stringify(reg.verify(entry.id))}`);
console.log(`  score()             ${JSON.stringify(reg.score())}`);
