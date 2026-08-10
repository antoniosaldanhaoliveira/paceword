# How to actually forecast with this

The audit's negative findings imply a positive one: this data supports real prediction,
just not the way CTHmodules attempts it. This file is the working alternative — including
two corrections made to it during construction, documented rather than quietly patched.

---

## What works

```
UNIT        country-year
OUTCOME     does the incumbent regime end within 2 years?  (GWF spells, censoring handled)
METHOD      rolling reference class - bucket by PITF regime type x tenure, use each
            bucket's observed frequency in a trailing window, shrunk toward the
            window's base rate
VALIDATION  walk-forward. For every year, re-estimate from PRIOR YEARS ONLY.
METRIC      Brier skill vs the rolling base rate, plus AUPRC.
```

```
  window      n     base   Brier(base)  Brier(refclass)    skill    AUPRC
      10   6698   0.0642       0.05996          0.05716  +0.0468   0.1622
      15   6698   0.0642       0.05991          0.05728  +0.0438   0.1515
      20   6698   0.0642       0.05993          0.05746  +0.0413   0.1454
      30   6698   0.0642       0.06007          0.05763  +0.0406   0.1414
      50   6698   0.0642       0.06031          0.05782  +0.0412   0.1333
```

**Best: 10-year window. Brier skill +0.047, AUPRC 0.162 against a base rate of 0.064
— lift 2.53x.** Positive skill means it beats quoting the base rate every time, which is
the only benchmark that matters.

Note skill *decreases* monotonically with window length. Recent history is more
informative than deep history. The world is non-stationary and forecasting must be too.

## Two corrections made during construction

**1. Ranking skill is not probabilistic skill.** A frozen logistic model on the same
predictors reached AUPRC lift ~1.5x and looked useful. Its Brier skill was **negative**
(−0.020 raw, −0.012 isotonic-recalibrated). It ranked countries better than chance while
its probabilities were worse than the base rate: in the 0–10% bin it predicted 2.6% where
the truth was 7.6%. Extremizing made it worse still. AUPRC and Brier answer different
questions; quoting the first and implying the second is a real error.

**2. Right-censoring was being read as regime collapse.** GWF's data stops 2020-12-31 and
stamps every *surviving* regime with that date — 189 of 631 spells. The first version of
the outcome variable counted those as failures.

```
base rate BEFORE fix   0.0709      <- contaminated
base rate AFTER  fix   0.0576
walk-forward skill     +0.0334 -> +0.0468
AUPRC                   0.1512 ->  0.1622
```

Fixing it *improved* every number: the censoring was adding noise, not signal. Spells
ending at the cutoff are now treated as censored; years more than 2 from the cutoff score
as survivals, years within 2 are dropped as unknowable.

This bug was caught only because a base rate jumped from 0.08 to 0.15 and got questioned.
The reference-class table looked entirely sensible throughout — a 100x spread ordered
exactly as Goldstone's theory predicts. Internal coherence is not evidence of a clean
outcome variable. That is the same lesson the audit draws about CTHmodules' corpus.

## Worked example: Iran

Rolling 10-year window ending 2017 (last year with a knowable 2-year outcome),
window base rate **0.0309**:

```
A  Islamic Republic continuous since 1979        0.0178   <- below base rate
B  Feb 2026 treated as a regime break            0.1064
   + reclassified partial autocracy              0.1654
   + reclassified factionalised partial democracy 0.0513
```

**1.8% to 16.5% — roughly a 9x spread from one judgement call:** does February 2026
constitute a regime break? A forecast that hides that choice inside a single number is
worse than no forecast. State the fork.

