"""Shared geometry helpers for the fireball's local brick impact area."""

import math

from constants import (
    BRICK_HEIGHT,
    BRICK_MARGIN,
    BRICK_WIDTH,
    FIREBALL_IMPACT_COLUMNS,
    FIREBALL_IMPACT_ROWS,
)


def _inside_directional_axis(offset, direction, reach, epsilon=1e-6):
    """Return whether an offset stays within one grid step in the travel direction."""
    if abs(direction) <= epsilon:
        return abs(offset) <= epsilon

    directed_offset = offset * math.copysign(1, direction)
    return -epsilon <= directed_offset <= reach + epsilon


def inside_fireball_impact_area(offset_x, offset_y, direction_x, direction_y):
    """Limit fireball damage to the source brick's directional 2x2 grid area."""
    return (
        _inside_directional_axis(
            offset_x,
            direction_x,
            (FIREBALL_IMPACT_COLUMNS - 1) * (BRICK_WIDTH + BRICK_MARGIN),
        )
        and _inside_directional_axis(
            offset_y,
            direction_y,
            (FIREBALL_IMPACT_ROWS - 1) * (BRICK_HEIGHT + BRICK_MARGIN),
        )
    )
