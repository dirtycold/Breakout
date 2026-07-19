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
    """Roll the shared drop chance, then choose from the weighted reward pool."""
    if rng.random() >= REWARD_TRIGGER_PROBABILITY:
        return None
    return rng.choices(REWARD_TYPES, weights=REWARD_WEIGHTS, k=1)[0]


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


@lru_cache(maxsize=4)
def create_reset_reward_image(size=REWARD_SIZE):
    """Draw a neutral circular reset arrow."""
    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_NEUTRAL_COLOR, 246),
        border=(*REWARD_NEUTRAL_BORDER_COLOR, 255),
    )
    accent = (226, 232, 240, 255)
    draw.arc(
        (8 * scale, 8 * scale, 30 * scale, 30 * scale),
        start=35,
        end=325,
        fill=accent,
        width=4 * scale,
    )
    draw.polygon(
        ((27 * scale, 5 * scale), (34 * scale, 9 * scale), (27 * scale, 14 * scale)),
        fill=accent,
    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def create_laser_reward_image(size=REWARD_SIZE):
    """Draw twin laser barrels and bright beams on a positive hint."""
    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_FIREBALL_COLOR, 246),
        border=(*REWARD_FIREBALL_BORDER_COLOR, 255),
    )
    metal = (226, 232, 240, 255)
    beam = (*LASER_BULLET_COLOR, 255)
    for center_x in (12, 26):
        draw.rounded_rectangle(
            ((center_x - 4) * scale, 19 * scale, (center_x + 4) * scale, 31 * scale),
            radius=2 * scale,
            fill=metal,
        )
        draw.rounded_rectangle(
            ((center_x - 1.5) * scale, 6 * scale, (center_x + 1.5) * scale, 22 * scale),
            radius=1 * scale,
            fill=beam,
        )
    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def create_magnet_reward_image(size=REWARD_SIZE):
    """Draw a bright horseshoe magnet on a positive green hint."""
    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_FIREBALL_COLOR, 246),
        border=(*REWARD_FIREBALL_BORDER_COLOR, 255),
    )

    # A thick horseshoe silhouette, with cyan pole caps to match the paddle arcs.
    magnet_red = (239, 68, 68, 255)
    magnet_shadow = (153, 27, 27, 255)
    pole = (*MAGNET_EFFECT_COLOR, 255)
    horseshoe = [
        (10 * scale, 10 * scale),
        (10 * scale, 21 * scale),
        (13 * scale, 27 * scale),
        (19 * scale, 30 * scale),
        (25 * scale, 27 * scale),
        (28 * scale, 21 * scale),
        (28 * scale, 10 * scale),
    ]
    draw.line(
        horseshoe,
        fill=magnet_shadow,
        width=11 * scale,
        joint="curve",
    )
    draw.line(
        horseshoe,
        fill=magnet_red,
        width=7 * scale,
        joint="curve",
    )
    draw.rounded_rectangle(
        (5 * scale, 6 * scale, 15 * scale, 13 * scale),
        radius=2 * scale,
        fill=pole,
    )
    draw.rounded_rectangle(
        (23 * scale, 6 * scale, 33 * scale, 13 * scale),
        radius=2 * scale,
        fill=pole,
    )
    draw.ellipse(
        (17 * scale, 17 * scale, 21 * scale, 21 * scale),
        fill=(224, 242, 254, 245),
    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def create_skull_reward_image(size=REWARD_SIZE):
    """Draw a compact white skull on a negative red hint."""
    image, draw, scale = _create_reward_canvas(
        size,
        background=(*REWARD_NEGATIVE_COLOR, 246),
        border=(*REWARD_NEGATIVE_BORDER_COLOR, 255),
    )
    bone = (248, 250, 252, 255)
    shadow = (71, 85, 105, 255)
    draw.ellipse((8 * scale, 6 * scale, 30 * scale, 28 * scale), fill=bone)
    draw.rectangle((12 * scale, 22 * scale, 26 * scale, 32 * scale), fill=bone)
    draw.ellipse((12 * scale, 13 * scale, 18 * scale, 20 * scale), fill=shadow)
    draw.ellipse((20 * scale, 13 * scale, 26 * scale, 20 * scale), fill=shadow)
    draw.polygon(
        ((19 * scale, 19 * scale), (16.5 * scale, 24 * scale), (21.5 * scale, 24 * scale)),
        fill=shadow,
    )
    for x in (15, 19, 23):
        draw.line((x * scale, 26 * scale, x * scale, 32 * scale), fill=shadow, width=1 * scale)
    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=12)
def create_reward_image(reward_type, size=REWARD_SIZE):
    if reward_type == REWARD_TYPE_FIREBALL:
        return create_fireball_reward_image(size)
    if reward_type in (REWARD_TYPE_EXTEND_PADDLE, REWARD_TYPE_SHRINK_PADDLE):
        return create_paddle_size_reward_image(reward_type, size)
    if reward_type == REWARD_TYPE_RESET:
        return create_reset_reward_image(size)
    if reward_type == REWARD_TYPE_LASER:
        return create_laser_reward_image(size)
    if reward_type == REWARD_TYPE_MAGNET:
        return create_magnet_reward_image(size)
    if reward_type == REWARD_TYPE_SKULL:
        return create_skull_reward_image(size)
    raise ValueError(f"Unsupported reward type: {reward_type}")


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
