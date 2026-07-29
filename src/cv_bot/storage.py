import json
from pathlib import Path

from cv_bot.models import CV


class CVStore:
    def __init__(self, data_dir: Path) -> None:
        self._directory = data_dir / "users"
        self._directory.mkdir(parents=True, exist_ok=True)

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

    def _path(self, user_id: int) -> Path:
        return self._directory / f"{user_id}.json"

