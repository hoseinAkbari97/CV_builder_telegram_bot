from cv_bot.templates import TEMPLATES, build_template_thumbnail


def test_each_template_has_a_png_thumbnail() -> None:
    for template in TEMPLATES:
        thumbnail = build_template_thumbnail(template)

        assert thumbnail.read(8) == b"\x89PNG\r\n\x1a\n"
