"""Level selection, commands, iteration, validation, and UI mediation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Iterator

from coin_collector.factory import GameObjectFactory
from coin_collector.input_adapter import InputFrame
from coin_collector.level import (
    GameLevel,
    build_bonus_level,
    build_corner_level,
    build_default_level,
)

LevelBuilder = Callable[[GameObjectFactory, tuple[int, int]], GameLevel]


@dataclass(frozen=True)
class LevelDefinition:
    id: str
    name: str
    description: str
    build: LevelBuilder


class LevelIterator(Iterator[LevelDefinition]):
    def __init__(self, levels: tuple[LevelDefinition, ...]) -> None:
        self._levels = levels
        self._index = 0

    def __iter__(self) -> LevelIterator:
        return self

    def __next__(self) -> LevelDefinition:
        if self._index >= len(self._levels):
            raise StopIteration
        level = self._levels[self._index]
        self._index += 1
        return level


class LevelCatalog:
    def __init__(self, levels: tuple[LevelDefinition, ...]) -> None:
        if not levels:
            raise ValueError("A level catalog must contain at least one level")
        ids = [level.id for level in levels]
        if len(set(ids)) != len(ids) or any(not level_id for level_id in ids):
            raise ValueError("Level identifiers must be non-empty and unique")
        self._levels = levels

    def __iter__(self) -> LevelIterator:
        return LevelIterator(self._levels)

    def get(self, level_id: str) -> LevelDefinition:
        for level in self:
            if level.id == level_id:
                return level
        raise KeyError(f"Unknown level: {level_id!r}")


def create_level_catalog() -> LevelCatalog:
    return LevelCatalog(
        (
            LevelDefinition(
                "classic",
                "Классическая арена",
                "Соберите восемь монет и обходите четыре опасности.",
                build_default_level,
            ),
            LevelDefinition(
                "corners",
                "Четыре угла",
                "Заберите монеты по углам, не задев центральные опасности.",
                build_corner_level,
            ),
            LevelDefinition(
                "bonus",
                "Охота за бонусом",
                "Бонусная монета стоит вдвое больше обычной.",
                build_bonus_level,
            ),
        )
    )


class LevelValidationHandler(ABC):
    def __init__(self, next_handler: LevelValidationHandler | None = None) -> None:
        self._next_handler = next_handler

    def handle(self, level: GameLevel) -> GameLevel:
        self._validate(level)
        if self._next_handler is not None:
            return self._next_handler.handle(level)
        return level

    @abstractmethod
    def _validate(self, level: GameLevel) -> None:
        raise NotImplementedError


class SinglePlayerLevelHandler(LevelValidationHandler):
    def _validate(self, level: GameLevel) -> None:
        if len(level.players) != 1:
            raise ValueError("A selectable level must contain exactly one player")


class CollectibleLevelHandler(LevelValidationHandler):
    def _validate(self, level: GameLevel) -> None:
        if not level.coins:
            raise ValueError("A selectable level must contain at least one coin")


class LevelBoundsHandler(LevelValidationHandler):
    def _validate(self, level: GameLevel) -> None:
        objects = [*level.players, *level.coins, *level.hazards]
        if any(not level.bounds.contains(game_object.rect) for game_object in objects):
            raise ValueError("All objects in a selectable level must fit inside its bounds")


def create_level_validation_chain() -> LevelValidationHandler:
    return SinglePlayerLevelHandler(
        CollectibleLevelHandler(LevelBoundsHandler())
    )


@dataclass(frozen=True)
class StartLevelCommand:
    definition: LevelDefinition
    factory: GameObjectFactory
    size: tuple[int, int]
    validator: LevelValidationHandler

    def execute(self) -> GameLevel:
        level = self.definition.build(self.factory, self.size)
        return self.validator.handle(level)


@dataclass(frozen=True)
class LevelSelectionMemento:
    selected_level_id: str


@dataclass(frozen=True)
class _SelectionResult:
    level: GameLevel | None = None
    back_requested: bool = False


class LevelSelectionInputHandler(ABC):
    def __init__(self, next_handler: LevelSelectionInputHandler | None = None) -> None:
        self._next_handler = next_handler

    def handle(
        self,
        frame: InputFrame,
        mediator: LevelSelectionMediator,
    ) -> _SelectionResult | None:
        result = self._handle(frame, mediator)
        if result is not None:
            return result
        if self._next_handler is not None:
            return self._next_handler.handle(frame, mediator)
        return None

    @abstractmethod
    def _handle(
        self,
        frame: InputFrame,
        mediator: LevelSelectionMediator,
    ) -> _SelectionResult | None:
        raise NotImplementedError


class BackSelectionHandler(LevelSelectionInputHandler):
    def _handle(
        self,
        frame: InputFrame,
        mediator: LevelSelectionMediator,
    ) -> _SelectionResult | None:
        if "back" not in frame.pressed:
            return None
        mediator.cancel()
        return _SelectionResult(back_requested=True)


class NavigateSelectionHandler(LevelSelectionInputHandler):
    def _handle(
        self,
        frame: InputFrame,
        mediator: LevelSelectionMediator,
    ) -> _SelectionResult | None:
        if "up" in frame.pressed:
            mediator.move(-1)
        elif "down" in frame.pressed:
            mediator.move(1)
        else:
            return None
        return _SelectionResult()


class ConfirmSelectionHandler(LevelSelectionInputHandler):
    def _handle(
        self,
        frame: InputFrame,
        mediator: LevelSelectionMediator,
    ) -> _SelectionResult | None:
        if "confirm" not in frame.pressed:
            return None
        return _SelectionResult(level=mediator.start_selected())


class LevelSelectionMediator:
    """Coordinate selection input, the catalog, and the level-start command."""

    def __init__(
        self,
        catalog: LevelCatalog,
        factory: GameObjectFactory,
        size: tuple[int, int],
    ) -> None:
        self.catalog = catalog
        self.levels = tuple(catalog)
        self.factory = factory
        self.size = size
        self.selected_level_id = self.levels[0].id
        self._validator = create_level_validation_chain()
        self._input_handler = BackSelectionHandler(
            NavigateSelectionHandler(ConfirmSelectionHandler())
        )
        self._memento = self.save()
        self.back_requested = False

    @property
    def selected_index(self) -> int:
        return next(
            index
            for index, level in enumerate(self.levels)
            if level.id == self.selected_level_id
        )

    @property
    def selected_level(self) -> LevelDefinition:
        return self.catalog.get(self.selected_level_id)

    def begin(self) -> None:
        self._memento = self.save()
        self.back_requested = False

    def save(self) -> LevelSelectionMemento:
        return LevelSelectionMemento(self.selected_level_id)

    def restore(self, memento: LevelSelectionMemento) -> None:
        self.catalog.get(memento.selected_level_id)
        self.selected_level_id = memento.selected_level_id

    def cancel(self) -> None:
        self.restore(self._memento)

    def move(self, offset: int) -> None:
        index = (self.selected_index + offset) % len(self.levels)
        self.selected_level_id = self.levels[index].id

    def start_selected(self) -> GameLevel:
        return StartLevelCommand(
            self.selected_level,
            self.factory,
            self.size,
            self._validator,
        ).execute()

    def handle(self, frame: InputFrame) -> GameLevel | None:
        result = self._input_handler.handle(frame, self)
        self.back_requested = result.back_requested if result is not None else False
        return result.level if result is not None else None
