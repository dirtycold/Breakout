import math
import unittest
from types import MethodType

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    BALL_RADIUS,
    BALL_SPEED,
    MAGNET_EFFECT_FRAME_COUNT,
    MAGNET_EFFECT_HEIGHT,
    MAGNET_EFFECT_WIDTH,
    PADDLE_HEIGHT,
    PADDLE_WIDTH,
    REWARD_TYPE_MAGNET,
    REWARD_TYPE_SHRINK_PADDLE,
    GameStatus,
)
from game_logic_qml import GameController
from magnet_visual import (
    create_magnet_effect_frames,
    create_magnet_effect_sprite_sheet_data_url,
)
from main_arcade import BreakoutGame, RainbowBall, RoundedRectPaddle


_APP = QCoreApplication.instance() or QCoreApplication([])


class MagnetRewardTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()
        self.controller.state.gameStatus = GameStatus.PLAYING
        self.controller.ball.launch()
        self.controller._apply_reward(REWARD_TYPE_MAGNET)

    def _capture_qml_ball(self, offset=24):
        ball = self.controller.ball
        ball._x = self.controller.paddleX + self.controller.paddleWidth / 2 + offset
        ball._y = self.controller._paddle_y - BALL_RADIUS + 1
        ball._dx = 80
        ball._dy = 260
        self.assertTrue(
            ball.checkPaddleCollision(
                self.controller.paddleX,
                self.controller._paddle_y,
                self.controller.paddleWidth,
                self.controller.magnetActive,
            )
        )
        return ball

    def test_qml_ball_sticks_follows_and_space_releases_without_pausing(self):
        ball = self._capture_qml_ball()
        attached_offset = ball.x - (
            self.controller.paddleX + self.controller.paddleWidth / 2
        )
        self.assertTrue(ball.magnetAttached)
        self.assertEqual((ball._dx, ball._dy), (0.0, 0.0))

        old_ball_x = ball.x
        self.controller.setPaddleX(self.controller.paddleX + 50)
        self.assertAlmostEqual(ball.x, old_ball_x + 50)
        self.assertAlmostEqual(
            ball.x - (self.controller.paddleX + self.controller.paddleWidth / 2),
            attached_offset,
        )

        self.controller.handleSpace()
        self.assertEqual(self.controller.state.gameStatus, GameStatus.PLAYING)
        self.assertFalse(ball.magnetAttached)
        self.assertLess(ball._dy, 0)
        self.assertGreaterEqual(math.hypot(ball._dx, ball._dy), BALL_SPEED)

    def test_qml_primary_action_releases_before_firing_lasers(self):
        ball = self._capture_qml_ball()
        self.controller._set_laser_active(True)

        self.controller.handlePrimaryAction()

        self.assertFalse(ball.magnetAttached)
        self.assertEqual(len(self.controller.laserModel._bullets), 0)
        self.controller.handlePrimaryAction()
        self.assertEqual(len(self.controller.laserModel._bullets), 2)

    def test_attached_ball_stays_on_the_paddle_when_it_shrinks(self):
        ball = self._capture_qml_ball(offset=38)

        for _ in range(3):
            self.controller._apply_reward(REWARD_TYPE_SHRINK_PADDLE)

        self.assertTrue(ball.magnetAttached)
        self.assertAlmostEqual(
            ball.x,
            self.controller.paddleX + self.controller.paddleWidth / 2,
        )

    def test_reset_reward_clears_magnet_and_safely_releases_ball(self):
        ball = self._capture_qml_ball()

        self.controller._reset_active_rewards()

        self.assertFalse(self.controller.magnetActive)
        self.assertFalse(ball.magnetAttached)
        self.assertLess(ball._dy, 0)

    def test_arcade_capture_tracks_paddle_and_releases_upward(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        for method_name in (
            "attach_ball_to_magnet",
            "on_key_press",
            "on_mouse_press",
            "release_magnet_ball",
            "update_attached_ball",
            "update_magnet_effect",
        ):
            setattr(game, method_name, MethodType(getattr(BreakoutGame, method_name), game))
        game.paddle = RoundedRectPaddle(PADDLE_WIDTH, PADDLE_HEIGHT, (52, 152, 219))
        game.paddle.center_x = 400
        game.paddle.center_y = 50
        game.ball = RainbowBall(BALL_RADIUS)
        game.ball.center_x = 430
        game.ball.change_x = 80
        game.ball.change_y = -260
        game.magnet_attached = False
        game.magnet_effect = None
        game.game_status = GameStatus.PLAYING
        game.left_pressed = False
        game.right_pressed = False
        game.space_pressed = False
        laser_fires = []
        game.fire_lasers = lambda: laser_fires.append(True)

        self.assertTrue(game.attach_ball_to_magnet())
        self.assertTrue(game.magnet_attached)
        self.assertEqual((game.ball.change_x, game.ball.change_y), (0.0, 0.0))
        game.paddle.center_x += 60
        game.update_attached_ball()
        self.assertEqual(game.ball.center_x, 490)

        game.on_key_press(arcade.key.SPACE, None)
        self.assertFalse(game.magnet_attached)
        self.assertEqual(game.game_status, GameStatus.PLAYING)
        self.assertGreater(game.ball.change_y, 0)
        self.assertGreaterEqual(
            math.hypot(game.ball.change_x, game.ball.change_y),
            BALL_SPEED,
        )

        game.attach_ball_to_magnet()
        game.on_mouse_press(0, 0, arcade.MOUSE_BUTTON_LEFT, None)
        self.assertFalse(game.magnet_attached)
        self.assertEqual(laser_fires, [])
        game.on_mouse_press(0, 0, arcade.MOUSE_BUTTON_LEFT, None)
        self.assertEqual(laser_fires, [True])

    def test_electromagnetic_animation_is_a_nonempty_sprite_sheet(self):
        frames = create_magnet_effect_frames()

        self.assertEqual(len(frames), MAGNET_EFFECT_FRAME_COUNT)
        self.assertEqual(frames[0].size, (MAGNET_EFFECT_WIDTH, MAGNET_EFFECT_HEIGHT))
        self.assertIsNotNone(frames[0].getbbox())
        self.assertNotEqual(frames[0].tobytes(), frames[1].tobytes())
        self.assertTrue(
            create_magnet_effect_sprite_sheet_data_url().startswith(
                "data:image/png;base64,"
            )
        )


if __name__ == "__main__":
    unittest.main()
