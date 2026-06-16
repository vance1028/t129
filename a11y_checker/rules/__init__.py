from .base import Rule, RuleRegistry
from .images import ImageAltRule
from .forms import FormLabelRule
from .headings import HeadingOrderRule
from .lang import HtmlLangRule
from .link_text import LinkTextRule
from .contrast import ColorContrastRule
from .aria import AriaRule
from .dead_links import DeadLinkRule

DEFAULT_RULES = [
    ImageAltRule,
    FormLabelRule,
    HeadingOrderRule,
    HtmlLangRule,
    LinkTextRule,
    ColorContrastRule,
    AriaRule,
    DeadLinkRule,
]

__all__ = [
    "Rule",
    "RuleRegistry",
    "ImageAltRule",
    "FormLabelRule",
    "HeadingOrderRule",
    "HtmlLangRule",
    "LinkTextRule",
    "ColorContrastRule",
    "AriaRule",
    "DeadLinkRule",
    "DEFAULT_RULES",
]
