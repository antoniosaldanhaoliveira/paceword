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

### 3. The output barely responds to its inputs

Six very different analyst codings of the same event:

```
mine (pessimistic)   0.22 0.15 0.28 → 0.497551  decline
very optimistic      0.55 0.45 0.60 → 0.465208  decline
very pessimistic     0.12 0.08 0.18 → 0.506123  decline

span across all six codings: 0.0936      and the ordering inverts
```

Replacing hand-coded inputs with V-Dem measurements moved the prediction by **0.0037**.

### 4. Non-monotone in the trend

`ultraCTH` reverses direction 5–6 times out of 14 steps as the trend input sweeps
monotonically — under all six policies, and through both adapters. Root cause is
`Math.abs(d)` in `cth-data-adapters.js:255`, which discards the sign of the trend before
the engines see it.

### 5. Entropy and "Monte Carlo"

Entropy is computed over `[cthGlobal*0.9, cthGlobal*1.1, evei, blackSwan]` — elements 0
and 1 are the same variable. On realistic inputs it spans 0.792–0.998.

The "Monte Carlo" contains no randomness. It is 25,000 evenly spaced evaluations of four
sine waves, a function of exactly two scalars. Its own audit string calls it
`deterministic_trig_disruption_simulation`. Iteration count is a *shape* parameter, not a
precision one — the shipped 25,000 reports 0.833 against an asymptote of ~0.802.

### 6. Individual actors outweigh mass conditions

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
