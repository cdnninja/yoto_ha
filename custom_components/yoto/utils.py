"""utils.py"""

import re
import logging

_LOGGER = logging.getLogger(__name__)

def rgetattr(obj: object, attr: str) -> object:
    """Recursively get nested attributes."""
    _this_func = rgetattr
    sp = attr.split(".", 1)
    if len(sp) == 1:
        left, right = sp[0], ""
    else:
        left, right = sp

    obj = getattr(obj, left)
    if right:
        obj = _this_func(obj, right)
    return obj


def split_media_id(text: str) -> tuple[str, str | None, str | None, int]:
    """Split media id into components.

    Format: cardid+chapterid+trackid+seconds
    """
    if text.count("-") > 1:
        _LOGGER.ERROR("Switch Media ID format to use + as separator instead of -") 
    parts = text.split("+")
    if len(parts) == 4:
        cardid, chapterid, trackid, time_str = parts
        time = int(time_str)
    elif len(parts) == 3:
        cardid, chapterid, trackid = parts
        time = 0
    elif len(parts) == 2:
        cardid, chapterid = parts
        trackid = None
        time = 0
    else:
        cardid = text
        chapterid = None
        trackid = None
        time = 0
    return cardid, chapterid, trackid, time


def parse_key(text: str) -> tuple[str, int] | None:
    """Parse a key string in format 'name[index]'.

    Returns tuple of (name, index) or None if format doesn't match.
    """
    match = re.match(r"(\w+)\[(\d+)\]", text)

    if match:
        object1 = match.group(1)  # This will be 'alarms'
        object2 = int(match.group(2))  # This will be 1
        return object1, object2
    return None
