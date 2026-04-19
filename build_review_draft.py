#!/usr/bin/env python3
"""
Build a review-draft PDF with photo thumbnails for each proposal section.

Reads the proposal markdown files and embeds up to 3 thumbnail photos
per section from the Pictures folders.

Requirements:
    pip install reportlab Pillow

Usage:
    python3 build_review_draft.py

Output:
    review-draft-with-photos.pdf
"""

import os
import tempfile
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black, gray
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICTURES_DIR = os.path.join(BASE_DIR, "Pictures")
OUTPUT_FILE = os.path.join(BASE_DIR, "review-draft-with-photos.pdf")

THUMB_W = 2.4 * inch
THUMB_H = 1.8 * inch

SECTIONS = [
    {
        "title": "Gazebo Installation Proposal",
        "folder": "Gazibo with Patio",
        "photos": ["885877.jpg", "885878.jpg", "885880.jpg"],
        "proposal": "GAZEBO_PROPOSAL.md",
    },
    {
        "title": "Fence with Gate Replacement Proposal",
        "folder": "Fence with Gate",
        "photos": ["885874.jpg", "885875.jpg", "885876.jpg"],
        "proposal": "FENCE_PROPOSAL.md",
    },
    {
        "title": "Walkway with Stone Blocks Proposal",
        "folder": "Walkway with stone blocks",
        "photos": ["885893.jpg", "885900.jpg", "885895.jpg"],
        "proposal": "WALKWAY_PROPOSAL.md",
    },
    {
        "title": "Tudor Style Trim Proposal",
        "folder": "Tutor style trim",
        "photos": [
            "885882.jpg",
            "Screenshot_20260416_182719_Edge~2.jpg",
            "Screenshot_20260416_182719_Edge~2[65].jpg",
        ],
        "proposal": "TUDOR_TRIM_PROPOSAL.md",
    },
    {
        "title": "Gutter with French Drain Proposal",
        "folder": "Gutter with french drain",
        "photos": ["885883.jpg", "885884.jpg", "885885.jpg"],
        "proposal": "GUTTER_DRAIN_PROPOSAL.md",
    },
    {
        "title": "Front Door Replacement Proposal",
        "folder": "Frontdoor",
        "photos": ["20260416_180601.jpg", "20260416_180603.jpg", "20260416_180550.jpg"],
        "proposal": "FRONTDOOR_PROPOSAL.md",
    },
]


def make_thumbnail(src_path, max_w=800, max_h=600):
    """Resize image to a reasonable size and save as temp JPEG."""
    img = Image.open(src_path)
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.convert("RGB").save(tmp.name, "JPEG", quality=80)
    return tmp.name


