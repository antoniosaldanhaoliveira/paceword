#!/usr/bin/env python3
"""Track Portuguese property listings over time.

Keeps one CSV of unique properties plus an append-only price history, and
answers the questions that only accumulate with time: what is new, what dropped,
what disappeared, and what a square metre actually costs in this zone.

Several named searches can run in parallel. Every statistic is scoped to one
search, because a search is the unit that has a coherent €/m² baseline — pooling
two zones produces a median that describes neither.

Standard library only, except `export --xlsx` which uses openpyxl if present.

Commands:
    ingest   record listings from a JSON array
    sweep    mark which listings are still live; flag the rest as disappeared
    digest   what changed since the last run
    stats    €/m² medians, days on market, outliers
    searches overview of every search being tracked
    note     attach a note or log a visit
    set      change status / rating / dd_status on a listing
    export   write a spreadsheet for the user
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
from datetime import date, datetime
from pathlib import Path

COLUMNS = [
    "id", "search", "source", "source_ref", "url", "title", "property_type",
    "concelho", "freguesia", "lat", "lon",
    "price", "first_price", "land_m2", "built_m2",
    "eur_per_land_m2", "eur_per_built_m2", "bedrooms",
    "agency", "agent_phone",
    "first_seen", "last_seen", "listed_date", "days_on_market",
    "status", "rating", "dd_status", "flags", "notes",
]

LAND_TYPES = {"urban_land", "rustic_land", "tourism_land", "modular", "mobile_home"}
TERMINAL = {"sold", "rejected"}


def workspace() -> Path:
    return Path(os.environ.get("PROPERTY_WORKSPACE", Path.home() / "property-portugal"))


def paths(ws: Path) -> dict[str, Path]:
    return {
        "csv": ws / "listings.csv",
        "history": ws / "price_history.json",
        "notes": ws / "notes",
        "digests": ws / "digests",
        "state": ws / ".tracker_state.json",
    }


def today() -> str:
    return date.today().isoformat()


def load(ws: Path) -> list[dict]:
    p = paths(ws)["csv"]
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def save(ws: Path, rows: list[dict]) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    p = paths(ws)["csv"]
    tmp = p.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})
    tmp.replace(p)


def load_history(ws: Path) -> dict[str, list[dict]]:
    p = paths(ws)["history"]
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_history(ws: Path, hist: dict) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    paths(ws)["history"].write_text(
        json.dumps(hist, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_state(ws: Path) -> dict:
    p = paths(ws)["state"]
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(ws: Path, state: dict) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    paths(ws)["state"].write_text(json.dumps(state, indent=2), encoding="utf-8")


def scoped(rows: list[dict], search: str | None) -> list[dict]:
    """Limit rows to one search.

    Every statistic is scoped this way on purpose. A plot in the Algarve and a
    ruin in Alentejo pooled into one median produce a number that describes
    neither market — separate baselines are what make parallel searches work
    instead of quietly cancelling each other out.
    """
    if not search:
        return rows
    return [r for r in rows if (r.get("search") or "") == search]


def search_names(rows: list[dict]) -> list[str]:
    return sorted({r.get("search") or "" for r in rows} - {""})


def num(value, cast=float):
    if value in (None, "", "None"):
        return None
    try:
        return cast(float(value))
    except (TypeError, ValueError):
        return None


def make_id(item: dict) -> str:
    ref = item.get("source_ref") or ""
    if not ref:
        url = (item.get("url") or "").rstrip("/")
        ref = url.rsplit("/", 1)[-1] or str(abs(hash(item.get("title", ""))))[:8]
    return f"{item.get('source', 'unknown')}-{ref}"


def derive(row: dict) -> dict:
    price = num(row.get("price"))
    land = num(row.get("land_m2"))
    built = num(row.get("built_m2"))
    row["eur_per_land_m2"] = round(price / land, 2) if price and land else ""
    row["eur_per_built_m2"] = round(price / built, 2) if price and built else ""

    anchor = row.get("listed_date") or row.get("first_seen")
    if anchor:
        try:
            start = datetime.fromisoformat(str(anchor)).date()
            row["days_on_market"] = (date.today() - start).days
        except ValueError:
            pass
    return row


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_ingest(args, ws: Path) -> int:
    raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Input is not valid JSON: {exc}", file=sys.stderr)
        return 1
    if isinstance(items, dict):
        items = [items]

    rows = load(ws)
    index = {r["id"]: r for r in rows}
    hist = load_history(ws)
    stamp = today()
    new, dropped, raised, unchanged = [], [], [], 0

    for item in items:
        lid = item.get("id") or make_id(item)
        price = num(item.get("price"), int)
        existing = index.get(lid)

        if existing is None:
            row = {c: "" for c in COLUMNS}
            row.update({k: v for k, v in item.items() if k in COLUMNS})
            row.update({
                "id": lid,
                "price": price if price is not None else "",
                "first_price": price if price is not None else "",
                "first_seen": stamp,
                "last_seen": stamp,
                "status": "active",
                "rating": item.get("rating", 0),
                "dd_status": "none",
                "search": item.get("search") or args.search or "",
                "flags": ";".join(item.get("description_flags", []))
                         or item.get("flags", ""),
            })
            derive(row)
            rows.append(row)
            index[lid] = row
            if price is not None:
                hist.setdefault(lid, []).append({"date": stamp, "price": price})
            new.append(row)
            continue

        old_price = num(existing.get("price"), int)
        existing["last_seen"] = stamp
        if not existing.get("search") and (item.get("search") or args.search):
            existing["search"] = item.get("search") or args.search
        if existing.get("status") not in TERMINAL:
            existing["status"] = "active"
        # Refresh any field the scan learned that we did not have before.
        for key, value in item.items():
            if key in COLUMNS and key not in ("price", "first_price", "status") \
                    and value not in (None, "") and not existing.get(key):
                existing[key] = value

        if price is not None and old_price is not None and price != old_price:
            existing["price"] = price
            existing["status"] = "price_drop" if price < old_price else "price_rise"
            hist.setdefault(lid, []).append({"date": stamp, "price": price})
            (dropped if price < old_price else raised).append(
                (existing, old_price, price)
            )
        elif price is not None and old_price is None:
            existing["price"] = price
            hist.setdefault(lid, []).append({"date": stamp, "price": price})
        else:
            unchanged += 1
        derive(existing)

    for row in rows:
        derive(row)
    save(ws, rows)
    save_history(ws, hist)

    state = load_state(ws)
    state["last_ingest"] = stamp
    state["runs"] = state.get("runs", 0) + 1
    state.setdefault("started", stamp)
    save_state(ws, state)

    print(f"Ingested {len(items)} listing(s): {len(new)} new, {len(dropped)} price drop(s), "
          f"{len(raised)} price rise(s), {unchanged} unchanged. Total tracked: {len(rows)}.")
    for row in new:
        print(f"  + {row['id']}  {row.get('title', '')[:60]}  €{row.get('price')}")
    for row, old, cur in dropped:
        pct = round((cur - old) / old * 100, 1) if old else 0
        print(f"  ↓ {row['id']}  €{old} → €{cur} ({pct}%)")
    for row, old, cur in raised:
        print(f"  ↑ {row['id']}  €{old} → €{cur}")
    return 0


def cmd_sweep(args, ws: Path) -> int:
    """Anything not seen in this run's result pages is no longer listed."""
    if args.seen_file:
        seen = set(json.loads(Path(args.seen_file).read_text(encoding="utf-8")))
    else:
        seen = set(filter(None, (args.seen or "").split(",")))
    if not seen:
        print("No seen ids supplied — refusing to mark everything disappeared.",
              file=sys.stderr)
        return 1

    rows = load(ws)
    stamp = today()
    gone = []
    for row in rows:
        if row.get("status") in TERMINAL or row.get("status") == "disappeared":
            continue
        if args.source and row.get("source") != args.source:
            continue
        # A sweep only speaks for the search it ran. Without this, scanning one
        # search would mark every other search's listings as disappeared.
        if args.search and (row.get("search") or "") != args.search:
            continue
        if row["id"] in seen or row.get("source_ref") in seen:
            row["last_seen"] = stamp
            continue
        row["status"] = "disappeared"
        gone.append(row)
    save(ws, rows)

    print(f"{len(gone)} listing(s) no longer visible:")
    for row in gone:
        print(f"  - {row['id']}  {row.get('title','')[:50]}  €{row.get('price')} "
              f"after {row.get('days_on_market','?')} days")
    if gone:
        print("\nCheck whether any of these reappear under a new reference before "
              "recording them as sold — a relist at a higher price is the clearest "
              "sign of an unrealistic seller.")
    return 0


