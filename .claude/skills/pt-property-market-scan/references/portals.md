# Portuguese property portals — URL structure and quirks

Ordered by yield for a serious buyer.

## Idealista.pt

The broadest inventory in Portugal and the one the guide recommends as primary.

**URL shape:** `https://www.idealista.pt/{operation}/{location-slug}/com-{filters}/`

- operation: `comprar-casas`, `comprar-terrenos`, `comprar-quintas-e-casas-rusticas`
- location slug: `{concelho}/{freguesia}` lowercased, hyphenated, accents stripped
  — e.g. `sao-bras-de-alportel`, `caldas-da-rainha/a-dos-francos`
- filters joined by commas after `com-`:
  - `preco-max_150000`, `preco-min_50000`
  - `tamanho-terreno-min_1000` (land m²), `metros-quadrados-min_100` (built m²)
  - `t2`, `t3` (bedrooms), `ordem-publicado-desc` (newest first — always add this)

**Radius search:** Idealista does not expose a clean radius parameter in the path.
Either list the neighbouring concelhos explicitly in the profile, or use the map
view and let the user save it. Listing the concelhos is more reliable.

**Quirks:**
- Aggressive bot protection. Fetch individual listing pages the user has already
  surfaced; do not crawl result pages in bulk. Automated harvesting violates the
  terms of use and gets the IP blocked within a handful of requests.
- Saved search + daily email alert (account required) is the intended intake and
  is what the guide tells buyers to set up.
- Reference numbers are stable, which makes them the best dedupe key.
- The same property routinely appears from several agencies at different prices.
  Dedupe on coordinates + area, not on title.

## Imovirtual.com

**URL shape:** `https://www.imovirtual.com/comprar/{type}/{location}/`
with query params: `?search%5Bfilter_float_price%3Ato%5D=150000`,
`search%5Bfilter_float_m%3Afrom%5D=1000`, `nrAdsPerPage=72`

- type: `terreno`, `moradia`, `apartamento`, `quinta`
- Supports a real radius parameter: `search%5Bdist%5D=15` (km) — useful for the
  guide's 15–20 km rule when combined with an anchor location.

## Casa Sapo

**URL shape:** `https://casa.sapo.pt/comprar-{type}/{district}/{municipality}/`
Query params: `?pn=1&or=10` (order 10 = most recent), `pmax=`, `pmin=`

Strong on agency listings that skip Idealista, especially in the north.

## OLX.pt

Private sellers, no agency commission, and the place rural land appears first.

**URL shape:** `https://www.olx.pt/imoveis/terrenos-quintas/{region}/`
Query: `?search%5Bfilter_float_price%3Ato%5D=100000&search%5Border%5D=created_at%3Adesc`

**Quirks:** listing quality is poor — often no area, no coordinates, no documents.
Treat every OLX figure as unverified until the caderneta says otherwise. This is
also where the best prices are, because the seller is not paying 5% to an agency.

## Facebook Marketplace

No stable URL API. Search `terreno {concelho}`, `ruína {concelho}`, `quinta
{concelho}` in Marketplace with a radius filter, plus the local buy/sell groups
("Terrenos {distrito}", "Comprar e vender {concelho}").

Highest noise, but the guide singles it out for small and rural deals that never
reach a portal. Worth one pass per week, not per day.

## Municipal and judicial sources (bonus, not in the guide)

Worth adding once the user is fluent in the zone:

- **e-leiloes.pt / Portal dos Leilões** — judicial auctions, deep discounts, but
  the buyer takes on any occupancy and charges. Only for buyers with legal support.
- **Câmara Municipal** notices — municipal land sales and subdivision approvals.
- **BUPi** (bupi.gov.pt) — rural cadastre; useful later for boundary verification.