def build_styles():
    """Create all paragraph styles used in the PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "CoverDraft",
        parent=styles["Normal"],
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=gray,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "CoverDate",
        parent=styles["Normal"],
        fontSize=12,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=white,
        backColor=HexColor("#2c3e50"),
        borderPadding=(6, 8, 6, 8),
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=HexColor("#2c3e50"),
        spaceBefore=12,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "H4",
        parent=styles["Heading4"],
        fontSize=10,
        leading=13,
        spaceBefore=6,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "PhotoCaption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=gray,
        spaceBefore=2,
        spaceAfter=4,
    ))

    return styles


def build_photo_row(photo_paths):
    """Build a table flowable containing up to 3 thumbnail images."""
    from reportlab.platypus import Image as RLImage

    valid = [p for p in photo_paths if os.path.exists(p)]
    if not valid:
        return []

    tmp_files = []
    cells = []

    for photo_path in valid[:3]:
        tmp = make_thumbnail(photo_path)
        tmp_files.append(tmp)
        img = RLImage(tmp, width=THUMB_W, height=THUMB_H)
        cells.append(img)

    while len(cells) < 3:
        cells.append("")

    tbl = Table([cells], colWidths=[THUMB_W + 6] * 3)
    tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    return [tbl], tmp_files


def parse_and_render_proposal(proposal_path, styles):
    """Parse a markdown proposal and return a list of flowables."""
    flowables = []

    if not os.path.exists(proposal_path):
        flowables.append(Paragraph("<i>(Proposal file not found)</i>", styles["BodyText2"]))
        return flowables

    with open(proposal_path, "r") as f:
        lines = f.readlines()

    table_rows = []

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        parsed = []
        for row_line in table_rows:
            cells = [c.strip() for c in row_line.split("|")[1:-1]]
            if all(set(c) <= set("- :") for c in cells):
                continue
            parsed.append(cells)
        if parsed:
            col_count = max(len(r) for r in parsed)
            col_w = (7.0 * inch) / max(col_count, 1)
            for row in parsed:
                while len(row) < col_count:
                    row.append("")

            para_data = []
            for i, row in enumerate(parsed):
                style = styles["BodyText2"]
                if i == 0:
                    para_row = [Paragraph(f"<b>{c}</b>", style) for c in row]
                else:
                    para_row = [Paragraph(c, style) for c in row]
                para_data.append(para_row)

            tbl = Table(para_data, colWidths=[col_w] * col_count)
            tbl.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, gray),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#ecf0f1")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            flowables.append(tbl)
            flowables.append(Spacer(1, 6))
        table_rows = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue
        if stripped == "---":
            flush_table()
            continue
        if not stripped:
            flush_table()
            continue

        if stripped.startswith("|"):
            table_rows.append(stripped)
            continue

        flush_table()

        if stripped.startswith("## "):
            text = stripped[3:].strip()
            flowables.append(Paragraph(text, styles["H2"]))
        elif stripped.startswith("### "):
            text = stripped[4:].strip()
            flowables.append(Paragraph(text, styles["H3"]))
        elif stripped.startswith("#### "):
            text = stripped[5:].strip()
            flowables.append(Paragraph(text, styles["H4"]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:]
            text = text.replace("**", "<b>", 1).replace("**", "</b>", 1)
            flowables.append(Paragraph(f"\u2022  {text}", styles["BulletItem"]))
        else:
            text = stripped
            if text.startswith("**") and text.endswith("**"):
                text = f"<b>{text.strip('*')}</b>"
            else:
                text = text.replace("**", "<b>", 1).replace("**", "</b>", 1)
            flowables.append(Paragraph(text, styles["BodyText2"]))

    flush_table()
    return flowables


def main():
    print("Building review draft PDF with photo thumbnails...")

    styles = build_styles()
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )

    story = []
    all_tmp_files = []

    # Cover page
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("Elcy and Sam Sandora", styles["CoverTitle"]))
    story.append(Paragraph("Home Improvement Jobs", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Review Draft — Not for Distribution", styles["CoverDraft"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("April 2026", styles["CoverDate"]))
    story.append(PageBreak())

    for section in SECTIONS:
        print(f"  Adding: {section['title']}")

        # Section title
        story.append(Paragraph(section["title"], styles["SectionTitle"]))
        story.append(Spacer(1, 6))

        # Photo thumbnails
        photo_paths = []
        for photo in section["photos"]:
            path = os.path.join(PICTURES_DIR, section["folder"], photo)
            if os.path.exists(path):
                photo_paths.append(path)
            else:
                print(f"    Warning: {photo} not found in {section['folder']}")

        if photo_paths:
            story.append(Paragraph("Site Photos:", styles["PhotoCaption"]))
            row_flowables, tmp_files = build_photo_row(photo_paths)
            story.extend(row_flowables)
            all_tmp_files.extend(tmp_files)
            story.append(Spacer(1, 8))

        # Proposal content
        proposal_path = os.path.join(BASE_DIR, section["proposal"])
        content = parse_and_render_proposal(proposal_path, styles)
        story.extend(content)

        story.append(PageBreak())

    doc.build(story)

    # Clean up temp thumbnail files
    for tmp in all_tmp_files:
        if os.path.exists(tmp):
            os.remove(tmp)

    print(f"\nDone! Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
