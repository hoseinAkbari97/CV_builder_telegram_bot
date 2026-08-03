from html import escape
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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

from cv_bot.i18n import text
from cv_bot.models import CV

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5F6B7A")
WHITE = colors.white
TEMPLATE_COLORS = {
    "modern": colors.HexColor("#2563EB"),
    "classic": colors.HexColor("#374151"),
    "minimal": colors.HexColor("#0F766E"),
}


def build_cv_pdf(cv: CV, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_unicode_font()
    accent = TEMPLATE_COLORS.get(cv.template, TEMPLATE_COLORS["modern"])
    styles = _styles(font_name, cv, accent)
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
    story = _header(cv, styles, accent)
    story.append(_section(text(cv.language, "profile").upper(), cv.summary, styles, cv))

    if cv.skills:
        story.extend(_skills(cv, styles, accent))
    if cv.experiences:
        story.append(_heading(text(cv.language, "experience_label").upper(), styles, cv))
        for experience in cv.experiences:
            role = _display(experience.role, cv)
            company = _display(experience.company, cv)
            dates = _display(experience.dates, cv)
            description = _display(experience.description, cv)
            header = (
                f"<b>{role}</b> · {company}"
                f"<br/><font color='#5F6B7A'>{dates}</font>"
            )
            story.extend(
                [
                    KeepTogether(
                        [
                            Paragraph(header, styles["item_heading"]),
                            Paragraph(description, styles["body"]),
                        ]
                    ),
                    Spacer(1, 3 * mm),
                ]
            )
    if cv.education:
        story.append(_heading(text(cv.language, "education_label").upper(), styles, cv))
        for education in cv.education:
            degree = _display(education.degree, cv)
            institution = _display(education.institution, cv)
            dates = _display(education.dates, cv)
            value = (
                f"<b>{degree}</b><br/>{institution}"
                f"<br/><font color='#5F6B7A'>{dates}</font>"
            )
            story.extend([Paragraph(value, styles["item_heading"]), Spacer(1, 3 * mm)])

    document.build(story)
    return output_path


def _header(
    cv: CV,
    styles: dict[str, ParagraphStyle],
    accent: colors.Color,
) -> list[object]:
    name = Paragraph(_display(cv.full_name, cv), styles["name"])
    title = Paragraph(_display(cv.professional_title, cv), styles["title"])
    contact = Paragraph(_contact_line(cv), styles["contact"])
    if cv.template == "modern":
        table = Table([[name], [title], [contact]], colWidths=[174 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 2), (-1, 2), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if cv.template == "minimal":
        table = Table(
            [["", name], ["", title], ["", contact]],
            colWidths=[4 * mm, 170 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (1, 0), (1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, 0), 5),
                    ("BOTTOMPADDING", (0, 2), (-1, 2), 5),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    return [
        name,
        title,
        Spacer(1, 2 * mm),
        contact,
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=0.8, color=accent),
        Spacer(1, 4 * mm),
    ]


def _skills(
    cv: CV,
    styles: dict[str, ParagraphStyle],
    accent: colors.Color,
) -> list[object]:
    cells = [Paragraph(_display(skill, cv), styles["skill"]) for skill in cv.skills]
    if cv.template == "classic":
        return [
            _heading(text(cv.language, "skills_label").upper(), styles, cv),
            Paragraph(_display(" • ".join(cv.skills), cv), styles["body"]),
            Spacer(1, 4 * mm),
        ]
    rows = [cells[index : index + 3] for index in range(0, len(cells), 3)]
    while rows and len(rows[-1]) < 3:
        rows[-1].append("")
    table = Table(rows, colWidths=[53 * mm] * 3, hAlign="RIGHT" if cv.language == "fa" else "LEFT")
    background = colors.Color(accent.red, accent.green, accent.blue, alpha=0.1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.4, WHITE),
                ("INNERGRID", (0, 0), (-1, -1), 1.5, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        _heading(text(cv.language, "skills_label").upper(), styles, cv),
        table,
        Spacer(1, 4 * mm),
    ]


def _contact_line(cv: CV) -> str:
    values = [cv.email, cv.phone, cv.location, cv.linkedin]
    displayed = [_display(value, cv) for value in values if value]
    return " &nbsp; • &nbsp; ".join(displayed)


def _heading(title: str, styles: dict[str, ParagraphStyle], cv: CV) -> Paragraph:
    return Paragraph(_display(title, cv), styles["section"])


def _section(
    title: str,
    body: str,
    styles: dict[str, ParagraphStyle],
    cv: CV,
) -> KeepTogether:
    return KeepTogether(
        [
            _heading(title, styles, cv),
            Paragraph(_display(body, cv).replace("\n", "<br/>"), styles["body"]),
            Spacer(1, 4 * mm),
        ]
    )


def _display(value: str, cv: CV) -> str:
    if cv.language == "fa":
        lines = [
            get_display(arabic_reshaper.reshape(line))
            for line in value.splitlines()
        ]
        value = "\n".join(lines)
    return escape(value)


def _register_unicode_font() -> str:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
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


def _styles(
    font_name: str,
    cv: CV,
    accent: colors.Color,
) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    rtl = cv.language == "fa"
    header_on_accent = cv.template == "modern"
    header_alignment = TA_RIGHT if rtl else (TA_LEFT if cv.template == "minimal" else TA_CENTER)
    return {
        "name": ParagraphStyle(
            "CVName",
            parent=base["Title"],
            fontName=font_name,
            fontSize=24,
            leading=29,
            textColor=WHITE if header_on_accent else INK,
            alignment=header_alignment,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "CVTitle",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=12,
            leading=16,
            textColor=WHITE if header_on_accent else accent,
            alignment=header_alignment,
        ),
        "contact": ParagraphStyle(
            "CVContact",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8.5,
            leading=12,
            textColor=WHITE if header_on_accent else MUTED,
            alignment=header_alignment,
        ),
        "section": ParagraphStyle(
            "CVSection",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=accent,
            alignment=TA_RIGHT if rtl else TA_LEFT,
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
            alignment=TA_RIGHT if rtl else TA_LEFT,
        ),
        "item_heading": ParagraphStyle(
            "CVItemHeading",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            textColor=INK,
            alignment=TA_RIGHT if rtl else TA_LEFT,
            spaceAfter=2,
        ),
        "skill": ParagraphStyle(
            "CVSkill",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8.5,
            leading=11,
            textColor=INK,
            alignment=TA_RIGHT if rtl else TA_LEFT,
        ),
    }
