"""
挡板纹理工具 / Paddle texture helpers
"""

import base64
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw

from constants import *


def create_paddle_image(
    width=PADDLE_WIDTH,
    height=PADDLE_HEIGHT,
    corner_radius=PADDLE_CORNER_RADIUS,
    gradient_offset=0,
):
    """创建一帧彩虹尖牙挡板图像 / Create one rainbow fang paddle image frame."""
    scale = 4
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)

    image = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)

    for x in range(scaled_width):
        gradient_x = (x / scale - gradient_offset) % width
        color = gradient_color(gradient_x / max(1, width))
        gradient_draw.line([(x, 0), (x, scaled_height)], fill=(*color, 255))

    mask = Image.new("L", (scaled_width, scaled_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, scaled_width - 1, scaled_height - 1],
        radius=corner_radius * scale,
        fill=255,
    )
    image.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(image)
    fang_height = PADDLE_FANG_HEIGHT * scale
    fang_inset = PADDLE_FANG_SIDE_INSET * scale
    usable_width = scaled_width - fang_inset * 2
    fang_spacing = usable_width / PADDLE_FANG_COUNT

    for index in range(PADDLE_FANG_COUNT):
        base_left = fang_inset + index * fang_spacing
        base_right = fang_inset + (index + 1) * fang_spacing
        tip_x = (base_left + base_right) / 2

        draw.polygon(
            [
                (base_left, 0),
                (base_right, 0),
                (tip_x, fang_height),
            ],
            fill=COLOR_PADDLE_FANG,
            outline=COLOR_PADDLE_FANG_SHADOW,
        )

    return image.resize((int(width), int(height)), Image.Resampling.LANCZOS)


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
    sheet.save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
