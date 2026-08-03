from PIL import Image

from cv_bot.models import CV, Education, Experience
from cv_bot.pdf import build_cv_pdf
from cv_bot.templates import TEMPLATES


def test_build_cv_pdf(tmp_path) -> None:
    cv = CV(
        full_name="Ada Lovelace",
        professional_title="Software Engineer",
        email="ada@example.com",
        phone="+44 123 456",
        location="London, UK",
        summary="Creates reliable software and communicates complex ideas clearly.",
        skills=["Python", "Algorithms", "Technical Writing"],
        experiences=[
            Experience(
                company="Analytical Engines",
                role="Engineer",
                dates="1842–1843",
                description="Wrote the first published algorithm for a computing machine.",
            )
        ],
        education=[
            Education(
                institution="Self-directed",
                degree="Advanced Mathematics",
                dates="1830–1840",
            )
        ],
    )
    output = build_cv_pdf(cv, tmp_path / "cv.pdf")

    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1_000


def test_build_persian_pdf_for_each_template(tmp_path) -> None:
    photo_path = tmp_path / "profile.jpg"
    Image.new("RGB", (300, 400), "#CBD5E1").save(photo_path)
    for template in TEMPLATES:
        cv = CV(
            language="fa",
            template=template,
            photo_path=str(photo_path),
            full_name="سارا احمدی",
            professional_title="مهندس نرم‌افزار",
            email="sara@example.com",
            location="تهران، ایران",
            summary="توسعه‌دهنده نرم‌افزار با تمرکز بر سامانه‌های قابل اعتماد.",
            skills=["پایتون", "طراحی سامانه", "تحلیل داده"],
        )
        output = build_cv_pdf(cv, tmp_path / f"{template}.pdf")

        assert output.read_bytes().startswith(b"%PDF")
