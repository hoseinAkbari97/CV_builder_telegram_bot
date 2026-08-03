import json
from pathlib import Path

from cv_bot.models import CV


class CVStore:
    def __init__(self, data_dir: Path) -> None:
        self._directory = data_dir / "users"
        self._photo_directory = data_dir / "photos"
        self._directory.mkdir(parents=True, exist_ok=True)
        self._photo_directory.mkdir(parents=True, exist_ok=True)

    def load(self, user_id: int) -> CV:
        path = self._path(user_id)
        if not path.exists():
            return CV()
        try:
            return CV.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return CV()

    def save(self, user_id: int, cv: CV) -> None:
        path = self._path(user_id)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(cv.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary_path.replace(path)

    def delete(self, user_id: int) -> None:
        self._path(user_id).unlink(missing_ok=True)
        self._language_path(user_id).unlink(missing_ok=True)
        self.photo_path(user_id).unlink(missing_ok=True)
        self.draft_photo_path(user_id).unlink(missing_ok=True)

    def load_language(self, user_id: int) -> str:
        try:
            language = self._language_path(user_id).read_text(encoding="utf-8").strip()
        except OSError:
            return ""
        return language if language in {"en", "fa"} else ""

    def save_language(self, user_id: int, language: str) -> None:
        if language not in {"en", "fa"}:
            raise ValueError("Unsupported language")
        self._language_path(user_id).write_text(language, encoding="utf-8")

    def photo_path(self, user_id: int) -> Path:
        return self._photo_directory / f"{user_id}.jpg"

    def draft_photo_path(self, user_id: int) -> Path:
        return self._photo_directory / f"{user_id}-draft.jpg"

    def finalize_photo(self, user_id: int, has_photo: bool) -> str:
        final_path = self.photo_path(user_id)
        draft_path = self.draft_photo_path(user_id)
        if has_photo and draft_path.exists():
            draft_path.replace(final_path)
            return str(final_path)
        draft_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        return ""

    def discard_draft_photo(self, user_id: int) -> None:
        self.draft_photo_path(user_id).unlink(missing_ok=True)

    def _path(self, user_id: int) -> Path:
        return self._directory / f"{user_id}.json"

    def _language_path(self, user_id: int) -> Path:
        return self._directory / f"{user_id}.language"
