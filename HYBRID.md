# Version 3 — the hybrid layer

Can the tool become a superforecaster? The 2024–2026 literature finally gives a
precise answer: **a statistical model cannot, but a model + retrieval + reconciliation
+ calibration pipeline reached superforecaster parity in late 2025.** This file
replicates that architecture on our pre-registered Iran question, with every
judgement increment written down.

---

## The research: who is actually best (as of August 2026)

**Humans, ranked by documented track record:**

| Who | Evidence | Method |
|---|---|---|
| [Samotsvety](https://samotsvety.org/track-record/) | Won CSET-Foretell/INFER by ~2x the next team, multiple years; members' GJOpen Brier ratios 0.67–0.71 vs median | Small team of independent forecasters; each forecasts alone, then aggregate; Fermi decomposition; explicit base rates; frequent updates |
| Superforecasters (GJP lineage) | [ForecastBench](https://arxiv.org/abs/2409.19839): Brier 0.093 vs public 0.107; on extended data 0.068 vs 0.083 | Outside view first; granular probabilities; small frequent updates; teaming; log-odds extremizing of aggregates |
| Metaculus Pros | [Q2 2026 AIB results](https://www.lesswrong.com/posts/Surnjh8A4WjgtQTkZ/q2-ai-benchmark-results-pros-maintain-clear-lead): beat all bots every quarter for 1.5 years | Recalibrated community aggregation |

**Machines:**

| System | Result | Architecture |
|---|---|---|
| [AIA Forecaster](https://arxiv.org/abs/2511.07678) (Nov 2025) | **0.1125 vs superforecaster median 0.1110 on ForecastBench — parity, first ever** | (1) agentic search over high-quality news; (2) supervisor agent reconciling disparate forecasts; (3) statistical calibration against LLM biases. Underperforms liquid prediction markets, but ensemble with market consensus beats consensus alone |
| Metaculus AIB best bot (metac-claude + asknews) | top ~3% of 1130 humans, Spring 2026 Cup | LLM + news retrieval |
| Halawi et al. 2024 | approached crowd aggregate | retrieval-augmented LLM, fine-tuned |
| [ViEWS/Conflictology](https://journals.sagepub.com/doi/10.1177/00223433241300862) (Hegre et al.) | leads the 2023/24 fatalities challenge | ensembles forecasting full probability *distributions* of conflict deaths, country-month |

**Convergent findings across all of them:**
1. The aggregate of several *independent* forecasts beats any single one; extremizing the
   aggregate in log-odds (the GJP result) adds skill — but only for genuinely independent inputs.
2. Retrieval is where machine skill comes from; the model supplies the prior.
3. Pros still lead bots head-to-head (every Metaculus quarter to date), but the gap closed
   from "not close" (2024) to "parity on one benchmark" (AIA, late 2025).
4. Nobody reports a bare number: distributions, intervals, and named resolution criteria.

## What that means for this tool

Our walk-forward reference class **is** the outside view — the thing superforecasters do
*first*. What it lacks is everything they do *second*: retrieval, reconciliation,
calibration, updating. Those are now buildable. The pipeline below is the AIA recipe
executed by one analyst-LLM session — with the honesty caveat that its "multiple
perspectives" come from one source and are therefore correlated, exactly the
IRT-independence problem documented in `project-2026.py`. This is a demonstration of the
architecture, not a claim of superforecaster status. Status is earned on a scored ledger.

---

## The hybrid forecast, executed 2026-08-10

**Question (pre-registered):** criterion A of `PRED-1-IRAN-SYSTEMIC-2026` — is
velayat-e faqih replaced as the governing authority of Iran by **2029-08-09**?
Construct: regime *replacement* (`v2regdur` reset), not reclassification.

### Step 1 — outside view (the tool, nothing else)

2-year bucket rates from v2 (window ending 2023), converted to the 3.25-year horizon via
p₃.₂₅ = 1 − (1−p₂)^1.625:

```
scenario                                   p(2y)      p(3.25y)
A:  continuous, electoral autocracy       0.0614   ->  0.098
A2: continuous, closed autocracy          0.0447   ->  0.072
B:  new regime, electoral autocracy       0.0953   ->  0.150
B2: new regime, closed autocracy          0.1965   ->  0.299
```

### Step 2 — reconcile the scenario fork (supervisor step)

Is post-Feb-2026 Iran in the "young regime" hazard class? The 1989 Khomeini→Khamenei
succession did NOT reset V-Dem's regime clock — orderly succession inside velayat-e faqih
is the same regime. But 2026 is not 1989: leader killed by foreign strike, succession
contested between Mojtaba and rivals, active war, mass protests. Weights (judgement,
stated): P(young-regime class) = 0.40, P(continuous class) = 0.60; within each, split
electoral/closed 50/50 given wartime hardening vs V-Dem's 2024 reclassification.

```
prior = 0.6·(0.098+0.072)/2 + 0.4·(0.150+0.299)/2 = 0.051 + 0.090 = 0.141
```

### Step 3 — inside view increments (retrieval, each with direction and size)

From the news record retrieved this session (House of Commons Library, Britannica, CNN,
Critical Threats, IMF via CNBC/Euronews, all cited in the audit README):

| Evidence | Direction | Increment (log-odds) |
|---|---|---|
| Explicit US/Israeli regime-change campaign; ~900 strikes; leadership decapitated | ↑ | +0.45 |
| But: reference class of air-campaign-only regime-change attempts without ground invasion (Iraq 1991–2003, Serbia 1999, Libya pre-ground 2011) shows survival is common short-term | ↓ | −0.20 |
| Economy: −6.1% GDP, 69% inflation, wage = 37% of subsistence — historically corrosive but autocracies survive hyperinflation for years (Venezuela, Zimbabwe) | ↑ | +0.15 |
| Protests in all 31 provinces, thousands killed — but security forces still cohesive (no defection reports) | ↑ | +0.10 |
| Succession contested but Mojtaba installed and IRGC aligned — the single best short-term survival predictor | ↓ | −0.25 |

Net: +0.25 log-odds on 0.141 → **0.175**.

### Step 4 — calibration guards (the AIA step)

- No extremizing: inputs are one correlated source, not independent forecasts —
  extremizing would manufacture false confidence (the GJP result applies to crowds only).
- Round-number avoidance: report 0.17, not 0.15 or 0.20.
- Interval from the scenario spread and increment uncertainty: **[0.09, 0.32]**.

### Final hybrid forecast

```
P(velayat-e faqih replaced by 2029-08-09) = 0.17   [0.09, 0.32]
```

For the full pre-registered composite (criteria A+B+C), the same machinery gives
E[A] ≈ 0.55 (0.28 replaced / 0.35 contested / 0.37 intact), E[B] ≈ 0.33 (inflation),
E[C] ≈ 0.55 (conflict deaths) → **E[outcome] ≈ 0.48, interval [0.35, 0.62]**.

Note what happened: the hybrid lands near the CTH kernel's registered 0.4976 — but where
the kernel's number was shown to be insensitive to its inputs and unstable under
re-specification, this one decomposes into auditable parts, each of which can be argued
with, updated, and scored. Two similar numbers; only one is a forecast.

### The updating loop (what makes it "super", and what a session cannot do alone)

The literature is unanimous that the edge is in *frequent small updates*. That requires a
standing process, not a one-shot session:

1. Re-run retrieval on a cadence (weekly/monthly); log each increment against the ledger.
2. Freeze the outside view except at V-Dem/ERT annual releases.
3. Score criterion-A at resolution (2029-08-09) with Brier against both the registered
   kernel forecast and this hybrid — that pair of scores is the actual test of everything
   in this repository.
4. If ensembling ever becomes possible (a second genuinely independent forecaster or a
   liquid market on the question), combine and extremize per Satopää — the AIA report
   found model+market beats market alone, which is the realistic ceiling here.

## Version 3.1 — the panel (executed 2026-08-10)

The missing ensemble layer, built three ways in one pass:

**Independent forecasters (Samotsvety pattern, adapted).** Three different models
(Haiku 4.5, Sonnet 5, Opus 5) each forecast the registered question alone — same
outside-view table, no access to this file's number, to the increments, or to each
other. Each ran its own news retrieval and surfaced evidence the others missed.

```
forecaster    p     90% CI        distinctive evidence
haiku-4.5    0.19  [0.11,0.29]   IRGC-Army rift, officer defections, Mojtaba invisible
sonnet-5     0.35  [0.18,0.58]   Hormuz closed since Jul 8; ~12k Jan deaths reported
opus-5       0.17  [0.08,0.33]   cohesion held under max stress; creeping-coup construct discount
fable-5      0.17  [0.09,0.32]   log-odds increments on the refclass prior (above)

median 0.18   geometric-odds mean 0.21   extremized (a=1.2) 0.17
FINAL ENSEMBLE: 0.18  [0.10, 0.35]
```

Median adopted (robust at n=4). Extremizing reported but not adopted: the panelists
share a model family and the outside-view table, so their independence is partial —
full Satopaa extremizing (a~1.7) would manufacture confidence.

**The crowd, found on GitHub (Metaculus workaround).** The
[forecastbench-datasets](https://github.com/forecastingresearch/forecastbench-datasets)
repository carries frozen Metaculus/Polymarket/Manifold/INFER values inside its question
snapshots, current through 2026-08-02 — no API access needed. Iran anchors:

```
Polymarket "Iran leadership change" (2wk horizon)   Apr 0.105 -> Jul 0.032  (hazard cooled ~3x)
Polymarket "Israel-Iran permanent peace deal"       0.0155   (war expected to continue)
Manifold  "Iranian protests end tragically"         0.875
```

Consistent with a front-loaded, decaying hazard — the shape all four panelists converged on.

**What the disagreement localises.** The 0.17-0.35 spread reduces to two judgements:
(1) credibility of IRGC-fracture reporting, which traces to opposition-aligned outlets
(NCRI, Iran International) — weighted by two panelists, discounted by one; and
(2) the construct discount — Opus's point that the likeliest dramatic outcome, a creeping
coup leaving Mojtaba a figurehead, would NOT reset the V-Dem regime spell and so resolves
NO. A resolvable-question forecast is lower than a "regime falls" intuition. This is the
audit's construct lesson, now doing live work inside a forecast.

Full panel data: `results/panel-forecasts.json`. The git commit of that file is the
ensemble's timestamp.

## Sources

- Karger, Bastani, Yueh-Han, Jacobs, Halawi, Zhang & Tetlock, [ForecastBench](https://arxiv.org/abs/2409.19839), ICLR 2025
- [AIA Forecaster: Technical Report](https://arxiv.org/abs/2511.07678), Nov 2025
- [Samotsvety track record](https://samotsvety.org/track-record/)
- [Metaculus AI Benchmark, Q2 2026 results](https://www.lesswrong.com/posts/Surnjh8A4WjgtQTkZ/q2-ai-benchmark-results-pros-maintain-clear-lead) · [Spring 2026 AIB](https://www.metaculus.com/aib/2026/spring/)
- Hegre et al., [The 2023/24 VIEWS Prediction Challenge](https://journals.sagepub.com/doi/10.1177/00223433241300862), JPR
- Halawi, Zhang, Yueh-Han & Steinhardt, *Approaching Human-Level Forecasting with Language Models*, 2024