def _median(values):
    values = [v for v in values if v]
    return round(statistics.median(values), 2) if values else None


def _fmt(value):
    """Prices read better as integers; rates keep their cents."""
    if value is None:
        return "-"
    return f"{int(value):,}" if float(value).is_integer() else f"{value:,}"


def cmd_stats(args, ws: Path) -> int:
    rows = scoped([r for r in load(ws) if r.get("status") != "rejected"], args.search)
    if args.concelho:
        rows = [r for r in rows if r.get("concelho", "").lower() == args.concelho.lower()]
    if args.type:
        rows = [r for r in rows if r.get("property_type") == args.type]
    if not rows:
        print("No listings match that filter yet.")
        return 0

    by_type: dict[str, list[dict]] = {}
    for row in rows:
        by_type.setdefault(row.get("property_type") or "unknown", []).append(row)

    print(f"Zone statistics — {len(rows)} listing(s)"
          + (f" in search '{args.search}'" if args.search else "")
          + (f" in {args.concelho}" if args.concelho else "") + "\n")

    for ptype, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        land_type = ptype in LAND_TYPES
        key = "eur_per_land_m2" if land_type else "eur_per_built_m2"
        rates = [num(r.get(key)) for r in group]
        priced = [num(r.get("price")) for r in group]
        ages = [num(r.get("days_on_market"), int) for r in group]
        med = _median(rates)
        unit = "land m²" if land_type else "built m²"

        known_prices = [p for p in priced if p]
        print(f"## {ptype}  (n={len(group)})")
        print(f"   price:       median €{_fmt(_median(priced))}   "
              f"range €{_fmt(min(known_prices, default=None))}–"
              f"€{_fmt(max(known_prices, default=None))}")
        if med:
            known = [r for r in rates if r]
            print(f"   €/{unit}:   median €{med}   "
                  f"p25 €{round(statistics.quantiles(known, n=4)[0], 2) if len(known) > 3 else '-'}   "
                  f"p75 €{round(statistics.quantiles(known, n=4)[2], 2) if len(known) > 3 else '-'}   "
                  f"(n={len(known)})")
        else:
            print(f"   €/{unit}:   not computable — no areas recorded")

        # Ruins and quintas are land with a building on it; pricing them on one
        # area alone is how buyers talk themselves into overpaying.
        other_key = "eur_per_land_m2" if not land_type else "eur_per_built_m2"
        other_med = _median([num(r.get(other_key)) for r in group])
        if other_med:
            other_unit = "built m²" if land_type else "land m²"
            print(f"   €/{other_unit}:   median €{other_med}   (secondary view)")
        print(f"   days listed: median {_median(ages)}   "
              f"over 120 days: {sum(1 for a in ages if a and a > 120)}")

        if med:
            cheap = sorted(
                (r for r in group if num(r.get(key)) and num(r.get(key)) < med * 0.75),
                key=lambda r: num(r.get(key)),
            )
            if cheap:
                print("   ⚠ more than 25% below median — opportunity or hidden problem:")
                for row in cheap[:5]:
                    print(f"      {row['id']}  €{row.get('price')}  "
                          f"€{row.get(key)}/{'m² land' if land_type else 'm² built'}  "
                          f"{row.get('title','')[:45]}")
                    print(f"        {row.get('url','')}")
        missing = [r for r in group
                   if not num(r.get("land_m2")) and not num(r.get("built_m2"))]
        if missing:
            print(f"   {len(missing)} listing(s) have no area recorded and are "
                  f"excluded from the €/m² figures.")
        print()

    dupes = _duplicates(rows)
    if dupes:
        print("Possible duplicates (same area and concelho, price within 10%):")
        for a, b in dupes[:10]:
            print(f"  {a['id']} €{a.get('price')}  ≈  {b['id']} €{b.get('price')}  "
                  f"— {a.get('title','')[:40]}")
        print("  Compare the photographs before merging; duplicates skew every median.")
    return 0


