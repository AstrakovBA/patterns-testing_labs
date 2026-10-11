"""Rendering bridge between game entities and the Pygame drawing API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import pygame

Color = tuple[int, int, int]
Point = tuple[int, int]


class DrawingAPI(ABC):
    """Primitive drawing operations used by the game's visual abstractions."""

    @abstractmethod
    def circle(self, color: Color, center: Point, radius: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def rectangle(self, color: Color, rect: pygame.Rect, radius: int = 0, width: int = 0) -> None:
        raise NotImplementedError

    @abstractmethod
    def ellipse(self, color: Color, rect: pygame.Rect) -> None:
        raise NotImplementedError

    @abstractmethod
    def line(self, color: Color, start: Point, end: Point, width: int = 1) -> None:
        raise NotImplementedError

    @abstractmethod
    def polygon(self, color: Color, points: Sequence[Point]) -> None:
        raise NotImplementedError


class PygameDrawingAPI(DrawingAPI):
    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self._fonts: dict[int, pygame.font.Font] = {}

    def circle(self, color: Color, center: Point, radius: int) -> None:
        pygame.draw.circle(self.surface, color, center, radius)

    def rectangle(self, color: Color, rect: pygame.Rect, radius: int = 0, width: int = 0) -> None:
        pygame.draw.rect(self.surface, color, rect, width=width, border_radius=radius)

    def ellipse(self, color: Color, rect: pygame.Rect) -> None:
        pygame.draw.ellipse(self.surface, color, rect)

    def line(self, color: Color, start: Point, end: Point, width: int = 1) -> None:
        pygame.draw.line(self.surface, color, start, end, width)

    def polygon(self, color: Color, points: Sequence[Point]) -> None:
        pygame.draw.polygon(self.surface, color, points)

    def text(
        self,
        value: str,
        position: Point,
        size: int = 24,
        color: Color = (245, 245, 245),
        centered: bool = False,
    ) -> None:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        font = self._fonts[size]
        image = font.render(value, True, color)
        rect = image.get_rect(center=position) if centered else image.get_rect(topleft=position)
        self.surface.blit(image, rect)
