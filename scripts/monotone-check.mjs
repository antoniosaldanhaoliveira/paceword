/** Is ultraCTH monotone in the trend input? Verify on Iran AND on corpus events. */
import { CTHAIBridge } from './CTHmodules/cth-bridge.js';
import { SnapshotAdapter } from './CTHmodules/cth-data-adapters.js';
import { POLICY_GEOPOLITICAL, POLICY_GENERAL } from './CTHmodules/cth-policy-variants.js';

const bridge = new CTHAIBridge(), adapter = new SnapshotAdapter();
let n = 0;
const run = async (raw, policy) => {
  const id = `T${n++}`;
  await bridge.registerContext(id, { ...raw, id }, policy, { adapter });
  await bridge.runFullPrediction(id);
  return bridge.contexts.get(id).lastPrediction.synthesis.ultraCTH;
};

// ── A. determinism sanity: same input twice ─────────────────────────────────
const base = { year: 2026, political_stability: .22, economic_stability: .15, social_cohesion: .28, delta_cth: 0, black_swan: .72 };
const [d1, d2] = [await run(base, POLICY_GEOPOLITICAL), await run(base, POLICY_GEOPOLITICAL)];
console.log(`A. determinism: ${d1.toFixed(6)} vs ${d2.toFixed(6)} → ${d1 === d2 ? 'IDENTICAL ✓' : 'DIFFERS ✗'}`);

// ── B. fine sweep on Iran ───────────────────────────────────────────────────
console.log('\nB. fine sweep, Iran inputs (delta_cth from -0.40 to +0.30, step 0.05):');
const iran = [];
for (let d = -0.40; d <= 0.3001; d += 0.05) iran.push({ d: +d.toFixed(2), u: await run({ ...base, delta_cth: +d.toFixed(2) }, POLICY_GEOPOLITICAL) });
console.log('   ' + iran.map(r => `${r.d >= 0 ? '+' : ''}${r.d.toFixed(2)}:${r.u.toFixed(3)}`).join('  '));
let inv = 0;
for (let i = 1; i < iran.length; i++) if (iran[i].u < iran[i - 1].u) inv++;
console.log(`   direction reversals: ${inv} of ${iran.length - 1} steps  (0 = perfectly monotone increasing)`);

// ── C. same test on a real corpus event (French Revolution indicators) ──────
console.log('\nC. same sweep, French Revolution 1789 corpus indicators:');
const fr = { year: 1789, political_stability: .34, economic_stability: .30, social_cohesion: .48, black_swan: .42 };
const frs = [];
for (let d = -0.40; d <= 0.3001; d += 0.05) frs.push({ d: +d.toFixed(2), u: await run({ ...fr, delta_cth: +d.toFixed(2) }, POLICY_GENERAL) });
console.log('   ' + frs.map(r => `${r.d >= 0 ? '+' : ''}${r.d.toFixed(2)}:${r.u.toFixed(3)}`).join('  '));
let inv2 = 0;
for (let i = 1; i < frs.length; i++) if (frs[i].u < frs[i - 1].u) inv2++;
console.log(`   direction reversals: ${inv2} of ${frs.length - 1} steps`);

// ── D. Spearman rank correlation between delta_cth and ultraCTH ─────────────
const spearman = (a, b) => {
  const rank = v => { const s = [...v].sort((x, y) => x - y); return v.map(x => s.indexOf(x) + 1); };
  const [ra, rb] = [rank(a), rank(b)], n = a.length;
  const m = arr => arr.reduce((s, x) => s + x, 0) / n;
  const [ma, mb] = [m(ra), m(rb)];
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) { const x = ra[i] - ma, y = rb[i] - mb; num += x * y; da += x * x; db += y * y; }
  return num / Math.sqrt(da * db);
};
console.log(`\nD. Spearman rank corr (delta_cth → ultraCTH):`);
console.log(`   Iran inputs:       ${spearman(iran.map(r => r.d), iran.map(r => r.u)).toFixed(4)}`);
console.log(`   French Rev inputs: ${spearman(frs.map(r => r.d), frs.map(r => r.u)).toFixed(4)}`);
console.log(`   (1.00 = trend fully drives prediction; 0.00 = trend has no ordered effect)`);