def _duplicates(rows: list[dict]) -> list[tuple[dict, dict]]:
    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a.get("concelho") != b.get("concelho") or not a.get("concelho"):
                continue
            area_a = num(a.get("land_m2")) or num(a.get("built_m2"))
            area_b = num(b.get("land_m2")) or num(b.get("built_m2"))
            pa, pb = num(a.get("price")), num(b.get("price"))
            if not (area_a and area_b and pa and pb):
                continue
            if abs(area_a - area_b) / max(area_a, area_b) < 0.02 \
                    and abs(pa - pb) / max(pa, pb) < 0.10:
                pairs.append((a, b))
    return pairs


def cmd_digest(args, ws: Path) -> int:
    rows = scoped(load(ws), args.search)
    if not rows:
        if args.search:
            print(f"Nothing tracked yet in search '{args.search}'.")
        else:
            print("Nothing tracked yet. Run `ingest` first.")
        return 0
    hist = load_history(ws)
    state = load_state(ws)
    # Each search keeps its own "since" cursor, so scanning one search does not
    # silently consume the unread window of another.
    per_search = state.setdefault("searches", {}).setdefault(
        args.search or "_all", {})
    since = (args.since or per_search.get("last_digest")
             or state.get("last_digest") or state.get("started") or today())

    def after(value: str | None) -> bool:
        return bool(value) and str(value) >= since

    new = [r for r in rows if after(r.get("first_seen"))]
    changed = [r for r in rows if r.get("status") in ("price_drop", "price_rise")
               and after(r.get("last_seen"))]
    gone = [r for r in rows if r.get("status") == "disappeared" and after(r.get("last_seen"))]
    stale = [r for r in rows if r.get("status") == "active"
             and (num(r.get("days_on_market"), int) or 0) > 120]

    title = f"## Property digest — {today()}"
    if args.search:
        title += f" — {args.search}"
    lines = [title + f" (since {since})", ""]
    lines.append(f"**New {len(new)} · Changed {len(changed)} · Gone {len(gone)} · "
                 f"Tracked total {len(rows)}**")
    lines.append("")

    cohorts: dict[str, list[float]] = {}
    for row in rows:
        ptype = row.get("property_type") or "unknown"
        key = "eur_per_land_m2" if ptype in LAND_TYPES else "eur_per_built_m2"
        value = num(row.get(key))
        if value:
            cohorts.setdefault(ptype, []).append(value)
    # A "median" over one or two listings is not a market reading, so only
    # compare against cohorts big enough to mean something.
    medians = {k: statistics.median(v) for k, v in cohorts.items() if len(v) >= 4}

    if new:
        lines.append("### New")
        for row in sorted(new, key=lambda r: num(r.get("price")) or 0):
            ptype = row.get("property_type") or "unknown"
            key = "eur_per_land_m2" if ptype in LAND_TYPES else "eur_per_built_m2"
            rate, med = num(row.get(key)), medians.get(ptype)
            verdict = ""
            if rate and med:
                delta = round((rate - med) / med * 100)
                verdict = (" — at the zone median" if abs(delta) < 3 else
                           f" — {abs(delta)}% {'below' if delta < 0 else 'above'} zone median")
            elif rate:
                verdict = f" — too few comparables in {ptype} to place it yet"
            lines.append(f"- **{row.get('title','(untitled)')}** — €{row.get('price')} · "
                         f"{row.get('land_m2') or row.get('built_m2') or '?'} m² · "
                         f"€{rate or '?'}/m²{verdict}")
            lines.append(f"  {row.get('url','')}")
            if row.get("flags"):
                lines.append(f"  ⚠ {row['flags'].replace(';', ' · ')}")
        lines.append("")

    if changed:
        lines.append("### Price changes")
        for row in changed:
            entries = hist.get(row["id"], [])
            if len(entries) >= 2:
                old, cur = entries[-2]["price"], entries[-1]["price"]
                pct = round((cur - old) / old * 100, 1) if old else 0
                days = num(row.get("days_on_market"), int) or 0
                read = ("seller adjusting to market after a long wait — likely more room"
                        if days > 90 and abs(pct) < 10 else
                        "large early cut — the original price was probably fiction"
                        if days < 45 and abs(pct) >= 15 else "")
                lines.append(f"- **{row.get('title','')}** €{old} → €{cur} ({pct}%) "
                             f"after {days} days" + (f" · {read}" if read else ""))
                lines.append(f"  {row.get('url','')}")
        lines.append("")

    if gone:
        lines.append("### No longer listed")
        for row in gone:
            lines.append(f"- {row.get('title','')} — €{row.get('price')} after "
                         f"{row.get('days_on_market','?')} days · cause unconfirmed")
        lines.append("")

    if stale:
        lines.append(f"### Sitting over 120 days ({len(stale)}) — negotiation leverage")
        for row in sorted(stale, key=lambda r: -(num(r.get("days_on_market"), int) or 0))[:8]:
            lines.append(f"- {row.get('title','')} — €{row.get('price')} · "
                         f"{row.get('days_on_market')} days · "
                         f"€{row.get('first_price')} originally")
        lines.append("")

    if medians:
        lines.append("**Zone medians:** " + " · ".join(
            f"€{round(v)}/m² {k} (n={len(cohorts[k])})" for k, v in sorted(medians.items())))
    elif cohorts:
        lines.append("_Not enough listings in any one type yet for a reliable "
                     "median — keep going._")

    runs = state.get("runs", 0)
    lines.append("")
    lines.append(f"_Run {runs} · {len(rows)} listings tracked since "
                 f"{state.get('started', '?')}_")
    if 60 <= len(rows) <= 85:
        lines.append("")
        lines.append("You now have enough listings in this zone to price it yourself — "
                     "this is the point the daily habit was building towards.")

    text = "\n".join(lines)
    print(text)

    digests = paths(ws)["digests"]
    digests.mkdir(parents=True, exist_ok=True)
    stem = f"{today()}-{args.search}" if args.search else today()
    (digests / f"{stem}.md").write_text(text, encoding="utf-8")
    per_search["last_digest"] = today()
    state["last_digest"] = today()
    save_state(ws, state)
    return 0


