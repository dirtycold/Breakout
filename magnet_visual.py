"""Programmatic electromagnetic artwork shared by the QML and Arcade frontends."""

import base64
import math
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

from constants import (
    BALL_PADDLE_GAP,
    BALL_RADIUS,
    MAGNET_EFFECT_COLOR,
    MAGNET_EFFECT_DECK_Y,
    MAGNET_EFFECT_FRAME_COUNT,
    MAGNET_EFFECT_HEIGHT,
    MAGNET_EFFECT_WIDTH,
)

MAGNET_ELECTRODE_HALF_WIDTH = 6
MAGNET_ELECTRODE_GLOW_HALF_WIDTH = 9
MAGNET_ELECTRODE_SIDE_MARGIN = 2
MAGNET_ELECTRODE_DESIRED_HALF_GAP = 19
MAGNET_BALL_OFFSET_QUANTUM = 2
MAGNET_SIDE_MOUNT_THRESHOLD = 8
MAGNET_SIDE_ELECTRODE_DEPTH = 13


@dataclass(frozen=True)
class MagnetEffectLayout:
    """Positions relative to the paddle and the fixed-size effect canvas."""

    center_offset: float
    ball_art_offset: float
    electrode_half_gap: float
    side_mount: int
    side_electrode_x: float


def magnet_effect_layout(paddle_width, ball_offset):
    """Keep fixed-size electrodes inside the paddle without moving the ball."""
    side_margin = min(
        MAGNET_ELECTRODE_SIDE_MARGIN,
        max(0.0, paddle_width / 2 - MAGNET_ELECTRODE_GLOW_HALF_WIDTH),
    )
    half_gap = min(
        MAGNET_ELECTRODE_DESIRED_HALF_GAP,
        max(
            0.0,
            paddle_width / 2
            - side_margin
            - MAGNET_ELECTRODE_GLOW_HALF_WIDTH,
        ),
    )
    outer_extent = (
        half_gap
        + MAGNET_ELECTRODE_GLOW_HALF_WIDTH
        + side_margin
    )
    ball_from_left = paddle_width / 2 + ball_offset
    pair_center_from_left = max(
        outer_extent,
        min(paddle_width - outer_extent, ball_from_left),
    )
    center_offset = pair_center_from_left - paddle_width / 2
    exact_ball_art_offset = ball_offset - center_offset
    ball_art_offset = round(
        exact_ball_art_offset / MAGNET_BALL_OFFSET_QUANTUM
    ) * MAGNET_BALL_OFFSET_QUANTUM
    side_mount = 0
    if exact_ball_art_offset < -MAGNET_SIDE_MOUNT_THRESHOLD:
        side_mount = -1
    elif exact_ball_art_offset > MAGNET_SIDE_MOUNT_THRESHOLD:
        side_mount = 1

    if side_mount < 0:
        side_electrode_x = (
            MAGNET_EFFECT_WIDTH / 2
            - (paddle_width / 2 + center_offset)
        )
    elif side_mount > 0:
        side_electrode_x = (
            MAGNET_EFFECT_WIDTH / 2
            + (paddle_width / 2 - center_offset)
        )
    else:
        side_electrode_x = MAGNET_EFFECT_WIDTH / 2

    return MagnetEffectLayout(
        center_offset=center_offset,
        ball_art_offset=ball_art_offset,
        electrode_half_gap=half_gap,
        side_mount=side_mount,
        side_electrode_x=side_electrode_x,
    )


