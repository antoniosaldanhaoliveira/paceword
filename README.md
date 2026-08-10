# CTHmodules — independent audit

An empirical audit of [CTHmodules](https://github.com/AlejoMalia/CTHmodules) v4.1 by Alejo Malia,
a framework that aims to implement Asimov's fictional *Psychohistory* as working software.

Audit date: **2026-08-09**. Everything here was produced by running the framework,
not by reading about it.

---

## Summary

The **engineering claims hold**. The **analytical claims do not survive independent targets.**

| Claim | Verdict |
|---|---|
| Deterministic, reproducible | ✅ verified — identical to 6 decimals across runs |
| JS ↔ Python kernel parity | ✅ verified independently — 8/8 fields, Δ = 0.000000 |
| Test suite passes | ✅ 13/13 |
| Published validation is honest | ✅ reproduced exactly against the committed report |
| "Validated on 5,100 years of history" | ❌ inputs and targets share provenance |
| "Shannon entropy" | ⚠️ near-constant on real inputs; two of four terms collinear |
| "High-density Monte Carlo" | ❌ no randomness; deterministic function of two scalars |
| "99.7% confidence" | ❌ returned 0.4976 at its lowest certainty tier |
| Beats trivial baselines | ❌ the repo's own harness reports `beats_linear: false` |
| Predicts independent outcomes (n=399) | ❌ r = −0.23; best of 62 configurations still −0.11, vs +0.38 for linear regression |

The author states the central flaw himself in his README, and built the harness that
reports it. That is to his credit and is the reason this audit was possible.

---

## Findings

### 1. The corpus is circular

The 32 calibration events are hand-coded tuples. One input, `deltaCTH`, correlates with
the target at **r = 0.9575**. A single-variable least-squares line reproduces the corpus
at MAE 0.0351 (in-sample).

The repo's own leave-one-out figures, reproduced exactly by this audit:

```
kernel  LOO MAE            0.1271
linear regression (4f)     0.0415   ← 3x better
kernel_adds_skill          false
beats_linear               false
```

### 2. The first independent-target test

Never previously run. 16 corpus events given outcome targets from two sources that know
nothing about CTHmodules:

- **[Seshat Crisis Consequences](https://github.com/datasets/seshat)** — 169 expert-coded
  crises, published 2023; severity 0–9 (ancient → 1918)
- **[V-Dem](https://github.com/vdeminstitute/vdemdata)** — measured 30-year trajectory in
  GDP per capita and rule of law, percentile-ranked against all 16,277 country-year
  windows in the dataset (1789 → 2025)

Every event→source match and the target construction were declared before scoring.

```
r(author's coding, independent targets)   -0.0918      Spearman -0.1769
r(ultraCTH, author's targets)             +0.6737
r(ultraCTH, independent targets)          +0.0505

MAE vs independent targets (n = 16):
  climatology (mean)     0.1399   <- best
  constant 0.5           0.1475
  linear(deltaCTH) LOO   0.1596
  CTH kernel             0.1865
  author's hand coding   0.2055   <- worst
```

The kernel tracks the author at r = 0.67 and independent reality at r = 0.05. Against
independent targets it loses to every trivial baseline.

**Robustness.** The V-Dem target embeds two of my choices — a 30-year horizon and rule of
law as the institutional axis. Both were swept (4 horizons × 4 indicators, `robustness.py`):

```
16 specifications tested
r range: -0.1509 to +0.3498   mean +0.0396
specifications with r > 0.3:  1/16
```

The near-zero agreement is not an artifact of the specification.

**Limits — still a probe, not a verdict.**

- n = 16 is small; the 95% CI on r = 0.05 spans roughly −0.45 to +0.53.
- **The independent sources disagree with each other.** On the single overlapping event
  (French Revolution) Seshat says 0.111 and V-Dem says 0.328 — a gap of 0.217. Some of the
  measured disagreement is noise in the yardstick, not error in the corpus.
- **Construct validity is genuinely contested.** The V-Dem measure scores the Chinese
  Revolution at 0.793 because GDP per capita rose 1949–1979 — true, and it passes over the
  Great Leap Forward. The Qin case cuts the other way: author 0.58 (successful
  unification), Seshat severity 7. Qin unified China *and* collapsed within fifteen years.

The fair reading is not "the corpus is wrong." It is: **the corpus has never been shown to
track any external measure, and attempting it reveals that the outcome construct itself is
under-defined.** A target that two expert sources code 0.217 apart cannot support a claimed
MAE of 0.0356.

### 3. Deep-history validation, n = 399 — the decisive test

The n=16 test above was underpowered. This one is not.

**Panel construction.** Seshat's Equinox file contains a complexity panel
(`AggrSCWarAgriRelig`): 35 NGAs, 373 polities, −13,600 → 1900, on a 100-year grid.
But that grid is **already an upsampling** — Seshat codes one value per *polity* and
repeats it across centuries:

```
consecutive century pairs      1,460
  same polity in both          1,050  (72%)
  change exactly zero            68%
```

So the analysis was rebuilt on the honest unit — **polity succession**:

```
polity spells   434
successions     399    35 NGAs, -9300 to 1800
exact-zero        2%   (vs 68% on the century grid)
```

Inputs and outcome are both Seshat, neither touched by the framework's author.
Outcome = complexity change at succession, percentile-ranked. Cross-validation is
**leave-one-NGA-out** (35 folds); successions inside a region share polities, so
row-wise CV would leak.

```
MODEL                          MAE        r      rho
CTH kernel (ultraCTH)       0.3048  -0.2293  -0.2302
constant 0.5                0.2501   0.0000  +0.0279
climatology (mean)          0.2504  -0.1850  -0.1938
linear, 5 Seshat CCs        0.2335  +0.3835  +0.4015   <- real signal
linear, prior change        0.2389  +0.2511  +0.1790
```

Two results, and the first is positive:

**There is genuine predictive signal in social complexity.** A five-feature linear
regression reaches r = 0.38 out-of-sample under clustered CV. Turchin's variables
carry real information about whether a successor polity will be more or less complex.

**The CTH kernel is anti-correlated at r = −0.23** — not uninformative but inverted.
You would do better negating its output.

**Fairness sweep.** The mapping of Seshat variables onto CTH's three input slots was
the auditor's choice, so all 62 configurations were tested — every permutation of
{Gov, Infra, Info, Money, Hier} across the three slots, delta on/off, two policies
(`mapping-robustness.mjs`):

```
BEST CASE FOR THE FRAMEWORK   r = -0.1083
worst case                    r = -0.2973
mean                          r = -0.2151
configurations with r > 0     0 / 62
reference: plain linear reg.  r = +0.3835
```

Not one configuration achieves positive correlation. The negative result is a
property of the kernel, not of the mapping.

This is the audit's strongest finding, because it is no longer "no skill detectable
in a small sample." n = 399, the signal is demonstrably present, a trivial model
finds it, and the framework finds its negative.

### 4. Why the century grid cannot be refined to 10-year points

A natural instinct is to interpolate for more resolution. It manufactures precision:

```
century grid (as shipped)     1,460 rows    72.0% identical to previous
10-year grid (interpolated)  14,573 rows    97.2% identical to previous

              n        SE(r)    95% CI      (at the real r = 0.3835)
honest      399       0.0428    +-0.0838
century   1,333       0.0234    +-0.0458
10-year  13,330       0.0074    +-0.0145
```

The correlation never changes. Only the error bars shrink — by ~6x — because rows
were copied, not because evidence was added.

### 5. The output barely responds to its inputs

Six very different analyst codings of the same event:

```
mine (pessimistic)   0.22 0.15 0.28 → 0.497551  decline
very optimistic      0.55 0.45 0.60 → 0.465208  decline
very pessimistic     0.12 0.08 0.18 → 0.506123  decline

span across all six codings: 0.0936      and the ordering inverts
```

Replacing hand-coded inputs with V-Dem measurements moved the prediction by **0.0037**.

### 6. Non-monotone in the trend

`ultraCTH` reverses direction 5–6 times out of 14 steps as the trend input sweeps
monotonically — under all six policies, and through both adapters. Root cause is
`Math.abs(d)` in `cth-data-adapters.js:255`, which discards the sign of the trend before
the engines see it.

### 7. Entropy and "Monte Carlo"

Entropy is computed over `[cthGlobal*0.9, cthGlobal*1.1, evei, blackSwan]` — elements 0
and 1 are the same variable. On realistic inputs it spans 0.792–0.998.

The "Monte Carlo" contains no randomness. It is 25,000 evenly spaced evaluations of four
sine waves, a function of exactly two scalars. Its own audit string calls it
`deterministic_trig_disruption_simulation`. Iteration count is a *shape* parameter, not a
precision one — the shipped 25,000 reports 0.833 against an asymptote of ~0.802.

### 8. Individual actors outweigh mass conditions

Adding one opposing actor moved the score by **0.126** — more than the 0.094 produced by
rewriting all three societal indicators. Asimov's founding axiom is the opposite:
individuals are noise, populations are signal.

---

## The pre-registered prediction

`results/iran-ledger.json` contains the first forward prediction this framework has made.
The author's own ledger is empty by design ("a track record is earned, not declared").

```
PRED-1-IRAN-SYSTEMIC-2026
predicted_ultraCTH   0.497551      (CMN — decline/stagnation)
certainty_bracket    BRACKET_BASE  (lowest)
resolution_date      2029-08-09
```

Resolution criterion, with sources named so it is resolvable by a third party:

> `observed = 0.4*A + 0.3*B + 0.3*C`
> **A** (V-Dem `v2x_regime` / Polity5) — velayat-e faqih remains governing authority: 1.0 / contested: 0.5 / replaced: 0.0
> **B** (IMF WEO, Iran annual average CPI) — <25%: 1.0 / 25–50%: 0.5 / >50%: 0.0
> **C** (UCDP/PRIO, prior 12 months) — <1000 deaths: 1.0 / 1000–10000: 0.5 / >10000: 0.0

**On what this prediction is worth.** It sits 0.0267 from the corpus mean (0.4709) and
0.0024 from a coin flip. It is the climatology baseline. Because the model returns ~0.5
for nearly any input, resolving it can **falsify** but cannot meaningfully **confirm**.

**On the 2026 inputs.** No independent expert coding exists for 2026 — V-Dem, Freedom
House and EIU all end at 2025, and V-Dem's 2026 wave ships around March 2027. V-Dem's
protocol cannot be replicated here either: its expert layer is aggregated by a Bayesian
IRT model across multiple *independent* coders, and several ratings from one source
would be read as high inter-coder agreement, returning a falsely narrow interval.

Instead `project-2026.py` bounds 2026 empirically from V-Dem's own dynamics. Across
27,469 country-years the median one-year change in `v2x_rule` is exactly 0.0000; across
481 autocratic-regime breakdowns it is still 0.0000, with a p5–p95 band of −0.105 to
+0.134. Iran's projected 2026 `v2x_rule` is therefore 0.104–0.343 (median 0.209) — and
the hand-coded input of 0.22 used in the registered prediction sits almost exactly on
that median. This is a projection with an empirical band, **not** a coding, and must
never be merged into V-Dem data.

**The commitment hash is not a timestamp.** The registry hashes an entry against itself;
`registered_at` is self-generated. The only third-party attestation is this repository's
git commit date. That is the point of committing it.

---

## Reproducing

Clone the framework as a sibling of `scripts/`, then run from that directory:

```bash
git clone --depth 1 https://github.com/AlejoMalia/CTHmodules.git
cd CTHmodules && npm test && npm run parity && npm run validate && cd ..

node scripts/analyze.mjs            # corpus leakage (r = 0.9575)
node scripts/iran-blind.mjs         # blind forecast + pre-registration
node scripts/policy-sweep.mjs       # all six policy variants
node scripts/entropy-mc.mjs         # entropy + "Monte Carlo" internals
node scripts/close-gaps.mjs         # adapter, sensitivity, multi-token
python3 scripts/independent-test.py # Seshat independent-target comparison
node scripts/rerun-independent.mjs  # kernel scored against Seshat targets
python3 scripts/build-vdem-targets.py  # V-Dem 30yr trajectory targets
node scripts/final-independent.mjs     # combined n=16 independent-target run
python3 scripts/robustness.py          # 16-specification robustness sweep

python3 scripts/seshat-transitions.py  # century-grid panel (shows the upsampling)
python3 scripts/seshat-spells.py       # collapse to 399 polity successions
node    scripts/seshat-validate.mjs    # leave-one-NGA-out validation
node    scripts/mapping-robustness.mjs # 62-configuration fairness sweep (slow)
python3 scripts/project-2026.py        # empirical 2026 bands from V-Dem dynamics
```

Independent datasets (both public, cloned via git):

```bash
git clone --depth 1 https://github.com/datasets/seshat.git data/seshat
git clone --depth 1 https://github.com/vdeminstitute/vdemdata.git data/vdemdata
pip install pyreadr    # to read vdem.RData (28,092 x 4,618, 1789-2025)
```

World Bank, OWID, UCDP, Polity5, Harvard Dataverse and Metaculus were unreachable from
the audit environment (egress policy denials), so they are cited but not used.

---

## What would settle it

This audit did the afternoon's work: 16 of the 32 events now have independent targets from
Seshat and V-Dem, and the kernel does not track them. But the exercise surfaced a deeper
problem than the one it set out to test.

**Before the framework can be validated, the target has to be defined.** Two expert sources
code the same event 0.217 apart. A 30-year GDP measure and a crisis-severity measure
disagree about the Chinese Revolution by 0.35. "Did this society adapt or collapse?" is not
currently a well-posed quantity, and no amount of entropy or simulation downstream can fix
an undefined dependent variable.

So the ordered next steps are:

1. **Define the construct.** Publish a coding manual with worked examples and boundary
   cases, so two coders working independently produce the same number.
2. **Measure inter-coder reliability.** Two or more coders, blind to each other, on all 32
   events. Report Krippendorff's alpha. If it is low, stop — nothing downstream is testable.
3. **Only then** re-run calibration against the independently coded targets, and compare
   to the linear baseline the repo's own harness already runs.

The remaining 16 events need pre-1789 economic series (Maddison) and non-European polity
coverage; both exist and neither was reachable from this audit environment.

---

## Sources

- [CTHmodules](https://github.com/AlejoMalia/CTHmodules) · [cthmodules.cc](https://www.cthmodules.cc/)
- [Seshat: Global History Databank](https://github.com/datasets/seshat)
- [V-Dem Institute](https://github.com/vdeminstitute/vdemdata)
- Goldstone et al., [*A Global Model for Forecasting Political Instability*](https://www.systemicpeace.org/vlibrary/PITFForecastingInstabilityAJPS2010.pdf), AJPS 2010 — 80%+ two-year out-of-sample accuracy, the fair benchmark
- [Explainable models for forecasting political instability](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0254350), PLOS One 2021 — AUPRC 0.108–0.115, showing how hard this genuinely is
- Rocha, [*Towards Asimov's Psychohistory: Harnessing Topological Data Analysis, AI and Social Media data*](https://arxiv.org/abs/2407.03446), arXiv:2407.03446, 2024 — a theoretical position paper arguing feasibility; reports no forecasting track record, so it is a statement of ambition rather than evidence
