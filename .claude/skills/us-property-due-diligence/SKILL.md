---
name: us-property-due-diligence
description: Evaluate a specific property in Austin / Central Texas before touring, offering or closing — check its type-specific criteria (vacant land, Hill Country acreage, existing house, condo), assemble the document and disclosure checklist (title commitment, survey/T-47, seller's disclosure, tax certificate, MUD notice, restrictive covenants), size the real carrying cost, and surface the things that kill Texas deals. Use whenever the user is assessing, comparing or asking whether to buy a particular property in Texas, asks what to request or inspect, mentions ETJ, MUD, floodplain, Atlas 14, septic or OSSF, well or groundwater, impervious cover, deed restrictions, HOA, title commitment, survey, option period, TREC contract, homestead exemption or a property tax protest, asks whether a lot is buildable, or is about to make an offer or sign a contract.
---

# Texas / Austin property due diligence

The Portuguese path asks *is this legally what it claims to be*. The Texas path
mostly assumes it is — recording and title insurance are strong — and asks two
different questions instead:

1. **What is it actually worth?** Texas is a non-disclosure state. Sold prices
   are not public record, so the number you would anchor on in Portugal does not
   exist here.
2. **What will it cost to hold?** Property tax around 2% of assessed value a
   year is the dominant number in Texas, and it is assessed on a value the
   county sets, not the price you paid.

Get those two wrong and nothing else matters.

## The non-disclosure problem — read this first

Texas does not record sale prices. Neither the county clerk nor the appraisal
district publishes what a property actually sold for. Only licensed agents can
pull sold comparables from the MLS.

What this means for the tracker:

- **Asking prices are what you can collect yourself.** The tracker's medians
  are therefore asking-price medians, and asking prices in a soft market run
  above what closes. Treat the median as a ceiling, not as market value.
- **Days on market is unusually informative here**, precisely because price
  history is not. A tract 200 days in with two cuts tells you more about the
  real number than any list price does.
- **You need one MLS-side source.** Either an agent who will send you sold
  comps, or a paid appraisal/BPO. Until you have that, every "12% below median"
  reading in your digest is relative to asking prices only, and the skill will
  say so rather than implying it is market value.

Record that source in the profile once you have it. It is the single highest-value
thing you can add to a Texas search.

## Carrying cost is a first-class filter, not a footnote

At roughly 2.0–2.2% combined inside Austin city limits in Travis County, a
$500,000 property carries about $10,000–11,000 a year in tax before insurance.
That is not a closing detail — it changes which properties are affordable, and
it is why a cheap-looking outlying tract with a MUD can cost more to hold than a
dearer one inside the city.

Always compute, before touring:

- **Combined tax rate** for the exact parcel — city + county + school district +
  ACC + healthcare district, plus **MUD** and any **PID/emergency services**
  district. Travis County alone has over 120 taxing entities.
- **MUD rate if any.** Newer subdivisions outside city limits commonly carry a
  MUD at $0.25–$1.00+ per $100 of value, on top of everything else. A $0.75 MUD
  on a $500k home is ~$3,750/year, forever, and it is easy to miss because the
  listing rarely mentions it. Sellers must give a statutory MUD notice before
  contract — read it.
- **Homestead exemption** only applies if this becomes the primary residence.
  For a non-resident buyer or a land-banking purchase it does not apply at all,
  and the 10% annual appraisal cap that comes with it does not either. Budget
  for the assessed value rising toward market each year.
- Whether the parcel currently sits under an **agricultural ("ag") valuation**.
  It slashes the tax bill — and triggers a multi-year **rollback tax** with
  interest if you change the use. Buying an ag-valued tract to build on can
  hand you a five-figure bill at the moment you break ground.

Insurance is the other half: Central Texas carries hail and wind exposure, and
anything in or near a floodplain needs a real flood quote, not an estimate.

See `references/carrying-costs.md`.

## Routing

| Property | Reference |
|---|---|
| Vacant lot, acreage, Hill Country tract, ranch | `references/land-acreage.md` |
| Existing house | `references/house.md` |
| Condo or townhome | `references/house.md` (plus the HOA section) |
| Anything, document side | `references/documents.md` |
| Anything, cost side | `references/carrying-costs.md` |

## The gate

Do not tour until you have: the combined tax rate including any MUD, the flood
status, and — for land — how it gets water and sewer. Do not offer until the
title commitment, survey and restrictions are in hand. Do not waive the option
period.

## The option period is your real due diligence window

Texas contracts (TREC promulgated forms) normally include a paid **option
period** — a short window, commonly around 7–10 days, in which the buyer can
terminate for any reason and get the earnest money back. This is where
inspections, surveys and the checks in this skill actually happen.

Two rules:

- **Never waive it to win a bidding war** unless everything in `documents.md`
  is already resolved. It is the only unconditional exit in the contract.
- **The clock is short and strict.** Order the inspection and the survey review
  the day the option period starts, not midway through it.

## Red flags that kill Texas deals

- **In a floodplain — including the updated Atlas 14 maps.** Austin's own
  floodplain maps are being redrawn upward from the NOAA Atlas 14 rainfall
  study and are stricter than the FEMA maps, so a property can be outside the
  FEMA flood zone and inside Austin's. Check both. The Onion Creek corridor
  (78748 / 78739) has a destructive history and an 800-property buyout behind
  it — treat anything there as flood-suspect until proven otherwise.
- **No confirmed water.** A rural tract with no well and no utility commitment
  may be unbuildable in practice. See the acreage reference — Travis County
  requires 5-acre minimum lots for individual wells drawing on the Trinity
  aquifer, which quietly disqualifies smaller tracts.
- **No septic feasibility.** Shallow limestone and slope defeat conventional
  systems across the Hill Country; an aerobic system is a real capital cost.
- **ETJ status unresolved.** See `land-acreage.md` — this is genuinely unsettled
  in Austin right now and is being litigated.
- **Ag rollback exposure** on a tract you intend to develop.
- **Deed restrictions or HOA rules** that forbid what you are buying it for —
  in Texas these bind more tightly and more durably than zoning does.
- **Unpermitted additions** on a house. The tax record's square footage not
  matching the listing's is the tell.
- **Seller is an out-of-state LLC that bought recently.** Common flip pattern;
  expect cosmetic work over sound work.
