"""Small Cocoa input adaptations for the Arcade frontend."""

import sys


def enable_first_mouse_for_game_view(platform=None, view_subclass=None):
    """Let the first click both activate the macOS window and reach the game."""
    platform = sys.platform if platform is None else platform
    if platform != "darwin":
        return False

    if view_subclass is None:
        from pyglet.window.cocoa.pyglet_view import PygletView_Implementation

        view_subclass = PygletView_Implementation.PygletView

    marker = "_breakout_accepts_first_mouse"
    if getattr(view_subclass, marker, False):
        return True

    @view_subclass.method("B@")
    def acceptsFirstMouse_(self, _event):
        return True

    setattr(view_subclass, marker, True)
    return True
