"""Persistent application settings."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GameSettings:
    sound_effects: bool = True
    difficulty: str = "normal"

    @property
    def player_health(self) -> int:
        return 2 if self.difficulty == "hard" else 3

    @property
    def damage_cooldown(self) -> float:
        return 0.65 if self.difficulty == "hard" else 1.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> GameSettings:
        sound_effects = data.get("sound_effects", True)
        difficulty = data.get("difficulty", "normal")
        return cls(
            sound_effects=sound_effects if isinstance(sound_effects, bool) else True,
            difficulty=difficulty if difficulty in ("normal", "hard") else "normal",
        )


class SettingsManager:
    """A process-wide settings store that persists changes as JSON."""

    _instance: SettingsManager | None = None

    def __new__(cls) -> SettingsManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        default_path = Path.home() / ".coin_collector" / "settings.json"
        self.path = Path(os.environ.get("COIN_COLLECTOR_SETTINGS", default_path))
        self.settings = self._load()
        self._initialized = True

    def _load(self) -> GameSettings:
        if not self.path.exists():
            return GameSettings()
        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Could not load settings from %s: %s", self.path, error)
            return GameSettings()
        if not isinstance(data, dict):
            logger.warning("Settings in %s must be a JSON object; using defaults", self.path)
            return GameSettings()
        return GameSettings.from_dict(data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(self.settings.to_dict(), file, ensure_ascii=False, indent=2)
            temporary_path.replace(self.path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise

    def toggle_sound(self) -> None:
        self.settings.sound_effects = not self.settings.sound_effects
        self.save()

    def toggle_difficulty(self) -> None:
        self.settings.difficulty = "hard" if self.settings.difficulty == "normal" else "normal"
        self.save()
