/** Direct interrogation of the entropy and "Monte Carlo" internals. */
const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
const bs = { tail_av: .52, tail_tf: .48, wave_freq: [.00073, .00061, .00088, .00079],
  phase_av: [4.17, 1.73], phase_tf: [2.91, 5.02], phase_sum: 3.14, phase_u: 6.2832,
  p_base: .20, p_range: .60, h_base: .15, h_range: .70, e_base: .05, e_range: .30,
  o_base: .10, o_range: .50, cross_scalar: .22, w_p: .34, w_h: .29, w_e: .20, w_o: .17 };

// verbatim reimplementation of _blackSwanCore
function blackSwan(av, tf, n = 25000) {
  const tailBias = clamp(av * bs.tail_av + tf * bs.tail_tf), d = [];
  for (let i = 0; i < n; i++) {
    const u = (i + .5) / n, f = bs.wave_freq;
    const w0 = .5 + .5 * Math.sin(i * f[0] + av * bs.phase_av[0] + tf * bs.phase_tf[0]);
    const w1 = .5 + .5 * Math.cos(i * f[1] + tf * bs.phase_av[1] + av * bs.phase_tf[1]);
    const w2 = .5 + .5 * Math.sin(i * f[2] + (av + tf) * bs.phase_sum);
    const w3 = .5 + .5 * Math.cos(i * f[3] + u * bs.phase_u);
    const p_ = clamp(bs.p_base + bs.p_range * (w0 * (1 - tailBias * .35) + tailBias * (.35 + u * .65)));
    const h = clamp(bs.h_base + bs.h_range * (w1 * (1 - tailBias * .28) + tailBias * (.32 + u * .58)));
    const e = clamp(bs.e_base + bs.e_range * (w2 * (1 - tailBias * .40) + tailBias * (.45 + av * .35)));
    const o = clamp(bs.o_base + bs.o_range * (w3 * (1 - tailBias * .30) + tailBias * (.28 + tf * .42)));
    const cross = bs.cross_scalar * Math.max(0, (p_ - .4) * (h - .4) + (p_ - .4) * (o - .4));
    d.push(clamp(bs.w_p * p_ + bs.w_h * h + bs.w_e * e + bs.w_o * o + cross));
  }
  d.sort((a, b) => a - b);
  return { VaR95: d[Math.floor(n * .95)], ES95: d.slice(Math.floor(n * .95)).reduce((a, b) => a + b, 0) / (n * .05),
           mean: d.reduce((a, b) => a + b, 0) / n };
}

console.log('═══ 1. Does "25,000 simulations" buy anything? (av=.60, tf=.62) ═══');
console.log('     nSim      VaR95       ES95       mean     Δ VaR95 vs 25k');
const ref = blackSwan(.60, .62, 25000);
for (const n of [10, 25, 100, 250, 1000, 5000, 25000, 100000]) {
  const r = blackSwan(.60, .62, n);
  console.log(`  ${String(n).padStart(7)}   ${r.VaR95.toFixed(6)}  ${r.ES95.toFixed(6)}  ${r.mean.toFixed(6)}   ${(r.VaR95 - ref.VaR95 >= 0 ? '+' : '') + (r.VaR95 - ref.VaR95).toExponential(2)}`);
}

console.log('\n═══ 2. Cycles traced: how much of a sine wave do 25,000 "samples" cover? ═══');
bs.wave_freq.forEach((f, i) => console.log(`  wave ${i}: freq ${f} × 25000 = ${(f * 25000).toFixed(2)} rad = ${(f * 25000 / (2 * Math.PI)).toFixed(2)} full cycles`));

console.log('\n═══ 3. Is VaR95 monotone in analytical_vulnerability? (tf held at .62) ═══');
let prev = null, rev = 0; const row = [];
for (let av = 0; av <= 1.0001; av += .05) {
  const v = blackSwan(+av.toFixed(2), .62, 25000).VaR95;
  if (prev !== null && v < prev) rev++;
  prev = v; row.push(`${av.toFixed(2)}:${v.toFixed(3)}`);
}
console.log('  ' + row.join('  '));
console.log(`  direction reversals: ${rev}/20   ${rev ? '→ QUASI-PERIODIC WOBBLE, not monotone risk' : '→ monotone'}`);

console.log('\n═══ 4. Shannon entropy: what is it actually computed over? ═══');
function entropy(cthGlobal, evei, blackSwanIndex) {
  const dims = [cthGlobal * 0.9, cthGlobal * 1.1, evei, blackSwanIndex];
  const sum = dims.reduce((a, b) => a + b, 0);
  let H = 0;
  dims.forEach(p => { const q = p / sum; if (q > 0) H -= q * Math.log2(q); });
  return H / Math.log2(dims.length);
}
console.log('  dims = [cthGlobal*0.9, cthGlobal*1.1, evei, blackSwanIndex]');
console.log('  → elements 0 and 1 are the SAME variable scaled 0.9 / 1.1 (collinear by construction)');
let lo = 1, hi = 0, loAt, hiAt;
for (let c = .05; c <= 1; c += .05) for (let e = .05; e <= 1; e += .05) for (let b = .05; b <= 1; b += .05) {
  const H = entropy(c, e, b);
  if (H < lo) { lo = H; loAt = [c, e, b]; }
  if (H > hi) { hi = H; hiAt = [c, e, b]; }
}
console.log(`\n  achievable range over the ENTIRE input space (8000 combos):`);
console.log(`    min ${lo.toFixed(4)}  at cth=${loAt[0].toFixed(2)} evei=${loAt[1].toFixed(2)} bs=${loAt[2].toFixed(2)}`);
console.log(`    max ${hi.toFixed(4)}  at cth=${hiAt[0].toFixed(2)} evei=${hiAt[1].toFixed(2)} bs=${hiAt[2].toFixed(2)}`);
console.log(`    span ${(hi - lo).toFixed(4)} of the nominal [0,1] scale`);

console.log('\n  realistic band (indicators 0.15–0.75, as in any real event):');
let rl = 1, rh = 0;
for (let c = .15; c <= .75; c += .05) for (let e = .15; e <= .75; e += .05) for (let b = .15; b <= .75; b += .05) {
  const H = entropy(c, e, b); rl = Math.min(rl, H); rh = Math.max(rh, H);
}
console.log(`    ${rl.toFixed(4)} → ${rh.toFixed(4)}   span ${(rh - rl).toFixed(4)}`);
