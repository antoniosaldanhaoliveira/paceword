# Portuguese property buyer agent

An agent and skill set that automate the workflow in *The Ultimate Guide for
Property Buyers in Portugal* (Find a Land) — the daily market research loop and
the per-property due-diligence gate.

## What's here

```
.claude/
├── agents/
│   └── property-scout-pt.md          the agent that runs the loop
├── commands/
│   ├── property-scan.md              /property-scan — today's sweep + digest
│   └── property-dd.md                /property-dd <url> — full due diligence
└── skills/
    ├── pt-property-market-scan/      guide steps 1–4, 6: strategy, alerts, study, visits
    ├── pt-property-tracker/          guide step 5: save, track, price history, digest
    └── pt-property-due-diligence/    property types, legal documents, red flags
```

## How the guide maps onto it

| Guide step | Automated by |
|---|---|
| 1. Define your strategy | `profile.yaml` — one or more named searches, each with type, anchor town + 15–20 km, purpose, budget |
| 2. Set up property alerts | `build_search_urls.py` generates saved-search URLs per search across 5 portals |
| 3. Study the market | `tracker.py stats --search X` — €/m² medians, quartiles, outliers |
| 4. Visit properties | `tracker.py note --visit` — visit log per property, agent network captured |
| 5. Save & track listings | `tracker.py ingest` / `sweep` — price history, days on market, disappearances |
| 6. Be consistent | `/property-scan` daily; the digest tracks the streak and milestones |
| Property type evaluation | `pt-property-due-diligence` — one reference file per type |
| Legal document checklist | `references/documents.md` — what each proves, what to cross-check |
| The 15 essentials tips | Folded into the skills where each one applies |

## Setup

```bash
# 1. Make the skills available outside this repo (optional)
bash .claude/install.sh

# 2. Point at the workspace and fill in the profile
export PROPERTY_WORKSPACE="$PWD/property-workspace"   # add to your shell profile
$EDITOR "$PROPERTY_WORKSPACE/profile.yaml"            # or run /property-scan and answer
```

### Where the data lives, and why it is in the repo

`property-workspace/` is committed. That is deliberate: scheduled runs happen in
ephemeral cloud containers, so a workspace under `~/` would be wiped between
runs and the tracker would restart from zero every morning — which destroys the
one thing the method depends on, the accumulated history.

Keeping it in git means the price history survives, and it doubles as a backup
and an audit trail of how the market moved.

If you run only locally and would rather keep the data out of the repo, set
`PROPERTY_WORKSPACE=~/property-portugal` instead and add `property-workspace/`
to `.gitignore`.

Optional: `pip install pyyaml openpyxl` — PyYAML for richer profile parsing (a
fallback parser handles the template without it), openpyxl for `export --xlsx`.

## Multiple searches

A profile holds any number of named searches, each with its own zone, property
types, budget and — critically — its own €/m² baseline:

```yaml
searches:
  - name: algarve-plots
    property_types: [urban_land]
    zone: {anchor: "São Brás de Alportel", radius_km: 20, concelhos: [...]}
    budget: {min: 50000, max: 200000}
  - name: alentejo-ruins
    property_types: [ruin, rustic_land]
    zone: {anchor: "Évora", radius_km: 20, concelhos: [...]}
    budget: {min: 20000, max: 120000}
  - name: porto-houses
    active: false        # paused, history kept
```

Every statistic is scoped by search. That is deliberate: a median pooling plots
near Loulé with ruins near Évora describes neither market, and would make every
"below market" judgement wrong in both.

The trade-off worth knowing: each search needs its own 60–80 tracked listings
before its numbers are trustworthy, so three searches is three times the runway,
not three times the coverage. Two or three active at once is realistic. Widening
one search's zone is the thing to avoid — add a second narrow search instead.

```bash
python .claude/skills/pt-property-tracker/scripts/tracker.py searches
```

shows every search's size, medians, and distance from that 60-listing mark.

## Daily use

```
/property-scan                      every active search — new listings, drops, digests
/property-scan algarve-plots        one search only
/property-scan searches             overview of all searches
/property-scan stats algarve-plots  zone statistics only
/property-dd <listing-url>          full due diligence on one property
```

Or address the agent directly: "run my property scan", "what changed in Alentejo
this week", "should I buy this plot: <url>".

## The data

Everything lives in `$PROPERTY_WORKSPACE` as plain files, so nothing is trapped:

```
property-workspace/
├── profile.yaml         buyer strategy
├── listings.csv         one row per property — opens in Excel
├── price_history.json   every observed price change
├── notes/               visit notes per property
├── digests/             dated digests, so you can look back
└── dd/                  due-diligence reports
```

## Scheduled runs

A Routine can fire `/property-scan` on a schedule in a fresh cloud session. Such
a run must, in order: pull the repo, export `PROPERTY_WORKSPACE` to
`property-workspace/`, run the scan, then **commit and push the workspace** —
otherwise the container is reclaimed and the day's data is lost.

The scheduled prompt also checks the profile first. An unfilled `profile.yaml`
means it runs the strategy setup rather than scanning a zone that doesn't exist,
so the schedule is safe to create before the profile is complete.

## Two deliberate constraints

**No bulk scraping.** Idealista and the other portals forbid automated harvesting
in their terms and block it quickly. The intake is what the guide itself
recommends: saved searches with daily email alerts, plus individual listing pages
fetched at human pace. The agent is built around that, not around evading it.

**No legal or technical conclusions.** The skills produce document checklists,
cross-checks and open questions. Buildability answers come from the PDM and a
PIP; building condition comes from a technical inspection; ownership comes from an
independent lawyer. The agent says which professional answers what, and says so
every time it matters.
