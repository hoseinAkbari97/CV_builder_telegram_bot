from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

TEMPLATES = {
    "modern": {"en": "Modern", "fa": "مدرن", "accent": "#2563EB"},
    "classic": {"en": "Classic", "fa": "کلاسیک", "accent": "#374151"},
    "minimal": {"en": "Minimal", "fa": "مینیمال", "accent": "#0F766E"},
}


def template_name(template: str, language: str) -> str:
    value = TEMPLATES.get(template, TEMPLATES["modern"])
    return value["fa" if language == "fa" else "en"]


def build_template_thumbnail(template: str) -> BytesIO:
    config = TEMPLATES.get(template, TEMPLATES["modern"])
    image = Image.new("RGB", (720, 480), "#E5E7EB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    page = (175, 28, 545, 452)
    draw.rounded_rectangle(page, radius=4, fill="white")
    accent = config["accent"]

    if template == "modern":
        draw.rectangle((175, 28, 545, 112), fill=accent)
        draw.rectangle((202, 58, 342, 68), fill="white")
        draw.rectangle((202, 78, 292, 84), fill="#DBEAFE")
        content_left = 202
    elif template == "classic":
        draw.text((330, 50), "ALEX MORGAN", fill="#111827", font=font, anchor="mm")
        draw.line((215, 77, 505, 77), fill=accent, width=2)
        content_left = 215
    else:
        draw.rectangle((175, 28, 190, 452), fill=accent)
        draw.rectangle((215, 52, 355, 62), fill="#111827")
        draw.rectangle((215, 72, 305, 78), fill=accent)
        content_left = 215

    y = 130 if template == "modern" else 104
    for width in (90, 290, 260, 275, 90, 300, 285, 250, 90, 295, 270):
        height = 7 if width == 90 else 4
        color = accent if width == 90 else "#CBD5E1"
        draw.rectangle((content_left, y, content_left + width, y + height), fill=color)
        y += 22 if width == 90 else 13

    draw.text((360, 466), config["en"], fill="#374151", font=font, anchor="mm")
    output = BytesIO()
    image.save(output, "PNG")
    output.seek(0)
    output.name = f"{template}.png"
    return output
