"""
Color output helpers for Gitty Up.

This module provides color constants and helpers for terminal output.
In Phase 1, we're using Rich for output, so this is mostly for reference.
"""

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"


def colorize(text: str, color: str, bold: bool = False) -> str:
    """
    Colorize text with ANSI codes.

    Args:
        text: Text to colorize
        color: Color code
        bold: Whether to make text bold

    Returns:
        Colorized text
    """
    prefix = BOLD + color if bold else color
    return f"{prefix}{text}{RESET}"


def strip_ansi(text: str) -> str:
    """
    Strip ANSI color codes from text.

    Args:
        text: Text containing ANSI codes

    Returns:
        Text without ANSI codes
    """
    import re

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)
