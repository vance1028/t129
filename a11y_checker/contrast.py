from __future__ import annotations

import re
from typing import Tuple, Optional, Dict, List


_NAMED_COLORS: Dict[str, str] = {
    "black": "#000000",
    "white": "#FFFFFF",
    "red": "#FF0000",
    "lime": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "aqua": "#00FFFF",
    "magenta": "#FF00FF",
    "fuchsia": "#FF00FF",
    "silver": "#C0C0C0",
    "gray": "#808080",
    "maroon": "#800000",
    "olive": "#808000",
    "green": "#008000",
    "purple": "#800080",
    "teal": "#008080",
    "navy": "#000080",
    "orange": "#FFA500",
    "transparent": "transparent",
}


def parse_color(color_str: str) -> Optional[Tuple[int, int, int, float]]:
    if not color_str:
        return None
    color_str = color_str.strip().lower()
    if not color_str or color_str == "transparent" or color_str == "inherit":
        return None

    if color_str in _NAMED_COLORS:
        color_str = _NAMED_COLORS[color_str]

    hex_match = re.match(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", color_str)
    if hex_match:
        hex_val = hex_match.group(1)
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)
        return (r, g, b, 1.0)

    rgba_match = re.match(
        r"^rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)$",
        color_str,
    )
    if rgba_match:
        r = min(255, max(0, int(rgba_match.group(1))))
        g = min(255, max(0, int(rgba_match.group(2))))
        b = min(255, max(0, int(rgba_match.group(3))))
        a_str = rgba_match.group(4)
        a = float(a_str) if a_str else 1.0
        a = min(1.0, max(0.0, a))
        return (r, g, b, a)

    return None


def _srgb_to_linear(c: float) -> float:
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(r: int, g: int, b: int) -> float:
    rs = r / 255.0
    gs = g / 255.0
    bs = b / 255.0
    rl = _srgb_to_linear(rs)
    gl = _srgb_to_linear(gs)
    bl = _srgb_to_linear(bs)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def contrast_ratio(
    color1: Tuple[int, int, int, float],
    color2: Tuple[int, int, int, float],
    bg_color: Tuple[int, int, int, float] = (255, 255, 255, 1.0),
) -> float:
    c1 = _flatten_alpha(color1, bg_color)
    c2 = _flatten_alpha(color2, bg_color)
    l1 = relative_luminance(c1[0], c1[1], c1[2])
    l2 = relative_luminance(c2[0], c2[1], c2[2])
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _flatten_alpha(
    fg: Tuple[int, int, int, float],
    bg: Tuple[int, int, int, float],
) -> Tuple[int, int, int, float]:
    alpha = fg[3]
    if alpha >= 1.0:
        return (fg[0], fg[1], fg[2], 1.0)
    r = int(fg[0] * alpha + bg[0] * (1 - alpha))
    g = int(fg[1] * alpha + bg[1] * (1 - alpha))
    b = int(fg[2] * alpha + bg[2] * (1 - alpha))
    return (r, g, b, 1.0)


def meets_aa(ratio: float, is_large_text: bool = False) -> bool:
    threshold = 3.0 if is_large_text else 4.5
    return ratio >= threshold


def meets_aaa(ratio: float, is_large_text: bool = False) -> bool:
    threshold = 4.5 if is_large_text else 7.0
    return ratio >= threshold


def classify_contrast_level(ratio: float, is_large_text: bool = False) -> str:
    if meets_aaa(ratio, is_large_text):
        return "AAA"
    if meets_aa(ratio, is_large_text):
        return "AA"
    return "fail"


def parse_simple_css(css_text: str) -> Dict[str, Dict[str, str]]:
    styles: Dict[str, Dict[str, str]] = {}
    css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)

    pattern = re.compile(r"([^{]+)\s*\{([^}]*)\}", re.DOTALL)
    for match in pattern.finditer(css_text):
        selector = match.group(1).strip()
        declarations = match.group(2).strip()
        props: Dict[str, str] = {}
        for decl in declarations.split(";"):
            decl = decl.strip()
            if not decl:
                continue
            if ":" in decl:
                prop, value = decl.split(":", 1)
                props[prop.strip().lower()] = value.strip()
        if selector:
            for sel in selector.split(","):
                sel = sel.strip()
                if sel:
                    styles[sel] = props
    return styles


def get_element_styles(
    element,
    css_styles: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, str]:
    styles: Dict[str, str] = {}
    if css_styles is not None:
        tag_name = element.name.lower() if element.name else ""
        if tag_name and tag_name in css_styles:
            styles.update(css_styles[tag_name])
        classes = element.get("class", [])
        if isinstance(classes, str):
            classes = [classes]
        for cls in classes:
            class_sel = f".{cls}"
            if class_sel in css_styles:
                styles.update(css_styles[class_sel])
        elem_id = element.get("id")
        if elem_id:
            id_sel = f"#{elem_id}"
            if id_sel in css_styles:
                styles.update(css_styles[id_sel])

    style_attr = element.get("style", "")
    if style_attr:
        for decl in style_attr.split(";"):
            decl = decl.strip()
            if not decl:
                continue
            if ":" in decl:
                prop, value = decl.split(":", 1)
                styles[prop.strip().lower()] = value.strip()
    return styles


def get_text_colors(element, css_styles=None) -> Tuple[Optional[str], Optional[str]]:
    styles = get_element_styles(element, css_styles)
    fg = styles.get("color")
    bg = styles.get("background-color") or styles.get("background")
    if bg and not bg.startswith("#") and not bg.startswith("rgb"):
        if " " in bg or "," in bg:
            bg = None
    return fg, bg
