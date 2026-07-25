# Tracker data schema

Workspace: `$PROPERTY_WORKSPACE`, default `~/property-portugal/`

```
property-portugal/
├── profile.yaml         # buyer strategy (owned by pt-property-market-scan)
├── listings.csv         # one row per unique property
├── price_history.json   # {listing_id: [{date, price}, ...]}
├── notes/               # per-property markdown: visits, calls, documents
├── digests/             # dated digest markdown, so the user can look back
└── dd/                  # due-diligence reports (pt-property-due-diligence)
```

## listings.csv columns

| Column | Type | Notes |
|---|---|---|
| `id` | string | Stable internal key: `{source}-{source_ref}` |
| `source` | string | idealista, imovirtual, casa_sapo, olx, facebook, agent, offmarket |
| `source_ref` | string | Portal reference number — the best dedupe key |
| `url` | string | Canonical listing URL |
| `title` | string | As listed |
| `property_type` | enum | urban_land, rustic_land, house, apartment, ruin, tourism_land, modular, mobile_home, quinta |
| `concelho` | string | Municipality — the unit statistics are grouped by |
| `freguesia` | string | Parish, when stated |
| `lat`, `lon` | float | When available; enables real duplicate detection |
| `price` | int | Current asking price, EUR |
| `first_price` | int | Price when first seen — the anchor for total movement |
| `land_m2` | int | Plot area |
| `built_m2` | int | Construction area |
| `eur_per_land_m2` | float | Derived; null when area unknown |
| `eur_per_built_m2` | float | Derived |
| `bedrooms` | int | |
| `agency` | string | Also the seed of the local agent network the guide describes |
| `agent_phone` | string | |
| `first_seen` | date | When the tracker first recorded it |
| `last_seen` | date | Last run that confirmed it is still listed |
| `listed_date` | date | Portal's own publication date, when shown |
| `days_on_market` | int | From `listed_date` if known, else `first_seen` |
| `status` | enum | See below |
| `rating` | int | 0–5, the user's own interest level |
| `dd_status` | enum | none, requested, in_progress, cleared, rejected |
| `flags` | string | Semicolon-joined description_flags |
| `notes` | string | Short free text; long notes go in `notes/{id}.md` |

## status values

| Status | Meaning |
|---|---|
| `active` | Seen in the most recent sweep |
| `price_drop` | Price fell since the previous run (resets to active next run) |
| `price_rise` | Price rose — rare, and usually means a relist |
| `disappeared` | Not seen in the last sweep; cause unknown |
| `sold` | Confirmed sold |
| `relisted` | Reappeared under a new reference — link via `notes` |
| `rejected` | Ruled out by the user or by due diligence |
| `favourite` | User is actively pursuing it |

`disappeared` is deliberately distinct from `sold`. Recording every vanished
listing as sold inflates your sense of the clearing price, which is exactly the
bias the tracking exercise exists to remove.

## price_history.json

```json
{
  "idealista-33012345": [
    {"date": "2026-05-02", "price": 95000},
    {"date": "2026-06-18", "price": 89000},
    {"date": "2026-07-21", "price": 85000}
  ]
}
```

Append-only, one entry per observed change. A staircase of small cuts is a seller
being walked down by their agent and usually has further to go; a single large
cut is often a repricing to market with less room left.
