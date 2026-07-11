import unittest

from constants import BRICK_HEIGHT, BRICK_MARGIN, BRICK_WIDTH
from fireball_effect import inside_fireball_impact_area


class FireballImpactAreaTests(unittest.TestCase):
    def setUp(self):
        self.step_x = BRICK_WIDTH + BRICK_MARGIN
        self.step_y = BRICK_HEIGHT + BRICK_MARGIN

    def test_up_right_impact_is_limited_to_directional_two_by_two(self):
        allowed = {
            (0, 0),
            (self.step_x, 0),
            (0, self.step_y),
            (self.step_x, self.step_y),
        }
        samples = {
            *allowed,
            (self.step_x * 2, 0),
            (0, self.step_y * 2),
            (-self.step_x, 0),
            (0, -self.step_y),
        }

        actual = {
            point
            for point in samples
            if inside_fireball_impact_area(*point, 1, 1)
        }
        self.assertEqual(actual, allowed)

    def test_all_four_diagonal_directions_use_their_own_quadrant(self):
        for direction_x, direction_y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            with self.subTest(direction=(direction_x, direction_y)):
                self.assertTrue(inside_fireball_impact_area(
                    direction_x * self.step_x,
                    direction_y * self.step_y,
                    direction_x,
                    direction_y,
                ))
                self.assertFalse(inside_fireball_impact_area(
                    -direction_x * self.step_x,
                    direction_y * self.step_y,
                    direction_x,
                    direction_y,
                ))

    def test_axis_aligned_motion_does_not_expand_sideways(self):
        self.assertTrue(inside_fireball_impact_area(0, self.step_y, 0, 1))
        self.assertFalse(inside_fireball_impact_area(self.step_x, self.step_y, 0, 1))
        self.assertTrue(inside_fireball_impact_area(self.step_x, 0, 1, 0))
        self.assertFalse(inside_fireball_impact_area(self.step_x, self.step_y, 1, 0))


if __name__ == "__main__":
    unittest.main()
