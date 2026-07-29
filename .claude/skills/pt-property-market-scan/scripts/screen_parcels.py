#!/usr/bin/env python3
"""Screen every parcel in an area by characteristics, not by listing status.

Listing portals only show what is for sale. This asks a different question:
which parcels *could* hold the project, whoever owns them and whether or not
they are on the market. For a constrained programme — a hotel in a watershed
with an impervious-cover cap — that set is small, findable, and mostly
off-market.

The screen is driven by public GIS: a parcel layer for geometry and area, a
watershed or overlay layer for the regulatory cap, and optionally a zoning
layer. All three are ordinary ArcGIS REST endpoints published by the city or
county. Nothing here scrapes a listing site.

    # find the layer endpoints once, when the network allows it
    python screen_parcels.py discover --config config/austin.json

    # run the screen
    python screen_parcels.py screen --config config/austin.json --out targets.csv

    # prove the scoring logic without touching the network
    python screen_parcels.py selftest

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SQFT_PER_ACRE = 43560.0
UA = "Mozilla/5.0 (compatible; property-research/1.0)"


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Unreachable(RuntimeError):
    """The endpoint could not be reached — usually the sandbox, not the host."""


def fetch_json(url: str, params: dict | None = None, timeout: int = 60) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 407):
            raise Unreachable(
                f"HTTP {exc.code} for {url[:90]}...\n"
                "  A 403 on CONNECT usually means this environment's network policy\n"
                "  is refusing the host, not that the host is refusing you. Check\n"
                "  the sandbox egress allowlist before assuming the endpoint is dead."
            ) from exc
        raise Unreachable(f"HTTP {exc.code} for {url[:90]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise Unreachable(f"Could not reach {url[:90]}: {exc}") from exc


# --------------------------------------------------------------------------
# Geometry — point in polygon, ray casting. Enough for centroid-in-watershed.
# --------------------------------------------------------------------------

def ring_contains(ring: list[list[float]], x: float, y: float) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            xint = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
            if x < xint:
                inside = not inside
    return inside


def polygon_contains(geometry: dict, x: float, y: float) -> bool:
    """ArcGIS polygon: outer rings clockwise, holes counter-clockwise.

    Treating every ring as a toggle handles holes correctly for our purpose —
    a point inside a hole flips twice and lands outside.
    """
    rings = geometry.get("rings") or []
    inside = False
    for ring in rings:
        if len(ring) >= 3 and ring_contains(ring, x, y):
            inside = not inside
    return inside


def centroid(geometry: dict) -> tuple[float, float] | None:
    """Area-weighted centroid of the largest ring, falling back to mean vertex."""
    rings = geometry.get("rings") or []
    if not rings:
        return None
    ring = max(rings, key=len)
    a = cx = cy = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(a) < 1e-12:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)


def ring_area(ring: list[list[float]]) -> float:
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return abs(a) * 0.5


def polygon_area(geometry: dict) -> float:
    """Projected area in the layer's own units. Only valid for projected CRS."""
    rings = geometry.get("rings") or []
    if not rings:
        return 0.0
    outer = ring_area(max(rings, key=ring_area))
    holes = sum(ring_area(r) for r in rings if r is not max(rings, key=ring_area))
    return max(outer - holes, 0.0)


# --------------------------------------------------------------------------
# ArcGIS REST
# --------------------------------------------------------------------------

def query_layer(url: str, where: str = "1=1", out_fields: str = "*",
                geometry: dict | None = None, page: int = 1000,
                max_records: int | None = None) -> list[dict]:
    """Page through an ArcGIS feature layer, returning features with geometry."""
    features: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where, "outFields": out_fields, "returnGeometry": "true",
            "f": "json", "resultOffset": offset, "resultRecordCount": page,
            "outSR": 4326,
        }
        if geometry:
            params.update({
                "geometry": json.dumps(geometry), "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects", "inSR": 4326,
            })
        data = fetch_json(f"{url.rstrip('/')}/query", params)
        if "error" in data:
            raise Unreachable(f"Layer error: {data['error'].get('message', data['error'])}")
        batch = data.get("features", [])
        features.extend(batch)
        if len(batch) < page or not data.get("exceededTransferLimit"):
            break
        offset += page
        if max_records and len(features) >= max_records:
            break
    return features[:max_records] if max_records else features


