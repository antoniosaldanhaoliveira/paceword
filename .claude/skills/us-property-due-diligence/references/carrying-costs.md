# What it costs to hold — Central Texas

Texas has no state income tax and funds itself through property tax. For a buyer
coming from Portugal the shape is inverted: **acquisition is cheap, holding is
expensive.**

| | Portugal | Texas |
|---|---|---|
| Purchase taxes | IMT up to ~7.5% + 0.8% stamp | **None** — no transfer tax |
| Annual property tax | IMI, roughly 0.3–0.45% | **~2.0–2.2%** combined in Austin/Travis |
| Who sets the taxable value | Municipality, slow to move | Appraisal district, **annually, toward market** |

A €200,000 Portuguese plot costs perhaps €700/year to hold. A $500,000 Austin
property costs around $10,000–11,000/year. That difference should drive the
budget, not surprise it.

## Building the real number

Work it parcel by parcel — rates vary sharply across a few miles.

1. **Pull the parcel on TCAD** (or HaysCAD). It lists every taxing entity on
   that specific parcel.
2. **Sum the rates.** Inside Austin city limits in Travis County the combined
   2025–26 rate is roughly **$2.05 per $100** of assessed value (~2.046%), of
   which the City of Austin portion is about $0.574. School district is usually
   the largest single component.
3. **Add MUD / PID / ESD if present.** Travis County has 54 MUDs and 16
   emergency services districts among 127 taxing entities. A MUD commonly adds
   **$0.25–$1.00+ per $100** — on a $500k home a $0.75 MUD is about $3,750 a
   year. MUD debt is amortised over decades; the rate usually falls over time,
   but slowly, and the seller's current rate is what you inherit.
4. **Apply exemptions only if they apply to you.** The school-district homestead
   exemption is **$140,000** as of the 2025 tax year (up from $100,000), with a
   further $60,000 for owners 65+ or with a qualifying disability. It requires
   the property to be your **primary residence** — so for a second home, a
   rental, or a land-banking purchase, model the tax with **no exemption and no
   10% appraisal cap**.
5. **Vacant land gets no homestead exemption at all**, and is assessed on market
   value unless it carries an agricultural valuation.

Rates are re-adopted every year. Re-verify at contract rather than trusting a
figure from a listing or from this file.

## Agricultural valuation and rollback

An ag-valued tract is taxed on productivity value rather than market value,
often cutting the bill by an order of magnitude. Two consequences:

- A listing's "taxes: $400/year" on 10 acres almost certainly reflects an ag
  valuation, **not** what you will pay if you build a house on it.
- Changing the use triggers a **rollback**: back taxes for prior years plus
  interest. Model this as a real line item before buying an ag tract to develop,
  and confirm the current rollback exposure with the appraisal district.

If you intend to keep it in agricultural use, confirm what qualifies — the
requirements are specific (stocking rates, history of use) and losing the
valuation is expensive.

## Insurance

- **Wind and hail** drive Central Texas premiums; roof age and material matter
  a great deal to what you will be quoted.
- **Flood is separate** and is not in a standard homeowner policy. If any part
  of the parcel touches a flood zone — Austin's Atlas 14 mapping or FEMA's — get
  a real quote during the option period, not an estimate.
- **Foundation** claims are common on Central Texas clay soils; prior claims on
  a CLUE report can make a property expensive or difficult to insure.
- On vacant land, carry liability coverage.

## Rules of thumb for the tracker

When comparing two Austin properties, compare **price + 10 years of carrying
cost**, not price. A $450k tract in a MUD outside the city can cost more over a
decade than a $520k parcel inside it. Record the combined rate and any MUD in
the listing's `notes` field so the comparison survives into the digest.
