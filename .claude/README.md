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
| 1. Define your strategy | `profile.yaml` — type, anchor town + 15–20 km, purpose, budget |
| 2. Set up property alerts | `build_search_urls.py` generates saved-search URLs for 5 portals |
| 3. Study the market | `tracker.py stats` — €/m² medians, quartiles, outliers by type and concelho |
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

# 2. Choose where the buyer's data lives
export PROPERTY_WORKSPACE=~/property-portugal      # add to your shell profile
mkdir -p "$PROPERTY_WORKSPACE"
cp .claude/skills/pt-property-market-scan/references/profile-template.yaml \
   "$PROPERTY_WORKSPACE/profile.yaml"

# 3. Fill in the profile — or just run /property-scan and answer the questions
```

Optional: `pip install pyyaml openpyxl` — PyYAML for richer profile parsing (a
fallback parser handles the template without it), openpyxl for `export --xlsx`.

## Daily use

```
/property-scan                      today's new listings, price drops, digest
/property-scan stats                zone statistics only
/property-dd <listing-url>          full due diligence on one property
```

Or address the agent directly: "run my property scan", "what changed this week",
"should I buy this plot: <url>".

## The data

Everything lives in `$PROPERTY_WORKSPACE` as plain files, so nothing is trapped:

```
property-portugal/
├── profile.yaml         buyer strategy
├── listings.csv         one row per property — opens in Excel
├── price_history.json   every observed price change
├── notes/               visit notes per property
├── digests/             dated digests, so you can look back
└── dd/                  due-diligence reports
```

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
