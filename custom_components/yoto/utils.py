"""utils.py"""


def rgetattr(obj, attr):
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


def split_media_id(text):
    # a synthetic media idea in the format of cardid-chapterid-trackid
    parts = text.split("-")
    if len(parts) >= 3:
        cardid, chapterid, trackid = parts
    elif len(parts) == 2:
        cardid, chapterid = parts
        trackid = None
    else:
        cardid = text
        chapterid = trackid = None
    return cardid, chapterid, trackid