def cmd_searches(args, ws: Path) -> int:
    """One line per search — what is tracked, and where the action is."""
    rows = load(ws)
    names = search_names(rows)
    unassigned = [r for r in rows if not r.get("search")]
    if not names and not unassigned:
        print("No searches tracked yet.")
        return 0

    for name in names:
        group = scoped(rows, name)
        active = [r for r in group if r.get("status") not in TERMINAL
                  and r.get("status") != "disappeared"]
        drops = [r for r in group if r.get("status") == "price_drop"]
        favs = [r for r in group if r.get("status") == "favourite"]
        stale = [r for r in active if (num(r.get("days_on_market"), int) or 0) > 120]
        concelhos = sorted({r.get("concelho") for r in group if r.get("concelho")})

        rates = {}
        for row in group:
            ptype = row.get("property_type") or "unknown"
            key = "eur_per_land_m2" if ptype in LAND_TYPES else "eur_per_built_m2"
            value = num(row.get(key))
            if value:
                rates.setdefault(ptype, []).append(value)

        print(f"## {name}  —  {len(group)} tracked, {len(active)} active")
        print(f"   zone: {', '.join(concelhos) or 'unset'}")
        for ptype, values in sorted(rates.items()):
            note = "" if len(values) >= 4 else "  (too few to be reliable)"
            print(f"   {ptype}: median €{round(statistics.median(values), 2)}/m² "
                  f"(n={len(values)}){note}")
        flags = []
        if drops:
            flags.append(f"{len(drops)} price drop(s)")
        if favs:
            flags.append(f"{len(favs)} favourite(s)")
        if stale:
            flags.append(f"{len(stale)} over 120 days")
        if flags:
            print(f"   → {' · '.join(flags)}")
        if len(group) < 60:
            print(f"   {60 - len(group)} more listings until this zone is readable "
                  f"from memory.")
        print()

    if unassigned:
        print(f"{len(unassigned)} listing(s) have no search assigned "
              f"(tracked before searches existed). Assign with "
              f"`set <id> --search <name>`.")
    return 0


