import math
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import patch

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    BALL_SPEED,
    GameStatus,
    MESSAGE_PAUSED,
    REWARD_TYPE_FIREBALL,
    SCREEN_HEIGHT,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame


_APP = QCoreApplication.instance() or QCoreApplication([])


class GameStateTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()

    def test_qml_left_click_launches_and_space_controls_the_round(self):
        self.assertEqual(self.controller.state.gameStatus, GameStatus.NOT_STARTED)
        self.assertTrue(self.controller.ball.magnetAttached)
        self.assertFalse(self.controller.ball._active)

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.NOT_STARTED)

        old_ball_x = self.controller.ball.x
        self.controller.setPaddleX(self.controller.paddleX + 40)
        self.assertAlmostEqual(self.controller.ball.x, old_ball_x + 40)

        self.controller.handlePrimaryAction()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)
        self.assertFalse(self.controller.ball.magnetAttached)
        self.assertTrue(self.controller.ball._active)
        self.assertAlmostEqual(
            math.hypot(self.controller.ball._dx, self.controller.ball._dy),
            BALL_SPEED,
        )

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PAUSED)
        self.assertEqual(self.controller.state.message, MESSAGE_PAUSED)
        paused_position = (self.controller.ball.x, self.controller.ball.y)
        self.controller._update()
        self.assertEqual((self.controller.ball.x, self.controller.ball.y), paused_position)

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)

        self.controller.rewardModel.create_reward(
            REWARD_TYPE_FIREBALL,
            100,
            100,
        )
        self.controller.ball._y = SCREEN_HEIGHT
        self.controller.state.score = 999
        self.controller._update()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.GAME_OVER)
        self.assertEqual(self.controller.rewardModel.rowCount(), 0)
        self.assertFalse(self.controller.ball.magnetAttached)
        self.assertFalse(self.controller.ball._active)

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.NOT_STARTED)
        self.assertEqual(self.controller.state.score, 0)
        self.assertTrue(self.controller.ball.magnetAttached)
        self.assertFalse(self.controller.ball._active)

        self.controller.handlePrimaryAction()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)
        self.assertTrue(self.controller.ball._active)

    def test_arcade_left_click_launches_and_space_controls_the_round(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.game_status = GameStatus.NOT_STARTED
        game.left_pressed = False
        game.right_pressed = False
        game.space_pressed = False
        game.paddle = SimpleNamespace(width=100.0)
        game.ball = SimpleNamespace(
            change_x=0.0,
            change_y=0.0,
            motion=SimpleNamespace(set_spin_from_paddle_hit=lambda _hit: None),
        )
        game.start_playing = MethodType(BreakoutGame.start_playing, game)
        game.handle_cheat = MethodType(BreakoutGame.handle_cheat, game)
        game.on_key_press = MethodType(BreakoutGame.on_key_press, game)
        game.on_mouse_press = MethodType(BreakoutGame.on_mouse_press, game)
        game.release_magnet_ball = MethodType(BreakoutGame.release_magnet_ball, game)
        game.fire_lasers = lambda: None
        game.magnet_attached = True
        game.magnet_offset = 0.0
        game.magnet_speed = BALL_SPEED

        def setup():
            game.game_status = GameStatus.NOT_STARTED
            game.ball.change_x = 0.0
            game.ball.change_y = 0.0
            game.magnet_attached = True
            game.magnet_offset = 0.0
            game.magnet_speed = BALL_SPEED

        game.setup = setup

        game.on_key_press(arcade.key.SPACE, None)
        self.assertEqual(game.game_status, GameStatus.NOT_STARTED)
        game.space_pressed = False
        game.on_mouse_press(0, 0, arcade.MOUSE_BUTTON_LEFT, None)
        self.assertEqual(game.game_status, GameStatus.PLAYING)
        self.assertAlmostEqual(math.hypot(game.ball.change_x, game.ball.change_y), BALL_SPEED)
        game.space_pressed = False
        game.on_key_press(arcade.key.SPACE, None)
        self.assertEqual(game.game_status, GameStatus.PAUSED)
        game.space_pressed = False
        game.on_key_press(arcade.key.SPACE, None)
        self.assertEqual(game.game_status, GameStatus.PLAYING)
        game.game_status = GameStatus.VICTORY
        game.space_pressed = False
        game.on_key_press(arcade.key.SPACE, None)
        self.assertEqual(game.game_status, GameStatus.NOT_STARTED)
        self.assertTrue(game.magnet_attached)
        self.assertEqual((game.ball.change_x, game.ball.change_y), (0.0, 0.0))
        game.on_mouse_press(0, 0, arcade.MOUSE_BUTTON_LEFT, None)
        self.assertEqual(game.game_status, GameStatus.PLAYING)

    def test_arcade_terminal_state_clears_active_play_objects(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.finish_game = MethodType(BreakoutGame.finish_game, game)
        game.game_status = GameStatus.PLAYING
        game.reward_list = [object(), object()]
        game.laser_bullet_list = [object()]
        game.laser_active = True
        game.magnet_active = True
        game.magnet_attached = True
        game.ball = SimpleNamespace(change_x=100.0, change_y=-200.0)

        game.finish_game(GameStatus.GAME_OVER)

        self.assertEqual(game.game_status, GameStatus.GAME_OVER)
        self.assertEqual(game.reward_list, [])
        self.assertEqual(game.laser_bullet_list, [])
        self.assertFalse(game.laser_active)
        self.assertFalse(game.magnet_active)
        self.assertFalse(game.magnet_attached)
        self.assertEqual((game.ball.change_x, game.ball.change_y), (0.0, 0.0))

    def test_arcade_requests_focus_again_after_the_event_loop_starts(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.request_startup_focus = MethodType(
            BreakoutGame.request_startup_focus,
            game,
        )
        game._retry_startup_focus = MethodType(
            BreakoutGame._retry_startup_focus,
            game,
        )
        activations = []
        game.activate = lambda: activations.append(True)

        with patch("main_arcade.arcade.schedule_once") as schedule_once:
            game.request_startup_focus()

            self.assertEqual(activations, [True])
            callback, delay = schedule_once.call_args.args
            self.assertEqual(delay, 0.1)
            callback(delay)

        self.assertEqual(activations, [True, True])


if __name__ == "__main__":
    unittest.main()
