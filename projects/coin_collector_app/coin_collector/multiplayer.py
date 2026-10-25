"""Composite players and the two-player match facade."""

from __future__ import annotations

import pygame

from coin_collector.entities import Collectible, Player
from coin_collector.input_adapter import InputFrame
from coin_collector.level import GameLevel
from coin_collector.rendering import DrawingAPI


class PlayerComposite:
    """Apply shared game operations to all players in a match."""

    def __init__(self, players: list[Player]) -> None:
        if not players:
            raise ValueError("A player composite must contain at least one player")
        self.players = tuple(players)

    def update(
        self,
        frames: tuple[InputFrame, ...],
        delta_time: float,
        bounds: pygame.Rect,
    ) -> None:
        if len(frames) != len(self.players):
            raise ValueError("Each player must have exactly one input frame")
        for player, frame in zip(self.players, frames):
            player.update(frame, delta_time, bounds)

    def draw(self, drawing: DrawingAPI) -> None:
        for player in self.players:
            player.draw(drawing)


class TwoPlayerMatch:
    """Facade coordinating movement, coin collection, scoring, and the result."""

    def __init__(self, level: GameLevel) -> None:
        if len(level.players) != 2:
            raise ValueError("A two-player match requires exactly two players")
        self.level = level
        self.players = PlayerComposite(level.players)
        self.coin_counts = [0, 0]
        self.scores = [0, 0]
        self.finished = False

    def update(
        self,
        player_one: InputFrame,
        player_two: InputFrame,
        delta_time: float,
    ) -> int:
        if self.finished:
            return 0
        self.players.update(
            (player_one, player_two),
            delta_time,
            self.level.bounds,
        )
        for coin in self.level.coins:
            coin.update(delta_time)
        collected = 0
        remaining: list[Collectible] = []
        for coin in self.level.coins:
            collector = next(
                (
                    index
                    for index, player in enumerate(self.players.players)
                    if player.rect.colliderect(coin.rect)
                ),
                None,
            )
            if collector is None:
                remaining.append(coin)
            else:
                self.coin_counts[collector] += 1
                self.scores[collector] += coin.value
                collected += 1
        self.level.coins = remaining
        self.finished = not remaining
        return collected

    @property
    def result_message(self) -> str:
        if not self.finished:
            raise RuntimeError("The match result is not available before the match ends")
        if self.coin_counts[0] == self.coin_counts[1]:
            return "Ничья!"
        winner = 1 if self.coin_counts[0] > self.coin_counts[1] else 2
        return f"Игрок {winner} победил!"
