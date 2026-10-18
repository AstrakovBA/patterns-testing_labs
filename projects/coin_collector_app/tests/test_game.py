import unittest

import pygame

from coin_collector.entities import Coin, Hazard, Player
from coin_collector.factory import ArcadeObjectFactory, ObjectKind
from coin_collector.input_adapter import InputFrame
from coin_collector.level import GameLevelBuilder


class EntityTests(unittest.TestCase):
    def test_factory_creates_requested_entities(self):
        factory = ArcadeObjectFactory()
        self.assertIsInstance(factory.create(ObjectKind.PLAYER, (40, 40)), Player)
        self.assertIsInstance(factory.create(ObjectKind.COIN, (50, 50)), Coin)
        self.assertIsInstance(factory.create(ObjectKind.HAZARD, (60, 60)), Hazard)

    def test_prototype_clones_have_independent_positions_and_state(self):
        factory = ArcadeObjectFactory()
        first = factory.create(ObjectKind.COIN, (50, 50))
        second = factory.create(ObjectKind.COIN, (90, 90))
        self.assertIsInstance(first, Coin)
        self.assertIsInstance(second, Coin)
        first.rect.center = (10, 10)
        first.animation_time = 3
        self.assertEqual(second.rect.center, (90, 90))
        self.assertEqual(second.animation_time, 0)

    def test_level_builder_rejects_out_of_bounds_objects(self):
        builder = GameLevelBuilder(ArcadeObjectFactory(), (960, 640))
        builder.add_coin((0, 0))
        builder.add_hazard((0, 0))
        with self.assertRaises(ValueError):
            builder.build()

    def test_player_moves_and_stays_within_bounds(self):
        player = Player((50, 50))
        bounds = pygame.Rect(0, 0, 100, 100)
        player.update(InputFrame(movement=(1, 0)), 0.1, bounds)
        self.assertGreater(player.rect.centerx, 50)
        player.update(InputFrame(movement=(-1, -1)), 2.0, bounds)
        self.assertTrue(bounds.contains(player.rect))

    def test_player_damage_obeys_invulnerability_cooldown(self):
        player = Player((50, 50))
        self.assertTrue(player.take_damage(1.0))
        self.assertFalse(player.take_damage(1.0))
        self.assertEqual(player.health, 2)


if __name__ == "__main__":
    unittest.main()
