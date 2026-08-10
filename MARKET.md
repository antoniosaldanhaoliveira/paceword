# Private Manifold market — ready to create

Manifold is unreachable from the audit environment, and a market must be created from
your account regardless. Everything below is paste-ready. Creating it takes ~5 minutes
at manifold.markets/create.

## Market settings

**Question (title):**
> Will velayat-e faqih be replaced as the governing authority of Iran before Aug 9, 2029?

**Type:** Yes/No · **Visibility:** Unlisted (Manifold's "private" mode) · **Close date:** 2029-08-08

**Description (paste verbatim):**

> Resolves YES if the velayat-e faqih system (clerical Supreme-Leader rule) is replaced as
> Iran's governing authority on any date up to and including 2029-08-09 — by revolution,
> coup installing a different ruling coalition, collapse, or foreign-imposed change.
>
> Resolves NO otherwise. Explicitly NOT sufficient for YES: leadership succession inside
> the system (a new Supreme Leader), reforms, a "creeping coup" that leaves the same
> ruling coalition in place behind a figurehead, or a mere reclassification of regime
> type by outside observers.
>
> Resolution authority: V-Dem regime spell change (v2regdur reset) in the first V-Dem
> release covering the period; if V-Dem is discontinued, the GWF successor dataset; if
> both are unavailable, creator judgement applying the criteria above.
>
> Context and prior work: [link the repo here AFTER initial trading — see protocol below.]

## Anti-anchoring protocol (this is the part that makes it worth doing)

The market's value is *independent* estimates. Our numbers (0.17/0.18/0.35) are published
in the repo and this conversation, so:

1. Invite 3–5 traders. Ask them to make their first trade **before** reading the repo,
   the report, or any of our numbers. Send the question only.
2. After everyone's first trade, share the repo link in the market description. Later
   trades are then informed-but-anchored — normal market behaviour, fine.
3. Record the **pre-disclosure price** separately (screenshot or note the probability
   before step 2). That price is the genuinely independent crowd estimate.

## Integration protocol (what to do with the price)

Per the AIA Forecaster finding — the model does not replace the market; the ensemble of
model + market beats the market alone:

1. Log the pre-disclosure price and date in `results/panel-forecasts.json` under a new
   `market` key.
2. Combined forecast: geometric-odds mean of {panel ensemble 0.18, market price}, weights
   2:1 in the market's favour if it has ≥5 active traders, 1:1 otherwise (thin private
   markets are noisy).
3. With the market as a genuinely independent input, mild extremizing of the combined
   log-odds (a = 1.3–1.5) becomes defensible for the first time.
4. Re-log the price at each monthly update (see RUNBOOK.md).

## Known limits of a private Manifold market

- Play-money and thin: 3–5 friends is a sentiment poll with a price, not a liquid market.
  Its value is independence, not efficiency.
- Manifold resolves by creator judgement — the named-source criterion above is what keeps
  that honest. Do not resolve early on news headlines; wait for the V-Dem release.
- Mana incentives are weak for 3-year questions. Expect participation to decay; the
  pre-disclosure price is the main harvest.