def discover(base: str) -> list[str]:
    """List services and layers under an ArcGIS REST root."""
    out = []
    root = fetch_json(base.rstrip("/"), {"f": "json"})
    for svc in root.get("services", []):
        name, typ = svc.get("name"), svc.get("type")
        out.append(f"{base.rstrip('/')}/{name.split('/')[-1]}/{typ}")
    for folder in root.get("folders", []):
        out.append(f"[folder] {base.rstrip('/')}/{folder}")
    return out


# --------------------------------------------------------------------------
# The screen
# --------------------------------------------------------------------------

def required_impervious(prog: dict) -> tuple[float, float]:
    """Impervious footprint the programme needs, low and high, in ft²."""
    gfa_lo = gfa_hi = 0.0
    for part in prog["program"]:
        gfa_lo += part["sf_low"]
        gfa_hi += part["sf_high"]
    storeys = prog.get("storeys", 2)
    foot_lo, foot_hi = gfa_lo / max(storeys, 1), gfa_hi / max(storeys - 1, 1)

    spaces_lo, spaces_hi = prog["parking_spaces"]
    if prog.get("structured_parking"):
        park_lo = park_hi = prog.get("deck_footprint_sf", 12000)
    else:
        sf = prog.get("sf_per_surface_space", 340)
        park_lo, park_hi = spaces_lo * sf, spaces_hi * sf

    other_lo, other_hi = prog.get("other_impervious_sf", [15000, 25000])
    return foot_lo + park_lo + other_lo, foot_hi + park_hi + other_hi


def screen_parcel(parcel: dict, cap: float, req: tuple[float, float],
                  rules: dict) -> dict | None:
    """Score one parcel. Returns None if it fails a hard rule."""
    acres = parcel["acres"]
    if acres < rules.get("min_acres", 0):
        return None
    if rules.get("max_acres") and acres > rules["max_acres"]:
        return None

    allowed = acres * SQFT_PER_ACRE * cap
    existing = parcel.get("existing_impervious_sf") or 0.0
    # A grandfathered site may redevelop up to its existing cover where that
    # exceeds the current cap — the whole reason an old building beats raw land.
    envelope = max(allowed, existing) if rules.get("allow_grandfathered", True) else allowed

    req_lo, req_hi = req
    if envelope < req_lo * rules.get("headroom", 1.0):
        return None

    parcel = dict(parcel)
    parcel.update({
        "ic_cap": round(cap, 3),
        "allowed_impervious_sf": round(allowed),
        "envelope_sf": round(envelope),
        "grandfathered": envelope > allowed + 1,
        "fits_low_program": envelope >= req_lo,
        "fits_high_program": envelope >= req_hi,
        # Headroom over the *high* programme is the real comfort margin.
        "headroom_ratio": round(envelope / req_hi, 2) if req_hi else None,
    })
    return parcel


