from cv_bot.models import CV, Education, Experience
from cv_bot.pdf import build_cv_pdf


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

