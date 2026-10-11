"""Level data and a builder for assembling playable arenas."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from coin_collector.entities import Coin, Hazard, Player
from coin_collector.factory import GameObjectFactory, ObjectKind


@dataclass
class GameLevel:
    bounds: pygame.Rect
    player: Player
    coins: list[Coin]
    hazards: list[Hazard]


class GameLevelBuilder:
    def __init__(self, factory: GameObjectFactory, size: tuple[int, int]) -> None:
        self.factory = factory
        self.bounds = pygame.Rect(32, 82, size[0] - 64, size[1] - 114)
        self.player_start = self.bounds.center
        self._coins: list[tuple[int, int]] = []
        self._hazards: list[tuple[int, int]] = []

    def set_player_start(self, position: tuple[int, int]) -> GameLevelBuilder:
        self.player_start = position
        return self

    def add_coin(self, position: tuple[int, int]) -> GameLevelBuilder:
        self._coins.append(position)
        return self

    def add_hazard(self, position: tuple[int, int]) -> GameLevelBuilder:
        self._hazards.append(position)
        return self

    def build(self) -> GameLevel:
        if not self.bounds.collidepoint(self.player_start):
            raise ValueError("Player start must be inside the level bounds")
        if any(not self.bounds.collidepoint(point) for point in self._coins + self._hazards):
            raise ValueError("All level objects must be inside the level bounds")
        player = self.factory.create(ObjectKind.PLAYER, self.player_start)
        coins = [self.factory.create(ObjectKind.COIN, point) for point in self._coins]
        hazards = [self.factory.create(ObjectKind.HAZARD, point) for point in self._hazards]
        if not isinstance(player, Player):
            raise TypeError("The object factory must create a Player for ObjectKind.PLAYER")
        if any(not isinstance(coin, Coin) for coin in coins):
            raise TypeError("The object factory must create Coins for ObjectKind.COIN")
        if any(not isinstance(hazard, Hazard) for hazard in hazards):
            raise TypeError("The object factory must create Hazards for ObjectKind.HAZARD")
        objects = [player, *coins, *hazards]
        if any(not self.bounds.contains(obj.rect) for obj in objects):
            raise ValueError("All game object rectangles must fit inside the level bounds")
        return GameLevel(self.bounds.copy(), player, coins, hazards)


def build_default_level(factory: GameObjectFactory, size: tuple[int, int]) -> GameLevel:
    bounds = pygame.Rect(32, 82, size[0] - 64, size[1] - 114)
    builder = GameLevelBuilder(factory, size).set_player_start(bounds.center)
    coin_positions = [
        (bounds.left + 80, bounds.top + 74),
        (bounds.centerx, bounds.top + 56),
        (bounds.right - 80, bounds.top + 74),
        (bounds.left + 100, bounds.centery),
        (bounds.right - 100, bounds.centery),
        (bounds.left + 80, bounds.bottom - 70),
        (bounds.centerx, bounds.bottom - 55),
        (bounds.right - 80, bounds.bottom - 70),
    ]
    hazard_positions = [
        (bounds.centerx - 90, bounds.centery),
        (bounds.centerx + 90, bounds.centery),
        (bounds.centerx, bounds.top + 160),
        (bounds.centerx, bounds.bottom - 160),
    ]
    for position in coin_positions:
        builder.add_coin(position)
    for position in hazard_positions:
        builder.add_hazard(position)
    return builder.build()