def rank_key(p: dict) -> tuple:
    return (not p["fits_high_program"], -(p.get("headroom_ratio") or 0), -p["acres"])


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def run_screen(cfg: dict, max_records: int | None) -> list[dict]:
    layers = cfg["layers"]
    rules = cfg["rules"]
    prog = cfg["programme"]
    req = required_impervious(prog)
    env = cfg.get("extent")

    print(f"Programme needs {req[0]:,.0f} – {req[1]:,.0f} ft² of impervious cover.",
          file=sys.stderr)

    print("Fetching overlay (watershed / regulatory) polygons…", file=sys.stderr)
    overlays = query_layer(layers["overlay"]["url"], where=layers["overlay"].get("where", "1=1"),
                           geometry=env)
    name_field = layers["overlay"]["name_field"]
    caps = {k.lower(): v for k, v in cfg["ic_caps"].items()}
    default_cap = cfg.get("default_ic_cap", 0.20)
    print(f"  {len(overlays)} overlay polygons", file=sys.stderr)

    print("Fetching parcels…", file=sys.stderr)
    parcels = query_layer(layers["parcels"]["url"], where=layers["parcels"].get("where", "1=1"),
                          geometry=env, max_records=max_records)
    print(f"  {len(parcels)} parcels", file=sys.stderr)

    pf = layers["parcels"]["fields"]
    results = []
    for feat in parcels:
        attrs, geom = feat.get("attributes", {}), feat.get("geometry", {})
        c = centroid(geom)
        if not c:
            continue
        acres = attrs.get(pf.get("acres")) if pf.get("acres") else None
        if acres in (None, ""):
            continue
        try:
            acres = float(acres)
        except (TypeError, ValueError):
            continue

        # Which overlay is this parcel's centroid in?
        cap, zone_name = default_cap, ""
        for ov in overlays:
            if polygon_contains(ov.get("geometry", {}), c[0], c[1]):
                zone_name = str(ov.get("attributes", {}).get(name_field, ""))
                cap = caps.get(zone_name.lower(), default_cap)
                break

        improved = attrs.get(pf.get("improvement_sf")) if pf.get("improvement_sf") else None
        try:
            improved = float(improved) if improved not in (None, "") else 0.0
        except (TypeError, ValueError):
            improved = 0.0
        # Building footprint understates site impervious cover; the multiplier
        # is a screening estimate only and must be replaced by a survey.
        est_existing = improved * cfg.get("improvement_to_impervious", 2.2)

        parcel = {
            "parcel_id": attrs.get(pf.get("id"), ""),
            "address": attrs.get(pf.get("address"), ""),
            "owner": attrs.get(pf.get("owner"), ""),
            "acres": round(acres, 2),
            "zoning": attrs.get(pf.get("zoning"), "") if pf.get("zoning") else "",
            "improvement_sf": round(improved),
            "existing_impervious_sf": round(est_existing),
            "overlay": zone_name,
            "lon": round(c[0], 6), "lat": round(c[1], 6),
        }
        scored = screen_parcel(parcel, cap, req, rules)
        if scored:
            results.append(scored)

    results.sort(key=rank_key)
    return results


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def report(rows: list[dict], cfg: dict, req: tuple[float, float]) -> str:
    lines = [
        "# Parcel screen — candidates by characteristic",
        "",
        f"Programme requires **{req[0]:,.0f} – {req[1]:,.0f} ft²** of impervious cover.",
        f"**{len(rows)}** parcels clear the screen.",
        "",
        "Ranked by headroom over the full programme, then by size. `grandfathered`",
        "means the parcel's *existing* cover exceeds what the cap would allow today —",
        "that cover cannot be recreated on vacant land, and is the reason to prefer",
        "a built site. Every existing-cover figure here is **estimated from",
        "improvement area and must be replaced by a survey** before it means anything.",
        "",
        "| Parcel | Address | Acres | Overlay | Cap | Envelope ft² | Grandfathered | Headroom |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows[:60]:
        lines.append(
            f"| {r['parcel_id']} | {r['address'][:38]} | {r['acres']} | "
            f"{r['overlay'][:22]} | {r['ic_cap']:.0%} | {r['envelope_sf']:,} | "
            f"{'yes' if r['grandfathered'] else '—'} | {r['headroom_ratio']}× |"
        )
    if len(rows) > 60:
        lines.append(f"\n_{len(rows) - 60} further parcels in the CSV._")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Self-test — proves the scoring without any network
# --------------------------------------------------------------------------

def selftest() -> int:
    ok = True

    def check(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: {got!r}"
              + ("" if good else f" (expected {want!r})"))

    print("geometry")
    square = {"rings": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]]}
    check("centre inside", polygon_contains(square, 5, 5), True)
    check("outside", polygon_contains(square, 15, 5), False)
    check("area", polygon_area(square), 100.0)
    cx, cy = centroid(square)
    check("centroid", (round(cx, 6), round(cy, 6)), (5.0, 5.0))

    donut = {"rings": [
        [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]],
        [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]],
    ]}
    check("point in hole excluded", polygon_contains(donut, 5, 5), False)
    check("point in ring included", polygon_contains(donut, 1, 1), True)

    print("\nprogramme")
    prog = {
        "program": [
            {"name": "rooms", "sf_low": 20000, "sf_high": 25000},
            {"name": "spa", "sf_low": 10000, "sf_high": 15000},
            {"name": "f&b/boh", "sf_low": 10000, "sf_high": 15000},
        ],
        "storeys": 3, "parking_spaces": [120, 170],
        "sf_per_surface_space": 340, "other_impervious_sf": [15000, 25000],
    }
    lo, hi = required_impervious(prog)
    check("surface parking low", round(lo), 69133)
    check("surface parking high", round(hi), 110300)
    prog_struct = dict(prog, structured_parking=True, deck_footprint_sf=12000)
    slo, shi = required_impervious(prog_struct)
    check("structured is smaller", shi < hi, True)

    print("\nscreen")
    rules = {"min_acres": 5, "allow_grandfathered": True}
    raw5 = {"parcel_id": "A", "acres": 5.0, "existing_impervious_sf": 0}
    check("5ac raw @15% rejected", screen_parcel(raw5, 0.15, (lo, hi), rules), None)
    raw12 = {"parcel_id": "B", "acres": 12.0, "existing_impervious_sf": 0}
    r = screen_parcel(raw12, 0.15, (lo, hi), rules)
    check("12ac raw @15% passes", bool(r), True)
    check("12ac not grandfathered", r["grandfathered"], False)

    # The strategic case: small site, big existing cover.
    built5 = {"parcel_id": "C", "acres": 5.0, "existing_impervious_sf": 126000}
    r2 = screen_parcel(built5, 0.15, (lo, hi), rules)
    check("5ac grandfathered passes", bool(r2), True)
    check("flagged grandfathered", r2["grandfathered"], True)
    check("envelope is existing cover", r2["envelope_sf"], 126000)
    check("beats raw 5ac allowance", r2["envelope_sf"] > 5 * SQFT_PER_ACRE * 0.15, True)

    check("min_acres enforced", screen_parcel(
        {"parcel_id": "D", "acres": 2.0, "existing_impervious_sf": 200000},
        0.15, (lo, hi), rules), None)

    print("\nranking")
    rows = [
        {"fits_high_program": False, "headroom_ratio": 0.8, "acres": 20},
        {"fits_high_program": True, "headroom_ratio": 1.4, "acres": 9},
        {"fits_high_program": True, "headroom_ratio": 2.1, "acres": 14},
    ]
    rows.sort(key=rank_key)
    check("best headroom first", rows[0]["headroom_ratio"], 2.1)
    check("non-fitting last", rows[-1]["fits_high_program"], False)

    print("\n" + ("ALL PASS" if ok else "FAILURES"))
    return 0 if ok else 1


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="list ArcGIS services/layers at a root")
    d.add_argument("--config", type=Path)
    d.add_argument("--url", help="ArcGIS REST root, overrides config")

    s = sub.add_parser("screen", help="run the parcel screen")
    s.add_argument("--config", type=Path, required=True)
    s.add_argument("--out", type=Path, default=Path("targets.csv"))
    s.add_argument("--report", type=Path)
    s.add_argument("--max", type=int, help="cap parcels fetched (for a trial run)")

    sub.add_parser("selftest", help="verify the scoring logic offline")

    args = ap.parse_args()

    if args.cmd == "selftest":
        return selftest()

    if args.cmd == "discover":
        roots = []
        if args.url:
            roots = [args.url]
        elif args.config:
            cfg = json.loads(args.config.read_text())
            roots = cfg.get("discover_roots", [])
        if not roots:
            print("Give --url or a config with discover_roots.", file=sys.stderr)
            return 1
        for root in roots:
            print(f"\n== {root}")
            try:
                for line in discover(root):
                    print(f"   {line}")
            except Unreachable as exc:
                print(f"   {exc}", file=sys.stderr)
                return 2
        return 0

    cfg = json.loads(args.config.read_text())
    try:
        rows = run_screen(cfg, args.max)
    except Unreachable as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        print("Nothing was written. Run `selftest` to confirm the logic is intact.",
              file=sys.stderr)
        return 2

    write_csv(rows, args.out)
    req = required_impervious(cfg["programme"])
    text = report(rows, cfg, req)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text)
    print(f"{len(rows)} candidates -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
