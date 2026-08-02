import math
import unittest
from types import MethodType, SimpleNamespace

from qtpy.QtCore import QCoreApplication

from ball_speed import accelerate_ball_velocity, reset_ball_velocity
from constants import (
    BALL_MAX_SPEED,
    BALL_SPEED,
    BALL_SPEED_ACCELERATION,
    GameStatus,
    REWARD_TYPE_SLOW_BALL,
)
from game_logic_qml import GameController
from main_arcade import BreakoutGame


_APP = QCoreApplication.instance() or QCoreApplication([])


class BallSpeedTests(unittest.TestCase):
    def test_speed_ramp_preserves_direction_and_stops_at_the_cap(self):
        dx, dy = 180.0, -240.0
        accelerated = accelerate_ball_velocity(dx, dy, 10.0)

        self.assertAlmostEqual(
            math.hypot(*accelerated),
            BALL_SPEED + BALL_SPEED_ACCELERATION * 10,
        )
        self.assertAlmostEqual(accelerated[0] / accelerated[1], dx / dy)

        capped = accelerate_ball_velocity(*accelerated, 1000.0)
        self.assertAlmostEqual(math.hypot(*capped), BALL_MAX_SPEED)
        self.assertAlmostEqual(capped[0] / capped[1], dx / dy)

    def test_slow_ball_reward_resets_qml_speed_and_magnetic_release_speed(self):
        controller = GameController()
        controller.timer.stop()
        controller.state.gameStatus = GameStatus.PLAYING
        controller.ball.launch()
        controller.ball.update(10.0)
        self.assertGreater(
            math.hypot(controller.ball._dx, controller.ball._dy),
            BALL_SPEED,
        )

        direction = math.atan2(controller.ball._dy, controller.ball._dx)
        controller._apply_reward(REWARD_TYPE_SLOW_BALL)
        self.assertAlmostEqual(
            math.hypot(controller.ball._dx, controller.ball._dy),
            BALL_SPEED,
        )
        self.assertAlmostEqual(
            math.atan2(controller.ball._dy, controller.ball._dx),
            direction,
        )

        controller.ball._set_magnet_attached(True)
        controller.ball._magnet_speed = BALL_MAX_SPEED
        controller._apply_reward(REWARD_TYPE_SLOW_BALL)
        self.assertEqual(controller.ball._magnet_speed, BALL_SPEED)

    def test_slow_ball_reward_resets_arcade_speed(self):
        class ArcadeGameHarness:
            pass

        game = ArcadeGameHarness()
        game.apply_reward = MethodType(BreakoutGame.apply_reward, game)
        game.reset_ball_speed = MethodType(BreakoutGame.reset_ball_speed, game)
        game.ball = SimpleNamespace(change_x=360.0, change_y=-480.0)
        game.magnet_attached = False

        direction = math.atan2(game.ball.change_y, game.ball.change_x)
        game.apply_reward(REWARD_TYPE_SLOW_BALL)

        self.assertAlmostEqual(
            math.hypot(game.ball.change_x, game.ball.change_y),
            BALL_SPEED,
        )
        self.assertAlmostEqual(
            math.atan2(game.ball.change_y, game.ball.change_x),
            direction,
        )

        game.magnet_attached = True
        game.magnet_speed = BALL_MAX_SPEED
        game.apply_reward(REWARD_TYPE_SLOW_BALL)
        self.assertEqual(game.magnet_speed, BALL_SPEED)

    def test_zero_velocity_is_not_given_an_arbitrary_direction(self):
        self.assertEqual(reset_ball_velocity(0.0, 0.0), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
