---
description: Run today's Portuguese property scan — new listings, price drops, digest
---

Run the daily property research loop for the profile in `$PROPERTY_WORKSPACE`
(default `~/property-portugal/`).

Use the **pt-property-market-scan** skill for the harvest and the
**pt-property-tracker** skill for the record and the digest.

The profile may hold several named searches. Run every active one unless
$ARGUMENTS names a specific search. Keep them separate end to end — ingest and
sweep with `--search <name>`, and produce one digest per search. A sweep without
`--search` marks every other search's listings as disappeared.

If `profile.yaml` has no searches defined, set up the first one instead of
scanning: property type (one or two), anchor town plus a 15–20 km radius,
purpose, and budget. Then build the portal search URLs so the user can save them
and switch on the daily email alerts, named after the search.

Arguments (optional): $ARGUMENTS
- a search name — scan only that one
- `searches` — overview of every search: size, medians, what needs attention
- `stats [search]` — zone statistics only
- a listing URL — add it to the tracker
- `weekly` — broader sweep including Facebook Marketplace and private sellers
