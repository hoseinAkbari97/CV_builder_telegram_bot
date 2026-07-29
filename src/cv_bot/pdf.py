from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cv_bot.models import CV

INK = colors.HexColor("#172033")
ACCENT = colors.HexColor("#2563EB")
MUTED = colors.HexColor("#5F6B7A")
PALE = colors.HexColor("#E8EEF8")


def build_cv_pdf(cv: CV, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_unicode_font()
    styles = _styles(font_name)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"{cv.full_name} - CV",
        author=cv.full_name,
    )
    story: list[object] = [
        Paragraph(escape(cv.full_name), styles["name"]),
        Paragraph(escape(cv.professional_title), styles["title"]),
        Spacer(1, 3 * mm),
        Paragraph(_contact_line(cv), styles["contact"]),
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=1.5, color=ACCENT),
        Spacer(1, 4 * mm),
        _section("PROFILE", cv.summary, styles),
    ]

    if cv.skills:
        skill_cells = [
            Paragraph(escape(skill), styles["skill"])
            for skill in cv.skills
        ]
        rows = [skill_cells[index : index + 3] for index in range(0, len(skill_cells), 3)]
        while rows and len(rows[-1]) < 3:
            rows[-1].append("")
        skills_table = Table(rows, colWidths=[53 * mm] * 3, hAlign="LEFT")
        skills_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE),
                    ("BOX", (0, 0), (-1, -1), 0.4, colors.white),
                    ("INNERGRID", (0, 0), (-1, -1), 1.5, colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([_heading("SKILLS", styles), skills_table, Spacer(1, 4 * mm)])

    if cv.experiences:
        story.append(_heading("EXPERIENCE", styles))
        for experience in cv.experiences:
            header = (
                f"<b>{escape(experience.role)}</b> · {escape(experience.company)}"
                f"<br/><font color='#5F6B7A'>{escape(experience.dates)}</font>"
            )
            story.extend(
                [
                    KeepTogether(
                        [
                            Paragraph(header, styles["item_heading"]),
                            Paragraph(escape(experience.description), styles["body"]),
                        ]
                    ),
                    Spacer(1, 3 * mm),
                ]
            )

    if cv.education:
        story.append(_heading("EDUCATION", styles))
        for education in cv.education:
            text = (
                f"<b>{escape(education.degree)}</b><br/>{escape(education.institution)}"
                f"<br/><font color='#5F6B7A'>{escape(education.dates)}</font>"
            )
            story.extend([Paragraph(text, styles["item_heading"]), Spacer(1, 3 * mm)])

    document.build(story)
    return output_path


def _contact_line(cv: CV) -> str:
    values = [cv.email, cv.phone, cv.location, cv.linkedin]
    return " &nbsp; • &nbsp; ".join(escape(value) for value in values if value)


def _heading(title: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(title, styles["section"])


def _section(
    title: str, body: str, styles: dict[str, ParagraphStyle]
) -> KeepTogether:
    return KeepTogether(
        [
            _heading(title, styles),
            Paragraph(escape(body).replace("\n", "<br/>"), styles["body"]),
            Spacer(1, 4 * mm),
        ]
    )


def _register_unicode_font() -> str:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            font_name = "CVUnicode"
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(candidate)))
                pdfmetrics.registerFontFamily(
                    font_name,
                    normal=font_name,
                    bold=font_name,
                    italic=font_name,
                    boldItalic=font_name,
                )
            return font_name
    return "Helvetica"


def _styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "CVName",
            parent=base["Title"],
            fontName=font_name,
            fontSize=24,
            leading=29,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "CVTitle",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=12,
            leading=16,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "contact": ParagraphStyle(
            "CVContact",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8.5,
            leading=12,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "CVSection",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=ACCENT,
            spaceBefore=2,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "CVBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            textColor=INK,
        ),
        "item_heading": ParagraphStyle(
            "CVItemHeading",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            textColor=INK,
            spaceAfter=2,
        ),
        "skill": ParagraphStyle(
            "CVSkill",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
    }
