"""Translate Pygame events and keys to the game's input interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from typing import Protocol

import pygame


@dataclass(frozen=True)
class InputFrame:
    movement: tuple[int, int] = (0, 0)
    pressed: frozenset[str] = frozenset()
    quit_requested: bool = False


class KeyState(Protocol):
    def __getitem__(self, key: int) -> bool: ...


class PygameInputAdapter:
    """Adapt Pygame's key/event representation to named game actions."""

    def read(self, events: Iterable[pygame.event.Event], keys: KeyState) -> InputFrame:
        pressed: set[str] = set()
        quit_requested = False
        actions = {
            pygame.K_RETURN: "confirm",
            pygame.K_SPACE: "confirm",
            pygame.K_ESCAPE: "back",
            pygame.K_UP: "up",
            pygame.K_w: "up",
            pygame.K_DOWN: "down",
            pygame.K_s: "down",
            pygame.K_LEFT: "left",
            pygame.K_a: "left",
            pygame.K_RIGHT: "right",
            pygame.K_d: "right",
        }
        for event in events:
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN:
                action = actions.get(event.key)
                if action:
                    pressed.add(action)

        horizontal = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        vertical = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        return InputFrame((horizontal, vertical), frozenset(pressed), quit_requested)
