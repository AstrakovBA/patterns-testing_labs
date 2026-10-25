"""Factory-method creation of game objects, using reusable prototypes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from coin_collector.entities import Coin, CoinStyle, GameObject, Hazard, Player


class ObjectKind(Enum):
    PLAYER = "player"
    COIN = "coin"
    HAZARD = "hazard"


class GameObjectFactory(ABC):
    @abstractmethod
    def create(self, kind: ObjectKind, position: tuple[int, int]) -> GameObject:
        """Factory method implemented by concrete game modes."""
        raise NotImplementedError


class CoinStyleFactory:
    """Flyweight factory for immutable visual data shared by coin instances."""

    _styles: dict[str, CoinStyle] = {"gold": Coin.DEFAULT_STYLE}

    @classmethod
    def get(cls, name: str) -> CoinStyle:
        try:
            return cls._styles[name]
        except KeyError as error:
            raise ValueError(f"Unsupported coin style: {name!r}") from error


class ArcadeObjectFactory(GameObjectFactory):
    def __init__(self) -> None:
        self._coin_style = CoinStyleFactory.get("gold")
        self._coin_prototype = Coin((0, 0), style=self._coin_style)
        self._hazard_prototype = Hazard((0, 0))

    def create(self, kind: ObjectKind, position: tuple[int, int]) -> GameObject:
        if kind is ObjectKind.PLAYER:
            return Player(position)
        if kind is ObjectKind.COIN:
            return self._coin_prototype.clone_at(position)
        if kind is ObjectKind.HAZARD:
            return self._hazard_prototype.clone_at(position)
        raise ValueError(f"Unsupported game object kind: {kind!r}")
