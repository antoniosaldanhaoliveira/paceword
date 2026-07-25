#!/usr/bin/env python3
"""Build saved-search URLs for the Portuguese property portals from a buyer profile.

The URLs are meant to be opened by the user (logged in) so they can save the
search and switch on the daily email alert — that is the intake channel the
guide recommends and the one the portals actually permit.

Usage:
    python build_search_urls.py --profile ~/property-portugal/profile.yaml
    python build_search_urls.py --profile ... --portal idealista
    python build_search_urls.py --profile ... --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

PORTALS = ("idealista", "imovirtual", "casa_sapo", "olx")

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

LAND_TYPES = {"urban_land", "rustic_land", "tourism_land", "modular", "mobile_home"}


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


def _locations(profile: dict) -> list[str]:
    zone = (profile.get("strategy") or {}).get("zone") or {}
    locs = [c for c in (zone.get("concelhos") or []) if c]
    if not locs and zone.get("anchor"):
        locs = [zone["anchor"]]
    return locs


def idealista_urls(profile: dict) -> list[str]:
    strategy = profile.get("strategy") or {}
    budget = profile.get("budget") or {}
    req = profile.get("requirements") or {}
    urls = []
    for ptype in strategy.get("property_types") or []:
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
        for loc in _locations(profile):
            urls.append(
                f"https://www.idealista.pt/{op}/{slugify(loc)}/com-{','.join(filters)}/"
            )
    return urls


def imovirtual_urls(profile: dict) -> list[str]:
    strategy = profile.get("strategy") or {}
    zone = strategy.get("zone") or {}
    budget = profile.get("budget") or {}
    req = profile.get("requirements") or {}
    urls = []
    for ptype in strategy.get("property_types") or []:
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
        for loc in _locations(profile):
            urls.append(
                f"https://www.imovirtual.com/comprar/{kind}/{slugify(loc)}/?"
                + "&".join(params)
            )
    return urls


def casa_sapo_urls(profile: dict) -> list[str]:
    strategy = profile.get("strategy") or {}
    budget = profile.get("budget") or {}
    urls = []
    for ptype in strategy.get("property_types") or []:
        kind = SAPO_TYPE.get(ptype, "moradia")
        params = ["or=10"]  # most recent first
        if budget.get("max"):
            params.append(f"pmax={int(budget['max'])}")
        if budget.get("min"):
            params.append(f"pmin={int(budget['min'])}")
        for loc in _locations(profile):
            urls.append(
                f"https://casa.sapo.pt/comprar-{kind}/{slugify(loc)}/?" + "&".join(params)
            )
    return urls


def olx_urls(profile: dict) -> list[str]:
    strategy = profile.get("strategy") or {}
    budget = profile.get("budget") or {}
    urls = []
    for ptype in strategy.get("property_types") or []:
        category = (
            "terrenos-quintas" if ptype in LAND_TYPES or ptype == "quinta"
            else "apartamentos" if ptype == "apartment"
            else "moradias"
        )
        params = ["search%5Border%5D=created_at%3Adesc"]
        if budget.get("max"):
            params.append(f"search%5Bfilter_float_price%3Ato%5D={int(budget['max'])}")
        for loc in _locations(profile):
            urls.append(
                f"https://www.olx.pt/imoveis/{category}/{slugify(loc)}/?" + "&".join(params)
            )
    return urls


def facebook_queries(profile: dict) -> list[str]:
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
    strategy = profile.get("strategy") or {}
    out = []
    for ptype in strategy.get("property_types") or []:
        term = terms.get(ptype, "terreno")
        for loc in _locations(profile):
            out.append(
                "https://www.facebook.com/marketplace/search/?query="
                + quote(f"{term} {loc}")
            )
    return out


BUILDERS = {
    "idealista": idealista_urls,
    "imovirtual": imovirtual_urls,
    "casa_sapo": casa_sapo_urls,
    "olx": olx_urls,
    "facebook": facebook_queries,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--portal", choices=list(BUILDERS), help="limit to one portal")
    ap.add_argument("--format", choices=("markdown", "json", "plain"), default="markdown")
    args = ap.parse_args()

    if not args.profile.exists():
        print(f"Profile not found: {args.profile}", file=sys.stderr)
        print("Copy references/profile-template.yaml and fill it in first.", file=sys.stderr)
        return 1

    profile = load_profile(args.profile)
    strategy = profile.get("strategy") or {}
    if not strategy.get("property_types"):
        print("Profile has no strategy.property_types — nothing to search.", file=sys.stderr)
        return 1
    if not _locations(profile):
        print("Profile has no zone.anchor or zone.concelhos — nothing to search.", file=sys.stderr)
        return 1

    portals = [args.portal] if args.portal else list(BUILDERS)
    result = {p: BUILDERS[p](profile) for p in portals}

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.format == "plain":
        for urls in result.values():
            for u in urls:
                print(u)
        return 0

    zone = strategy.get("zone") or {}
    print(f"# Saved searches — {zone.get('anchor', 'zone')} "
          f"({zone.get('radius_km', '?')} km radius)\n")
    print("Open each while logged in, save the search, and switch on the daily "
          "email alert.\n")
    for portal, urls in result.items():
        if not urls:
            continue
        print(f"## {portal.replace('_', ' ').title()}")
        for u in urls:
            print(f"- {u}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