def cmd_note(args, ws: Path) -> int:
    rows = load(ws)
    row = next((r for r in rows if r["id"] == args.id or r.get("source_ref") == args.id), None)
    if row is None:
        print(f"No tracked listing with id {args.id}", file=sys.stderr)
        return 1

    notes_dir = paths(ws)["notes"]
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_file = notes_dir / f"{row['id']}.md"
    header = "### Visit" if args.visit else "### Note"
    entry = f"\n{header} — {today()}\n\n{args.text}\n"
    with note_file.open("a", encoding="utf-8") as fh:
        if note_file.stat().st_size == 0:
            fh.write(f"# {row.get('title','')}\n\n{row.get('url','')}\n")
        fh.write(entry)

    if args.visit:
        state = load_state(ws)
        state["visits"] = state.get("visits", 0) + 1
        save_state(ws, state)
    row["notes"] = (row.get("notes", "") + " | " + args.text[:80]).strip(" |")
    save(ws, rows)
    print(f"Noted against {row['id']} → {note_file}")
    return 0


def cmd_set(args, ws: Path) -> int:
    rows = load(ws)
    row = next((r for r in rows if r["id"] == args.id or r.get("source_ref") == args.id), None)
    if row is None:
        print(f"No tracked listing with id {args.id}", file=sys.stderr)
        return 1
    for field in ("status", "rating", "dd_status", "search"):
        value = getattr(args, field)
        if value is not None:
            row[field] = value
    save(ws, rows)
    print(f"{row['id']}: status={row.get('status')} rating={row.get('rating')} "
          f"dd_status={row.get('dd_status')}")
    return 0


