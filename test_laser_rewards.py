import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import patch

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    GameStatus,
    LASER_BULLET_HEIGHT,
    LASER_BULLET_WIDTH,
    LASER_GUN_COLOR,
    LASER_GUN_HEIGHT,
    LASER_GUN_WIDTH,
    BRICK_HEIGHT,
    BRICK_WIDTH,
    PADDLE_HEIGHT,
    PADDLE_WIDTH,
    REWARD_TYPE_EXTEND_PADDLE,
    REWARD_TYPE_FIREBALL,
    REWARD_TYPE_LASER,
    REWARD_TYPE_MAGNET,
    REWARD_TYPE_RESET,
    REWARD_TYPE_SKULL,
    SCORE_PER_BRICK,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame, RainbowBall, RoundedRectBrick, RoundedRectPaddle


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

        with patch("game_logic_qml.choose_reward_type", return_value=None):
            self.controller._update_lasers(0)

        self.assertTrue(self.controller.brickModel.brick_at(brick_row)["destroyed"])
        self.assertEqual(self.controller.state.brickCount, old_count - 1)
        self.assertEqual(self.controller.state.score, SCORE_PER_BRICK)
        self.assertEqual(len(self.controller.laserModel._bullets), 0)

    def test_qml_laser_hit_can_spawn_a_reward(self):
        brick_row, brick = next(self.controller.brickModel.active_brick_rows())
        self.controller.laserModel._bullets = [{
            "x": brick["x"],
            "y": brick["y"],
            "width": LASER_BULLET_WIDTH,
            "height": LASER_BULLET_HEIGHT,
        }]

        with patch("game_logic_qml.choose_reward_type", return_value=REWARD_TYPE_LASER):
            self.controller._update_lasers(0)

        self.assertEqual(self.controller.rewardModel.rowCount(), 1)
        self.assertEqual(self.controller.rewardModel._rewards[0]["type"], REWARD_TYPE_LASER)

    def test_arcade_laser_reset_and_skull_effects(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        for method_name in (
            "apply_reward",
            "clamp_paddle_to_screen",
            "fire_lasers",
            "finish_game",
            "reset_active_rewards",
            "release_magnet_ball",
            "resize_paddle",
            "set_magnet_active",
            "update_attached_ball",
            "update_magnet_effect",
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
        game.reward_list = arcade.SpriteList()
        game.laser_active = False
        game.magnet_active = False
        game.magnet_attached = False
        game.magnet_effect = None
        game.game_status = GameStatus.PLAYING

        game.apply_reward(REWARD_TYPE_FIREBALL)
        game.apply_reward(REWARD_TYPE_EXTEND_PADDLE)
        game.apply_reward(REWARD_TYPE_LASER)
        game.apply_reward(REWARD_TYPE_MAGNET)
        game.fire_lasers()
        self.assertEqual(len(game.laser_bullet_list), 2)
        self.assertTrue(game.magnet_active)

        game.apply_reward(REWARD_TYPE_RESET)
        self.assertFalse(game.ball.fireball_active)
        self.assertFalse(game.laser_active)
        self.assertFalse(game.magnet_active)
        self.assertEqual(game.paddle.width, PADDLE_WIDTH)
        self.assertEqual(len(game.laser_bullet_list), 0)

        game.apply_reward(REWARD_TYPE_SKULL)
        self.assertEqual(game.game_status, GameStatus.GAME_OVER)

    def test_arcade_laser_hit_calls_reward_drop(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        for method_name in ("finish_game", "update_laser_guns", "update_lasers"):
            setattr(game, method_name, MethodType(getattr(BreakoutGame, method_name), game))
        game.paddle = RoundedRectPaddle(PADDLE_WIDTH, PADDLE_HEIGHT, (52, 152, 219))
        game.paddle.center_x = 400
        game.paddle.center_y = 50
        game.laser_gun_list = arcade.SpriteList()
        for _ in range(2):
            game.laser_gun_list.append(arcade.SpriteSolidColor(
                LASER_GUN_WIDTH,
                LASER_GUN_HEIGHT,
                color=LASER_GUN_COLOR,
            ))
        game.laser_bullet_list = arcade.SpriteList()
        game.reward_list = arcade.SpriteList()
        game.brick_list = arcade.SpriteList()
        brick = RoundedRectBrick(BRICK_WIDTH, BRICK_HEIGHT, (255, 107, 107))
        brick.center_x = 400
        brick.center_y = 300
        game.brick_list.append(brick)
        bullet = arcade.SpriteSolidColor(LASER_BULLET_WIDTH, LASER_BULLET_HEIGHT)
        bullet.center_x = brick.center_x
        bullet.center_y = brick.center_y
        game.laser_bullet_list.append(bullet)
        game.score = 0
        game.game_status = GameStatus.PLAYING
        game.ball = SimpleNamespace(change_x=0.0, change_y=0.0)
        game.laser_active = True
        game.magnet_active = False
        game.magnet_attached = False
        game.create_explosion = lambda *_args: None
        reward_spawns = []
        game.spawn_reward = lambda *args: reward_spawns.append(args)

        game.update_lasers(0)

        self.assertEqual(len(reward_spawns), 1)
        self.assertEqual(len(game.brick_list), 0)


if __name__ == "__main__":
    unittest.main()
