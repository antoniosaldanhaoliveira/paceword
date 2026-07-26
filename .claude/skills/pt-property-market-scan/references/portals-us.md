# US property portals — Austin / Central Texas

Same intake model as Portugal: **you** open each URL logged in, confirm the
filters landed, save the search, and switch on the email alert. The alert is the
harvest channel. Zillow, Redfin and Realtor.com all forbid automated harvesting
and block it within a handful of requests, exactly like Idealista.

## URL reliability — read before trusting a generated link

The builder emits URLs from documented and observed patterns, but these sites
change their URL grammar without notice and could not be verified from the
build environment (all three block automated requests).

| Portal | Deep-linked filters | Confidence |
|---|---|---|
| **Redfin** | Full — property type, price, lot size, beds, sort | High. The `/filter/` grammar is comma-separated, stable and widely documented |
| **Realtor.com** | Type, price, lot size, beds, sort | Medium. Path-segment format is long-standing |
| **LandWatch** | County, price, acreage, sort | Medium |
| **Zillow** | **Region and type only** | Base path high; filters not attempted — see below |

**Treat the first run as a verification pass.** Open each link, check the
filters actually applied, fix them in the UI, then save. After that the saved
search is the source of truth and the generated URL does not matter.

## Zillow

`https://www.zillow.com/{city}-{st}/{type}/` — e.g.
`https://www.zillow.com/austin-tx/land/`. Types: `land`, `houses`, `condos`,
`townhomes`.

Zillow's actual filter state is a JSON `searchQueryState` blob in the query
string that it rewrites without notice, so the builder deliberately does not
try to construct it. Set price, acreage and sort-by-newest in the UI once, then
save. Zillow's saved-search email alerts are good and are the point of the
exercise.

Zillow is the broadest inventory and the one most sellers' agents feed first.

## Redfin

`https://www.redfin.com/zipcode/{zip}/filter/property-type=land,min-price=150k,max-price=600k,min-lot-size=5-acre,sort=newest`

Filters are comma-separated in the path. Prices take `k`/`M` shorthand.

The builder keys on **ZIP code** rather than city because Redfin's city URLs
require an opaque numeric region id (`/city/30818/TX/Austin/`) that cannot be
derived from the name. Put the ZIPs you care about in the profile's
`zone.zips`. If you would rather search by city, browse to the city on Redfin
once and paste the URL it produces — that captures the id.

Redfin's data is MLS-fed and it shows sold prices, which matters enormously in
a non-disclosure state. It is the best free source of comparables you have.

## Realtor.com

`https://www.realtor.com/realestateandhomes-search/{City}_{ST}/type-land/price-150000-600000/lot-sqft-217800/sby-6`

`sby-6` sorts newest first. Lot size is expressed in **square feet**, so the
builder converts acres (1 acre = 43,560 ft²).

Realtor.com is fed directly by the MLS and is often the fastest to show a new
listing. The least hostile of the three to a logged-in human browsing normally.

## LandWatch / Land.com

`https://www.landwatch.com/{county}-county-{state}-land-for-sale/price-150000-600000/acres-over-5/sort-recent`

Rural acreage, ranches and Hill Country tracts — much of which never reaches
Zillow. This is the OLX of the US search: better prices, worse data quality,
more private sellers. Verify everything against the county appraisal district.

State names are spelled out in the path, so the builder carries an explicit
state map and skips LandWatch for any state not in it rather than emitting a
broken slug.

## Facebook Marketplace

Same role as in Portugal: private sellers, rural land, no agency commission,
and no data discipline whatsoever. Worth a weekly manual look rather than an
alert.

## Also worth having, not automatable

- **An agent who will send you sold comps.** In a non-disclosure state this is
  the highest-value input in the whole search. Asking prices are all the
  tracker can collect on its own.
- **Unlock MLS** (the Austin-area MLS) public portal.
- **TCAD / HaysCAD** for parcel facts — not prices, but acreage, improvements,
  exemptions and every taxing entity on the parcel.

## What the tracker needs from a US listing

```json
{
  "source": "zillow", "source_ref": "29408811",
  "country": "US", "search": "austin-land",
  "property_type": "acreage", "region": "Travis",
  "price": 389000, "land_area": 5.1, "land_unit": "acre",
  "url": "https://www.zillow.com/homedetails/..."
}
```

`land_unit` matters. Rural tracts are quoted in acres and city infill lots in
square feet, and the tracker keeps those in separate medians on purpose — a
pooled median across both units is arithmetically valid and completely
meaningless.
