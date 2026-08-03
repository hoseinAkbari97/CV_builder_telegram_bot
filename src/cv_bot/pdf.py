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
from reportlab.platypus import Image as ReportLabImage

from cv_bot.i18n import text
from cv_bot.models import CV
from cv_bot.templates import TEMPLATES

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5F6B7A")
WHITE = colors.white
TEMPLATE_COLORS = {
    name: colors.HexColor(config["accent"]) for name, config in TEMPLATES.items()
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
    photo = _profile_photo(cv)
    if cv.template == "modern":
        identity = [name, title, contact]
        cells = [[photo, identity]] if photo else [["", identity]]
        table = Table(cells, colWidths=[31 * mm, 143 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if cv.template == "minimal":
        identity = [name, title, contact]
        table = Table(
            [["", photo or "", identity]],
            colWidths=[4 * mm, 29 * mm, 141 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (1, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if cv.template == "executive":
        identity = [name, title, Spacer(1, 2 * mm), contact]
        table = Table(
            [[photo or "", identity]],
            colWidths=[35 * mm, 139 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), accent),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F1F5F9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if cv.template == "creative":
        identity = [name, title, contact]
        table = Table(
            [[photo or "", identity]],
            colWidths=[33 * mm, 141 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 4 * mm)]
    if cv.template == "elegant":
        values: list[object] = []
        if photo:
            values.extend([photo, Spacer(1, 2 * mm)])
        values.extend([name, title, Spacer(1, 2 * mm), contact])
        return [
            Table([[values]], colWidths=[174 * mm], style=[("ALIGN", (0, 0), (-1, -1), "CENTER")]),
            Spacer(1, 2 * mm),
            HRFlowable(width="55%", thickness=1.2, color=accent, hAlign="CENTER"),
            Spacer(1, 4 * mm),
        ]
    if cv.template == "tech":
        identity = [name, title, contact]
        table = Table(
            [["", identity, photo or ""]],
            colWidths=[5 * mm, 139 * mm, 30 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), accent),
                    ("BACKGROUND", (1, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (1, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if cv.template == "compact":
        identity = [name, title]
        table = Table(
            [[identity, contact, photo or ""]],
            colWidths=[75 * mm, 72 * mm, 27 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [table, Spacer(1, 4 * mm)]
    if cv.template == "emerald":
        sidebar: list[object] = []
        if photo:
            sidebar.extend([photo, Spacer(1, 3 * mm)])
        sidebar.append(contact)
        identity = [name, title]
        table = Table(
            [[sidebar, identity]],
            colWidths=[54 * mm, 120 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), accent),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return [table, Spacer(1, 5 * mm)]
    if photo:
        table = Table(
            [[photo, [name, title, Spacer(1, 2 * mm), contact]]],
            colWidths=[32 * mm, 142 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [
            table,
            Spacer(1, 3 * mm),
            HRFlowable(width="100%", thickness=0.8, color=accent),
            Spacer(1, 4 * mm),
        ]
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
    if cv.template in {"classic", "compact", "elegant"}:
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


def _profile_photo(cv: CV) -> ReportLabImage | None:
    path = Path(cv.photo_path)
    if not cv.photo_path or not path.is_file():
        return None
    photo = ReportLabImage(str(path), width=25 * mm, height=25 * mm, kind="proportional")
    photo.hAlign = "CENTER"
    return photo


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
    header_on_accent = cv.template in {"modern", "creative", "compact", "emerald"}
    left_aligned = cv.template in {"minimal", "executive", "tech", "compact", "emerald"}
    header_alignment = TA_RIGHT if rtl else (TA_LEFT if left_aligned else TA_CENTER)
    section_background = accent if cv.template == "creative" else None
    section_text = WHITE if section_background else accent
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
            textColor=section_text,
            backColor=section_background,
            borderPadding=(3, 5, 3, 5) if section_background else 0,
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
