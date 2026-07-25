---
name: pt-property-due-diligence
description: Evaluate a specific Portuguese property before visiting, offering or signing — check its type-specific criteria (urban land, rustic land, house/apartment, ruin, tourism land, mobile or modular home), assemble the legal document checklist (Caderneta Predial, Certidão Permanente, Licença de Utilização, alvará, PIP), and surface the red flags that kill deals. Use this skill whenever the user is assessing, comparing or asking whether to buy a particular property in Portugal, asks what documents to request, mentions PDM, RAN, REN, PIP, loteamento, caderneta, certidão permanente, licença de utilização, alvará or viabilidade, asks whether land is buildable or whether a ruin can be rebuilt, asks what to check on a visit, or is about to sign a CPCV or make an offer.
---

# Portuguese Property Due Diligence

This skill exists because of one structural fact about the Portuguese market: the
information in a listing usually originates with the owner, passes through an
agent who has no duty and often no ability to verify it, and reaches the buyer as
a statement of fact. "Buildable", "with ruin", "1.2 hectares" are frequently
claims, not findings. Your job is to convert every claim into either a document
or an explicit open question.

The second structural fact matters just as much: **the tax registry and the
planning map disagree constantly.** Land registered as rústico at Finanças can
sit inside an urban zone on the municipal plan (in which case building is
allowed), and land registered as urbano can be caught by reserve constraints that
block construction entirely. The planning map (PDM) prevails. Never resolve a
buildability question from the caderneta alone.

## Workflow

### 1. Classify the property

Pick the path by what the property *is*, not what the listing hopes it becomes:

| Type | Reference to read |
|---|---|
| Urban land / plot | `references/urban-land.md` |
| Rustic land | `references/rustic-land.md` |
| House, apartment, quinta | `references/houses-apartments.md` |
| Ruin | `references/ruins.md` |
| Land for a tourism project | `references/tourism-land.md` |
| Mobile home / tiny house / modular | `references/mobile-modular.md` |

Read only the relevant file. If the property is genuinely two things — a ruin on
rustic land, which is the most common complicated case — read both, and treat
the rustic constraints as the binding ones.

### 2. Assemble the document set

`references/documents.md` lists every document, what it proves, where it comes
from, and the specific inconsistency to look for in each. Two are non-negotiable
for any property type:

- **Caderneta Predial** — the tax registration: what the state thinks this
  property is, its areas and its fiscal value.
- **Certidão Permanente do Registo Predial** — the legal registration: who owns
  it, and every mortgage, charge, easement or lien attached to it.

Requesting these early costs nothing and is the fastest way to end a bad deal
before anyone's time is spent. If a seller or agent resists producing them,
record that — it is itself a finding, and a common one.

### 3. Cross-check, because the discrepancies are the point

Run these comparisons explicitly. Each one has ended real purchases:

- **Caderneta area vs Certidão area vs listing area.** Three different numbers is
  routine. The registry governs ownership, the caderneta governs tax, and neither
  necessarily matches the fence line. A large mismatch means a rectification
  process before anything can be built or sold cleanly.
- **Registered buildings vs what is standing.** A ruin absent from the documents
  has no legal existence; a building in the documents that is no longer standing
  may or may not carry rebuild rights depending on the municipality.
- **Tax classification vs PDM classification.** As above — the PDM wins.
- **Owner on the certidão vs the person selling.** Inherited property with
  several heirs, an unresolved estate, or a usufruct held by a surviving spouse
  all mean the person showing you around may not be able to sell.
- **Charges section of the certidão.** Mortgages, seizures (penhoras), rights of
  way, pre-emption rights held by the municipality or by neighbouring
  landowners.

### 4. Answer the buildability question honestly

For any land, the buyer's real question is "what can I build here?" It resolves
in this order, and no earlier step substitutes for a later one:

1. PDM classification for that exact plot (municipal GIS or the Urbanismo desk)
2. Reserve overlays: RAN, REN, Natura 2000, coastal, forest or heritage zones
3. Construction indexes: implantação, área bruta de construção, number of floors,
   setbacks, road-widening cessions
4. Watercourses crossing the land — typically a 10 m buffer, or 5 m with APA
   consultation
5. Access: is there a legal, registered access to a public road?

Say plainly when the answer is "nobody can tell you without a PIP". The guide's
strongest procedural recommendation is exactly this: for ruins, rustic land and
tourism projects, sign a promissory contract (CPCV) **conditional on approval of
a Pedido de Informação Prévia**, so the buyer only completes if the municipality
confirms in writing what can be built. Verbal assurances at the Câmara counter
are helpful for orientation and are not binding — say so every time.

### 5. Produce the report

Use `assets/report-template.md`. Write it so someone can act on it: a
recommendation, then the findings, then the specific open questions with who
answers each. Save to `$PROPERTY_WORKSPACE/dd/{listing_id}.md` and update the
listing's `dd_status` via the tracker.

The verdict line should be one of four things, and it should be unambiguous:

- **Proceed** — nothing material outstanding
- **Proceed with conditions** — buy only with a CPCV conditional on X
- **Hold** — cannot assess until document Y is produced
- **Walk away** — a deal-breaker is confirmed

Where you are uncertain, be uncertain out loud with the specific reason. A buyer
who knows what is unresolved can decide; a buyer given false confidence cannot.

### 6. Cost the whole thing, not the asking price

The number that matters is price + acquisition costs + works, and for land the
third term is where budgets die. Include in every land report:

- IMT and stamp duty (rates change — verify at the time; rustic land is charged
  differently from urban)
- Notary, registration, and an independent lawyer
- Slope: steep ground raises construction cost sharply, which is why a cheap
  sloping plot often ends up the expensive option
- Infrastructure distance: bringing electricity to a remote ruin can cost tens of
  thousands, and this surprise is the one the guide singles out for ruins
- Architecture, engineering, licensing fees and the time they take

## Things to insist on, gently but repeatedly

These come from the guide's own tips list, and they are the advice buyers most
often skip and most often regret:

- **A technical inspection on any second-hand house.** It costs a few hundred
  euros, it tells you the truth about the roof and the wiring, and it is
  negotiating evidence.
- **Independent verification, not the agent's word.** The market is not
  professionally regulated; agents relay what sellers tell them.
- **Multiple contractor quotes.** Prices for identical work vary by around 30%.
- **A fixed-price contract with delay penalties** if the buyer is building.
- **Solar orientation.** South or west. Even in the Algarve a north-facing house
  is cold and dark, and it is permanent.
- **Time on market as leverage.** Something listed for a year is a negotiation,
  not a queue.

## Reference files

- `references/documents.md` — every document, what it proves, what to look for
- `references/urban-land.md` — plots: indexes, valuation factors, loteamentos
- `references/rustic-land.md` — the five paths to building, RAN/REN, minimum areas
- `references/houses-apartments.md` — legal status, structure, condominium, AL
- `references/ruins.md` — legal recognition, footprint rights, cost reality
- `references/tourism-land.md` — PDM tourism rules, feasibility, PIP
- `references/mobile-modular.md` — what is actually licensable, and what is a myth
- `assets/report-template.md` — the report format
