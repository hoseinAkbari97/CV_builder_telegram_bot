from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

TEMPLATES = {
    "modern": {
        "en": "Modern Blue",
        "fa": "مدرن آبی",
        "accent": "#2563EB",
        "layout": "banner",
    },
    "classic": {
        "en": "Classic",
        "fa": "کلاسیک",
        "accent": "#374151",
        "layout": "classic",
    },
    "minimal": {
        "en": "Minimal",
        "fa": "مینیمال",
        "accent": "#0F766E",
        "layout": "rail",
    },
    "executive": {
        "en": "Executive Navy",
        "fa": "مدیریتی سرمه‌ای",
        "accent": "#1E3A5F",
        "layout": "split",
    },
    "creative": {
        "en": "Creative Coral",
        "fa": "خلاق مرجانی",
        "accent": "#E05A47",
        "layout": "blocks",
    },
    "elegant": {
        "en": "Elegant Plum",
        "fa": "ظریف ارغوانی",
        "accent": "#7C3A6B",
        "layout": "centered",
    },
    "tech": {
        "en": "Tech Indigo",
        "fa": "فناوری نیلی",
        "accent": "#4338CA",
        "layout": "tech",
    },
    "compact": {
        "en": "Compact Slate",
        "fa": "فشرده خاکستری",
        "accent": "#475569",
        "layout": "compact",
    },
    "emerald": {
        "en": "Emerald",
        "fa": "زمردی",
        "accent": "#047857",
        "layout": "sidebar",
    },
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

    layout = config["layout"]
    if layout == "banner":
        draw.rectangle((175, 28, 545, 112), fill=accent)
        draw.rectangle((202, 58, 342, 68), fill="white")
        draw.rectangle((202, 78, 292, 84), fill="#DBEAFE")
        content_left = 202
    elif layout == "classic":
        draw.text((330, 50), "ALEX MORGAN", fill="#111827", font=font, anchor="mm")
        draw.line((215, 77, 505, 77), fill=accent, width=2)
        content_left = 215
    elif layout == "rail":
        draw.rectangle((175, 28, 190, 452), fill=accent)
        draw.rectangle((215, 52, 355, 62), fill="#111827")
        draw.rectangle((215, 72, 305, 78), fill=accent)
        content_left = 215
    elif layout == "split":
        draw.rectangle((175, 28, 545, 98), fill="#F8FAFC")
        draw.rectangle((175, 28, 300, 98), fill=accent)
        draw.ellipse((203, 45, 249, 91), fill="#CBD5E1")
        draw.rectangle((320, 50, 470, 60), fill="#111827")
        draw.rectangle((320, 70, 420, 76), fill=accent)
        content_left = 202
    elif layout == "blocks":
        draw.rectangle((175, 28, 545, 105), fill=accent)
        draw.ellipse((205, 48, 255, 98), fill="white")
        draw.rectangle((275, 53, 440, 64), fill="white")
        draw.rectangle((275, 76, 390, 82), fill="#FECACA")
        content_left = 202
    elif layout == "centered":
        draw.ellipse((315, 40, 365, 90), fill="#E2E8F0")
        draw.rectangle((280, 103, 400, 113), fill="#111827")
        draw.line((245, 127, 435, 127), fill=accent, width=2)
        content_left = 215
    elif layout == "tech":
        draw.rectangle((175, 28, 545, 104), fill="#EEF2FF")
        draw.rectangle((175, 28, 185, 104), fill=accent)
        draw.rectangle((210, 48, 400, 59), fill="#1E1B4B")
        draw.rectangle((210, 73, 340, 80), fill=accent)
        content_left = 202
    elif layout == "compact":
        draw.rectangle((175, 28, 545, 78), fill=accent)
        draw.rectangle((196, 45, 340, 54), fill="white")
        draw.rectangle((410, 45, 520, 51), fill="#CBD5E1")
        content_left = 202
    else:
        draw.rectangle((175, 28, 285, 452), fill=accent)
        draw.ellipse((205, 52, 255, 102), fill="white")
        draw.rectangle((195, 125, 265, 132), fill="#D1FAE5")
        draw.rectangle((310, 52, 465, 63), fill="#111827")
        draw.rectangle((310, 78, 410, 84), fill=accent)
        content_left = 310

    y = 130 if layout in {"banner", "blocks"} else 145 if layout == "centered" else 104
    widths = (
        (80, 205, 190, 200, 80, 210, 195, 185, 80, 205, 190)
        if layout == "sidebar"
        else (90, 290, 260, 275, 90, 300, 285, 250, 90, 295, 270)
    )
    for width in widths:
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
