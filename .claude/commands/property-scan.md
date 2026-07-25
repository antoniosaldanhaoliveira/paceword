---
description: Run today's Portuguese property scan — new listings, price drops, digest
---

Run the daily property research loop for the buyer profile in
`$PROPERTY_WORKSPACE` (default `~/property-portugal/`).

Use the **pt-property-market-scan** skill for the harvest and the
**pt-property-tracker** skill for the record and the digest.

If `profile.yaml` does not exist, set up the buyer strategy first — property type
(one or two), anchor town plus a 15–20 km radius, purpose, and budget — then
build the portal search URLs so the user can save them and switch on the daily
email alerts.

Arguments (optional): $ARGUMENTS — e.g. a listing URL to add, `stats` for the zone
statistics only, or `weekly` for a broader sweep including Facebook Marketplace
and the private-seller portals.
