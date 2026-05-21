"""
PDF report generation for the column buckling calculator.

Requires:
    pip install reportlab

This module intentionally contains no Streamlit code.
It receives prepared rows/values from app.py and returns PDF bytes.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


RowList = Iterable[tuple[str, str]]


def _clean_text(value: object) -> str:
    """Make text safer for ReportLab built-in fonts.

    ReportLab's default fonts can have problems with some Unicode symbols.
    This keeps the first PDF version robust.
    """
    text = str(value)
    replacements = {
        "²": "^2",
        "³": "^3",
        "⁴": "^4",
        "λ": "lambda",
        "σ": "sigma",
        "χ": "chi",
        "α": "alpha",
        "≤": "<=",
        "≥": ">=",
        "–": "-",
        "—": "-",
        "×": "x",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _make_table(rows: RowList, column_widths: list[float] | None = None) -> Table:
    data = [[_clean_text(label), _clean_text(value)] for label, value in rows]

    if column_widths is None:
        column_widths = [95 * mm, 70 * mm]

    table = Table(data, colWidths=column_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _figure_to_image_flowable(fig, width: float = 165 * mm) -> Image:
    image_buffer = BytesIO()
    fig.savefig(image_buffer, format="png", dpi=180, bbox_inches="tight")
    image_buffer.seek(0)

    image = Image(image_buffer)
    image.drawWidth = width
    image.drawHeight = width * image.imageHeight / image.imageWidth
    return image


def create_pdf_report(
    *,
    input_summary_rows: RowList,
    main_result_rows: RowList,
    detail_rows: RowList,
    design_check_message: str,
    buckling_curve_fig,
    project_title: str = "Column Buckling Report",
) -> bytes:
    """Create a PDF report and return it as bytes."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story = []

    story.append(Paragraph(_clean_text(project_title), title_style))
    story.append(Paragraph(_clean_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), normal_style))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Input summary", heading_style))
    story.append(_make_table(input_summary_rows))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Main results", heading_style))
    story.append(_make_table(main_result_rows))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Detailed buckling values", heading_style))
    story.append(_make_table(detail_rows))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Buckling curve", heading_style))
    story.append(_figure_to_image_flowable(buckling_curve_fig))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Design check summary", heading_style))
    story.append(Paragraph(_clean_text(design_check_message), normal_style))
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Notes", heading_style))
    story.append(
        Paragraph(
            _clean_text(
                "This report is generated from the entered data and the selected buckling curve factor. "
                "The user is responsible for verifying profile data, boundary conditions, imperfection factor, "
                "and applicability of the selected design standard. This calculator currently covers axial "
                "compression buckling only. If bending moment is expected, a combined compression + bending "
                "check is required."
            ),
            normal_style,
        )
    )

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
