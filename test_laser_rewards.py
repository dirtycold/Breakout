import unittest
from types import MethodType

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    GameStatus,
    LASER_BULLET_HEIGHT,
    LASER_BULLET_WIDTH,
    LASER_GUN_COLOR,
    LASER_GUN_HEIGHT,
    LASER_GUN_WIDTH,
    PADDLE_HEIGHT,
    PADDLE_WIDTH,
    REWARD_TYPE_EXTEND_PADDLE,
    REWARD_TYPE_FIREBALL,
    REWARD_TYPE_LASER,
    REWARD_TYPE_RESET,
    REWARD_TYPE_SKULL,
    SCORE_PER_BRICK,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame, RainbowBall, RoundedRectPaddle


_APP = QCoreApplication.instance() or QCoreApplication([])


class LaserRewardTests(unittest.TestCase):
    def setUp(self):
        self.controller = GameController()
        self.controller.timer.stop()

    def test_twin_guns_fire_from_both_paddle_sides(self):
        self.controller.state.gameStatus = GameStatus.PLAYING
        self.controller._set_laser_active(True)
        self.controller.fireLaser()
        bullets = self.controller.laserModel._bullets

        self.assertEqual(len(bullets), 2)
        self.assertLess(bullets[0]["x"], bullets[1]["x"])

    def test_laser_hit_destroys_one_brick_and_scores(self):
        brick_row, brick = next(self.controller.brickModel.active_brick_rows())
        self.controller.laserModel._bullets = [{
            "x": brick["x"] + brick["width"] / 2 - LASER_BULLET_WIDTH / 2,
            "y": brick["y"] + brick["height"] / 2 - LASER_BULLET_HEIGHT / 2,
            "width": LASER_BULLET_WIDTH,
            "height": LASER_BULLET_HEIGHT,
        }]
        old_count = self.controller.state.brickCount

        self.controller._update_lasers(0)

        self.assertTrue(self.controller.brickModel.brick_at(brick_row)["destroyed"])
        self.assertEqual(self.controller.state.brickCount, old_count - 1)
        self.assertEqual(self.controller.state.score, SCORE_PER_BRICK)
        self.assertEqual(len(self.controller.laserModel._bullets), 0)

    def test_arcade_laser_reset_and_skull_effects(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        for method_name in (
            "apply_reward",
            "clamp_paddle_to_screen",
            "fire_lasers",
            "reset_active_rewards",
            "resize_paddle",
            "update_laser_guns",
        ):
            setattr(game, method_name, MethodType(getattr(BreakoutGame, method_name), game))
        game.paddle = RoundedRectPaddle(PADDLE_WIDTH, PADDLE_HEIGHT, (52, 152, 219))
        game.paddle.center_x = 400
        game.paddle.center_y = 50
        game.ball = RainbowBall(10)
        game.laser_gun_list = arcade.SpriteList()
        for _ in range(2):
            game.laser_gun_list.append(arcade.SpriteSolidColor(
                LASER_GUN_WIDTH,
                LASER_GUN_HEIGHT,
                color=LASER_GUN_COLOR,
            ))
        game.laser_bullet_list = arcade.SpriteList()
        game.laser_active = False
        game.game_status = GameStatus.PLAYING

        game.apply_reward(REWARD_TYPE_FIREBALL)
        game.apply_reward(REWARD_TYPE_EXTEND_PADDLE)
        game.apply_reward(REWARD_TYPE_LASER)
        game.fire_lasers()
        self.assertEqual(len(game.laser_bullet_list), 2)

        game.apply_reward(REWARD_TYPE_RESET)
        self.assertFalse(game.ball.fireball_active)
        self.assertFalse(game.laser_active)
        self.assertEqual(game.paddle.width, PADDLE_WIDTH)
        self.assertEqual(len(game.laser_bullet_list), 0)

        game.apply_reward(REWARD_TYPE_SKULL)
        self.assertEqual(game.game_status, GameStatus.GAME_OVER)


if __name__ == "__main__":
    unittest.main()
