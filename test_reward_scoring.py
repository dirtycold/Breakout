import unittest
from types import MethodType

import arcade
from qtpy.QtCore import QCoreApplication

from constants import (
    GameStatus,
    PADDLE_HEIGHT,
    PADDLE_WIDTH,
    REWARD_TYPE_FIREBALL,
    SCORE_PER_REWARD,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame, RewardSprite, RoundedRectPaddle


_APP = QCoreApplication.instance() or QCoreApplication([])


class RewardScoringTests(unittest.TestCase):
    def test_qml_collecting_a_reward_adds_five_points(self):
        controller = GameController()
        controller.timer.stop()
        controller.state.gameStatus = GameStatus.PLAYING
        controller.rewardModel.create_reward(
            REWARD_TYPE_FIREBALL,
            controller.paddleX + 20,
            controller._paddle_y + 10,
        )
        reward = controller.rewardModel._rewards[0]
        reward["vx"] = 0
        reward["vy"] = 0
        reward["gravity"] = 0

        controller._update()

        self.assertEqual(controller.state.score, SCORE_PER_REWARD)
        self.assertEqual(controller.rewardModel.rowCount(), 0)

    def test_arcade_collecting_a_reward_adds_five_points(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.paddle = RoundedRectPaddle(PADDLE_WIDTH, PADDLE_HEIGHT, (52, 152, 219))
        game.paddle.center_x = 400
        game.paddle.center_y = 50
        game.reward_list = arcade.SpriteList()
        reward = RewardSprite(REWARD_TYPE_FIREBALL, 400, 50)
        reward.change_x = 0
        reward.change_y = 0
        reward.gravity = 0
        game.reward_list.append(reward)
        game.score = 0
        game.game_status = GameStatus.PLAYING
        game.apply_reward = lambda _reward_type: None
        game.update_rewards = MethodType(BreakoutGame.update_rewards, game)

        game.update_rewards(0)

        self.assertEqual(game.score, SCORE_PER_REWARD)
        self.assertEqual(len(game.reward_list), 0)


if __name__ == "__main__":
    unittest.main()
