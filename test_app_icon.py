import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from app_icon import (
    APP_ICON_PATH,
    set_arcade_window_icon,
    set_qt_application_icon,
)


class AppIconTests(unittest.TestCase):
    def test_icon_is_a_large_square_transparent_png(self):
        with Image.open(APP_ICON_PATH) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.size, (1024, 1024))
            self.assertGreater(len(image.resize((32, 32)).getcolors(1024)), 32)
            alpha_histogram = image.getchannel("A").histogram()
            self.assertGreater(alpha_histogram[0], 0)
            self.assertGreater(alpha_histogram[255], 0)
            self.assertGreater(sum(alpha_histogram[1:255]), 0)
            for corner in ((0, 0), (1023, 0), (0, 1023), (1023, 1023)):
                self.assertEqual(image.getpixel(corner)[3], 0)

    def test_arcade_loader_passes_pyglet_image_to_window(self):
        class FakeWindow:
            icon = None

            def set_icon(self, icon):
                self.icon = icon

        window = FakeWindow()
        fake_icon = SimpleNamespace(width=1024, height=1024)
        fake_pyglet = SimpleNamespace(
            image=SimpleNamespace(load=lambda _path: fake_icon)
        )
        with patch.dict("sys.modules", {"pyglet": fake_pyglet}):
            self.assertTrue(set_arcade_window_icon(window))
        self.assertEqual((window.icon.width, window.icon.height), (1024, 1024))

    def test_qt_loader_passes_non_null_icon_to_application(self):
        class FakeApplication:
            icon = None

            def setWindowIcon(self, icon):
                self.icon = icon

        application = FakeApplication()
        fake_icon = object()
        fake_qt_gui = SimpleNamespace(QIcon=lambda _path: fake_icon)
        with patch.dict("sys.modules", {"qtpy.QtGui": fake_qt_gui}):
            self.assertTrue(set_qt_application_icon(application))
        self.assertIs(application.icon, fake_icon)


if __name__ == "__main__":
    unittest.main()
