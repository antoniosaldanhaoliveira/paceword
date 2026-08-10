# Runbook — the standing process

Everything in this repo is a snapshot. Forecasting skill lives in the loop. This is the
loop, sized at roughly one hour per month.

## Monthly update (repeat until 2029-08-09)

1. **Retrieve.** Search current Iran news: war status, succession/Mojtaba, security-force
   cohesion (defections? unit-level fractures?), protests, rial/inflation. The two live
   cruxes from the panel: (a) credibility of IRGC-fracture reporting, (b) any sign of a
   creeping coup (which resolves NO — construct!).
2. **Increment.** For each genuinely new development, one log-odds increment with
   direction and size, appended to a dated section of this file. Superforecaster norm:
   most months the honest increment is 0.00–0.10; moves >0.3 need extraordinary evidence.
3. **Re-poll the panel** (quarterly is enough): re-run the three blind model-forecasters
   with the same prompt, updated context. Do not show them prior answers.
4. **Log the market** price (pre- and post-update) per MARKET.md.
5. **Publish the new ensemble number** in this file with the date. Never edit old entries.

## Annual events

- **V-Dem release (~March):** re-run `scripts/improve.py` on the new dataset; re-anchor
  the outside view; check whether V-Dem coded a regime spell change for Iran.
- **ForecastBench snapshots:** refresh crowd anchors from
  `forecastingresearch/forecastbench-datasets`.

## At resolution (2029-08-09)

Score every logged forecast with Brier against the resolved outcome, per the
pre-registered criteria and named sources:

| forecast | p (criterion A) | logged |
|---|---|---|
| CTH kernel (registered composite 0.4976; A-implied) | — | 2026-08-09 |
| Session hybrid | 0.17 | 2026-08-10 |
| Panel ensemble | 0.18 | 2026-08-10 |
| Market (pre-disclosure) | TBD | — |
| Every monthly update | dated series | — |

Also score criteria B (IMF WEO inflation) and C (UCDP/PRIO deaths) for the composite.
The comparison of the kernel's score against the hybrid/ensemble series is the final
empirical verdict of this entire project. Publish it either way.

## Update log

*(append below; never edit past entries)*

**2026-08-10 — baseline.** Panel ensemble 0.18 [0.10, 0.35]. Cruxes: IRGC-fracture
reporting credibility; creeping-coup construct discount. Market anchors: Polymarket
leadership-change 2wk hazard cooled 10.5%→3.2% Apr→Jul; permanent-peace 1.6%.