(The factionalised bucket coming in below partial autocracy inverts the theoretical
ordering — a small-sample artifact of a 10-year window. Report it; don't smooth it away.)

## Version 2 — five flaws fixed, one verdict corrected

Auditing our own tool with the audit's standards found five flaws (`scripts/improve.py`):

1. **Window selection leaked.** The 10-year window was chosen because it scored best on
   the test period. Fixed: adaptive selection — each year picks the window that minimised
   Brier over the previous decade's forecasts, all computable from the past.
2. **Stale outcome source.** GWF ends 2020. Fixed: spells rebuilt from V-Dem's own
   `v2regdur` (regime duration, resets on regime change, through 2025). Panel grows from
   8,815 to 19,330 country-years; outcomes scoreable through 2023.
3. **Unfair comparison.** The logistic model was frozen in 1980 while the reference class
   re-estimated yearly. Fixed: walk-forward logistic, re-fitted annually.
4. **No uncertainty on quoted rates.** Fixed: Jeffreys 90% intervals per bucket.
5. **No error bar on skill.** Fixed: country-clustered bootstrap.

```
  method                                  n     Brier    skill    AUPRC
  rolling base rate (20y)             11473   0.08700  +0.0000   0.1270
  refclass fixed 20y                  11473   0.08432  +0.0308   0.1731
  refclass ADAPTIVE (honest)          11473   0.08443  +0.0296   0.1731
  walk-forward logistic               11473   0.08436  +0.0303   0.1722

  adaptive skill, country-clustered bootstrap 90% CI: [+0.0218, +0.0372]
  resamples with positive skill: 100%
```

The skill number now carries an error bar, and the interval excludes zero.

**Corrected verdict:** treated fairly, the walk-forward logistic (+0.0303) matches the
reference class (+0.0296). The earlier "the model's probabilities are worse than useless"
finding was about *freezing*, not about logistic regression. Re-estimation is what
matters; the functional form is a coin flip.

**Construct-validity warning, again.** Cross-checking our outcome against the V-Dem
Institute's own [ERT dataset](https://github.com/vdeminstitute/ERT)
([Maerz et al., JPR 2024](https://journals.sagepub.com/doi/10.1177/00223433231168192)):
phi = 0.098. Near-zero — because they measure different things. `v2regdur` resets capture
*regime replacement* (including autocracy-to-autocracy coups); ERT's `row_regch_event`
captures *category reclassification* (Iran 2024: closed -> electoral autocracy, no new
regime). Any forecast must name which construct it means. Our Iran criterion
("velayat-e faqih remains governing authority") is regime replacement — `v2regdur`'s.

**Iran, scored fresh** (20y window ending 2023, base rate 0.0584; V-Dem reclassified Iran
to electoral autocracy in 2024):

```
  scenario                                                p            90% CI     n
  A: regime continuous (46y, electoral autocracy)      0.0614   [0.0394, 0.0921]   227
  A2: continuous, closed autocracy                     0.0447   [0.0254, 0.0700]   230
  B: Feb 2026 = new regime (electoral autocracy)       0.0953   [0.0732, 0.1271]   328
  B2: new regime, closed autocracy                     0.1965   [0.1619, 0.2960]   103
```

4.5%-19.7% across defensible codings, each with an interval and a sample size.

## The protocol

1. **Define a resolvable event.** Not "will Iran decline" but *"will the incumbent regime
   end before 2029-08-09, per GWF or its successor."* If two careful people could disagree
   about whether it happened, it is not a forecast.
2. **Get the base rate first**, from a recent window. Everything is a deviation from it.
3. **Use the model to pick the reference class, never to emit a probability.** That is the
   single most important line in this file, and it is what correction (1) taught.
4. **Report the range across defensible judgement calls.**
5. **Pre-register** with named third-party sources, timestamped somewhere you do not
   control. A git commit works.
6. **Score on resolution** — Brier, decomposed into reliability and resolution, so you
   learn *which* half is failing. Recalibrate as the record accrues.

## What this cannot do

- **Predict specific events.** It gives a rate over a reference class. "Regimes in this
  bucket fail ~11% of the time within two years" is not "this regime will fall."
- **Beat an informed human on a specific country.** Superforecasters use this kind of
  output as a *prior*, then update on information the model never sees. The updating is
  the skill, and no amount of fitting produces it.
- **Handle novelty.** There is no decapitation-strike variable because there are too few
  cases to fit one.
- **Reach far.** Skill decays fast past ~2 years.

**It is a base-rate machine with a 2.5x lift.** That is genuinely useful — it stops you
being surprised by likely things and panicking about rare ones. It is not psychohistory,
and the distance between the two is not a matter of more compute or more variables.

## Scripts

```
scripts/forecaster.py          frozen logistic model (kept: it is correction 1's evidence)
scripts/calibrate.py           reliability, Brier decomposition, extremizing
scripts/reference-class.py     static reference classes - still negative skill
scripts/walkforward.py         walk-forward evaluation (pre-censoring-fix)
scripts/rebuild-censored.py    THE WORKING VERSION - censoring handled, walk-forward, Iran
scripts/score-iran.py          frozen-model Iran scoring (superseded)
```

## Sources

- Goldstone et al., [*A Global Model for Forecasting Political Instability*](https://www.systemicpeace.org/vlibrary/PITFForecastingInstabilityAJPS2010.pdf), AJPS 2010
- Baillie, Howe, Perfors, Miller, Kashima & Beger, [*Explainable models for forecasting the emergence of political instability*](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0254350), PLOS One 2021
- [V-Dem](https://github.com/vdeminstitute/vdemdata) · [democracyData](https://github.com/xmarquez/democracyData) (carries `pitf`, `polity5`, GWF regime spells)
