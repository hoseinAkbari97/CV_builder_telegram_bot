import pytest

from cv_bot.models import CV, parse_education, parse_experience


def test_cv_round_trip() -> None:
    cv = CV(
        language="fa",
        template="minimal",
        photo_path="/tmp/profile.jpg",
        full_name="Ada Lovelace",
        professional_title="Software Engineer",
        email="ada@example.com",
        summary="Builds thoughtful software.",
        skills=["Python", "Algorithms"],
        experiences=[
            parse_experience("Analytical Engines | Engineer | 1842–1843 | Wrote an algorithm")
        ],
        education=[parse_education("Self-directed | Mathematics | 1830–1840")],
    )

    assert CV.from_dict(cv.to_dict()) == cv
    assert cv.is_ready
    assert CV.from_dict({"full_name": "A"}).language == "en"
    assert CV.from_dict({"full_name": "A"}).template == "modern"
    assert CV.from_dict({"full_name": "A"}).photo_path == ""


def test_experience_requires_four_fields() -> None:
    with pytest.raises(ValueError, match="Company"):
        parse_experience("Company | Role")


def test_education_requires_three_fields() -> None:
    with pytest.raises(ValueError, match="Institution"):
        parse_education("University | Degree")
