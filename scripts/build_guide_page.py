#!/usr/bin/env python3
"""Render the US property buyer's guide as a standalone HTML page.

The guide is authored as Markdown so it stays readable and diffable in the
repo; this produces the published version. Run it again after editing the
Markdown — the design lives here, the content lives there.

    python3 scripts/build_guide_page.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = {
    "guide": (
        ROOT / "docs" / "us-property-buyers-guide.md",
        ROOT / "docs" / "us-property-buyers-guide.html",
        "Field guide · United States · Texas · Austin",
        "The Property Buyer's Guide to the United States",
        "Three parts — the national picture, then Texas, then Austin — written "
        "for a buyer who already knows how to run a Portuguese search. The "
        "method transfers. The facts underneath it do not.",
        "Research current as of July 2026. Every rate, threshold and deadline in "
        "this document changes — verify at purchase time.<br>Nothing here is "
        "legal or tax advice.",
    ),
    "hotel": (
        ROOT / "docs" / "austin-wellness-hotel-site-brief.md",
        ROOT / "docs" / "austin-wellness-hotel-site-brief.html",
        "Site brief · Boutique wellness hotel · West Austin",
        "West Austin wellness hotel — site search brief",
        "A ~50-key membership hotel-spa at $500+ ADR, within 25 minutes of "
        "downtown. The binding constraint is not price or availability. It is "
        "impervious cover.",
        "Research current as of July 2026. Verify every regulatory figure with "
        "the City of Austin before committing capital — these rules are "
        "site-specific and change.",
    ),
}

STYLE = """
<style>
  /* ---- tokens -------------------------------------------------------- */
  :root {
    --paper:      #F7F8F5;   /* drafting stock, faint green-grey bias      */
    --surface:    #FFFFFF;
    --sunk:       #EFF2EC;
    --ink:        #1A1F1C;
    --ink-soft:   #45504A;
    --muted:      #6B7370;
    --rule:       #DCE2DB;
    --rule-firm:  #C3CCC1;
    --accent:     #0F6E62;   /* the water layer of a topographic sheet     */
    --accent-dim: #0F6E6218;
    --caution:    #9C6B14;
    --caution-bg: #9C6B1412;

    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua",
             "URW Palladio L", Georgia, ui-serif, serif;
    --mono:  ui-monospace, "SF Mono", SFMono-Regular, "Cascadia Mono", Menlo,
             Consolas, "Liberation Mono", monospace;

    --measure: 68ch;
    --step-0: 1.0625rem;
    --step-1: 1.1875rem;
    --step-2: 1.5rem;
    --step-3: 2rem;
    --step-4: 2.75rem;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --paper:      #101413;
      --surface:    #161B19;
      --sunk:       #1B211E;
      --ink:        #E7EDE8;
      --ink-soft:   #B6C0B8;
      --muted:      #8A948C;
      --rule:       #2A312D;
      --rule-firm:  #3C453F;
      --accent:     #58C3B1;
      --accent-dim: #58C3B11F;
      --caution:    #D9A441;
      --caution-bg: #D9A4411A;
    }
  }

  /* The viewer's own toggle must win over the OS preference, both ways. */
  :root[data-theme="dark"] {
    --paper:      #101413;
    --surface:    #161B19;
    --sunk:       #1B211E;
    --ink:        #E7EDE8;
    --ink-soft:   #B6C0B8;
    --muted:      #8A948C;
    --rule:       #2A312D;
    --rule-firm:  #3C453F;
    --accent:     #58C3B1;
    --accent-dim: #58C3B11F;
    --caution:    #D9A441;
    --caution-bg: #D9A4411A;
  }
  :root[data-theme="light"] {
    --paper:      #F7F8F5;
    --surface:    #FFFFFF;
    --sunk:       #EFF2EC;
    --ink:        #1A1F1C;
    --ink-soft:   #45504A;
    --muted:      #6B7370;
    --rule:       #DCE2DB;
    --rule-firm:  #C3CCC1;
    --accent:     #0F6E62;
    --accent-dim: #0F6E6218;
    --caution:    #9C6B14;
    --caution-bg: #9C6B1412;
  }

  /* ---- frame --------------------------------------------------------- */
  html { scroll-behavior: smooth; }
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    * { animation: none !important; transition: none !important; }
  }

  body {
    background: var(--paper);
    color: var(--ink);
    font-family: var(--serif);
    font-size: var(--step-0);
    line-height: 1.62;
    -webkit-font-smoothing: antialiased;
  }

  .shell {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
    max-width: 1240px;
    margin: 0 auto;
    padding: 0 1.5rem 6rem;
  }
  @media (min-width: 1060px) {
    .shell { grid-template-columns: 15.5rem minmax(0, 1fr); gap: 4rem; }
  }

  /* ---- masthead ------------------------------------------------------ */
  .masthead {
    grid-column: 1 / -1;
    padding: 4.5rem 0 2rem;
    border-bottom: 2px solid var(--ink);
    display: grid;
    gap: 1.25rem 4rem;
    align-items: start;
  }
  @media (min-width: 1060px) {
    .masthead {
      grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
      column-gap: 5rem;
    }
    .masthead .eyebrow { grid-column: 1 / -1; }
    .masthead h1 { grid-row: 2; grid-column: 1; margin: 0; }
    .masthead .standfirst { grid-row: 2; grid-column: 2; align-self: end; }
    .masthead .stamp { grid-row: 3; grid-column: 2; }
  }
  .eyebrow {
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--accent);
  }
  .masthead h1 {
    font-size: var(--step-4);
    line-height: 1.06;
    font-weight: 600;
    letter-spacing: -0.02em;
    text-wrap: balance;
    max-width: 20ch;
  }
  .masthead .standfirst {
    font-size: var(--step-1);
    color: var(--ink-soft);
    max-width: 52ch;
    text-wrap: pretty;
  }
  .masthead .stamp {
    font-family: var(--mono);
    font-size: 0.72rem;
    line-height: 1.7;
    color: var(--muted);
    border-left: 2px solid var(--rule-firm);
    padding-left: 0.9rem;
    max-width: 60ch;
  }

  /* ---- index --------------------------------------------------------- */
  .index { display: none; }
  @media (min-width: 1060px) {
    .index {
      display: block;
      position: sticky;
      top: 0;
      align-self: start;
      max-height: 100vh;
      overflow-y: auto;
      padding: 2.25rem 0 3rem;
      font-family: var(--mono);
      font-size: 0.72rem;
      line-height: 1.5;
    }
  }
  .index h2 {
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 1rem;
  }
  .index ol { list-style: none; display: flex; flex-direction: column; gap: 0.1rem; }
  .index a {
    display: block;
    padding: 0.3rem 0.5rem 0.3rem 0;
    color: var(--ink-soft);
    text-decoration: none;
    border-left: 2px solid transparent;
    padding-left: 0.7rem;
  }
  .index a:hover { color: var(--accent); border-left-color: var(--accent); }
  .index li.part-row a {
    color: var(--ink);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-size: 0.66rem;
    margin-top: 1.1rem;
    border-left-color: var(--rule-firm);
  }

  /* ---- article ------------------------------------------------------- */
  .article { min-width: 0; padding-top: 2.25rem; }
  .article > * { max-width: var(--measure); }

  .article h1 {  /* part dividers */
    max-width: none;
    font-size: var(--step-3);
    font-weight: 600;
    letter-spacing: -0.015em;
    line-height: 1.1;
    margin: 5rem 0 2.5rem;
    padding: 1.5rem 0 1.25rem;
    border-top: 2px solid var(--ink);
    border-bottom: 1px solid var(--rule);
    text-wrap: balance;
  }
  .article h1:first-child { margin-top: 0; }

  .article h2 {
    font-size: var(--step-2);
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: -0.01em;
    margin: 3.25rem 0 1rem;
    text-wrap: balance;
  }
  .article h3 {
    font-family: var(--mono);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 2.25rem 0 0.75rem;
  }
  .article p { margin: 0 0 1.1rem; text-wrap: pretty; }
  .article a { color: var(--accent); text-underline-offset: 0.18em; }
  .article strong { font-weight: 600; }

  .article ul, .article ol { margin: 0 0 1.4rem; padding-left: 1.3rem; }
  .article li { margin-bottom: 0.5rem; padding-left: 0.2rem; }
  .article li::marker { color: var(--muted); font-family: var(--mono); font-size: 0.85em; }

  .article hr {
    max-width: none;
    border: 0;
    border-top: 1px solid var(--rule);
    margin: 3.5rem 0;
  }

  /* Notices — the ETJ warning and its kin */
  .article blockquote {
    max-width: var(--measure);
    margin: 1.75rem 0;
    padding: 1.15rem 1.35rem;
    background: var(--caution-bg);
    border-left: 3px solid var(--caution);
    border-radius: 2px;
  }
  .article blockquote p { margin-bottom: 0.7rem; }
  .article blockquote p:last-child { margin-bottom: 0; }
  .article blockquote strong { color: var(--caution); }

  .article code {
    font-family: var(--mono);
    font-size: 0.85em;
    background: var(--sunk);
    padding: 0.12em 0.38em;
    border-radius: 3px;
  }

  /* ---- tables -------------------------------------------------------- */
  .table-wrap {
    max-width: none;
    overflow-x: auto;
    margin: 1.75rem 0 2rem;
    border: 1px solid var(--rule);
    border-radius: 3px;
    background: var(--surface);
  }
  .article table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9rem;
    line-height: 1.45;
  }
  .article thead th {
    font-family: var(--mono);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-align: left;
    color: var(--muted);
    background: var(--sunk);
    padding: 0.7rem 0.95rem;
    border-bottom: 1px solid var(--rule-firm);
    white-space: nowrap;
  }
  .article tbody td {
    padding: 0.72rem 0.95rem;
    border-bottom: 1px solid var(--rule);
    vertical-align: top;
  }
  .article tbody tr:last-child td { border-bottom: 0; }
  .article tbody td:first-child { font-weight: 600; }
  /* Figures line up: any cell that is essentially numeric gets mono digits. */
  .article td.num, .article th.num {
    font-family: var(--mono);
    font-variant-numeric: tabular-nums;
    font-size: 0.82rem;
    white-space: nowrap;
  }

  /* ---- footer -------------------------------------------------------- */
  .colophon {
    grid-column: 1 / -1;
    margin-top: 5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--rule);
    font-family: var(--mono);
    font-size: 0.7rem;
    line-height: 1.7;
    color: var(--muted);
    max-width: 68ch;
  }

  :where(a, button):focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
    border-radius: 2px;
  }
