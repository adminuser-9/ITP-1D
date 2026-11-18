import unittest

import mylibrary


class BaselineTests(unittest.TestCase):
    def test_original_assignment_example(self):
        self.assertEqual(mylibrary.calculate_total(2, 2), (20, 10))
        self.assertEqual(mylibrary.audio_guides(2), 6)
        self.assertEqual(sum(mylibrary.calculate_total(2, 2)) + mylibrary.audio_guides(2), 36)

    def test_empty_subtotals(self):
        self.assertEqual(mylibrary.calculate_total(0, 0), (0, 0))
        self.assertEqual(mylibrary.audio_guides(0), 0)

    def test_invalid_quantities(self):
        for value in (-1, True, 1.5, "2", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    mylibrary.calculate_total(value, 0)
                with self.assertRaises(ValueError):
                    mylibrary.calculate_total(0, value)
                with self.assertRaises(ValueError):
                    mylibrary.audio_guides(value)
