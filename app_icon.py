"""Shared application-icon loading for the Arcade and QML frontends."""

from pathlib import Path


APP_ICON_PATH = Path(__file__).resolve().parent / "assets" / "app_icon.png"


def set_arcade_window_icon(window):
    """Load the project PNG through Pyglet and apply it to an Arcade window."""
    if not APP_ICON_PATH.is_file():
        return False

    import pyglet

    window.set_icon(pyglet.image.load(str(APP_ICON_PATH)))
    return True


def set_qt_application_icon(application):
    """Load the project PNG as the default icon for every QML window."""
    if not APP_ICON_PATH.is_file():
        return False

    from qtpy.QtGui import QIcon

    application.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    return True
