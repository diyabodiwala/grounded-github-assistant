"""
Small shared utility functions used across the sample application.
"""

import re


def slugify(text: str) -> str:
    """Convert a string into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length characters, appending an ellipsis if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "\u2026"
