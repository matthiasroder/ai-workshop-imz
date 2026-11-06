"""Render a plain-text email draft as a The Mindshift letterhead PDF."""

import argparse
import re
from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

LOGO = Path(__file__).resolve().parents[1] / "assets" / "mindshift-halo.png"
INK = HexColor("#0a0f0d")
GREEN = HexColor("#4ade80")
MUTED = HexColor("#3e5148")
PALE_GREEN = HexColor("#dcfce7")
MARGIN = 58


def read_draft(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if (
        len(lines) < 4
        or not lines[0].startswith("**To** ")
        or not lines[1].startswith("**Subject** ")
        or lines[2].strip()
    ):
        raise ValueError("Expected **To** and **Subject** lines, then a blank line and the body.")
    recipient = lines[0].removeprefix("**To** ").strip()
    subject = lines[1].removeprefix("**Subject** ").strip()
    body = "\n".join(line.rstrip() for line in lines[3:]).strip()
    if not all((recipient, subject, body)):
        raise ValueError("The recipient, subject, and body must all have text.")
    return recipient, subject, body


def draw_letterhead(pdf, document):
    width, height = document.pagesize
    pdf.saveState()
    pdf.setFillColor(INK)
    pdf.rect(0, height - 107, width, 107, stroke=0, fill=1)
    pdf.setFillColor(GREEN)
    pdf.rect(0, height - 109.5, width, 2.5, stroke=0, fill=1)
    pdf.drawImage(str(LOGO), MARGIN, height - 77, 48, 48, mask="auto")

    x = MARGIN + 60
    pdf.setFont("Helvetica-Bold", 24)
    pdf.setFillColor(white)
    pdf.drawString(x, height - 62, "The")
    pdf.setFillColor(GREEN)
    pdf.drawString(x + pdf.stringWidth("The ", "Helvetica-Bold", 24), height - 62, "Mindshift")
    pdf.restoreState()


def render_draft(recipient, subject, body, output):
    # The default frame adds six points of padding inside each margin.
    document = SimpleDocTemplate(
        str(output), pagesize=A4, title=subject, author="The Mindshift",
        leftMargin=MARGIN - 6, rightMargin=MARGIN - 6, topMargin=137, bottomMargin=58,
    )
    subject_style = ParagraphStyle(
        "Subject", fontName="Helvetica-Bold", fontSize=31, leading=36,
        textColor=INK, spaceAfter=12, keepWithNext=True,
    )
    recipient_style = ParagraphStyle(
        "Recipient", fontName="Helvetica", fontSize=11, leading=14,
        textColor=INK, keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=13, leading=20,
        textColor=INK, spaceAfter=14,
    )
    story = [
        Paragraph(escape(subject), subject_style),
        Paragraph(f'<font color="{MUTED.hexval()}"><b>To</b></font>&nbsp;&nbsp;&nbsp;{escape(recipient)}', recipient_style),
        HRFlowable(width="100%", thickness=0.8, color=PALE_GREEN, spaceBefore=10),
        Spacer(1, 20),
    ]
    for block in re.split(r"\n[ \t]*\n+", body):
        story.append(Paragraph("<br/>".join(escape(line) for line in block.splitlines()), body_style))
    document.build(story, onFirstPage=draw_letterhead, onLaterPages=draw_letterhead)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".pdf" or args.output.resolve() == args.draft.resolve():
        parser.error("Specify a separate PDF output path.")
    try:
        recipient, subject, body = read_draft(args.draft)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    render_draft(recipient, subject, body, args.output)


if __name__ == "__main__":
    main()
