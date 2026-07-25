# Fields to extract from every listing

Emit one JSON object per listing and pass the array to the tracker's `ingest`
command. Leave a field `null` when the listing does not state it — never infer.
A guessed area silently corrupts every €/m² statistic downstream, and "not
stated" is itself a signal worth tracking (listings without an area are
disproportionately problematic).

```json
{
  "source": "idealista",
  "source_ref": "33012345",
  "url": "https://www.idealista.pt/imovel/33012345/",
  "title": "Terreno urbano com 1.200 m2",
  "property_type": "urban_land",
  "concelho": "São Brás de Alportel",
  "freguesia": "São Brás de Alportel",
  "lat": null,
  "lon": null,
  "price": 85000,
  "land_m2": 1200,
  "built_m2": null,
  "bedrooms": null,
  "agency": "XYZ Mediação",
  "agent_phone": null,
  "listed_date": "2026-07-18",
  "description_flags": ["claims buildable", "no construction index given"],
  "notes": ""
}
```

## property_type values

`urban_land`, `rustic_land`, `house`, `apartment`, `ruin`, `tourism_land`,
`modular`, `mobile_home`, `quinta`

Classify by what the listing *is*, not what it claims it could become. A rustic
plot advertised as "buildable" is `rustic_land` with a `description_flags` entry —
that distinction is the entire point of the due-diligence stage.

## description_flags — the highest-signal field

Record any claim that the documents will need to prove. These are what turn into
due-diligence questions later, and they are where agents most often pass on
unverified owner claims:

| Flag | What it means you must verify |
|---|---|
| `claims buildable` | Land classification in the PDM, not the tax registry |
| `no construction index given` | Ask for implantação / área bruta / n.º de pisos |
| `claims ruin` | Is the ruin registered as an urban building? Is it still standing? |
| `viable for tourism` | PDM tourism rules for that specific zone |
| `mobile home / tiny house allowed` | Almost always false outside licensed parks |
| `area mismatch` | Caderneta area ≠ listing area ≠ registry area |
| `no area stated` | Cannot compute €/m²; treat price as unassessed |
| `RAN/REN mentioned` | Reserve constraints — construction likely blocked |
| `access via private land` | Is there a registered right of way? |
| `price recently reduced` | Negotiation leverage; check how long it has been listed |
| `duplicate` | Same property listed by multiple agencies at different prices |

## Deriving €/m²

- Land plots: `price / land_m2`
- Houses and apartments: `price / built_m2`
- Quintas and ruins with both: compute both, and compare each against the right
  cohort. A quinta priced as a house on 3 hectares is being sold as land with a
  building on it, and confusing the two is how buyers overpay.
