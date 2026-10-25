"""Level data and a builder for assembling playable arenas."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from coin_collector.entities import BonusCoin, Collectible, Coin, Hazard, Player
from coin_collector.factory import GameObjectFactory, ObjectKind


@dataclass
class GameLevel:
    bounds: pygame.Rect
    players: list[Player]
    coins: list[Collectible]
    hazards: list[Hazard]

    @property
    def player(self) -> Player:
        return self.players[0]


class GameLevelBuilder:
    def __init__(self, factory: GameObjectFactory, size: tuple[int, int]) -> None:
        self.factory = factory
        self.bounds = pygame.Rect(32, 82, size[0] - 64, size[1] - 114)
        self.player_starts = [self.bounds.center]
        self._coins: list[tuple[int, int]] = []
        self._bonus_coins: list[tuple[int, int]] = []
        self._hazards: list[tuple[int, int]] = []

    def set_player_start(self, position: tuple[int, int]) -> GameLevelBuilder:
        self.player_starts[0] = position
        return self

    def add_player_start(self, position: tuple[int, int]) -> GameLevelBuilder:
        self.player_starts.append(position)
        return self

    def add_coin(self, position: tuple[int, int]) -> GameLevelBuilder:
        self._coins.append(position)
        return self

    def add_bonus_coin(self, position: tuple[int, int]) -> GameLevelBuilder:
        self._bonus_coins.append(position)
        return self

    def add_hazard(self, position: tuple[int, int]) -> GameLevelBuilder:
        self._hazards.append(position)
        return self

    def build(self) -> GameLevel:
        all_positions = self.player_starts + self._coins + self._bonus_coins + self._hazards
        if any(not self.bounds.collidepoint(point) for point in all_positions):
            raise ValueError("All level objects must be inside the level bounds")
        players = [self.factory.create(ObjectKind.PLAYER, point) for point in self.player_starts]
        regular_coins = [
            self.factory.create(ObjectKind.COIN, point) for point in self._coins
        ]
        bonus_coins = [
            self.factory.create(ObjectKind.COIN, point) for point in self._bonus_coins
        ]
        hazards = [self.factory.create(ObjectKind.HAZARD, point) for point in self._hazards]
        if any(not isinstance(player, Player) for player in players):
            raise TypeError("The object factory must create Players for ObjectKind.PLAYER")
        if any(not isinstance(coin, Coin) for coin in regular_coins + bonus_coins):
            raise TypeError("The object factory must create Coins for ObjectKind.COIN")
        if any(not isinstance(hazard, Hazard) for hazard in hazards):
            raise TypeError("The object factory must create Hazards for ObjectKind.HAZARD")
        coins: list[Collectible] = [
            *regular_coins,
            *(BonusCoin(coin) for coin in bonus_coins),
        ]
        objects = [*players, *coins, *hazards]
        if any(not self.bounds.contains(obj.rect) for obj in objects):
            raise ValueError("All game object rectangles must fit inside the level bounds")
        return GameLevel(self.bounds.copy(), players, coins, hazards)


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


def build_two_player_level(factory: GameObjectFactory, size: tuple[int, int]) -> GameLevel:
    bounds = pygame.Rect(32, 82, size[0] - 64, size[1] - 114)
    builder = (
        GameLevelBuilder(factory, size)
        .set_player_start((bounds.left + 145, bounds.centery))
        .add_player_start((bounds.right - 145, bounds.centery))
    )
    coin_positions = [
        (bounds.left + 80, bounds.top + 70),
        (bounds.centerx, bounds.top + 70),
        (bounds.right - 80, bounds.top + 70),
        (bounds.left + 100, bounds.centery - 70),
        (bounds.right - 100, bounds.centery - 70),
        (bounds.left + 100, bounds.centery + 70),
        (bounds.right - 100, bounds.centery + 70),
        (bounds.left + 80, bounds.bottom - 70),
        (bounds.centerx, bounds.bottom - 70),
        (bounds.right - 80, bounds.bottom - 70),
    ]
    for position in coin_positions:
        builder.add_coin(position)
    builder.add_bonus_coin((bounds.centerx, bounds.centery))
    level = builder.build()
    level.players[1].color = (255, 139, 85)
    return level
