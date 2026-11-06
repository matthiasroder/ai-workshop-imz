---
name: sales-pipeline-follow-up
description: Find overdue leads in a workspace sales pipeline and draft follow-up emails. Use for last-contact checks, local Markdown drafts, or The Mindshift-branded PDFs of those drafts.
---

# Sales pipeline follow-up

1. Read the pipeline the user identifies. In this workshop, use `docs/example_contacts.csv`. Its `date` column records last contact. Use the CSV for this workshop's pipeline and treat the rows in its prompt examples as fixtures.
2. Use the requested cutoff or default to three calendar days. For date-only records, count today in the user's timezone as the most recent day in the window. A date before that window is due. For example, on November 5 the window is November 3–5, so November 2 is due. State the window used. Flag missing, invalid, or future dates separately. If the pipeline explicitly says a lead was never contacted, distinguish first outreach from follow-up.
3. Draft a short email for each due lead with a clear next step. Use only known context. A last-contact date alone gives no evidence of the channel, offer, prior discussion, or promises. Use the user's name for the sign-off when known. Show drafts in chat by default.
4. When files are requested, save one UTF-8 Markdown draft per lead in `outputs/` or the specified folder. Begin with `**To** recipient@example.com` and `**Subject** Following up` on separate lines, then a blank line and the plain-text body. Use distinct filenames when names collide. Keep this workflow draft-only.

## Branded PDF

When requested, use [render_mindshift_pdf.py](scripts/render_mindshift_pdf.py) to render the Markdown draft. Pass the input Markdown and output PDF paths. Use a Python runtime with ReportLab, available via the Codex workspace dependencies. The renderer uses the bundled Halo mark and the green and charcoal palette from The Mindshift website. Use a font that covers the draft's characters if the default font cannot render them.

Save the PDF next to its Markdown draft unless the user gives another destination. Render a preview and check the logo, line breaks, and completeness against the draft. Link the requested files in the reply.
