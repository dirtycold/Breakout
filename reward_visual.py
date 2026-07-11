"""Programmatic reward artwork and randomized reward motion."""

import base64
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw

from constants import *


@dataclass(frozen=True)
class RewardMotion:
    vx: float
    upward_speed: float
    gravity: float
    angle: float
    angular_velocity: float


def should_spawn_reward(rng=random):
    """Return whether a destroyed brick drops a reward."""
    return rng.random() < REWARD_TRIGGER_PROBABILITY


def create_reward_motion(source_dx=0, rng=random):
    """Create a varied but catchable launch path for one reward block."""
    speed_x = rng.uniform(REWARD_MIN_SPEED_X, REWARD_MAX_SPEED_X)
    random_direction = rng.choice((-1, 1))
    source_direction = 0 if abs(source_dx) < 1e-6 else math.copysign(1, source_dx)
    vx = random_direction * speed_x + source_direction * REWARD_SOURCE_DIRECTION_BIAS
    vx = max(-REWARD_MAX_SPEED_X, min(REWARD_MAX_SPEED_X, vx))

    spin_direction = rng.choice((-1, 1))
    return RewardMotion(
        vx=vx,
        upward_speed=rng.uniform(REWARD_MIN_SPEED_Y, REWARD_MAX_SPEED_Y),
        gravity=rng.uniform(REWARD_MIN_GRAVITY, REWARD_MAX_GRAVITY),
        angle=rng.uniform(-12, 12),
        angular_velocity=spin_direction * rng.uniform(REWARD_MIN_SPIN, REWARD_MAX_SPIN),
    )


@lru_cache(maxsize=4)
def create_fireball_reward_image(size=REWARD_SIZE):
    """Draw a rounded reward block containing a fireball icon."""
    scale = REWARD_TEXTURE_SUPERSAMPLE
    side = int(size * scale)
    radius = REWARD_CORNER_RADIUS * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (1 * scale, 1 * scale, side - 1 * scale - 1, side - 1 * scale - 1),
        radius=radius,
        fill=(77, 18, 35, 246),
        outline=(251, 146, 60, 255),
        width=2 * scale,
    )

    # A diagonal flame with a round, bright fireball at its leading edge.
    draw.polygon(
        [
            (7 * scale, 29 * scale),
            (12 * scale, 14 * scale),
            (17 * scale, 19 * scale),
            (21 * scale, 8 * scale),
            (27 * scale, 21 * scale),
        ],
        fill=(239, 68, 68, 255),
    )
    draw.polygon(
        [
            (10 * scale, 29 * scale),
            (15 * scale, 18 * scale),
            (19 * scale, 23 * scale),
            (23 * scale, 14 * scale),
            (27 * scale, 25 * scale),
        ],
        fill=(249, 115, 22, 255),
    )
    draw.ellipse(
        (13 * scale, 13 * scale, 31 * scale, 31 * scale),
        fill=(249, 115, 22, 255),
        outline=(255, 214, 10, 255),
        width=2 * scale,
    )
    draw.ellipse(
        (18 * scale, 18 * scale, 27 * scale, 27 * scale),
        fill=(255, 235, 92, 255),
    )
    draw.ellipse(
        (20 * scale, 19 * scale, 23 * scale, 22 * scale),
        fill=(255, 255, 225, 235),
    )

    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def create_fireball_reward_data_url(size=REWARD_SIZE):
    """Return the generated reward artwork as an embeddable PNG URL."""
    output = BytesIO()
    create_fireball_reward_image(size).save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
