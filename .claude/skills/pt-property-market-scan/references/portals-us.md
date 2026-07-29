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

## Business-broker channels — where operating lodging actually sells

A tired hotel is usually sold as a **going concern by a business broker**, not
as real estate by a CRE broker. It never reaches LoopNet. These are the channels
that carry it — but they are tiered, and using the wrong tier wastes weeks.

### Tier by deal size

| Deal size | Where it lives |
|---|---|
| Under ~$500k | BizBuySell + BizQuest |
| ~$500k – $3M | BizBuySell primary, plus regional brokers |
| **$3M+ / middle market** | **Specialist hotel brokers and M&A advisors. The Main Street marketplaces will not have it.** |

**BizBuySell's median closed sale is around $350,000.** That is Main Street
territory. It will surface a small independent lodge and will not surface a
$20M resort. Know which you are hunting before you spend time there.

### Marketplaces (URL-generatable)

| Site | Note |
|---|---|
| **BizBuySell** | Largest — ~45,000 listings, ~9,600 closed transactions in 2025. CoStar-owned |
| **BizQuest** | Same owner, ~35,000 listings, but **only 65–75% overlap with BizBuySell**. That quarter is why you run both |
| **BusinessBroker.net** | Independent of the CoStar pair; also carries a state broker directory |
| **BusinessesForSale.com** | Simple marketplace, franchise-leaning |
| **DealStream** | Skews larger than the Main Street sites |
| **Axial** | Curated middle-market M&A. Closer to your tier than any of the above |

All five marketplaces are generated by `build_search_urls.py`, gated to
searches whose `property_types` include `hotel` or `resort`.

### Specialist hotel brokers — relationships, not URLs

At $3M+ this is the real channel, and none of it is a search you can save.

| Firm | Why |
|---|---|
| **HREC — Hospitality Real Estate Counselors** | 600+ hotel/casino transactions, $9B+ in value. Among the top hotel brokers nationally |
| **Mumford Company** | 1,200+ hotel transactions since 1978; mid-market and economy focus, **with a Dallas office** |
| **Hotel Brokers International (HBI)** | National hotel brokerage network |
| **Marcus & Millichap** — hospitality division | Austin office, local hotel transaction history |
| **JLL Hotels & Hospitality**, **CBRE Hotels** | Institutional end of the market |

Mumford is the most directly relevant of these: mid-market and economy hotels
are exactly the tired-asset category, and they have Texas coverage.

### Broker directories — for finding people, not listings

- **IBBA** (International Business Brokers Association) — certified brokers by state
- **TABB** (Texas Association of Business Brokers) — oldest such association in
  the US, with an **Austin chapter**
- **Sunbelt Business Brokers Austin** — handles businesses up to ~$50M revenue
- **Transworld Business Advisors** — brokerage plus commercial real estate

### The practical sequence

1. Run the five marketplace searches with alerts on. Cheap, and it catches the
   small independent lodges.
2. Call **Mumford** and **HREC** directly. Ask for under-performing independent
   lodging in western Travis County. That is where the real inventory is.
3. Use **TABB's Austin chapter** and **IBBA** to find local brokers who see
   Hill Country hospitality before it is marketed anywhere.


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
