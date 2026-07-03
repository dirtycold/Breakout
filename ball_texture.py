"""
彩虹球纹理与动画工具 / Rainbow ball texture and animation helpers
"""

import base64
import math
import random
from functools import lru_cache
from io import BytesIO

from PIL import Image

from constants import *


@lru_cache(maxsize=8)
def create_rainbow_ball_image(radius=BALL_RADIUS):
    """创建彩虹条纹球纹理 / Create rainbow striped ball texture."""
    scale = BALL_TEXTURE_SUPERSAMPLE
    diameter = int(radius * 2)
    size = diameter * scale
    center = (size - 1) / 2
    outer_radius = radius * scale
    stripe_width = BALL_STRIPE_WIDTH * scale
    edge_stripe_extra_width = BALL_EDGE_STRIPE_EXTRA_WIDTH * scale
    stripe_widths = [
        stripe_width + edge_stripe_extra_width,
        *([stripe_width] * (len(BALL_STRIPE_COLORS) - 2)),
        stripe_width + edge_stripe_extra_width,
    ]
    total_stripe_width = sum(stripe_widths)
    stripe_angle = math.radians(BALL_STRIPE_ANGLE)
    cos_angle = math.cos(stripe_angle)
    sin_angle = math.sin(stripe_angle)

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()

    for y in range(size):
        for x in range(size):
            px = x - center
            py = y - center
            distance = math.sqrt(px * px + py * py)

            if distance > outer_radius:
                continue

            local_x = px * cos_angle + py * sin_angle
            local_y = -px * sin_angle + py * cos_angle
            curved_x = local_x + BALL_STRIPE_CURVE * (local_y * local_y / outer_radius)
            stripe_coordinate = max(
                0,
                min(total_stripe_width - 1, (curved_x + outer_radius) / (outer_radius * 2) * total_stripe_width)
            )

            band_start = 0
            red, green, blue = BALL_STRIPE_COLORS[-1]
            for band_width, color in zip(stripe_widths, BALL_STRIPE_COLORS):
                if stripe_coordinate < band_start + band_width:
                    red, green, blue = color
                    break
                band_start += band_width

            edge_alpha = min(1.0, max(0.0, outer_radius - distance))
            alpha = int(255 * edge_alpha)
            pixels[x, y] = (red, green, blue, alpha)

    return image.resize((diameter, diameter), Image.Resampling.LANCZOS)


@lru_cache(maxsize=8)
def create_rainbow_ball_data_url(radius=BALL_RADIUS):
    """创建供 QML Image 使用的 PNG data URL / Create PNG data URL for QML Image."""
    output = BytesIO()
    create_rainbow_ball_image(radius).save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


class RainbowBallMotion:
    """连续变向的彩虹球旋转状态 / Smoothly changing rainbow ball rotation."""

    def __init__(self):
        self._random = random.Random()
        self.reset()

    def reset(self):
        """重置为随机初始角度和方向 / Reset to random rotation and direction."""
        self.rotation = self._random.uniform(0, 360)
        self.angular_velocity = self._random_target_velocity()
        self.target_angular_velocity = self.angular_velocity
        self.target_time_remaining = self._random_target_time()

    def update(self, delta_time):
        """更新旋转角度 / Update rotation."""
        self.target_time_remaining -= delta_time
        if self.target_time_remaining <= 0:
            self.target_angular_velocity = self._random_target_velocity()
            self.target_time_remaining = self._random_target_time()

        blend = min(1.0, BALL_ROTATION_SMOOTHING * delta_time)
        self.angular_velocity += (self.target_angular_velocity - self.angular_velocity) * blend
        self.rotation = (self.rotation + self.angular_velocity * delta_time) % 360
        return self.rotation

    def _random_target_velocity(self):
        speed = self._random.uniform(BALL_ROTATION_MIN_SPEED, BALL_ROTATION_MAX_SPEED)
        direction = -1 if self._random.random() < 0.5 else 1
        return speed * direction

    def _random_target_time(self):
        return self._random.uniform(BALL_ROTATION_TARGET_MIN_TIME, BALL_ROTATION_TARGET_MAX_TIME)
