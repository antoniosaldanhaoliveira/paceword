---
description: Full due diligence on one property (Portugal or Texas) before visiting or offering
---

Run due diligence on the property in $ARGUMENTS (a listing URL, a tracker id, or
a description).

First determine the country — from the listing's `country` column in the tracker,
from its search, or from the URL's domain. Then use the matching skill:

- **Portugal** → **pt-property-due-diligence**. Classify the property type, read
  the matching reference file, assemble the document checklist, run the
  cross-checks between the caderneta, the certidão and the listing, and produce
  the report from the template.
- **Texas / United States** → **us-property-due-diligence**. Classify the
  property type, read the matching reference file, pull the parcel on TCAD,
  compute the real combined tax rate including any MUD, resolve flood status
  against both the Austin and FEMA maps, and — for land — settle water, septic
  and access before anything else.

Do not mix the two checklists. They share no law.

Save it to `$PROPERTY_WORKSPACE/dd/{id}.md` and update the listing's `dd_status`
in the tracker.

End with an unambiguous verdict — proceed, proceed with conditions, hold, or walk
away — and the specific open questions with who answers each.
