"""Game entities and their renderer-independent visual behavior."""

from __future__ import annotations

import copy
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

import pygame

from coin_collector.input_adapter import InputFrame
from coin_collector.rendering import DrawingAPI


@dataclass(frozen=True)
class CoinStyle:
    shadow: tuple[int, int, int]
    fill: tuple[int, int, int]
    highlight: tuple[int, int, int]


class Collectible(Protocol):
    rect: pygame.Rect
    value: int

    def update(self, delta_time: float) -> None: ...

    def draw(self, drawing: DrawingAPI) -> None: ...


class GameObject(ABC):
    def __init__(self, position: tuple[int, int], size: tuple[int, int]) -> None:
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = position

    @abstractmethod
    def draw(self, drawing: DrawingAPI) -> None:
        raise NotImplementedError


class Player(GameObject):
    SIZE = (38, 46)
    COLOR = (79, 190, 255)

    def __init__(
        self,
        position: tuple[int, int],
        speed: float = 270.0,
        color: tuple[int, int, int] = COLOR,
    ) -> None:
        super().__init__(position, self.SIZE)
        self.speed = speed
        self.color = color
        self.animation_time = 0.0
        self.facing = 1
        self.health = 3
        self.damage_timer = 0.0

    def update(self, frame: InputFrame, delta_time: float, bounds: pygame.Rect) -> None:
        horizontal, vertical = frame.movement
        if horizontal and vertical:
            scale = math.sqrt(0.5)
            horizontal *= scale
            vertical *= scale
        self.rect.x += round(horizontal * self.speed * delta_time)
        self.rect.y += round(vertical * self.speed * delta_time)
        self.rect.clamp_ip(bounds)
        self.damage_timer = max(0.0, self.damage_timer - delta_time)
        if horizontal:
            self.facing = 1 if horizontal > 0 else -1
        if horizontal or vertical:
            self.animation_time += delta_time * 12

    def take_damage(self, cooldown: float) -> bool:
        if self.damage_timer > 0:
            return False
        self.health -= 1
        self.damage_timer = cooldown
        return True

    def draw(self, drawing: DrawingAPI) -> None:
        if self.damage_timer > 0 and int(self.damage_timer * 14) % 2 == 0:
            return
        bounce = round(math.sin(self.animation_time) * 3) if self.animation_time else 0
        body = self.rect.move(0, bounce)
        drawing.ellipse(self.color, body)
        shade = (
            max(0, self.color[0] - 18),
            max(0, self.color[1] - 18),
            max(0, self.color[2] - 18),
        )
        drawing.rectangle(
            shade,
            pygame.Rect(body.x + 3, body.y + 22, body.width - 6, 24),
            8,
        )
        eye_x = body.centerx + self.facing * 7
        drawing.circle((255, 255, 255), (eye_x, body.y + 16), 5)
        drawing.circle((24, 36, 62), (eye_x + self.facing, body.y + 16), 2)
        step = round(math.sin(self.animation_time) * 4) if self.animation_time else 0
        drawing.line((25, 50, 75), (body.centerx - 8, body.bottom - 1), (body.centerx - 8 - step, body.bottom + 5), 4)
        drawing.line((25, 50, 75), (body.centerx + 8, body.bottom - 1), (body.centerx + 8 + step, body.bottom + 5), 4)


class Coin(GameObject):
    SIZE = (30, 30)
    DEFAULT_STYLE = CoinStyle((229, 151, 36), (255, 205, 69), (255, 238, 156))

    def __init__(
        self,
        position: tuple[int, int],
        value: int = 10,
        style: CoinStyle = DEFAULT_STYLE,
    ) -> None:
        super().__init__(position, self.SIZE)
        self.value = value
        self.style = style
        self.animation_time = 0.0

    def clone_at(self, position: tuple[int, int]) -> Coin:
        clone = copy.copy(self)
        clone.rect = self.rect.copy()
        clone.rect.center = position
        clone.animation_time = 0.0
        return clone

    def update(self, delta_time: float) -> None:
        self.animation_time += delta_time

    def draw(self, drawing: DrawingAPI) -> None:
        width = max(6, round(22 * abs(math.cos(self.animation_time * 4))))
        coin = pygame.Rect(0, 0, width, 28)
        coin.center = self.rect.center
        drawing.ellipse(self.style.shadow, self.rect.inflate(4, 4))
        drawing.ellipse(self.style.fill, coin)
        if width > 12:
            drawing.line(
                self.style.highlight,
                (coin.centerx, coin.y + 6),
                (coin.centerx, coin.bottom - 6),
                2,
            )


class BonusCoin:
    """Decorate a coin with a higher value and a visible bonus ring."""

    def __init__(self, coin: Coin, multiplier: int = 2) -> None:
        if multiplier < 2:
            raise ValueError("A bonus coin multiplier must be at least 2")
        self._coin = coin
        self.value = coin.value * multiplier

    @property
    def rect(self) -> pygame.Rect:
        return self._coin.rect

    def update(self, delta_time: float) -> None:
        self._coin.update(delta_time)

    def draw(self, drawing: DrawingAPI) -> None:
        drawing.ellipse((110, 222, 255), self.rect.inflate(12, 12))
        self._coin.draw(drawing)


class Hazard(GameObject):
    SIZE = (48, 42)

    def __init__(self, position: tuple[int, int], size: tuple[int, int] = SIZE) -> None:
        super().__init__(position, size)

    def clone_at(self, position: tuple[int, int]) -> Hazard:
        clone = copy.copy(self)
        clone.rect = self.rect.copy()
        clone.rect.center = position
        return clone

    def draw(self, drawing: DrawingAPI) -> None:
        r = self.rect
        drawing.rectangle((196, 65, 84), r, 10)
        drawing.polygon((236, 104, 94), [(r.x + 5, r.y + 3), (r.x + 14, r.y - 8), (r.x + 22, r.y + 3)])
        drawing.polygon((236, 104, 94), [(r.right - 22, r.y + 3), (r.right - 14, r.y - 8), (r.right - 5, r.y + 3)])
        drawing.circle((255, 255, 255), (r.centerx - 9, r.centery - 2), 5)
        drawing.circle((255, 255, 255), (r.centerx + 9, r.centery - 2), 5)
        drawing.circle((56, 39, 51), (r.centerx - 8, r.centery - 1), 2)
        drawing.circle((56, 39, 51), (r.centerx + 10, r.centery - 1), 2)
        drawing.line((104, 43, 56), (r.centerx - 7, r.bottom - 9), (r.centerx + 7, r.bottom - 9), 2)
