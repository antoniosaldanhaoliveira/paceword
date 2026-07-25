---
name: pt-property-tracker
description: Maintain the running record of Portuguese properties a buyer is watching — ingest listings, detect price drops, listing age and disappearances, compute €/m² statistics for a zone, log visits, and produce the daily or weekly digest. Use this skill whenever the user asks to save, track, log, compare or update properties or land they are considering, asks what changed since last time, asks how long something has been on the market, asks for price history or negotiation leverage on a listing, or wants their property shortlist as a spreadsheet. Also use it after any market scan, to record what the scan found.
---

# Portuguese Property Tracker

The tracker is what converts scattered browsing into market knowledge. Two months
of records answers the questions no single listing can: what is actually
expensive here, what sells in a week, what has been sitting since spring and is
therefore negotiable, and which "new" listing is really the same plot relisted by
a different agency at a different price.

Everything lives in one CSV plus a JSON price history, in
`$PROPERTY_WORKSPACE` (default `~/property-portugal/`). Plain files on purpose:
the user can open them in Excel or Numbers, and nothing is trapped in a tool.

## The script

`scripts/tracker.py` does the mechanical work. Use it rather than hand-editing
the CSV — it handles dedupe, price history and status transitions consistently.

```bash
# Record listings found by a scan (JSON array on stdin or --file)
python scripts/tracker.py ingest --file today.json

# What changed since the last run
python scripts/tracker.py digest
python scripts/tracker.py digest --since 2026-07-01

# Zone statistics: median €/m² by type, days on market, outliers
python scripts/tracker.py stats
python scripts/tracker.py stats --type urban_land --concelho "São Brás de Alportel"

# Mark listings still present this run; anything unseen becomes 'disappeared'
python scripts/tracker.py sweep --seen-file seen_ids.json

# Log a visit or free-text note against a tracked property
python scripts/tracker.py note <id> --visit --text "Agent says buildable; caderneta says rustic"

# Export to a spreadsheet for the user
python scripts/tracker.py export --xlsx shortlist.xlsx
```

Run `python scripts/tracker.py --help` for the full flag list. Field definitions
and status semantics are in `references/schema.md`.

## Reading the data, not just printing it

The commands produce numbers; the value is in what you say about them.

**A price drop is a signal about the seller, not the property.** A 5% cut after
90 days on market means the seller has accepted reality and there is likely more
room. A 20% cut in week two usually means the original price was fantasy and the
"discount" is against a number nobody would have paid. Always report a drop
alongside days-on-market and the zone median — the three together are a
negotiating position; the drop alone is marketing.

**Disappearance is ambiguous and worth chasing.** A listing that vanishes may
have sold, or the owner may have switched agency, or the agency's contract
expired. Sold-and-gone teaches you the real clearing price for that type; relisted
elsewhere at a higher price is the single clearest sign of an unrealistic seller.
When something disappears, check whether it reappears under a different reference
before recording it as sold.

**Long time on market is leverage, and the guide says so explicitly.** Flag
anything over 120 days in the digest. Rural land routinely sits for a year, which
is normal there and not a defect — compare against the zone's own median
listing age rather than an absolute threshold.

**Duplicates distort every average.** The same property listed by four agencies
counts once. The script flags likely duplicates on area + concelho + price
proximity, but it cannot see photographs — when it flags a pair, look at the
listings and merge or dismiss deliberately.

## The digest

Keep it short enough that the user actually reads it every day for two months —
that daily habit is the whole method, and a wall of text is what kills it.

```markdown
## {date} — {zone} — day {n} of tracking

**New {n} · Price drops {n} · Disappeared {n} · Tracked total {n}**

### New
- **{title}** — €{price} · {€/m²}/m² · {area} m² — {above/below} zone median by {x}%
  {url}
  {flag lines, if any}

### Changed
- **{title}** — €{old} → €{new} ({pct}%) after {days} days · {read on the seller}

### Gone
- **{title}** — listed {days} days at €{price} · {likely sold / relisted / withdrawn}

**Zone median:** €{x}/m² urban land (n={count}) · €{y}/m² houses (n={count})
{one line: what this run changed about your read of the area, or nothing}
```

When nothing happened, say so in one line. Manufacturing content on quiet days
trains the user to skim.

## When to escalate

Two triggers should interrupt the routine and get a direct recommendation:

- A listing lands more than ~25% below the zone median for its type with no
  visible reason. Either it is the opportunity the whole exercise exists to
  catch, or something is wrong that the listing is not saying. Both deserve
  same-day attention — send it to **pt-property-due-diligence** immediately.
- A property the user marked as a favourite drops in price. This is the moment
  the guide is training them for; surface it at the top of the digest.

## Milestones worth naming

Update `profile.yaml` `progress` each run. Tell the user when they hit ~60–80
tracked listings in one zone — that is the point where their own price instinct
becomes reliable, and it is motivating to hear that the tedious daily habit
worked.

## Reference files

- `references/schema.md` — CSV columns, status values, price-history format
