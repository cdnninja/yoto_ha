"""utils.py"""

import logging

_LOGGER = logging.getLogger(__name__)


def split_media_id(text: str) -> tuple[str, str | None, str | None, int]:
    """Split media id into components.

    Format: cardid+chapterid+trackid+seconds
    """
    if text.count("-") > 1:
        _LOGGER.error("Switch Media ID format to use + as separator instead of -")
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
