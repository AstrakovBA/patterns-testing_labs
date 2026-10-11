"""Pygame application, screens, and the main game loop."""

from __future__ import annotations

import logging
import pygame

from coin_collector.audio import PygameSoundAdapter
from coin_collector.entities import Coin, Hazard
from coin_collector.factory import ArcadeObjectFactory
from coin_collector.input_adapter import InputFrame, PygameInputAdapter
from coin_collector.level import GameLevel, build_default_level
from coin_collector.rendering import Color, PygameDrawingAPI
from coin_collector.settings import SettingsManager

WIDTH = 960
HEIGHT = 640
FPS = 60
BACKGROUND: Color = (22, 31, 49)
ARENA: Color = (30, 43, 64)
TEXT: Color = (237, 242, 250)
ACCENT: Color = (255, 200, 70)

logger = logging.getLogger(__name__)


class CoinCollectorApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Собиратель монет")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.drawing = PygameDrawingAPI(self.screen)
        self.clock = pygame.time.Clock()
        self.input_adapter = PygameInputAdapter()
        self.settings = SettingsManager()
        self.audio = PygameSoundAdapter()
        self.factory = ArcadeObjectFactory()
        self.screen_name = "menu"
        self.menu_selection = 0
        self.settings_selection = 0
        self.running = True
        self.level: GameLevel | None = None
        self.score = 0
        self.message = ""

    def run(self) -> None:
        try:
            while self.running:
                delta_time = min(self.clock.tick(FPS) / 1000.0, 0.05)
                frame = self.input_adapter.read(pygame.event.get(), pygame.key.get_pressed())
                if frame.quit_requested:
                    self.running = False
                elif self.screen_name == "menu":
                    self._handle_menu(frame)
                    self._draw_menu()
                elif self.screen_name == "settings":
                    self._handle_settings(frame)
                    self._draw_settings()
                elif self.screen_name == "playing":
                    self._update_game(frame, delta_time)
                    self._draw_game()
                else:
                    self._handle_result(frame)
                    self._draw_result()
                pygame.display.flip()
        finally:
            pygame.quit()

    def _handle_menu(self, frame: InputFrame) -> None:
        if "up" in frame.pressed:
            self.menu_selection = (self.menu_selection - 1) % 3
        if "down" in frame.pressed:
            self.menu_selection = (self.menu_selection + 1) % 3
        if "confirm" not in frame.pressed:
            return
        if self.menu_selection == 0:
            self._start_game()
        elif self.menu_selection == 1:
            self.screen_name = "settings"
        else:
            self.running = False

    def _handle_settings(self, frame: InputFrame) -> None:
        if "back" in frame.pressed:
            self.screen_name = "menu"
            return
        if "up" in frame.pressed:
            self.settings_selection = (self.settings_selection - 1) % 3
        if "down" in frame.pressed:
            self.settings_selection = (self.settings_selection + 1) % 3
        activate = "confirm" in frame.pressed or "left" in frame.pressed or "right" in frame.pressed
        if not activate:
            return
        if self.settings_selection == 0:
            self.settings.toggle_sound()
        elif self.settings_selection == 1:
            self.settings.toggle_difficulty()
        else:
            self.screen_name = "menu"

    def _start_game(self) -> None:
        self.level = build_default_level(self.factory, (WIDTH, HEIGHT))
        self.level.player.health = self.settings.settings.player_health
        self.score = 0
        self.message = ""
        self.screen_name = "playing"

    def _update_game(self, frame: InputFrame, delta_time: float) -> None:
        if self.level is None:
            raise RuntimeError("Cannot update a game before starting a level")
        if "back" in frame.pressed:
            self.screen_name = "menu"
            return
        player = self.level.player
        player.update(frame, delta_time, self.level.bounds)
        for coin in self.level.coins:
            coin.update(delta_time)
        for coin in self.level.coins[:]:
            if player.rect.colliderect(coin.rect):
                self.score += coin.value
                self.level.coins.remove(coin)
                if self.settings.settings.sound_effects:
                    self.audio.play("coin")
        for hazard in self.level.hazards:
            if player.rect.colliderect(hazard.rect) and player.take_damage(
                self.settings.settings.damage_cooldown
            ):
                logger.info("Player took damage; %s health remaining", player.health)
                if self.settings.settings.sound_effects:
                    self.audio.play("hit")
        if player.health <= 0:
            self.message = "Здоровье закончилось"
            self.screen_name = "result"
        elif not self.level.coins:
            self.message = "Все монеты собраны!"
            self.screen_name = "result"

    def _draw_menu(self) -> None:
        self._background()
        self.drawing.text("СОБИРАТЕЛЬ МОНЕТ", (WIDTH // 2, 165), 64, ACCENT, centered=True)
        self.drawing.text("Собери все монеты и избегай опасностей", (WIDTH // 2, 225), 27, TEXT, centered=True)
        self._draw_options(("Начать игру", "Настройки", "Выход"), self.menu_selection, 330)
        self.drawing.text("Перемещение: WASD или стрелки   •   Выбор: Enter", (WIDTH // 2, 540), 22, TEXT, centered=True)

    def _draw_settings(self) -> None:
        self._background()
        self.drawing.text("НАСТРОЙКИ", (WIDTH // 2, 140), 58, ACCENT, centered=True)
        sound = "Вкл." if self.settings.settings.sound_effects else "Выкл."
        difficulty = "Обычная" if self.settings.settings.difficulty == "normal" else "Сложная"
        options = (f"Звуковые эффекты: {sound}", f"Сложность: {difficulty}", "Назад")
        self._draw_options(options, self.settings_selection, 270)
        self.drawing.text("Выберите пункт стрелками; Enter или ←/→ — изменить", (WIDTH // 2, 505), 22, TEXT, centered=True)

    def _draw_options(self, options: tuple[str, ...], selection: int, start_y: int) -> None:
        for index, option in enumerate(options):
            color = ACCENT if index == selection else TEXT
            prefix = "›  " if index == selection else "   "
            self.drawing.text(prefix + option, (WIDTH // 2, start_y + index * 62), 34, color, centered=True)

    def _draw_game(self) -> None:
        self._background()
        assert self.level is not None
        self.drawing.rectangle(ARENA, self.level.bounds, 16)
        self.drawing.rectangle((60, 76, 101), self.level.bounds, 16, 4)
        self.drawing.text(f"Очки: {self.score}", (40, 25), 30, ACCENT)
        health = "♥ " * self.level.player.health
        self.drawing.text(f"Здоровье: {health}", (WIDTH - 245, 25), 30, (255, 112, 126))
        self.drawing.text("Esc — меню", (WIDTH // 2, 35), 22, TEXT, centered=True)
        for coin in self.level.coins:
            coin.draw(self.drawing)
        for hazard in self.level.hazards:
            hazard.draw(self.drawing)
        self.level.player.draw(self.drawing)

    def _handle_result(self, frame: InputFrame) -> None:
        if "confirm" in frame.pressed or "back" in frame.pressed:
            self.screen_name = "menu"

    def _draw_result(self) -> None:
        self._background()
        self.drawing.text(self.message, (WIDTH // 2, 230), 54, ACCENT, centered=True)
        self.drawing.text(f"Ваш счёт: {self.score}", (WIDTH // 2, 315), 38, TEXT, centered=True)
        self.drawing.text("Enter или Esc — вернуться в меню", (WIDTH // 2, 410), 28, TEXT, centered=True)

    def _background(self) -> None:
        self.screen.fill(BACKGROUND)
        for index in range(24):
            x = (index * 157 + 41) % WIDTH
            y = (index * 113 + 27) % HEIGHT
            radius = 1 + index % 2
            self.drawing.circle((53, 66, 89), (x, y), radius)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    CoinCollectorApp().run()
