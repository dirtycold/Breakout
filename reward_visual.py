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


def choose_reward_type(rng=random):
    """Roll the shared drop chance, then choose each reward type uniformly."""
    if rng.random() >= REWARD_TRIGGER_PROBABILITY:
        return None
    return rng.choice(REWARD_TYPES)


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


def _create_reward_canvas(size, background, border):
    scale = REWARD_TEXTURE_SUPERSAMPLE
    side = int(size * scale)
    radius = REWARD_CORNER_RADIUS * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (1 * scale, 1 * scale, side - 1 * scale - 1, side - 1 * scale - 1),
        radius=radius,
        fill=background,
        outline=border,
        width=2 * scale,
    )
    return image, draw, scale


@lru_cache(maxsize=4)
def create_fireball_reward_image(size=REWARD_SIZE):
    """Draw a green-hinted reward block containing a fireball icon."""
    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_FIREBALL_COLOR, 246),
        border=(*REWARD_FIREBALL_BORDER_COLOR, 255),
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


@lru_cache(maxsize=8)
def create_paddle_size_reward_image(reward_type, size=REWARD_SIZE):
    """Draw prominent colored direction triangles on a neutral block."""
    if reward_type not in (REWARD_TYPE_EXTEND_PADDLE, REWARD_TYPE_SHRINK_PADDLE):
        raise ValueError(f"Unsupported paddle reward type: {reward_type}")

    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_NEUTRAL_COLOR, 246),
        border=(*REWARD_NEUTRAL_BORDER_COLOR, 255),
    )
    if reward_type == REWARD_TYPE_EXTEND_PADDLE:
        accent = (59, 130, 246, 255)
        draw.polygon(
            ((4 * scale, 19 * scale), (16 * scale, 8 * scale), (16 * scale, 30 * scale)),
            fill=accent,
        )
        draw.polygon(
            ((34 * scale, 19 * scale), (22 * scale, 8 * scale), (22 * scale, 30 * scale)),
            fill=accent,
        )
    else:
        accent = (239, 68, 68, 255)
        draw.polygon(
            ((17 * scale, 19 * scale), (5 * scale, 8 * scale), (5 * scale, 30 * scale)),
            fill=accent,
        )
        draw.polygon(
            ((21 * scale, 19 * scale), (33 * scale, 8 * scale), (33 * scale, 30 * scale)),
            fill=accent,
        )

    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=12)
def create_reward_image(reward_type, size=REWARD_SIZE):
    if reward_type == REWARD_TYPE_FIREBALL:
        return create_fireball_reward_image(size)
    return create_paddle_size_reward_image(reward_type, size)


@lru_cache(maxsize=12)
def create_reward_data_url(reward_type, size=REWARD_SIZE):
    """Return generated reward artwork as an embeddable PNG URL."""
    output = BytesIO()
    create_reward_image(reward_type, size).save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def create_fireball_reward_data_url(size=REWARD_SIZE):
    """Compatibility wrapper for the fireball reward texture."""
    return create_reward_data_url(REWARD_TYPE_FIREBALL, size)
