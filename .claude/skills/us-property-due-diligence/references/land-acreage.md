# Vacant land and acreage — Austin and the Hill Country

The Portuguese question "is this legally buildable" has a Texas equivalent, but
it is answered by utilities and private restrictions far more than by zoning.
A tract can be entirely unrestricted and still be unbuildable because no water
can reach it.

Work the four gates in order. Any one of them failing ends the deal.

## Gate 1 — Water

This is the binding constraint west and south-west of Austin, and the one
buyers most often discover last.

**If it is on a public/utility supply:** get written confirmation of service
availability from the retail water provider for *this parcel* — a "will-serve"
or service availability letter. Proximity to a line means nothing; capacity and
commitment do. Ask what the tap/impact fee is, because it can run into five
figures.

**If it is on a well, or would need one:**

- Travis County regulates groundwater availability, and for the **Trinity
  aquifer** the lot-size rules are hard: **individual wells require lots of at
  least 5 acres**; a centralised groundwater system allows 3-acre lots; or the
  lot count cannot exceed acreage divided by four. A 3-acre tract you planned to
  put a private well on may simply not qualify.
- Subdivisions relying on wells must prove adequate supply through aquifer
  testing, with a **Groundwater Availability Certification** prepared by a
  licensed P.E. or P.G.
- For an existing well, get the driller's log, depth, static level and a current
  flow test plus a potability test. Hill Country wells vary enormously well to
  well, and a neighbour's good well predicts nothing.
- Check which groundwater conservation district governs the parcel and what its
  permitting and spacing rules are.

**Edwards Aquifer recharge zone:** development over the recharge zone carries
additional water-quality rules and impervious-cover limits, and a required
water pollution abatement plan. It slows and constrains everything.

## Gate 2 — Wastewater

Outside a sewer service area you are on an **OSSF** (on-site sewage facility —
septic), permitted through Travis County under its OSSF rules.

- A **site evaluation by a licensed professional** with soil borings comes
  before anything. Shallow limestone, thin soils and slope are the norm in the
  Hill Country and defeat conventional drainfields, pushing you to an aerobic
  system with ongoing maintenance contracts.
- **Budget 3–8 weeks** for evaluation, design and permitting in Travis, Hays,
  Comal or Kendall counties — longer over the recharge zones.
- Confirm required **separation distances** between well, septic and any
  surface water. On small or oddly shaped tracts these setbacks alone can leave
  no legal location for the system.
- For an existing system: permit, as-built, maintenance records, and last
  pump-out. An unpermitted system is the buyer's problem after closing.

## Gate 3 — Jurisdiction and what you may build

**Inside Austin city limits:** city zoning and the land development code apply —
zoning category, impervious cover limit, setbacks, compatibility rules, and the
heritage tree ordinance (Austin protects large-diameter trees; removing or
building near one is a permit matter and can reshape a site plan).

**In Austin's ETJ (extraterritorial jurisdiction):** the city has no zoning
power but does control subdivision and some development standards. **This is
currently unsettled.** SB 2038 (effective September 2023) created a petition
process for owners to leave a city's ETJ; Austin notified around 170 Travis
County properties that they were released, then reversed those releases in
March 2026 citing a statutory exception, and is being sued over it as of
June 2026.

Practical consequence: **do not accept "it's out of the ETJ" from a listing or
an agent.** Get the parcel's current status in writing from the City of Austin,
and if the plan depends on being outside the ETJ, treat that as an open legal
question rather than a settled fact. Re-check it at contract, because it may
move again.

**Outside both:** county authority only. Travis County controls subdivision,
floodplain, OSSF and road access — not land use. Which means the binding limits
on what you can build are usually private, not public: see Gate 4.

## Gate 4 — Private restrictions, access and easements

- **Restrictive covenants / deed restrictions.** In Texas these do the work
  zoning does elsewhere and they run with the land. They routinely bar
  manufactured homes, short-term rentals, subdividing, livestock, outbuildings,
  business use, or set minimum dwelling sizes. Read the recorded document — not
  the agent's summary.
- **HOA or POA.** Get the dues, the transfer fee, the reserve position and any
  active special assessment or litigation.
- **Legal access.** Confirm the tract touches a public road, or has a recorded,
  permanent, appurtenant easement to one. A verbal or historical "everyone uses
  that track" is not access. Landlocked acreage is the classic cheap tract.
  Also confirm a **driveway/culvert permit** is obtainable for the intended
  access point.
- **Easements and encumbrances on the survey:** utility, pipeline, transmission
  line, drainage. Pipelines and high-voltage corridors sterilise building
  envelopes and are common east and south of Austin.
- **Mineral rights.** Texas severs mineral estate from surface estate routinely,
  and **the mineral estate is dominant** — the holder can use the surface to
  access minerals. Ask what mineral interest conveys. Often none does. A surface
  waiver is worth negotiating.
- **Floodplain and drainage.** Check FEMA *and* Austin's own updated Atlas 14
  floodplain mapping, which is stricter. Get the elevation certificate if any
  part is near a boundary. Flood status drives insurance, lending and whether
  you can build at all.

## What to record in the tracker

`land_area` in **acres** with `land_unit: acre` (city infill lots quoted in
square feet get `land_unit: sqft` — the tracker keeps those medians separate on
purpose). Put the county in `region`. Use `flags` for the disqualifiers:
`no-well`, `floodplain`, `etj-unresolved`, `ag-rollback`, `no-legal-access`,
`pipeline-easement`, `mud`.