@lru_cache(maxsize=64)
def create_magnet_effect_frames(
    width=MAGNET_EFFECT_WIDTH,
    height=MAGNET_EFFECT_HEIGHT,
    frame_count=MAGNET_EFFECT_FRAME_COUNT,
    ball_offset=0,
    electrode_half_gap=MAGNET_ELECTRODE_DESIRED_HALF_GAP,
    side_mount=0,
    side_electrode_x=MAGNET_EFFECT_WIDTH / 2,
):
    """Create electric arcs whose fixed electrodes can point to an offset ball."""
    scale = 3
    frames = []

    for frame_index in range(frame_count):
        phase = frame_index / frame_count
        side = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        glow = Image.new("RGBA", side.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(side)
        glow_draw = ImageDraw.Draw(glow)

        center_x = width / 2
        ball_x = center_x + ball_offset
        ball_y = MAGNET_EFFECT_DECK_Y - BALL_RADIUS - BALL_PADDLE_GAP
        deck_y = MAGNET_EFFECT_DECK_Y
        pulse = 0.5 + 0.5 * math.sin(phase * math.tau)

        # Glowing induction pads sit directly on the paddle.
        for direction in (-1, 1):
            pad_x = center_x + direction * electrode_half_gap
            if direction == side_mount:
                inward = -direction
                side_center_x = (
                    side_electrode_x
                    + inward * MAGNET_ELECTRODE_HALF_WIDTH / 2
                )
                glow_draw.rounded_rectangle(
                    (
                        (
                            side_center_x
                            - MAGNET_ELECTRODE_GLOW_HALF_WIDTH / 2
                            - pulse
                        ) * scale,
                        (deck_y - 3 - pulse) * scale,
                        (
                            side_center_x
                            + MAGNET_ELECTRODE_GLOW_HALF_WIDTH / 2
                            + pulse
                        ) * scale,
                        (
                            deck_y
                            + MAGNET_SIDE_ELECTRODE_DEPTH
                            + pulse
                        ) * scale,
                    ),
                    radius=3 * scale,
                    fill=(*MAGNET_EFFECT_COLOR, 110),
                )
                draw.rounded_rectangle(
                    (
                        (
                            side_center_x
                            - MAGNET_ELECTRODE_HALF_WIDTH / 2
                        ) * scale,
                        (deck_y - 1) * scale,
                        (
                            side_center_x
                            + MAGNET_ELECTRODE_HALF_WIDTH / 2
                        ) * scale,
                        (
                            deck_y
                            + MAGNET_SIDE_ELECTRODE_DEPTH
                        ) * scale,
                    ),
                    radius=2 * scale,
                    fill=(*MAGNET_EFFECT_COLOR, 235),
                )
                continue

            glow_draw.ellipse(
                (
                    (
                        pad_x
                        - MAGNET_ELECTRODE_HALF_WIDTH
                        - 1
                        - pulse * 2
                    ) * scale,
                    (deck_y - 5 - pulse) * scale,
                    (
                        pad_x
                        + MAGNET_ELECTRODE_HALF_WIDTH
                        + 1
                        + pulse * 2
                    ) * scale,
                    (deck_y + 3 + pulse) * scale,
                ),
                fill=(*MAGNET_EFFECT_COLOR, 90),
            )
            draw.rounded_rectangle(
                (
                    (pad_x - MAGNET_ELECTRODE_HALF_WIDTH) * scale,
                    (deck_y - 3) * scale,
                    (pad_x + MAGNET_ELECTRODE_HALF_WIDTH) * scale,
                    (deck_y + 1) * scale,
                ),
                radius=2 * scale,
                fill=(*MAGNET_EFFECT_COLOR, 225),
            )

        # Two phase-shifting lightning paths connect the pads to the captured ball.
        jitter = (phase * frame_count) % 2
        for direction in (-1, 1):
            if direction == side_mount:
                pad_x = (
                    side_electrode_x
                    - direction * MAGNET_ELECTRODE_HALF_WIDTH / 2
                )
                pad_y = deck_y + 2
            else:
                pad_x = center_x + direction * electrode_half_gap
                pad_y = deck_y - 3
            points = [
                (pad_x, pad_y),
                (
                    pad_x * 0.68
                    + ball_x * 0.32
                    + direction * (1 + 2 * jitter),
                    31,
                ),
                (
                    pad_x * 0.35
                    + ball_x * 0.65
                    - direction * (2 * jitter),
                    27,
                ),
                (ball_x + direction * 5, ball_y + 3),
            ]
            scaled_points = [(x * scale, y * scale) for x, y in points]
            glow_draw.line(
                scaled_points,
                fill=(*MAGNET_EFFECT_COLOR, 150),
                width=5 * scale,
                joint="curve",
            )
            draw.line(
                scaled_points,
                fill=(224, 242, 254, 245),
                width=4,
                joint="curve",
            )

        glow = glow.filter(ImageFilter.GaussianBlur(3 * scale))
        side = Image.alpha_composite(glow, side)
        frames.append(
            side.resize((width, height), Image.Resampling.LANCZOS)
        )

    return tuple(frames)


@lru_cache(maxsize=64)
def create_magnet_effect_sprite_sheet_data_url(
    width=MAGNET_EFFECT_WIDTH,
    height=MAGNET_EFFECT_HEIGHT,
    frame_count=MAGNET_EFFECT_FRAME_COUNT,
    ball_offset=0,
    electrode_half_gap=MAGNET_ELECTRODE_DESIRED_HALF_GAP,
    side_mount=0,
    side_electrode_x=MAGNET_EFFECT_WIDTH / 2,
):
    """Return all electromagnetic frames as one QML-friendly PNG sprite sheet."""
    frames = create_magnet_effect_frames(
        width,
        height,
        frame_count,
        ball_offset,
        electrode_half_gap,
        side_mount,
        side_electrode_x,
    )
    sheet = Image.new("RGBA", (width * frame_count, height), (0, 0, 0, 0))
    for frame_index, frame in enumerate(frames):
        sheet.paste(frame, (frame_index * width, 0), frame)

    output = BytesIO()
    sheet.save(output, format="PNG", compress_level=1)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
