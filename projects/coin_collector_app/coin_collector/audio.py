"""Semantic sound effects backed by Pygame's mixer."""

from __future__ import annotations

import array
import logging
import math

import pygame

logger = logging.getLogger(__name__)


class PygameSoundAdapter:
    """Turn game events into short generated Pygame sound effects."""

    SAMPLE_RATE = 22050

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] | None = None
        self._unavailable = False

    def play(self, effect: str) -> None:
        if self._unavailable:
            return
        try:
            self._initialize()
            sound = self._sounds.get(effect) if self._sounds else None
            if sound is None:
                raise ValueError(f"Unknown sound effect: {effect}")
            sound.play()
        except pygame.error as error:
            logger.warning("Sound effects are unavailable: %s", error)
            self._unavailable = True

    def _initialize(self) -> None:
        if self._sounds is not None:
            return
        pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1)
        self._sounds = {
            "coin": self._tone((880, 1175), 0.13),
            "hit": self._tone((220, 165), 0.22),
        }

    @classmethod
    def _tone(cls, frequencies: tuple[int, ...], duration: float) -> pygame.mixer.Sound:
        frames = int(cls.SAMPLE_RATE * duration)
        samples = array.array("h")
        for frame in range(frames):
            position = frame / cls.SAMPLE_RATE
            frequency = frequencies[min(len(frequencies) - 1, int(position / duration * len(frequencies)))]
            envelope = min(1.0, frame / 250, (frames - frame) / 800)
            sample = round(5000 * envelope * math.sin(2 * math.pi * frequency * position))
            samples.append(sample)
        return pygame.mixer.Sound(buffer=samples.tobytes())
