# How to actually forecast with this

The audit's negative findings imply a positive one: the data supports real prediction,
just not the way CTHmodules attempts it. This file is the working alternative.

`scripts/forecaster.py` rebuilds the Baillie et al. (2021) minimal design from data
reachable here. `scripts/score-iran.py` applies it.

---

## The model

```
UNIT        country-year
OUTCOME     does the incumbent regime end within 2 years?   (GWF end-dates)
PREDICTORS  1. PITF regime type (5 categories)
            2. fertility rate  - proxy for infant mortality, same construct
            3. years of stability
VALIDATION  temporal split. train <= Y, test > Y. No shuffling.
METRIC      AUPRC against base rate. Accuracy is meaningless for rare events.
```

## What it achieves

```
                              train   test     base    AUPRC   AUROC    lift
3 predictors, train<=1970      3075   5866   0.0796   0.1375   0.624    1.73x
3 predictors, train<=1980      4171   4770   0.0797   0.1260   0.622    1.58x
3 predictors, train<=1990      5302   3639   0.0800   0.1294   0.608    1.62x
3 predictors, train<=2000      6569   2372   0.0927   0.1370   0.581    1.48x
+ log GDPpc,  train<=1990      5302   3639   0.0800   0.1293   0.608    1.62x
```

**Modest, real, and stable.** Roughly 1.5–1.7x better than the base rate, holding across
four independent temporal splits. Adding GDP per capita adds nothing. AUROC of 0.58–0.62
is weak — this is not a crystal ball, and anything claiming to be one is lying.

Standardised coefficients (train ≤1990):

```
years_stable                              -1.1927   <- dominates
rg_4-Full democracy                       -0.7922
rg_2-Partial democracy with factionalism  +0.3603   <- riskiest category
rg_1-Partial autocracy                    +0.3059
rg_0-Full autocracy                       +0.2450
e_miferrat                                +0.1638
rg_3-Partial democracy                    +0.0101
```

This independently reproduces Goldstone's ordering — factionalised partial democracy
riskiest, full democracy safest — and shows hazard decay dominating everything else.

## Worked example: Iran

```
Iran fertility (V-Dem 2025): 1.670
PITF regime type (through 2018): full autocracy
Islamic Republic per GWF: party-based, began 1979-01-16
base rate: 0.0709

SCENARIO A - Islamic Republic continuous since 1979 (47 years stable)
  p(regime ends within 2y) = 0.0558        <- BELOW base rate

SCENARIO B - Feb 2026 treated as a regime break
  years_stable reset to 0                  = 0.0846
  + reclassified partial autocracy         = 0.1251
  + reclassified factionalised part. dem.  = 0.1417

range 5.6% - 14.2%, a 2.5x spread
```

**The spread is the point.** One judgement call — does February 2026 constitute a regime
break? — moves the answer 2.5x. A forecast that hides that choice behind a single number
is worse than useless. State the fork; let the reader weigh it.

Hazard decay, full autocracy, holding everything else fixed:

```
 0 years -> 0.0846      10 years -> 0.0775      30 years -> 0.0649
 2 years -> 0.0831      20 years -> 0.0709      47 years -> 0.0558
```

Gentle. Longevity protects, but not dramatically.

---

## The protocol

1. **Define a resolvable event.** Not "will Iran decline" — *"will the incumbent regime
   end before 2029-08-09, per GWF or its successor."* If two people could disagree about
   whether it happened, it is not a forecast.
2. **Get the base rate first.** Everything is a deviation from it. A model output with no
   base rate attached carries no information.
3. **Use the model for lift, not for truth.** 1.6x over base rate is what this buys.
4. **Report the range across defensible judgement calls**, as in Scenario A vs B.
5. **Pre-register**: prediction, resolution date, named third-party source, before the
   outcome. Timestamp it somewhere you do not control — a git commit works.
6. **Score it** when it resolves: Brier or log score against the base rate. A track record
   is the only evidence that any of this works.

## What this cannot do

- **Predict specific events.** It gives a rate over a reference class. "This regime is in
  a category that fails ~8% of the time within 2 years" is not "this regime will fall."
- **Beat a well-informed human on a specific country.** Superforecasters use these as
  priors, then adjust on information the model never sees.
- **Handle novelty.** No decapitation-strike variable exists because there are too few
  cases to fit one.
- **Reach beyond ~2 years usefully.** Skill decays fast.

The honest summary: this is a **base-rate machine with modest lift**. That is genuinely
useful — it stops you from being surprised by things that were always likely, and from
panicking about things that are rare. It is not psychohistory, and the gap between the
two is not a matter of more compute or more variables.

## Sources

- Goldstone et al., [*A Global Model for Forecasting Political Instability*](https://www.systemicpeace.org/vlibrary/PITFForecastingInstabilityAJPS2010.pdf), AJPS 2010
- Baillie, Howe, Perfors, Miller, Kashima & Beger, [*Explainable models for forecasting the emergence of political instability*](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0254350), PLOS One 2021
- [V-Dem](https://github.com/vdeminstitute/vdemdata) · [democracyData](https://github.com/xmarquez/democracyData) (carries `pitf`, `polity5`, GWF regimes)
