import unittest
from types import MethodType

import arcade

from game_canvas import game_canvas_viewport
from main_arcade import BreakoutGame


class GameCanvasTests(unittest.TestCase):
    def test_wide_window_is_letterboxed_at_the_sides(self):
        viewport = game_canvas_viewport(1600, 900)

        self.assertEqual(viewport.scale, 1.5)
        self.assertEqual((viewport.width, viewport.height), (1200, 900))
        self.assertEqual((viewport.x, viewport.y), (200, 0))
        self.assertIsNone(viewport.to_game(199, 450))
        self.assertEqual(viewport.to_game(200, 0), (0, 0))
        self.assertEqual(viewport.to_game(1400, 900), (800, 600))

    def test_tall_window_is_letterboxed_above_and_below(self):
        viewport = game_canvas_viewport(800, 1000)

        self.assertEqual(viewport.scale, 1.0)
        self.assertEqual((viewport.width, viewport.height), (800, 600))
        self.assertEqual((viewport.x, viewport.y), (0, 200))
        self.assertIsNone(viewport.to_game(400, 199))
        self.assertEqual(viewport.to_game(400, 500), (400, 300))

    def test_smaller_window_scales_input_back_to_logical_coordinates(self):
        viewport = game_canvas_viewport(400, 300)

        self.assertEqual(viewport.scale, 0.5)
        self.assertEqual(viewport.to_game(125, 75), (250, 150))

    def test_arcade_f11_and_f_toggle_native_fullscreen(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.fullscreen = False
        game.left_pressed = False
        game.right_pressed = False
        game.space_pressed = False
        game.handle_cheat = lambda _key, _modifiers: False
        game.toggle_fullscreen = MethodType(BreakoutGame.toggle_fullscreen, game)
        game.on_key_press = MethodType(BreakoutGame.on_key_press, game)

        def set_fullscreen(fullscreen):
            game.fullscreen = fullscreen

        game.set_fullscreen = set_fullscreen

        game.on_key_press(arcade.key.F11, 0)
        self.assertTrue(game.fullscreen)
        game.on_key_press(arcade.key.F, 0)
        self.assertFalse(game.fullscreen)


if __name__ == "__main__":
    unittest.main()
