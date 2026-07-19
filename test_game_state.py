import math
import unittest
from types import MethodType, SimpleNamespace

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    BALL_SPEED,
    GameStatus,
    MESSAGE_PAUSED,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame


_APP = QCoreApplication.instance() or QCoreApplication([])


class GameStateTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()

    def test_qml_space_controls_start_pause_resume_and_restart(self):
        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PAUSED)
        self.assertEqual(self.controller.state.message, MESSAGE_PAUSED)
        paused_position = (self.controller.ball.x, self.controller.ball.y)
        self.controller._update()
        self.assertEqual((self.controller.ball.x, self.controller.ball.y), paused_position)

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)

        self.controller.state.gameStatus = GameStatus.GAME_OVER
        self.controller.state.score = 999
        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)
        self.assertEqual(self.controller.state.score, 0)
        self.assertTrue(self.controller.ball._active)

    def test_arcade_space_uses_the_same_state_machine(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.game_status = GameStatus.NOT_STARTED
        game.left_pressed = False
        game.right_pressed = False
        game.space_pressed = False
        game.ball = SimpleNamespace(change_x=0.0, change_y=0.0)
        game.start_playing = MethodType(BreakoutGame.start_playing, game)
        game.on_key_press = MethodType(BreakoutGame.on_key_press, game)
        game.release_magnet_ball = MethodType(BreakoutGame.release_magnet_ball, game)
        game.magnet_attached = False

        def setup():
            game.game_status = GameStatus.NOT_STARTED
            game.ball = SimpleNamespace(change_x=0.0, change_y=0.0)
            game.magnet_attached = False

        game.setup = setup

        game.on_key_press(arcade.key.SPACE, None)
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
        self.assertEqual(game.game_status, GameStatus.PLAYING)


if __name__ == "__main__":
    unittest.main()
