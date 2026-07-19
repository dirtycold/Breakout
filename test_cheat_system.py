import unittest
from types import MethodType, SimpleNamespace

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    GameStatus,
    PADDLE_REWARD_SIZE_STEP,
    PADDLE_WIDTH,
    REWARD_TYPE_FIREBALL,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame


_APP = QCoreApplication.instance() or QCoreApplication([])


class CheatSystemTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()

    def test_qml_cheats_toggle_and_reverse_reward_effects(self):
        self.assertTrue(self.controller.handleCheat(2, False))
        self.assertEqual(
            self.controller.paddleWidth,
            PADDLE_WIDTH + PADDLE_REWARD_SIZE_STEP,
        )
        self.assertTrue(self.controller.handleCheat(2, True))
        self.assertEqual(self.controller.paddleWidth, PADDLE_WIDTH)

        self.controller.handleCheat(3, False)
        self.assertTrue(self.controller.laserActive)
        self.controller.state.gameStatus = GameStatus.PLAYING
        self.controller.fireLaser()
        self.assertEqual(len(self.controller.laserModel._bullets), 2)
        self.controller.handleCheat(3, True)
        self.assertFalse(self.controller.laserActive)
        self.assertEqual(len(self.controller.laserModel._bullets), 0)

        self.controller.handleCheat(4, False)
        self.assertTrue(self.controller.magnetActive)
        self.controller.handleCheat(4, True)
        self.assertFalse(self.controller.magnetActive)
        self.assertFalse(self.controller.handleCheat(99, False))

    def test_qml_ctrl_f1_semantics_reset_all_persistent_rewards(self):
        self.controller._apply_reward(REWARD_TYPE_FIREBALL)
        self.controller.handleCheat(2, False)
        self.controller.handleCheat(3, False)
        self.controller.handleCheat(4, False)

        self.assertTrue(self.controller.handleCheat(1, False))

        self.assertFalse(self.controller.ball.fireball_active)
        self.assertFalse(self.controller.laserActive)
        self.assertFalse(self.controller.magnetActive)
        self.assertEqual(self.controller.paddleWidth, PADDLE_WIDTH)

    def test_arcade_ctrl_shortcuts_dispatch_without_plain_f_key_side_effects(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.handle_cheat = MethodType(BreakoutGame.handle_cheat, game)
        game.on_key_press = MethodType(BreakoutGame.on_key_press, game)
        game.paddle = SimpleNamespace(width=PADDLE_WIDTH)
        game.left_pressed = False
        game.right_pressed = False
        game.space_pressed = False
        game.laser_active = False
        game.laser_bullet_list = [object()]
        resize_calls = []
        magnet_calls = []
        reset_calls = []
        gun_updates = []

        def resize_paddle(width):
            game.paddle.width = width
            resize_calls.append(width)

        game.resize_paddle = resize_paddle
        game.set_magnet_active = magnet_calls.append
        game.reset_active_rewards = lambda: reset_calls.append(True)
        game.update_laser_guns = lambda: gun_updates.append(True)

        self.assertFalse(game.handle_cheat(arcade.key.F2, 0))
        self.assertEqual(resize_calls, [])

        game.on_key_press(arcade.key.F2, arcade.key.MOD_COMMAND)
        self.assertEqual(
            resize_calls[-1],
            PADDLE_WIDTH + PADDLE_REWARD_SIZE_STEP,
        )
        game.on_key_press(
            arcade.key.F2,
            arcade.key.MOD_CTRL | arcade.key.MOD_SHIFT,
        )
        self.assertEqual(resize_calls[-1], PADDLE_WIDTH)

        game.on_key_press(arcade.key.F3, arcade.key.MOD_CTRL)
        self.assertTrue(game.laser_active)
        self.assertEqual(gun_updates, [True])
        game.on_key_press(
            arcade.key.F3,
            arcade.key.MOD_CTRL | arcade.key.MOD_SHIFT,
        )
        self.assertFalse(game.laser_active)
        self.assertEqual(game.laser_bullet_list, [])

        game.on_key_press(arcade.key.F4, arcade.key.MOD_CTRL)
        game.on_key_press(
            arcade.key.F4,
            arcade.key.MOD_CTRL | arcade.key.MOD_SHIFT,
        )
        self.assertEqual(magnet_calls, [True, False])

        game.on_key_press(arcade.key.F1, arcade.key.MOD_CTRL)
        self.assertEqual(reset_calls, [True])


if __name__ == "__main__":
    unittest.main()
