import unittest
import math
from a11y_checker.contrast import (
    parse_color,
    relative_luminance,
    contrast_ratio,
    meets_aa,
    meets_aaa,
    classify_contrast_level,
    parse_simple_css,
)


class TestContrast(unittest.TestCase):
    def test_parse_color_hex(self):
        self.assertEqual(parse_color("#000000"), (0, 0, 0, 1.0))
        self.assertEqual(parse_color("#ffffff"), (255, 255, 255, 1.0))
        self.assertEqual(parse_color("#ff0000"), (255, 0, 0, 1.0))
        self.assertEqual(parse_color("#0f0"), (0, 255, 0, 1.0))
        self.assertEqual(parse_color("f00"), (255, 0, 0, 1.0))

    def test_parse_color_named(self):
        self.assertEqual(parse_color("black"), (0, 0, 0, 1.0))
        self.assertEqual(parse_color("white"), (255, 255, 255, 1.0))
        self.assertEqual(parse_color("red"), (255, 0, 0, 1.0))

    def test_parse_color_rgb(self):
        self.assertEqual(parse_color("rgb(255, 0, 0)"), (255, 0, 0, 1.0))
        self.assertEqual(parse_color("rgba(255, 0, 0, 0.5)"), (255, 0, 0, 0.5))
        self.assertEqual(parse_color("rgb(0, 0, 0)"), (0, 0, 0, 1.0))

    def test_parse_color_invalid(self):
        self.assertIsNone(parse_color(""))
        self.assertIsNone(parse_color("transparent"))
        self.assertIsNone(parse_color("inherit"))
        self.assertIsNone(parse_color("notacolor"))

    def test_relative_luminance_black(self):
        self.assertAlmostEqual(relative_luminance(0, 0, 0), 0.0, places=6)

    def test_relative_luminance_white(self):
        self.assertAlmostEqual(relative_luminance(255, 255, 255), 1.0, places=2)

    def test_relative_luminance_red(self):
        lum = relative_luminance(255, 0, 0)
        self.assertGreater(lum, 0.2)
        self.assertLess(lum, 0.22)

    def test_contrast_ratio_black_white(self):
        black = (0, 0, 0, 1.0)
        white = (255, 255, 255, 1.0)
        ratio = contrast_ratio(black, white)
        self.assertAlmostEqual(ratio, 21.0, places=1)

    def test_contrast_ratio_same_color(self):
        color = (128, 128, 128, 1.0)
        ratio = contrast_ratio(color, color)
        self.assertAlmostEqual(ratio, 1.0, places=6)

    def test_contrast_ratio_known_value(self):
        white = (255, 255, 255, 1.0)
        dark_gray = (128, 128, 128, 1.0)
        ratio = contrast_ratio(white, dark_gray)
        self.assertGreater(ratio, 3.0)
        self.assertLess(ratio, 5.0)

    def test_meets_aa_normal_text(self):
        self.assertTrue(meets_aa(4.5))
        self.assertTrue(meets_aa(7.0))
        self.assertFalse(meets_aa(4.4))
        self.assertFalse(meets_aa(3.0))

    def test_meets_aa_large_text(self):
        self.assertTrue(meets_aa(3.0, is_large_text=True))
        self.assertFalse(meets_aa(2.9, is_large_text=True))
        self.assertTrue(meets_aa(4.5, is_large_text=True))

    def test_meets_aaa_normal_text(self):
        self.assertTrue(meets_aaa(7.0))
        self.assertFalse(meets_aaa(6.9))

    def test_meets_aaa_large_text(self):
        self.assertTrue(meets_aaa(4.5, is_large_text=True))
        self.assertFalse(meets_aaa(4.4, is_large_text=True))

    def test_classify_contrast_level(self):
        self.assertEqual(classify_contrast_level(10.0), "AAA")
        self.assertEqual(classify_contrast_level(5.0), "AA")
        self.assertEqual(classify_contrast_level(2.0), "fail")
        self.assertEqual(classify_contrast_level(5.0, is_large_text=True), "AAA")
        self.assertEqual(classify_contrast_level(3.5, is_large_text=True), "AA")
        self.assertEqual(classify_contrast_level(2.5, is_large_text=True), "fail")

    def test_parse_simple_css(self):
        css = """
        body {
            color: #333;
            background: white;
        }
        .highlight {
            color: red;
            font-weight: bold;
        }
        """
        styles = parse_simple_css(css)
        self.assertIn("body", styles)
        self.assertEqual(styles["body"]["color"], "#333")
        self.assertEqual(styles["body"]["background"], "white")
        self.assertIn(".highlight", styles)
        self.assertEqual(styles[".highlight"]["color"], "red")

    def test_parse_simple_css_comments(self):
        css = """
        /* This is a comment */
        p {
            color: blue; /* inline comment */
        }
        """
        styles = parse_simple_css(css)
        self.assertIn("p", styles)
        self.assertEqual(styles["p"]["color"], "blue")


if __name__ == "__main__":
    unittest.main()
