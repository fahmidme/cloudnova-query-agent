"""Small semantic color palette; no dependency or escape codes in redirected output."""

import os
import sys
from typing import TextIO

STYLES = {
    "heading": "1;36", "prompt": "1;34", "sql": "1;35",
    "success": "32", "warning": "33", "error": "1;31", "muted": "2",
}


def paint(text: str, tone: str, stream: TextIO | None = None) -> str:
    stream = sys.stdout if stream is None else stream
    if "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb" or not stream.isatty():
        return text
    # Older Windows consoles may print ANSI literally; use plain text there.
    if os.name == "nt" and not (os.environ.get("WT_SESSION") or os.environ.get("ANSICON")):
        return text
    return f"\033[{STYLES[tone]}m{text}\033[0m"