def cmd_export(args, ws: Path) -> int:
    rows = scoped(load(ws), args.search)
    if args.status:
        rows = [r for r in rows if r.get("status") == args.status]
    out = Path(args.xlsx or args.csv or "shortlist.csv")

    if args.xlsx:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
        except ImportError:
            print("openpyxl not installed (pip install openpyxl); writing CSV instead.",
                  file=sys.stderr)
            out = out.with_suffix(".csv")
        else:
            wb = Workbook()
            sheet = wb.active
            sheet.title = "Listings"
            sheet.append(COLUMNS)
            for cell in sheet[1]:
                cell.font = Font(bold=True)
            for row in rows:
                sheet.append([row.get(c, "") for c in COLUMNS])
            sheet.freeze_panes = "A2"
            for i, col in enumerate(COLUMNS, start=1):
                sheet.column_dimensions[sheet.cell(1, i).column_letter].width = \
                    max(10, min(38, len(col) + 6))
            wb.save(out)
            print(f"Wrote {len(rows)} listing(s) to {out}")
            return 0

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} listing(s) to {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=Path, default=None,
                    help="defaults to $PROPERTY_WORKSPACE or ~/property-portugal")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="record listings from a JSON array")
    p.add_argument("--file", help="JSON file; omit to read stdin")
    p.add_argument("--search", help="assign these listings to a named search")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("sweep", help="mark listings still live; flag the rest as gone")
    p.add_argument("--seen-file", help="JSON array of ids or source_refs seen this run")
    p.add_argument("--seen", help="comma-separated ids seen this run")
    p.add_argument("--source", help="limit the sweep to one portal")
    p.add_argument("--search", help="limit the sweep to one search (recommended — "
                                    "a sweep only speaks for the search it ran)")
    p.set_defaults(func=cmd_sweep)

    p = sub.add_parser("digest", help="what changed since the last run")
    p.add_argument("--since", help="ISO date; defaults to this search's last digest")
    p.add_argument("--search", help="digest one search only")
    p.set_defaults(func=cmd_digest)

    p = sub.add_parser("stats", help="zone medians, ages and outliers")
    p.add_argument("--type", help="filter by property_type")
    p.add_argument("--concelho", help="filter by municipality")
    p.add_argument("--search", help="scope the statistics to one search")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("searches", help="overview of every search being tracked")
    p.set_defaults(func=cmd_searches)

    p = sub.add_parser("note", help="attach a note or log a visit")
    p.add_argument("id")
    p.add_argument("--text", required=True)
    p.add_argument("--visit", action="store_true")
    p.set_defaults(func=cmd_note)

    p = sub.add_parser("set", help="update status / rating / dd_status")
    p.add_argument("id")
    p.add_argument("--status")
    p.add_argument("--rating")
    p.add_argument("--dd-status", dest="dd_status")
    p.add_argument("--search", help="move the listing to a named search")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("export", help="write a spreadsheet")
    p.add_argument("--xlsx")
    p.add_argument("--csv")
    p.add_argument("--status", help="export only listings with this status")
    p.add_argument("--search", help="export one search only")
    p.set_defaults(func=cmd_export)

    args = ap.parse_args()
    ws = args.workspace or workspace()
    return args.func(args, ws)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Piping into `head` closes the stream early; that is not an error.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        raise SystemExit(0)
