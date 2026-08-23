"""Shared fixed-aspect game-canvas geometry."""

from dataclasses import dataclass

from constants import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass(frozen=True)
class CanvasViewport:
    x: float
    y: float
    width: float
    height: float
    scale: float

    def contains(self, screen_x, screen_y):
        return (
            self.x <= screen_x <= self.x + self.width
            and self.y <= screen_y <= self.y + self.height
        )

    def to_game(self, screen_x, screen_y):
        if not self.contains(screen_x, screen_y):
            return None
        return (
            (screen_x - self.x) / self.scale,
            (screen_y - self.y) / self.scale,
        )


def game_canvas_viewport(
    window_width,
    window_height,
    game_width=SCREEN_WIDTH,
    game_height=SCREEN_HEIGHT,
):
    """Return a centered, aspect-preserving viewport for the logical game."""
    if window_width <= 0 or window_height <= 0:
        return CanvasViewport(0, 0, 0, 0, 1.0)

    scale = min(window_width / game_width, window_height / game_height)
    width = game_width * scale
    height = game_height * scale
    return CanvasViewport(
        x=(window_width - width) / 2,
        y=(window_height - height) / 2,
        width=width,
        height=height,
        scale=scale,
    )
