import unittest

from qtpy.QtCore import QCoreApplication

from constants import (
    PADDLE_MAX_WIDTH,
    PADDLE_MIN_WIDTH,
    PADDLE_REWARD_SIZE_STEP,
    PADDLE_FANG_WIDTH,
    PADDLE_WIDTH,
    BALL_DIAMETER,
    SCREEN_WIDTH,
    REWARD_TYPE_EXTEND_PADDLE,
    REWARD_TYPE_FIREBALL,
    REWARD_TYPE_LASER,
    REWARD_TYPE_RESET,
    REWARD_TYPE_SHRINK_PADDLE,
    REWARD_TYPE_SKULL,
    GameStatus,
)
from game_logic_qml import GameController
from main_arcade import RoundedRectPaddle
from paddle_texture import paddle_fang_geometry


_APP = QCoreApplication.instance() or QCoreApplication([])


class PaddleRewardTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()

    def test_extend_and_shrink_preserve_the_paddle_center(self):
        old_center = self.controller.paddleX + self.controller.paddleWidth / 2

        self.controller._apply_reward(REWARD_TYPE_EXTEND_PADDLE)
        self.assertEqual(self.controller.paddleWidth, PADDLE_WIDTH + PADDLE_REWARD_SIZE_STEP)
        self.assertAlmostEqual(
            self.controller.paddleX + self.controller.paddleWidth / 2,
            old_center,
        )

        self.controller._apply_reward(REWARD_TYPE_SHRINK_PADDLE)
        self.assertEqual(self.controller.paddleWidth, PADDLE_WIDTH)

    def test_repeated_rewards_are_clamped(self):
        for _ in range(20):
            self.controller._apply_reward(REWARD_TYPE_EXTEND_PADDLE)
        self.assertEqual(self.controller.paddleWidth, PADDLE_MAX_WIDTH)
        self.assertEqual(PADDLE_MAX_WIDTH, SCREEN_WIDTH / 2)

        for _ in range(20):
            self.controller._apply_reward(REWARD_TYPE_SHRINK_PADDLE)
        self.assertEqual(self.controller.paddleWidth, PADDLE_MIN_WIDTH)
        self.assertEqual(PADDLE_MIN_WIDTH, BALL_DIAMETER)

    def test_fang_dimensions_stay_fixed_at_every_paddle_width(self):
        for paddle_width in (PADDLE_MIN_WIDTH, 70, PADDLE_WIDTH, 250, PADDLE_MAX_WIDTH):
            with self.subTest(paddle_width=paddle_width):
                fangs = paddle_fang_geometry(paddle_width)
                self.assertGreaterEqual(len(fangs), 1)
                for base_left, base_right, tip_x in fangs:
                    self.assertAlmostEqual(base_right - base_left, PADDLE_FANG_WIDTH)
                    self.assertAlmostEqual(tip_x, (base_left + base_right) / 2)

    def test_arcade_hit_box_tracks_the_resized_texture(self):
        paddle = RoundedRectPaddle(PADDLE_WIDTH, 20, (52, 152, 219))
        paddle.center_x = 400
        paddle.center_y = 50

        for paddle_width in (130, 70, PADDLE_MAX_WIDTH, PADDLE_MIN_WIDTH):
            with self.subTest(paddle_width=paddle_width):
                paddle.set_paddle_width(paddle_width)
                points = paddle.hit_box.get_adjusted_points()
                hit_box_width = max(point[0] for point in points) - min(point[0] for point in points)
                self.assertAlmostEqual(hit_box_width, paddle.width)

    def test_reset_reward_clears_all_persistent_effects(self):
        self.controller.state.gameStatus = GameStatus.PLAYING
        self.controller._apply_reward(REWARD_TYPE_FIREBALL)
        self.controller._apply_reward(REWARD_TYPE_EXTEND_PADDLE)
        self.controller._apply_reward(REWARD_TYPE_LASER)
        self.controller.fireLaser()
        self.assertEqual(len(self.controller.laserModel._bullets), 2)

        self.controller._apply_reward(REWARD_TYPE_RESET)
        self.assertFalse(self.controller.ball.fireball_active)
        self.assertFalse(self.controller.laserActive)
        self.assertEqual(self.controller.paddleWidth, PADDLE_WIDTH)
        self.assertEqual(len(self.controller.laserModel._bullets), 0)

    def test_skull_reward_ends_the_game_immediately(self):
        self.controller.state.gameStatus = GameStatus.PLAYING
        self.controller._apply_reward(REWARD_TYPE_SKULL)
        self.assertEqual(self.controller.state.gameStatus, GameStatus.GAME_OVER)

if __name__ == "__main__":
    unittest.main()
