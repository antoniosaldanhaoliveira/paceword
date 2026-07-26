# Existing houses, condos and townhomes — Austin

Land questions (water, septic, ETJ) mostly resolve themselves inside city
limits. What replaces them is structure, permit history and — for attached
housing — the association.

## Structure first

**Foundation.** Central Texas clay soils shrink and swell dramatically between
drought and heavy rain, and slab movement is the region's characteristic defect.
Look for stair-step cracking in brick, doors out of square, sloping floors,
separation at door frames. A general inspector will flag it; a **structural
engineer** tells you what it costs. Get one whenever the general inspector
raises it — cosmetic patching over active movement is common in flips.

**Roof.** Ages fast under hail. Ask the roof's age, whether it has been claimed
on, and whether the current insurer will write it. A roof at the end of its life
is both a capital cost and an insurance problem.

**HVAC.** A failing system in Austin's summer is not deferred maintenance; size,
age and duct condition all matter.

**Trees.** Large mature trees near a foundation drive soil moisture swings.
Austin also protects large-diameter trees by ordinance, so removal is a permit
question, not a choice.

## Permit history — where the money hides

Pull the **City of Austin permit history** and compare it to the **TCAD**
record and the listing.

- **Square footage that disagrees** between TCAD and the listing usually means
  an addition, a garage conversion or a finished-out attic that was never
  permitted. Unpermitted space can be uninsurable, can block a lender, and
  becomes your liability at resale — the city can require it be brought to code
  or removed.
- **Short-term rental history** where the plan is to keep letting it: Austin's
  STR licensing is restrictive and has been repeatedly litigated. Do not
  underwrite an STR income assumption without confirming the property can
  actually be licensed for it. Deed restrictions and HOA rules can bar it
  independently of city rules.
- Austin has been loosening single-family lot rules (smaller minimum lot sizes,
  more units permitted per lot). If the plan involves adding a unit or
  subdividing, verify the current rules for that specific parcel with the city
  rather than from a news article — this area has changed repeatedly and is
  still moving.

## Condos and townhomes — the association is the asset

Get the **resale certificate** and read past the dues:

- Monthly dues, what they cover, and their trajectory over five years.
- **Reserve balance** against the age of roofs, elevators, plumbing. An
  underfunded association with a 25-year-old roof means a special assessment is
  coming, whatever the seller says.
- **Special assessments** — current, and any voted or contemplated.
- **Litigation.** An association in active construction-defect litigation can be
  effectively unfinanceable — many lenders will not lend into it, which also
  shrinks your buyer pool at resale.
- Insurance: what the master policy covers versus what your HO-6 must.
- Rental caps, if letting is part of the plan.

## Flood, even in the city

City lots flood. Check the parcel against **both** Austin's updated Atlas 14
floodplain mapping and the FEMA maps — Austin's are stricter and a property can
be clear on FEMA and inside Austin's. Creekside lots in 78704, 78745, 78748 and
78739 deserve particular care; the Onion Creek corridor has a destructive
history and a large buyout behind it.

Also check plain drainage — where water goes in a heavy storm — which no map
shows and a walk in the rain does.

## What to record in the tracker

`built_area` in **square feet** with `built_unit: sqft`, `region` = county,
bedrooms, and the combined tax rate in `notes`. Flags worth using: `foundation`,
`roof-age`, `unpermitted-sqft`, `hoa-litigation`, `special-assessment`,
`floodplain`, `str-restricted`.
