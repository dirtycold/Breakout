import random
import unittest

from constants import (
    REWARD_MAX_GRAVITY,
    REWARD_MAX_SPEED_X,
    REWARD_MAX_SPEED_Y,
    REWARD_MAX_SPIN,
    REWARD_MIN_GRAVITY,
    REWARD_MIN_SPEED_Y,
    REWARD_MIN_SPIN,
    REWARD_SIZE,
)
from reward_visual import (
    create_fireball_reward_data_url,
    create_fireball_reward_image,
    create_reward_motion,
    should_spawn_reward,
)


class StubRandom:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


class RewardVisualTests(unittest.TestCase):
    def test_drop_roll_has_success_and_failure_boundaries(self):
        self.assertTrue(should_spawn_reward(StubRandom(0.0)))
        self.assertFalse(should_spawn_reward(StubRandom(1.0)))

    def test_motion_is_varied_and_stays_in_configured_ranges(self):
        motions = [create_reward_motion(200, random.Random(seed)) for seed in range(12)]

        self.assertGreater(len({round(motion.vx, 3) for motion in motions}), 1)
        self.assertGreater(len({round(motion.gravity, 3) for motion in motions}), 1)
        for motion in motions:
            self.assertLessEqual(abs(motion.vx), REWARD_MAX_SPEED_X)
            self.assertLessEqual(REWARD_MIN_SPEED_Y, motion.upward_speed)
            self.assertLessEqual(motion.upward_speed, REWARD_MAX_SPEED_Y)
            self.assertLessEqual(REWARD_MIN_GRAVITY, motion.gravity)
            self.assertLessEqual(motion.gravity, REWARD_MAX_GRAVITY)
            self.assertLessEqual(REWARD_MIN_SPIN, abs(motion.angular_velocity))
            self.assertLessEqual(abs(motion.angular_velocity), REWARD_MAX_SPIN)

    def test_fireball_texture_is_a_square_transparent_png(self):
        image = create_fireball_reward_image()

        self.assertEqual(image.size, (REWARD_SIZE, REWARD_SIZE))
        self.assertEqual(image.mode, "RGBA")
        self.assertTrue(create_fireball_reward_data_url().startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
