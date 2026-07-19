"""Programmatic electromagnetic artwork shared by the QML and Arcade frontends."""

import base64
import math
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

from constants import (
    MAGNET_EFFECT_COLOR,
    MAGNET_EFFECT_FRAME_COUNT,
    MAGNET_EFFECT_HEIGHT,
    MAGNET_EFFECT_SECONDARY_COLOR,
    MAGNET_EFFECT_WIDTH,
)


@lru_cache(maxsize=2)
def create_magnet_effect_frames(
    width=MAGNET_EFFECT_WIDTH,
    height=MAGNET_EFFECT_HEIGHT,
    frame_count=MAGNET_EFFECT_FRAME_COUNT,
):
    """Create a short loop of coils and electrical arcs around an attached ball."""
    scale = 3
    frames = []

    for frame_index in range(frame_count):
        phase = frame_index / frame_count
        side = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        glow = Image.new("RGBA", side.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(side)
        glow_draw = ImageDraw.Draw(glow)

        center_x = width / 2
        ball_y = 25
        deck_y = height - 5
        pulse = 0.5 + 0.5 * math.sin(phase * math.tau)

        # Glowing induction pads sit directly on the paddle.
        for pad_x in (17, width - 17):
            glow_draw.ellipse(
                (
                    (pad_x - 7 - pulse * 2) * scale,
                    (deck_y - 5 - pulse) * scale,
                    (pad_x + 7 + pulse * 2) * scale,
                    (deck_y + 3 + pulse) * scale,
                ),
                fill=(*MAGNET_EFFECT_COLOR, 90),
            )
            draw.rounded_rectangle(
                (
                    (pad_x - 6) * scale,
                    (deck_y - 3) * scale,
                    (pad_x + 6) * scale,
                    (deck_y + 1) * scale,
                ),
                radius=2 * scale,
                fill=(*MAGNET_EFFECT_COLOR, 225),
            )

        # Alternating field lines make the captured state legible without hiding the ball.
        for radius_index in range(3):
            radius = 16 + radius_index * 5 + pulse * 2
            alpha = 205 - radius_index * 48
            arc_box = (
                (center_x - radius) * scale,
                (ball_y - radius * 0.48) * scale,
                (center_x + radius) * scale,
                (ball_y + radius * 1.10) * scale,
            )
            start = 18 + phase * 28 + radius_index * 8
            draw.arc(
                arc_box,
                start=start,
                end=80 + phase * 20,
                fill=(*MAGNET_EFFECT_SECONDARY_COLOR, alpha),
                width=1 * scale,
            )
            draw.arc(
                arc_box,
                start=100 - phase * 20,
                end=162 - phase * 28 - radius_index * 8,
                fill=(*MAGNET_EFFECT_COLOR, alpha),
                width=1 * scale,
            )

        # Two phase-shifting lightning paths connect the pads to the captured ball.
        jitter = (phase * frame_count) % 2
        for direction in (-1, 1):
            pad_x = center_x + direction * 19
            points = [
                (pad_x, deck_y - 3),
                (center_x + direction * (15 + 2 * jitter), 29),
                (center_x + direction * (11 - 2 * jitter), 24),
                (center_x + direction * 8, 19),
            ]
            scaled_points = [(x * scale, y * scale) for x, y in points]
            glow_draw.line(
                scaled_points,
                fill=(*MAGNET_EFFECT_COLOR, 150),
                width=4 * scale,
                joint="curve",
            )
            draw.line(
                scaled_points,
                fill=(224, 242, 254, 245),
                width=1 * scale,
                joint="curve",
            )

        glow = glow.filter(ImageFilter.GaussianBlur(3 * scale))
        side = Image.alpha_composite(glow, side)
        frames.append(
            side.resize((width, height), Image.Resampling.LANCZOS)
        )

    return tuple(frames)


@lru_cache(maxsize=2)
def create_magnet_effect_sprite_sheet_data_url(
    width=MAGNET_EFFECT_WIDTH,
    height=MAGNET_EFFECT_HEIGHT,
    frame_count=MAGNET_EFFECT_FRAME_COUNT,
):
    """Return all electromagnetic frames as one QML-friendly PNG sprite sheet."""
    frames = create_magnet_effect_frames(width, height, frame_count)
    sheet = Image.new("RGBA", (width * frame_count, height), (0, 0, 0, 0))
    for frame_index, frame in enumerate(frames):
        sheet.paste(frame, (frame_index * width, 0), frame)

    output = BytesIO()
    sheet.save(output, format="PNG", compress_level=1)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
