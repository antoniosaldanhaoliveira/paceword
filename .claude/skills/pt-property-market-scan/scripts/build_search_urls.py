#!/usr/bin/env python3
"""Build saved-search URLs for the Portuguese property portals from a buyer profile.

The URLs are meant to be opened by the user (logged in) so they can save the
search and switch on the daily email alert — that is the intake channel the
guide recommends and the one the portals actually permit.

A profile may hold several named searches, each with its own zone, types and
budget. URLs are always built per search, because a search is the unit that has
a coherent €/m² baseline.

Usage:
    python build_search_urls.py --profile property-workspace/profile.yaml
    python build_search_urls.py --profile ... --search algarve-plots
    python build_search_urls.py --profile ... --portal idealista --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

DEFAULT_COUNTRY = "PT"

# Portal-specific vocabulary for each profile property_type.
IDEALISTA_OP = {
    "urban_land": "comprar-terrenos",
    "rustic_land": "comprar-terrenos",
    "tourism_land": "comprar-terrenos",
    "ruin": "comprar-casas",
    "house": "comprar-casas",
    "apartment": "comprar-casas",
    "modular": "comprar-terrenos",
    "mobile_home": "comprar-terrenos",
    "quinta": "comprar-quintas-e-casas-rusticas",
}

IMOVIRTUAL_TYPE = {
    "urban_land": "terreno",
    "rustic_land": "terreno",
    "tourism_land": "terreno",
    "ruin": "moradia",
    "house": "moradia",
    "apartment": "apartamento",
    "modular": "terreno",
    "mobile_home": "terreno",
    "quinta": "quinta",
}

SAPO_TYPE = {
    "urban_land": "terreno",
    "rustic_land": "terreno",
    "tourism_land": "terreno",
    "ruin": "moradia",
    "house": "moradia",
    "apartment": "apartamento",
    "modular": "terreno",
    "mobile_home": "terreno",
    "quinta": "quinta",
}

LAND_TYPES = {
    "urban_land", "rustic_land", "tourism_land", "modular", "mobile_home",
    "lot", "acreage", "ranch", "commercial_land",
}

# Commercial types route to the CRE portals instead of the residential ones —
# a 50-key hotel site never appears on Zillow.
COMMERCIAL_TYPES = {"hotel", "office", "industrial", "commercial_land", "retail"}

LOOPNET_TYPE = {
    "hotel": "hotels", "office": "office-buildings", "industrial": "industrial",
    "commercial_land": "land", "retail": "retail",
}
CREXI_TYPE = {
    "hotel": "hospitality", "office": "office", "industrial": "industrial",
    "commercial_land": "land", "retail": "retail",
}
CCAFE_TYPE = {
    "hotel": "hotel", "office": "office", "industrial": "industrial",
    "commercial_land": "land", "retail": "retail",
}

# US portal vocabulary.
ZILLOW_TYPE = {
    "lot": "land", "acreage": "land", "ranch": "land",
    "house": "houses", "condo": "condos", "townhouse": "townhomes",
}

REDFIN_TYPE = {
    "lot": "land", "acreage": "land", "ranch": "land",
    "house": "house", "condo": "condo", "townhouse": "townhouse",
}

# LandWatch paths spell the state out. Only the states actually searched are
# listed; an unlisted state skips LandWatch rather than emitting a broken slug.
US_STATE_NAMES = {"TX": "texas"}

REALTOR_TYPE = {
    "lot": "land", "acreage": "land", "ranch": "farm",
    "house": "single-family-home", "condo": "condo", "townhouse": "townhome",
}


def slugify(value: str) -> str:
    """Portal location slug: lowercase, accents stripped, hyphen separated."""
    norm = unicodedata.normalize("NFKD", value)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return norm


def load_profile(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError:
        return _mini_yaml(text)


def _mini_yaml(text: str) -> dict:
    """Minimal YAML subset parser so the script runs without PyYAML installed.

    Handles nested mappings by indentation, `- item` block lists and inline
    `[]` / `{}`. That covers the profile template; install PyYAML if the profile
    ever grows anchors, multi-line strings or lists of mappings.
    """
    lines = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        body = raw.split(" #", 1)[0].rstrip()
        lines.append((len(body) - len(body.lstrip()), body.strip()))

    def parse_block(idx: int, indent: int):
        """Return (container, next_index) for the block starting at idx."""
        container = None
        while idx < len(lines):
            cur_indent, content = lines[idx]
            if cur_indent < indent:
                break

            if content.startswith("- "):
                if container is None:
                    container = []
                if not isinstance(container, list):
                    break
                container.append(_scalar(content[2:]))
                idx += 1
                continue

            if ":" not in content:
                idx += 1
                continue

            if container is None:
                container = {}
            if not isinstance(container, dict):
                break

            key, _, value = content.partition(":")
            key, value = key.strip(), value.strip()
            idx += 1
            if value:
                container[key] = _scalar(value)
            elif idx < len(lines) and lines[idx][0] > cur_indent:
                child, idx = parse_block(idx, lines[idx][0])
                container[key] = child if child is not None else {}
            else:
                container[key] = ""
        return container, idx

    parsed, _ = parse_block(0, 0)
    return parsed if isinstance(parsed, dict) else {}


def _scalar(value: str):
    value = value.strip().strip('"').strip("'")
    if value in ("[]", "{}", ""):
        return [] if value == "[]" else ({} if value == "{}" else "")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(p) for p in inner.split(",")] if inner else []
    low = value.lower()
    if low in ("true", "false"):
        return low == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d*\.\d+", value):
        return float(value)
    return value


def searches(profile: dict, only: str | None = None) -> list[dict]:
    """Return the profile's searches.

    Accepts both the multi-search schema and the older single-`strategy` profile,
    so existing profiles keep working without migration.
    """
    found = profile.get("searches")
    if isinstance(found, list) and found:
        result = [s for s in found if isinstance(s, dict) and s.get("name")]
    elif profile.get("strategy"):
        legacy = dict(profile["strategy"])
        legacy.setdefault("name", "default")
        legacy["budget"] = profile.get("budget") or {}
        legacy["requirements"] = profile.get("requirements") or {}
        result = [legacy]
    else:
        result = []

    result = [s for s in result if s.get("active", True)]
    if only:
        result = [s for s in result if s.get("name") == only]
    return result


def country_of(search: dict) -> str:
    return (search.get("country") or DEFAULT_COUNTRY).upper()


def _locations(search: dict) -> list[str]:
    """The place names a portal path is built from.

    `concelhos` (Portugal) and `counties`/`cities` (US) are the same idea wearing
    local clothes, so both feed the same list.
    """
    zone = search.get("zone") or {}
    locs = [c for c in (zone.get("concelhos") or []) if c]
    locs += [c for c in (zone.get("cities") or []) if c]
    locs += [c for c in (zone.get("counties") or []) if c]
    if not locs and zone.get("anchor"):
        locs = [zone["anchor"]]
    return locs


def _cities(search: dict) -> list[str]:
    zone = search.get("zone") or {}
    cities = [c for c in (zone.get("cities") or []) if c]
    return cities or ([zone["anchor"]] if zone.get("anchor") else [])


def _state(search: dict) -> str:
    return ((search.get("zone") or {}).get("state") or "TX").upper()


def _usd(value) -> str:
    """Redfin and Realtor take price shorthand: 450000 -> 450k, 1200000 -> 1.2M."""
    n = int(value)
    if n >= 1_000_000:
        text = f"{n / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"{text}M"
    return f"{n // 1000}k" if n % 1000 == 0 else str(n)


def idealista_urls(search: dict) -> list[str]:
    budget = search.get("budget") or {}
    req = search.get("requirements") or {}
    urls = []
    for ptype in search.get("property_types") or []:
        op = IDEALISTA_OP.get(ptype, "comprar-casas")
        filters = ["ordem-publicado-desc"]
        if budget.get("max"):
            filters.insert(0, f"preco-max_{int(budget['max'])}")
        if budget.get("min"):
            filters.insert(0, f"preco-min_{int(budget['min'])}")
        if ptype in LAND_TYPES and req.get("land_m2_min"):
            filters.append(f"tamanho-terreno-min_{int(req['land_m2_min'])}")
        if ptype not in LAND_TYPES and req.get("built_m2_min"):
            filters.append(f"metros-quadrados-min_{int(req['built_m2_min'])}")
        for loc in _locations(search):
            urls.append(
                f"https://www.idealista.pt/{op}/{slugify(loc)}/com-{','.join(filters)}/"
            )
    return urls


def imovirtual_urls(search: dict) -> list[str]:
    zone = search.get("zone") or {}
    budget = search.get("budget") or {}
    req = search.get("requirements") or {}
    urls = []
    for ptype in search.get("property_types") or []:
        kind = IMOVIRTUAL_TYPE.get(ptype, "moradia")
        params = ["nrAdsPerPage=72", "search%5Border%5D=created_at%3Adesc"]
        if budget.get("max"):
            params.append(f"search%5Bfilter_float_price%3Ato%5D={int(budget['max'])}")
        if budget.get("min"):
            params.append(f"search%5Bfilter_float_price%3Afrom%5D={int(budget['min'])}")
        if zone.get("radius_km"):
            params.append(f"search%5Bdist%5D={int(zone['radius_km'])}")
        if ptype in LAND_TYPES and req.get("land_m2_min"):
            params.append(f"search%5Bfilter_float_m%3Afrom%5D={int(req['land_m2_min'])}")
        for loc in _locations(search):
            urls.append(
                f"https://www.imovirtual.com/comprar/{kind}/{slugify(loc)}/?"
                + "&".join(params)
            )
    return urls


def casa_sapo_urls(search: dict) -> list[str]:
    budget = search.get("budget") or {}
    urls = []
    for ptype in search.get("property_types") or []:
        kind = SAPO_TYPE.get(ptype, "moradia")
        params = ["or=10"]  # most recent first
        if budget.get("max"):
            params.append(f"pmax={int(budget['max'])}")
        if budget.get("min"):
            params.append(f"pmin={int(budget['min'])}")
        for loc in _locations(search):
            urls.append(
                f"https://casa.sapo.pt/comprar-{kind}/{slugify(loc)}/?" + "&".join(params)
            )
    return urls


def olx_urls(search: dict) -> list[str]:
    budget = search.get("budget") or {}
    urls = []
    for ptype in search.get("property_types") or []:
        category = (
            "terrenos-quintas" if ptype in LAND_TYPES or ptype == "quinta"
            else "apartamentos" if ptype == "apartment"
            else "moradias"
        )
        params = ["search%5Border%5D=created_at%3Adesc"]
        if budget.get("max"):
            params.append(f"search%5Bfilter_float_price%3Ato%5D={int(budget['max'])}")
        for loc in _locations(search):
            urls.append(
                f"https://www.olx.pt/imoveis/{category}/{slugify(loc)}/?" + "&".join(params)
            )
    return urls


def facebook_queries(search: dict) -> list[str]:
    terms = {
        "urban_land": "terreno urbano",
        "rustic_land": "terreno rustico",
        "tourism_land": "terreno turismo",
        "ruin": "ruina",
        "house": "moradia",
        "apartment": "apartamento",
        "quinta": "quinta",
        "modular": "casa modular",
        "mobile_home": "casa movel",
    }
    out = []
    for ptype in search.get("property_types") or []:
        term = terms.get(ptype, "terreno")
        for loc in _locations(search):
            out.append(
                "https://www.facebook.com/marketplace/search/?query="
                + quote(f"{term} {loc}")
            )
    return out




# --- United States -----------------------------------------------------------
#
# Zillow, Redfin and Realtor.com all forbid automated harvesting and block it
# quickly, exactly like Idealista. These URLs exist to be opened once by the
# logged-in user, checked, and saved with an email alert — that alert is the
# intake channel, not a crawler.


def zillow_urls(search: dict) -> list[str]:
    """Zillow region pages.

    Zillow's real filter grammar is a JSON `searchQueryState` blob that it
    rewrites without notice, so only the region and property type go in the
    path. Price and acreage are set once in the UI before saving — see
    references/portals-us.md.
    """
    urls = []
    for ptype in search.get("property_types") or []:
        if ptype in COMMERCIAL_TYPES:
            continue
        kind = ZILLOW_TYPE.get(ptype, "houses")
        for city in _cities(search):
            urls.append(
                f"https://www.zillow.com/{slugify(city)}-{_state(search).lower()}/{kind}/"
            )
    return urls


def redfin_urls(search: dict) -> list[str]:
    """Redfin filter URLs.

    Redfin's `/filter/` grammar is comma-separated and stable, so the whole
    search deep-links. It is keyed by ZIP here on purpose: the city form needs
    an opaque numeric region id that cannot be derived from the name.
    """
    zone = search.get("zone") or {}
    budget = search.get("budget") or {}
    req = search.get("requirements") or {}
    zips = [str(z) for z in (zone.get("zips") or []) if z]
    if not zips:
        return []

    urls = []
    for ptype in search.get("property_types") or []:
        if ptype in COMMERCIAL_TYPES:
            continue
        filters = [f"property-type={REDFIN_TYPE.get(ptype, 'house')}"]
        if budget.get("min"):
            filters.append(f"min-price={_usd(budget['min'])}")
        if budget.get("max"):
            filters.append(f"max-price={_usd(budget['max'])}")
        if ptype in LAND_TYPES and req.get("land_acres_min"):
            filters.append(f"min-lot-size={req['land_acres_min']}-acre")
        if ptype not in LAND_TYPES:
            if req.get("built_sqft_min"):
                filters.append(f"min-sqft={int(req['built_sqft_min'])}-sqft")
            if req.get("bedrooms_min"):
                filters.append(f"min-beds={int(req['bedrooms_min'])}")
        filters.append("sort=newest")
        for zipcode in zips:
            urls.append(
                f"https://www.redfin.com/zipcode/{zipcode}/filter/" + ",".join(filters)
            )
    return urls


def realtor_urls(search: dict) -> list[str]:
    """Realtor.com search paths — MLS-fed, and the least hostile of the three."""
    budget = search.get("budget") or {}
    req = search.get("requirements") or {}
    urls = []
    for ptype in search.get("property_types") or []:
        if ptype in COMMERCIAL_TYPES:
            continue
        segments = [f"type-{REALTOR_TYPE.get(ptype, 'single-family-home')}"]
        lo, hi = int(budget.get("min") or 0), int(budget.get("max") or 0)
        if hi:
            segments.append(f"price-{lo}-{hi}" if lo else f"price-na-{hi}")
        if ptype in LAND_TYPES and req.get("land_acres_min"):
            segments.append(f"lot-sqft-{int(float(req['land_acres_min']) * 43560)}")
        if ptype not in LAND_TYPES and req.get("bedrooms_min"):
            segments.append(f"beds-{int(req['bedrooms_min'])}")
        segments.append("sby-6")  # newest first
        for city in _cities(search):
            place = f"{slugify(city).replace('-', '-').title()}_{_state(search)}"
            urls.append(
                "https://www.realtor.com/realestateandhomes-search/"
                + place + "/" + "/".join(segments)
            )
    return urls


def landwatch_urls(search: dict) -> list[str]:
    """LandWatch — rural acreage, where Hill Country tracts surface first."""
    budget = search.get("budget") or {}
    req = search.get("requirements") or {}
    state = _state(search)
    urls = []
    types = [t for t in (search.get("property_types") or [])
             if t in LAND_TYPES and t != "commercial_land"]
    if not types:
        return []
    if state not in US_STATE_NAMES:
        print(f"LandWatch skipped: no path slug known for state {state!r}. "
              f"Add it to US_STATE_NAMES.", file=sys.stderr)
        return []
    for county in ((search.get("zone") or {}).get("counties") or _cities(search)):
        parts = [f"https://www.landwatch.com/{slugify(county)}-county-"
                 f"{slugify(US_STATE_NAMES.get(state, state))}-land-for-sale"]
        if budget.get("max"):
            parts.append(f"price-{int(budget.get('min') or 0)}-{int(budget['max'])}")
        if req.get("land_acres_min"):
            parts.append(f"acres-over-{int(float(req['land_acres_min']))}")
        parts.append("sort-recent")
        urls.append("/".join(parts))
    return urls


def _is_lodging(search: dict) -> bool:
    return any(t in ("hotel", "resort") for t in (search.get("property_types") or []))


def bizbuysell_urls(search: dict) -> list[str]:
    """Operating lodging businesses, listed as businesses rather than as land.

    A tired hotel is usually sold as a going concern by a business broker, not
    as real estate by a CRE broker — so it never appears on LoopNet at all.

    Tier caveat: BizBuySell's median closed sale is around $350,000, which is
    Main Street territory. It will surface a small independent lodge and will
    not surface a $20M resort. Use it for the small end and specialist hotel
    brokers for everything above — see references/portals-us.md.
    """
    if not _is_lodging(search):
        return []
    state = US_STATE_NAMES.get(_state(search), _state(search)).lower()
    urls = [f"https://www.bizbuysell.com/{state}/hotels-for-sale/",
            f"https://www.bizbuysell.com/{state}/motels-for-sale/",
            f"https://www.bizbuysell.com/{state}/bed-and-breakfasts-for-sale/"]
    for county in ((search.get("zone") or {}).get("counties") or []):
        urls.append(f"https://www.bizbuysell.com/{state}/{slugify(county)}-county/"
                    "hotels-for-sale/")
    return urls


def bizquest_urls(search: dict) -> list[str]:
    """BizQuest — same owner as BizBuySell, but only 65-75% overlapping stock.

    That gap is the whole reason to run both: a quarter of the listings appear
    on one and not the other.
    """
    if not _is_lodging(search):
        return []
    state = US_STATE_NAMES.get(_state(search), _state(search)).lower()
    return [
        f"https://www.bizquest.com/hotels-and-motels-for-sale-in-{state}/",
        f"https://www.bizquest.com/bed-and-breakfasts-for-sale-in-{state}/",
    ]


def businessbroker_urls(search: dict) -> list[str]:
    """BusinessBroker.net — independent of the CoStar pair, plus a broker directory."""
    if not _is_lodging(search):
        return []
    state = US_STATE_NAMES.get(_state(search), _state(search)).lower()
    return [f"https://www.businessbroker.net/businesses-for-sale/{state}/",
            f"https://www.businessbroker.net/brokers/{state}.aspx"]


def businessesforsale_urls(search: dict) -> list[str]:
    if not _is_lodging(search):
        return []
    state = US_STATE_NAMES.get(_state(search), _state(search)).lower()
    return [f"https://us.businessesforsale.com/us/search/hotels-for-sale/{state}",
            f"https://us.businessesforsale.com/us/search/bed-and-breakfasts-for-sale/{state}"]


def dealstream_urls(search: dict) -> list[str]:
    """DealStream — skews larger than the Main Street marketplaces."""
    if not _is_lodging(search):
        return []
    state = US_STATE_NAMES.get(_state(search), _state(search)).lower()
    return [f"https://dealstream.com/hotels-for-sale/{state}",
            f"https://dealstream.com/businesses-for-sale/{state}"]


def facebook_us_queries(search: dict) -> list[str]:
    terms = {"lot": "vacant lot", "acreage": "acreage land",
             "ranch": "ranch land", "house": "house"}
    out = []
    for ptype in search.get("property_types") or []:
        # Marketplace is a private-seller channel for land and houses. It is not
        # where a multi-million-dollar hotel site trades.
        if ptype in COMMERCIAL_TYPES:
            continue
        term = terms.get(ptype, "land")
        for city in _cities(search):
            out.append("https://www.facebook.com/marketplace/search/?query="
                       + quote(f"{term} {city} {_state(search)}"))
    return out



# --- United States, commercial ----------------------------------------------
#
# Hotel sites, office buildings and commercial land trade on entirely different
# platforms from houses. LoopNet (CoStar-owned) has the deepest on-market
# inventory and the strongest SEO; Crexi is the main competitor and runs the
# better auction channel. Both gate detail behind a login and block automated
# access, so these URLs are for a logged-in human to open and save.


def loopnet_urls(search: dict) -> list[str]:
    """LoopNet search paths, one per commercial type per city."""
    urls = []
    for ptype in search.get("property_types") or []:
        if ptype not in COMMERCIAL_TYPES:
            continue
        kind = LOOPNET_TYPE.get(ptype, "commercial-real-estate")
        for city in _cities(search):
            urls.append(
                f"https://www.loopnet.com/search/{kind}/"
                f"{slugify(city)}-{_state(search).lower()}/for-sale/"
            )
    return urls


def crexi_urls(search: dict) -> list[str]:
    urls = []
    state = _state(search)
    for ptype in search.get("property_types") or []:
        if ptype not in COMMERCIAL_TYPES:
            continue
        kind = CREXI_TYPE.get(ptype, "")
        for city in _cities(search):
            urls.append(
                f"https://www.crexi.com/properties/{state}/{slugify(city)}"
                + (f"/{kind}" if kind else "")
            )
    return urls


def commercialcafe_urls(search: dict) -> list[str]:
    urls = []
    for ptype in search.get("property_types") or []:
        if ptype not in COMMERCIAL_TYPES:
            continue
        kind = CCAFE_TYPE.get(ptype, "")
        for city in _cities(search):
            urls.append(
                "https://www.commercialcafe.com/commercial-real-estate/us/"
                f"{_state(search).lower()}/{slugify(city)}/"
                + (f"{kind}/" if kind else "") + "for-sale/"
            )
    return urls


BUILDERS = {
    "PT": {
        "idealista": idealista_urls,
        "imovirtual": imovirtual_urls,
        "casa_sapo": casa_sapo_urls,
        "olx": olx_urls,
        "facebook": facebook_queries,
    },
    "US": {
        "zillow": zillow_urls,
        "redfin": redfin_urls,
        "realtor": realtor_urls,
        "landwatch": landwatch_urls,
        "facebook": facebook_us_queries,
        "loopnet": loopnet_urls,
        "crexi": crexi_urls,
        "commercialcafe": commercialcafe_urls,
        "bizbuysell": bizbuysell_urls,
        "bizquest": bizquest_urls,
        "businessbroker": businessbroker_urls,
        "businessesforsale": businessesforsale_urls,
        "dealstream": dealstream_urls,
    },
}

ALL_PORTALS = sorted({p for country in BUILDERS.values() for p in country})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--search", help="build only this named search")
    ap.add_argument("--portal", choices=ALL_PORTALS, help="limit to one portal")
    ap.add_argument("--format", choices=("markdown", "json", "plain"), default="markdown")
    ap.add_argument("--list", action="store_true", help="list the searches and exit")
    args = ap.parse_args()

    if not args.profile.exists():
        print(f"Profile not found: {args.profile}", file=sys.stderr)
        print("Copy references/profile-template.yaml and fill it in first.", file=sys.stderr)
        return 1

    profile = load_profile(args.profile)
    active = searches(profile, args.search)

    if args.list:
        every = searches(profile)
        if not every:
            print("No searches defined yet.")
            return 0
        for s in every:
            zone = s.get("zone") or {}
            print(f"{s['name']:20} {country_of(s):3} "
                  f"{', '.join(s.get('property_types') or []) or '?':26} "
                  f"{zone.get('anchor', '?')} ({zone.get('radius_km', '?')} km)")
        return 0

    if not active:
        names = [s.get("name") for s in searches(profile)]
        if args.search:
            print(f"No active search named {args.search!r}. Defined: "
                  f"{', '.join(n for n in names if n) or 'none'}", file=sys.stderr)
        else:
            print("No active searches in the profile — nothing to build.", file=sys.stderr)
        return 1

    result: dict[str, dict[str, list[str]]] = {}
    for search in active:
        if not (search.get("property_types") and _locations(search)):
            print(f"Search {search['name']!r} has no property_types or no zone — skipped.",
                  file=sys.stderr)
            continue
        country = country_of(search)
        builders = BUILDERS.get(country)
        if not builders:
            print(f"Search {search['name']!r} has country {country!r}, which has no "
                  f"portals defined. Known: {', '.join(sorted(BUILDERS))}.",
                  file=sys.stderr)
            continue
        if args.portal and args.portal not in builders:
            continue  # portal belongs to another country
        chosen = [args.portal] if args.portal else list(builders)
        result[search["name"]] = {p: builders[p](search) for p in chosen}

    if not result:
        return 1

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.format == "plain":
        for per_portal in result.values():
            for urls in per_portal.values():
                for u in urls:
                    print(u)
        return 0

    print("# Saved searches\n")
    print("Open each while logged in, save the search, and switch on the daily "
          "email alert. Name each alert after its search so the incoming mail "
          "sorts itself.\n")
    for search in active:
        name = search["name"]
        if name not in result:
            continue
        zone = search.get("zone") or {}
        budget = search.get("budget") or {}
        header = (f"## {name} — {zone.get('anchor', 'zone')} "
                  f"({zone.get('radius_km', '?')} km) · "
                  f"{', '.join(search.get('property_types') or [])}")
        if budget.get("max"):
            symbol = "$" if country_of(search) == "US" else "€"
            header += (f" · {symbol}{int(budget.get('min') or 0):,}"
                       f"–{symbol}{int(budget['max']):,}")
        print(header + "\n")
        for portal, urls in result[name].items():
            if not urls:
                continue
            print(f"### {portal.replace('_', ' ').title()}")
            for u in urls:
                print(f"- {u}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
