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
    REWARD_TRIGGER_PROBABILITY,
    REWARD_TYPES,
    REWARD_WEIGHTS,
    REWARD_TYPE_EXTEND_PADDLE,
    REWARD_TYPE_FIREBALL,
    REWARD_TYPE_SHRINK_PADDLE,
    REWARD_TYPE_SKULL,
)
from reward_visual import (
    choose_reward_type,
    create_fireball_reward_data_url,
    create_fireball_reward_image,
    create_paddle_size_reward_image,
    create_reward_data_url,
    create_reward_image,
    create_reward_motion,
)


class StubRandom:
    def __init__(self, value, choice_value=REWARD_TYPE_FIREBALL):
        self.value = value
        self.choice_value = choice_value

    def random(self):
        return self.value

    def choice(self, values):
        return self.choice_value

    def choices(self, values, weights, k):
        assert tuple(values) == REWARD_TYPES
        assert tuple(weights) == REWARD_WEIGHTS
        assert k == 1
        return [self.choice_value]


class RewardVisualTests(unittest.TestCase):
    def test_drop_roll_uses_shared_probability_then_weighted_type_pool(self):
        self.assertEqual(REWARD_TRIGGER_PROBABILITY, 0.5)
        self.assertIsNone(choose_reward_type(StubRandom(REWARD_TRIGGER_PROBABILITY)))
        for reward_type in REWARD_TYPES:
            self.assertEqual(
                choose_reward_type(StubRandom(0.0, reward_type)),
                reward_type,
            )
        skull_weight = REWARD_WEIGHTS[REWARD_TYPES.index(REWARD_TYPE_SKULL)]
        for reward_type, weight in zip(REWARD_TYPES, REWARD_WEIGHTS):
            if reward_type != REWARD_TYPE_SKULL:
                self.assertEqual(weight, skull_weight * 2)

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

    def test_reward_color_hints_and_neutral_paddle_icons(self):
        fireball = create_fireball_reward_image()
        extend = create_paddle_size_reward_image(REWARD_TYPE_EXTEND_PADDLE)
        shrink = create_paddle_size_reward_image(REWARD_TYPE_SHRINK_PADDLE)

        fireball_hint = fireball.getpixel((REWARD_SIZE // 2, 5))
        neutral_hint = extend.getpixel((REWARD_SIZE // 2, 5))
        extend_triangle = extend.getpixel((10, REWARD_SIZE // 2))
        shrink_triangle = shrink.getpixel((10, REWARD_SIZE // 2))
        extend_center = extend.getpixel((REWARD_SIZE // 2, REWARD_SIZE // 2))
        self.assertGreater(fireball_hint[1], fireball_hint[0])
        self.assertLess(max(neutral_hint[:3]) - min(neutral_hint[:3]), 35)
        self.assertEqual(max(extend_triangle[:3]), extend_triangle[2])
        self.assertEqual(max(shrink_triangle[:3]), shrink_triangle[0])
        self.assertLessEqual(
            max(abs(center - hint) for center, hint in zip(extend_center, neutral_hint)),
            2,
        )
        self.assertNotEqual(extend.tobytes(), shrink.tobytes())
        self.assertTrue(
            create_reward_data_url(REWARD_TYPE_SHRINK_PADDLE).startswith("data:image/png;base64,")
        )
        for reward_type in REWARD_TYPES:
            self.assertEqual(create_reward_image(reward_type).size, (REWARD_SIZE, REWARD_SIZE))


if __name__ == "__main__":
    unittest.main()
