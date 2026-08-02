"""Shared ball-speed ramp and reset helpers."""

import math

from constants import BALL_MAX_SPEED, BALL_SPEED, BALL_SPEED_ACCELERATION


def set_velocity_speed(dx, dy, target_speed):
    """Preserve direction while changing a non-zero velocity's magnitude."""
    speed = math.hypot(dx, dy)
    if speed <= 1e-9:
        return dx, dy

    scale = target_speed / speed
    return dx * scale, dy * scale


def accelerate_ball_velocity(dx, dy, delta_time):
    """Apply the subtle time-based ramp without exceeding the speed ceiling."""
    speed = math.hypot(dx, dy)
    if speed <= 1e-9:
        return dx, dy

    target_speed = min(
        BALL_MAX_SPEED,
        speed + BALL_SPEED_ACCELERATION * max(0.0, delta_time),
    )
    return set_velocity_speed(dx, dy, target_speed)


def reset_ball_velocity(dx, dy):
    """Restore the initial playable speed while preserving direction."""
    return set_velocity_speed(dx, dy, BALL_SPEED)