</style>
"""

# A cell is "numeric" if its visible text is dominated by figures, currency,
# percentages or ranges — those are the ones that must line up in columns.
NUMERIC = re.compile(
    r"^[\s~≈+\-–—$€%.,0-9]*(?:[0-9][\s~≈+\-–—$€%.,0-9]*)"
    r"(?:months?|years?|acres?|ft²|k|M|/100|/yr)?[\s.]*$",
    re.I,
)


def numeric_cells(html_text: str) -> str:
    """Tag numeric table cells so they render with tabular figures."""

    def mark(match: re.Match) -> str:
        # group(2) is None when the cell carries no attributes at all — without
        # the fallback the f-string below writes the literal text "None" into
        # the tag name and quietly destroys the table.
        tag, attrs, body = match.group(1), match.group(2) or "", match.group(3)
        text = re.sub(r"<[^>]+>", "", body).strip()
        if text and NUMERIC.match(text) and any(ch.isdigit() for ch in text):
            return f'<{tag}{attrs} class="num">{body}</{tag}>'
        return match.group(0)

    return re.sub(r"<(td|th)(\s[^>]*)?>(.*?)</\1>", mark, html_text, flags=re.S)


def wrap_tables(html_text: str) -> str:
    """Every table scrolls inside its own container, never the page body."""
    return re.sub(
        r"<table>(.*?)</table>",
        lambda m: f'<div class="table-wrap"><table>{m.group(1)}</table></div>',
        html_text,
        flags=re.S,
    )


def build_index(html_text: str) -> tuple[str, str]:
    """Slug every h1/h2 and return (article_html, index_html)."""
    entries: list[tuple[str, str, str]] = []
    used: set[str] = set()

    def slug_for(text: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        return slug

    def anchor(match: re.Match) -> str:
        level, body = match.group(1), match.group(2)
        text = html.unescape(re.sub(r"<[^>]+>", "", body)).strip()
        slug = slug_for(text)
        entries.append((level, slug, text))
        return f'<h{level} id="{slug}">{body}</h{level}>'

    article = re.sub(r"<h([12])>(.*?)</h\1>", anchor, html_text, flags=re.S)

    rows = []
    for level, slug, text in entries:
        label = text if len(text) <= 46 else text[:44].rstrip(" ,—-") + "…"
        cls = ' class="part-row"' if level == "1" else ""
        rows.append(f'<li{cls}><a href="#{slug}">{html.escape(label)}</a></li>')

    index = (
        '<nav class="index" aria-label="Contents">'
        "<h2>Contents</h2><ol>" + "".join(rows) + "</ol></nav>"
    )
    return article, index


def render(key: str) -> None:
    source, output, eyebrow, title, standfirst, stamp = DOCS[key]
    text = source.read_text(encoding="utf-8")

    # The masthead is composed from the front matter, so drop the source's own
    # title block and let the styled header carry it.
    body_md = re.sub(r"^#[^\n]*\n", "", text, count=1)
    body_md = body_md.split("---", 1)[1].lstrip()

    rendered = markdown.markdown(
        body_md,
        extensions=["tables", "attr_list", "sane_lists", "smarty"],
        output_format="html5",
    )
    rendered = numeric_cells(rendered)
    rendered = wrap_tables(rendered)
    article, index = build_index(rendered)

    page = f"""<title>{html.escape(title)}</title>
{STYLE}
<div class="shell">
  <header class="masthead">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{html.escape(title)}</h1>
    <p class="standfirst">{standfirst}</p>
    <p class="stamp">{stamp}</p>
  </header>
  {index}
  <article class="article">
{article}
  </article>
  <footer class="colophon">
    Compiled from primary sources and market data, July 2026. Full source list
    at the end. Market figures move weekly; the structural facts — impervious
    cover caps, non-disclosure, the option period, ETJ status — move on their
    own schedule and are worth re-checking before you act on any of them.
  </footer>
</div>
"""
    output.write_text(page, encoding="utf-8")
    print(f"wrote {output.relative_to(ROOT)}  ({len(page):,} bytes)")


def main() -> int:
    for key in DOCS:
        render(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
