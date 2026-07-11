"""
挡板纹理工具 / Paddle texture helpers
"""

import base64
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw

from constants import *


def paddle_fang_geometry(width=PADDLE_WIDTH):
    """Return fixed-size fang triangles centered across the current paddle width."""
    available_width = max(0, width - PADDLE_FANG_SIDE_INSET * 2)
    fang_count = max(1, int(available_width / PADDLE_FANG_WIDTH))
    occupied_width = fang_count * PADDLE_FANG_WIDTH
    start_x = (width - occupied_width) / 2

    return [
        (
            start_x + index * PADDLE_FANG_WIDTH,
            start_x + (index + 1) * PADDLE_FANG_WIDTH,
            start_x + (index + 0.5) * PADDLE_FANG_WIDTH,
        )
        for index in range(fang_count)
    ]


@lru_cache(maxsize=32)
def _create_paddle_assets(width, height, corner_radius):
    """Cache the expensive gradient, mask, and fixed-size fang layer per width."""
    scale = 4
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)

    gradient_row = Image.new("RGBA", (width, 1))
    gradient_row.putdata([
        (*gradient_color(x / max(1, width - 1)), 255)
        for x in range(width)
    ])
    gradient = gradient_row.resize((width, height))

    mask = Image.new("L", (scaled_width, scaled_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, scaled_width - 1, scaled_height - 1],
        radius=corner_radius * scale,
        fill=255,
    )

    fangs = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    fang_draw = ImageDraw.Draw(fangs)
    fang_height = PADDLE_FANG_HEIGHT * scale
    for base_left, base_right, tip_x in paddle_fang_geometry(width):
        fang_draw.polygon(
            [
                (base_left * scale, 0),
                (base_right * scale, 0),
                (tip_x * scale, fang_height),
            ],
            fill=COLOR_PADDLE_FANG,
            outline=COLOR_PADDLE_FANG_SHADOW,
        )

    mask = mask.resize((width, height), Image.Resampling.LANCZOS)
    fangs = fangs.resize((width, height), Image.Resampling.LANCZOS)
    return gradient, mask, fangs


def create_paddle_image(
    width=PADDLE_WIDTH,
    height=PADDLE_HEIGHT,
    corner_radius=PADDLE_CORNER_RADIUS,
    gradient_offset=0,
):
    """创建一帧彩虹尖牙挡板图像 / Create one rainbow fang paddle image frame."""
    width = int(width)
    height = int(height)
    gradient, mask, fangs = _create_paddle_assets(width, height, corner_radius)
    shifted_gradient = ImageChops.offset(gradient, int(round(gradient_offset)), 0)
    image = Image.new("RGBA", gradient.size, (0, 0, 0, 0))
    image.paste(shifted_gradient, (0, 0), mask)
    image.alpha_composite(fangs)

    return image


def gradient_color(position):
    """返回渐变位置对应颜色 / Return color for a gradient position."""
    position = max(0.0, min(1.0, position))

    for index in range(len(PADDLE_GRADIENT_STOPS) - 1):
        if position <= PADDLE_GRADIENT_STOPS[index + 1]:
            start_stop = PADDLE_GRADIENT_STOPS[index]
            end_stop = PADDLE_GRADIENT_STOPS[index + 1]
            blend = 0 if end_stop == start_stop else (position - start_stop) / (end_stop - start_stop)
            start = PADDLE_GRADIENT_COLORS[index]
            end = PADDLE_GRADIENT_COLORS[index + 1]
            return tuple(
                int(start[channel] + (end[channel] - start[channel]) * blend)
                for channel in range(3)
            )

    return PADDLE_GRADIENT_COLORS[-1]


@lru_cache(maxsize=4)
def create_paddle_sprite_sheet_data_url(
    width=PADDLE_WIDTH,
    height=PADDLE_HEIGHT,
    corner_radius=PADDLE_CORNER_RADIUS,
    frame_count=PADDLE_GRADIENT_FRAME_COUNT,
):
    """创建供 QML Image 使用的挡板动画帧图集 / Create a QML sprite-sheet data URL."""
    sheet = Image.new("RGBA", (int(width * frame_count), int(height)), (0, 0, 0, 0))

    for frame_index in range(frame_count):
        gradient_offset = width * frame_index / frame_count
        frame = create_paddle_image(width, height, corner_radius, gradient_offset)
        sheet.paste(frame, (int(width * frame_index), 0))

    output = BytesIO()
    # Fast compression keeps width changes within a frame budget; the data URL is cached.
    sheet.save(output, format="PNG", compress_level=1)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
