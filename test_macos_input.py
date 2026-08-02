import unittest

from macos_input import enable_first_mouse_for_game_view


class FakeViewSubclass:
    def __init__(self):
        self.registrations = []

    def method(self, encoding):
        def register(callback):
            self.registrations.append((encoding, callback))
            return callback

        return register


class MacOSInputTests(unittest.TestCase):
    def test_non_macos_platforms_are_untouched(self):
        view = FakeViewSubclass()

        self.assertFalse(
            enable_first_mouse_for_game_view("linux", view),
        )
        self.assertEqual(view.registrations, [])

    def test_macos_game_view_accepts_the_activation_click_once(self):
        view = FakeViewSubclass()

        self.assertTrue(enable_first_mouse_for_game_view("darwin", view))
        self.assertEqual(len(view.registrations), 1)
        encoding, callback = view.registrations[0]
        self.assertEqual(encoding, "B@")
        self.assertTrue(callback(None, None))

        self.assertTrue(enable_first_mouse_for_game_view("darwin", view))
        self.assertEqual(len(view.registrations), 1)


if __name__ == "__main__":
    unittest.main()
