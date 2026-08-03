from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Experience:
    company: str
    role: str
    dates: str
    description: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Experience":
        return cls(
            company=str(value.get("company", "")),
            role=str(value.get("role", "")),
            dates=str(value.get("dates", "")),
            description=str(value.get("description", "")),
        )


@dataclass(slots=True)
class Education:
    institution: str
    degree: str
    dates: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Education":
        return cls(
            institution=str(value.get("institution", "")),
            degree=str(value.get("degree", "")),
            dates=str(value.get("dates", "")),
        )


@dataclass(slots=True)
class CV:
    language: str = "en"
    template: str = "modern"
    content_source: str = "static"
    photo_path: str = ""
    full_name: str = ""
    professional_title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experiences: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CV":
        return cls(
            language=str(value.get("language", "en")),
            template=str(value.get("template", "modern")),
            content_source=str(value.get("content_source", "static")),
            photo_path=str(value.get("photo_path", "")),
            full_name=str(value.get("full_name", "")),
            professional_title=str(value.get("professional_title", "")),
            email=str(value.get("email", "")),
            phone=str(value.get("phone", "")),
            location=str(value.get("location", "")),
            linkedin=str(value.get("linkedin", "")),
            summary=str(value.get("summary", "")),
            skills=[str(item) for item in value.get("skills", [])],
            experiences=[
                Experience.from_dict(item) for item in value.get("experiences", [])
            ],
            education=[Education.from_dict(item) for item in value.get("education", [])],
        )

    @property
    def is_ready(self) -> bool:
        return bool(self.full_name and self.professional_title and self.email and self.summary)


def parse_experience(value: str) -> Experience:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 4 or not all(parts):
        raise ValueError("Use: Company | Role | Dates | Achievement or responsibility")
    return Experience(company=parts[0], role=parts[1], dates=parts[2], description=parts[3])


def parse_education(value: str) -> Education:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 3 or not all(parts):
        raise ValueError("Use: Institution | Degree | Dates")
    return Education(institution=parts[0], degree=parts[1], dates=parts[2])
